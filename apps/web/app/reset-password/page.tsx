"use client";

import { FormEvent, useMemo, useState } from "react";
import { confirmPasswordReset } from "../../lib/api";

export default function ResetPasswordPage() {
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const token = useMemo(() => {
    if (typeof window === "undefined") return "";
    return new URLSearchParams(window.location.search).get("token") || "";
  }, []);

  async function submit(event: FormEvent) {
    event.preventDefault();
    setError("");
    setMessage("");
    if (!token) { setError("This password reset link is invalid."); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    if (password !== confirm) { setError("Passwords do not match."); return; }
    setBusy(true);
    try {
      const result = await confirmPasswordReset(token, password);
      setMessage(result.detail);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to reset your password.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <main style={{ minHeight: "100vh", display: "grid", placeItems: "center", padding: 24 }}>
      <section className="connectCard" style={{ width: "min(460px, 100%)" }}>
        <span className="eyebrow">BUSINESS BRAIN</span>
        <h2>Reset your password.</h2>
        <p className="connectLead">Choose a new password for your Business Brain account.</p>
        <form onSubmit={submit} className="connectForm">
          <label className="connectField"><span>New password</span><input type="password" value={password} onChange={(e) => setPassword(e.target.value)} autoComplete="new-password" /></label>
          <label className="connectField"><span>Confirm password</span><input type="password" value={confirm} onChange={(e) => setConfirm(e.target.value)} autoComplete="new-password" /></label>
          <button className="connectPrimary" disabled={busy || !token}>{busy ? "Updating…" : "Update password →"}</button>
        </form>
        {error && <div className="connectError">{error}</div>}
        {message && <div className="connectSuccess">{message} You can now return to the sign-in screen.</div>}
      </section>
    </main>
  );
}
