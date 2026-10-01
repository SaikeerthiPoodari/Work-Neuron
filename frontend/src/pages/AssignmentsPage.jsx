import { useCallback, useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { get, post, put } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { useI18n } from "../i18n/I18nContext";

const blankLevel = () => ({ title: "", description: "", deliverables: "", required_materials: "", requirements: "", tasks: "" });
const levelDrafts = (levels) => levels.map((level) => ({
  title: level.title,
  description: level.description,
  deliverables: level.deliverables || "",
  required_materials: level.required_materials || "",
  requirements: level.requirements,
  tasks: (level.tasks || []).map((task) => task.title).join("\n"),
}));

export default function AssignmentsPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [items, setItems] = useState([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [submissions, setSubmissions] = useState({});
  const [feedback, setFeedback] = useState({});
  const [drafts, setDrafts] = useState({});
  const [busy, setBusy] = useState("");

  const load = useCallback(async ({ quiet = false } = {}) => {
    if (!quiet) setLoading(true);
    setError("");
    try {
      const data = await get("/assignments/");
      setItems(data);
      setDrafts((current) => {
        const next = { ...current };
        data.forEach((item) => { next[item.id] = current[item.id] || (item.levels.length ? levelDrafts(item.levels) : [blankLevel()]); });
        return next;
      });
    } catch (err) { setError(err.message); }
    finally { if (!quiet) setLoading(false); }
  }, []);

  useEffect(() => { load(); }, [load]);

  const action = async (key, fn) => {
    setBusy(key); setError("");
    try { await fn(); await load({ quiet: true }); }
    catch (err) { setError(err.message); }
    finally { setBusy(""); }
  };

  const updateDraft = (assignmentId, index, field, value) => setDrafts((state) => ({
    ...state,
    [assignmentId]: state[assignmentId].map((level, i) => i === index ? { ...level, [field]: value } : level),
  }));

  const worker = user.role === "WORKER";
  return <div className="space-y-6">
    <header><p className="text-sm font-semibold text-brand">{worker ? t("workInMotion") : "Work in motion"}</p><h1 className="mt-1 text-3xl font-black">{worker ? t("assignments") : "Assignments"}</h1><p className="mt-2 max-w-2xl text-slate-500">{worker ? t("assignmentIntro") : "Review each submitted level to approve it and unlock the next stage."}</p></header>
    <ErrorMessage message={error} />
    {loading ? <div className="card text-sm text-slate-500" role="status">{worker ? t("loadingAssignments") : "Loading assignments…"}</div> : items.length ? <div className="space-y-5">{items.map((item) => {
      const levels = item.levels || [];
      const canConfigure = !worker && item.task_status === "ASSIGNED" && !item.started_at;
      const isCompleted = item.task_status === "COMPLETED";
      return <article className="card" key={item.id}>
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start"><div><h2 className="text-lg font-bold">{item.task_title}</h2><p className="mt-1 text-sm text-slate-500">{worker ? "Your assignment" : `Worker: ${item.worker_email}`} · {isCompleted ? "COMPLETED" : item.task_status.replaceAll("_", " ").toLowerCase()}</p></div><div className="text-right"><span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-black text-brand">{item.progress}% complete</span>{isCompleted && <p className="mt-2 text-xs font-bold text-emerald-700">Assignment completed</p>}</div></div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-brand transition-all" style={{ width: `${item.progress}%` }} /></div>

        {canConfigure && <section className="mt-6 rounded-2xl border border-blue-100 bg-blue-50/40 p-4 sm:p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-bold">Plan assignment levels</h3><p className="mt-1 text-sm text-slate-500">Define the ordered stages. The worker can work on one unlocked stage at a time.</p></div><button className="button-secondary" type="button" onClick={() => setDrafts((state) => ({ ...state, [item.id]: [...state[item.id], blankLevel()] }))}>Add level</button></div>
          <div className="mt-4 space-y-3">{(drafts[item.id] || [blankLevel()]).map((level, index) => <div className="grid gap-3 rounded-xl border border-slate-100 bg-white p-3 md:grid-cols-2" key={index}><div className="flex items-center justify-between gap-3 md:col-span-2"><span className="text-xs font-black uppercase tracking-widest text-brand">Level {index + 1}</span>{(drafts[item.id] || []).length > 1 && <button type="button" className="text-xs font-bold text-rose-600" onClick={() => setDrafts((state) => ({ ...state, [item.id]: state[item.id].filter((_, i) => i !== index) }))}>Remove</button>}</div><input className="field mt-0" aria-label={`Level ${index + 1} title`} required placeholder="Level title" value={level.title} onChange={(event) => updateDraft(item.id, index, "title", event.target.value)} /><textarea className="field mt-0" rows="2" aria-label={`Level ${index + 1} task description`} required placeholder="Task / what the worker has to do" value={level.description} onChange={(event) => updateDraft(item.id, index, "description", event.target.value)} /><textarea className="field mt-0" rows="4" aria-label={`Level ${index + 1} step-by-step instructions`} required placeholder="Step-by-step instructions (one step per line)" value={level.tasks} onChange={(event) => updateDraft(item.id, index, "tasks", event.target.value)} /><textarea className="field mt-0" rows="2" aria-label={`Level ${index + 1} deliverables`} required placeholder="Required deliverables (one per line)" value={level.deliverables || ""} onChange={(event) => updateDraft(item.id, index, "deliverables", event.target.value)} /><textarea className="field mt-0" rows="2" aria-label={`Level ${index + 1} required files or data`} required placeholder="Files or data the worker needs" value={level.required_materials || ""} onChange={(event) => updateDraft(item.id, index, "required_materials", event.target.value)} /><textarea className="field mt-0" rows="2" aria-label={`Level ${index + 1} submission requirements`} required placeholder="Submission requirements and proof to provide" value={level.requirements} onChange={(event) => updateDraft(item.id, index, "requirements", event.target.value)} /></div>)}</div>
          <button className="button-primary mt-4" disabled={busy === `configure-${item.id}`} onClick={() => action(`configure-${item.id}`, () => put(`/assignments/${item.id}/levels/`, { levels: drafts[item.id].map(({ tasks = "", ...level }) => ({ ...level, tasks: tasks.split("\n").map((task) => task.trim()).filter(Boolean) })) }))}>{busy === `configure-${item.id}` ? "Saving…" : "Save assignment plan"}</button>
        </section>}

        {levels.length > 0 && <section className="mt-6" aria-label="Assignment levels"><div className="mb-3"><h3 className="font-bold">{worker ? t("assignmentStages") : "Assignment levels"}</h3></div>
          <ol className="space-y-3">{levels.map((level) => {
            const stateLabels = worker ? { COMPLETED: "Approved", CURRENT: "Unlocked", SUBMITTED: "Pending Client Approval", LOCKED: "Locked" } : { COMPLETED: "Approved", CURRENT: "Unlocked", SUBMITTED: "Pending review", LOCKED: "Locked" };
            const tone = level.status === "COMPLETED" ? "border-emerald-200 bg-emerald-50/50" : level.status === "CURRENT" ? "border-blue-200 bg-blue-50/50" : level.status === "SUBMITTED" ? "border-amber-200 bg-amber-50/50" : "border-slate-200 bg-slate-50";
            const canWork = worker && level.status === "CURRENT" && ["IN_PROGRESS", "SUBMITTED"].includes(item.task_status);
            const blocker = level.status === "LOCKED" ? `Complete and get Level ${level.order - 1} approved by the client to unlock this level.` : level.status === "SUBMITTED" ? "Waiting for the client to approve this level before the next level unlocks." : "";
            return <li id={`level-detail-${level.id}`} className={`rounded-xl border p-4 ${tone}`} key={level.id}>
              <div className="flex flex-wrap items-start justify-between gap-2"><div className="flex items-start gap-2"><span className="mt-0.5 text-sm font-black" aria-hidden="true">{level.status === "COMPLETED" ? "✓" : level.status === "CURRENT" ? "→" : level.status === "SUBMITTED" ? "⏳" : "🔒"}</span><div><p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Level {level.order}</p><h4 className="mt-1 font-bold">{level.title}</h4></div></div><span className="rounded-full bg-white/80 px-2.5 py-1 text-xs font-bold text-slate-700">{stateLabels[level.status] || level.status}</span></div>
              <>
                <div className="mt-4 rounded-lg bg-white/80 p-3"><h5 className="text-xs font-bold uppercase tracking-wide text-slate-500">Task / what to do</h5><p className={`mt-2 whitespace-pre-wrap text-sm leading-6 ${level.description ? "text-slate-700" : "italic text-slate-400"}`}>{level.description || "The client has not provided a task description for this level yet."}</p></div>
                <div className="mt-3 rounded-lg bg-white/80 p-3"><div className="flex items-center justify-between"><h5 className="text-xs font-bold uppercase tracking-wide text-slate-500">Step-by-step instructions</h5>{level.tasks?.length > 0 && <span className="text-xs font-bold text-brand">{level.tasks.filter((task) => task.is_completed).length}/{level.tasks.length} done</span>}</div>{level.tasks?.length > 0 ? <ol className="mt-2 list-decimal space-y-2 pl-5">{level.tasks.map((task) => <li className="text-sm text-slate-700" key={task.id}><label className="flex items-start gap-2"><input type="checkbox" checked={task.is_completed} disabled={!worker || task.is_completed || level.status !== "CURRENT" || !["IN_PROGRESS", "SUBMITTED"].includes(item.task_status) || busy === `check-${task.id}`} onChange={() => action(`check-${task.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/tasks/${task.id}/complete/`, {}))} /><span>{task.title}{task.completed_at && <small className="mt-1 block text-xs text-slate-400">Completed {new Date(task.completed_at).toLocaleDateString()}</small>}</span></label></li>)}</ol> : <p className="mt-2 text-sm italic text-slate-400">The client has not added step-by-step tasks for this level.</p>}</div>
                <SpecField label="Required deliverables" value={level.deliverables} />
                <SpecField label="Files or data needed" value={level.required_materials} />
                <SpecField label="Submission requirements" value={level.requirements} />
                {blocker && <p className={`mt-3 rounded-lg p-3 text-sm font-semibold ${level.status === "LOCKED" ? "bg-slate-200 text-slate-700" : "bg-amber-100 text-amber-800"}`}>{level.status === "LOCKED" ? "Locked: " : "Pending approval: "}{blocker}</p>}
                {level.submission && <div className="mt-3 rounded-lg bg-white p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Worker submission</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{level.submission}</p>{level.submitted_at && <p className="mt-2 text-xs text-slate-400">Submitted {new Date(level.submitted_at).toLocaleString()}</p>}</div>}
                {level.feedback && <p className="mt-3 rounded-lg bg-white/75 p-3 text-sm text-slate-600"><span className="font-bold">Client feedback: </span>{level.feedback}</p>}
                {worker && level.status === "CURRENT" && item.task_status === "ASSIGNED" && <button className="button-primary mt-4" disabled={busy === `start-${item.id}`} onClick={() => action(`start-${item.id}`, () => post(`/assignments/${item.id}/start/`))}>{busy === `start-${item.id}` ? "Starting…" : `Start Level ${level.order}`}</button>}
                {canWork && <div className="mt-4 space-y-2"><label htmlFor={`submission-${level.id}`} className="text-sm font-semibold">Submit Level {level.order} for client approval</label><textarea id={`submission-${level.id}`} className="field mt-0" rows="3" placeholder="Describe your completed work and provide the required proof" value={submissions[level.id] || ""} onChange={(event) => setSubmissions((state) => ({ ...state, [level.id]: event.target.value }))} /><button className="button-primary" disabled={!submissions[level.id]?.trim() || busy === `submit-${level.id}`} onClick={() => action(`submit-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/submit/`, { submission: submissions[level.id] }))}>{busy === `submit-${level.id}` ? "Submitting…" : `Submit Level ${level.order}`}</button></div>}
                {!worker && level.status === "SUBMITTED" && <div className="mt-4 space-y-2"><label className="text-sm font-semibold" htmlFor={`feedback-${level.id}`}>Review feedback</label><textarea id={`feedback-${level.id}`} className="field mt-0" rows="2" placeholder="Optional feedback for the worker" value={feedback[level.id] || ""} onChange={(event) => setFeedback((state) => ({ ...state, [level.id]: event.target.value }))} /><div className="flex flex-wrap gap-2"><button className="button-primary" disabled={busy === `approve-${level.id}`} onClick={() => action(`approve-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/review/`, { action: "approve", feedback: feedback[level.id] || "" }))}>{level.order === levels.length ? "Approve final level" : "Approve and unlock next"}</button><button className="button-secondary" disabled={busy === `reject-${level.id}`} onClick={() => action(`reject-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/review/`, { action: "reject", feedback: feedback[level.id] || "Please revise and resubmit this level." }))}>Reject and request changes</button></div></div>}
              </>
            </li>;
          })}</ol>
        </section>}
        {levels.length === 0 && !canConfigure && <p className="mt-4 text-sm text-amber-700">The assignment plan has not been configured yet. The task owner needs to add levels before work can start.</p>}
      </article>;
    })}</div> : <EmptyState>{worker ? t("noAssignments") : "No assignments yet. Create a task, review applications, and accept a worker to create an assignment."}</EmptyState>}
  </div>;
}

function SpecField({ label, value }) {
  return <div className="mt-3 rounded-lg bg-white/80 p-3"><h5 className="text-xs font-bold uppercase tracking-wide text-slate-500">{label}</h5><p className={`mt-2 whitespace-pre-wrap text-sm leading-6 ${value ? "text-slate-700" : "italic text-slate-400"}`}>{value || "The client has not provided this information yet."}</p></div>;
}
