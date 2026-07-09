export const VERIFICATION_STEP = {
  UPLOAD: "upload",
  CHALLENGE: "challenge",
  RESULT: "result",
};

export const VERIFICATION_STATUS = {
  IDLE: "idle",
  IN_PROGRESS: "in_progress",
  PASSED: "passed",
  FAILED: "failed",
  ERROR: "error",
};

// Mirrors the backend's cosine-similarity threshold (see similarity_service.py)
// so the UI can show a meaningful confidence label without another round trip.
export const MATCH_THRESHOLD = 0.55;

// How often (ms) the browser captures + posts a frame to /liveness/frame
// while a challenge is in progress. challenge_service.py requires 15
// consecutive successful frames for LEFT/RIGHT/UP, so this needs to be
// frequent enough to feel responsive without flooding the backend.
export const FRAME_INTERVAL_MS = 120;
