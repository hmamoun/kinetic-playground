# Kinetic Playground

Interactive Streamlit playground for kinetic math and physics toys.

## What is inside

- **Spirograph Studio**: animated Spirograph drawing with linked rotating objects, live pen color changes, motion controls, and JPG export.
- **Galton Board Works**: falling-ball probability simulation with adjustable rows, bias, speed, colors, and histogram curve.
- **Sealed Sand Art**: rotating sealed-glass sand-art simulator with liquid thickness, air bubbles, gravity scale, random sand grain weights, bubble buoyancy, and saved defaults.

## Run locally

```powershell
pip install -r requirements.txt
streamlit run app.py
```

Then open:

```text
http://localhost:8501
```

To run on another port:

```powershell
streamlit run app.py --server.port 8502
```

## Project layout

```text
app.py                          # Spirograph Studio home page
pages/1_Galton_Board_Works.py   # Galton board simulation
pages/2_Sealed_Sand_Art.py      # Sealed sand-art simulation
requirements.txt                # Python dependencies
```

## Notes

The Sealed Sand Art page can save local default settings to `sealed_sand_art_defaults.json`. That file is ignored by Git because it is meant to be personal to your local setup.
