import html
import json
from textwrap import dedent

import streamlit as st


st.set_page_config(
    page_title="Spirograph Studio",
    page_icon="S",
    layout="wide",
)


def clamp(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, value))


def build_canvas(config: dict) -> str:
    config_json = html.escape(json.dumps(config), quote=True)

    return dedent(
        f"""
        <div class="spiro-shell" data-config="{config_json}">
          <div class="stage">
            <canvas id="spiro-canvas"></canvas>
            <canvas id="tool-canvas"></canvas>
            <div class="hud">
              <button id="play-pause" type="button" aria-label="Pause drawing" title="Pause drawing">&#10074;&#10074;</button>
              <button id="clear" type="button" aria-label="Clear drawing" title="Clear drawing">&#8634;</button>
              <button id="save-jpg" type="button" aria-label="Save drawing as JPG" title="Save drawing as JPG">JPG</button>
              <label class="live-color" title="Change pen color while drawing">
                <span>Pen</span>
                <input id="live-pen" type="color" />
              </label>
            </div>
          </div>
        </div>

        <style>
          :root {{
            color-scheme: light;
          }}

          .spiro-shell {{
            width: 100%;
            display: flex;
            justify-content: center;
            padding: 8px 0 14px;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }}

          .stage {{
            position: relative;
            width: min(100%, var(--canvas-size));
            aspect-ratio: 1;
            background:
              linear-gradient(135deg, rgba(255,255,255,.7), rgba(255,255,255,.25)),
              var(--background);
            border: 1px solid rgba(28, 37, 65, .14);
            border-radius: 8px;
            box-shadow: 0 18px 46px rgba(22, 31, 56, .16);
            overflow: hidden;
          }}

          canvas {{
            position: absolute;
            inset: 0;
            display: block;
            width: 100%;
            height: 100%;
          }}

          #spiro-canvas {{
            z-index: 1;
          }}

          #tool-canvas {{
            z-index: 2;
            pointer-events: none;
          }}

          .hud {{
            position: absolute;
            z-index: 3;
            left: 14px;
            right: 14px;
            bottom: 14px;
            display: flex;
            align-items: center;
            gap: 8px;
            pointer-events: none;
          }}

          button,
          .live-color {{
            pointer-events: auto;
            height: 38px;
            display: inline-flex;
            align-items: center;
            justify-content: center;
            border: 1px solid rgba(25, 34, 58, .18);
            border-radius: 8px;
            background: rgba(255, 255, 255, .82);
            box-shadow: 0 8px 22px rgba(20, 27, 48, .12);
            backdrop-filter: blur(12px);
          }}

          button {{
            width: 42px;
            color: #172033;
            font-size: 17px;
            cursor: pointer;
          }}

          button:hover,
          .live-color:hover {{
            background: rgba(255, 255, 255, .95);
          }}

          .live-color {{
            margin-left: auto;
            gap: 8px;
            padding: 0 8px 0 12px;
            color: #172033;
            font-size: 13px;
            font-weight: 650;
          }}

          .live-color input {{
            width: 28px;
            height: 28px;
            padding: 0;
            border: 0;
            background: transparent;
            cursor: pointer;
          }}
        </style>

        <script>
          (() => {{
            const root = document.querySelector(".spiro-shell");
            const config = JSON.parse(root.dataset.config);
            const stage = root.querySelector(".stage");
            const canvas = root.querySelector("#spiro-canvas");
            const toolCanvas = root.querySelector("#tool-canvas");
            const drawCtx = canvas.getContext("2d");
            const toolCtx = toolCanvas.getContext("2d");
            const playPause = root.querySelector("#play-pause");
            const clearButton = root.querySelector("#clear");
            const saveJpgButton = root.querySelector("#save-jpg");
            const livePen = root.querySelector("#live-pen");

            const TWO_PI = Math.PI * 2;
            const guideShape = config.guideShape;
            const movingShape = config.movingShape;
            const objectCount = Math.max(2, config.objectCount);
            const attachments = buildAttachments();
            let running = true;
            let penColor = config.penColor;
            let hue = config.startHue;
            let step = 0;
            let tCursor = 0;
            let previous = null;
            let animationId = null;

            stage.style.setProperty("--canvas-size", `${{config.canvasSize}}px`);
            stage.style.setProperty("--background", config.backgroundColor);
            livePen.value = penColor;

            function resizeCanvas() {{
              const rect = canvas.getBoundingClientRect();
              const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
              const width = Math.max(260, Math.round(rect.width * dpr));
              const height = Math.max(260, Math.round(rect.height * dpr));
              if (
                canvas.width !== width ||
                canvas.height !== height ||
                toolCanvas.width !== width ||
                toolCanvas.height !== height
              ) {{
                canvas.width = width;
                canvas.height = height;
                toolCanvas.width = width;
                toolCanvas.height = height;
                drawCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
                toolCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
                resetDrawing();
              }}
            }}

            function clearToolLayer() {{
              const size = toolCanvas.getBoundingClientRect().width;
              toolCtx.clearRect(0, 0, size, size);
            }}

            function resetDrawing() {{
              const size = canvas.getBoundingClientRect().width;
              drawCtx.clearRect(0, 0, size, size);
              drawCtx.fillStyle = config.backgroundColor;
              drawCtx.fillRect(0, 0, size, size);
              clearToolLayer();
              drawTools(0);
              previous = null;
              step = 0;
              tCursor = 0;
            }}

            function saveAsJpg() {{
              const exportCanvas = document.createElement("canvas");
              exportCanvas.width = canvas.width;
              exportCanvas.height = canvas.height;
              const exportCtx = exportCanvas.getContext("2d");
              exportCtx.fillStyle = config.backgroundColor;
              exportCtx.fillRect(0, 0, exportCanvas.width, exportCanvas.height);
              exportCtx.drawImage(canvas, 0, 0);

              const link = document.createElement("a");
              link.download = `spirograph-drawing-${{new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-")}}.jpg`;
              link.href = exportCanvas.toDataURL("image/jpeg", 0.95);
              document.body.appendChild(link);
              link.click();
              link.remove();
            }}

            function shapeMultiplier(shape, angle) {{
              if (shape === "circle") return 1;
              if (shape === "triangle") return 1 + 0.11 * Math.cos(3 * angle);
              if (shape === "square") return 1 + 0.08 * Math.cos(4 * angle + Math.PI / 4);
              if (shape === "pentagon") return 1 + 0.07 * Math.cos(5 * angle);
              if (shape === "star") return 1 + 0.16 * Math.cos(5 * angle);
              if (shape === "flower") return 1 + 0.12 * Math.sin(6 * angle);
              return 1;
            }}

            function seededRandom(seed) {{
              let value = seed >>> 0;
              return function random() {{
                value += 0x6D2B79F5;
                let next = value;
                next = Math.imul(next ^ next >>> 15, next | 1);
                next ^= next + Math.imul(next ^ next >>> 7, next | 61);
                return ((next ^ next >>> 14) >>> 0) / 4294967296;
              }};
            }}

            function rotorRadius(index) {{
              return Math.max(6, config.innerRadius * Math.pow(config.objectScale, index));
            }}

            function buildAttachments() {{
              const random = seededRandom(config.attachmentSeed);
              const links = [];

              for (let index = 1; index < objectCount; index += 1) {{
                const previousRadius = rotorRadius(index - 1);
                const anchorRadius = previousRadius * config.attachmentSpread * (0.25 + random() * 0.74);
                const spinDirection = random() < 0.5 ? -1 : 1;
                links.push({{
                  anchorAngle: random() * TWO_PI,
                  anchorRadius,
                  phase: random() * TWO_PI,
                  spin: spinDirection * (0.7 + random() * 1.65) * (1 + index * 0.16),
                }});
              }}

              return {{
                links,
                pen: {{
                  angle: random() * TWO_PI,
                  radius: config.penOffset * (0.65 + random() * 0.7),
                }},
              }};
            }}

            function firstRotorAt(t) {{
              const R = config.outerRadius;
              const r = config.innerRadius;
              const inside = config.patternType === "inside";
              const guideWarp = shapeMultiplier(guideShape, t);
              const movingWarp = shapeMultiplier(movingShape, -t * R / Math.max(1, r));
              const outer = R * guideWarp;
              const inner = r * movingWarp;
              const ratio = inside ? (outer - inner) / inner : (outer + inner) / inner;
              const base = inside ? outer - inner : outer + inner;

              return {{
                x: base * Math.cos(t),
                y: base * Math.sin(t),
                radius: Math.max(8, inner),
                angle: inside ? Math.PI + ratio * t : -ratio * t,
                shape: movingShape,
              }};
            }}

            function chainState(t) {{
              const nodes = [firstRotorAt(t)];

              for (let index = 1; index < objectCount; index += 1) {{
                const previous = nodes[index - 1];
                const link = attachments.links[index - 1];
                const anchorAngle = previous.angle + link.anchorAngle;
                const x = previous.x + Math.cos(anchorAngle) * link.anchorRadius;
                const y = previous.y + Math.sin(anchorAngle) * link.anchorRadius;
                const radius = rotorRadius(index);

                nodes.push({{
                  x,
                  y,
                  radius,
                  angle: previous.angle + link.phase + link.spin * config.relationSpeed * t,
                  shape: movingShape,
                  anchorX: previous.x,
                  anchorY: previous.y,
                }});
              }}

              const last = nodes[nodes.length - 1];
              const penAngle = last.angle + attachments.pen.angle;
              const tip = {{
                x: last.x + Math.cos(penAngle) * attachments.pen.radius,
                y: last.y + Math.sin(penAngle) * attachments.pen.radius,
              }};

              return {{ nodes, tip }};
            }}

            function pointAt(t) {{
              const state = chainState(t);
              const first = state.nodes[0];

              return {{
                x: state.tip.x,
                y: state.tip.y,
                rollingX: first.x,
                rollingY: first.y,
                rollingRadius: first.radius,
                nodes: state.nodes,
              }};
            }}

            function colorForStep(advance = true) {{
              if (config.colorMode === "rainbow") {{
                if (advance) hue = (hue + config.rainbowSpeed) % 360;
                return `hsl(${{hue}}, 84%, 52%)`;
              }}
              if (config.colorMode === "pulse") {{
                const light = 42 + Math.sin(step * 0.04) * 16;
                return `hsl(${{config.startHue}}, 78%, ${{light}}%)`;
              }}
              return penColor;
            }}

            function drawPolygon(ctx, cx, cy, radius, sides, rotation, strokeStyle, fillStyle) {{
              ctx.beginPath();
              for (let i = 0; i <= sides; i += 1) {{
                const angle = rotation + (i / sides) * TWO_PI;
                const x = cx + Math.cos(angle) * radius;
                const y = cy + Math.sin(angle) * radius;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
              }}
              ctx.closePath();
              ctx.fillStyle = fillStyle;
              ctx.strokeStyle = strokeStyle;
              ctx.lineWidth = 1.5;
              ctx.fill();
              ctx.stroke();
            }}

            function drawShapeOutline(ctx, cx, cy, radius, shape, rotation, strokeStyle, fillStyle) {{
              if (shape === "circle") {{
                ctx.beginPath();
                ctx.arc(cx, cy, radius, 0, TWO_PI);
                ctx.fillStyle = fillStyle;
                ctx.strokeStyle = strokeStyle;
                ctx.lineWidth = 1.5;
                ctx.fill();
                ctx.stroke();
                return;
              }}

              if (shape === "triangle") return drawPolygon(ctx, cx, cy, radius, 3, rotation - Math.PI / 2, strokeStyle, fillStyle);
              if (shape === "square") return drawPolygon(ctx, cx, cy, radius, 4, rotation + Math.PI / 4, strokeStyle, fillStyle);
              if (shape === "pentagon") return drawPolygon(ctx, cx, cy, radius, 5, rotation - Math.PI / 2, strokeStyle, fillStyle);

              ctx.beginPath();
              const points = shape === "star" ? 10 : 180;
              for (let i = 0; i <= points; i += 1) {{
                const a = rotation + (i / points) * TWO_PI;
                const wave = shape === "star"
                  ? (i % 2 === 0 ? 1 : 0.56)
                  : 1 + 0.12 * Math.sin(6 * a);
                const x = cx + Math.cos(a) * radius * wave;
                const y = cy + Math.sin(a) * radius * wave;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
              }}
              ctx.closePath();
              ctx.fillStyle = fillStyle;
              ctx.strokeStyle = strokeStyle;
              ctx.lineWidth = 1.5;
              ctx.fill();
              ctx.stroke();
            }}

            function drawTools(t) {{
              if (!config.showTools) return;

              clearToolLayer();
              const size = toolCanvas.getBoundingClientRect().width;
              const center = size / 2;
              const scale = config.scale;
              const state = chainState(t);
              const nodes = state.nodes;

              toolCtx.save();
              toolCtx.translate(center, center);
              toolCtx.globalAlpha = 0.9;
              drawShapeOutline(
                toolCtx,
                0,
                0,
                config.outerRadius * scale,
                guideShape,
                0,
                "rgba(23, 32, 51, .32)",
                "rgba(255, 255, 255, .16)"
              );

              toolCtx.beginPath();
              for (let index = 1; index < nodes.length; index += 1) {{
                const previous = nodes[index - 1];
                const node = nodes[index];
                toolCtx.moveTo(previous.x * scale, previous.y * scale);
                toolCtx.lineTo(node.x * scale, node.y * scale);
              }}
              toolCtx.strokeStyle = "rgba(23, 32, 51, .28)";
              toolCtx.lineWidth = 1.4;
              toolCtx.stroke();

              nodes.forEach((node, index) => {{
                drawShapeOutline(
                  toolCtx,
                  node.x * scale,
                  node.y * scale,
                  node.radius * scale,
                  node.shape,
                  node.angle,
                  index === 0 ? "rgba(23, 32, 51, .46)" : "rgba(23, 32, 51, .38)",
                  index === nodes.length - 1 ? "rgba(255, 255, 255, .36)" : "rgba(255, 255, 255, .24)"
                );

                toolCtx.beginPath();
                toolCtx.arc(node.x * scale, node.y * scale, Math.max(2.5, config.lineWidth + 1), 0, TWO_PI);
                toolCtx.fillStyle = "rgba(23, 32, 51, .36)";
                toolCtx.fill();
              }});

              toolCtx.beginPath();
              toolCtx.arc(state.tip.x * scale, state.tip.y * scale, Math.max(3, config.lineWidth + 2), 0, TWO_PI);
              toolCtx.fillStyle = colorForStep(false);
              toolCtx.fill();
              toolCtx.restore();
            }}

            function drawFrame() {{
              if (running) {{
                const size = canvas.getBoundingClientRect().width;
                const center = size / 2;
                const scale = config.scale;

                const segmentCount = Math.max(1, config.samplesPerFrame);
                const segmentStep = config.frameAdvance / segmentCount;

                for (let i = 0; i < segmentCount; i += 1) {{
                  const t = tCursor;
                  const p = pointAt(t);
                  const next = {{
                    x: center + p.x * scale,
                    y: center + p.y * scale,
                  }};

                  if (previous) {{
                    drawCtx.beginPath();
                    drawCtx.moveTo(previous.x, previous.y);
                    drawCtx.lineTo(next.x, next.y);
                    drawCtx.strokeStyle = colorForStep();
                    drawCtx.lineWidth = config.lineWidth;
                    drawCtx.lineCap = "round";
                    drawCtx.lineJoin = "round";
                    drawCtx.globalAlpha = config.penOpacity;
                    drawCtx.stroke();
                    drawCtx.globalAlpha = 1;
                  }}

                  previous = next;
                  step += 1;
                  tCursor += segmentStep;
                  if (tCursor >= config.maxAngle) {{
                    if (config.loopDrawing) resetDrawing();
                    else running = false;
                  }}
                }}

                if (config.showTools) drawTools(tCursor);
              }}

              playPause.innerHTML = running ? "&#10074;&#10074;" : "&#9654;";
              playPause.setAttribute("aria-label", running ? "Pause drawing" : "Resume drawing");
              animationId = requestAnimationFrame(drawFrame);
            }}

            playPause.addEventListener("click", () => {{
              running = !running;
            }});

            clearButton.addEventListener("click", () => {{
              resetDrawing();
              running = true;
            }});

            saveJpgButton.addEventListener("click", saveAsJpg);

            livePen.addEventListener("input", (event) => {{
              penColor = event.target.value;
            }});

            window.addEventListener("resize", resizeCanvas);
            resizeCanvas();
            drawFrame();

            window.addEventListener("pagehide", () => {{
              if (animationId) cancelAnimationFrame(animationId);
            }});
          }})();
        </script>
        """
    )


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


def render_canvas(html_doc: str, height: int) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html_doc, height=height, width="stretch")
        return

    import streamlit.components.v1 as components

    components.html(html_doc, height=height, scrolling=False)


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
    render_canvas(build_canvas(config), height=canvas_size + 44)

with right:
    st.subheader("Current setup")
    st.metric("Canvas", f"{canvas_size}px")
    st.metric("Tool sizes", f"{outer_radius} / {inner_radius}")
    st.metric("Rotating objects", object_count)
    st.metric("Pen hole", pen_offset)
    st.caption("Use the small pen swatch on the canvas to change color while the drawing keeps moving.")
    st.caption("Each extra object attaches to the previous one at a seeded random spot, then the pen rides on the final object.")
