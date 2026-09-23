"use client";

import { FormEvent, useState } from "react";
import { login, register, requestPasswordReset } from "../lib/api";

export default function ConnectGate({ onConnected }: { onConnected: () => void }) {
  const [mode, setMode] = useState<"login" | "register" | "forgot">("login");
  const [identifier, setIdentifier] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [industry, setIndustry] = useState("distribution");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");
    try {
      if (mode === "login") {
        await login(identifier.trim(), password);
        onConnected();
      } else if (mode === "forgot") {
        await requestPasswordReset(identifier.trim());
        setError("If an account matches, a password reset link has been sent.");
      } else {
        await register({
          username: username.trim(),
          email: email.trim() || undefined,
          phone: phone.trim() || undefined,
          password,
          business_name: businessName.trim(),
          industry: industry.trim(),
        });
        onConnected();
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to authenticate.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <section className="connectGate">
      <div className="connectCard">
        <div className="connectBrand">
          <span className="brandMark"><span>✦</span></span>
          <div>
            <span className="eyebrow">BUSINESS BRAIN</span>
            <h2>{mode === "login" ? "Welcome back." : "Create your workspace."}</h2>
          </div>
        </div>

        <p className="connectLead">
          {mode === "login"
            ? "Sign in to your Business Brain workspace. Your business connection is handled automatically."
            : "Create a Business Brain account and your private business workspace."}
        </p>

        <form onSubmit={submit} className="connectForm">
          <div className="connectSection">
            {mode === "login" ? (
              <>
                <label className="connectField">
                  <span>Email, username or phone</span>
                  <input value={identifier} onChange={(e) => setIdentifier(e.target.value)} placeholder="you@example.com" autoComplete="username" autoFocus />
                </label>
                <label className="connectField">
                  <span>Password</span>
                  <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Enter your password" type="password" autoComplete="current-password" />
                </label>
                <button className="connectPrimary" disabled={busy}>
                  {busy ? "Signing in…" : "Sign in →"}
                </button>
                <button type="button" className="authModeSwitch" onClick={() => { setMode("forgot"); setError(""); }}>
                  Forgot password?
                </button>
              </>
            ) : mode === "forgot" ? (
              <>
                <label className="connectField">
                  <span>Email, username or phone</span>
                  <input value={identifier} onChange={(e) => setIdentifier(e.target.value)} placeholder="you@example.com" autoComplete="username" autoFocus />
                </label>
                <button className="connectPrimary" disabled={busy}>
                  {busy ? "Sending…" : "Send reset link →"}
                </button>
              </>
            ) : (
              <>
                <label className="connectField">
                  <span>Username</span>
                  <input value={username} onChange={(e) => setUsername(e.target.value)} placeholder="yourname" autoComplete="username" autoFocus />
                </label>
                <label className="connectField">
                  <span>Email <em>or phone below</em></span>
                  <input value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" type="email" autoComplete="email" />
                </label>
                <label className="connectField">
                  <span>Phone <em>optional if email is provided</em></span>
                  <input value={phone} onChange={(e) => setPhone(e.target.value)} placeholder="+91..." autoComplete="tel" />
                </label>
                <label className="connectField">
                  <span>Password</span>
                  <input value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 8 characters" type="password" autoComplete="new-password" />
                </label>
                <label className="connectField">
                  <span>Business name</span>
                  <input value={businessName} onChange={(e) => setBusinessName(e.target.value)} placeholder="ABC Electricals" autoComplete="organization" />
                </label>
                <label className="connectField">
                  <span>Industry</span>
                  <input value={industry} onChange={(e) => setIndustry(e.target.value)} placeholder="distribution" />
                </label>
                <button className="connectPrimary" disabled={busy}>
                  {busy ? "Creating…" : "Create account →"}
                </button>
              </>
            )}
          </div>
        </form>

        {error && <div className="connectError">{error}</div>}

        <button
          type="button"
          className="authModeSwitch"
          onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
        >
          {mode === "login" ? "New to Business Brain? Create an account" : mode === "forgot" ? "Back to sign in" : "Already have an account? Sign in"}
        </button>

        <p className="connectFootnote">
          Business IDs, connector credentials and API keys are infrastructure details and are never required here.
        </p>
      </div>
    </section>
  );
}
