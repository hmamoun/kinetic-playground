import json
import random
from textwrap import dedent

import streamlit as st

st.set_page_config(
    page_title="Machine Learning Lab",
    page_icon="🧠",
    layout="wide",
)


def new_seed() -> int:
    return random.SystemRandom().randint(1, 999_999_999)


if "ml_seed" not in st.session_state:
    st.session_state.ml_seed = new_seed()


DATASET_INFO = {
    "xor": (
        "XOR quadrants",
        "Four clusters arranged so the two classes alternate diagonally. No straight line can ever "
        "separate them — a single-layer network is mathematically incapable of solving this. Watch the "
        "hidden layer bend the boundary into an X shape to carve out the diagonal quadrants.",
    ),
    "circles": (
        "Concentric circles",
        "One class forms a ring around the other. A hidden layer with only two or three neurons already "
        "learns to draw a closed loop instead of a straight line — something a plain linear model can't do.",
    ),
    "spirals": (
        "Two spirals",
        "The classic hard case: two interleaved spiral arms with no simple separating shape. This one "
        "usually needs more hidden neurons and more training time — try raising both if it won't converge.",
    ),
    "blobs": (
        "Two blobs",
        "Two well-separated clusters. Almost any line through the middle works, so this is the easy "
        "baseline — a good way to confirm the network and learning rate are behaving before trying "
        "something harder.",
    ),
}


def build_ml_view(payload: dict) -> str:
    payload_json = json.dumps(payload).replace("<", "\\u003c")

    return dedent(
        """
        <div class="ml-shell">
          <div class="ml-controls">
            <button id="ml-play-pause" type="button">Pause</button>
            <button id="ml-step" type="button">Step</button>
            <button id="ml-reset" type="button">Reset weights</button>
            <span id="ml-status" class="ml-status"></span>
          </div>

          <div class="ml-panels">
            <div class="ml-panel ml-stage-wrap">
              <div class="ml-label">Decision Boundary</div>
              <canvas id="ml-stage-canvas"></canvas>
              <div class="ml-legend">
                <span><i class="ml-swatch" style="background:#3b82f6"></i>Class 0</span>
                <span><i class="ml-swatch" style="background:#f97316"></i>Class 1</span>
              </div>
            </div>

            <div class="ml-panel ml-loss-wrap">
              <div class="ml-label">Training Loss</div>
              <canvas id="ml-loss-canvas"></canvas>
            </div>
          </div>
        </div>

        <script id="ml-data" type="application/json">%s</script>

        <style>
          .ml-shell {
            width: 100%%;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }

          .ml-controls {
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 12px;
            flex-wrap: wrap;
          }

          .ml-controls button {
            padding: 6px 16px;
            border-radius: 999px;
            border: 1px solid rgba(23, 32, 51, .18);
            background: #172033;
            color: #f4f6fb;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
          }

          .ml-controls button:hover {
            background: #232f47;
          }

          .ml-status {
            font-size: 13px;
            color: #475467;
          }

          .ml-panels {
            display: flex;
            gap: 14px;
            flex-wrap: wrap;
          }

          .ml-panel {
            border: 1px solid rgba(23, 32, 51, .14);
            border-radius: 8px;
            background: rgba(255, 255, 255, .6);
            padding: 10px 14px;
          }

          .ml-stage-wrap {
            flex: 1 1 420px;
          }

          .ml-loss-wrap {
            flex: 1 1 260px;
          }

          .ml-label {
            font-size: 12px;
            font-weight: 700;
            color: #475467;
            margin-bottom: 6px;
            text-transform: uppercase;
            letter-spacing: .03em;
          }

          #ml-stage-canvas {
            width: 100%%;
            aspect-ratio: 1;
            display: block;
            border-radius: 6px;
          }

          #ml-loss-canvas {
            width: 100%%;
            height: 260px;
            display: block;
          }

          .ml-legend {
            display: flex;
            gap: 14px;
            margin-top: 8px;
            font-size: 12px;
            color: #475467;
          }

          .ml-legend span {
            display: inline-flex;
            align-items: center;
            gap: 6px;
          }

          .ml-swatch {
            width: 10px;
            height: 10px;
            border-radius: 999px;
            display: inline-block;
          }
        </style>

        <script>
          (() => {
            const payload = JSON.parse(document.getElementById("ml-data").textContent);
            const {
              datasetType, pointsPerClass, noise, seed,
              hiddenNeurons, activationName, learningRate, maxEpochs,
            } = payload;

            const stageCanvas = document.getElementById("ml-stage-canvas");
            const stageCtx = stageCanvas.getContext("2d");
            const lossCanvas = document.getElementById("ml-loss-canvas");
            const lossCtx = lossCanvas.getContext("2d");
            const playPauseButton = document.getElementById("ml-play-pause");
            const stepButton = document.getElementById("ml-step");
            const resetButton = document.getElementById("ml-reset");
            const statusLabel = document.getElementById("ml-status");

            const HEATMAP_SIZE = 70;
            const heatCanvas = document.createElement("canvas");
            heatCanvas.width = HEATMAP_SIZE;
            heatCanvas.height = HEATMAP_SIZE;
            const heatCtx = heatCanvas.getContext("2d");

            const COLOR_A = [59, 130, 246];
            const COLOR_B = [249, 115, 22];
            const EPOCHS_PER_FRAME = 3;
            const CONVERGED_LOSS = 0.03;

            function seededRandom(seedValue) {
              let value = seedValue >>> 0;
              return function random() {
                value += 0x6D2B79F5;
                let next = value;
                next = Math.imul(next ^ next >>> 15, next | 1);
                next ^= next + Math.imul(next ^ next >>> 7, next | 61);
                return ((next ^ next >>> 14) >>> 0) / 4294967296;
              };
            }

            function gaussian(random) {
              const u1 = Math.max(1e-9, random());
              const u2 = random();
              return Math.sqrt(-2 * Math.log(u1)) * Math.cos(2 * Math.PI * u2);
            }

            function buildDataset(random) {
              const points = [];
              const spread = 0.16 + noise * 0.35;

              if (datasetType === "xor") {
                const corners = [
                  { x: 0.5, y: 0.5, label: 0 },
                  { x: -0.5, y: -0.5, label: 0 },
                  { x: 0.5, y: -0.5, label: 1 },
                  { x: -0.5, y: 0.5, label: 1 },
                ];
                corners.forEach((corner) => {
                  for (let i = 0; i < pointsPerClass / 2; i += 1) {
                    points.push({
                      x: corner.x + gaussian(random) * spread,
                      y: corner.y + gaussian(random) * spread,
                      label: corner.label,
                    });
                  }
                });
              } else if (datasetType === "circles") {
                for (let cls = 0; cls < 2; cls += 1) {
                  const radius = cls === 0 ? 0.35 : 0.9;
                  for (let i = 0; i < pointsPerClass; i += 1) {
                    const angle = random() * Math.PI * 2;
                    const r = radius + gaussian(random) * (0.06 + noise * 0.22);
                    points.push({ x: r * Math.cos(angle), y: r * Math.sin(angle), label: cls });
                  }
                }
              } else if (datasetType === "spirals") {
                for (let cls = 0; cls < 2; cls += 1) {
                  const sign = cls === 0 ? 1 : -1;
                  for (let i = 0; i < pointsPerClass; i += 1) {
                    const t = i / pointsPerClass;
                    const angle = t * Math.PI * 4 * sign + (cls === 0 ? 0 : Math.PI);
                    const radius = t * 0.85 + 0.06;
                    const jitter = noise * 0.3;
                    points.push({
                      x: radius * Math.cos(angle) + gaussian(random) * jitter,
                      y: radius * Math.sin(angle) + gaussian(random) * jitter,
                      label: cls,
                    });
                  }
                }
              } else {
                const centers = [{ x: -0.5, y: 0 }, { x: 0.5, y: 0 }];
                for (let cls = 0; cls < 2; cls += 1) {
                  for (let i = 0; i < pointsPerClass; i += 1) {
                    points.push({
                      x: centers[cls].x + gaussian(random) * (0.18 + noise * 0.4),
                      y: centers[cls].y + gaussian(random) * (0.18 + noise * 0.4),
                      label: cls,
                    });
                  }
                }
              }
              return points;
            }

            function activate(z) {
              return activationName === "relu" ? Math.max(0, z) : Math.tanh(z);
            }

            function activateDerivative(z, a) {
              return activationName === "relu" ? (z > 0 ? 1 : 0) : 1 - a * a;
            }

            let W1;
            let b1;
            let W2;
            let b2;
            let epoch = 0;
            let lastLoss = 1;
            let lastAccuracy = 0;
            let lossHistory = [];
            let running = true;
            let animationId = null;
            const setupRandom = seededRandom(seed);
            const dataset = buildDataset(setupRandom);

            function initNetwork() {
              const initRandom = seededRandom(seed + 1);
              W1 = [new Array(hiddenNeurons), new Array(hiddenNeurons)];
              for (let h = 0; h < hiddenNeurons; h += 1) {
                W1[0][h] = (initRandom() * 2 - 1) * 0.8;
                W1[1][h] = (initRandom() * 2 - 1) * 0.8;
              }
              b1 = new Array(hiddenNeurons).fill(0);
              W2 = new Array(hiddenNeurons);
              for (let h = 0; h < hiddenNeurons; h += 1) W2[h] = (initRandom() * 2 - 1) * 0.8;
              b2 = 0;
              epoch = 0;
              lastLoss = 1;
              lastAccuracy = 0;
              lossHistory = [];
            }

            function forward(x, y) {
              const z1 = new Array(hiddenNeurons);
              const a1 = new Array(hiddenNeurons);
              for (let h = 0; h < hiddenNeurons; h += 1) {
                z1[h] = x * W1[0][h] + y * W1[1][h] + b1[h];
                a1[h] = activate(z1[h]);
              }
              let z2 = b2;
              for (let h = 0; h < hiddenNeurons; h += 1) z2 += a1[h] * W2[h];
              const p = 1 / (1 + Math.exp(-z2));
              return { z1, a1, p };
            }

            function trainEpoch() {
              const n = dataset.length;
              const gW1 = [new Array(hiddenNeurons).fill(0), new Array(hiddenNeurons).fill(0)];
              const gb1 = new Array(hiddenNeurons).fill(0);
              const gW2 = new Array(hiddenNeurons).fill(0);
              let gb2 = 0;
              let totalLoss = 0;
              let correct = 0;
              const eps = 1e-7;

              for (const point of dataset) {
                const { z1, a1, p } = forward(point.x, point.y);
                const yTrue = point.label;
                totalLoss += -(yTrue * Math.log(p + eps) + (1 - yTrue) * Math.log(1 - p + eps));
                if ((p >= 0.5 ? 1 : 0) === yTrue) correct += 1;

                const dz2 = (p - yTrue) / n;
                gb2 += dz2;
                for (let h = 0; h < hiddenNeurons; h += 1) {
                  gW2[h] += a1[h] * dz2;
                  const da1 = dz2 * W2[h];
                  const dz1 = da1 * activateDerivative(z1[h], a1[h]);
                  gW1[0][h] += point.x * dz1;
                  gW1[1][h] += point.y * dz1;
                  gb1[h] += dz1;
                }
              }

              for (let h = 0; h < hiddenNeurons; h += 1) {
                W1[0][h] -= learningRate * gW1[0][h];
                W1[1][h] -= learningRate * gW1[1][h];
                b1[h] -= learningRate * gb1[h];
                W2[h] -= learningRate * gW2[h];
              }
              b2 -= learningRate * gb2;

              epoch += 1;
              lastLoss = totalLoss / n;
              lastAccuracy = correct / n;
              lossHistory.push(lastLoss);
            }

            function lerp(a, b, t) {
              return a + (b - a) * t;
            }

            function renderHeatmap() {
              const imageData = heatCtx.createImageData(HEATMAP_SIZE, HEATMAP_SIZE);
              const data = imageData.data;
              for (let gy = 0; gy < HEATMAP_SIZE; gy += 1) {
                const ny = 1 - (gy / (HEATMAP_SIZE - 1)) * 2;
                for (let gx = 0; gx < HEATMAP_SIZE; gx += 1) {
                  const nx = (gx / (HEATMAP_SIZE - 1)) * 2 - 1;
                  const { p } = forward(nx, ny);
                  const idx = (gy * HEATMAP_SIZE + gx) * 4;
                  data[idx] = lerp(COLOR_A[0], COLOR_B[0], p);
                  data[idx + 1] = lerp(COLOR_A[1], COLOR_B[1], p);
                  data[idx + 2] = lerp(COLOR_A[2], COLOR_B[2], p);
                  data[idx + 3] = 255;
                }
              }
              heatCtx.putImageData(imageData, 0, 0);
            }

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

            function renderStage() {
              const { width, height } = setupCanvas(stageCanvas);
              stageCtx.clearRect(0, 0, width, height);
              stageCtx.drawImage(heatCanvas, 0, 0, HEATMAP_SIZE, HEATMAP_SIZE, 0, 0, width, height);

              dataset.forEach((point) => {
                const px = ((point.x + 1) / 2) * width;
                const py = ((1 - point.y) / 2) * height;
                stageCtx.beginPath();
                stageCtx.arc(px, py, 4, 0, Math.PI * 2);
                stageCtx.fillStyle = point.label === 0 ? "#1d4ed8" : "#c2410c";
                stageCtx.fill();
                stageCtx.lineWidth = 1.2;
                stageCtx.strokeStyle = "rgba(255,255,255,.85)";
                stageCtx.stroke();
              });
            }

            function renderLossChart() {
              const { ctx, width, height } = setupCanvas(lossCanvas);
              ctx.clearRect(0, 0, width, height);

              ctx.strokeStyle = "rgba(23, 32, 51, .18)";
              ctx.lineWidth = 1;
              ctx.beginPath();
              ctx.moveTo(0, height - 1);
              ctx.lineTo(width, height - 1);
              ctx.stroke();

              if (lossHistory.length < 2) return;
              const maxLoss = Math.max(...lossHistory, 0.1);

              ctx.strokeStyle = "#172033";
              ctx.lineWidth = 2;
              ctx.lineJoin = "round";
              ctx.beginPath();
              lossHistory.forEach((loss, i) => {
                const x = (i / (maxEpochs - 1)) * width;
                const y = height - (loss / maxLoss) * height;
                if (i === 0) ctx.moveTo(x, y);
                else ctx.lineTo(x, y);
              });
              ctx.stroke();
            }

            function updateStatus() {
              statusLabel.textContent =
                `Epoch ${epoch} / ${maxEpochs} · loss ${lastLoss.toFixed(4)} · ` +
                `accuracy ${(lastAccuracy * 100).toFixed(0)}%%`;
            }

            function renderAll() {
              renderHeatmap();
              renderStage();
              renderLossChart();
              updateStatus();
            }

            function animate() {
              if (running) {
                for (let i = 0; i < EPOCHS_PER_FRAME && epoch < maxEpochs; i += 1) {
                  trainEpoch();
                }
                if (epoch >= maxEpochs || lastLoss <= CONVERGED_LOSS) {
                  running = false;
                  playPauseButton.textContent = "Play";
                }
                renderAll();
              }
              animationId = requestAnimationFrame(animate);
            }

            playPauseButton.addEventListener("click", () => {
              if (!running && epoch >= maxEpochs) {
                initNetwork();
              }
              running = !running;
              playPauseButton.textContent = running ? "Pause" : "Play";
            });

            stepButton.addEventListener("click", () => {
              running = false;
              playPauseButton.textContent = "Play";
              if (epoch < maxEpochs) trainEpoch();
              renderAll();
            });

            resetButton.addEventListener("click", () => {
              initNetwork();
              running = true;
              playPauseButton.textContent = "Pause";
              renderAll();
            });

            window.addEventListener("resize", renderAll);
            window.addEventListener("pagehide", () => {
              if (animationId) cancelAnimationFrame(animationId);
            });

            initNetwork();
            renderAll();
            animate();
          })();
        </script>
        """
    ) % payload_json


def render_ml_view(html_doc: str, height: int) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html_doc, height=height, width="stretch")
        return

    import streamlit.components.v1 as components

    components.html(html_doc, height=height, scrolling=False)


st.title("Machine Learning Lab")
st.write(
    "Watch a tiny neural network learn a 2D classification problem, live. Every epoch of gradient "
    "descent is drawn as it happens — the colored background is the network's current decision "
    "boundary, and it visibly reshapes itself as training progresses."
)

with st.sidebar:
    st.header("Dataset")
    if st.button("New dataset", width="stretch"):
        st.session_state.ml_seed = new_seed()

    seed = st.number_input(
        "Dataset seed",
        min_value=1,
        max_value=999_999_999,
        value=int(st.session_state.ml_seed),
        step=1,
    )
    st.session_state.ml_seed = int(seed)

    dataset_labels = {
        "XOR quadrants": "xor",
        "Concentric circles": "circles",
        "Two spirals": "spirals",
        "Two blobs": "blobs",
    }
    dataset_label = st.selectbox("Shape", list(dataset_labels), index=0)
    dataset_key = dataset_labels[dataset_label]

    points_per_class = st.slider("Points per class", 20, 150, 60, 5)
    noise = st.slider("Noise", 0.0, 0.5, 0.08, 0.01)

    st.header("Network")
    hidden_neurons = st.slider("Hidden neurons", 2, 16, 6)
    activation_label = st.radio("Activation", ["tanh", "relu"], horizontal=True)
    learning_rate = st.slider("Learning rate", 0.05, 3.0, 0.8, 0.05)
    max_epochs = st.slider("Max epochs", 200, 3000, 800, 100)

dataset_title, dataset_description = DATASET_INFO[dataset_key]
st.caption(f"**{dataset_title}** — {dataset_description}")

payload = {
    "datasetType": dataset_key,
    "pointsPerClass": points_per_class,
    "noise": noise,
    "seed": int(seed),
    "hiddenNeurons": hidden_neurons,
    "activationName": activation_label,
    "learningRate": learning_rate,
    "maxEpochs": max_epochs,
}

render_ml_view(build_ml_view(payload), height=620)

st.divider()
st.header("How the learning works, step by step")
st.caption(
    f"A plain-language walkthrough tied to the network currently on screen — **{dataset_title}**, "
    f"**{hidden_neurons}** hidden neurons, **{activation_label}** activation, "
    f"learning rate **{learning_rate}**."
)

st.subheader("1. A network is just a chain of two simple steps")
st.write(
    "Every point (x, y) on the chart passes through two layers. Each hidden neuron computes a weighted "
    "sum of x and y, passes it through a nonlinear activation function, and the output layer combines "
    "all those hidden results into a single probability."
)
st.latex(r"z^{(1)}_h = w_{x,h}\,x + w_{y,h}\,y + b_h, \qquad a^{(1)}_h = \text{activation}(z^{(1)}_h)")
st.latex(r"p = \sigma\!\left(\sum_{h=1}^{H} w_h\, a^{(1)}_h + b\right)")
st.markdown(
    f"On screen right now, H = **{hidden_neurons}** hidden neurons, and the activation function is "
    f"**{activation_label}**. The nonlinearity is the whole point: without it, stacking layers would "
    "collapse back into a single straight line, unable to solve shapes like XOR or spirals."
)

st.subheader("2. Score the guess with a loss function")
st.write(
    "For every point, the network's output p is a probability that the point belongs to class 1. "
    "Binary cross-entropy compares that probability against the true label and penalizes confident "
    "wrong answers heavily:"
)
st.latex(r"\mathcal{L} = -\frac{1}{N}\sum_{n=1}^{N}\Big[y_n \log p_n + (1-y_n)\log(1-p_n)\Big]")
st.write(
    "That single number — averaged over every training point — is the loss curve animating on the right "
    "of the lab. A falling curve means the network's probabilities are getting closer to the true labels."
)

st.subheader("3. Backpropagation: assign blame, then correct it")
st.write(
    "Gradient descent needs to know how much each individual weight contributed to the loss. "
    "Backpropagation computes that by working backward from the output error through the hidden layer, "
    "one derivative at a time:"
)
st.latex(r"\delta^{(2)} = p - y, \qquad \frac{\partial \mathcal{L}}{\partial w_h} = \delta^{(2)} \, a^{(1)}_h")
st.latex(
    r"\delta^{(1)}_h = \delta^{(2)} w_h \cdot \text{activation}'(z^{(1)}_h), "
    r"\qquad \frac{\partial \mathcal{L}}{\partial w_{x,h}} = \delta^{(1)}_h \, x"
)
st.markdown(
    f"Every weight is nudged in the direction that reduces the loss, scaled by the learning rate "
    f"(currently **{learning_rate}**):"
)
st.latex(r"w \leftarrow w - \eta \, \frac{\partial \mathcal{L}}{\partial w}")
st.write(
    "One full pass over every training point is a single epoch — the counter climbing in the status "
    "line above. Too small a learning rate and the boundary creeps along slowly; too large and it can "
    "overshoot and wobble instead of settling."
)

st.subheader("4. Why the dataset shape matters")
st.write(
    "A network with zero hidden neurons is just logistic regression — a single straight decision line. "
    "Every dataset in the sidebar is chosen to make that limitation obvious: XOR needs a bent boundary, "
    "circles need a closed loop, and spirals need the boundary to wind around itself. Watch the heatmap "
    "as it trains — the shape it eventually settles into is the network discovering the minimum "
    "complexity needed to separate the classes in front of it."
)
