import { useEffect, useState } from "react";
import { get } from "../services/api";
import { ErrorMessage, EmptyState } from "./StatusMessage";

export default function ProfessionalPortfolio({ workerId, compact = false }) {
  const [portfolio, setPortfolio] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { get(workerId ? `/profiles/portfolio/${workerId}/` : "/profiles/portfolio/").then(setPortfolio).catch((err) => setError(err.message)); }, [workerId]);
  if (error) return <ErrorMessage message={error} />;
  if (!portfolio) return <div className="card text-sm text-slate-500" role="status">Generating verified portfolio…</div>;
  const profile = portfolio.profile || {};
  return <section className="card space-y-5">
    <div className="flex flex-wrap items-start gap-4 border-b border-slate-100 pb-4"><div className="flex h-20 w-20 items-center justify-center overflow-hidden rounded-2xl bg-blue-50 text-2xl font-black text-brand">{profile.profile_photo ? <img src={profile.profile_photo} alt={portfolio.worker_name} className="h-full w-full object-cover" /> : portfolio.worker_name?.slice(0, 1)}</div><div><p className="text-xs font-black uppercase tracking-widest text-brand">Professional Portfolio</p><h2 className="mt-1 text-2xl font-black">{portfolio.worker_name}</h2><p className="text-sm text-slate-500">{profile.headline || "WorkNeuron professional"}{profile.location ? ` · ${profile.location}` : ""}</p></div></div>
    <div><h3 className="font-bold">Professional summary</h3><p className="mt-2 text-sm leading-6 text-slate-600">{portfolio.summary || "A verified summary will appear after completed WorkNeuron activity is available."}</p></div>
    {portfolio.skills?.length > 0 && <div><h3 className="font-bold">Skills and expertise</h3><div className="mt-2 flex flex-wrap gap-2">{portfolio.skills.map((skill) => <span className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-bold text-brand" key={skill.name}>{skill.name} · {skill.proficiency}/5</span>)}</div></div>}
    <div className="grid gap-3 sm:grid-cols-3"><Metric label="Completed assignments" value={portfolio.performance?.completed_assignments || 0} /><Metric label="Average rating" value={portfolio.performance?.average_rating ? `${portfolio.performance.average_rating}/5` : "Not rated"} /><Metric label="Verified reviews" value={portfolio.performance?.review_count || 0} /></div>
    {!compact && <div><h3 className="font-bold">Verified work experience</h3>{portfolio.experience?.length ? <div className="mt-3 space-y-3">{portfolio.experience.map((item) => <article className="rounded-xl bg-slate-50 p-3" key={item.assignment_id}><div className="flex flex-wrap justify-between gap-2"><div><p className="font-bold">{item.title}</p><p className="text-xs text-slate-500">{item.client_name} · {item.category || "Professional assignment"}</p></div><span className="text-xs font-semibold text-slate-500">{item.duration_days == null ? "Verified work" : `${item.duration_days} day${item.duration_days === 1 ? "" : "s"}`}</span></div><p className="mt-2 text-sm text-slate-600">{item.description}</p><div className="mt-2 flex flex-wrap gap-1.5">{item.skills.map((skill) => <span className="rounded bg-white px-2 py-1 text-[11px] text-slate-500" key={skill}>{skill}</span>)}</div></article>)}</div> : <EmptyState>No completed assignments are available yet.</EmptyState>}</div>}
    <p className="text-xs text-slate-400">Generated from verified WorkNeuron records · refreshed {portfolio.generated_at ? new Date(portfolio.generated_at).toLocaleString() : "when activity changes"}.</p>
  </section>;
}
function Metric({ label, value }) { return <div className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-xl font-black text-ink">{value}</p></div>; }
