import { ReactNode } from "react";

import Brand from "@/components/Brand";

export default function AuthShell({ title, intro, alert, children, footer }: { title: string; intro: string; alert?: ReactNode; children: ReactNode; footer: ReactNode }) {
  return <main className="login-shell">
    <header className="topbar"><Brand /></header>
    <section className="login-card">
      <div className="login-mark">N</div>
      <p className="eyebrow">VENDOR PORTAL</p>
      <h1>{title}</h1>
      <p className="login-intro">{intro}</p>
      {alert}
      {children}
      {footer}
    </section>
  </main>;
}
