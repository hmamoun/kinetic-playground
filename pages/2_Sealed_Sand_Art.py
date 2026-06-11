import html
import json
from pathlib import Path
from textwrap import dedent

import streamlit as st


st.set_page_config(
    page_title="Sealed Sand Art",
    page_icon="S",
    layout="wide",
)


PALETTES = {
    "Glacier blue": ["#f7fbff", "#9ed8ff", "#2c78d4", "#0c2f73", "#111827", "#d7b07b", "#ffffff", "#6388b5"],
    "Desert sunset": ["#fff2cf", "#f2bf6b", "#d97745", "#9f3650", "#44233d", "#f9fbff", "#45312a", "#efdfb8"],
    "Earth mineral": ["#f8f4e8", "#c8a36a", "#8e6c4a", "#465a63", "#1f2933", "#d8dde0", "#6e4b2f", "#bcc7bd"],
    "Aurora glass": ["#ecfeff", "#77e4d4", "#2ba7b8", "#31499f", "#171733", "#efc3ff", "#ffffff", "#5c6f86"],
}


DEFAULT_SETTINGS = {
    "diameter": 680,
    "liquid_thickness": 8,
    "show_glare": True,
    "sand_types": 5,
    "sand_amount": 34,
    "initial_mix_percent": 28,
    "air_amount": 9,
    "air_bubbles": 8,
    "bubble_scale_percent": 96,
    "rotation_step": 90,
    "initial_angle": 0,
    "speed": 4,
    "gravity_scale_percent": 100,
    "max_weight_difference_percent": 18,
    "resolution": 166,
    "seed": 24817,
    "palette_name": "Glacier blue",
    "liquid_color": "#e7f4ff",
    "air_color": "#ffffff",
}


def app_root() -> Path:
    path = Path(__file__).resolve()
    if path.parent.name.lower() == "pages":
        return path.parent.parent
    return path.parent


DEFAULTS_PATH = app_root() / "sealed_sand_art_defaults.json"


def clamp_setting(value: int, minimum: int, maximum: int) -> int:
    return max(minimum, min(maximum, int(value)))


def load_settings() -> dict:
    settings = DEFAULT_SETTINGS.copy()
    if DEFAULTS_PATH.exists():
        try:
            saved = json.loads(DEFAULTS_PATH.read_text(encoding="utf-8"))
            if isinstance(saved, dict):
                settings.update({key: saved[key] for key in settings if key in saved})
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            pass

    settings["diameter"] = clamp_setting(settings["diameter"], 460, 860)
    settings["liquid_thickness"] = clamp_setting(settings["liquid_thickness"], 1, 20)
    settings["sand_types"] = clamp_setting(settings["sand_types"], 2, 8)
    settings["sand_amount"] = clamp_setting(settings["sand_amount"], 8, 64)
    settings["initial_mix_percent"] = clamp_setting(settings["initial_mix_percent"], 0, 100)
    settings["air_amount"] = clamp_setting(settings["air_amount"], 1, 26)
    settings["air_bubbles"] = clamp_setting(settings["air_bubbles"], 1, 28)
    settings["bubble_scale_percent"] = clamp_setting(settings["bubble_scale_percent"], 60, 150)
    settings["rotation_step"] = clamp_setting(settings["rotation_step"], 15, 180)
    settings["initial_angle"] = clamp_setting(settings["initial_angle"], 0, 345)
    settings["speed"] = clamp_setting(settings["speed"], 1, 8)
    settings["gravity_scale_percent"] = clamp_setting(settings["gravity_scale_percent"], 10, 300)
    settings["max_weight_difference_percent"] = clamp_setting(settings["max_weight_difference_percent"], 0, 100)
    settings["resolution"] = clamp_setting(settings["resolution"], 110, 220)
    settings["seed"] = clamp_setting(settings["seed"], 1, 999999)
    settings["show_glare"] = bool(settings["show_glare"])
    settings["air_color"] = "#ffffff"

    if settings["palette_name"] not in PALETTES:
        settings["palette_name"] = DEFAULT_SETTINGS["palette_name"]

    return settings


def save_settings(settings: dict) -> None:
    DEFAULTS_PATH.write_text(json.dumps(settings, indent=2), encoding="utf-8")


def build_simulator(config: dict) -> str:
    config_json = html.escape(json.dumps(config), quote=True)
    template = """
    <div class="sand-art-shell" data-config="__CONFIG__">
      <div class="stage">
        <canvas id="sand-canvas"></canvas>
        <div class="hud">
          <button id="play-pause" type="button" aria-label="Pause simulation" title="Pause simulation">&#10074;&#10074;</button>
          <button id="rotate-left" type="button" aria-label="Rotate left" title="Rotate left">&#8634;</button>
          <button id="rotate-right" type="button" aria-label="Rotate right" title="Rotate right">&#8635;</button>
          <button id="reset" type="button" aria-label="Reset simulation" title="Reset simulation">Reset</button>
          <span id="stats"></span>
        </div>
      </div>
    </div>

    <style>
      .sand-art-shell {
        width: 100%;
        display: flex;
        justify-content: center;
        padding: 8px 0 18px;
        font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      }

      .stage {
        position: relative;
        width: min(100%, var(--stage-width));
        height: var(--stage-height);
        background:
          linear-gradient(135deg, rgba(255, 255, 255, .8), rgba(255, 255, 255, .22)),
          #f2f5f8;
        border: 1px solid rgba(24, 33, 54, .12);
        border-radius: 8px;
        box-shadow: 0 18px 48px rgba(22, 31, 56, .18);
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
        border: 1px solid rgba(25, 34, 58, .2);
        border-radius: 8px;
        background: rgba(255, 255, 255, .86);
        box-shadow: 0 8px 22px rgba(20, 27, 48, .14);
        backdrop-filter: blur(12px);
      }

      button {
        min-width: 42px;
        padding: 0 12px;
        color: #172033;
        font-size: 14px;
        font-weight: 750;
        cursor: pointer;
      }

      button:hover {
        background: rgba(255, 255, 255, .97);
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
        const root = document.querySelector(".sand-art-shell");
        const config = JSON.parse(root.dataset.config);
        const stage = root.querySelector(".stage");
        const canvas = root.querySelector("#sand-canvas");
        const ctx = canvas.getContext("2d");
        const playPause = root.querySelector("#play-pause");
        const rotateLeft = root.querySelector("#rotate-left");
        const rotateRight = root.querySelector("#rotate-right");
        const resetButton = root.querySelector("#reset");
        const stats = root.querySelector("#stats");

        const G = config.gridSize;
        const total = G * G;
        const outside = -9;
        const air = -1;
        const liquid = 0;
        const center = (G - 1) / 2;
        const radius = G * 0.48;
        const radiusSq = radius * radius;
        const palette = config.palette;
        const rng = mulberry32(config.seed);
        const density = buildDensities();

        let cells = new Int8Array(total);
        let airPressure = new Float32Array(total);
        let angle = config.initialAngle * Math.PI / 180;
        let running = true;
        let frame = 0;
        let movedRecently = 0;
        const airVisited = new Uint8Array(total);
        const floodQueue = new Int32Array(total);
        const clusterCells = new Int32Array(total);
        const neighborDx = [-1, 1, 0, 0];
        const neighborDy = [0, 0, -1, 1];

        const offscreen = document.createElement("canvas");
        offscreen.width = G;
        offscreen.height = G;
        const offCtx = offscreen.getContext("2d", { willReadFrequently: true });
        const image = offCtx.createImageData(G, G);

        stage.style.setProperty("--stage-width", `${config.stageWidth}px`);
        stage.style.setProperty("--stage-height", `${config.stageHeight}px`);

        function mulberry32(seed) {
          let value = seed >>> 0;
          return function random() {
            value += 0x6D2B79F5;
            let t = value;
            t = Math.imul(t ^ t >>> 15, t | 1);
            t ^= t + Math.imul(t ^ t >>> 7, t | 61);
            return ((t ^ t >>> 14) >>> 0) / 4294967296;
          };
        }

        function buildDensities() {
          const densityRandom = mulberry32((config.seed ^ 0x9E3779B9) >>> 0);
          const values = [0];
          for (let i = 1; i <= config.sandTypes; i += 1) {
            values.push(1 + densityRandom() * config.maxWeightDifference);
          }
          return values;
        }

        function idx(x, y) {
          return y * G + x;
        }

        function inCircle(x, y) {
          const dx = x - center;
          const dy = y - center;
          return dx * dx + dy * dy <= radiusSq;
        }

        function resizeCanvas() {
          const rect = canvas.getBoundingClientRect();
          const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
          const width = Math.max(420, Math.round(rect.width * dpr));
          const height = Math.max(520, Math.round(rect.height * dpr));
          if (canvas.width !== width || canvas.height !== height) {
            canvas.width = width;
            canvas.height = height;
            ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
          }
        }

        function gravity() {
          return { x: 0, y: 1 };
        }

        function sortedDirections(sign) {
          const g = gravity();
          const pull = Math.max(0.1, config.gravityScale);
          const dirs = [
            { x: -1, y: -1 }, { x: 0, y: -1 }, { x: 1, y: -1 },
            { x: -1, y: 0 },                    { x: 1, y: 0 },
            { x: -1, y: 1 },  { x: 0, y: 1 },  { x: 1, y: 1 },
          ];
          return dirs
            .map((d) => ({ ...d, score: sign * (d.x * g.x + d.y * g.y) * pull + rng() * 0.08 }))
            .filter((d) => d.score > 0.08)
            .sort((a, b) => b.score - a.score);
        }

        function rotateCellsBy(radians) {
          const rotated = new Int8Array(total);
          rotated.fill(outside);
          const cos = Math.cos(radians);
          const sin = Math.sin(radians);

          for (let y = 0; y < G; y += 1) {
            for (let x = 0; x < G; x += 1) {
              if (!inCircle(x, y)) continue;
              const dx = x - center;
              const dy = y - center;
              const sx = Math.round(center + dx * cos + dy * sin);
              const sy = Math.round(center - dx * sin + dy * cos);
              const target = idx(x, y);

              if (sx >= 0 && sx < G && sy >= 0 && sy < G && inCircle(sx, sy)) {
                rotated[target] = cells[idx(sx, sy)];
              } else {
                rotated[target] = liquid;
              }
            }
          }

          cells = rotated;
        }

        function setupCells() {
          cells.fill(outside);

          const inside = [];
          for (let y = 0; y < G; y += 1) {
            for (let x = 0; x < G; x += 1) {
              if (inCircle(x, y)) {
                const i = idx(x, y);
                cells[i] = liquid;
                inside.push({
                  i,
                  x,
                  y,
                  down: y - center,
                });
              }
            }
          }

          const sandTarget = Math.floor(inside.length * config.sandAmount / 100);
          inside
            .map((cell) => ({ ...cell, score: cell.down + rng() * radius * config.initialMix }))
            .sort((a, b) => b.score - a.score)
            .slice(0, sandTarget)
            .forEach((cell, rank) => {
              const band = Math.floor(rank / Math.max(1, sandTarget) * config.sandTypes);
              const type = 1 + Math.min(config.sandTypes - 1, Math.max(0, band + Math.floor(rng() * 2) - 1));
              cells[cell.i] = type;
            });

          const airTarget = Math.floor(inside.length * config.airAmount / 100);
          const eachBubble = Math.max(4, airTarget / Math.max(1, config.airBubbles));
          const bubbleRadius = Math.max(2.1, Math.sqrt(eachBubble / Math.PI) * config.bubbleScale);
          let placedAir = 0;

          for (let b = 0; b < config.airBubbles; b += 1) {
            const offset = (rng() - 0.5) * radius * 1.35;
            const topness = -radius * (0.54 + rng() * 0.22);
            const cx = center + offset;
            const cy = center + topness;
            const stretch = 1 + config.liquidThickness * 0.025;

            for (let y = Math.floor(cy - bubbleRadius * stretch - 2); y <= Math.ceil(cy + bubbleRadius * stretch + 2); y += 1) {
              for (let x = Math.floor(cx - bubbleRadius - 2); x <= Math.ceil(cx + bubbleRadius + 2); x += 1) {
                if (x < 0 || x >= G || y < 0 || y >= G || !inCircle(x, y)) continue;
                const dx = (x - cx) / bubbleRadius;
                const dy = (y - cy) / (bubbleRadius * stretch);
                if (dx * dx + dy * dy <= 1 + rng() * 0.08) {
                  const i = idx(x, y);
                  if (cells[i] !== outside && placedAir < airTarget) {
                    cells[i] = air;
                    placedAir += 1;
                  }
                }
              }
            }
          }

          let guard = 0;
          while (placedAir < airTarget && guard < inside.length * 3) {
            const cell = inside[Math.floor(rng() * inside.length)];
            if (cells[cell.i] === liquid && cell.down < 0) {
              cells[cell.i] = air;
              placedAir += 1;
            }
            guard += 1;
          }

          if (Math.abs(angle) > 0.0001) {
            rotateCellsBy(angle);
          }
        }

        function canSwapSand(a, b) {
          if (b === liquid) return true;
          if (b === air) return rng() < config.sandThroughAir;
          return false;
        }

        function tryMoveSand(x, y, i, dirs) {
          const type = cells[i];
          const normalizedWeight = density[type] - 1;
          const chance = Math.min(
            0.98,
            config.motionChance * config.gravityScale * (0.72 + normalizedWeight * 1.45)
          );
          if (rng() > chance) return false;

          for (const d of dirs) {
            const nx = x + d.x;
            const ny = y + d.y;
            if (nx < 0 || nx >= G || ny < 0 || ny >= G) continue;
            const j = idx(nx, ny);
            const other = cells[j];
            if (other === outside) continue;
            if (canSwapSand(type, other)) {
              cells[j] = type;
              cells[i] = other;
              return true;
            }
          }
          return false;
        }

        function refreshAirPressure() {
          airPressure.fill(0);
          airVisited.fill(0);

          for (let start = 0; start < total; start += 1) {
            if (cells[start] !== air || airVisited[start]) continue;

            let head = 0;
            let tail = 0;
            let count = 0;
            floodQueue[tail] = start;
            tail += 1;
            airVisited[start] = 1;

            while (head < tail) {
              const current = floodQueue[head];
              head += 1;
              clusterCells[count] = current;
              count += 1;

              const x = current % G;
              const y = Math.floor(current / G);

              for (let dir = 0; dir < 4; dir += 1) {
                const nx = x + neighborDx[dir];
                const ny = y + neighborDy[dir];
                if (nx < 0 || nx >= G || ny < 0 || ny >= G) continue;
                const next = idx(nx, ny);
                if (!airVisited[next] && cells[next] === air) {
                  airVisited[next] = 1;
                  floodQueue[tail] = next;
                  tail += 1;
                }
              }
            }

            const equivalentRadius = Math.sqrt(count / Math.PI);
            const pressure = equivalentRadius * config.gravityScale * (0.9 + config.airAmount * 0.018);
            for (let n = 0; n < count; n += 1) {
              airPressure[clusterCells[n]] = pressure;
            }
          }
        }

        function sandStackResistance(x, y) {
          let resistance = 0;
          for (let sy = y; sy >= 0 && inCircle(x, sy); sy -= 1) {
            const value = cells[idx(x, sy)];
            if (value <= 0) break;
            resistance += 0.72 + (density[value] - 1) * 1.65;
            if (resistance > 120) break;
          }
          return resistance;
        }

        function canAirLiftSand(x, y, pressure) {
          const resistance = sandStackResistance(x, y);
          const surplus = pressure - resistance;

          if (surplus <= 0) {
            return rng() < config.airThroughSand * 0.12;
          }

          const chance = Math.min(
            0.9,
            config.airThroughSand + (surplus / (surplus + resistance + 6)) * 0.72
          );
          return rng() < chance;
        }

        function tryMoveAir(x, y, i, dirs) {
          const pressure = airPressure[i] || 0.1;
          const chance = Math.min(
            0.98,
            config.airMobility * Math.sqrt(config.gravityScale) * (0.7 + Math.min(pressure, 14) * 0.035)
          );
          if (rng() > chance) return false;

          for (const d of dirs) {
            const nx = x + d.x;
            const ny = y + d.y;
            if (nx < 0 || nx >= G || ny < 0 || ny >= G) continue;
            const j = idx(nx, ny);
            const other = cells[j];
            if (other === outside) continue;
            if (other === liquid || (other > 0 && canAirLiftSand(nx, ny, pressure))) {
              cells[j] = air;
              cells[i] = other;
              return true;
            }
          }
          return false;
        }

        function physicsStep() {
          const sandDirs = sortedDirections(1);
          const airDirs = sortedDirections(-1);
          const attempts = Math.floor(total * config.simulationWork * Math.sqrt(config.gravityScale));
          let moved = 0;

          refreshAirPressure();

          for (let n = 0; n < attempts; n += 1) {
            const x = Math.floor(rng() * G);
            const y = Math.floor(rng() * G);
            const i = idx(x, y);
            const value = cells[i];
            if (value > 0) {
              if (tryMoveSand(x, y, i, sandDirs)) moved += 1;
            } else if (value === air) {
              if (tryMoveAir(x, y, i, airDirs)) moved += 1;
            }
          }

          movedRecently = movedRecently * 0.9 + moved * 0.1;
        }

        function hexToRgb(hex) {
          const normalized = hex.replace("#", "");
          return {
            r: parseInt(normalized.slice(0, 2), 16),
            g: parseInt(normalized.slice(2, 4), 16),
            b: parseInt(normalized.slice(4, 6), 16),
          };
        }

        const rgbPalette = palette.map(hexToRgb);
        const liquidRgb = hexToRgb(config.liquidColor);
        const airRgb = hexToRgb(config.airColor);

        function paintCells() {
          const data = image.data;
          for (let i = 0; i < total; i += 1) {
            const value = cells[i];
            const p = i * 4;
            if (value === outside) {
              data[p + 3] = 0;
            } else if (value === air) {
              data[p] = airRgb.r;
              data[p + 1] = airRgb.g;
              data[p + 2] = airRgb.b;
              data[p + 3] = 205;
            } else if (value === liquid) {
              data[p] = liquidRgb.r;
              data[p + 1] = liquidRgb.g;
              data[p + 2] = liquidRgb.b;
              data[p + 3] = 54;
            } else {
              const base = rgbPalette[(value - 1) % rgbPalette.length];
              const speckle = ((i * 13 + frame * 3) % 17) - 8;
              data[p] = Math.max(0, Math.min(255, base.r + speckle));
              data[p + 1] = Math.max(0, Math.min(255, base.g + speckle));
              data[p + 2] = Math.max(0, Math.min(255, base.b + speckle));
              data[p + 3] = 238;
            }
          }
          offCtx.putImageData(image, 0, 0);
        }

        function drawBase(width, height, cx, cy, r) {
          const baseTop = cy + r * 0.82;
          const baseHeight = height - baseTop - 18;
          ctx.save();
          ctx.fillStyle = "#050608";
          ctx.shadowColor = "rgba(0, 0, 0, .32)";
          ctx.shadowBlur = 18;
          ctx.shadowOffsetY = 9;
          ctx.fillRect(cx - r * 0.92, baseTop, r * 1.84, baseHeight);
          ctx.fillStyle = "rgba(255, 255, 255, .08)";
          ctx.fillRect(cx - r * 0.85, baseTop + 8, r * 1.7, 2);
          ctx.restore();
        }

        function drawGlass(width, height, cx, cy, r) {
          ctx.save();
          const liquidGradient = ctx.createRadialGradient(cx - r * 0.3, cy - r * 0.34, r * 0.1, cx, cy, r);
          liquidGradient.addColorStop(0, "rgba(255, 255, 255, .62)");
          liquidGradient.addColorStop(0.45, "rgba(210, 230, 245, .22)");
          liquidGradient.addColorStop(1, "rgba(85, 120, 145, .2)");

          ctx.beginPath();
          ctx.arc(cx, cy, r * 0.94, 0, Math.PI * 2);
          ctx.fillStyle = liquidGradient;
          ctx.fill();

          ctx.beginPath();
          ctx.arc(cx, cy, r * 1.01, 0, Math.PI * 2);
          ctx.strokeStyle = "#08090c";
          ctx.lineWidth = Math.max(16, r * 0.058);
          ctx.shadowColor = "rgba(0, 0, 0, .34)";
          ctx.shadowBlur = 10;
          ctx.stroke();

          ctx.shadowColor = "transparent";
          ctx.beginPath();
          ctx.arc(cx, cy, r * 0.94, 0, Math.PI * 2);
          ctx.strokeStyle = "rgba(255, 255, 255, .52)";
          ctx.lineWidth = Math.max(2, r * 0.009);
          ctx.stroke();

          if (config.showGlare) {
            ctx.beginPath();
            ctx.arc(cx - r * 0.07, cy - r * 0.05, r * 0.78, Math.PI * 1.08, Math.PI * 1.45);
            ctx.strokeStyle = "rgba(255, 255, 255, .42)";
            ctx.lineWidth = Math.max(3, r * 0.018);
            ctx.stroke();

            ctx.beginPath();
            ctx.arc(cx + r * 0.19, cy + r * 0.02, r * 0.68, Math.PI * 1.77, Math.PI * 1.96);
            ctx.strokeStyle = "rgba(255, 255, 255, .28)";
            ctx.lineWidth = Math.max(2, r * 0.011);
            ctx.stroke();
          }

          ctx.restore();
        }

        function drawScene() {
          resizeCanvas();
          const rect = canvas.getBoundingClientRect();
          const width = rect.width;
          const height = rect.height;
          const diameter = Math.min(config.diameter, width - 28, height - 96);
          const r = diameter / 2;
          const cx = width / 2;
          const cy = r + 20;
          const left = cx - r;
          const top = cy - r;

          ctx.clearRect(0, 0, width, height);

          const bg = ctx.createLinearGradient(0, 0, width, height);
          bg.addColorStop(0, "#ffffff");
          bg.addColorStop(1, "#e7edf3");
          ctx.fillStyle = bg;
          ctx.fillRect(0, 0, width, height);

          drawBase(width, height, cx, cy, r);

          ctx.save();
          ctx.beginPath();
          ctx.arc(cx, cy, r * 0.93, 0, Math.PI * 2);
          ctx.clip();
          ctx.fillStyle = config.liquidColor;
          ctx.globalAlpha = 0.55;
          ctx.fillRect(left, top, diameter, diameter);
          ctx.globalAlpha = 1;
          ctx.imageSmoothingEnabled = false;
          ctx.drawImage(offscreen, left, top, diameter, diameter);
          ctx.restore();

          drawGlass(width, height, cx, cy, r);

          const g = gravity();
          ctx.save();
          ctx.translate(cx, cy);
          ctx.rotate(angle);
          ctx.beginPath();
          ctx.moveTo(-r * 0.1, -r * 0.86);
          ctx.lineTo(0, -r * 0.79);
          ctx.lineTo(r * 0.1, -r * 0.86);
          ctx.strokeStyle = "rgba(20, 30, 45, .32)";
          ctx.lineWidth = 2;
          ctx.stroke();
          ctx.restore();

          stats.textContent = `${Math.round(angle * 180 / Math.PI) % 360} deg | flow ${Math.round(movedRecently)}`;
          playPause.innerHTML = running ? "&#10074;&#10074;" : "&#9654;";
          playPause.setAttribute("aria-label", running ? "Pause simulation" : "Resume simulation");
        }

        function tick() {
          frame += 1;
          if (running) {
            for (let s = 0; s < config.stepsPerFrame; s += 1) physicsStep();
          }
          paintCells();
          drawScene();
          requestAnimationFrame(tick);
        }

        function rotate(deltaDegrees) {
          const delta = deltaDegrees * Math.PI / 180;
          const fullTurn = Math.PI * 2;
          angle = (angle + delta) % fullTurn;
          if (angle < 0) angle += fullTurn;
          rotateCellsBy(delta);
          movedRecently += total * 0.04;
          running = true;
        }

        playPause.addEventListener("click", () => {
          running = !running;
        });

        rotateLeft.addEventListener("click", () => rotate(-config.rotationStep));
        rotateRight.addEventListener("click", () => rotate(config.rotationStep));
        resetButton.addEventListener("click", () => {
          setupCells();
          running = true;
        });

        canvas.addEventListener("click", (event) => {
          const rect = canvas.getBoundingClientRect();
          const x = event.clientX - rect.left;
          const y = event.clientY - rect.top;
          const diameter = Math.min(config.diameter, rect.width - 28, rect.height - 96);
          const r = diameter / 2;
          const cx = rect.width / 2;
          const cy = r + 20;
          const dx = x - cx;
          const dy = y - cy;
          if (dx * dx + dy * dy < r * r) {
            rotate(config.rotationStep);
          }
        });

        window.addEventListener("resize", resizeCanvas);
        setupCells();
        tick();
      })();
    </script>
    """
    return dedent(template).replace("__CONFIG__", config_json)


def render_simulator(html_doc: str, height: int) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html_doc, height=height, width="stretch")
        return

    import streamlit.components.v1 as components

    components.html(html_doc, height=height, scrolling=False)


st.title("Sealed Sand Art")

saved_settings = load_settings()
palette_names = list(PALETTES)

with st.sidebar:
    st.header("Glass")
    diameter = st.slider("Circle size", 460, 860, saved_settings["diameter"], 20)
    liquid_thickness = st.slider("Liquid thickness", 1, 20, saved_settings["liquid_thickness"])
    show_glare = st.toggle("Show glass glare", value=saved_settings["show_glare"])

    st.header("Sand")
    sand_types = st.slider("Sand grain types", 2, 8, saved_settings["sand_types"])
    sand_amount = st.slider("Amount of sand", 8, 64, saved_settings["sand_amount"])
    initial_mix_percent = st.slider("Initial layer mixing", 0, 100, saved_settings["initial_mix_percent"])
    initial_mix = initial_mix_percent / 100

    st.header("Air")
    air_amount = st.slider("Amount of air", 1, 26, saved_settings["air_amount"])
    air_bubbles = st.slider("Air bubbles formed", 1, 28, saved_settings["air_bubbles"])
    bubble_scale_percent = st.slider("Bubble size variation", 60, 150, saved_settings["bubble_scale_percent"])
    bubble_scale = bubble_scale_percent / 100

    st.header("Motion")
    rotation_step = st.slider("Rotate step", 15, 180, saved_settings["rotation_step"], 15)
    initial_angle = st.slider("Initial rotation", 0, 345, saved_settings["initial_angle"], 15)
    speed = st.slider("Simulation speed", 1, 8, saved_settings["speed"])
    gravity_scale_percent = st.slider("Gravity scale", 10, 300, saved_settings["gravity_scale_percent"], 10)
    resolution = st.slider("Simulation resolution", 110, 220, saved_settings["resolution"], 2)
    seed = st.number_input("Initial state seed", min_value=1, max_value=999999, value=saved_settings["seed"], step=1)

    st.header("Look")
    max_weight_difference_percent = st.slider(
        "Max grain weight difference",
        0,
        100,
        saved_settings["max_weight_difference_percent"],
        5,
    )
    palette_name = st.selectbox(
        "Sand palette",
        palette_names,
        index=palette_names.index(saved_settings["palette_name"]),
    )
    liquid_color = st.color_picker("Liquid tint", saved_settings["liquid_color"])
    air_color = "#ffffff"
    st.color_picker("Air bubble color", air_color, disabled=True)

    st.header("Defaults")
    current_settings = {
        "diameter": diameter,
        "liquid_thickness": liquid_thickness,
        "show_glare": show_glare,
        "sand_types": sand_types,
        "sand_amount": sand_amount,
        "initial_mix_percent": initial_mix_percent,
        "air_amount": air_amount,
        "air_bubbles": air_bubbles,
        "bubble_scale_percent": bubble_scale_percent,
        "rotation_step": rotation_step,
        "initial_angle": initial_angle,
        "speed": speed,
        "gravity_scale_percent": gravity_scale_percent,
        "max_weight_difference_percent": max_weight_difference_percent,
        "resolution": resolution,
        "seed": int(seed),
        "palette_name": palette_name,
        "liquid_color": liquid_color,
        "air_color": air_color,
    }
    if st.button("Save settings as default", use_container_width=True):
        save_settings(current_settings)
        st.success("Saved as default.")


stage_width = diameter + 92
stage_height = diameter + 118

viscosity = 0.34 + liquid_thickness * 0.033
gravity_scale = gravity_scale_percent / 100
max_weight_difference = max_weight_difference_percent / 100
motion_chance = max(0.10, min(0.72, 0.82 - viscosity * 0.46))
air_mobility = max(0.18, min(0.86, 0.58 - liquid_thickness * 0.012 + air_amount * 0.005))
bubble_barrier = min(0.92, air_amount / 26 * 0.42 + air_bubbles / 28 * 0.24 + bubble_scale * 0.2)
sand_through_air = max(0.004, min(0.12, 0.16 - bubble_barrier * 0.15))
air_through_sand = max(0.004, min(0.10, 0.07 - bubble_barrier * 0.045 + liquid_thickness * 0.001))

config = {
    "stageWidth": stage_width,
    "stageHeight": stage_height,
    "diameter": diameter,
    "gridSize": resolution,
    "sandTypes": sand_types,
    "sandAmount": sand_amount,
    "airAmount": air_amount,
    "airBubbles": air_bubbles,
    "liquidThickness": liquid_thickness,
    "bubbleScale": bubble_scale,
    "rotationStep": rotation_step,
    "initialAngle": initial_angle,
    "seed": int(seed),
    "palette": PALETTES[palette_name][:sand_types],
    "liquidColor": liquid_color,
    "airColor": air_color,
    "showGlare": show_glare,
    "initialMix": initial_mix,
    "motionChance": motion_chance,
    "airMobility": air_mobility,
    "gravityScale": gravity_scale,
    "maxWeightDifference": max_weight_difference,
    "sandThroughAir": sand_through_air,
    "airThroughSand": air_through_sand,
    "simulationWork": 0.12 + speed * 0.055,
    "stepsPerFrame": 1 + speed // 3,
}

left, right = st.columns([0.74, 0.26], vertical_alignment="top")

with left:
    render_simulator(build_simulator(config), height=stage_height + 44)

with right:
    st.subheader("Current Mix")
    st.metric("Sand types", sand_types)
    st.metric("Sand / air", f"{sand_amount}% / {air_amount}%")
    st.metric("Liquid thickness", f"{liquid_thickness} mm")
    st.metric("Gravity scale", f"{gravity_scale:.1f}x")
    st.metric("Max weight spread", f"{max_weight_difference_percent}%")
    st.caption("Click inside the circle, or use the rotate buttons, to turn the sealed glass and let the same grains reform.")
    st.caption("Rotation now turns the current sand and air state first; then sand falls down while air rises and blocks most direct paths.")
