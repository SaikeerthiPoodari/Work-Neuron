import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { get } from "../services/api";
import { useI18n } from "../i18n/I18nContext";

const periods = ["week", "month", "year"];

export default function SkillGraphPage() {
  const { user } = useAuth(); const { t } = useI18n();
  const [period, setPeriod] = useState("month");
  const [progress, setProgress] = useState(null);
  const [skills, setSkills] = useState([]);
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [selected, setSelected] = useState(null);
  const [error, setError] = useState("");
  const activities = [
    ...(progress?.completed_tasks || []).map((item) => ({ ...item, kind: "task", at: item.completed_at })),
    ...(progress?.earnings || []).map((item) => ({ ...item, kind: "earning", at: item.created_at })),
  ].sort((a, b) => new Date(b.at) - new Date(a.at));
  useEffect(() => { get("/skills/graph/").then(setGraph).catch((err) => setError(err.message)); }, []);
  useEffect(() => {
    if (user.role !== "WORKER") return;
    let active = true;
    Promise.all([get(`/skills/progress/?period=${period}`), get("/skills/mine/")]).then(([result, mine]) => { if (active) { setProgress(result); setSkills(mine); setSelected(null); } }).catch((err) => { if (active) setError(err.message); });
    return () => { active = false; };
  }, [period, user.role]);

  if (user.role === "WORKER") {
    const points = progress?.skill_history || [];
    return <div className="space-y-6">
      <header><p className="text-sm font-semibold text-brand">{t("workHistory")}</p><h1 className="mt-1 text-3xl font-black tracking-tight">{t("skillProgressTitle")}</h1><p className="mt-2 text-slate-500">{t("progressDataHelp")}</p></header>
      <ErrorMessage message={error} />
      <section className="card flex flex-wrap items-center justify-between gap-3"><div><h2 className="font-bold">{t("activityRange")}</h2><p className="mt-1 text-sm text-slate-500">{t("realActivityWindow")}</p></div><div className="flex gap-2">{periods.map((value) => <button key={value} className={`rounded-xl px-4 py-2 text-sm font-bold ${period === value ? "bg-brand text-white" : "bg-slate-100 text-slate-600"}`} onClick={() => setPeriod(value)}>{t(value === "week" ? "weekRange" : value === "month" ? "monthRange" : "yearRange")}</button>)}</div></section>
      <section className="grid gap-4 sm:grid-cols-3"><Metric label="Current skills" value={skills.length} /><Metric label="Completed tasks in range" value={progress?.summary.completed_tasks ?? "—"} /><Metric label="Verified earnings in range" value={progress ? `₹${Number(progress.summary.verified_earnings).toFixed(2)}` : "—"} /></section>
      <section className="card"><div className="flex flex-wrap items-start justify-between gap-3"><div><h2 className="text-lg font-black">{t("skillHistory")}</h2><p className="mt-1 text-sm text-slate-500">{t("historicalSnapshotHelp")}</p></div><span className="text-xs font-semibold text-slate-400">{t("historyRangeHelp")}</span></div>
        {points.length ? <div className="mt-5 space-y-4">{skills.map((skill) => { const rows = points.filter((point) => point.skill_id === skill.skill); if (!rows.length) return null; const width = 100; const coords = rows.map((row, index) => `${rows.length === 1 ? 50 : 8 + index * 84 / (rows.length - 1)},${92 - row.proficiency * 16}`).join(" "); return <div key={skill.skill} className="rounded-xl border border-slate-100 p-4"><div className="flex items-center justify-between"><p className="font-bold">{skill.skill_name}</p><span className="text-sm font-semibold text-brand">{t("currentLevel")} {skill.proficiency}/5</span></div><svg viewBox={`0 0 ${width} 100`} className="mt-2 h-24 w-full overflow-visible" role="img" aria-label={`${skill.skill_name} ${t("skillHistory")}`}><polyline points={coords} fill="none" stroke="#2563eb" strokeWidth="2.5" vectorEffect="non-scaling-stroke" />{rows.map((row, index) => { const x = rows.length === 1 ? 50 : 8 + index * 84 / (rows.length - 1); const y = 92 - row.proficiency * 16; return <circle key={`${row.recorded_at}-${index}`} cx={x} cy={y} r="4" fill="#2563eb" role="button" tabIndex="0" onClick={() => setSelected(row)} onKeyDown={(event) => event.key === "Enter" && setSelected(row)} />; })}</svg></div>; })}</div> : <EmptyState>{t("noSkillHistory")}</EmptyState>}
        {selected && <div className="mt-4 rounded-xl border border-blue-100 bg-blue-50 p-4 text-sm"><div className="flex items-center justify-between"><strong>{selected.skill_name ? `${selected.skill_name}: ${selected.proficiency}/5` : selected.task_title}</strong><button className="text-brand" onClick={() => setSelected(null)} aria-label="Close point details">×</button></div><p className="mt-1 text-slate-600">{selected.recorded_at ? `${selected.years_experience} years experience · ${new Date(selected.recorded_at).toLocaleString()}` : `${selected.kind === "earning" ? `Verified payment: ₹${selected.amount} ${selected.currency}` : "Completed assignment"} · ${new Date(selected.at).toLocaleString()}`}</p></div>}
      </section>
      <section className="card"><h2 className="text-lg font-black">{t("workActivityEarnings")}</h2>{activities.length ? <div className="mt-3 divide-y divide-slate-100">{activities.map((item, index) => <button className="flex w-full flex-wrap items-center justify-between gap-3 py-3 text-left" key={`${item.kind}-${item.assignment_id || item.transaction_id}-${index}`} onClick={() => setSelected(item)}><span><span className={`mr-2 rounded-full px-2 py-1 text-xs font-bold ${item.kind === "task" ? "bg-emerald-50 text-emerald-700" : "bg-blue-50 text-brand"}`}>{item.kind === "task" ? t("completedTaskLabel") : t("verifiedPaymentLabel")}</span><strong>{item.task_title}</strong>{item.skills?.length > 0 && <span className="ml-2 text-xs text-slate-500">{item.skills.join(", ")}</span>}</span><span className="text-sm text-slate-500">{item.kind === "earning" ? `₹${item.amount} ${item.currency}` : ""} · {new Date(item.at).toLocaleDateString()}</span></button>)}</div> : <EmptyState>{t("noActivityRange")}</EmptyState>}</section>
      <GlobalSkillGraph graph={graph} />
    </div>;
  }
  return <div className="space-y-6"><header><p className="text-sm font-semibold text-brand">Advanced discovery</p><h1 className="mt-1 text-3xl font-black tracking-tight">Skill Graph</h1><p className="mt-2 text-slate-500">Skills are connected when workers list them together. Edge weight shows the number of workers sharing that pair.</p></header><ErrorMessage message={error} /><GlobalSkillGraph graph={graph} /></div>;
}

function Metric({ label, value }) { return <div className="metric-card"><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 text-2xl font-black">{value}</p></div>; }

function GlobalSkillGraph({ graph }) {
  const { t } = useI18n();
  const popular = [...(graph.nodes || [])].sort((a, b) => b.worker_count - a.worker_count || a.name.localeCompare(b.name));
  return popular.length ? <div className="grid gap-4 lg:grid-cols-2"><div className="card"><h2 className="font-bold">{t("skillNodes")}</h2><div className="mt-4 space-y-3">{popular.map((skill) => <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3" key={skill.id}><div><p className="font-semibold">{skill.name}</p><p className="text-xs text-slate-500">{skill.category || "Uncategorized"}</p></div><span className="text-sm font-bold text-brand">{skill.worker_count} {t("workers")}</span></div>)}</div></div><div className="card"><h2 className="font-bold">{t("relatedSkills")}</h2>{graph.edges?.length ? <div className="mt-4 space-y-3">{graph.edges.map((edge) => { const source = graph.nodes.find((node) => node.id === edge.source); const target = graph.nodes.find((node) => node.id === edge.target); return <div className="flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3" key={`${edge.source}-${edge.target}`}><span className="text-sm font-semibold">{source?.name} ↔ {target?.name}</span><span className="text-sm font-bold text-emerald-700">{edge.weight} {t("shared")}</span></div>; })}</div> : <p className="mt-4 text-sm text-slate-500">{t("skillGraphHelp")}</p>}</div></div> : <EmptyState>{t("noSkillNodes")}</EmptyState>;
}
