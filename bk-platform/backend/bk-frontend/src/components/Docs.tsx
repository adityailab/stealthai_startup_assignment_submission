import { useEffect, useState } from "react";
import { api } from "../api";

export default function Docs() {
  const [docs, setDocs] = useState<any[]>([]);
  const [q, setQ] = useState("");

  const load = async () => {
    const r = await api.listDocs(q || undefined);
    setDocs(r);
  };
  useEffect(()=>{ load(); }, []);

  return (
    <>
      <h3>Documents</h3>
      <div className="row">
        <input placeholder="filter by filename…" value={q} onChange={e=>setQ(e.target.value)} />
        <button onClick={load}>Refresh</button>
      </div>
      <div>
        {docs.map(d => (
          <div key={d.id} className="card">
            <div className="row" style={{justifyContent:"space-between"}}>
              <div><b>{d.filename}</b> <span className="badge">{d.mime_type}</span></div>
              <div><small>id #{d.id}</small></div>
            </div>
            <small>{(d.size/1024).toFixed(1)} KB • {d.has_text ? "has text" : "no text"}</small>
          </div>
        ))}
        {docs.length === 0 && <small>No documents yet.</small>}
      </div>
    </>
  );
}
