import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../services/api";
import { ErrorMessage, EmptyState } from "./StatusMessage";

export default function ProfessionalPortfolio({ workerId, initialPortfolio = null }) {
  const [portfolio, setPortfolio] = useState(initialPortfolio);
  const [error, setError] = useState("");
  useEffect(() => {
    if (initialPortfolio) { setPortfolio(initialPortfolio); return; }
    get(workerId ? `/profiles/portfolio/${workerId}/` : "/profiles/portfolio/").then(setPortfolio).catch((err) => setError(err.message));
  }, [workerId, initialPortfolio]);
  if (error) return <ErrorMessage message={error} />;
  if (!portfolio) return <div className="card text-sm text-slate-500" role="status">Preparing verified professional summary…</div>;
  const profile = portfolio.profile || {};
  const isOwnPortfolio = !workerId && window.location.pathname.includes("/profile");
  const routePrefix = window.location.pathname.startsWith("/worker") ? "/worker" : window.location.pathname.startsWith("/client") ? "/client" : "";
  const portfolioUrl = `${window.location.origin}${routePrefix}/portfolio/${portfolio.worker}`;
  const copyLink = async () => { try { await navigator.clipboard.writeText(portfolioUrl); } catch { window.prompt("Copy portfolio link", portfolioUrl); } };
  const sharePortfolio = async () => { if (navigator.share) await navigator.share({ title: `${portfolio.worker_name} · WorkNeuron Portfolio`, url: portfolioUrl }); else await copyLink(); };
  return <section className="card space-y-6 border-blue-100 bg-white shadow-sm" aria-labelledby="professional-portfolio-title">
    <header className="flex items-start gap-4 border-b border-slate-100 pb-5">
      <div className="flex h-16 w-16 shrink-0 items-center justify-center overflow-hidden rounded-2xl bg-blue-50 text-2xl font-black text-brand">{profile.profile_photo ? <img src={profile.profile_photo} alt={portfolio.worker_name} className="h-full w-full object-cover" /> : portfolio.worker_name?.slice(0, 1)}</div>
      <div className="min-w-0 flex-1">
        <p className="text-xs font-black uppercase tracking-widest text-brand">{isOwnPortfolio ? "My Professional Portfolio" : "Professional Portfolio"}</p>
        <h2 id="professional-portfolio-title" className="mt-1 text-2xl font-black text-slate-900">{portfolio.worker_name}</h2>
        {portfolio.worker != null && <p className="text-xs font-semibold text-slate-500">WorkNeuron member ID #{portfolio.worker}</p>}
        <p className="mt-1 text-sm text-slate-500">{profile.headline || "WorkNeuron professional"}{profile.location ? ` · ${profile.location}` : ""}</p>
      </div>
      <div className="flex shrink-0 flex-wrap justify-end gap-2 print:hidden"><Link className="button-secondary text-xs" to={`${routePrefix}/portfolio/${portfolio.worker}`}>View portfolio</Link><button type="button" className="button-secondary text-xs" onClick={copyLink}>Copy link</button><button type="button" className="button-secondary text-xs" onClick={sharePortfolio}>Share</button><button type="button" className="button-primary text-xs" onClick={() => window.print()}>Download / Print PDF</button></div>
    </header>
    <section aria-labelledby="professional-summary-title">
      <h3 id="professional-summary-title" className="font-bold text-slate-900">Professional Summary</h3>
      <p className="mt-2 rounded-2xl bg-slate-50 p-4 text-sm leading-7 text-slate-700">{portfolio.summary || "A verified professional summary will appear as WorkNeuron activity is completed."}</p>
    </section>
    <section aria-labelledby="portfolio-performance-title">
      <h3 id="portfolio-performance-title" className="font-bold text-slate-900">Performance Metrics</h3>
      <div className="mt-3 grid gap-3 sm:grid-cols-3"><Metric label="Verified assignments" value={portfolio.performance?.completed_assignments || 0} /><Metric label="Average client rating" value={portfolio.performance?.average_rating ? `${portfolio.performance.average_rating}/5` : "Not rated"} /><Metric label="Verified reviews" value={portfolio.performance?.review_count || 0} /></div>
    </section>
    <section aria-labelledby="portfolio-skills-title">
      <h3 id="portfolio-skills-title" className="font-bold text-slate-900">Skills &amp; Expertise</h3>
      {portfolio.skills?.length ? <div className="mt-3 flex flex-wrap gap-2">{portfolio.skills.map((skill) => <span className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-bold text-brand" key={skill.name}>{skill.name} · {skill.proficiency}/5</span>)}</div> : <p className="mt-2 text-sm text-slate-500">No skills have been added yet.</p>}
    </section>
    <section aria-labelledby="portfolio-experience-title">
      <h3 id="portfolio-experience-title" className="font-bold text-slate-900">Verified Work Experience</h3>
      {portfolio.experience?.length ? <div className="mt-3 space-y-3 border-l-2 border-blue-100 pl-4">{portfolio.experience.map((item) => <article className="relative rounded-xl bg-slate-50 p-4 before:absolute before:-left-[1.65rem] before:top-5 before:h-3 before:w-3 before:rounded-full before:bg-brand" key={item.assignment_id}><div className="flex flex-wrap justify-between gap-2"><div><p className="font-bold text-slate-900">{item.title}</p><p className="text-xs text-slate-500">{item.client_name} · {item.category || "Professional assignment"}</p></div><span className="text-xs font-semibold text-slate-500">{item.completed_at ? `Completed ${new Date(item.completed_at).toLocaleDateString()}` : item.duration_days == null ? "Verified" : `${item.duration_days} day${item.duration_days === 1 ? "" : "s"}`}</span></div><p className="mt-2 text-sm text-slate-600">{item.description}</p>{item.skills?.length > 0 && <div className="mt-3 flex flex-wrap gap-2">{item.skills.map((skill) => <span className="rounded-full bg-white px-2.5 py-1 text-xs text-slate-600" key={skill}>{skill}</span>)}</div>}</article>)}</div> : <EmptyState>No completed assignments are available yet.</EmptyState>}
    </section>
    <section aria-labelledby="portfolio-reviews-title">
      <h3 id="portfolio-reviews-title" className="font-bold text-slate-900">Client Reviews</h3>
      {portfolio.reviews?.length ? <div className="mt-3 grid gap-3 md:grid-cols-2">{portfolio.reviews.slice(0, 4).map((item, index) => <article className="rounded-xl border border-slate-100 p-3" key={`${item.created_at}-${index}`}><p className="font-bold text-amber-500">{"★".repeat(item.rating)}<span className="ml-2 text-xs text-slate-400">{item.rating}/5</span></p>{item.review && <p className="mt-2 text-sm leading-6 text-slate-600">“{item.review}”</p>}<p className="mt-2 text-xs text-slate-400">{item.client_name}</p></article>)}</div> : <p className="mt-2 text-sm text-slate-500">No verified client reviews yet.</p>}
    </section>
    {portfolio.achievements?.length > 0 && <section aria-labelledby="portfolio-achievements-title"><h3 id="portfolio-achievements-title" className="font-bold text-slate-900">Verified Achievements</h3><div className="mt-3 flex flex-wrap gap-2">{portfolio.achievements.map((item) => <span className="rounded-full border border-emerald-100 bg-emerald-50 px-3 py-1.5 text-xs font-bold text-emerald-700" key={item.key}>✓ {item.label}</span>)}</div></section>}
    <p className="text-xs text-slate-400">Generated from verified WorkNeuron records · last updated {portfolio.generated_at ? new Date(portfolio.generated_at).toLocaleString() : "when activity changes"}.</p>
  </section>;
}
function Metric({ label, value }) { return <div className="rounded-xl bg-slate-50 p-3"><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-xl font-black text-brand">{value}</p></div>; }
