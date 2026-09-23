"use client";

import { FormEvent, useState } from "react";
import {
  completeBusinessOnboarding,
  login,
  register,
  type SessionUser,
} from "../lib/api";

type AuthMode = "login" | "register" | "onboarding";

export default function ConnectGate({ onConnected }: { onConnected: () => void }) {
  const [mode, setMode] = useState<AuthMode>("login");
  const [identifier, setIdentifier] = useState("");
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [businessName, setBusinessName] = useState("");
  const [industry, setIndustry] = useState("distribution");
  const [currency, setCurrency] = useState("INR");
  const [timezone, setTimezone] = useState("Asia/Kolkata");
  const [fiscalYearStartMonth, setFiscalYearStartMonth] = useState("4");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function beginOnboarding(user: SessionUser) {
    setBusinessName(user.business.name);
    setIndustry(user.business.industry);
    setCurrency(user.business.currency_code || "INR");
    setTimezone(user.business.timezone || "Asia/Kolkata");
    setFiscalYearStartMonth(String(user.business.fiscal_year_start_month || 4));
    setMode("onboarding");
  }

  async function submit(e: FormEvent) {
    e.preventDefault();
    setBusy(true);
    setError("");

    try {
      if (mode === "login") {
        const result = await login(identifier.trim(), password);
        if (result.user.business.onboarding_completed) onConnected();
        else beginOnboarding(result.user);
        return;
      }

      if (mode === "register") {
        const result = await register({
          username: username.trim(),
          email: email.trim() || undefined,
          phone: phone.trim() || undefined,
          password,
          business_name: businessName.trim(),
          industry: industry.trim(),
        });
        if (result.user.business.onboarding_completed) onConnected();
        else beginOnboarding(result.user);
        return;
      }

      await completeBusinessOnboarding({
        name: businessName.trim(),
        industry: industry.trim(),
        currency_code: currency.trim().toUpperCase(),
        timezone: timezone.trim(),
        fiscal_year_start_month: Number(fiscalYearStartMonth),
      });
      onConnected();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Unable to continue.");
    } finally {
      setBusy(false);
    }
  }

  const isOnboarding = mode === "onboarding";

  return (
    <section className="connectGate">
      <div className="connectCard">
        <div className="connectBrand">
          <span className="brandMark"><span>✦</span></span>
          <div>
            <span className="eyebrow">BUSINESS BRAIN</span>
            <h2>
              {mode === "login"
                ? "Welcome back."
                : mode === "register"
                  ? "Create your workspace."
                  : "Set up your business."}
            </h2>
          </div>
        </div>

        <p className="connectLead">
          {mode === "login"
            ? "Sign in to your Business Brain workspace. Your business connection is handled automatically."
            : mode === "register"
              ? "Create a Business Brain account and your private business workspace."
              : "A few details help Business Brain interpret your data correctly. You can update these later."}
        </p>

        <form onSubmit={submit} className="connectForm">
          <div className="connectSection">
            {mode === "login" && (
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
              </>
            )}

            {mode === "register" && (
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

            {isOnboarding && (
              <>
                <div className="connectOnboardingStep">
                  <span className="eyebrow">BUSINESS PROFILE · 1 OF 1</span>
                  <p>These settings are used for reporting periods, currency formatting and time-based analysis.</p>
                </div>
                <label className="connectField">
                  <span>Business name</span>
                  <input value={businessName} onChange={(e) => setBusinessName(e.target.value)} placeholder="ABC Electricals" autoFocus />
                </label>
                <label className="connectField">
                  <span>Industry</span>
                  <input value={industry} onChange={(e) => setIndustry(e.target.value)} placeholder="distribution" />
                </label>
                <label className="connectField">
                  <span>Currency</span>
                  <input value={currency} onChange={(e) => setCurrency(e.target.value.toUpperCase())} placeholder="INR" maxLength={3} />
                </label>
                <label className="connectField">
                  <span>Timezone</span>
                  <input value={timezone} onChange={(e) => setTimezone(e.target.value)} placeholder="Asia/Kolkata" />
                </label>
                <label className="connectField">
                  <span>Financial year starts in</span>
                  <select value={fiscalYearStartMonth} onChange={(e) => setFiscalYearStartMonth(e.target.value)}>
                    <option value="1">January</option>
                    <option value="2">February</option>
                    <option value="3">March</option>
                    <option value="4">April</option>
                    <option value="5">May</option>
                    <option value="6">June</option>
                    <option value="7">July</option>
                    <option value="8">August</option>
                    <option value="9">September</option>
                    <option value="10">October</option>
                    <option value="11">November</option>
                    <option value="12">December</option>
                  </select>
                </label>
                <button className="connectPrimary" disabled={busy}>
                  {busy ? "Saving…" : "Finish setup →"}
                </button>
              </>
            )}
          </div>
        </form>

        {error && <div className="connectError">{error}</div>}

        {!isOnboarding && (
          <button
            type="button"
            className="authModeSwitch"
            onClick={() => { setMode(mode === "login" ? "register" : "login"); setError(""); }}
          >
            {mode === "login" ? "New to Business Brain? Create an account" : "Already have an account? Sign in"}
          </button>
        )}

        <p className="connectFootnote">
          Business IDs, connector credentials and API keys are infrastructure details and are never required here.
        </p>
      </div>
    </section>
  );
}
