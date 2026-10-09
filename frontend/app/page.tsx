import CoverageForm from "@/components/CoverageForm";
import SessionControls from "@/components/SessionControls";
import Brand from "@/components/Brand";

export default function Home() {
  return (
    <main className="shell">
      <header className="topbar"><Brand /><SessionControls /></header>
      <div className="content">
        <div className="breadcrumbs"><span>Settings</span><span>/</span><strong>Service coverage</strong></div>
        <div className="heading-row"><div><p className="eyebrow">BUSINESS PROFILE</p><h1>Service coverage</h1><p className="intro">Choose where you’re available to serve customers. Your coverage helps us match you with the right opportunities.</p></div><span className="step-pill"><span className="step-dot">✓</span> Profile setup</span></div>
        <CoverageForm />
        <footer className="page-footer"><span>Need a hand? <a href="mailto:support@nova.example">Contact support</a></span><span>Changes apply to new opportunities</span></footer>
      </div>
    </main>
  );
}
