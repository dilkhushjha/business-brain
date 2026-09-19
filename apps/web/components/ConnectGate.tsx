"use client";

import { FormEvent, useState } from "react";
import { getBusinessId, registerAndConnect, setBusinessId, setToken } from "../lib/api";

export default function ConnectGate({ onConnected }: { onConnected: () => void }) {
  const [businessId, setBusinessIdInput] = useState(getBusinessId());
  const [registrationKey, setRegistrationKey] = useState("");
  const [existingToken, setExistingToken] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function handleRegister(e: FormEvent) {
    e.preventDefault();
    if (!businessId.trim()) {
      setError("Business ID is required.");
      return;
    }
    setBusy(true);
    setError("");
    try {
      await registerAndConnect(businessId.trim(), registrationKey.trim() || undefined);
      onConnected();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Registration failed.");
    } finally {
      setBusy(false);
    }
  }

  function handleUseExisting(e: FormEvent) {
    e.preventDefault();
    if (!businessId.trim() || !existingToken.trim()) {
      setError("Business ID and token are both required.");
      return;
    }
    setBusinessId(businessId.trim());
    setToken(businessId.trim(), existingToken.trim());
    onConnected();
  }

  return (
    <section className="connectGate">
      <div className="connectCard">
        <div className="connectBrand">
          <span className="brandMark"><span>✦</span></span>
          <div>
            <span className="eyebrow">BUSINESS BRAIN</span>
            <h2>Welcome back.</h2>
          </div>
        </div>
        <p className="connectLead">Connect your business workspace to unlock evidence-backed intelligence, metrics and recommendations.</p>

        <form onSubmit={handleRegister} className="connectForm">
          <div className="connectSection">
            <div className="connectSectionTitle"><span>01</span><div><b>Business workspace</b><small>Identify the business you want to access.</small></div></div>
            <label className="connectField">
              <span>Business ID</span>
              <input value={businessId} onChange={(e) => setBusinessIdInput(e.target.value)} placeholder="Enter business UUID" autoComplete="organization" />
            </label>
            <label className="connectField">
              <span>Registration key <em>optional for local development</em></span>
              <input value={registrationKey} onChange={(e) => setRegistrationKey(e.target.value)} placeholder="Enter registration key" type="password" autoComplete="off" />
            </label>
            <button className="connectPrimary" disabled={busy}>{busy ? "Connecting…" : "Connect to Business Brain →"}</button>
          </div>
        </form>

        <div className="connectDivider"><span>or</span></div>

        <form onSubmit={handleUseExisting} className="connectForm">
          <div className="connectSection secondary">
            <div className="connectSectionTitle"><span>02</span><div><b>Existing access</b><small>Use an API token you already received.</small></div></div>
            <label className="connectField">
              <span>API access token</span>
              <input value={existingToken} onChange={(e) => setExistingToken(e.target.value)} placeholder="Paste your token" type="password" autoComplete="current-password" />
            </label>
            <button className="connectSecondary" type="submit">Use existing token</button>
          </div>
        </form>

        {error && <div className="connectError">{error}</div>}
        <p className="connectFootnote">Your access token is stored locally in this browser and attached to Business Brain API requests.</p>
      </div>
    </section>
  );
}
