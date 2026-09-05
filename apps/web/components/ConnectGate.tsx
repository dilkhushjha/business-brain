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
    <section className="card" style={{ maxWidth: 520, margin: "48px auto" }}>
      <div className="cardTitle">
        <span>🔒</span>
        <h3>Connect to your business</h3>
      </div>
      <p className="muted">
        Every dashboard request now requires an API access token for your business. Register a new
        one below, or paste a token you already have (for example, one printed by the connector's{" "}
        <code>register</code> command).
      </p>

      <form onSubmit={handleRegister} style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
        <label>
          Business ID
          <input value={businessId} onChange={(e) => setBusinessIdInput(e.target.value)} placeholder="Business UUID" />
        </label>
        <label>
          Registration key (leave blank in local development)
          <input
            value={registrationKey}
            onChange={(e) => setRegistrationKey(e.target.value)}
            placeholder="X-Connector-Registration-Key"
          />
        </label>
        <button disabled={busy}>{busy ? "Connecting…" : "Register & connect"}</button>
      </form>

      <form onSubmit={handleUseExisting} style={{ display: "flex", flexDirection: "column", gap: 8, marginTop: 16 }}>
        <label>
          Or paste an existing token
          <input value={existingToken} onChange={(e) => setExistingToken(e.target.value)} placeholder="API token" />
        </label>
        <button type="submit">Use this token</button>
      </form>

      {error && <p className="errorBox">{error}</p>}
    </section>
  );
}
