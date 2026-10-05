import { useEffect, useMemo, useState } from "react";
import { Link } from "react-router-dom";
import { get, post } from "../services/api";
import { EmptyState, ErrorMessage } from "./StatusMessage";
import { languageLabels } from "../i18n/languages";

const score = (value) => value == null ? "—" : `${Math.round(value)}%`;
const rating = (value, count) => value == null ? "Not rated" : `${Number(value).toFixed(1)} / 5 (${count})`;

export default function ApplicationComparison() {
  const [tasks, setTasks] = useState([]);
  const [applicationCounts, setApplicationCounts] = useState({});
  const [taskId, setTaskId] = useState("");
  const [comparison, setComparison] = useState(null);
  const [selected, setSelected] = useState([]);
  const [sortBy, setSortBy] = useState("score");
  const [minSkill, setMinSkill] = useState("0");
  const [minRating, setMinRating] = useState("0");
  const [availability, setAvailability] = useState("");
  const [requiredSkill, setRequiredSkill] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [acting, setActing] = useState(null);

  useEffect(() => {
    Promise.all([get("/tasks/"), get("/applications/")]).then(([clientTasks, applications]) => {
      setTasks(clientTasks);
      const counts = applications.reduce((result, item) => {
        if (["SUBMITTED", "ACCEPTED"].includes(item.status)) result[item.task] = (result[item.task] || 0) + 1;
        return result;
      }, {});
      setApplicationCounts(counts);
      const initial = clientTasks.find((item) => counts[item.id] > 0);
      if (initial) setTaskId(String(initial.id));
      else if (clientTasks.length) setTaskId(String(clientTasks[0].id));
      else setLoading(false);
    }).catch((err) => { setError(err.message); setLoading(false); });
  }, []);

  useEffect(() => {
    if (!taskId) return;
    let current = true;
    setLoading(true);
    setComparison(null);
    get(`/applications/tasks/${taskId}/comparison/`).then((result) => {
      if (!current) return;
      setComparison(result);
      setSelected(result.applicants.slice(0, 4).map((item) => item.application.id));
      setError("");
    }).catch((err) => { if (current) setError(err.message); })
      .finally(() => { if (current) setLoading(false); });
    return () => { current = false; };
  }, [taskId]);

  const applicants = useMemo(() => {
    const list = [...(comparison?.applicants || [])].filter((item) => {
      if (Number(minSkill) && (item.match.skill_match == null || item.match.skill_match < Number(minSkill))) return false;
      if (Number(minRating) && (item.worker.rating_average == null || item.worker.rating_average < Number(minRating))) return false;
      if (availability && item.worker.availability !== availability) return false;
      if (requiredSkill && !item.worker.skills.some((skill) => skill.id === Number(requiredSkill))) return false;
      return true;
    });
    const value = (item) => ({
      score: item.match.overall_score,
      skill: item.match.skill_match ?? -1,
      rating: item.worker.rating_average ?? -1,
      experience: item.worker.experience_years ?? -1,
      completed: item.worker.completed_tasks,
      price: item.application.proposed_budget == null ? Number.POSITIVE_INFINITY : Number(item.application.proposed_budget),
    }[sortBy]);
    return list.sort((a, b) => sortBy === "price" ? value(a) - value(b) : value(b) - value(a));
  }, [comparison, minSkill, minRating, availability, requiredSkill, sortBy]);

  const selectedApplicants = applicants.filter((item) => selected.includes(item.application.id));
  const toggleSelected = (applicationId) => setSelected((current) => {
    if (current.includes(applicationId)) return current.filter((id) => id !== applicationId);
    if (current.length >= 4) return current;
    return [...current, applicationId];
  });

  const decide = async (application, action) => {
    setActing(application.id);
    setError("");
    setNotice("");
    try {
      const result = await post(`/applications/${application.id}/decide/`, { action });
      setNotice(action === "accept" ? `Worker selected${result.assignment_id ? `; assignment ${result.assignment_id} created` : ""}.` : "Application rejected.");
      const refreshed = await get(`/applications/tasks/${taskId}/comparison/`);
      setComparison(refreshed);
      setSelected((current) => current.filter((id) => refreshed.applicants.some((item) => item.application.id === id)));
    } catch (err) {
      setError(err.message);
    } finally {
      setActing(null);
    }
  };

  return <section className="card space-y-5" aria-labelledby="application-comparison-title">
    <div><p className="text-xs font-black uppercase tracking-widest text-brand">Client hiring tools</p><h2 id="application-comparison-title" className="mt-1 text-xl font-black">Compare applicants</h2><p className="mt-1 text-sm text-slate-500">Review applicant skills, experience, reputation, and existing match scores before continuing to your normal hiring flow.</p></div>
    <ErrorMessage message={error} />
    {notice && <p role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
    {tasks.length > 0 && <label className="block max-w-xl text-sm font-semibold text-slate-600">Your task<select className="field" value={taskId} onChange={(event) => setTaskId(event.target.value)}><option value="">Select a task</option>{tasks.map((task) => <option value={task.id} key={task.id}>{task.title} · {applicationCounts[task.id] || 0} applicants</option>)}</select></label>}
    {loading ? <div className="rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-500" role="status">Loading applicant comparison…</div> : !tasks.length ? <EmptyState>Create a task to start receiving worker applications.</EmptyState> : comparison && <>
      {!comparison.applicants.length ? <EmptyState>No applications received yet.</EmptyState> : <>
        <div className="flex flex-col gap-3 rounded-xl bg-slate-50 p-3 lg:flex-row lg:items-end">
          <label className="text-xs font-semibold text-slate-600">Sort by<select className="field" value={sortBy} onChange={(event) => setSortBy(event.target.value)}><option value="score">Existing match score</option><option value="skill">Skill match</option><option value="rating">Rating</option><option value="experience">Experience</option><option value="completed">Completed tasks</option><option value="price">Proposed price (low to high)</option></select></label>
          <label className="text-xs font-semibold text-slate-600">Minimum skill match<select className="field" value={minSkill} onChange={(event) => setMinSkill(event.target.value)}>{[0, 25, 50, 75, 100].map((value) => <option key={value} value={value}>{value === 0 ? "Any" : `${value}%`}</option>)}</select></label>
          <label className="text-xs font-semibold text-slate-600">Minimum rating<select className="field" value={minRating} onChange={(event) => setMinRating(event.target.value)}>{[[0, "Any"], [3, "3+"], [4, "4+"], [4.5, "4.5+"]].map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
          <label className="text-xs font-semibold text-slate-600">Profile availability<select className="field" value={availability} onChange={(event) => setAvailability(event.target.value)}><option value="">Any</option><option value="FLEXIBLE">Flexible</option><option value="FULL_TIME">Full time</option><option value="PART_TIME">Part time</option><option value="WEEKENDS">Weekends</option></select></label>
          <label className="text-xs font-semibold text-slate-600">Has required skill<select className="field" value={requiredSkill} onChange={(event) => setRequiredSkill(event.target.value)}><option value="">Any skill</option>{comparison.task.required_skills.map((skill) => <option value={skill.id} key={skill.id}>{skill.name}</option>)}</select></label>
        </div>
        <p className="text-xs text-slate-500">Select 2–4 applicants to compare. Match scores use existing WorkNeuron weights and include their factors below.</p>
        <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{applicants.map((item) => <ApplicantCard key={item.application.id} item={item} selected={selected.includes(item.application.id)} canSelect={selected.length < 4 || selected.includes(item.application.id)} onToggle={() => toggleSelected(item.application.id)} acting={acting === item.application.id} onDecide={decide} />)}</div>
        {comparison.applicants.length === 1 && <p className="rounded-lg bg-amber-50 p-3 text-sm text-amber-900">Only one applicant is available. Comparison requires at least two applicants.</p>}
        {selectedApplicants.length >= 2 && <ComparisonTable applicants={selectedApplicants} task={comparison.task} />}
        {selectedApplicants.length < 2 && comparison.applicants.length > 1 && <p className="text-sm text-slate-500">Select at least two applicants to see the side-by-side comparison.</p>}
        <div className="flex flex-wrap items-center justify-between gap-3 border-t border-slate-100 pt-4"><p className="text-xs text-slate-500">Applicant scoring uses the existing configurable WorkNeuron matching weights. Ratings and profile details are shown from available records.</p><Link className="button-primary" to={`/tasks/${taskId}`}>Open existing application flow</Link></div>
      </>}
    </>}
  </section>;
}

function ApplicantCard({ item, selected, canSelect, onToggle, acting, onDecide }) {
  const { worker, application, match } = item;
  return <article className="rounded-xl border border-slate-200 p-4">
    <div className="flex items-start justify-between gap-3"><div><p className="font-bold text-slate-900">{worker.name}</p><p className="mt-0.5 text-xs text-slate-500">{worker.headline || "Worker profile"}</p></div><label className="flex items-center gap-2 text-xs font-semibold text-brand"><input type="checkbox" checked={selected} disabled={!canSelect} onChange={onToggle} aria-label={`Select ${worker.name} for comparison`} />Compare</label></div>
    <div className="mt-3 flex flex-wrap gap-2 text-xs"><span className="rounded-full bg-blue-50 px-2.5 py-1 font-bold text-blue-800">Match {Math.round(match.overall_score)}%</span><span className="rounded-full bg-emerald-50 px-2.5 py-1 font-bold text-emerald-800">Skills {score(match.skill_match)}</span><span className="rounded-full bg-slate-100 px-2.5 py-1 font-semibold text-slate-700">{rating(worker.rating_average, worker.rating_count)}</span></div>
    <p className="mt-3 line-clamp-3 text-sm text-slate-600">{application.cover_letter}</p>
    <div className="mt-3 flex flex-wrap gap-1.5">{worker.skills.slice(0, 6).map((skill) => <span className="rounded-md bg-slate-100 px-2 py-1 text-[11px] text-slate-600" key={skill.id}>{skill.name}</span>)}{!worker.skills.length && <span className="text-xs text-slate-400">No profile skills listed</span>}</div>
    <details className="mt-3"><summary className="cursor-pointer text-sm font-bold text-brand">View applicant profile</summary><div className="mt-2 space-y-1 text-sm text-slate-600"><p>{worker.bio || "No profile summary provided."}</p><p>Experience: {worker.experience_years == null ? "Not provided" : `${worker.experience_years} years`}</p><p>Availability: {worker.availability?.replaceAll("_", " ") || "Not provided"}</p>{worker.languages?.length > 0 && <p>Languages: {worker.languages.map((code) => languageLabels[code] || code).join(", ")}</p>}<p>Completed tasks: {worker.completed_tasks} · Relevant tasks: {worker.relevant_completed_tasks}</p>{worker.portfolio_url && <a className="font-semibold text-brand underline" href={worker.portfolio_url} target="_blank" rel="noreferrer">Portfolio</a>}</div></details>
    <div className="mt-4 flex flex-wrap items-center gap-2 border-t border-slate-100 pt-3">{application.status === "ACCEPTED" ? <span className="rounded-md bg-emerald-50 px-2.5 py-1 text-xs font-bold text-emerald-800">Worker selected</span> : <><button className="button-primary" disabled={acting} onClick={() => onDecide(application, "accept")}>{acting ? "Updating..." : "Select worker"}</button><button className="rounded-lg border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50" disabled={acting} onClick={() => onDecide(application, "reject")}>Reject</button></>}</div>
  </article>;
}

function ComparisonTable({ applicants, task }) {
  const rows = [
    ["Existing applicant score", (item) => `${item.match.overall_score}%`],
    ["Skill match", (item) => score(item.match.skill_match)],
    ["Experience", (item) => item.worker.experience_years == null ? "Not provided" : `${item.worker.experience_years} years`],
    ["Rating", (item) => rating(item.worker.rating_average, item.worker.rating_count)],
    ["Completed tasks", (item) => item.worker.completed_tasks],
    ["Relevant completed work", (item) => item.worker.relevant_completed_tasks],
    ["Availability", (item) => item.worker.availability?.replaceAll("_", " ") || "Not provided"],
    ["Proposed price", (item) => item.application.proposed_budget == null ? "Not provided" : `₹${Number(item.application.proposed_budget).toLocaleString()}`],
    ["Status", (item) => item.application.status],
  ];
  return <section><h3 className="mb-2 font-bold">Side-by-side comparison · {task.title}</h3><div className="overflow-x-auto rounded-xl border border-slate-200"><table className="min-w-[680px] w-full border-collapse text-left text-sm"><thead className="bg-slate-50"><tr><th className="sticky left-0 bg-slate-50 p-3">Measure</th>{applicants.map((item) => <th className="min-w-36 p-3" key={item.application.id}>{item.worker.name}</th>)}</tr></thead><tbody>{rows.map(([label, getValue]) => <tr className="border-t border-slate-100" key={label}><th className="sticky left-0 bg-white p-3 font-semibold text-slate-600">{label}</th>{applicants.map((item) => <td className="p-3 text-slate-800" key={item.application.id}>{getValue(item)}</td>)}</tr>)}<tr className="border-t border-slate-100"><th className="sticky left-0 bg-white p-3 font-semibold text-slate-600">Score factors</th>{applicants.map((item) => <td className="p-3" key={item.application.id}><details><summary className="cursor-pointer text-xs font-bold text-brand">View factors & weights</summary><ul className="mt-2 space-y-1">{Object.entries(item.match.components).map(([name, value]) => <li className="flex justify-between gap-3 text-xs text-slate-600" key={name}><span>{name.replaceAll("_score", "").replaceAll("_", " ")} ({Math.round(item.match.weights[name.replace(/_score$/, "")] * 100)}%)</span><span>{value == null ? "N/A" : `${Math.round(value)}%`}</span></li>)}</ul><p className="mt-2 max-w-52 text-xs text-slate-500">{item.match.explanation}</p></details></td>)}</tr></tbody></table></div><p className="mt-2 text-xs text-slate-500">Skill match is the existing task-required skill overlap. If the task has no required skills, skill match is unavailable. Scores retain the existing match engine’s neutral defaults where profile signals are absent.</p></section>;
}
