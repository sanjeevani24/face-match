import { useState } from "react";
import { PhoneCall, Copy, ExternalLink, Check, Search } from "lucide-react";
import Card from "../components/common/Card.jsx";
import Button from "../components/common/Button.jsx";
import { createCallSession, getApplicant } from "../services/verificationApi.js";

export default function CallSessionTest() {
  const [applicantId, setApplicantId] = useState("");
  const [aadhaarPath, setAadhaarPath] = useState("");
  const [creating, setCreating] = useState(false);
  const [error, setError] = useState(null);
  const [session, setSession] = useState(null);
  const [copied, setCopied] = useState(false);

  const [fetchingApplicant, setFetchingApplicant] = useState(false);
  const [applicantError, setApplicantError] = useState(null);
  const [applicantFound, setApplicantFound] = useState(false);

  async function handleFetchApplicant() {
    if (!applicantId) return;
    setApplicantError(null);
    setApplicantFound(false);
    setFetchingApplicant(true);
    try {
      const data = await getApplicant(applicantId);
      setAadhaarPath(data.image_path);
      setApplicantFound(true);
    } catch (err) {
      setAadhaarPath("");
      setApplicantFound(false);
      setApplicantError(
        err?.response?.status === 404
          ? "No applicant found with that ID."
          : err?.response?.data?.detail || err.message || "Could not fetch applicant."
      );
    } finally {
      setFetchingApplicant(false);
    }
  }

  async function handleSubmit(e) {
    e.preventDefault();
    if (!applicantId || !aadhaarPath) {
      setError("Applicant ID and an Aadhaar file path are both required.");
      return;
    }
    setError(null);
    setCreating(true);
    setSession(null);
    try {
      const data = await createCallSession(applicantId, aadhaarPath);
      setSession(data);
    } catch (err) {
      setError(err?.response?.data?.detail || err.message || "Could not create call session.");
    } finally {
      setCreating(false);
    }
  }

  async function copyCustomerLink() {
    if (!session?.customer_join_url) return;
    await navigator.clipboard.writeText(session.customer_join_url);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  }

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-6 p-6">
      <div>
        <h2 className="text-xl font-bold text-[var(--color-ink)]">Call Verification (Test)</h2>
        <p className="text-sm text-[var(--color-ink-faint)]">
          Internal test harness — creates a call session and gives you both join links
          instead of curling <code>/call/sessions</code> by hand.
        </p>
      </div>

      <Card title="Create a call session">
        <form onSubmit={handleSubmit} className="flex flex-col gap-4 p-4">
          <label className="flex flex-col gap-1 text-sm font-medium text-[var(--color-ink)]">
            Applicant ID
            <div className="flex gap-2">
              <input
                type="text"
                value={applicantId}
                onChange={(e) => {
                  setApplicantId(e.target.value);
                  setApplicantFound(false);
                  setApplicantError(null);
                }}
                onBlur={handleFetchApplicant}
                onKeyDown={(e) => {
                  if (e.key === "Enter") {
                    e.preventDefault();
                    handleFetchApplicant();
                  }
                }}
                placeholder="e.g. APPL-3F9A21B0C4"
                className="flex-1 rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm"
              />
              <Button
                type="button"
                variant="outline"
                icon={Search}
                loading={fetchingApplicant}
                onClick={handleFetchApplicant}
                disabled={!applicantId || fetchingApplicant}
              >
                Fetch
              </Button>
            </div>
            {applicantFound && (
              <span className="text-xs text-[var(--color-brand-green)]">
                ✓ Applicant found — Aadhaar path auto-filled below.
              </span>
            )}
            {applicantError && (
              <span className="text-xs text-[var(--color-danger)]">{applicantError}</span>
            )}
          </label>

          <label className="flex flex-col gap-1 text-sm font-medium text-[var(--color-ink)]">
            Aadhaar reference image path (on the backend's machine)
            <input
              type="text"
              value={aadhaarPath}
              onChange={(e) => setAadhaarPath(e.target.value)}
              placeholder="e.g. /Users/you/Desktop/Face_match/samples/sample4_aadhaar.png"
              className="rounded-lg border border-[var(--color-border)] px-3 py-2 text-sm"
            />
            <span className="text-xs text-[var(--color-ink-faint)]">
              Auto-filled from the applicant record when found — you can still edit it manually
              if needed (e.g. testing with a different image).
            </span>
          </label>

          <Button type="submit" icon={PhoneCall} loading={creating} disabled={creating}>
            Create call session
          </Button>

          {error && <p className="text-xs text-[var(--color-danger)]">{error}</p>}
        </form>
      </Card>

      {session && (
        <Card title="Session created">
          <div className="flex flex-col gap-3 p-4">
            <div className="flex items-center justify-between gap-3">
              <div>
                <p className="text-sm font-semibold text-[var(--color-ink)]">Officer link</p>
                <p className="text-xs text-[var(--color-ink-faint)]">Opens in this tab, dashboard chrome.</p>
              </div>
              <a href={session.officer_join_url} target="_blank" rel="noreferrer">
                <Button icon={ExternalLink}>Open</Button>
              </a>
            </div>

            <div className="flex items-center justify-between gap-3 border-t border-[var(--color-border)] pt-3">
              <div>
                <p className="text-sm font-semibold text-[var(--color-ink)]">Customer link</p>
                <p className="text-xs text-[var(--color-ink-faint)]">
                  Copy and open in a second tab or incognito window.
                </p>
              </div>
              <Button icon={copied ? Check : Copy} onClick={copyCustomerLink}>
                {copied ? "Copied" : "Copy"}
              </Button>
            </div>
          </div>
        </Card>
      )}
    </div>
  );
}