import { useState } from "react";
import { api } from "../api";

export default function Search() {
  const [q, setQ] = useState("latte");
  const [k, setK] = useState(5);
  const [minScore, setMinScore] = useState(0.25);
  const [keywordFilter, setKeywordFilter] = useState(true);
  const [perDoc, setPerDoc] = useState(2);
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    try {
      setErr(null);
      const r = await api.search({
        q, k, min_score: minScore, keyword_filter: keywordFilter, per_doc: perDoc
      });
      setRes(r);
    } catch (e:any) { setErr(e.message); }
  };

  return (
    <>
      <h3>Semantic Search</h3>
      <div className="row">
        <input style={{flex:2}} value={q} onChange={e=>setQ(e.target.value)} />
        <input type="number" value={k} onChange={e=>setK(+e.target.value)} />
        <input type="number" step="0.05" value={minScore} onChange={e=>setMinScore(+e.target.value)} />
        <label><input type="checkbox" checked={keywordFilter} onChange={e=>setKeywordFilter(e.target.checked)} /> keyword gate</label>
        <input type="number" value={perDoc} onChange={e=>setPerDoc(+e.target.value)} />
        <button onClick={run}>Search</button>
      </div>
      {err && <small>{err}</small>}
      {res && <pre>{JSON.stringify(res, null, 2)}</pre>}
    </>
  );
}
