import { useEffect, useMemo, useRef, useState } from "react";
import { AlertCircle } from "lucide-react";
import UploadCard from "../components/verification/UploadCard.jsx";
import WebcamCard from "../components/verification/WebcamCard.jsx";
import ChallengeCard from "../components/verification/ChallengeCard.jsx";
import StatusCard from "../components/verification/StatusCard.jsx";
import ResultCard from "../components/verification/ResultCard.jsx";
import Button from "../components/common/Button.jsx";
import Loader from "../components/common/Loader.jsx";
import { useVerification } from "../context/VerificationContext.jsx";
import { startLivenessSession, sendLivenessFrame, cancelLivenessSession } from "../services/verificationApi.js";
import { VERIFICATION_STEP } from "../utils/constants.js";

const STEP_INDEX = {
  [VERIFICATION_STEP.UPLOAD]: 0,
  [VERIFICATION_STEP.CHALLENGE]: 1,
  [VERIFICATION_STEP.RESULT]: 2,
};

export default function Verification() {
  const {
    step,
    setStep,
    aadhaarFile,
    setAadhaarFile,
    aadhaarPreview,
    setAadhaarPreview,
    bestFrame,
    setBestFrame,
    matchResult,
    setMatchResult,
    errorMessage,
    setErrorMessage,
    reset,
  } = useVerification();

  const [sessionId, setSessionId] = useState(null);
  const [isStarting, setIsStarting] = useState(false);
  const [challengeState, setChallengeState] = useState({
    instruction: "",
    challengeIndex: 1,
    challengeTotal: 4,
    progress: 0,
    faceDetected: null,
  });

  // Prevents posting a new frame while a previous /liveness/frame request is
  // still in flight — a session response can take longer than the capture
  // interval, especially the final frame that triggers face verification.
  const isSendingRef = useRef(false);
  const sessionIdRef = useRef(null);

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

  // Best-effort cancel of an abandoned session if the user navigates away
  // mid-challenge (component unmount, e.g. clicking Dashboard in the sidebar).
  useEffect(() => {
    return () => {
      if (sessionIdRef.current) cancelLivenessSession(sessionIdRef.current);
    };
  }, []);

  const stepIndex = STEP_INDEX[step] ?? 0;
  const progress = useMemo(() => (stepIndex / (Object.keys(STEP_INDEX).length - 1)) * 100, [stepIndex]);

  const handleFileSelected = (file) => {
    setAadhaarFile(file);
    setAadhaarPreview(URL.createObjectURL(file));
    setErrorMessage(null);
  };

  const handleClearFile = () => {
    setAadhaarFile(null);
    setAadhaarPreview(null);
  };

  const startChallenge = async () => {
    setErrorMessage(null);
    setIsStarting(true);
    try {
      const res = await startLivenessSession(aadhaarFile);
      setSessionId(res.session_id);
      setChallengeState({
        instruction: res.challenge,
        challengeIndex: res.challenge_index,
        challengeTotal: res.challenge_total,
        progress: res.progress ?? 0,
        faceDetected: res.face_detected,
      });
      setStep(VERIFICATION_STEP.CHALLENGE);
    } catch (err) {
      setErrorMessage(err.message || "Couldn't start the verification session. Please try again.");
    } finally {
      setIsStarting(false);
    }
  };

  const handleFrame = async (frameDataUrl) => {
    if (isSendingRef.current || !sessionIdRef.current) return;
    isSendingRef.current = true;
    try {
      const res = await sendLivenessFrame(sessionIdRef.current, frameDataUrl);
      setChallengeState({
        instruction: res.challenge,
        challengeIndex: res.challenge_index,
        challengeTotal: res.challenge_total,
        progress: res.progress ?? 0,
        faceDetected: res.face_detected,
      });
      setBestFrame(frameDataUrl);

      if (res.finished) {
        setMatchResult(res.verification);
        setStep(VERIFICATION_STEP.RESULT);
      }
    } catch (err) {
      setErrorMessage(err.message || "Lost connection to the verification server.");
    } finally {
      isSendingRef.current = false;
    }
  };

  const handleRestart = () => {
    if (sessionIdRef.current) cancelLivenessSession(sessionIdRef.current);
    setSessionId(null);
    reset();
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-ink)]">New Verification</h2>
        <p className="text-sm text-[var(--color-ink-faint)]">
          Upload the Aadhaar card, then complete the live liveness challenge to verify identity.
        </p>
      </div>

      <StatusCard stepIndex={stepIndex} progress={progress} />

      {errorMessage && (
        <div className="flex items-start gap-2 rounded-xl border border-[var(--color-danger)]/30 bg-[var(--color-danger)]/5 p-3 text-sm text-[var(--color-danger)]">
          <AlertCircle className="mt-0.5 size-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {step === VERIFICATION_STEP.UPLOAD && (
        <div className="flex flex-col gap-4">
          <UploadCard
            file={aadhaarFile}
            preview={aadhaarPreview}
            onFileSelected={handleFileSelected}
            onClear={handleClearFile}
          />
          <div className="flex justify-end">
            <Button onClick={startChallenge} disabled={!aadhaarFile} loading={isStarting}>
              Continue to Camera
            </Button>
          </div>
        </div>
      )}

      {step === VERIFICATION_STEP.CHALLENGE && (
        <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
          <WebcamCard active continuous onCapture={handleFrame} />
          <ChallengeCard
            instruction={challengeState.instruction}
            challengeIndex={challengeState.challengeIndex}
            challengeTotal={challengeState.challengeTotal}
            progress={challengeState.progress}
            faceDetected={challengeState.faceDetected}
          />
        </div>
      )}

      {step === VERIFICATION_STEP.RESULT && !matchResult && (
        <div className="card flex flex-col items-center gap-3 py-16">
          <Loader size="lg" label="Finalizing verification…" />
        </div>
      )}

      {step === VERIFICATION_STEP.RESULT && matchResult && (
        <ResultCard result={matchResult} liveFrame={bestFrame} onRestart={handleRestart} />
      )}
    </div>
  );
}
