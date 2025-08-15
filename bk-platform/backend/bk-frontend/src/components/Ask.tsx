import { useState } from "react";
import { api } from "../api";

export default function Ask() {
  const [question, setQuestion] = useState("What is the name of server in \"BEAN & BREW COFFEE SHOP\"?");
  const [k, setK] = useState(6);
  const [provider, setProvider] = useState("ollama"); // avoids HF by default
  const [model, setModel] = useState("phi3:3.8b");   // or llama3:latest/tinyllama
  const [res, setRes] = useState<any>(null);
  const [err, setErr] = useState<string | null>(null);

  const run = async () => {
    try {
      setErr(null);
      const r = await api.ask({
        question,
        k,
        max_context_tokens: 800,
        provider,
        model,
        require_all_terms: false,
        min_score: 0.2,
        per_file: 1,
        max_answer_chars: 140
      });
      setRes(r);
    } catch (e:any) { setErr(e.message); }
  };

  return (
    <>
      <h3>Ask (RAG)</h3>
      <div className="row">
        <input style={{flex:2}} value={question} onChange={e=>setQuestion(e.target.value)} />
        <input type="number" value={k} onChange={e=>setK(+e.target.value)} />
        <select value={provider} onChange={e=>setProvider(e.target.value)}>
          <option value="ollama">ollama</option>
          <option value="openai">openai</option>
          <option value="hf">huggingface</option>
        </select>
        <input placeholder="model" value={model} onChange={e=>setModel(e.target.value)} />
        <button onClick={run}>Ask</button>
      </div>
      {err && <small>{err}</small>}
      {res && (
        <>
          <div className="card">
            <b>Answer</b>
            <div style={{marginTop:8}}>{res.answer}</div>
          </div>
          <div className="card">
            <b>Citations</b>
            <pre>{JSON.stringify(res.citations, null, 2)}</pre>
          </div>
        </>
      )}
    </>
  );
}
