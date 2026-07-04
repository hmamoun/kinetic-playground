import html
from textwrap import dedent

import streamlit as st


st.set_page_config(
    page_title="Water Ripple Touch",
    page_icon="W",
    layout="wide",
)


def build_camera_view() -> str:
    return dedent(
        """
        <div class="ripple-shell">
          <div class="status-bar">
            <span id="os-status" class="pill">Detecting OS...</span>
            <span id="camera-status" class="pill">Checking for a camera...</span>
          </div>

          <div class="stage">
            <video id="camera-feed" autoplay playsinline muted></video>
            <div id="placeholder" class="placeholder">
              <button id="enable-camera" type="button">Enable Camera</button>
              <p id="error-message" class="error"></p>
            </div>
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

          .status-bar {
            width: min(100%, 720px);
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
          }

          .pill {
            padding: 6px 12px;
            border-radius: 999px;
            background: rgba(23, 32, 51, .06);
            border: 1px solid rgba(23, 32, 51, .14);
            font-size: 13px;
            color: #172033;
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
            transform: scaleX(-1);
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
          (() => {
            const osStatus = document.getElementById("os-status");
            const cameraStatus = document.getElementById("camera-status");
            const enableButton = document.getElementById("enable-camera");
            const errorMessage = document.getElementById("error-message");
            const video = document.getElementById("camera-feed");
            const placeholder = document.getElementById("placeholder");
            let activeStream = null;

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
                video.style.display = "block";
                placeholder.style.display = "none";

                const tracks = activeStream.getVideoTracks();
                if (tracks.length > 0) {
                  const label = tracks[0].label;
                  cameraStatus.textContent = label ? `Streaming from: ${label}` : "Camera stream active.";
                }
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
              if (activeStream) {
                activeStream.getTracks().forEach((track) => track.stop());
                activeStream = null;
              }
            }

            osStatus.textContent = `Detected OS: ${detectOS()}`;
            checkForCamera();
            enableButton.addEventListener("click", enableCamera);
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


st.title("Water Ripple Touch")
st.caption(
    "Step 1: get the camera working. Detect the OS, check for an attached camera, "
    "request permission, and show the live feed. The tap-to-ripple effect comes next."
)

render_camera_view(build_camera_view(), height=620)
