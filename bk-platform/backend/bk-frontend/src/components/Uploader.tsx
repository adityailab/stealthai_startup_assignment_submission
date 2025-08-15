import { useState } from "react";
import { api } from "../api";

export default function Uploader() {
  const [file, setFile] = useState<File | null>(null);
  const [resp, setResp] = useState<any>(null);
  const [msg, setMsg] = useState<string | null>(null);

  const upload = async () => {
    if (!file) return;
    try {
      setMsg(null);
      const r = await api.upload(file);
      setResp(r);
    } catch (e: any) { setMsg(e.message); }
  };

  return (
    <>
      <h3>Upload Document</h3>
      <div className="row">
        <input type="file" onChange={e=>setFile(e.target.files?.[0] || null)} />
        <button onClick={upload} disabled={!file}>Upload</button>
      </div>
      {msg && <small>{msg}</small>}
      {resp && <pre>{JSON.stringify(resp, null, 2)}</pre>}
    </>
  );
}
