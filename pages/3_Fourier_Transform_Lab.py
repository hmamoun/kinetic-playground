import random

import numpy as np
import pandas as pd
import streamlit as st


st.set_page_config(
    page_title="Fourier Transform Lab",
    page_icon="F",
    layout="wide",
)


def new_seed() -> int:
    return random.SystemRandom().randint(1, 999_999_999)


if "fourier_seed" not in st.session_state:
    st.session_state.fourier_seed = new_seed()


def make_random_wave(
    seed: int,
    samples: int,
    sample_rate: int,
    component_count: int,
    max_frequency: int,
    noise_level: float,
) -> tuple[np.ndarray, np.ndarray, list[dict]]:
    rng = np.random.default_rng(seed)
    t = np.arange(samples) / sample_rate
    usable_frequencies = np.arange(1, min(max_frequency, sample_rate // 2 - 1) + 1)
    chosen = rng.choice(usable_frequencies, size=component_count, replace=False)
    y = np.zeros_like(t, dtype=float)
    ingredients = []

    for frequency in sorted(chosen):
        amplitude = float(rng.uniform(0.25, 1.0))
        phase = float(rng.uniform(-np.pi, np.pi))
        y += amplitude * np.cos(2 * np.pi * frequency * t + phase)
        ingredients.append(
            {
                "frequency_hz": int(frequency),
                "amplitude": amplitude,
                "phase_rad": phase,
            }
        )

    if noise_level > 0:
        y += rng.normal(0, noise_level, size=samples)

    y -= y.mean()
    max_abs = np.max(np.abs(y))
    if max_abs > 0:
        y = y / max_abs

    return t, y, ingredients


def analyze_wave(y: np.ndarray, sample_rate: int) -> pd.DataFrame:
    samples = len(y)
    spectrum = np.fft.rfft(y)
    frequencies = np.fft.rfftfreq(samples, d=1 / sample_rate)
    amplitudes = np.abs(spectrum) * 2 / samples
    amplitudes[0] = np.abs(spectrum[0]) / samples
    phases = np.angle(spectrum)

    return pd.DataFrame(
        {
            "frequency_hz": frequencies,
            "amplitude": amplitudes,
            "phase_rad": phases,
            "real": spectrum.real,
            "imag": spectrum.imag,
        }
    )


def reconstruct_from_components(
    t: np.ndarray,
    components: pd.DataFrame,
    count: int,
) -> tuple[np.ndarray, pd.DataFrame]:
    selected = components[components["frequency_hz"] > 0].nlargest(count, "amplitude").copy()
    y = np.zeros_like(t, dtype=float)

    for row in selected.itertuples(index=False):
        y += row.amplitude * np.cos(2 * np.pi * row.frequency_hz * t + row.phase_rad)

    return y, selected


def component_series(t: np.ndarray, selected: pd.DataFrame) -> pd.DataFrame:
    data = {"t": t}
    for rank, row in enumerate(selected.itertuples(index=False), start=1):
        label = f"{rank}: {row.frequency_hz:.0f} Hz"
        data[label] = row.amplitude * np.cos(2 * np.pi * row.frequency_hz * t + row.phase_rad)
    return pd.DataFrame(data)


st.title("Fourier Transform Lab")

with st.sidebar:
    st.header("Random Wave")
    if st.button("New random wave", width="stretch"):
        st.session_state.fourier_seed = new_seed()

    seed = st.number_input(
        "Wave seed",
        min_value=1,
        max_value=999_999_999,
        value=int(st.session_state.fourier_seed),
        step=1,
    )
    st.session_state.fourier_seed = int(seed)

    component_count = st.slider("Hidden components", 2, 10, 5)
    max_frequency = st.slider("Max random frequency", 4, 60, 28)
    noise_level = st.slider("Noise", 0.0, 0.4, 0.03, 0.01)

    st.header("Analysis")
    sample_rate = st.slider("Sample rate", 64, 512, 256, 32)
    duration = st.slider("Duration", 1, 4, 2)
    top_count = st.slider("Components to reconstruct", 1, 12, 5)

samples = sample_rate * duration
t, y, ingredients = make_random_wave(
    seed=int(seed),
    samples=samples,
    sample_rate=sample_rate,
    component_count=component_count,
    max_frequency=max_frequency,
    noise_level=noise_level,
)
spectrum = analyze_wave(y, sample_rate)
reconstruction, selected = reconstruct_from_components(t, spectrum, top_count)
error = float(np.sqrt(np.mean((y - reconstruction) ** 2)))

tab_wave, tab_formula, tab_components = st.tabs(["Visual Lab", "Formulas", "Components"])

with tab_wave:
    left, right = st.columns([0.62, 0.38], vertical_alignment="top")

    with left:
        st.subheader("Random Wave")
        wave_df = pd.DataFrame({"time_s": t, "random wave": y})
        st.line_chart(wave_df, x="time_s", y="random wave", height=260)

        st.subheader("Reconstruction From Discovered Components")
        compare_df = pd.DataFrame(
            {
                "time_s": t,
                "random wave": y,
                "reconstructed": reconstruction,
                "difference": y - reconstruction,
            }
        )
        st.line_chart(compare_df, x="time_s", y=["random wave", "reconstructed"], height=260)

    with right:
        st.subheader("Frequency Spectrum")
        display_spectrum = spectrum[spectrum["frequency_hz"] > 0].copy()
        display_spectrum = display_spectrum[display_spectrum["frequency_hz"] <= max_frequency + 10]
        st.bar_chart(display_spectrum, x="frequency_hz", y="amplitude", height=260)

        st.metric("Reconstruction error", f"{error:.4f}")
        st.metric("Strongest frequency", f"{selected.iloc[0]['frequency_hz']:.0f} Hz")
        st.caption("The tallest bars are the wave's strongest repeating ingredients.")

    st.subheader("Individual Component Waves")
    components_df = component_series(t, selected)
    st.line_chart(
        components_df,
        x="t",
        y=[column for column in components_df.columns if column != "t"],
        height=300,
    )

with tab_formula:
    st.subheader("Idea")
    st.write(
        "A complicated wave can be written as a sum of simple rotating waves. "
        "The Fourier Transform finds which frequencies are present and how strong each one is."
    )

    st.latex(r"x(t) \approx \sum_{k=1}^{K} A_k \cos(2\pi f_k t + \phi_k)")
    st.write("For sampled data, the Discrete Fourier Transform is:")
    st.latex(r"X_k = \sum_{n=0}^{N-1} x_n e^{-i2\pi kn/N}")
    st.write("The amplitude and phase used for reconstruction are:")
    st.latex(r"A_k = \frac{2|X_k|}{N}")
    st.latex(r"\phi_k = \arg(X_k)")

    st.info(
        "In this page the wave starts as a random mix of hidden cosine waves. "
        "The FFT does not know the ingredients; it estimates them from the samples."
    )

with tab_components:
    st.subheader("Components Found By FFT")
    found = selected[["frequency_hz", "amplitude", "phase_rad"]].copy()
    found["frequency_hz"] = found["frequency_hz"].round(3)
    found["amplitude"] = found["amplitude"].round(4)
    found["phase_rad"] = found["phase_rad"].round(4)
    found.insert(0, "rank", range(1, len(found) + 1))
    st.dataframe(found, width="stretch", hide_index=True)

    with st.expander("Reveal the random ingredients used to create this wave"):
        true_df = pd.DataFrame(ingredients)
        true_df["amplitude"] = true_df["amplitude"].round(4)
        true_df["phase_rad"] = true_df["phase_rad"].round(4)
        st.dataframe(true_df, width="stretch", hide_index=True)

    st.write("A clean random wave will show discovered components close to the hidden ingredients. More noise makes the spectrum fuzzier.")
