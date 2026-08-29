"use client";
import {useEffect,useState} from "react";
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api";const BUSINESS_ID=process.env.NEXT_PUBLIC_BUSINESS_ID||"11111111-1111-1111-1111-111111111111";
export default function ImportHistory(){const[rows,setRows]=useState<any[]>([]);useEffect(()=>{fetch(`${API}/imports/${BUSINESS_ID}/history`).then(r=>r.ok?r.json():[]).then(setRows).catch(()=>{})},[]);if(!rows.length)return null;return <section className="card"><div className="cardTitle"><span>◷</span><h3>Import history</h3></div>{rows.map(r=><div className="marginRow" key={r.run_id}><span>{r.file_name}</span><b>{r.rows_accepted.toLocaleString()} accepted</b><em>{r.status} · {new Date(r.started_at).toLocaleDateString()}</em></div>)}</section>}
