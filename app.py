import streamlit as st

st.set_page_config(
    page_title="Kinetic Playground",
    page_icon="K",
    layout="wide",
)

st.title("Kinetic Playground")
st.write(
    "A small, growing collection of physics and math toys, digitized one page at a time. "
    "Pick a page from the sidebar, or jump in below."
)

st.divider()

PAGES = [
    (
        "pages/1_Spirograph_Studio.py",
        "Spirograph Studio",
        "🌀",
        "Animated gears draw hypotrochoid curves. Link rotating objects together, "
        "change the pen color mid-draw, and export a JPG.",
    ),
    (
        "pages/1_Galton_Board_Works.py",
        "Galton Board Works",
        "🎲",
        "Balls bounce randomly through a wall of pegs and pile up into a bell curve. "
        "Tune the rows, bias, drop speed, and colors.",
    ),
    (
        "pages/2_Sealed_Sand_Art.py",
        "Sealed Sand Art",
        "⏳",
        "A simulated sand-art toy: colored grains, liquid, air bubbles, and gravity "
        "settle into a new pattern every time you turn it.",
    ),
    (
        "pages/3_Fourier_Transform_Lab.py",
        "Fourier Transform Lab",
        "📈",
        "Build a signal from hidden sine waves, run an FFT to recover them, and watch "
        "the pieces add back up into the whole.",
    ),
    (
        "pages/4_Camera_Games.py",
        "Camera Games",
        "📷",
        "Turn your webcam into a toy: live water-ripple distortion, a spinning "
        "kaleidoscope, or a color-based object counter.",
    ),
    (
        "pages/5_Machine_Learning_Lab.py",
        "Machine Learning Lab",
        "🧠",
        "Watch a tiny neural network learn a 2D classification problem live, its "
        "decision boundary reshaping itself epoch by epoch.",
    ),
]

for path, label, icon, description in PAGES:
    st.page_link(path, label=f"**{label}**", icon=icon)
    st.caption(description)
