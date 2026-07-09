import { useCallback, useRef, useState } from "react";
import { UploadCloud, FileCheck2, X } from "lucide-react";
import Card from "../common/Card.jsx";
import Button from "../common/Button.jsx";

const ACCEPTED_TYPES = ["image/jpeg", "image/png", "image/webp"];
const MAX_SIZE_MB = 8;

export default function UploadCard({
  file,
  preview,
  onFileSelected,
  onClear,
  title = "Upload Aadhaar",
  subtitle = "Front side, clear and unobstructed photo of the Aadhaar card",
  invalidTypeMessage = "Please upload a JPG, PNG, or WEBP image of the Aadhaar card.",
  previewAlt = "Aadhaar preview",
}) {
  const inputRef = useRef(null);
  const [dragActive, setDragActive] = useState(false);
  const [validationError, setValidationError] = useState(null);

  const validateAndSet = useCallback(
    (selected) => {
      if (!selected) return;
      if (!ACCEPTED_TYPES.includes(selected.type)) {
        setValidationError(invalidTypeMessage);
        return;
      }
      if (selected.size > MAX_SIZE_MB * 1024 * 1024) {
        setValidationError(`File is too large. Maximum size is ${MAX_SIZE_MB}MB.`);
        return;
      }
      setValidationError(null);
      onFileSelected(selected);
    },
    [onFileSelected, invalidTypeMessage]
  );

  const handleDrop = (e) => {
    e.preventDefault();
    setDragActive(false);
    validateAndSet(e.dataTransfer.files?.[0]);
  };

  return (
    <Card title={title} subtitle={subtitle}>
      {!file ? (
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragActive(true);
          }}
          onDragLeave={() => setDragActive(false)}
          onDrop={handleDrop}
          onClick={() => inputRef.current?.click()}
          className={`flex cursor-pointer flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed py-10 text-center transition-colors ${
            dragActive
              ? "border-[var(--color-brand-blue)] bg-[var(--color-brand-blue)]/5"
              : "border-[var(--color-border)] hover:border-[var(--color-brand-blue)]/50"
          }`}
        >
          <UploadCloud className="size-8 text-[var(--color-brand-blue)]" />
          <p className="text-sm font-medium text-[var(--color-ink)]">Drag & drop or click to upload</p>
          <p className="text-xs text-[var(--color-ink-faint)]">JPG, PNG or WEBP · up to {MAX_SIZE_MB}MB</p>
          <input
            ref={inputRef}
            type="file"
            accept={ACCEPTED_TYPES.join(",")}
            className="hidden"
            onChange={(e) => validateAndSet(e.target.files?.[0])}
          />
        </div>
      ) : (
        <div className="flex items-center gap-4 rounded-xl border border-[var(--color-border)] p-3">
          <img src={preview} alt={previewAlt} className="size-16 rounded-lg object-cover" />
          <div className="flex-1 min-w-0">
            <p className="flex items-center gap-1.5 text-sm font-medium text-[var(--color-ink)]">
              <FileCheck2 className="size-4 text-[var(--color-brand-green)]" />
              {file.name}
            </p>
            <p className="text-xs text-[var(--color-ink-faint)]">{(file.size / 1024 / 1024).toFixed(2)} MB</p>
          </div>
          <Button variant="ghost" size="sm" icon={X} onClick={onClear}>
            Remove
          </Button>
        </div>
      )}
      {validationError && <p className="mt-2 text-xs text-[var(--color-danger)]">{validationError}</p>}
    </Card>
  );
}