"use client";
import {useEffect,useState} from "react";
const API=process.env.NEXT_PUBLIC_API_URL||"http://localhost:8000/api";const ID=process.env.NEXT_PUBLIC_BUSINESS_ID||"11111111-1111-1111-1111-111111111111";
export default function DataFreshness(){const[x,setX]=useState<any>(null);useEffect(()=>{fetch(`${API}/imports/${ID}/history?limit=1`).then(r=>r.ok?r.json():[]).then(a=>a[0]&&setX(a[0])).catch(()=>{})},[]);if(!x)return null;return <div className="freshness">Data last imported <strong>{new Date(x.completed_at||x.started_at).toLocaleString()}</strong> · {x.file_name}</div>}
