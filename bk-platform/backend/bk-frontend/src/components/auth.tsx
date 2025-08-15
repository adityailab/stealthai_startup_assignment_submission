import { useState } from "react";
import { api } from "../api";

export default function Auth({ onAuthed }: { onAuthed: () => void }) {
  const [email, setEmail] = useState("demo@example.com");
  const [password, setPassword] = useState("demo1234");
  const [mode, setMode] = useState<"login"|"register">("login");
  const [name, setName] = useState("Demo User");
  const [msg, setMsg] = useState<string | null>(null);

  const submit = async () => {
    try {
      setMsg(null);
      if (mode === "register") await api.register(email, password, name);
      await api.login(email, password);
      onAuthed();
    } catch (e: any) { setMsg(e.message); }
  };

  return (
    <>
      <h3>Auth</h3>
      <div className="row">
        <select value={mode} onChange={e=>setMode(e.target.value as any)}>
          <option value="login">Login</option>
          <option value="register">Register</option>
        </select>
      </div>
      <div className="row">
        {mode === "register" && (
          <div style={{flex:1}}>
            <label>Name</label>
            <input value={name} onChange={e=>setName(e.target.value)} />
          </div>
        )}
        <div style={{flex:1}}>
          <label>Email</label>
          <input value={email} onChange={e=>setEmail(e.target.value)} />
        </div>
        <div style={{flex:1}}>
          <label>Password</label>
          <input type="password" value={password} onChange={e=>setPassword(e.target.value)} />
        </div>
        <button onClick={submit}>{mode === "login" ? "Login" : "Register & Login"}</button>
      </div>
      {msg && <small>{msg}</small>}
    </>
  );
}
