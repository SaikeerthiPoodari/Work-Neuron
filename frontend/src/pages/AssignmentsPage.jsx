import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { get, post, put } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";

const blankLevel = () => ({ title: "", description: "", requirements: "" });

export default function AssignmentsPage() {
  const { user } = useAuth();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submissions, setSubmissions] = useState({});
  const [feedback, setFeedback] = useState({});
  const [drafts, setDrafts] = useState({});
  const [busy, setBusy] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await get("/assignments/");
      setItems(data);
      setDrafts((current) => Object.fromEntries(data.map((item) => [item.id, current[item.id] || (item.levels.length ? item.levels.map(({ title, description, requirements }) => ({ title, description, requirements })) : [blankLevel()])])));
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load(); }, []);

  const action = async (key, fn) => {
    setBusy(key); setError("");
    try { await fn(); await load(); }
    catch (err) { setError(err.message); }
    finally { setBusy(""); }
  };

  const updateDraft = (assignmentId, index, field, value) => setDrafts((state) => ({
    ...state,
    [assignmentId]: state[assignmentId].map((level, i) => i === index ? { ...level, [field]: value } : level),
  }));

  return <div className="space-y-6">
    <div><p className="text-sm font-semibold text-brand">Work in motion</p><h1 className="mt-1 text-3xl font-black">Assignments</h1><p className="mt-2 max-w-2xl text-slate-500">Work moves through the project stages in order. Each stage must be reviewed before the next one opens.</p></div>
    <ErrorMessage message={error} />
    {loading ? <div className="card text-sm text-slate-500" role="status">Loading assignments…</div> : items.length ? <div className="space-y-5">{items.map((item) => {
      const levels = item.levels || [];
      const canConfigure = user.role === "CLIENT" && item.task_status === "ASSIGNED" && !item.started_at;
      const current = levels.find((level) => level.status === "CURRENT" || level.status === "SUBMITTED");
      return <article className="card" key={item.id}>
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start"><div><h2 className="text-lg font-bold">{item.task_title}</h2><p className="mt-1 text-sm text-slate-500">{user.role === "WORKER" ? "Your assignment" : `Worker: ${item.worker_email}`} · {item.task_status.replaceAll("_", " ").toLowerCase()}</p></div><span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-black text-brand">{item.progress}% complete</span></div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-brand transition-all" style={{ width: `${item.progress}%` }} /></div>

        {canConfigure && <section className="mt-6 rounded-2xl border border-blue-100 bg-blue-50/40 p-4 sm:p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-bold">Plan assignment levels</h3><p className="mt-1 text-sm text-slate-500">Define the ordered stages for this job. The worker can only submit the current stage.</p></div><button className="button-secondary" type="button" onClick={() => setDrafts((state) => ({ ...state, [item.id]: [...state[item.id], blankLevel()] }))}>Add level</button></div>
          <div className="mt-4 space-y-3">{(drafts[item.id] || [blankLevel()]).map((level, index) => <div className="grid gap-3 rounded-xl border border-slate-100 bg-white p-3 md:grid-cols-2" key={index}><div className="flex items-center justify-between gap-3 md:col-span-2"><span className="text-xs font-black uppercase tracking-widest text-brand">Level {index + 1}</span>{(drafts[item.id] || []).length > 1 && <button type="button" className="text-xs font-bold text-rose-600" onClick={() => setDrafts((state) => ({ ...state, [item.id]: state[item.id].filter((_, i) => i !== index) }))}>Remove</button>}</div><input className="field mt-0" aria-label={`Level ${index + 1} title`} placeholder="Stage title" value={level.title} onChange={(event) => updateDraft(item.id, index, "title", event.target.value)} /><input className="field mt-0" aria-label={`Level ${index + 1} requirements`} placeholder="Requirements and proof to submit" value={level.requirements} onChange={(event) => updateDraft(item.id, index, "requirements", event.target.value)} /><textarea className="field mt-0 md:col-span-2" rows="2" aria-label={`Level ${index + 1} description`} placeholder="Instructions for this stage" value={level.description} onChange={(event) => updateDraft(item.id, index, "description", event.target.value)} /></div>)}</div>
          <button className="button-primary mt-4" disabled={busy === `configure-${item.id}`} onClick={() => action(`configure-${item.id}`, () => put(`/assignments/${item.id}/levels/`, { levels: drafts[item.id] }))}>{busy === `configure-${item.id}` ? "Saving…" : "Save assignment plan"}</button>
        </section>}

        {levels.length > 0 && <section className="mt-6"><div className="mb-3 flex items-center justify-between gap-3"><h3 className="font-bold">Assignment stages</h3>{user.role === "WORKER" && item.task_status === "ASSIGNED" && <button className="button-primary" disabled={busy === `start-${item.id}`} onClick={() => action(`start-${item.id}`, () => post(`/assignments/${item.id}/start/`))}>{busy === `start-${item.id}` ? "Starting…" : "Start assignment"}</button>}</div>
          <ol className="space-y-3">{levels.map((level) => {
            const stateLabel = { COMPLETED: "Completed", CURRENT: "Current", SUBMITTED: "Awaiting review", LOCKED: "Locked" }[level.status] || level.status;
            const tone = level.status === "COMPLETED" ? "border-emerald-200 bg-emerald-50/50" : level.status === "CURRENT" ? "border-blue-200 bg-blue-50/50" : level.status === "SUBMITTED" ? "border-amber-200 bg-amber-50/50" : "border-slate-100 bg-slate-50/70";
            return <li className={`rounded-xl border p-4 ${tone}`} key={level.id}><div className="flex flex-wrap items-start justify-between gap-2"><div><p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Level {level.order}</p><h4 className="mt-1 font-bold">{level.title}</h4></div><span className="rounded-full bg-white/80 px-2.5 py-1 text-xs font-bold text-slate-600">{stateLabel}</span></div>
              {level.description && <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-600">{level.description}</p>}{level.requirements && <div className="mt-3 rounded-lg bg-white/75 p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Instructions and requirements</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{level.requirements}</p></div>}
              {level.submission && <div className="mt-3 rounded-lg bg-white p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Worker submission</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{level.submission}</p>{level.submitted_at && <p className="mt-2 text-xs text-slate-400">Submitted {new Date(level.submitted_at).toLocaleString()}</p>}</div>}
              {level.feedback && <p className="mt-3 rounded-lg bg-white/75 p-3 text-sm text-slate-600"><span className="font-bold">Client feedback: </span>{level.feedback}</p>}
              {user.role === "WORKER" && level.status === "CURRENT" && ["IN_PROGRESS", "SUBMITTED"].includes(item.task_status) && <div className="mt-4 space-y-2"><label htmlFor={`submission-${level.id}`} className="text-sm font-semibold">Submit this level</label><textarea id={`submission-${level.id}`} className="field mt-0" rows="3" placeholder="Describe the work completed or provide the requested proof" value={submissions[level.id] || ""} onChange={(event) => setSubmissions((state) => ({ ...state, [level.id]: event.target.value }))} /><button className="button-primary" disabled={!submissions[level.id]?.trim() || busy === `submit-${level.id}`} onClick={() => action(`submit-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/submit/`, { submission: submissions[level.id] }))}>{busy === `submit-${level.id}` ? "Submitting…" : "Submit for review"}</button></div>}
              {user.role === "CLIENT" && level.status === "SUBMITTED" && <div className="mt-4 space-y-2"><label className="text-sm font-semibold" htmlFor={`feedback-${level.id}`}>Review feedback</label><textarea id={`feedback-${level.id}`} className="field mt-0" rows="2" placeholder="Optional feedback for the worker" value={feedback[level.id] || ""} onChange={(event) => setFeedback((state) => ({ ...state, [level.id]: event.target.value }))} /><div className="flex flex-wrap gap-2"><button className="button-primary" disabled={busy === `approve-${level.id}`} onClick={() => action(`approve-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/review/`, { action: "approve", feedback: feedback[level.id] || "" }))}>{level.order === levels.length ? "Approve final level" : "Approve and unlock next"}</button><button className="button-secondary" disabled={busy === `changes-${level.id}`} onClick={() => action(`changes-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/review/`, { action: "changes", feedback: feedback[level.id] || "Please revise and resubmit this level." }))}>Request changes</button></div></div>}
            </li>;
          })}</ol>
        </section>}
        {levels.length === 0 && !canConfigure && <p className="mt-4 text-sm text-amber-700">The assignment plan has not been configured yet. The task owner needs to add levels before work starts.</p>}
      </article>;
    })}</div> : <EmptyState>{user.role === "WORKER" ? "No assignments yet. Apply to a task and wait for the client to accept your application." : "No assignments yet. Create a task, review applications, and accept a worker to create an assignment."}</EmptyState>}
  </div>;
}
