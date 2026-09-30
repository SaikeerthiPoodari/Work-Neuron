import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../services/api";
import JobMap, { hasCoordinates } from "../components/JobMap";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { useI18n } from "../i18n/I18nContext";

export default function NearbyJobsPage() {
  const { t } = useI18n();
  const [coords, setCoords] = useState(null);
  const [radius, setRadius] = useState(25);
  const [jobs, setJobs] = useState([]);
  const [view, setView] = useState("list");
  const [error, setError] = useState("");
  const [manual, setManual] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [loading, setLoading] = useState(false);

  const locate = () => {
    if (!navigator.geolocation) { setError(t("locationUnavailable")); return; }
    navigator.geolocation.getCurrentPosition(
      (position) => { setCoords([position.coords.latitude, position.coords.longitude]); setError(""); },
      () => setError(t("locationDenied")),
    );
  };
  useEffect(() => { locate(); }, []);
  useEffect(() => {
    if (!coords) return undefined;
    let active = true;
    setLoading(true); setError("");
    get(`/tasks/?latitude=${coords[0]}&longitude=${coords[1]}&radius_km=${radius}`)
      .then((response) => {
        // The task endpoint currently returns an array. Accept DRF's paginated
        // shape too so a deployment setting cannot silently discard the jobs.
        const data = Array.isArray(response) ? response : (response?.results || []);
        if (active) {
          setJobs(data);
          setSelectedId((current) => data.some((job) => job.id === current) ? current : null);
        }
      })
      .catch((err) => { if (active) setError(err.message); })
      .finally(() => { if (active) setLoading(false); });
    return () => { active = false; };
  }, [coords, radius]);

  const directions = (job) => `https://www.google.com/maps/dir/?api=1&destination=${Number(job.latitude)},${Number(job.longitude)}`;
  const selected = jobs.find((job) => job.id === selectedId);
  return <div className="space-y-6">
    <header><p className="text-sm font-semibold text-brand">{t("localOpportunities")}</p><h1 className="mt-1 text-3xl font-black tracking-tight">{t("nearbyTitle")}</h1><p className="mt-2 text-slate-500">{t("locationPrivacy")}</p></header>
    <div className="card flex flex-col gap-3 sm:flex-row sm:items-center">
      <button className="button-primary" onClick={locate}>{t("currentLocation")}</button>
      <label className="text-sm font-semibold text-slate-600">{t("searchRadius")}<select className="field mt-1 w-auto" value={radius} onChange={(event) => setRadius(Number(event.target.value))} aria-label={t("searchRadius")}>{[5, 10, 25, 50, 100].map((value) => <option value={value} key={value}>{value} km radius</option>)}</select></label>
      <div className="flex overflow-hidden rounded-xl border border-slate-200"><button className={`px-3 py-2 text-sm font-bold ${view === "list" ? "bg-blue-50 text-brand" : "text-slate-500"}`} onClick={() => setView("list")}>{t("listView")}</button><button className={`px-3 py-2 text-sm font-bold ${view === "map" ? "bg-blue-50 text-brand" : "text-slate-500"}`} onClick={() => setView("map")}>{t("mapView")}</button></div>
    </div>
    <div className="flex gap-2"><input className="field mt-0" placeholder={t("manualLocation")} aria-label={t("manualLocation")} value={manual} onChange={(event) => setManual(event.target.value)} /><Link className="button-secondary whitespace-nowrap" to={`/tasks?location=${encodeURIComponent(manual)}`}>{t("searchJobs")}</Link></div>
    <ErrorMessage message={error} />
    {loading && <div className="card text-sm text-slate-500" role="status">{t("loadingNearby")}</div>}
    {view === "map" ? <>
      <div className="grid min-w-0 gap-4 xl:grid-cols-[minmax(0,1.6fr)_minmax(18rem,.8fr)]">
        <div className="min-w-0"><JobMap jobs={jobs} center={coords} selectedJobId={selectedId} onSelect={setSelectedId} /></div>
        <section className="card max-h-[38rem] overflow-y-auto" aria-label={t("nearbyJobs")}>
          <h2 className="mb-3 text-lg font-black">{t("nearbyJobs")} ({jobs.length})</h2>
          <div className="space-y-2">{jobs.map((job) => <button type="button" key={job.id} onClick={() => setSelectedId(job.id)} className={`w-full rounded-xl border p-3 text-left transition ${job.id === selectedId ? "border-brand bg-blue-50 ring-2 ring-blue-100" : "border-slate-200 hover:border-blue-200"}`}><span className="block font-bold">{job.title}</span><span className="mt-1 block text-sm text-slate-600">{hasCoordinates(job) ? (job.location || job.location_city || t("localJob")) : t("locationUnavailable")}</span>{job.distance_km != null && <span className="mt-1 block text-xs text-slate-500">{job.distance_km} km {t("away")}</span>}</button>)}</div>
        </section>
      </div>
      {selected && <SelectedJob job={selected} t={t} directions={directions} />}
    </> : jobs.length ? <><div className="grid gap-4 lg:grid-cols-2">{jobs.map((job) => <article className={`card cursor-pointer transition hover:border-blue-200 ${job.id === selectedId ? "border-brand ring-2 ring-blue-100" : ""}`} key={job.id} onClick={() => setSelectedId(job.id)}><div className="flex justify-between gap-4"><div><Link to={`/tasks/${job.id}`} className="font-bold hover:text-brand" onClick={(event) => event.stopPropagation()}>{job.title}</Link><p className="mt-1 text-sm text-slate-500">{hasCoordinates(job) ? (job.location || job.location_city || t("localJob")) : t("locationUnavailable")}</p><p className="mt-1 text-xs text-slate-500">{t("clientLabel")}: {job.client_name || job.owner_email || t("clientLabel")}</p></div><span className="font-black text-emerald-700">₹{job.budget}</span></div><div className="mt-3 flex flex-wrap gap-2 text-xs font-bold text-slate-500"><span>{job.job_type?.replaceAll("_", " ")}</span>{job.category && <span>{job.category}</span>}{job.distance_km != null && <span>{job.distance_km} km {t("away")}</span>}{job.employer_verification?.status === "VERIFIED" && <span className="text-emerald-700">✓ {t("verifiedEmployer")}</span>}</div>{hasCoordinates(job) && <a className="mt-3 inline-block text-sm font-bold text-brand" target="_blank" rel="noreferrer" href={directions(job)} onClick={(event) => event.stopPropagation()}>{t("directions")} →</a>}</article>)}</div>{selected && <SelectedJob job={selected} t={t} directions={directions} />}</> : <EmptyState>{coords ? t("noNearbyJobs") : t("chooseLocation")}</EmptyState>}
  </div>;
}

function SelectedJob({ job, t, directions }) {
  return <article className="card border-brand" aria-live="polite"><div className="flex flex-wrap items-center justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wide text-brand">{t("selectedJob")}</p><h2 className="mt-1 text-lg font-black">{job.title}</h2><p className="text-sm text-slate-600">{t("clientLabel")}: {job.client_name || job.owner_email || t("clientLabel")}</p><p className="text-sm text-slate-600">{hasCoordinates(job) ? (job.location || job.location_city || t("localJob")) : t("locationUnavailable")}{job.distance_km != null ? ` · ${job.distance_km} km ${t("away")}` : ""}</p><p className="mt-1 text-sm text-slate-600">{job.job_type?.replaceAll("_", " ")}{job.category ? ` · ${job.category}` : ""} · ₹{job.budget}</p></div><div className="flex gap-2"><Link className="button-secondary" to={`/tasks/${job.id}`}>{t("viewDetails")}</Link>{hasCoordinates(job) && <a className="button-primary" target="_blank" rel="noreferrer" href={directions(job)}>{t("directions")}</a>}</div></div></article>;
}
