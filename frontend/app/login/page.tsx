"use client";

import { FormEvent, useState } from "react";
import { api, saveAccessToken } from "@/lib/api";
import AuthShell from "@/components/AuthShell";

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

  return <AuthShell
    title="Welcome back"
    intro="Sign in to manage your business service coverage."
    alert={error ? <div className="login-error" role="alert">{error}</div> : null}
    footer={<>
      <div className="demo-credentials"><strong>Assignment demo account</strong><span>vendor-demo@nova.test</span><span>NOVA-demo-2026!</span></div>
      <p className="login-footnote">Demo authentication for the assignment environment.</p>
      <p className="login-footnote">New to NOVA? <a href="/signup">Create an account</a></p>
    </>}
  >
    <form onSubmit={submit}>
      <label className="field-label" htmlFor="email">Email address</label>
      <input className="login-input" id="email" type="email" autoComplete="username" required value={email} onChange={(event) => setEmail(event.target.value)} />
      <label className="field-label password-label" htmlFor="password">Password</label>
      <input className="login-input" id="password" type="password" autoComplete="current-password" required value={password} onChange={(event) => setPassword(event.target.value)} />
      <button className="save-button login-submit" type="submit" disabled={busy}>{busy ? "Signing in…" : "Sign in"}<span className="arrow">→</span></button>
    </form>
  </AuthShell>;
}
