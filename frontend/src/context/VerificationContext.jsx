import { createContext, useCallback, useContext, useMemo, useState } from "react";
import { VERIFICATION_STEP, VERIFICATION_STATUS } from "../utils/constants.js";

const VerificationContext = createContext(null);

export function VerificationProvider({ children }) {
  const [step, setStep] = useState(VERIFICATION_STEP.UPLOAD);
  const [status, setStatus] = useState(VERIFICATION_STATUS.IDLE);
  const [aadhaarFile, setAadhaarFile] = useState(null);
  const [aadhaarPreview, setAadhaarPreview] = useState(null);
  const [bestFrame, setBestFrame] = useState(null); // data URL of the last/best captured live frame
  const [matchResult, setMatchResult] = useState(null); // verification_agent.verify() output
  const [errorMessage, setErrorMessage] = useState(null);

  const reset = useCallback(() => {
    setStep(VERIFICATION_STEP.UPLOAD);
    setStatus(VERIFICATION_STATUS.IDLE);
    setAadhaarFile(null);
    setAadhaarPreview(null);
    setBestFrame(null);
    setMatchResult(null);
    setErrorMessage(null);
  }, []);

  const value = useMemo(
    () => ({
      step,
      setStep,
      status,
      setStatus,
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
    }),
    [step, status, aadhaarFile, aadhaarPreview, bestFrame, matchResult, errorMessage, reset]
  );

  return <VerificationContext.Provider value={value}>{children}</VerificationContext.Provider>;
}

export function useVerification() {
  const ctx = useContext(VerificationContext);
  if (!ctx) throw new Error("useVerification must be used within a VerificationProvider");
  return ctx;
}
