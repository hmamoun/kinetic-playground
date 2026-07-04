import streamlit as st

from spirograph_component import spirograph_component


st.set_page_config(
    page_title="Spirograph Studio",
    page_icon="S",
    layout="wide",
)


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def calculate_scale(
    canvas_size: int,
    outer_radius: int,
    inner_radius: int,
    pen_offset: int,
    pattern_type: str,
    object_count: int,
    object_scale: float,
    attachment_spread: float,
) -> float:
    chain_reach = 0.0
    previous_radius = inner_radius
    for index in range(1, object_count):
        radius = inner_radius * (object_scale**index)
        chain_reach += previous_radius * attachment_spread + radius
        previous_radius = radius

    reach = outer_radius + inner_radius + chain_reach + pen_offset
    if pattern_type == "inside":
        reach = outer_radius + chain_reach + pen_offset

    return (canvas_size * 0.42) / max(1, reach)


st.title("Spirograph Studio")

with st.sidebar:
    st.header("Canvas")
    canvas_size = st.slider("Size", 420, 980, 720, 20)
    background_color = st.color_picker("Background color", "#fffaf0")
    show_tools = st.toggle("Show tools", value=True)

    st.header("Tools")
    pattern_type = st.segmented_control(
        "Rolling mode",
        options=["Inside ring", "Outside ring"],
        default="Inside ring",
    )
    tool_shapes = {
        "Circle": "circle",
        "Triangle": "triangle",
        "Square": "square",
        "Pentagon": "pentagon",
        "Star": "star",
        "Flower": "flower",
    }
    guide_shape_label = st.selectbox("Fixed tool shape", list(tool_shapes), index=0)
    moving_shape_label = st.selectbox("Moving tool shape", list(tool_shapes), index=0)

    outer_radius = st.slider("Fixed tool size", 80, 280, 180, 5)
    inner_radius = st.slider("Moving tool size", 12, 150, 64, 1)
    pen_offset = st.slider("Pen hole distance", 4, 180, 96, 1)

    st.header("Linked objects")
    object_count = st.slider("Rotating objects", 2, 8, 2)
    object_scale = st.slider("Object size decay", 45, 95, 72) / 100
    attachment_spread = st.slider("Random attach spread", 20, 100, 76) / 100
    relation_speed = st.slider("Linked object spin", 25, 220, 100) / 100
    attachment_seed = st.number_input("Random attachment seed", min_value=1, max_value=999999, value=7319, step=1)

    st.header("Pen")
    pen_color = st.color_picker("Pen color", "#136f63")
    color_mode = st.radio(
        "Color while running",
        ["Solid", "Rainbow", "Pulse"],
        horizontal=True,
    )
    line_width = st.slider("Line width", 1, 8, 2)
    pen_opacity = st.slider("Pen opacity", 20, 100, 88) / 100

    st.header("Motion")
    rotation_speed = st.slider("Rotation speed", 5, 200, 100, 5) / 100
    samples_per_frame = st.slider("Stroke smoothness", 1, 12, 5)
    detail = st.slider("Detail", 600, 9000, 4200, 100)
    loop_drawing = st.toggle("Loop drawing", value=True)


inner_radius = clamp(inner_radius, 8, max(8, outer_radius - 8))
last_rotor_radius = inner_radius * (object_scale ** (object_count - 1))
pen_offset = clamp(pen_offset, 4, max(4, int(last_rotor_radius)))
pattern_key = "inside" if pattern_type == "Inside ring" else "outside"
scale = calculate_scale(
    canvas_size,
    outer_radius,
    inner_radius,
    pen_offset,
    pattern_key,
    object_count,
    object_scale,
    attachment_spread,
)

config = {
    "canvasSize": canvas_size,
    "backgroundColor": background_color,
    "showTools": show_tools,
    "patternType": pattern_key,
    "guideShape": tool_shapes[guide_shape_label],
    "movingShape": tool_shapes[moving_shape_label],
    "outerRadius": outer_radius,
    "innerRadius": inner_radius,
    "penOffset": pen_offset,
    "objectCount": object_count,
    "objectScale": object_scale,
    "attachmentSpread": attachment_spread,
    "relationSpeed": relation_speed,
    "attachmentSeed": int(attachment_seed),
    "penColor": pen_color,
    "colorMode": color_mode.lower(),
    "lineWidth": line_width,
    "penOpacity": pen_opacity,
    "samplesPerFrame": samples_per_frame,
    "frameAdvance": 0.018 * 5 * rotation_speed,
    "maxAngle": detail * 0.018,
    "loopDrawing": loop_drawing,
    "scale": scale,
    "startHue": 174,
    "rainbowSpeed": 0.8,
}

left, right = st.columns([0.72, 0.28], vertical_alignment="top")

with left:
    spirograph_component(config=config, key="spirograph")

with right:
    st.subheader("Current setup")
    st.metric("Canvas", f"{canvas_size}px")
    st.metric("Tool sizes", f"{outer_radius} / {inner_radius}")
    st.metric("Rotating objects", object_count)
    st.metric("Pen hole", pen_offset)
    st.caption("Use the small pen swatch on the canvas to change color while the drawing keeps moving.")
    st.caption("Each extra object attaches to the previous one at a seeded random spot, then the pen rides on the final object.")
