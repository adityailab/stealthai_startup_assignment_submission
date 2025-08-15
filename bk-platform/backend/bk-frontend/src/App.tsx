import { useEffect, useState } from "react";
import { api, getToken, setToken } from "./api";
import Auth from "./components/Auth";
import Uploader from "./components/Uploader";
import Docs from "./components/Docs";
import Ask from "./components/Ask";
import Search from "./components/Search";

export default function App() {
  const [me, setMe] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  const loadMe = async () => {
    try {
      setError(null);
      if (!getToken()) { setMe(null); return; }
      const p = await api.profile();
      setMe(p);
    } catch (e: any) {
      setError(e.message);
      setToken(null);
      setMe(null);
    }
  };

  useEffect(() => { loadMe(); }, []);

  return (
    <div className="container">
      <div className="row" style={{justifyContent:"space-between"}}>
        <h2>BK Platform — Test Frontend</h2>
        <div>
          {me ? (
            <div className="row">
              <span className="badge">{me.email}</span>
              <button className="secondary" onClick={() => { setToken(null); setMe(null); }}>Logout</button>
            </div>
          ) : <span className="badge">Not signed in</span>}
        </div>
      </div>

      {error && <div className="card" style={{borderColor:"#ef4444"}}><b>Error:</b> {error}</div>}

      {!me ? (
        <div className="card"><Auth onAuthed={loadMe} /></div>
      ) : (
        <>
          <div className="card"><Uploader /></div>
          <div className="card"><Docs /></div>
          <div className="card"><Search /></div>
          <div className="card"><Ask /></div>
        </>
      )}
    </div>
  );
}
