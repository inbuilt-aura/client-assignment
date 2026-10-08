"use client";

import { FormEvent, useEffect, useMemo, useState } from "react";
import { api, clearAccessToken, Coverage, CoverageRecord, LocationOption } from "@/lib/api";

const AREAS = [
  { id: "sf-bay", name: "San Francisco Bay Area", detail: "San Francisco, Oakland, San Jose" },
  { id: "la-metro", name: "Los Angeles Metro", detail: "Los Angeles, Long Beach, Anaheim" },
  { id: "nyc-metro", name: "New York City Metro", detail: "New York, Newark, Jersey City" },
];
const VENDOR_ID = process.env.NEXT_PUBLIC_VENDOR_ID ?? "vendor-demo";

export default function CoverageForm() {
  const [record, setRecord] = useState<CoverageRecord | null>(null);
  const [mode, setMode] = useState<"RADIUS" | "AREAS">("RADIUS");
  const [location, setLocation] = useState<LocationOption | null>(null);
  const [radius, setRadius] = useState("25");
  const [areaIds, setAreaIds] = useState<string[]>([]);
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<LocationOption[]>([]);
  const [searchError, setSearchError] = useState("");
  const [loading, setLoading] = useState(true);
  const [searching, setSearching] = useState(false);
  const [saving, setSaving] = useState(false);
  const [notice, setNotice] = useState<{ kind: "success" | "error" | "conflict"; text: string } | null>(null);
  const [errors, setErrors] = useState<string[]>([]);

  async function loadCoverage() {
    setLoading(true);
    setNotice(null);
    try {
      const saved = await api.getCoverage(VENDOR_ID);
      setRecord(saved);
      if (saved.coverage?.mode === "RADIUS") {
        setMode("RADIUS"); setLocation(saved.coverage.location); setRadius(String(saved.coverage.radius_km)); setAreaIds([]);
      } else if (saved.coverage?.mode === "AREAS") {
        setMode("AREAS"); setAreaIds(saved.coverage.area_ids); setLocation(null);
      }
    } catch (error) {
      if ((error as Error & { status?: number }).status === 401) {
        clearAccessToken();
        window.location.assign("/login");
        return;
      }
      setNotice({ kind: "error", text: "We couldn’t load your saved coverage. Check your connection and try again." });
    } finally { setLoading(false); }
  }

  useEffect(() => { void loadCoverage(); }, []);
  async function searchLocations(event?: FormEvent) {
    event?.preventDefault();
    if (query.trim().length < 2) { setSearchError("Enter at least 2 characters to search."); return; }
    setSearching(true); setSearchError(""); setResults([]);
    try {
      const matches = await api.searchLocations(query.trim());
      setResults(matches);
      if (!matches.length) setSearchError("No matching locations found. Try a nearby city or a fuller address.");
    } catch {
      setSearchError("Location search is temporarily unavailable. Please try again.");
    } finally { setSearching(false); }
  }

  const selectedNames = useMemo(() => new Set(areaIds), [areaIds]);
  function validate(): Coverage | null {
    const nextErrors: string[] = [];
    let value: Coverage | null = null;
    if (mode === "RADIUS") {
      const parsed = Number(radius);
      if (!location) nextErrors.push("Search for and select a service location.");
      if (!Number.isFinite(parsed) || parsed <= 0 || parsed > 500) nextErrors.push("Enter a radius greater than 0 and no more than 500 km.");
      if (location && Number.isFinite(parsed) && parsed > 0 && parsed <= 500) value = { mode: "RADIUS", location, radius_km: parsed };
    } else {
      if (!areaIds.length) nextErrors.push("Select at least one service area.");
      else value = { mode: "AREAS", area_ids: areaIds };
    }
    setErrors(nextErrors);
    return nextErrors.length ? null : value;
  }

  async function submit(event: FormEvent) {
    event.preventDefault(); setNotice(null);
    const coverage = validate();
    if (!coverage || !record) return;
    setSaving(true);
    try {
      const updated = await api.saveCoverage(VENDOR_ID, record.revision, coverage);
      setRecord(updated); setNotice({ kind: "success", text: "Your service coverage has been saved." });
    } catch (error) {
      const status = (error as Error & { status?: number }).status;
      if (status === 409) setNotice({ kind: "conflict", text: "This coverage changed in another session. Reload the latest version before saving again." });
      else setNotice({ kind: "error", text: "We couldn’t save your changes. Please try again." });
    } finally { setSaving(false); }
  }

  function toggleArea(id: string) { setAreaIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]); }

  if (loading) return <section className="card loading-card" aria-live="polite"><span className="spinner" />Loading your saved coverage…</section>;

  return <form className="coverage-card" onSubmit={submit} noValidate>
    <div className="card-title"><div><h2>Where do you serve?</h2><p>Select the coverage that best describes your service area.</p></div><span className="required">* Required</span></div>
    {notice && <div className={`notice ${notice.kind}`} role="status"><span className="notice-icon">{notice.kind === "success" ? "✓" : notice.kind === "conflict" ? "↻" : "!"}</span><span>{notice.text}</span>{notice.kind === "conflict" && <button type="button" className="inline-button" onClick={() => void loadCoverage()}>Reload coverage</button>}</div>}
    <div className="mode-grid" role="radiogroup" aria-label="Coverage type">
      <button type="button" className={`mode-card ${mode === "RADIUS" ? "selected" : ""}`} role="radio" aria-checked={mode === "RADIUS"} onClick={() => { setMode("RADIUS"); setErrors([]); }}>
        <span className="mode-icon radius-icon"><span /></span><span className="mode-copy"><strong>Within a radius</strong><small>Serve customers near a central location</small></span><span className="radio-mark" />
      </button>
      <button type="button" className={`mode-card ${mode === "AREAS" ? "selected" : ""}`} role="radio" aria-checked={mode === "AREAS"} onClick={() => { setMode("AREAS"); setErrors([]); }}>
        <span className="mode-icon area-icon"><span>⌖</span></span><span className="mode-copy"><strong>Selected areas</strong><small>Choose from available service regions</small></span><span className="radio-mark" />
      </button>
    </div>
    {mode === "RADIUS" ? <div className="form-section">
      <label className="field-label" htmlFor="location-search">Service location <span>*</span></label>
      {location ? <div className="selected-location"><span className="pin">⌖</span><span><strong>{location.label}</strong><small>{location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}</small></span><button type="button" aria-label="Change location" onClick={() => { setLocation(null); setQuery(""); setResults([]); }}>Change</button></div> : <><div className="search-wrap"><span className="search-icon">⌕</span><input id="location-search" value={query} onChange={(event) => setQuery(event.target.value)} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); void searchLocations(); } }} placeholder="Search city or address" autoComplete="off" aria-describedby="location-help" /><button className="search-button" type="button" onClick={() => void searchLocations()} disabled={searching}>{searching ? "Searching…" : "Search"}</button></div>{results.length > 0 && <div className="search-results">{results.map((result) => <button type="button" key={result.id} onClick={() => { setLocation(result); setQuery(""); setResults([]); }}><span className="pin">⌖</span><span><strong>{result.label}</strong><small>{result.latitude.toFixed(3)}, {result.longitude.toFixed(3)}</small></span></button>)}</div>}{searchError && <p className="field-error" role="status">{searchError}</p>}</>}
      <p className="field-help" id="location-help">Search for a city or address, then select a result. Results are powered by OpenStreetMap.</p>
      <label className="field-label radius-label" htmlFor="radius">Service radius <span>*</span></label>
      <div className="radius-input"><input id="radius" type="number" min="1" max="500" step="1" value={radius} onChange={(event) => setRadius(event.target.value)} /><span>kilometers</span></div>
      <p className="field-help">Maximum radius is 500 km.</p>
    </div> : <div className="form-section areas-section">
      <div className="area-label-row"><label className="field-label">Service areas <span>*</span></label><span className="selection-count">{areaIds.length} selected</span></div>
      <p className="field-help area-intro">Select every region where you can reliably serve customers.</p>
      <div className="area-list">{AREAS.map((area) => <label className={`area-option ${selectedNames.has(area.id) ? "checked" : ""}`} key={area.id}><input type="checkbox" checked={selectedNames.has(area.id)} onChange={() => toggleArea(area.id)} /><span className="custom-check">✓</span><span className="area-description"><strong>{area.name}</strong><small>{area.detail}</small></span><span className="area-symbol">⌖</span></label>)}</div>
      <div className="dataset-note"><span>ⓘ</span><span>Service regions are based on NOVA’s supported geographic areas.</span></div>
    </div>}
    {errors.length > 0 && <div className="validation-errors" role="alert">{errors.map((error) => <p key={error}>• {error}</p>)}</div>}
    <div className="card-actions"><p><span className="lock">♧</span> Your coverage is only shared with relevant opportunities.<br /><span className="osm-attribution">Location data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a></span></p><button className="save-button" type="submit" disabled={saving}>{saving && <span className="button-spinner" />}{saving ? "Saving changes…" : "Save coverage"}<span className="arrow">→</span></button></div>
  </form>;
}
