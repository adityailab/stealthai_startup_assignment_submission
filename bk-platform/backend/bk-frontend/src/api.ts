const API_BASE = import.meta.env.VITE_API_BASE || "http://127.0.0.1:8001";

export function setToken(token: string | null) {
  if (token) localStorage.setItem("jwt", token);
  else localStorage.removeItem("jwt");
}
export function getToken() {
  return localStorage.getItem("jwt");
}

async function req(path: string, init: RequestInit = {}) {
  const headers: Record<string, string> = {
    ...(init.headers as Record<string, string> || {}),
  };
  const token = getToken();
  if (token) headers["Authorization"] = `Bearer ${token}`;
  const r = await fetch(`${API_BASE}${path}`, { ...init, headers });
  if (!r.ok) throw new Error(`${r.status} ${r.statusText}: ${await r.text()}`);
  const ct = r.headers.get("content-type") || "";
  return ct.includes("application/json") ? r.json() : r.text();
}

export const api = {
  // auth
  register: (email: string, password: string, name?: string) =>
    req("/api/auth/register", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password, name }),
    }),
  login: async (email: string, password: string) => {
    const data = await req("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });
    setToken(data.access_token);
    return data;
  },
  profile: () => req("/api/auth/profile"),

  // documents
  upload: (file: File) => {
    const fd = new FormData();
    fd.append("file", file);
    return req("/api/documents/upload", { method: "POST", body: fd });
  },
  listDocs: (q?: string) =>
    req(`/api/documents${q ? `?q=${encodeURIComponent(q)}` : ""}`),
  doc: (id: number) => req(`/api/documents/${id}`),

  // search (vector + keyword hybrid per your BE)
  search: (args: {
    q: string; k?: number; min_score?: number; keyword_filter?: boolean; per_doc?: number;
  }) => {
    const p = new URLSearchParams();
    p.set("q", args.q);
    if (args.k) p.set("k", String(args.k));
    if (args.min_score !== undefined) p.set("min_score", String(args.min_score));
    if (args.keyword_filter !== undefined) p.set("keyword_filter", String(args.keyword_filter));
    if (args.per_doc) p.set("per_doc", String(args.per_doc));
    return req(`/api/search?${p.toString()}`);
  },

  // knowledge ask (RAG)
  ask: (body: {
    question: string;
    k?: number;
    max_context_tokens?: number;
    provider?: string;   // e.g. "ollama"
    model?: string;      // e.g. "phi3:3.8b"
    require_all_terms?: boolean;
    phrase?: string | null;
    min_score?: number;
    per_file?: number;
    max_answer_chars?: number;
  }) =>
    req("/api/knowledge/ask", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    }),
};
