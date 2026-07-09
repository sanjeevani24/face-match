import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Cross-browser camera access hook.
 *
 * Handles the things that differ between Chrome / Safari / Firefox / Edge
 * and between desktop / mobile:
 *  - Secure-context requirement (getUserMedia is only available on https or
 *    localhost; every other origin gets `undefined` for mediaDevices).
 *  - Safari (desktop + iOS) needs `playsInline` and `muted` on the <video>
 *    element or autoplay silently fails.
 *  - Device labels are only populated by enumerateDevices() AFTER a
 *    permission has been granted at least once, so we re-enumerate after
 *    the first successful stream.
 *  - iOS Safari does not support facingMode "exact" reliably; we request it
 *    as "ideal" and fall back gracefully.
 *  - Every stream must have its tracks stopped explicitly (track.stop()) or
 *    the camera stays "in use" after navigating away, which then breaks the
 *    next getUserMedia call in Firefox/Safari with NotReadableError.
 */
export function useCamera({ facingMode = "user" } = {}) {
  const videoRef = useRef(null);
  const canvasRef = useRef(null);
  const streamRef = useRef(null);

  const [isSupported, setIsSupported] = useState(true);
  const [isSecureContext, setIsSecureContext] = useState(true);
  const [status, setStatus] = useState("idle"); // idle | requesting | ready | error
  const [error, setError] = useState(null);
  const [devices, setDevices] = useState([]);
  const [activeDeviceId, setActiveDeviceId] = useState(null);
  const [currentFacingMode, setCurrentFacingMode] = useState(facingMode);

  useEffect(() => {
    const supported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    setIsSupported(supported);
    setIsSecureContext(window.isSecureContext);
  }, []);

  const stopCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
    setStatus("idle");
  }, []);

  const refreshDeviceList = useCallback(async () => {
    try {
      const all = await navigator.mediaDevices.enumerateDevices();
      setDevices(all.filter((d) => d.kind === "videoinput"));
    } catch {
      // enumerateDevices failing is non-fatal — device switching UI is optional.
    }
  }, []);

  const mapError = (err) => {
    switch (err?.name) {
      case "NotAllowedError":
      case "PermissionDeniedError":
        return "Camera access was denied. Please allow camera permission in your browser's address-bar settings and try again.";
      case "NotFoundError":
      case "DevicesNotFoundError":
        return "No camera was found on this device.";
      case "NotReadableError":
      case "TrackStartError":
        return "The camera is already in use by another application or browser tab.";
      case "OverconstrainedError":
      case "ConstraintNotSatisfiedError":
        return "The selected camera doesn't support the required settings. Trying the default camera instead.";
      case "SecurityError":
        return "Camera access is blocked because this page isn't loaded over a secure (https) connection.";
      default:
        return err?.message || "Unable to access the camera.";
    }
  };

  const startCamera = useCallback(
    async (deviceId) => {
      if (!navigator.mediaDevices?.getUserMedia) {
        setIsSupported(false);
        setError("This browser doesn't support camera access. Please use a recent version of Chrome, Safari, Firefox, or Edge.");
        setStatus("error");
        return;
      }
      if (!window.isSecureContext) {
        setIsSecureContext(false);
        setError("Camera access requires https. Please open this page over a secure connection.");
        setStatus("error");
        return;
      }

      setStatus("requesting");
      setError(null);

      // Stop any existing stream first so the new getUserMedia call doesn't
      // collide with a still-active track (common Firefox/Safari failure).
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
        streamRef.current = null;
      }

      const constraints = {
        audio: false,
        video: deviceId
          ? { deviceId: { exact: deviceId } }
          : { facingMode: { ideal: currentFacingMode }, width: { ideal: 1280 }, height: { ideal: 720 } },
      };

      try {
        const stream = await navigator.mediaDevices.getUserMedia(constraints);
        streamRef.current = stream;

        if (videoRef.current) {
          videoRef.current.srcObject = stream;
          // iOS Safari requires an explicit play() call after assigning srcObject.
          await videoRef.current.play().catch(() => {});
        }

        const [track] = stream.getVideoTracks();
        setActiveDeviceId(track?.getSettings?.().deviceId ?? deviceId ?? null);
        setStatus("ready");
        await refreshDeviceList();
      } catch (err) {
        setError(mapError(err));
        setStatus("error");
      }
    },
    [currentFacingMode, refreshDeviceList]
  );

  const switchCamera = useCallback(async () => {
    if (devices.length < 2) {
      // No enumerated alternative devices — try flipping facingMode instead,
      // which is the more reliable path on mobile browsers.
      setCurrentFacingMode((prev) => (prev === "user" ? "environment" : "user"));
      await startCamera();
      return;
    }
    const currentIndex = devices.findIndex((d) => d.deviceId === activeDeviceId);
    const next = devices[(currentIndex + 1) % devices.length];
    await startCamera(next.deviceId);
  }, [devices, activeDeviceId, startCamera]);

  /**
   * Capture the current video frame to a JPEG data URL.
   * Uses a hidden <canvas> so it works identically across browsers,
   * instead of relying on any browser-specific screenshot API.
   */
  const capture = useCallback((quality = 0.92) => {
    const video = videoRef.current;
    if (!video || video.readyState < 2) return null;

    const canvas = canvasRef.current || document.createElement("canvas");
    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    const ctx = canvas.getContext("2d");
    ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
    return canvas.toDataURL("image/jpeg", quality);
  }, []);

  useEffect(() => {
    return () => stopCamera();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  return {
    videoRef,
    canvasRef,
    status, // idle | requesting | ready | error
    error,
    isSupported,
    isSecureContext,
    devices,
    activeDeviceId,
    startCamera,
    stopCamera,
    switchCamera,
    capture,
    hasMultipleCameras: devices.length > 1,
  };
}
