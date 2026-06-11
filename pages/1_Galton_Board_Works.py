import html
import json
from textwrap import dedent

import streamlit as st


st.set_page_config(
    page_title="Galton Board Works",
    page_icon="G",
    layout="wide",
)


def build_board(config: dict) -> str:
    config_json = html.escape(json.dumps(config), quote=True)
    template = """
    <div class="galton-shell" data-config="__CONFIG__">
      <div class="stage">
        <canvas id="galton-canvas"></canvas>
        <div class="hud">
          <button id="play-pause" type="button" aria-label="Pause simulation" title="Pause simulation">&#10074;&#10074;</button>
          <button id="reset" type="button" aria-label="Reset simulation" title="Reset simulation">&#8634;</button>
          <button id="burst" type="button" aria-label="Drop more balls" title="Drop more balls">+50</button>
          <span id="stats"></span>
        </div>
      </div>
    </div>

    <style>
      .galton-shell {
        width: 100%;
        display: flex;
        justify-content: center;
        padding: 8px 0 14px;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }

      .stage {
        position: relative;
        width: min(100%, var(--board-width));
        height: var(--board-height);
        background:
          linear-gradient(135deg, rgba(255, 255, 255, .78), rgba(255, 255, 255, .2)),
          var(--background);
        border: 1px solid rgba(24, 33, 54, .15);
        border-radius: 8px;
        box-shadow: 0 18px 46px rgba(22, 31, 56, .16);
        overflow: hidden;
      }

      canvas {
        position: absolute;
        inset: 0;
        display: block;
        width: 100%;
        height: 100%;
      }

      .hud {
        position: absolute;
        z-index: 2;
        left: 14px;
        right: 14px;
        bottom: 14px;
        display: flex;
        align-items: center;
        gap: 8px;
        pointer-events: none;
      }

      button,
      #stats {
        pointer-events: auto;
        height: 38px;
        display: inline-flex;
        align-items: center;
        justify-content: center;
        border: 1px solid rgba(25, 34, 58, .18);
        border-radius: 8px;
        background: rgba(255, 255, 255, .84);
        box-shadow: 0 8px 22px rgba(20, 27, 48, .12);
        backdrop-filter: blur(12px);
      }

      button {
        min-width: 42px;
        padding: 0 11px;
        color: #172033;
        font-size: 14px;
        font-weight: 750;
        cursor: pointer;
      }

      button:hover {
        background: rgba(255, 255, 255, .96);
      }

      #stats {
        margin-left: auto;
        padding: 0 12px;
        color: #172033;
        font-size: 13px;
        font-weight: 700;
      }
    </style>

    <script>
      (() => {
        const root = document.querySelector(".galton-shell");
        const config = JSON.parse(root.dataset.config);
        const stage = root.querySelector(".stage");
        const canvas = root.querySelector("#galton-canvas");
        const ctx = canvas.getContext("2d");
        const playPause = root.querySelector("#play-pause");
        const resetButton = root.querySelector("#reset");
        const burstButton = root.querySelector("#burst");
        const stats = root.querySelector("#stats");

        const TWO_PI = Math.PI * 2;
        const rows = config.rows;
        const bins = rows + 1;
        let counts = new Array(bins).fill(0);
        let balls = [];
        let running = true;
        let dropped = 0;
        let targetBalls = config.totalBalls;
        let landed = 0;
        let spawnCredit = 0;
        let lastTime = performance.now();
        let animationId = null;

        stage.style.setProperty("--board-width", `${config.boardWidth}px`);
        stage.style.setProperty("--board-height", `${config.boardHeight}px`);
        stage.style.setProperty("--background", config.backgroundColor);

        function resizeCanvas() {
          const rect = canvas.getBoundingClientRect();
          const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
          const width = Math.max(320, Math.round(rect.width * dpr));
          const height = Math.max(420, Math.round(rect.height * dpr));
          if (canvas.width !== width || canvas.height !== height) {
            canvas.width = width;
            canvas.height = height;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          }
        }

        function boardGeometry() {
          const rect = canvas.getBoundingClientRect();
          const width = rect.width;
          const height = rect.height;
          const top = 58;
          const bottomPad = 122;
          const usableHeight = Math.max(240, height - top - bottomPad);
          const rowGap = usableHeight / Math.max(1, rows);
          const maxSpacing = (width - 78) / Math.max(1, rows + 1);
          const pegSpacing = Math.min(config.pegSpacing, maxSpacing);
          const center = width / 2;
          const histogramTop = top + usableHeight + 24;
          const histogramBottom = height - 54;
          const binWidth = Math.min(pegSpacing, (width - 58) / bins);
          return { width, height, top, rowGap, pegSpacing, center, histogramTop, histogramBottom, binWidth };
        }

        function makePath() {
          const geom = boardGeometry();
          const points = [{ x: geom.center, y: 24 }];
          let rights = 0;

          for (let row = 1; row <= rows; row += 1) {
            if (Math.random() < config.rightBias) rights += 1;
            const x = geom.center + (rights - row / 2) * geom.pegSpacing;
            const y = geom.top + (row - 1) * geom.rowGap;
            points.push({ x, y });
          }

          const bin = rights;
          const finalX = geom.center + (bin - rows / 2) * geom.pegSpacing;
          const finalY = geom.histogramTop - 12;
          points.push({ x: finalX, y: finalY });

          return { points, bin };
        }

        function spawnBall(extraDelay = 0) {
          if (dropped >= targetBalls) return;
          const path = makePath();
          const now = performance.now();
          balls.push({
            path: path.points,
            bin: path.bin,
            start: now + extraDelay,
            duration: Math.max(900, rows * 190 / config.speed),
            hue: (dropped * 17 + rows * 11) % 360,
          });
          dropped += 1;
        }

        function resetSimulation() {
          counts = new Array(bins).fill(0);
          balls = [];
          dropped = 0;
          landed = 0;
          spawnCredit = 0;
          targetBalls = config.totalBalls;
          lastTime = performance.now();
        }

        function ease(t) {
          return 0.5 - Math.cos(Math.max(0, Math.min(1, t)) * Math.PI) / 2;
        }

        function ballPosition(ball, now) {
          const progress = Math.max(0, Math.min(1, (now - ball.start) / ball.duration));
          const span = ball.path.length - 1;
          const rawSegment = progress * span;
          const index = Math.min(span - 1, Math.floor(rawSegment));
          const local = ease(rawSegment - index);
          const a = ball.path[index];
          const b = ball.path[index + 1];
          const x = a.x + (b.x - a.x) * local;
          const y = a.y + (b.y - a.y) * local + Math.sin(local * Math.PI) * config.dropArc;
          return { x, y, done: progress >= 1 };
        }

        function ballColor(ball) {
          if (config.colorMode === "Spectrum") {
            return `hsl(${ball.hue}, 82%, 52%)`;
          }
          if (config.colorMode === "By bin") {
            const hue = 205 + (ball.bin / Math.max(1, rows)) * 120;
            return `hsl(${hue}, 74%, 46%)`;
          }
          return config.ballColor;
        }

        function combination(n, k) {
          if (k < 0 || k > n) return 0;
          k = Math.min(k, n - k);
          let result = 1;
          for (let i = 1; i <= k; i += 1) {
            result = result * (n - k + i) / i;
          }
          return result;
        }

        function drawPegs(geom) {
          ctx.save();
          ctx.fillStyle = config.pegColor;
          ctx.strokeStyle = "rgba(23, 32, 51, .22)";
          ctx.lineWidth = 1.2;

          for (let row = 0; row < rows; row += 1) {
            const count = row + 1;
            const y = geom.top + row * geom.rowGap;
            for (let col = 0; col < count; col += 1) {
              const x = geom.center + (col - row / 2) * geom.pegSpacing;
              ctx.beginPath();
              ctx.arc(x, y, config.pegRadius, 0, TWO_PI);
              ctx.fill();
              ctx.stroke();
            }
          }

          ctx.restore();
        }

        function drawGuides(geom) {
          ctx.save();
          ctx.strokeStyle = "rgba(23, 32, 51, .22)";
          ctx.lineWidth = 2;
          ctx.beginPath();
          ctx.moveTo(geom.center - geom.pegSpacing * 1.2, 24);
          ctx.lineTo(geom.center - geom.pegSpacing * .24, geom.top - 12);
          ctx.moveTo(geom.center + geom.pegSpacing * 1.2, 24);
          ctx.lineTo(geom.center + geom.pegSpacing * .24, geom.top - 12);
          ctx.stroke();

          const left = geom.center - rows / 2 * geom.pegSpacing - geom.binWidth / 2;
          const base = geom.histogramBottom;
          ctx.strokeStyle = "rgba(23, 32, 51, .18)";
          ctx.lineWidth = 1;
          for (let i = 0; i <= bins; i += 1) {
            const x = left + i * geom.binWidth;
            ctx.beginPath();
            ctx.moveTo(x, geom.histogramTop - 8);
            ctx.lineTo(x, base);
            ctx.stroke();
          }
          ctx.restore();
        }

        function drawHistogram(geom) {
          const maxCount = Math.max(1, ...counts);
          const left = geom.center - rows / 2 * geom.pegSpacing - geom.binWidth / 2;
          const height = Math.max(40, geom.histogramBottom - geom.histogramTop);

          ctx.save();
          for (let i = 0; i < bins; i += 1) {
            const barHeight = counts[i] / maxCount * height;
            const x = left + i * geom.binWidth + 3;
            const y = geom.histogramBottom - barHeight;
            const hue = 202 + (i / Math.max(1, bins - 1)) * 116;
            ctx.fillStyle = config.colorMode === "By bin" ? `hsl(${hue}, 76%, 45%)` : config.histogramColor;
            ctx.globalAlpha = 0.84;
            ctx.fillRect(x, y, Math.max(2, geom.binWidth - 6), barHeight);
          }
          ctx.globalAlpha = 1;

          if (config.showCurve && landed > 3) {
            const p = config.rightBias;
            let maxExpected = 0;
            const expected = counts.map((_, k) => {
              const value = landed * combination(rows, k) * Math.pow(p, k) * Math.pow(1 - p, rows - k);
              maxExpected = Math.max(maxExpected, value);
              return value;
            });

            ctx.beginPath();
            expected.forEach((value, k) => {
              const x = left + k * geom.binWidth + geom.binWidth / 2;
              const y = geom.histogramBottom - value / Math.max(1, maxExpected) * height;
              if (k === 0) ctx.moveTo(x, y);
              else ctx.lineTo(x, y);
            });
            ctx.strokeStyle = "rgba(18, 28, 46, .8)";
            ctx.lineWidth = 2.5;
            ctx.stroke();
          }

          ctx.restore();
        }

        function drawBalls(geom, now) {
          const active = [];
          for (const ball of balls) {
            if (now < ball.start) {
              active.push(ball);
              continue;
            }
            const position = ballPosition(ball, now);
            if (position.done) {
              counts[ball.bin] += 1;
              landed += 1;
              continue;
            }

            ctx.save();
            ctx.beginPath();
            ctx.arc(position.x, position.y, config.ballRadius, 0, TWO_PI);
            ctx.fillStyle = ballColor(ball);
            ctx.shadowColor = "rgba(23, 32, 51, .24)";
            ctx.shadowBlur = 7;
            ctx.shadowOffsetY = 2;
            ctx.fill();
            ctx.restore();
            active.push(ball);
          }
          balls = active;
        }

        function drawFrame(now) {
          resizeCanvas();
          const geom = boardGeometry();
          const elapsed = Math.min(120, now - lastTime);
          lastTime = now;

          if (running) {
            spawnCredit += config.dropRate * elapsed / 1000;
            while (spawnCredit >= 1 && dropped < targetBalls) {
              spawnBall();
              spawnCredit -= 1;
            }
          }

          ctx.clearRect(0, 0, geom.width, geom.height);
          ctx.fillStyle = config.backgroundColor;
          ctx.fillRect(0, 0, geom.width, geom.height);
          drawGuides(geom);
          drawPegs(geom);
          drawHistogram(geom);
          drawBalls(geom, now);

          playPause.innerHTML = running ? "&#10074;&#10074;" : "&#9654;";
          playPause.setAttribute("aria-label", running ? "Pause simulation" : "Resume simulation");
          stats.textContent = `${landed} landed / ${targetBalls} balls`;

          animationId = requestAnimationFrame(drawFrame);
        }

        playPause.addEventListener("click", () => {
          running = !running;
        });

        resetButton.addEventListener("click", () => {
          resetSimulation();
          running = true;
        });

        burstButton.addEventListener("click", () => {
          targetBalls += 50;
          for (let i = 0; i < 8; i += 1) {
            spawnBall(i * 60);
          }
          running = true;
        });

        window.addEventListener("resize", resizeCanvas);
        resizeCanvas();
        animationId = requestAnimationFrame(drawFrame);

        window.addEventListener("pagehide", () => {
          if (animationId) cancelAnimationFrame(animationId);
        });
      })();
    </script>
    """
    return dedent(template).replace("__CONFIG__", config_json)


def render_board(html_doc: str, height: int) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html_doc, height=height, width="stretch")
        return

    import streamlit.components.v1 as components

    components.html(html_doc, height=height, scrolling=False)


st.title("Galton Board Works")

with st.sidebar:
    st.header("Board")
    board_width = st.slider("Width", 520, 1040, 820, 20)
    board_height = st.slider("Height", 520, 900, 700, 20)
    rows = st.slider("Rows", 6, 18, 12)
    peg_spacing = st.slider("Peg spacing", 26, 74, 44)
    peg_radius = st.slider("Peg size", 2, 8, 4)

    st.header("Balls")
    total_balls = st.slider("Balls", 50, 2500, 600, 50)
    drop_rate = st.slider("Drop rate", 2, 80, 22)
    speed = st.slider("Fall speed", 1, 8, 4)
    ball_radius = st.slider("Ball size", 3, 10, 5)
    right_bias = st.slider("Right bounce chance", 0, 100, 50) / 100

    st.header("Color")
    background_color = st.color_picker("Background", "#f7fbff")
    peg_color = st.color_picker("Pegs", "#26364f")
    ball_color = st.color_picker("Balls", "#d94738")
    histogram_color = st.color_picker("Histogram", "#2b8a8a")
    color_mode = st.radio("Ball color mode", ["Classic", "Spectrum", "By bin"], horizontal=True)
    show_curve = st.toggle("Show expected curve", value=True)


config = {
    "boardWidth": board_width,
    "boardHeight": board_height,
    "rows": rows,
    "pegSpacing": peg_spacing,
    "pegRadius": peg_radius,
    "totalBalls": total_balls,
    "dropRate": drop_rate,
    "speed": speed,
    "ballRadius": ball_radius,
    "rightBias": right_bias,
    "backgroundColor": background_color,
    "pegColor": peg_color,
    "ballColor": ball_color,
    "histogramColor": histogram_color,
    "colorMode": color_mode,
    "showCurve": show_curve,
    "dropArc": 12,
}

left, right = st.columns([0.74, 0.26], vertical_alignment="top")

with left:
    render_board(build_board(config), height=board_height + 46)

with right:
    expected_center = rows * right_bias
    spread = (rows * right_bias * (1 - right_bias)) ** 0.5
    st.subheader("Run")
    st.metric("Rows", rows)
    st.metric("Expected bin", f"{expected_center:.1f}")
    st.metric("Spread", f"{spread:.2f}")
    st.caption("Use reset for a clean run after changing controls.")
