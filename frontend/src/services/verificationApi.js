import api from "./api.js";
import { dataUrlToFile } from "../utils/media.js";

/**
 * ---------------------------------------------------------------------------
 * Endpoint contract — matches the session-based /liveness router
 * (api/liveness.py wrapping agents/liveness_session.py::LivenessSession)
 * ---------------------------------------------------------------------------
 *   POST /liveness/start   multipart: aadhaar (file)
 *                           -> { session_id, challenge, challenge_index,
 *                                challenge_total, progress, finished,
 *                                face_detected, verification, capture }
 *
 *   POST /liveness/frame    multipart: session_id (form field), frame (file)
 *                           -> same shape as above, updated for this frame
 *
 *   DELETE /liveness/session/{session_id}
 *                           -> { cancelled: boolean } — best-effort cleanup
 *
 * LivenessSession.verify() runs face matching internally the moment the
 * challenge sequence + a stable capture are both complete, so there is no
 * separate "call /face-match after liveness passes" step in this flow —
 * `verification` arrives already populated on the frame response where
 * `finished: true`.
 *
 * `verification_agent.verify()`'s exact return shape wasn't provided, so
 * ResultCard reads `match` / `similarity` off it. If your agent returns
 * different keys (e.g. `is_match` / `score`), that's the only place to
 * adjust — see components/verification/ResultCard.jsx.
 * ---------------------------------------------------------------------------
 */

/**
 * Start a liveness/verification session for one Aadhaar upload.
 * @param {File} aadhaarFile
 * @returns {Promise<object>} initial session state, including session_id
 */
export async function startLivenessSession(aadhaarFile) {
  const formData = new FormData();
  formData.append("aadhaar", aadhaarFile);

  const { data } = await api.post("/liveness/start", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * Post one browser-captured frame for the active session.
 * @param {string} sessionId
 * @param {string} frameDataUrl - base64 data URL from the webcam canvas
 * @returns {Promise<object>} updated session state
 */
export async function sendLivenessFrame(sessionId, frameDataUrl) {
  const formData = new FormData();
  formData.append("session_id", sessionId);
  formData.append("frame", dataUrlToFile(frameDataUrl, "frame.jpg"));

  const { data } = await api.post("/liveness/frame", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

/**
 * Best-effort cleanup if the user leaves mid-session. Safe to fire-and-forget.
 * @param {string} sessionId
 */
export async function cancelLivenessSession(sessionId) {
  if (!sessionId) return;
  try {
    await api.delete(`/liveness/session/${sessionId}`);
  } catch {
    // Non-fatal — the backend can also expire stale sessions on its own.
  }
}

// ---------------------------------------------------------------------------
// Standalone face-match endpoint (POST /face-match/, fields: aadhaar, selfie).
// Not used by the main liveness-session flow above (verification already
// happens inside LivenessSession.verify()), but kept available in case you
// want a manual re-check against a specific captured image elsewhere in the
// app.
// ---------------------------------------------------------------------------
export async function matchFaces(aadhaarFile, liveFrameDataUrl) {
  const formData = new FormData();
  formData.append("aadhaar", aadhaarFile);
  formData.append("selfie", dataUrlToFile(liveFrameDataUrl, "selfie.jpg"));

  const { data } = await api.post("/face-match/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}

// ... existing exports (startLivenessSession, sendLivenessFrame, cancelLivenessSession) stay unchanged

export async function checkFaceMatch(aadhaarFile, selfieFile) {
  const formData = new FormData();
  formData.append("aadhaar", aadhaarFile);
  formData.append("selfie", selfieFile);

  // Trailing slash required — router prefix + @router.post("/") means the
  // real path is /face-match/. Without the slash, FastAPI 307-redirects
  // and the multipart body can get silently dropped.
  const { data } = await api.post("/face-match/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return data;
}