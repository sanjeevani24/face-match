import { useEffect } from "react";
import { Camera, RefreshCw, AlertTriangle, SwitchCamera, VideoOff } from "lucide-react";
import Card from "../common/Card.jsx";
import Button from "../common/Button.jsx";
import Loader from "../common/Loader.jsx";
import { useCamera } from "../../hooks/useCamera.js";
import { FRAME_INTERVAL_MS } from "../../utils/constants.js";

export default function WebcamCard({
  onCapture,
  active = true,
  continuous = false,
  intervalMs = FRAME_INTERVAL_MS,
  captureLabel = "Capture",
}) {
  const {
    videoRef,
    canvasRef,
    status,
    error,
    isSupported,
    isSecureContext,
    startCamera,
    stopCamera,
    switchCamera,
    capture,
    hasMultipleCameras,
  } = useCamera({ facingMode: "user" });

  useEffect(() => {
    if (active) {
      startCamera();
    } else {
      stopCamera();
    }
    return () => stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [active]);

  // Continuous mode: post a frame every `intervalMs` while the camera is
  // ready, instead of waiting for a manual click. The parent is responsible
  // for ignoring overlapping frames while a request is in flight (a session
  // response can take longer than intervalMs, e.g. the frame that finally
  // triggers face verification).
  useEffect(() => {
    if (!continuous || status !== "ready") return undefined;
    const id = setInterval(() => {
      const dataUrl = capture();
      if (dataUrl) onCapture?.(dataUrl);
    }, intervalMs);
    return () => clearInterval(id);
  }, [continuous, status, intervalMs, capture, onCapture]);

  const handleManualCapture = () => {
    const dataUrl = capture();
    if (dataUrl) onCapture?.(dataUrl);
  };

  return (
    <Card
      title="Live Camera"
      subtitle="Center your face in the frame and follow the on-screen instructions"
      action={
        hasMultipleCameras && status === "ready" ? (
          <Button variant="ghost" size="sm" icon={SwitchCamera} onClick={switchCamera}>
            Switch
          </Button>
        ) : null
      }
    >
      <div className="relative mx-auto aspect-[4/3] w-full max-w-md overflow-hidden rounded-xl bg-[var(--color-ink)]">
        {!isSupported && (
          <CameraNotice
            icon={VideoOff}
            title="Camera not supported"
            message="This browser doesn't support camera access. Please use a recent version of Chrome, Safari, Firefox, or Edge."
          />
        )}

        {isSupported && !isSecureContext && (
          <CameraNotice
            icon={AlertTriangle}
            title="Secure connection required"
            message="Camera access needs https (or localhost). Please open this page over a secure connection."
          />
        )}

        {isSupported && isSecureContext && status === "error" && (
          <CameraNotice
            icon={AlertTriangle}
            title="Camera unavailable"
            message={error}
            action={
              <Button variant="outline" size="sm" icon={RefreshCw} onClick={() => startCamera()}>
                Try again
              </Button>
            }
          />
        )}

        {isSupported && isSecureContext && status === "requesting" && (
          <div className="absolute inset-0 flex items-center justify-center">
            <Loader label="Requesting camera permission…" />
          </div>
        )}

        {/* Video element always mounted so the ref is ready before startCamera runs.
            playsInline + muted are required for autoplay on iOS Safari. */}
        <video
          ref={videoRef}
          playsInline
          muted
          autoPlay
          className={`h-full w-full object-cover [transform:scaleX(-1)] ${status === "ready" ? "opacity-100" : "opacity-0"}`}
        />
        <canvas ref={canvasRef} className="hidden" />

        {status === "ready" && (
          <div className="pointer-events-none absolute inset-6 rounded-full border-2 border-white/70" />
        )}
      </div>

      <div className="mt-4 flex justify-center">
        {continuous ? (
          <div className="flex items-center gap-2 text-xs text-[var(--color-ink-faint)]">
            <span
              className={`size-2 rounded-full ${
                status === "ready" ? "animate-pulse bg-[var(--color-brand-green)]" : "bg-[var(--color-border)]"
              }`}
            />
            {status === "ready" ? "Streaming to verification server…" : "Waiting for camera…"}
          </div>
        ) : (
          <Button icon={Camera} onClick={handleManualCapture} disabled={status !== "ready"}>
            {captureLabel}
          </Button>
        )}
      </div>
    </Card>
  );
}

function CameraNotice({ icon: Icon, title, message, action }) {
  return (
    <div className="absolute inset-0 flex flex-col items-center justify-center gap-2 px-6 text-center text-white">
      <Icon className="size-7 text-[var(--color-warning)]" />
      <p className="text-sm font-semibold">{title}</p>
      {message && <p className="text-xs text-white/70">{message}</p>}
      {action}
    </div>
  );
}
