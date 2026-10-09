"use client";

import { FormEvent, useEffect, useMemo, useRef, useState } from "react";
import { api, clearAccessToken, Coverage, CoverageRecord, LocationOption, SupportedArea } from "@/lib/api";
function Icon({ name }: { name: "pin" | "radius" | "areas" | "search" | "lock" | "check" | "arrow" | "info" }) {
  const paths = {
    pin: <><path d="M12 21s-6-5.2-6-11a6 6 0 0 1 12 0c0 5.8-6 11-6 11Z" /><circle cx="12" cy="10" r="2" /></>,
    radius: <><circle cx="12" cy="12" r="9" strokeDasharray="2.5 3" /><circle cx="12" cy="12" r="3" fill="currentColor" stroke="none" /></>,
    areas: <><path d="m3 6 6-3 6 3 6-3v15l-6 3-6-3-6 3V6Zm6-3v15m6-12v15" /></>,
    search: <><circle cx="10.8" cy="10.8" r="6.8" /><path d="m16 16 5 5" /></>,
    lock: <><rect x="5" y="10" width="14" height="11" rx="2" /><path d="M8 10V7a4 4 0 0 1 8 0v3" /></>,
    check: <path d="m5 12 4 4L19 6" />,
    arrow: <><path d="M4 12h16m-6-6 6 6-6 6" /></>,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v5m0-8h.01" /></>,
  };
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>;
}

export default function CoverageForm() {
  const [record, setRecord] = useState<CoverageRecord | null>(null);
  const [vendorId, setVendorId] = useState<string | null>(null);
  const [supportedAreas, setSupportedAreas] = useState<SupportedArea[]>([]);
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
  const searchVersion = useRef(0);
  const searchTimer = useRef<number | null>(null);

  async function loadCoverage() {
    setLoading(true);
    setNotice(null);
    try {
      const user = await api.currentUser();
      if (!user.vendor_id) {
        setRecord(null);
        setNotice({ kind: "error", text: "No business profile is linked to this account. Contact support for help." });
        return;
      }
      setVendorId(user.vendor_id);
      const [saved, catalog] = await Promise.all([api.getCoverage(user.vendor_id), api.serviceAreaCatalog()]);
      setSupportedAreas(catalog.areas);
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
      setRecord(null);
      setNotice({ kind: "error", text: "We couldn’t load your saved coverage. Check your connection and try again." });
    } finally { setLoading(false); }
  }

  useEffect(() => { void loadCoverage(); }, []);
  async function searchLocations(searchTerm = query) {
    if (searchTimer.current !== null) window.clearTimeout(searchTimer.current);
    searchTimer.current = null;
    const normalizedQuery = searchTerm.trim();
    if (normalizedQuery.length < 2) { setResults([]); setSearchError(""); setSearching(false); return; }
    const version = ++searchVersion.current;
    setSearching(true); setSearchError(""); setResults([]);
    try {
      const matches = await api.searchLocations(normalizedQuery);
      if (version !== searchVersion.current) return;
      setResults(matches);
      if (!matches.length) setSearchError("No matching locations found. Try a nearby city or a fuller address.");
    } catch {
      if (version === searchVersion.current) setSearchError("Location search is temporarily unavailable. Please try again.");
    } finally { if (version === searchVersion.current) setSearching(false); }
  }

  useEffect(() => {
    if (!query.trim() || query.trim().length < 2 || location) return;
    searchTimer.current = window.setTimeout(() => {
      searchTimer.current = null;
      void searchLocations(query);
    }, 700);
    return () => {
      if (searchTimer.current !== null) window.clearTimeout(searchTimer.current);
      searchTimer.current = null;
    };
  }, [query, location]);

  const selectedNames = useMemo(() => new Set(areaIds), [areaIds]);
  function validate(): Coverage | null {
    const nextErrors: string[] = [];
    let value: Coverage | null = null;
    if (mode === "RADIUS") {
      const parsed = Number(radius);
      if (!location) nextErrors.push("Search for and select a service location.");
      if (!radius.trim() || !Number.isFinite(parsed) || parsed <= 0 || parsed > 500) nextErrors.push("Enter a radius greater than 0 and no more than 500 km.");
      if (location && radius.trim() && Number.isFinite(parsed) && parsed > 0 && parsed <= 500) value = { mode: "RADIUS", location, radius_km: parsed };
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
      if (!vendorId) return;
      const updated = await api.saveCoverage(vendorId, record.revision, coverage);
      setRecord(updated); setNotice({ kind: "success", text: "Your service coverage has been saved." });
    } catch (error) {
      const status = (error as Error & { status?: number }).status;
      if (status === 401) { clearAccessToken(); window.location.assign("/login"); return; }
      if (status === 409) setNotice({ kind: "conflict", text: "This coverage changed in another session. Reload the latest version before saving again." });
      else setNotice({ kind: "error", text: "We couldn’t save your changes. Please try again." });
    } finally { setSaving(false); }
  }

  function toggleArea(id: string) { setAreaIds((current) => current.includes(id) ? current.filter((item) => item !== id) : [...current, id]); }

  if (loading) return <section className="card loading-card" role="status"><span className="spinner" />Loading your saved coverage…</section>;
  if (!record) return <section className="loading-card load-error" role="alert"><span>{notice?.text}</span><button type="button" className="retry-button" onClick={() => void loadCoverage()}>Try again</button></section>;

  return <form className="coverage-card" onSubmit={submit} noValidate>
    <div className="card-title"><div><h2>Where do you serve?</h2><p>Select the coverage that best describes your service area.</p></div><span className="required">* Required</span></div>
    {notice && <div className={`notice ${notice.kind}`} role={notice.kind === "success" ? "status" : "alert"}><span className="notice-icon"><Icon name={notice.kind === "success" ? "check" : "info"} /></span><span>{notice.text}</span>{notice.kind === "conflict" && <button type="button" className="inline-button" onClick={() => void loadCoverage()}>Reload coverage</button>}</div>}
    <fieldset className="mode-grid"><legend className="sr-only">Coverage type</legend>
      <label className={`mode-card ${mode === "RADIUS" ? "selected" : ""}`}><input className="mode-input" type="radio" name="coverage-mode" checked={mode === "RADIUS"} onChange={() => { setMode("RADIUS"); setErrors([]); setNotice(null); }} />
        <span className="mode-icon radius-icon"><Icon name="radius" /></span><span className="mode-copy"><strong>Within a radius</strong><small>Serve customers near a central location</small></span><span className="radio-mark" />
      </label>
      <label className={`mode-card ${mode === "AREAS" ? "selected" : ""}`}><input className="mode-input" type="radio" name="coverage-mode" checked={mode === "AREAS"} onChange={() => { setMode("AREAS"); setErrors([]); setNotice(null); }} />
        <span className="mode-icon area-icon"><Icon name="areas" /></span><span className="mode-copy"><strong>Selected areas</strong><small>Choose from available service regions</small></span><span className="radio-mark" />
      </label>
    </fieldset>
    {mode === "RADIUS" ? <div className="form-section">
      <label className="field-label" htmlFor="location-search">Service location <span>*</span></label>
      {location ? <div className="selected-location"><span className="pin">⌖</span><span><strong>{location.label}</strong><small>{location.latitude.toFixed(4)}, {location.longitude.toFixed(4)}</small></span><button type="button" aria-label="Change location" onClick={() => { searchVersion.current++; setLocation(null); setQuery(""); setResults([]); }}>Change</button></div> : <><div className="search-wrap"><span className="search-icon"><Icon name="search" /></span><input id="location-search" value={query} onChange={(event) => { searchVersion.current++; setSearching(false); setQuery(event.target.value); setResults([]); setSearchError(""); }} onKeyDown={(event) => { if (event.key === "Enter") { event.preventDefault(); void searchLocations(); } }} placeholder="City or address" autoComplete="off" aria-describedby="location-help" /><button className="search-button" type="button" onClick={() => void searchLocations()} disabled={searching}>{searching ? "Searching…" : "Search"}</button></div>{searching && <p className="field-help" role="status">Searching locations…</p>}{results.length > 0 && <div className="search-results">{results.map((result) => <button type="button" key={result.id} onClick={() => { searchVersion.current++; setLocation(result); setQuery(""); setResults([]); setSearchError(""); }}><span className="pin">⌖</span><span><strong>{result.label}</strong><small>{result.latitude.toFixed(3)}, {result.longitude.toFixed(3)}</small></span></button>)}</div>}{searchError && <p className="field-error" role="status">{searchError}</p>}</>}
      <p className="field-help" id="location-help">Results appear as you type. Select a location to continue. Powered by OpenStreetMap.</p>
      <label className="field-label radius-label" htmlFor="radius">Service radius <span>*</span></label>
      <div className="radius-input"><input id="radius" type="number" min="0.01" max="500" step="any" value={radius} onChange={(event) => setRadius(event.target.value)} /><span>kilometers</span></div>
      <p className="field-help">Maximum radius is 500 km.</p>
    </div> : <div className="form-section areas-section">
      <div className="area-label-row"><label className="field-label">Service areas <span>*</span></label><span className="selection-count">{areaIds.length} selected</span></div>
      <p className="field-help area-intro">Select every region where you can reliably serve customers.</p>
      <div className="area-list">{supportedAreas.map((area) => <label className={`area-option ${selectedNames.has(area.id) ? "checked" : ""}`} key={area.id}><input type="checkbox" checked={selectedNames.has(area.id)} onChange={() => toggleArea(area.id)} /><span className="custom-check"><Icon name="check" /></span><span className="area-description"><strong>{area.label}</strong><small>{area.detail}</small></span><span className="area-symbol"><Icon name="pin" /></span></label>)}</div>
      <div className="dataset-note"><Icon name="info" /><span>These regions use the assignment demo area dataset.</span></div>
    </div>}
    {errors.length > 0 && <div className="validation-errors" role="alert">{errors.map((error) => <p key={error}>• {error}</p>)}</div>}
    <div className="card-actions"><p><span className="lock">♧</span> Coverage is visible only to your organization.<br /><span className="osm-attribution">Location data © <a href="https://www.openstreetmap.org/copyright" target="_blank" rel="noreferrer">OpenStreetMap contributors</a></span></p><button className="save-button" type="submit" disabled={saving || notice?.kind === "conflict"}>{saving && <span className="button-spinner" />}{saving ? "Saving changes…" : "Save coverage"}<span className="arrow">→</span></button></div>
  </form>;
}
