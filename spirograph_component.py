from pathlib import Path

import streamlit.components.v1 as components

spirograph_component = components.declare_component(
    "spirograph", path=str(Path(__file__).resolve().parent / "component" / "spirograph")
)
