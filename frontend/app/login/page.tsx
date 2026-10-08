"use client";

import { FormEvent, useState } from "react";
import { api, saveAccessToken } from "@/lib/api";

export default function LoginPage() {
  const [email, setEmail] = useState("vendor-demo@nova.test");
  const [password, setPassword] = useState("NOVA-demo-2026!");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setBusy(true);
    try {
      const result = await api.login(email, password);
      saveAccessToken(result.access_token);
      window.location.assign("/");
    } catch {
      setError("We couldn’t sign you in. Check your email and password.");
      setBusy(false);
    }
  }

  return <main className="login-shell">
    <header className="topbar"><a className="brand" href="/">NOVA<span>VENDOR PORTAL</span></a></header>
    <section className="login-card">
      <div className="login-mark">N</div>
      <p className="eyebrow">VENDOR PORTAL</p>
      <h1>Welcome back</h1>
      <p className="login-intro">Sign in to manage your business service coverage.</p>
      {error && <div className="login-error" role="alert">{error}</div>}
      <form onSubmit={submit}>
        <label className="field-label" htmlFor="email">Email address</label>
        <input className="login-input" id="email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} />
        <label className="field-label password-label" htmlFor="password">Password</label>
        <input className="login-input" id="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
        <button className="save-button login-submit" type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}<span className="arrow">→</span></button>
      </form>
      <div className="demo-credentials"><strong>Assignment demo account</strong><span>vendor-demo@nova.test</span><span>NOVA-demo-2026!</span></div>
      <p className="login-footnote">Demo authentication for the assignment environment.</p>
    </section>
  </main>;
}
