from textwrap import dedent

import streamlit as st


st.set_page_config(
    page_title="Camera Games",
    page_icon="C",
    layout="wide",
)


def build_camera_view() -> str:
    return dedent(
        """
        <div class="ripple-shell">
          <div class="controls">
            <label class="effect-picker">
              <span>Effect</span>
              <select id="effect-select">
                <option value="water">Water Rippler</option>
                <option value="kaleidoscope">Kaleidoscope</option>
              </select>
            </label>
            <button id="snapshot-button" type="button" disabled>Save Snapshot</button>
          </div>

          <div class="stage">
            <video id="camera-feed" autoplay playsinline muted></video>
            <canvas id="fx-canvas"></canvas>
            <div id="placeholder" class="placeholder">
              <button id="enable-camera" type="button">Enable Camera</button>
              <p id="error-message" class="error"></p>
            </div>
          </div>

          <div class="status-bar">
            <span id="os-status" class="pill">Detecting OS...</span>
            <span id="camera-status" class="pill">Checking for a camera...</span>
            <span id="fx-status" class="pill">Effect: point at the camera</span>
          </div>
        </div>

        <style>
          :root {
            color-scheme: light;
          }

          .ripple-shell {
            width: 100%;
            display: flex;
            flex-direction: column;
            align-items: center;
            gap: 14px;
            padding: 8px 0 14px;
            font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
          }

          .controls,
          .status-bar {
            width: min(100%, 720px);
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }

          .pill,
          .effect-picker {
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(23, 32, 51, .06);
            border: 1px solid rgba(23, 32, 51, .14);
            font-size: 13px;
            color: #172033;
          }

          .effect-picker {
            display: inline-flex;
            align-items: center;
            gap: 8px;
            font-weight: 600;
          }

          .effect-picker select {
            border: none;
            background: transparent;
            font: inherit;
            font-weight: 700;
            color: inherit;
            cursor: pointer;
          }

          #snapshot-button {
            padding: 6px 14px;
            border-radius: 999px;
            border: 1px solid rgba(23, 32, 51, .14);
            background: #172033;
            color: #f4f6fb;
            font-size: 13px;
            font-weight: 600;
            cursor: pointer;
          }

          #snapshot-button:hover:not(:disabled) {
            background: #232f47;
          }

          #snapshot-button:disabled {
            opacity: .45;
            cursor: not-allowed;
          }

          .stage {
            position: relative;
            width: min(100%, 720px);
            aspect-ratio: 4 / 3;
            background: linear-gradient(135deg, rgba(255,255,255,.7), rgba(255,255,255,.25)), #0e1626;
            border: 1px solid rgba(28, 37, 65, .14);
            border-radius: 8px;
            box-shadow: 0 18px 46px rgba(22, 31, 56, .16);
            overflow: hidden;
          }

          #camera-feed {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            object-fit: cover;
            display: none;
          }

          #fx-canvas {
            position: absolute;
            inset: 0;
            width: 100%;
            height: 100%;
            display: none;
            pointer-events: none;
          }

          .placeholder {
            position: absolute;
            inset: 0;
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            gap: 12px;
            text-align: center;
            padding: 24px;
          }

          #enable-camera {
            padding: 10px 22px;
            border: 1px solid rgba(255, 255, 255, .28);
            border-radius: 8px;
            background: rgba(255, 255, 255, .12);
            color: #f4f6fb;
            font-size: 15px;
            font-weight: 600;
            cursor: pointer;
          }

          #enable-camera:hover {
            background: rgba(255, 255, 255, .2);
          }

          #enable-camera:disabled {
            opacity: .5;
            cursor: not-allowed;
          }

          .error {
            max-width: 480px;
            margin: 0;
            color: #ffb4a8;
            font-size: 13px;
          }
        </style>

        <script>
          (async () => {
            const osStatus = document.getElementById("os-status");
            const cameraStatus = document.getElementById("camera-status");
            const fxStatus = document.getElementById("fx-status");
            const enableButton = document.getElementById("enable-camera");
            const errorMessage = document.getElementById("error-message");
            const video = document.getElementById("camera-feed");
            const fxCanvas = document.getElementById("fx-canvas");
            const fxCtx = fxCanvas.getContext("2d");
            const placeholder = document.getElementById("placeholder");
            const effectSelect = document.getElementById("effect-select");
            const snapshotButton = document.getElementById("snapshot-button");

            let activeStream = null;
            let handLandmarker = null;
            let handModelLoading = false;
            let lastVideoTime = -1;
            let renderAnimationId = null;
            let currentEffect = effectSelect.value;
            let pointerNorm = null;

            const RIPPLE_W = 160;
            const RIPPLE_H = 120;
            let rippleCurrent = new Float32Array(RIPPLE_W * RIPPLE_H);
            let ripplePrevious = new Float32Array(RIPPLE_W * RIPPLE_H);
            const rippleWorkCanvas = document.createElement("canvas");
            rippleWorkCanvas.width = RIPPLE_W;
            rippleWorkCanvas.height = RIPPLE_H;
            const rippleWorkCtx = rippleWorkCanvas.getContext("2d", { willReadFrequently: true });
            const rippleOutCanvas = document.createElement("canvas");
            rippleOutCanvas.width = RIPPLE_W;
            rippleOutCanvas.height = RIPPLE_H;
            const rippleOutCtx = rippleOutCanvas.getContext("2d");

            const KALEIDOSCOPE_SEGMENTS = 10;
            let kaleidoscopeBase = null;
            let kaleidoscopeWedge = null;
            let kaleidoscopeRotation = 0;

            function detectOS() {
              const platform = (navigator.userAgentData && navigator.userAgentData.platform) || navigator.platform || "";
              const ua = navigator.userAgent || "";

              if (/Win/i.test(platform) || /Windows/i.test(ua)) return "Windows";
              if (/Mac/i.test(platform) && /Mobile/i.test(ua) === false && /iPhone|iPad|iPod/i.test(ua) === false) return "macOS";
              if (/iPhone|iPad|iPod/i.test(ua)) return "iOS";
              if (/Android/i.test(ua)) return "Android";
              if (/Linux/i.test(platform) || /Linux/i.test(ua)) return "Linux";
              return "Unknown OS";
            }

            async function checkForCamera() {
              if (!navigator.mediaDevices || !navigator.mediaDevices.enumerateDevices) {
                cameraStatus.textContent = "Camera detection is not supported in this browser.";
                enableButton.disabled = true;
                return;
              }

              try {
                const devices = await navigator.mediaDevices.enumerateDevices();
                const cameras = devices.filter((device) => device.kind === "videoinput");

                if (cameras.length === 0) {
                  cameraStatus.textContent = "No camera detected on this system.";
                  enableButton.disabled = true;
                } else {
                  cameraStatus.textContent = `${cameras.length} camera${cameras.length === 1 ? "" : "s"} detected.`;
                }
              } catch (error) {
                cameraStatus.textContent = "Could not check for a camera.";
              }
            }

            function showError(message) {
              errorMessage.textContent = message;
            }

            function resizeFxCanvas() {
              const rect = fxCanvas.getBoundingClientRect();
              const dpr = Math.max(1, Math.min(2, window.devicePixelRatio || 1));
              const width = Math.max(1, Math.round(rect.width * dpr));
              const height = Math.max(1, Math.round(rect.height * dpr));
              if (fxCanvas.width !== width || fxCanvas.height !== height) {
                fxCanvas.width = width;
                fxCanvas.height = height;
                fxCtx.setTransform(dpr, 0, 0, dpr, 0, 0);
              }
            }

            function saveSnapshot() {
              const link = document.createElement("a");
              const stamp = new Date().toISOString().slice(0, 19).replace(/[:T]/g, "-");
              link.download = `camera-games-${currentEffect}-${stamp}.jpg`;
              link.href = fxCanvas.toDataURL("image/jpeg", 0.95);
              document.body.appendChild(link);
              link.click();
              link.remove();
            }

            function distance3(a, b) {
              const dx = a.x - b.x;
              const dy = a.y - b.y;
              const dz = (a.z || 0) - (b.z || 0);
              return Math.sqrt(dx * dx + dy * dy + dz * dz);
            }

            function isFingerExtended(landmarks, tipIndex, pipIndex, wristIndex) {
              const wrist = landmarks[wristIndex];
              const tipDistance = distance3(landmarks[tipIndex], wrist);
              const pipDistance = distance3(landmarks[pipIndex], wrist);
              return tipDistance > pipDistance * 1.15;
            }

            function isPointingGesture(landmarks) {
              const indexExtended = isFingerExtended(landmarks, 8, 6, 0);
              const middleCurled = !isFingerExtended(landmarks, 12, 10, 0);
              const ringCurled = !isFingerExtended(landmarks, 16, 14, 0);
              const pinkyCurled = !isFingerExtended(landmarks, 20, 18, 0);
              return indexExtended && middleCurled && ringCurled && pinkyCurled;
            }

            function computeCoverMapping(videoWidth, videoHeight, containerWidth, containerHeight) {
              const videoRatio = videoWidth / videoHeight;
              const containerRatio = containerWidth / containerHeight;
              let scale = 1;
              let offsetX = 0;
              let offsetY = 0;

              if (videoRatio > containerRatio) {
                scale = containerHeight / videoHeight;
                offsetX = (containerWidth - videoWidth * scale) / 2;
              } else {
                scale = containerWidth / videoWidth;
                offsetY = (containerHeight - videoHeight * scale) / 2;
              }

              return { scale, offsetX, offsetY };
            }

            function clampByte(value) {
              return value < 0 ? 0 : value > 255 ? 255 : value;
            }

            function rippleIndex(x, y) {
              return y * RIPPLE_W + x;
            }

            function stepRipple() {
              for (let y = 1; y < RIPPLE_H - 1; y += 1) {
                const row = y * RIPPLE_W;
                for (let x = 1; x < RIPPLE_W - 1; x += 1) {
                  const i = row + x;
                  const value = (
                    ripplePrevious[i - 1] +
                    ripplePrevious[i + 1] +
                    ripplePrevious[i - RIPPLE_W] +
                    ripplePrevious[i + RIPPLE_W]
                  ) / 2 - rippleCurrent[i];
                  rippleCurrent[i] = value * 0.965;
                }
              }
              const swap = ripplePrevious;
              ripplePrevious = rippleCurrent;
              rippleCurrent = swap;
            }

            function injectRipple(normX, normY, strength) {
              const cx = Math.round(normX * (RIPPLE_W - 1));
              const cy = Math.round(normY * (RIPPLE_H - 1));
              for (let dy = -1; dy <= 1; dy += 1) {
                for (let dx = -1; dx <= 1; dx += 1) {
                  const x = cx + dx;
                  const y = cy + dy;
                  if (x > 0 && x < RIPPLE_W - 1 && y > 0 && y < RIPPLE_H - 1) {
                    ripplePrevious[rippleIndex(x, y)] = strength;
                  }
                }
              }
            }

            function renderWaterRippler() {
              if (pointerNorm) {
                injectRipple(pointerNorm.x, pointerNorm.y, 900);
              }
              stepRipple();

              rippleWorkCtx.save();
              rippleWorkCtx.translate(RIPPLE_W, 0);
              rippleWorkCtx.scale(-1, 1);
              const mapping = computeCoverMapping(video.videoWidth, video.videoHeight, RIPPLE_W, RIPPLE_H);
              rippleWorkCtx.drawImage(
                video,
                mapping.offsetX,
                mapping.offsetY,
                video.videoWidth * mapping.scale,
                video.videoHeight * mapping.scale
              );
              rippleWorkCtx.restore();

              const source = rippleWorkCtx.getImageData(0, 0, RIPPLE_W, RIPPLE_H);
              const output = rippleOutCtx.createImageData(RIPPLE_W, RIPPLE_H);
              const src = source.data;
              const dst = output.data;

              for (let y = 1; y < RIPPLE_H - 1; y += 1) {
                for (let x = 1; x < RIPPLE_W - 1; x += 1) {
                  const i = rippleIndex(x, y);
                  const dx = ripplePrevious[i + 1] - ripplePrevious[i - 1];
                  const dy = ripplePrevious[i + RIPPLE_W] - ripplePrevious[i - RIPPLE_W];

                  const sx = Math.min(RIPPLE_W - 1, Math.max(0, x + dx * 0.6));
                  const sy = Math.min(RIPPLE_H - 1, Math.max(0, y + dy * 0.6));
                  const si = (Math.round(sy) * RIPPLE_W + Math.round(sx)) * 4;
                  const di = i * 4;
                  const shade = 1 + dx * 0.012;

                  dst[di] = clampByte(src[si] * shade);
                  dst[di + 1] = clampByte(src[si + 1] * shade);
                  dst[di + 2] = clampByte(src[si + 2] * shade);
                  dst[di + 3] = 255;
                }
              }

              rippleOutCtx.putImageData(output, 0, 0);
              fxCtx.clearRect(0, 0, fxCanvas.clientWidth, fxCanvas.clientHeight);
              fxCtx.drawImage(
                rippleOutCanvas,
                0, 0, RIPPLE_W, RIPPLE_H,
                0, 0, fxCanvas.clientWidth, fxCanvas.clientHeight
              );

              fxStatus.textContent = pointerNorm
                ? "Rippling from your fingertip"
                : "Point at the camera to make ripples";
            }

            function renderKaleidoscope() {
              const width = fxCanvas.clientWidth;
              const height = fxCanvas.clientHeight;
              const size = Math.min(width, height);
              if (size <= 0) return;

              if (!kaleidoscopeBase || kaleidoscopeBase.width !== size) {
                kaleidoscopeBase = document.createElement("canvas");
                kaleidoscopeBase.width = size;
                kaleidoscopeBase.height = size;
                kaleidoscopeWedge = document.createElement("canvas");
                kaleidoscopeWedge.width = size;
                kaleidoscopeWedge.height = size;
              }

              const baseCtx = kaleidoscopeBase.getContext("2d");
              const mapping = computeCoverMapping(video.videoWidth, video.videoHeight, size, size);
              baseCtx.save();
              baseCtx.translate(size, 0);
              baseCtx.scale(-1, 1);
              baseCtx.drawImage(
                video,
                mapping.offsetX,
                mapping.offsetY,
                video.videoWidth * mapping.scale,
                video.videoHeight * mapping.scale
              );
              baseCtx.restore();

              const angleStep = (Math.PI * 2) / KALEIDOSCOPE_SEGMENTS;
              const wedgeCtx = kaleidoscopeWedge.getContext("2d");
              wedgeCtx.clearRect(0, 0, size, size);
              wedgeCtx.save();
              wedgeCtx.translate(size / 2, size / 2);
              wedgeCtx.beginPath();
              wedgeCtx.moveTo(0, 0);
              wedgeCtx.arc(0, 0, size / 2, -angleStep / 2, angleStep / 2);
              wedgeCtx.closePath();
              wedgeCtx.clip();
              wedgeCtx.translate(-size / 2, -size / 2);
              wedgeCtx.drawImage(kaleidoscopeBase, 0, 0);
              wedgeCtx.restore();

              kaleidoscopeRotation += 0.004;

              fxCtx.clearRect(0, 0, width, height);
              fxCtx.save();
              fxCtx.translate(width / 2, height / 2);
              fxCtx.rotate(kaleidoscopeRotation);
              for (let i = 0; i < KALEIDOSCOPE_SEGMENTS; i += 1) {
                fxCtx.save();
                fxCtx.rotate(angleStep * i);
                if (i % 2 === 1) fxCtx.scale(1, -1);
                fxCtx.drawImage(kaleidoscopeWedge, -size / 2, -size / 2);
                fxCtx.restore();
              }
              fxCtx.restore();

              fxStatus.textContent = "Kaleidoscope active";
            }

            function updatePointerFromHands(result) {
              const hands = result.landmarks || [];
              const pointingHand = hands.find(isPointingGesture);

              if (pointingHand) {
                const tip = pointingHand[8];
                pointerNorm = { x: 1 - tip.x, y: tip.y };
              } else {
                pointerNorm = null;
              }
            }

            async function loadHandModel() {
              if (handLandmarker || handModelLoading) return;
              handModelLoading = true;
              try {
                fxStatus.textContent = "Loading hand-tracking model...";
                const vision = await import("https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14");
                const filesetResolver = await vision.FilesetResolver.forVisionTasks(
                  "https://cdn.jsdelivr.net/npm/@mediapipe/tasks-vision@0.10.14/wasm"
                );
                handLandmarker = await vision.HandLandmarker.createFromOptions(filesetResolver, {
                  baseOptions: {
                    modelAssetPath:
                      "https://storage.googleapis.com/mediapipe-models/hand_landmarker/hand_landmarker/float16/1/hand_landmarker.task",
                    delegate: "GPU",
                  },
                  runningMode: "VIDEO",
                  numHands: 1,
                });
                fxStatus.textContent = "Point at the camera to make ripples";
              } catch (error) {
                fxStatus.textContent = `Hand tracking unavailable (${error.message || error})`;
              } finally {
                handModelLoading = false;
              }
            }

            function renderLoop() {
              if (video.readyState >= 2) {
                if (currentEffect === "water") {
                  if (handLandmarker && video.currentTime !== lastVideoTime) {
                    lastVideoTime = video.currentTime;
                    const result = handLandmarker.detectForVideo(video, performance.now());
                    updatePointerFromHands(result);
                  }
                  renderWaterRippler();
                } else if (currentEffect === "kaleidoscope") {
                  renderKaleidoscope();
                }
              }
              renderAnimationId = requestAnimationFrame(renderLoop);
            }

            function applyEffect(effect) {
              currentEffect = effect;
              pointerNorm = null;
              if (effect === "water") {
                loadHandModel();
                fxStatus.textContent = handLandmarker
                  ? "Point at the camera to make ripples"
                  : "Loading hand-tracking model...";
              } else {
                fxStatus.textContent = "Kaleidoscope active";
              }
            }

            async function enableCamera() {
              errorMessage.textContent = "";

              if (!window.isSecureContext) {
                showError("Camera access requires a secure context (HTTPS or localhost).");
                return;
              }

              if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
                showError("This browser does not support camera access.");
                return;
              }

              enableButton.disabled = true;
              enableButton.textContent = "Requesting permission...";

              try {
                activeStream = await navigator.mediaDevices.getUserMedia({
                  video: { facingMode: "user" },
                  audio: false,
                });

                video.srcObject = activeStream;
                fxCanvas.style.display = "block";
                placeholder.style.display = "none";

                const tracks = activeStream.getVideoTracks();
                if (tracks.length > 0) {
                  const label = tracks[0].label;
                  cameraStatus.textContent = label ? `Streaming from: ${label}` : "Camera stream active.";
                }

                video.addEventListener("loadedmetadata", resizeFxCanvas, { once: true });
                window.addEventListener("resize", resizeFxCanvas);
                resizeFxCanvas();
                applyEffect(currentEffect);
                renderLoop();
                snapshotButton.disabled = false;
              } catch (error) {
                enableButton.disabled = false;
                enableButton.textContent = "Enable Camera";

                if (error.name === "NotAllowedError" || error.name === "PermissionDeniedError") {
                  showError("Camera permission was denied. Allow camera access in your browser settings and try again.");
                } else if (error.name === "NotFoundError" || error.name === "DevicesNotFoundError") {
                  showError("No camera could be found on this system.");
                } else if (error.name === "NotReadableError") {
                  showError("The camera is already in use by another application.");
                } else {
                  showError(`Could not access the camera (${error.name || "unknown error"}).`);
                }
              }
            }

            function stopCamera() {
              if (renderAnimationId) {
                cancelAnimationFrame(renderAnimationId);
                renderAnimationId = null;
              }
              if (activeStream) {
                activeStream.getTracks().forEach((track) => track.stop());
                activeStream = null;
              }
              snapshotButton.disabled = true;
            }

            osStatus.textContent = `Detected OS: ${detectOS()}`;
            checkForCamera();
            enableButton.addEventListener("click", enableCamera);
            effectSelect.addEventListener("change", (event) => applyEffect(event.target.value));
            snapshotButton.addEventListener("click", saveSnapshot);
            window.addEventListener("pagehide", stopCamera);

            if (navigator.mediaDevices && navigator.mediaDevices.addEventListener) {
              navigator.mediaDevices.addEventListener("devicechange", checkForCamera);
            }
          })();
        </script>
        """
    )


def render_camera_view(html_doc: str, height: int) -> None:
    if hasattr(st, "iframe"):
        st.iframe(html_doc, height=height, width="stretch")
        return

    import streamlit.components.v1 as components

    components.html(html_doc, height=height, scrolling=False)


st.title("Camera Games")
st.caption(
    "Pick an effect, then enable your camera. Water Rippler distorts the feed with a live ripple "
    "simulation you trigger by pointing your index finger at the screen. Kaleidoscope mirrors the "
    "feed into a spinning symmetrical pattern. Use Save Snapshot to download the current frame."
)

render_camera_view(build_camera_view(), height=660)
