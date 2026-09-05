"use client";
import {useEffect,useState} from "react";
import { apiFetch, getBusinessId } from "../lib/api";

export default function ImportHistory(){const[rows,setRows]=useState<any[]>([]);useEffect(()=>{apiFetch(`/imports/${getBusinessId()}/history`).then(r=>r.ok?r.json():[]).then(setRows).catch(()=>{})},[]);if(!rows.length)return null;return <section className="card"><div className="cardTitle"><span>◷</span><h3>Import history</h3></div>{rows.map(r=><div className="marginRow" key={r.run_id}><span>{r.file_name}</span><b>{r.rows_accepted.toLocaleString()} accepted</b><em>{r.status} · {new Date(r.started_at).toLocaleDateString()}</em></div>)}</section>}
