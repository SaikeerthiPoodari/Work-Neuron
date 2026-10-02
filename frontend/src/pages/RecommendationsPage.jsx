import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { get } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { useI18n } from "../i18n/I18nContext";

export default function RecommendationsPage() {
  const { user } = useAuth(); const { t } = useI18n(); const worker = user.role === "WORKER";
  const [items, setItems] = useState([]); const [tasks, setTasks] = useState([]); const [selected, setSelected] = useState(""); const [filters, setFilters] = useState({ job_type: "", verified: false }); const [error, setError] = useState(""); const [loading, setLoading] = useState(true);
  const loadJobs = (next = filters) => { setLoading(true); const params = new URLSearchParams(); if (next.job_type) params.set("job_type", next.job_type); if (next.verified) params.set("verified", "true"); get(`/recommendations/jobs/${params.toString() ? `?${params}` : ""}`).then(setItems).catch((err) => setError(err.message)).finally(() => setLoading(false)); };
  useEffect(() => {
    let current = true;
    setError("");
    if (worker) {
      loadJobs();
      return () => { current = false; };
    }
    setLoading(true);
    get("/tasks/")
      .then((data) => {
        if (!current) return;
        setTasks(data);
        setSelected(data[0] ? String(data[0].id) : "");
        if (!data.length) setLoading(false);
      })
      .catch((err) => { if (current) { setError(err.message); setLoading(false); } });
    return () => { current = false; };
  }, [worker]);
  useEffect(() => {
    if (worker || !selected) return undefined;
    let current = true;
    setLoading(true);
    setError("");
    get(`/recommendations/workers/?task=${selected}`)
      .then((data) => { if (current) setItems(data); })
      .catch((err) => { if (current) { setItems([]); setError(err.message); } })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [selected, worker]);
  const updateFilter = (key, value) => { const next = { ...filters, [key]: value }; setFilters(next); loadJobs(next); };
  return <div className="space-y-6"><header><p className="text-sm font-semibold text-brand">{worker ? t("smartMatches") : "Explainable AI discovery"}</p><h1 className="mt-1 text-3xl font-black">{worker ? t("matchesCard") : "Recommendations"}</h1><p className="mt-2 text-slate-500">{worker ? t("recommendationIntro") : "Scores combine skills, semantic similarity, location, education, experience, job type, salary, and availability."}</p></header>
    {worker ? <div className="card flex flex-wrap items-center gap-3"><select className="field mt-0 w-auto" value={filters.job_type} onChange={(event) => updateFilter("job_type", event.target.value)}><option value="">{t("allJobTypes")}</option>{[["PART_TIME", "partTime"], ["DAILY_WAGE", "dailyWage"], ["WEEKEND", "weekend"], ["EVENT", "event"], ["FESTIVAL", "festival"], ["INTERNSHIP", "internship"]].map(([value, key]) => <option value={value} key={value}>{t(key)}</option>)}</select><label className="flex items-center gap-2 text-sm font-semibold text-slate-600"><input type="checkbox" checked={filters.verified} onChange={(event) => updateFilter("verified", event.target.checked)} />{t("verifiedOnly")}</label></div> : <select className="field mt-0 max-w-md" value={selected} onChange={(event) => setSelected(event.target.value)}><option value="">Select one of your tasks</option>{tasks.map((task) => <option value={task.id} key={task.id}>{task.title}</option>)}</select>}
    <ErrorMessage message={error} />
    {loading ? <div className="card text-sm text-slate-500" role="status">{t("loadingTasks")}</div> : items.length ? <div className="grid gap-4 lg:grid-cols-2">{items.map((item) => <article className="card" key={item.task?.id || item.worker?.id}><div className="flex justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wide text-brand">{worker ? item.task.title : item.worker.email}</p><h2 className="mt-2 font-bold">{worker ? `₹${item.task.budget} · ${item.task.location || t("remote")}` : `${item.worker.first_name || "Worker"} ${item.worker.last_name || ""}`}</h2>{worker && <div className="mt-2 flex flex-wrap gap-2 text-xs font-bold text-slate-500"><span>{item.task.job_type?.replaceAll("_", " ")}</span>{item.task.category && <span>{item.task.category}</span>}{item.task.employer_verification?.status === "VERIFIED" && <span className="text-emerald-700">✓ {item.task.employer_verification.badge_text || t("verifiedEmployer")}</span>}</div>}</div><span className="text-2xl font-black text-emerald-700">{item.match.overall_score}</span></div><p className="mt-3 text-sm text-slate-600">{item.match.explanation}</p><div className="mt-4 flex flex-wrap gap-2 text-xs text-slate-500">{[["semantic", item.match.semantic_score], ["skills", item.match.skill_score], [t("experienceScore"), item.match.experience_score], [t("categoryScore"), item.match.category_score], [t("availabilityScore"), item.match.availability_score], ["Education", item.match.education_score], ["Salary", item.match.salary_score], ["Location", item.match.location_score]].map(([label, score]) => <span className="rounded-full bg-slate-50 px-2.5 py-1" key={label}>{label} {score ?? "—"}</span>)}</div></article>)}</div> : <EmptyState>{!worker && !selected ? "Select a task to see suitable workers." : t("noMatches")}</EmptyState>}
  </div>;
}
