import json
import random
from textwrap import dedent

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


def build_wave_lab_view(payload: dict) -> str:
    payload_json = json.dumps(payload).replace("<", "\\u003c")

    return dedent(
        """
        <div class="wavelab-shell">
          <div class="wavelab-controls">
            <button id="wl-play-pause" type="button">Pause</button>
            <button id="wl-restart" type="button">Restart</button>
            <span id="wl-status" class="wavelab-status"></span>
          </div>

          <div class="wavelab-main">
            <div class="wavelab-label">Main Wave</div>
            <canvas id="wl-main-canvas"></canvas>
          </div>

          <div class="wavelab-grid" id="wl-grid"></div>
        </div>

        <script id="wl-data" type="application/json">%s</script>

        <style>
          .wavelab-shell {
            width: 100%%;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }

          .wavelab-controls {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 10px;
          }

          .wavelab-controls button {
            padding: 6px 16px;
            border-radius: 999px;
            border: 1px solid rgba(23, 32, 51, .18);
            background: #172033;
            color: #f4f6fb;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
          }

          .wavelab-controls button:hover {
            background: #232f47;
          }

          .wavelab-status {
            font-size: 13px;
            color: #475467;
          }

          .wavelab-label {
            font-size: 12px;
            font-weight: 700;
            color: #475467;
            margin-bottom: 4px;
            text-transform: uppercase;
            letter-spacing: .03em;
          }

          .wavelab-main {
            border: 1px solid rgba(23, 32, 51, .14);
            border-radius: 8px;
            background: rgba(255, 255, 255, .6);
            padding: 10px 14px;
            margin-bottom: 14px;
          }

          .wavelab-main canvas {
            width: 100%%;
            height: 160px;
            display: block;
          }

          .wavelab-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
            gap: 12px;
          }

          .wavelab-mini {
            border: 1px solid rgba(23, 32, 51, .14);
            border-radius: 8px;
            background: rgba(255, 255, 255, .6);
            padding: 8px 12px;
          }

          .wavelab-mini canvas {
            width: 100%%;
            height: 100px;
            display: block;
          }
        </style>

        <script>
          (() => {
            const payload = JSON.parse(document.getElementById("wl-data").textContent);
            const t = payload.t;
            const main = payload.main;
            const components = payload.components;
            const totalPoints = t.length;

            const playPauseButton = document.getElementById("wl-play-pause");
            const restartButton = document.getElementById("wl-restart");
            const statusLabel = document.getElementById("wl-status");
            const mainCanvas = document.getElementById("wl-main-canvas");
            const grid = document.getElementById("wl-grid");

            const COLORS = [
              "#136f63", "#b45309", "#7c3aed", "#dc2626", "#2563eb",
              "#059669", "#d97706", "#db2777", "#0891b2", "#65a30d",
              "#9333ea", "#e11d48",
            ];

            const componentCanvases = components.map((component) => {
              const wrap = document.createElement("div");
              wrap.className = "wavelab-mini";
              const label = document.createElement("div");
              label.className = "wavelab-label";
              label.textContent = component.label;
              const canvas = document.createElement("canvas");
              wrap.appendChild(label);
              wrap.appendChild(canvas);
              grid.appendChild(wrap);
              return canvas;
            });

            let running = true;
            let revealIndex = 0;
            let animationId = null;
            const pointsPerFrame = Math.max(1, Math.round(totalPoints / 240));

            function setupCanvas(canvas) {
              const rect = canvas.getBoundingClientRect();
              const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
              const width = Math.max(1, Math.round(rect.width * dpr));
              const height = Math.max(1, Math.round(rect.height * dpr));
              if (canvas.width !== width || canvas.height !== height) {
                canvas.width = width;
                canvas.height = height;
              }
              const ctx = canvas.getContext("2d");
              ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
              return { ctx, width: rect.width, height: rect.height };
            }

            function drawSeries(canvas, values, color, revealCount) {
              const { ctx, width, height } = setupCanvas(canvas);
              ctx.clearRect(0, 0, width, height);

              let maxAbs = 0;
              for (let i = 0; i < values.length; i += 1) {
                const magnitude = Math.abs(values[i]);
                if (magnitude > maxAbs) maxAbs = magnitude;
              }
              const range = (maxAbs || 1) * 1.15;
              const midY = height / 2;

              ctx.strokeStyle = "rgba(23, 32, 51, .18)";
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(0, midY);
              ctx.lineTo(width, midY);
              ctx.stroke();

              const count = Math.max(0, Math.min(revealCount, values.length));
              if (count > 1) {
                ctx.strokeStyle = color;
                ctx.lineWidth = 2;
                ctx.lineJoin = "round";
                ctx.beginPath();
                for (let i = 0; i < count; i += 1) {
                  const x = (i / (values.length - 1)) * width;
                  const y = midY - (values[i] / range) * midY;
                  if (i === 0) ctx.moveTo(x, y);
                  else ctx.lineTo(x, y);
                }
                ctx.stroke();

                const lastX = ((count - 1) / (values.length - 1)) * width;
                const lastY = midY - (values[count - 1] / range) * midY;
                ctx.fillStyle = color;
                ctx.beginPath();
                ctx.arc(lastX, lastY, 3.5, 0, Math.PI * 2);
                ctx.fill();
              }
            }

            function renderFrame() {
              drawSeries(mainCanvas, main, "#172033", revealIndex);
              components.forEach((component, index) => {
                drawSeries(componentCanvases[index], component.values, COLORS[index %% COLORS.length], revealIndex);
              });
              statusLabel.textContent = `${Math.min(revealIndex, totalPoints)} / ${totalPoints} samples`;
            }

            function tick() {
              if (running) {
                revealIndex += pointsPerFrame;
                if (revealIndex >= totalPoints) {
                  revealIndex = totalPoints;
                  running = false;
                  playPauseButton.textContent = "Play";
                }
                renderFrame();
              }
              animationId = requestAnimationFrame(tick);
            }

            playPauseButton.addEventListener("click", () => {
              if (!running && revealIndex >= totalPoints) {
                revealIndex = 0;
              }
              running = !running;
              playPauseButton.textContent = running ? "Pause" : "Play";
            });

            restartButton.addEventListener("click", () => {
              revealIndex = 0;
              running = true;
              playPauseButton.textContent = "Pause";
              renderFrame();
            });

            window.addEventListener("resize", renderFrame);
            renderFrame();
            tick();

            window.addEventListener("pagehide", () => {
              if (animationId) cancelAnimationFrame(animationId);
            });
          })();
        </script>
        """
    ) % payload_json


def render_wave_lab_view(html_doc: str, height: int) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html_doc, height=height, width="stretch")
        return

    import streamlit.components.v1 as components

    components.html(html_doc, height=height, scrolling=False)


def format_ingredient_list(ingredients: list[dict]) -> str:
    return ", ".join(
        f"{item['frequency_hz']} Hz (A={item['amplitude']:.2f}, φ={item['phase_rad']:.2f} rad)"
        for item in ingredients
    )


def format_component_list(components: pd.DataFrame) -> str:
    return ", ".join(
        f"{row.frequency_hz:.0f} Hz (A={row.amplitude:.2f}, φ={row.phase_rad:.2f} rad)"
        for row in components.itertuples(index=False)
    )


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

strongest = selected.iloc[0]
ingredients_text = format_ingredient_list(ingredients)
selected_text = format_component_list(selected)
nyquist = sample_rate / 2

tab_wave, tab_formula, tab_components = st.tabs(["Visual Lab", "Formulas", "Components"])

with tab_wave:
    st.subheader("Live Wave Playback")
    st.caption(
        "The random wave and each of its discovered components sweep across their own chart in sync. "
        "Use Pause/Play or Restart to control the animation."
    )
    components_df = component_series(t, selected)
    component_columns = [column for column in components_df.columns if column != "t"]
    wave_lab_payload = {
        "t": t.tolist(),
        "main": y.tolist(),
        "components": [
            {"label": column, "values": components_df[column].tolist()}
            for column in component_columns
        ],
    }
    grid_rows = -(-len(component_columns) // 4)
    render_wave_lab_view(build_wave_lab_view(wave_lab_payload), height=320 + grid_rows * 150)

    left, right = st.columns([0.62, 0.38], vertical_alignment="top")

    with left:
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

st.divider()
st.header("How the math works, step by step")
st.caption(
    f"A plain-language walkthrough tied to the wave currently on screen — seed **{int(seed)}**, "
    f"**{component_count}** hidden components, sample rate **{sample_rate} Hz**, duration **{duration} s**."
)

st.subheader("1. Build a wave out of simple waves")
st.write(
    "Every wave on this page starts as a sum of a few simple cosine waves. A cosine wave is just a smooth, "
    "repeating up-and-down wiggle. Three numbers describe one completely:"
)
st.markdown(
    "- **Frequency (f)** — how many wiggles happen every second, measured in Hz\n"
    "- **Amplitude (A)** — how tall the wiggle is (its strength)\n"
    "- **Phase (φ)** — where in its cycle the wiggle starts, i.e. a shift left or right in time"
)
st.write("Adding K of these wiggles together makes the random wave shown in the chart:")
st.latex(r"x(t) = \sum_{k=1}^{K} A_k \cos(2\pi f_k t + \phi_k)")
st.markdown(
    f"For **seed {int(seed)}**, with the sidebar set to **{component_count}** hidden components and a max "
    f"frequency of **{max_frequency} Hz**, the app rolled these K = {component_count} random ingredients "
    f"(then stirred in noise level **{noise_level}**) and hid the recipe:"
)
st.code(ingredients_text, language=None)
st.write("That hidden recipe is exactly the mystery the Fourier Transform has to reverse-engineer below.")

st.subheader("2. Turn the wave into numbers a computer can use (sampling)")
st.write(
    "A computer can't store a perfectly smooth curve, so it takes snapshots of the wave's height at evenly "
    "spaced moments in time. The **sample rate** is how many snapshots are taken per second, and **duration** "
    "is how many seconds are recorded. Multiplying the two gives the total number of samples, N."
)
st.latex(r"N = \text{sample rate} \times \text{duration}")
st.markdown(
    f"On screen right now: N = **{sample_rate}** × **{duration}** = **{samples}** samples. That also caps the "
    f"highest frequency the analysis can ever see — the Nyquist limit — at sample rate / 2 = **{nyquist:.0f} Hz**."
)

st.subheader("3. Ask \"how much of each frequency is hiding in there?\" — the Fourier Transform")
st.write(
    "This is the key trick. For every candidate frequency, the Discrete Fourier Transform (DFT) compares the "
    "wave against a perfectly spinning reference wave at that frequency:"
)
st.latex(r"X_k = \sum_{n=0}^{N-1} x_n \, e^{-i 2\pi k n / N}")
st.write(
    "Picture the term e^{-i2\\pi kn/N} as an arrow spinning around a clock face, completing k full spins over "
    "the whole recording. Each sample of the wave gives that arrow a little nudge. If the wave truly contains a "
    "wiggle at frequency k, every nudge lands pointing roughly the same way, so the arrow ends up far from the "
    "center. If frequency k is not really in the wave, the nudges point every which way and mostly cancel out, "
    "leaving the arrow near the center. X_k is simply where that arrow ends up — a point with a real part and an "
    "imaginary part."
)
st.markdown(
    f"With N = **{samples}** samples on this run, the app computes X_k for every k from 0 up to N/2 = "
    f"**{samples // 2}**, one candidate frequency at a time. The FFT (Fast Fourier Transform) is just a very "
    "efficient shortcut for getting all of those X_k values at once instead of one by one."
)

st.subheader("4. Read the arrow: turn X_k back into amplitude and phase")
st.write(
    "Each X_k lands on a 2D plane (real axis, imaginary axis). How far it lands from the center says *how "
    "strong* that frequency is, and the angle it points at says *where in its cycle* that frequency starts:"
)
st.latex(r"A_k = \frac{2\lvert X_k \rvert}{N}, \qquad \lvert X_k \rvert = \sqrt{\text{real}^2 + \text{imag}^2}")
st.latex(r"\phi_k = \arg(X_k) = \operatorname{atan2}(\text{imag}, \text{real})")
st.markdown(
    f"On the current Frequency Spectrum chart, the tallest bar — the arrow that landed farthest from the "
    f"center — sits at **{strongest.frequency_hz:.0f} Hz** with amplitude **A = {strongest.amplitude:.2f}** and "
    f"phase **φ = {strongest.phase_rad:.2f} rad**. The 2/N scaling (2/{samples} here) just undoes the DFT's "
    "internal bookkeeping so A_k comes back out in the same units as the original wave."
)

st.subheader("5. Keep only the loudest ingredients and rebuild the wave")
st.write(
    "The full spectrum usually has a little energy at almost every frequency, mostly from noise. To reconstruct "
    "a clean approximation, the app sorts every frequency by amplitude, keeps only the top few (however many you "
    "choose in the sidebar), and adds just those cosine waves back together using the same formula from step 1:"
)
st.latex(r"\hat{x}(t) = \sum_{k \,\in\, \text{top components}} A_k \cos(2\pi f_k t + \phi_k)")
st.markdown(
    f"You asked for the top **{top_count}** components. For this run, the FFT ranked these as strongest and "
    "used them to build the orange 'reconstructed' line:"
)
st.code(selected_text, language=None)
if top_count >= component_count:
    st.write(
        f"Since {top_count} ≥ the {component_count} hidden ingredients from step 1, this list should look very "
        "close to the hidden recipe above (small differences come from noise and sampling)."
    )
else:
    st.write(
        f"Because only {top_count} of the {component_count} hidden ingredients were kept, the reconstruction is "
        "missing some real components — increase 'Components to reconstruct' in the sidebar to recover them."
    )

st.subheader("6. Score the guess (reconstruction error)")
st.write(
    "To see how close the rebuilt wave is to the original, the app compares the two curves point by point using "
    "the root-mean-square error (RMSE):"
)
st.latex(r"\text{error} = \sqrt{\frac{1}{N}\sum_{n=0}^{N-1} \left(x_n - \hat{x}_n\right)^2}")
st.markdown(
    f"For the wave on screen right now, that works out to **error = {error:.4f}**. Squaring every difference "
    "makes it positive, so a spot where the reconstruction is too high doesn't cancel out a spot where it's too "
    "low; averaging those squares gives a typical mismatch size; the square root brings the units back in line "
    "with the original wave. Try lowering the noise slider or reconstructing with more components and watch this "
    "number shrink."
)
