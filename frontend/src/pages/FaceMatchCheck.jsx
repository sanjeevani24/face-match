import { useState } from "react";
import { ShieldAlert, RotateCcw } from "lucide-react";
import UploadCard from "../components/verification/UploadCard.jsx";
import Button from "../components/common/Button.jsx";
import Card from "../components/common/Card.jsx";
import Loader from "../components/common/Loader.jsx";
import FaceMatchResultCard from "../components/verification/FaceMatchResultCard.jsx";
import { checkFaceMatch } from "../services/verificationApi.js";

export default function FaceMatchCheck() {
  const [aadhaarFile, setAadhaarFile] = useState(null);
  const [aadhaarPreview, setAadhaarPreview] = useState(null);
  const [selfieFile, setSelfieFile] = useState(null);
  const [selfiePreview, setSelfiePreview] = useState(null);

  const [isChecking, setIsChecking] = useState(false);
  const [result, setResult] = useState(null);
  const [errorMessage, setErrorMessage] = useState(null);

  const handleAadhaarSelected = (file) => {
    setAadhaarFile(file);
    setAadhaarPreview(URL.createObjectURL(file));
    setErrorMessage(null);
  };

  const handleSelfieSelected = (file) => {
    setSelfieFile(file);
    setSelfiePreview(URL.createObjectURL(file));
    setErrorMessage(null);
  };

  const handleCheck = async () => {
    setErrorMessage(null);
    setIsChecking(true);
    try {
      const data = await checkFaceMatch(aadhaarFile, selfieFile);
      setResult(data);
    } catch (err) {
      setErrorMessage(
        err.response?.data?.detail || err.message || "Face match check failed. Please try again."
      );
    } finally {
      setIsChecking(false);
    }
  };

  const handleReset = () => {
    setAadhaarFile(null);
    setAadhaarPreview(null);
    setSelfieFile(null);
    setSelfiePreview(null);
    setResult(null);
    setErrorMessage(null);
  };

  return (
    <div className="flex flex-col gap-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-ink)]">Face Match Check</h2>
        <p className="text-sm text-[var(--color-ink-faint)]">
          Upload an Aadhaar photo and a selfie to run antispoofing and similarity comparison directly,
          without the live liveness challenge flow.
        </p>
      </div>

      {errorMessage && (
        <div className="flex items-start gap-2 rounded-xl border border-[var(--color-danger)]/30 bg-[var(--color-danger)]/5 p-3 text-sm text-[var(--color-danger)]">
          <ShieldAlert className="mt-0.5 size-4 shrink-0" />
          <span>{errorMessage}</span>
        </div>
      )}

      {!result && (
        <div className="flex flex-col gap-4">
          <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
            <UploadCard
              title="Aadhaar Photo"
              file={aadhaarFile}
              preview={aadhaarPreview}
              onFileSelected={handleAadhaarSelected}
              onClear={() => {
                setAadhaarFile(null);
                setAadhaarPreview(null);
              }}
            />
            <UploadCard
              title="Selfie"
              subtitle="Clear, front-facing photo of your face"
              invalidTypeMessage="Please upload a JPG, PNG, or WEBP image of your selfie."
              previewAlt="Selfie preview"
              file={selfieFile}
              preview={selfiePreview}
              onFileSelected={handleSelfieSelected}
              onClear={() => {
                setSelfieFile(null);
                setSelfiePreview(null);
              }}
            />
          </div>

          <div className="flex justify-end">
            <Button onClick={handleCheck} disabled={!aadhaarFile || !selfieFile} loading={isChecking}>
              Run Face Match Check
            </Button>
          </div>
        </div>
      )}

      {isChecking && !result && (
        <Card>
          <div className="flex flex-col items-center gap-3 py-10">
            <Loader size="lg" label="Running antispoofing and face comparison…" />
          </div>
        </Card>
      )}

      {result && (
        <FaceMatchResultCard
          result={result}
          aadhaarPreview={aadhaarPreview}
          selfiePreview={selfiePreview}
          onRestart={handleReset}
        />
      )}
    </div>
  );
}