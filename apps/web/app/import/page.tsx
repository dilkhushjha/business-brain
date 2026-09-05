"use client";

import { ChangeEvent, useEffect, useState } from "react";
import { API_BASE_URL, getBusinessId, getToken, setToken } from "../../lib/api";

type Preview = { source:string; checksum:string; rows_read:number; rows_accepted:number; rows_rejected:number; issues:Array<{row?:number;column?:string;message?:string}>; mapping?:Array<{canonical:string;source:string;confidence:number}> };
type ImportResult = Preview & { run_id:string; status:string; sales_created:number };

export default function ImportPage(){
 const [businessId,setBusinessId]=useState(()=>getBusinessId()),[apiToken,setApiToken]=useState(""),[file,setFile]=useState<File|null>(null),[preview,setPreview]=useState<Preview|null>(null),[result,setResult]=useState<ImportResult|null>(null),[error,setError]=useState(""),[busy,setBusy]=useState(false);
 useEffect(()=>{setApiToken(getToken(businessId)||"")},[businessId]);
 function chooseFile(e:ChangeEvent<HTMLInputElement>){setFile(e.target.files?.[0]||null);setPreview(null);setResult(null);setError("")}
 async function request(path:string){
   if(!file)throw Error("Choose a CSV or Excel file first.");
   if(!businessId.trim())throw Error("Business ID is required.");
   if(!apiToken.trim())throw Error("An API token for this business is required -- connect on the dashboard first, or paste one below.");
   setToken(businessId.trim(),apiToken.trim());
   const form=new FormData();form.append("file",file);
   const r=await fetch(`${API_BASE_URL}/ingestion/${path}/${businessId}`,{method:"POST",headers:{Authorization:`Bearer ${apiToken.trim()}`},body:form});
   const d=await r.json().catch(()=>({}));
   if(!r.ok)throw Error(r.status===401||r.status===403?"That token was rejected for this business. Check it and try again.":(d.detail||`Import service returned ${r.status}`));
   return d
 }
 async function previewFile(){setBusy(true);setError("");setResult(null);try{setPreview(await request("preview"))}catch(e){setError(e instanceof Error?e.message:"Unable to preview file")}finally{setBusy(false)}}
 async function importFile(){setBusy(true);setError("");try{setResult(await request("record-run"))}catch(e){setError(e instanceof Error?e.message:"Unable to import file")}finally{setBusy(false)}}
 return <main className="shell"><header className="header"><div><a href="/" className="eyebrow">← BUSINESS BRAIN</a><h1>Import business data</h1></div><span className="status">V1 · Safe onboarding</span></header><section className="hero"><p className="muted">Upload a Tally CSV or Excel export, inspect what Business Brain understands, then explicitly commit it.</p></section><section className="card"><div className="field"><label>Business ID</label><input value={businessId} onChange={e=>setBusinessId(e.target.value)}/></div><div className="field"><label>API token for this business</label><input value={apiToken} onChange={e=>setApiToken(e.target.value)} placeholder="Paste your API token"/></div><div className="field"><label>Source file</label><input type="file" accept=".csv,.xlsx,.xls" onChange={chooseFile}/></div>{file&&<p className="muted fileName">Selected: <strong>{file.name}</strong> · {(file.size/1024).toFixed(1)} KB</p>}<div className="actions"><button onClick={previewFile} disabled={busy||!file}>{busy?"Checking…":"Preview & Validate"}</button></div></section>{error&&<div className="errorBox">{error}</div>}{preview&&!result&&<section className="card resultCard"><span className="eyebrow">VALIDATION PREVIEW</span><h2>{preview.source}</h2><div className="metrics"><div className="metric"><span>Rows read</span><strong>{preview.rows_read.toLocaleString()}</strong></div><div className="metric"><span>Accepted</span><strong>{preview.rows_accepted.toLocaleString()}</strong></div><div className="metric"><span>Rejected</span><strong>{preview.rows_rejected.toLocaleString()}</strong></div></div>{preview.mapping&&preview.mapping.length>0&&<div className="issues"><b>Detected columns</b>{preview.mapping.map((m,i)=><p key={i}><strong>{m.canonical}</strong> ← {m.source} · {Math.round(m.confidence*100)}%</p>)}</div>}{preview.issues.length>0&&<div className="issues"><b>Validation issues</b>{preview.issues.slice(0,20).map((x,i)=><p key={i}>Row {x.row??"—"} · {x.column??"file"}: {x.message??"Validation issue"}</p>)}</div>}<button onClick={importFile} disabled={busy||preview.rows_accepted===0}>{busy?"Importing…":"Import accepted rows →"}</button></section>}{result&&<section className="card resultCard success"><span className="eyebrow">IMPORT COMPLETE</span><h2>Data committed successfully.</h2><p>{result.sales_created.toLocaleString()} sales records created · {result.rows_rejected.toLocaleString()} rejected.</p><p className="muted">Checksum: {result.checksum}</p><a className="buttonLink" href="/">View dashboard →</a></section>}</main>
}
