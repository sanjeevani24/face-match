import { useEffect, useState } from "react";
import { LiveKitRoom, VideoConference } from "@livekit/components-react";
import "@livekit/components-styles";
import { PhoneCall, PlayCircle, StopCircle } from "lucide-react";
import Card from "../components/common/Card.jsx";
import Button from "../components/common/Button.jsx";
import LiveStatusCard from "../components/verification/LiveStatusCard.jsx";
import {
  startCallCapture,
  stopCallCapture,
  getCallSessionStatus,
} from "../services/verificationApi.js";

function useQueryParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    roomId: params.get("room_id"),
    roomUrl: params.get("room_url"),
    token: params.get("token"),
  };
}

export default function OfficerCall() {
  const { roomId, roomUrl, token } = useQueryParams();

  const [joined, setJoined] = useState(false);
  const [captureStarted, setCaptureStarted] = useState(false);
  const [starting, setStarting] = useState(false);
  const [status, setStatus] = useState(null);
  const [lastUpdateAt, setLastUpdateAt] = useState(null);
  const [error, setError] = useState(null);

  async function startCapture() {
    setError(null);
    setStarting(true);
    try {
      await startCallCapture(roomId);
      setCaptureStarted(true);
    } catch (e) {
      setError(`Could not start capture: ${e?.response?.data?.detail || e.message}`);
    } finally {
      setStarting(false);
    }
  }

  async function stopCapture() {
    setError(null);
    try {
      await stopCallCapture(roomId);
      setCaptureStarted(false);
    } catch (e) {
      setError(`Could not stop capture: ${e?.response?.data?.detail || e.message}`);
    }
  }

  // Poll live status once capture has started.
  useEffect(() => {
    if (!captureStarted || !roomId) return undefined;
    const interval = setInterval(async () => {
      try {
        const data = await getCallSessionStatus(roomId);
        setStatus(data);
        setLastUpdateAt(Date.now());
      } catch {
        /* transient — next tick retries */
      }
    }, 1000);
    return () => clearInterval(interval);
  }, [captureStarted, roomId]);

  const framesAlive = Boolean(lastUpdateAt && Date.now() - lastUpdateAt < 3000);

  if (!roomId || !roomUrl || !token) {
    return (
      <div className="p-6">
        <Card title="Missing call details">
          <p className="text-sm text-[var(--color-ink-faint)]">
            This page needs <code>room_id</code>, <code>room_url</code>, and <code>token</code> in the
            URL — open it via the officer link generated when the session was created.
          </p>
        </Card>
      </div>
    );
  }

  return (
    <div className="grid grid-cols-1 gap-6 p-6 lg:grid-cols-[1fr_360px]">
      <Card
        title="Verification Call"
        subtitle={roomId}
        padded={false}
        action={
          <span className="flex items-center gap-2 text-xs text-[var(--color-ink-faint)]">
            <PhoneCall
              className={`size-4 ${joined ? "text-[var(--color-brand-green)]" : "text-[var(--color-ink-faint)]"}`}
            />
            {joined ? "Connected" : "Connecting…"}
          </span>
        }
      >
        <div className="relative aspect-video w-full overflow-hidden rounded-b-xl bg-[var(--color-ink)]">
          <LiveKitRoom
            serverUrl={roomUrl}
            token={token}
            connect
            video
            audio
            data-lk-theme="default"
            style={{ height: "100%" }}
            onConnected={() => setJoined(true)}
            onDisconnected={() => setJoined(false)}
            onError={(e) => setError(e?.message || "LiveKit call error")}
          >
            <VideoConference />
          </LiveKitRoom>
        </div>

        <div className="flex items-center gap-3 p-4">
          {!captureStarted ? (
            <Button icon={PlayCircle} onClick={startCapture} disabled={!joined || starting} loading={starting}>
              Start verification capture
            </Button>
          ) : (
            <Button variant="danger" icon={StopCircle} onClick={stopCapture}>
              Stop &amp; finalize
            </Button>
          )}
          {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
        </div>
      </Card>

      <LiveStatusCard status={status} framesAlive={framesAlive} />
    </div>
  );
}