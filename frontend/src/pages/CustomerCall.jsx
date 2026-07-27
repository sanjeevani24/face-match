import { useEffect, useState } from "react";
import { LiveKitRoom, VideoConference } from "@livekit/components-react";
import "@livekit/components-styles";
import { AlertTriangle } from "lucide-react";
import Loader from "../components/common/Loader.jsx";
import { getCallJoinInfo, consumeCallLink } from "../services/verificationApi.js";

function useQueryParams() {
  const params = new URLSearchParams(window.location.search);
  return {
    roomId: params.get("room_id"),
    linkToken: params.get("link_token"),
  };
}

export default function CustomerCall() {
  const { roomId, linkToken } = useQueryParams();

  const [state, setState] = useState("validating"); // validating | ready | joined | error
  const [error, setError] = useState(null);
  const [joinInfo, setJoinInfo] = useState(null); // { room_url, meeting_token }
  const [consumed, setConsumed] = useState(false);

  useEffect(() => {
    if (!roomId || !linkToken) {
      setState("error");
      setError("This link is missing required details. Ask for a new verification link.");
      return;
    }

    let cancelled = false;
    (async () => {
      try {
        const data = await getCallJoinInfo(roomId, linkToken);
        if (cancelled) return;
        setJoinInfo(data);
        setState("ready");
      } catch (e) {
        if (cancelled) return;
        setState("error");
        const status = e?.response?.status;
        setError(
          status === 410
            ? "This link has already been used or has expired."
            : e?.response?.data?.detail || "This link isn't valid. Ask for a new verification link."
        );
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [roomId, linkToken]);

  async function handleConnected() {
    setState("joined");
    // Mark the link consumed only once the join truly succeeds, so a
    // page refresh before this point doesn't burn the customer's link.
    if (!consumed) {
      setConsumed(true);
      await consumeCallLink(roomId);
    }
  }

  return (
    <div className="flex h-screen w-screen flex-col bg-[var(--color-ink)]">
      {state !== "joined" && (
        <div className="flex items-center gap-2 border-b border-white/10 px-4 py-3 text-sm text-white/80">
          {state === "error" ? (
            <>
              <AlertTriangle className="size-4 text-[var(--color-danger)]" />
              <span>{error}</span>
            </>
          ) : (
            <Loader label={state === "validating" ? "Checking your link…" : "Joining the call…"} />
          )}
        </div>
      )}

      {joinInfo && (
        <div className="flex-1">
          <LiveKitRoom
            serverUrl={joinInfo.room_url}
            token={joinInfo.meeting_token}
            connect
            video
            audio
            data-lk-theme="default"
            style={{ height: "100%" }}
            onConnected={handleConnected}
            onDisconnected={() => setState("ready")}
            onError={(e) => {
              setState("error");
              setError(e?.message || "The call could not be started.");
            }}
          >
            <VideoConference />
          </LiveKitRoom>
        </div>
      )}
    </div>
  );
}