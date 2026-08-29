"use client";

import { ChangeEvent, useState } from "react";

const API = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api";
const DEFAULT_BUSINESS_ID = process.env.NEXT_PUBLIC_BUSINESS_ID || "11111111-1111-1111-1111-111111111111";

type Preview = {
  source: string;
  checksum: string;
  rows_read: number;
  rows_accepted: number;
  rows_rejected: number;
  issues: Array<{ row?: number; column?: string; message?: string }>;
};

type ImportResult = Preview & { run_id: string; status: string; sales_created: number };

export default function ImportPage() {
  const [businessId, setBusinessId] = useState(DEFAULT_BUSINESS_ID);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<Preview | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    setFile(event.target.files?.[0] || null);
    setPreview(null);
    setResult(null);
    setError("");
  }

  async function request(path: string) {
    if (!file) throw new Error("Choose a CSV or Excel file first.");
    if (!businessId.trim()) throw new Error("Business ID is required.");
    const form = new FormData();
    form.append("file", file);
    const response = await fetch(`${API}/ingestion/${path}/${businessId}`, { method: "POST", body: form });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.detail || `Import service returned ${response.status}`);
    return data;
  }

  async function previewFile() {
    setBusy(true); setError(""); setResult(null);
    try { setPreview(await request("preview")); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to preview file"); }
    finally { setBusy(false); }
  }

  async function importFile() {
    setBusy(true); setError("");
    try { setResult(await request("record-run")); }
    catch (e) { setError(e instanceof Error ? e.message : "Unable to import file"); }
    finally { setBusy(false); }
  }

  return (
    <main className="shell">
      <header className="header">
        <div><a href="/" className="eyebrow">← BUSINESS BRAIN</a><h1>Import business data</h1></div>
        <span className="status">V1.1 · Data onboarding</span>
      </header>

      <section className="hero">
        <p className="muted">Bring in a Tally, CSV, or Excel export and validate it before it reaches the business database.</p>
      </section>

      <section className="card">
        <div className="field"><label>Business ID</label><input value={businessId} onChange={e => setBusinessId(e.target.value)} /></div>
        <div className="field"><label>Source file</label><input type="file" accept=".csv,.xlsx,.xls" onChange={chooseFile} /></div>
        {file && <p className="muted fileName">Selected: <strong>{file.name}</strong> · {(file.size / 1024).toFixed(1)} KB</p>}
        <div className="actions"><button onClick={previewFile} disabled={busy || !file}>{busy ? "Working…" : "Preview & Validate"}</button></div>
      </section>

      {error && <div className="errorBox">{error}</div>}

      {preview && !result && <section className="card resultCard">
        <span className="eyebrow">VALIDATION PREVIEW</span>
        <h2>{preview.source}</h2>
        <div className="metrics">
          <div className="metric"><span>Rows read</span><strong>{preview.rows_read.toLocaleString()}</strong></div>
          <div className="metric"><span>Accepted</span><strong>{preview.rows_accepted.toLocaleString()}</strong></div>
          <div className="metric"><span>Rejected</span><strong>{preview.rows_rejected.toLocaleString()}</strong></div>
        </div>
        {preview.issues.length > 0 && <div className="issues"><b>Issues ({preview.issues.length})</b>{preview.issues.slice(0, 20).map((issue, i) => <p key={i}>Row {issue.row ?? "—"} · {issue.column ?? "file"}: {issue.message ?? "Validation issue"}</p>)}</div>}
        <button onClick={importFile} disabled={busy || preview.rows_accepted === 0}>{busy ? "Importing…" : "Import accepted rows →"}</button>
      </section>}

      {result && <section className="card resultCard success"><span className="eyebrow">IMPORT COMPLETE</span><h2>Business data is now in Business Brain.</h2><p>{result.sales_created.toLocaleString()} sales records created · {result.rows_rejected.toLocaleString()} rejected · Run {result.run_id}</p><a className="buttonLink" href="/">View dashboard →</a></section>}
    </main>
  );
}
