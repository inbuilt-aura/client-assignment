"use client";

import { FormEvent, useState } from "react";
import { api, saveAccessToken } from "@/lib/api";

export default function SignupPage() {
  const [businessName, setBusinessName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [busy, setBusy] = useState(false);

  async function submit(event: FormEvent) {
    event.preventDefault(); setError(""); setBusy(true);
    try {
      const result = await api.signup(businessName, email, password);
      saveAccessToken(result.access_token);
      window.location.assign("/");
    } catch (cause) {
      const error = cause as Error & { status?: number };
      const message = error.message;
      setError(error.status === 409 || message === "email_already_registered"
        ? "An account with this email already exists. Sign in instead."
        : error.status === 404
          ? "Signup isn’t available on the connected API yet. Rebuild and restart the backend, then try again."
          : message === "Request failed"
            ? "We couldn’t reach the signup service. Check that the backend is running and try again."
            : "We couldn’t create your account. Check your details and try again.");
      setBusy(false);
    }
  }

  return <main className="login-shell">
    <header className="topbar"><a className="brand" href="/">NOVA<span>VENDOR PORTAL</span></a></header>
    <section className="login-card">
      <div className="login-mark">N</div>
      <p className="eyebrow">VENDOR PORTAL</p>
      <h1>Create your account</h1>
      <p className="login-intro">Set up your business profile to manage service coverage.</p>
      {error && <div className="login-error" role="alert">{error}{error.startsWith("An account with this email") && <> <a href="/login">Sign in</a>.</>}</div>}
      <form onSubmit={submit}>
        <label className="field-label" htmlFor="business-name">Business name</label>
        <input className="login-input" id="business-name" autoComplete="organization" minLength={2} maxLength={160} required value={businessName} onChange={(event) => setBusinessName(event.target.value)} />
        <label className="field-label password-label" htmlFor="email">Email address</label>
        <input className="login-input" id="email" type="email" autoComplete="email" required value={email} onChange={(event) => setEmail(event.target.value)} />
        <label className="field-label password-label" htmlFor="password">Password</label>
        <input className="login-input" id="password" type="password" autoComplete="new-password" minLength={10} maxLength={200} required value={password} onChange={(event) => setPassword(event.target.value)} />
        <p className="field-help">Use at least 10 characters.</p>
        <button className="save-button login-submit" type="submit" disabled={busy}>{busy ? "Creating account…" : "Create account"}<span className="arrow">→</span></button>
      </form>
      <p className="login-footnote">Already have an account? <a href="/login">Sign in</a></p>
    </section>
  </main>;
}
