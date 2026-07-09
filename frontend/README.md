# SK Finance — eKYC Verification Frontend

React (Vite) + Tailwind v4 dashboard frontend for the eKYC system, wired to the
FastAPI backend (`/face-match`, `/liveness`, with the session-based
`/verification/*` endpoints stubbed for when they ship).

## Quick start

```bash
npm install
cp .env.example .env      # then set VITE_API_URL to your backend, e.g. http://localhost:8000
npm run dev
```

Open the printed local URL. **Camera access requires either `https://` or
`localhost`** — browsers refuse `getUserMedia` on plain `http://` for any
other host (this matters when testing from a phone on your LAN; see "Testing
camera on another device" below).

## What's wired up vs. what's a placeholder

| Area | Status |
|---|---|
| Upload Aadhaar → `UploadCard` | Done — client-side validation, drag & drop |
| Live camera → `WebcamCard` / `useCamera` | Done — real `getUserMedia`, no mock data |
| Liveness challenge → `POST /liveness` | Done — sends one frame per challenge |
| Face match → `POST /face-match` | Done — sends Aadhaar file + best live frame |
| Dashboard stats / history | Placeholder — no backend endpoint exists yet for this |
| Auth / JWT | Placeholder — `api.js` already reads a token from `localStorage` if present |
| Session-based `/verification/*` flow | Stubbed in `verificationApi.js`, off by default |

## Architecture: continuous session streaming, not one-shot capture

The live challenge flow talks to a **session-based** `/liveness` API backed
by `agents/liveness_session.py::LivenessSession` (see `backend_patch/` at the
repo root for the exact FastAPI routes to add):

1. `POST /liveness/start` — uploads the Aadhaar image once, returns a `session_id`
2. `POST /liveness/frame` — the browser posts one captured frame roughly
   every 350ms (see `FRAME_INTERVAL_MS` in `utils/constants.js`) for as long
   as the challenge step is on screen; each response carries the current
   challenge instruction, capture progress, and (once everything is
   complete) the verification result — all in one round trip, since
   `LivenessSession.verify()` runs face matching internally the moment the
   challenge sequence finishes and a stable frame is captured.
3. `DELETE /liveness/session/{id}` — best-effort cleanup if the user leaves mid-flow

This replaced an earlier version of this frontend that called `/liveness`
once per challenge expecting a `challenge` field — that doesn't match how
`LivenessSession` actually works (it tracks challenge progress itself,
across many frames, and doesn't need the client to say which challenge it's
attempting).

`POST /face-match/` (fields: `aadhaar`, `selfie`) still exists as a
standalone endpoint and is wired up in `verificationApi.js` as
`matchFaces()`, but the main flow doesn't call it — verification already
happens inside the liveness session.

## What's wired up vs. what's a placeholder

| Area | Status |
|---|---|
| Upload Aadhaar → `UploadCard` | Done — client-side validation, drag & drop |
| Live camera → `WebcamCard` / `useCamera` | Done — real `getUserMedia`, continuous capture mode |
| Liveness + face match → `/liveness/start`, `/liveness/frame` | Done — see backend_patch/ for the routes this needs |
| Dashboard stats / history | Placeholder — no backend endpoint exists yet for this |
| Auth / JWT | Placeholder — `api.js` already reads a token from `localStorage` if present |

## Backend changes required (see `backend_patch/`)

Your existing `/liveness` route wraps `LivenessAgent.run()`, which opens the
**server's own webcam** via `cv2.VideoCapture` in an infinite loop — that's
unusable from a browser frontend, since the frontend can't see or drive that
loop. `LivenessSession` (in `liveness_session.py`) is already built the right
way — one `process_frame(frame)` call per frame, tracking challenge state
across calls — it just has no route exposing it yet.

Two files to add/replace in your backend, included alongside this frontend:

- `backend_patch/api/liveness.py` — new session-based router
  (`/liveness/start`, `/liveness/frame`, `/liveness/session/{id}`).
  `LivenessAgent`/`cv2.imshow`/`cv2.VideoCapture` are no longer touched by
  the API at all.
- `backend_patch/agents/liveness_session.py` — your `LivenessSession` with
  one small fix: `face_detected` in the response now reflects whether a
  face was actually found in that frame, instead of always being `True`.

Drop these into your backend at the matching paths (they're already wired to
your existing `FileUtils`, `ChallengeService`, `CaptureService`,
`VerificationAgent` — no other files need to change), and since the router
still uses `prefix="/liveness"`, no change to how it's included in `main.py`
should be needed if it's already registered.

**Still unknown / worth confirming:** the exact shape
`VerificationAgent.verify()` returns. `ResultCard` reads `match` and
`similarity` off the `verification` field — if your agent returns different
keys, adjust `ResultCard.jsx` (search for `result.match`).

## Backend contract

## Camera support notes (`src/hooks/useCamera.js`)

This was built as a custom hook rather than a wrapper library, specifically
so behavior across browsers is explicit and debuggable:

- **Secure-context check**: `getUserMedia` is undefined outside `https://` /
  `localhost`. The UI shows a clear message instead of a silent failure.
- **Safari (desktop + iOS)**: requires `playsInline` and `muted` on the
  `<video>` element for autoplay to work at all — both are set.
- **Device enumeration**: camera labels/IDs are only populated by
  `enumerateDevices()` *after* permission has been granted once, so the hook
  re-enumerates right after the first successful stream.
- **Multiple cameras**: `WebcamCard` shows a "Switch" button once more than
  one video input is detected, cycling through them; on mobile it falls back
  to flipping `facingMode` between `user`/`environment` if only one physical
  device is enumerated (common on iOS).
- **Track cleanup**: every stream's tracks are explicitly `.stop()`-ed on
  unmount and before requesting a new stream, which avoids the
  `NotReadableError: Could not start video source` that Firefox/Safari throw
  if a previous stream is left dangling.
- **Error mapping**: `NotAllowedError`, `NotFoundError`, `NotReadableError`,
  `OverconstrainedError`, and `SecurityError` are each translated into a
  plain-language message shown directly in `WebcamCard`.
- **Capture**: frames are captured via a hidden `<canvas>` +
  `drawImage`/`toDataURL`, which is the one approach that behaves
  identically across Chrome, Safari, Firefox, and Edge (no
  browser-specific screenshot API is used).

## Testing camera on another device (phone, etc.)

Since camera access needs a secure context, testing from a phone over your
LAN needs either:

1. A tunnel (e.g. `npx localtunnel --port 5173` or ngrok), or
2. Local HTTPS: run `vite --https` (Vite will generate a self-signed cert) and
   accept the certificate warning on the phone once.

`vite.config.js` has a commented-out `https: true` line as a starting point.

## Project structure

```
src/
  components/
    common/        Button, Card, Loader, ProgressBar (+StepIndicator)
    layout/         Sidebar, Header, DashboardLayout
    dashboard/      Statistics, RecentVerification
    verification/   UploadCard, WebcamCard, ChallengeCard, StatusCard, ResultCard
  pages/            Dashboard, Verification, History
  services/         api.js (axios instance), verificationApi.js (backend calls)
  hooks/            useCamera.js
  context/          VerificationContext.jsx (flow state)
  utils/            constants.js, media.js

backend_patch/       Drop-in files for your FastAPI backend — see above
  api/liveness.py
  agents/liveness_session.py
```

## Environment variables

| Var | Purpose |
|---|---|
| `VITE_API_URL` | Base URL of the FastAPI backend, no trailing slash |
| `VITE_API_TIMEOUT` | Axios request timeout in ms (default 15000) |

No API URLs are hardcoded anywhere in the codebase — everything routes
through `src/services/api.js`.
