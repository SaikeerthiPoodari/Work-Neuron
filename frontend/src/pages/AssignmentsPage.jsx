import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { get, post, put } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { useI18n } from "../i18n/I18nContext";

const blankLevel = () => ({ title: "", description: "", requirements: "", expected_completion_date: "", payment_amount: "", tasks: "" });

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

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const data = await get("/assignments/");
      setItems(data);
      setDrafts((current) => Object.fromEntries(data.map((item) => [item.id, current[item.id] || (item.levels.length ? item.levels.map(({ title, description, requirements, tasks = [] }) => ({ title, description, requirements, tasks: tasks.map((task) => task.title).join("\n") })) : [blankLevel()])])));
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
    <div><p className="text-sm font-semibold text-brand">{user.role === "WORKER" ? t("workInMotion") : "Work in motion"}</p><h1 className="mt-1 text-3xl font-black">{user.role === "WORKER" ? t("assignments") : "Assignments"}</h1><p className="mt-2 max-w-2xl text-slate-500">{user.role === "WORKER" ? t("assignmentIntro") : "Work moves through the project stages in order. Each stage must be reviewed before the next one opens."}</p></div>
    <ErrorMessage message={error} />
    {user.role === "CLIENT" && <ClientAssignmentOverview items={items} />}
    {user.role === "CLIENT" && <ClientLevelChecks items={items} onSaved={load} />}
    {user.role === "CLIENT" && <ClientStartConfirmations items={items} onSaved={load} />}
    <TwoWayTracker items={items} user={user} onAction={action} />
    {loading ? <div className="card text-sm text-slate-500" role="status">{user.role === "WORKER" ? t("loadingAssignments") : "Loading assignments…"}</div> : items.length ? <div className="space-y-5">{items.map((item) => {
      const levels = item.levels || [];
      const checklistTasks = levels.flatMap((level) => level.tasks || []);
      const requiredTasks = checklistTasks.length;
      const completedTasks = checklistTasks.filter((task) => task.is_completed).length;
      const pendingTasks = requiredTasks - completedTasks;
      const completedLevels = levels.filter((level) => level.status === "COMPLETED").length;
      const pendingLevels = Math.max(0, levels.length - completedLevels);
      const progress = levels.length ? Math.round(completedLevels * 100 / levels.length) : item.progress;
      const canConfigure = user.role === "CLIENT" && item.task_status === "ASSIGNED" && !item.started_at;
      const current = levels.find((level) => level.status === "CURRENT" || level.status === "SUBMITTED");
      return <article className="card" key={item.id}>
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start"><div><h2 className="text-lg font-bold">{item.task_title}</h2><p className="mt-1 text-sm text-slate-500">{user.role === "WORKER" ? "Your assignment" : `Worker: ${item.worker_email}`} · {item.task_status.replaceAll("_", " ").toLowerCase()}</p></div><span className="rounded-full bg-blue-50 px-3 py-1 text-sm font-black text-brand">{progress}% complete</span></div>
        <div className="mt-4 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-brand transition-all" style={{ width: `${progress}%` }} /></div>
        {levels.length > 0 && <section className="mt-5 rounded-2xl bg-slate-50 p-4" aria-label="Assignment level tracker">
          <div className="grid grid-cols-3 gap-2 text-center"><div className="rounded-xl bg-white p-3"><p className="text-xs font-semibold text-slate-500">Required tasks</p><p className="mt-1 text-xl font-black">{requiredTasks}</p></div><div className="rounded-xl bg-emerald-50 p-3"><p className="text-xs font-semibold text-emerald-700">Completed tasks</p><p className="mt-1 text-xl font-black text-emerald-800">{completedTasks}</p></div><div className="rounded-xl bg-white p-3"><p className="text-xs font-semibold text-slate-500">Pending tasks</p><p className="mt-1 text-xl font-black">{pendingTasks}</p></div></div>
          <ol className="mt-4 grid gap-2 sm:grid-cols-2 lg:grid-cols-3">{levels.map((level) => { const complete = level.status === "COMPLETED"; const locked = level.status === "LOCKED"; const label = user.role === "WORKER" ? (complete ? t("completed") : locked ? t("locked") : level.status === "SUBMITTED" ? t("awaitingReview") : t("inProgress")) : (complete ? "Completed" : locked ? "Locked" : level.status === "SUBMITTED" ? "In progress · submitted for review" : "In progress"); return <li key={level.id} className={`rounded-xl border p-3 ${complete ? "border-emerald-200 bg-emerald-50" : locked ? "border-slate-200 bg-slate-100 opacity-75" : "border-blue-200 bg-white"}`}><div className="flex items-center justify-between gap-2"><span className="text-xs font-black uppercase tracking-wide text-slate-500">Level {level.order}</span><span className={`rounded-full px-2 py-1 text-[10px] font-black ${complete ? "bg-emerald-100 text-emerald-800" : locked ? "bg-slate-200 text-slate-600" : "bg-blue-100 text-brand"}`}>{label}</span></div><button type="button" className="mt-2 text-left font-bold hover:text-brand focus-visible:outline focus-visible:outline-2 focus-visible:outline-brand" onClick={() => document.getElementById(`level-detail-${level.id}`)?.scrollIntoView({ behavior: "smooth", block: "center" })} aria-label={`View level ${level.order}: ${level.title}`}>{level.title}</button>{level.requirements && <p className="mt-1 whitespace-pre-line text-xs leading-5 text-slate-600">{level.requirements}</p>}{level.status === "COMPLETED" && level.reviewed_at && <p className="mt-2 text-[11px] text-emerald-800">{user.role === "WORKER" ? t("approved") : "Approved"} {new Date(level.reviewed_at).toLocaleDateString()}</p>}</li>; })}</ol>
        </section>}

        {canConfigure && <section className="mt-6 rounded-2xl border border-blue-100 bg-blue-50/40 p-4 sm:p-5"><div className="flex flex-wrap items-start justify-between gap-3"><div><h3 className="font-bold">Plan assignment levels</h3><p className="mt-1 text-sm text-slate-500">Define the ordered stages for this job. The worker can only submit the current stage.</p></div><button className="button-secondary" type="button" onClick={() => setDrafts((state) => ({ ...state, [item.id]: [...state[item.id], blankLevel()] }))}>Add level</button></div>
          <div className="mt-4 space-y-3">{(drafts[item.id] || [blankLevel()]).map((level, index) => <div className="grid gap-3 rounded-xl border border-slate-100 bg-white p-3 md:grid-cols-2" key={index}><div className="flex items-center justify-between gap-3 md:col-span-2"><span className="text-xs font-black uppercase tracking-widest text-brand">Level {index + 1}</span>{(drafts[item.id] || []).length > 1 && <button type="button" className="text-xs font-bold text-rose-600" onClick={() => setDrafts((state) => ({ ...state, [item.id]: state[item.id].filter((_, i) => i !== index) }))}>Remove</button>}</div><input className="field mt-0" aria-label={`Level ${index + 1} title`} placeholder="Stage title" value={level.title} onChange={(event) => updateDraft(item.id, index, "title", event.target.value)} /><input className="field mt-0" aria-label={`Level ${index + 1} requirements`} placeholder="Requirements and proof to submit" value={level.requirements} onChange={(event) => updateDraft(item.id, index, "requirements", event.target.value)} /><textarea className="field mt-0" rows="3" aria-label={`Level ${index + 1} checklist tasks`} placeholder="Required tasks (one per line). The worker must complete these before submitting." value={level.tasks} onChange={(event) => updateDraft(item.id, index, "tasks", event.target.value)} /><textarea className="field mt-0" rows="2" aria-label={`Level ${index + 1} description`} placeholder="Instructions for this stage" value={level.description} onChange={(event) => updateDraft(item.id, index, "description", event.target.value)} /></div>)}</div>
          <button className="button-primary mt-4" disabled={busy === `configure-${item.id}`} onClick={() => action(`configure-${item.id}`, () => put(`/assignments/${item.id}/levels/`, { levels: drafts[item.id].map(({ tasks = "", ...level }) => ({ ...level, tasks: tasks.split("\n").map((task) => task.trim()).filter(Boolean) })) }))}>{busy === `configure-${item.id}` ? "Saving…" : "Save assignment plan"}</button>
        </section>}

        {levels.length > 0 && <section className="mt-6"><div className="mb-3 flex items-center justify-between gap-3"><h3 className="font-bold">{user.role === "WORKER" ? t("assignmentStages") : "Assignment stages"}</h3>{user.role === "WORKER" && item.task_status === "ASSIGNED" && <button className="button-primary" disabled={busy === `start-${item.id}`} onClick={() => action(`start-${item.id}`, () => post(`/assignments/${item.id}/start/`))}>{busy === `start-${item.id}` ? "Starting…" : t("startAssignment")}</button>}</div>
          <ol className="space-y-3">{levels.map((level) => {
            const stateLabel = user.role === "WORKER" ? ({ COMPLETED: t("completed"), CURRENT: t("inProgress"), SUBMITTED: t("awaitingReview"), LOCKED: t("locked") }[level.status] || level.status) : ({ COMPLETED: "Completed", CURRENT: "Current", SUBMITTED: "Awaiting review", LOCKED: "Locked" }[level.status] || level.status);
            const tone = level.status === "COMPLETED" ? "border-emerald-200 bg-emerald-50/50" : level.status === "CURRENT" ? "border-blue-200 bg-blue-50/50" : level.status === "SUBMITTED" ? "border-amber-200 bg-amber-50/50" : "border-slate-100 bg-slate-50/70";
            return <li id={`level-detail-${level.id}`} className={`rounded-xl border p-4 ${tone}`} key={level.id}><div className="flex flex-wrap items-start justify-between gap-2"><div><p className="text-[10px] font-black uppercase tracking-widest text-slate-400">Level {level.order}</p><h4 className="mt-1 font-bold">{level.title}</h4></div><span className="rounded-full bg-white/80 px-2.5 py-1 text-xs font-bold text-slate-600">{stateLabel}</span></div>
              {level.description && <p className="mt-3 whitespace-pre-wrap text-sm leading-6 text-slate-600">{level.description}</p>}{level.requirements && <div className="mt-3 rounded-lg bg-white/75 p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Instructions and requirements</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{level.requirements}</p></div>}
              {level.tasks?.length > 0 && <div className="mt-3 rounded-lg bg-white/80 p-3"><div className="flex items-center justify-between"><p className="text-xs font-bold uppercase tracking-wide text-slate-500">Required tasks</p><span className="text-xs font-bold text-brand">{level.tasks.filter((task) => task.is_completed).length}/{level.tasks.length}</span></div><ul className="mt-2 space-y-2">{level.tasks.map((task) => <li key={task.id}><label className={`flex items-start gap-2 rounded-lg p-2 text-sm ${task.is_completed ? "bg-emerald-50 text-emerald-800" : "bg-slate-50 text-slate-700"}`}><input type="checkbox" checked={task.is_completed} disabled={user.role !== "WORKER" || task.is_completed || level.status !== "CURRENT" || busy === `check-${task.id}`} onChange={() => action(`check-${task.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/tasks/${task.id}/complete/`, {}))} /><span>{task.title}{task.completed_at && <small className="mt-1 block text-xs text-slate-400">Completed {new Date(task.completed_at).toLocaleDateString()}</small>}</span></label></li>)}</ul></div>}
              {level.submission && <div className="mt-3 rounded-lg bg-white p-3"><p className="text-xs font-bold uppercase tracking-wide text-slate-400">Worker submission</p><p className="mt-1 whitespace-pre-wrap text-sm text-slate-700">{level.submission}</p>{level.submitted_at && <p className="mt-2 text-xs text-slate-400">Submitted {new Date(level.submitted_at).toLocaleString()}</p>}</div>}
              {level.feedback && <p className="mt-3 rounded-lg bg-white/75 p-3 text-sm text-slate-600"><span className="font-bold">Client feedback: </span>{level.feedback}</p>}
              {user.role === "WORKER" && level.status === "CURRENT" && ["IN_PROGRESS", "SUBMITTED"].includes(item.task_status) && <div className="mt-4 space-y-2"><label htmlFor={`submission-${level.id}`} className="text-sm font-semibold">Submit this level</label><textarea id={`submission-${level.id}`} className="field mt-0" rows="3" placeholder="Describe the work completed or provide the requested proof" value={submissions[level.id] || ""} onChange={(event) => setSubmissions((state) => ({ ...state, [level.id]: event.target.value }))} /><button className="button-primary" disabled={!submissions[level.id]?.trim() || busy === `submit-${level.id}`} onClick={() => action(`submit-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/submit/`, { submission: submissions[level.id] }))}>{busy === `submit-${level.id}` ? "Submitting…" : "Submit for review"}</button></div>}
              {user.role === "CLIENT" && level.status === "SUBMITTED" && <div className="mt-4 space-y-2"><label className="text-sm font-semibold" htmlFor={`feedback-${level.id}`}>Review feedback</label><textarea id={`feedback-${level.id}`} className="field mt-0" rows="2" placeholder="Optional feedback for the worker" value={feedback[level.id] || ""} onChange={(event) => setFeedback((state) => ({ ...state, [level.id]: event.target.value }))} /><div className="flex flex-wrap gap-2"><button className="button-primary" disabled={busy === `approve-${level.id}`} onClick={() => action(`approve-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/review/`, { action: "approve", feedback: feedback[level.id] || "" }))}>{level.order === levels.length ? "Approve final level" : "Approve and unlock next"}</button><button className="button-secondary" disabled={busy === `changes-${level.id}`} onClick={() => action(`changes-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/review/`, { action: "changes", feedback: feedback[level.id] || "Please revise and resubmit this level." }))}>Request changes</button></div></div>}
            </li>;
          })}</ol>
        </section>}
        {levels.length === 0 && !canConfigure && <p className="mt-4 text-sm text-amber-700">The assignment plan has not been configured yet. The task owner needs to add levels before work starts.</p>}
      </article>;
    })}</div> : <EmptyState>{user.role === "WORKER" ? t("noAssignments") : "No assignments yet. Create a task, review applications, and accept a worker to create an assignment."}</EmptyState>}
  </div>;
}

function ClientAssignmentOverview({ items }) {
  if (!items.length) return null;
  return <section className="card"><div className="flex items-end justify-between gap-3"><div><p className="text-xs font-black uppercase tracking-widest text-brand">Client visibility</p><h2 className="mt-1 text-xl font-black">Worker progress overview</h2></div><span className="text-xs text-slate-500">Live assignment records</span></div><div className="mt-4 space-y-3">{items.map((item) => <article className="rounded-xl border border-slate-100 p-4" key={item.id}><div className="flex flex-wrap items-start justify-between gap-3"><div className="flex items-center gap-3"><div className="flex h-11 w-11 items-center justify-center overflow-hidden rounded-full bg-blue-50 font-black text-brand">{item.worker_profile_photo ? <img src={item.worker_profile_photo} alt="" className="h-full w-full object-cover" /> : item.worker_name?.[0]}</div><div><p className="font-bold">{item.worker_name || item.worker_email}</p><p className="text-xs text-slate-500">{item.worker_headline || "Worker profile"}{item.worker_location ? ` · ${item.worker_location}` : ""}</p></div></div><span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-black text-brand">{item.progress}% · {item.task_status?.replaceAll("_", " ")}</span></div><div className="mt-3 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-brand" style={{ width: `${item.progress}%` }} /></div><div className="mt-3 grid gap-2 text-xs text-slate-500 sm:grid-cols-4"><span>Applied {item.application_created_at ? new Date(item.application_created_at).toLocaleDateString() : "—"}</span><span>Updated {new Date(item.updated_at).toLocaleDateString()}</span><span>Deadline {item.task_deadline ? new Date(item.task_deadline).toLocaleDateString() : "Flexible"}</span><span>Payment {item.payment?.amount ? `${item.payment.currency} ${item.payment.amount} · ${item.payment.status}` : "Not created"}</span></div><p className="mt-2 text-xs font-semibold text-slate-600">Current stage: {item.current_level?.title || (item.task_status === "COMPLETED" ? "Completed" : item.task_status?.replaceAll("_", " "))}</p></article>)}</div></section>;
}

function ClientLevelChecks({ items, onSaved }) {
  const active = items.flatMap((item) => (item.levels || []).flatMap((level) => (level.tasks || []).filter((task) => !task.client_completed).map((task) => ({ item, level, task }))));
  if (!active.length) return null;
  const confirm = async (entry) => { await post(`/assignments/${entry.item.id}/levels/${entry.level.id}/tasks/${entry.task.id}/client-complete/`, {}); await onSaved(); };
  return <section className="card"><div><p className="text-xs font-black uppercase tracking-widest text-brand">Client confirmation</p><h2 className="mt-1 text-xl font-black">Confirm completed work</h2><p className="mt-1 text-sm text-slate-500">Confirm each delivered checklist item. Final escrow release is blocked until both the worker and client confirm.</p></div><div className="mt-4 grid gap-3 md:grid-cols-2">{active.map(({ item, level, task }) => <label className="flex items-start gap-3 rounded-xl border border-amber-200 bg-amber-50/60 p-4" key={task.id}><input type="checkbox" className="mt-1" onChange={() => confirm({ item, level, task })} /><span><b>{task.title}</b><span className="mt-1 block text-xs text-slate-500">{item.task_title} · Level {level.order}</span></span></label>)}</div></section>;
}

function ClientStartConfirmations({ items, onSaved }) {
  const pending = items.filter((item) => item.task_status === "ASSIGNED" && item.levels?.length && !item.client_started_at);
  if (!pending.length) return null;
  return <section className="card"><p className="text-xs font-black uppercase tracking-widest text-brand">Two-way start</p><h2 className="mt-1 text-xl font-black">Confirm task commencement</h2><p className="mt-1 text-sm text-slate-500">The client and worker must both confirm after escrow funding. Work unlocks only after both confirmations.</p><div className="mt-4 space-y-3">{pending.map((item) => <div className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-blue-200 bg-blue-50/60 p-4" key={item.id}><div><b>{item.task_title}</b><p className="mt-1 text-xs text-slate-500">Worker confirmation: {item.worker_started_at ? "received" : "waiting"}. Funds: {item.payment?.escrow_status || "not held"}.</p></div><button className="button-primary" disabled={item.payment?.escrow_status !== "HELD"} onClick={() => post(`/assignments/${item.id}/start/`).then(onSaved)}>Confirm start</button></div>)}</div></section>;
}

function TwoWayTracker({ items, user, onAction }) {
  const assignments = items.filter((item) => item.levels?.length);
  if (!assignments.length) return null;
  return <section className="space-y-4" aria-label="Two-way milestone trackers">{assignments.map((item) => <TrackerCard key={item.id} item={item} user={user} onAction={onAction} />)}</section>;
}

function TrackerCard({ item, user, onAction }) {
  const levels = item.levels || [];
  const completed = levels.filter((level) => level.status === "COMPLETED").length;
  const progress = Math.round(completed * 100 / levels.length);
  const funded = ["HELD", "RELEASED"].includes(item.payment?.escrow_status);
  const confirmTask = (level, task, role) => onAction(`tracker-${role}-${task.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/tasks/${task.id}/${role === "client" ? "client-complete" : "complete"}/`, {}));
  const submit = (level) => onAction(`tracker-submit-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/submit/`, { submission: "Progress confirmed from the milestone tracker." }));
  const approve = (level) => onAction(`tracker-approve-${level.id}`, () => post(`/assignments/${item.id}/levels/${level.id}/review/`, { action: "approve", feedback: "Confirmed from the milestone tracker." }));
  return <article className="card border-slate-200"><div className="flex flex-wrap items-start justify-between gap-4"><div><p className="text-xs font-black uppercase tracking-widest text-brand">WorkNeuron – Two-way work tracker</p><h2 className="mt-2 text-xl font-black">{item.task_title}</h2><p className="mt-1 text-sm text-slate-500">{user.role === "CLIENT" ? `Worker: ${item.worker_name || item.worker_email}` : `Client: ${item.client_name || "Task owner"}`}</p><p className="mt-2 max-w-2xl text-sm text-slate-600">{item.task_description || "Track the agreed work levels and confirm progress together."}</p></div><span className={`rounded-full px-3 py-1 text-xs font-bold ${funded ? "bg-emerald-100 text-emerald-700" : "bg-orange-100 text-orange-700"}`}>{funded ? "Funded" : "Payment pending"}</span></div><div className="mt-5 flex flex-wrap items-end justify-between gap-3 border-b border-slate-100 pb-4"><div><p className="text-sm font-bold">Total agreed amount</p><p className="mt-1 text-xs text-slate-500">Held payment</p></div><div className="text-right"><p className="text-xl font-black text-emerald-600">{item.payment?.currency || "INR"} {item.payment?.amount || "0"}</p><p className="text-xs text-slate-500">{item.payment?.escrow_status || "Not funded"}</p></div></div><h3 className="mt-5 text-sm font-black">Milestone tracker</h3><ol className="mt-3 space-y-0">{levels.map((level, index) => <TrackerLevel key={level.id} item={item} level={level} index={index} user={user} onAction={onAction} confirmTask={confirmTask} submit={submit} approve={approve} />)}</ol><div className="mt-2 border-t border-slate-100 pt-4"><div className="flex justify-between text-sm font-bold"><span>Overall progress</span><span>{progress}%</span></div><div className="mt-2 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-emerald-500 transition-all" style={{ width: `${progress}%` }} /></div></div></article>;
}

function TrackerLevel({ item, level, index, user, confirmTask, submit, approve }) {
  const locked = level.status === "LOCKED";
  const complete = level.status === "COMPLETED";
  const submitted = level.status === "SUBMITTED";
  const workerConfirmed = complete || submitted || (level.tasks?.length > 0 && level.tasks.every((task) => task.is_completed));
  const clientConfirmed = complete || (level.tasks?.length > 0 && level.tasks.every((task) => task.client_completed));
  const label = complete ? "Completed" : submitted ? (clientConfirmed ? "Both confirmed" : "Awaiting client") : locked ? "Locked" : "In progress";
  const tone = complete || (submitted && clientConfirmed) ? "bg-emerald-100 text-emerald-700" : submitted ? "bg-orange-100 text-orange-700" : locked ? "bg-slate-100 text-slate-600" : "bg-blue-100 text-brand";
  return <li className="relative border-l-2 border-slate-200 pb-5 pl-5 last:border-l-0"><span className={`absolute -left-[9px] top-0 h-4 w-4 rounded-full border-2 border-white ${complete ? "bg-emerald-500" : locked ? "bg-slate-300" : "bg-brand"}`} /><div className="flex flex-wrap items-center justify-between gap-2"><span className="font-bold">{index + 1} &nbsp; {level.title}</span><span className={`rounded-full px-2 py-1 text-[11px] font-bold ${tone}`}>{label}</span></div>{level.expected_completion_date && <p className="mt-1 text-xs text-slate-500">Expected: {level.expected_completion_date} · Allocation: ₹{level.payment_amount}</p>}{complete || locked ? <p className="mt-2 text-xs text-slate-500">{complete ? "Client ✓ · Worker ✓" : "This level remains locked until the previous level is mutually confirmed."}</p> : <div className="mt-3 rounded-xl border border-slate-200 bg-slate-50 p-3"><p className="text-xs font-bold">Confirmation status</p><div className="mt-2 grid gap-2 text-xs sm:grid-cols-2"><span>Worker <b className={`float-right rounded-full px-2 py-1 ${workerConfirmed ? "bg-emerald-100 text-emerald-700" : "bg-orange-100 text-orange-700"}`}>{workerConfirmed ? "Submitted" : "Pending"}</b></span><span>Client <b className={`float-right rounded-full px-2 py-1 ${clientConfirmed ? "bg-emerald-100 text-emerald-700" : "bg-orange-100 text-orange-700"}`}>{clientConfirmed ? "Confirmed" : "Pending"}</b></span></div>{level.tasks?.length > 0 && <div className="mt-3 space-y-2">{level.tasks.map((task) => <div className="flex flex-wrap items-center justify-between gap-2 rounded-lg bg-white p-2 text-xs" key={task.id}><span>{task.title}</span>{user.role === "WORKER" && !task.is_completed && <button className="button-secondary px-2 py-1 text-xs" onClick={() => confirmTask(level, task, "worker")}>Mark completed</button>}{user.role === "CLIENT" && !task.client_completed && <button className="button-secondary px-2 py-1 text-xs" onClick={() => confirmTask(level, task, "client")}>Confirm</button>}</div>)}</div>}{user.role === "WORKER" && item.task_status === "IN_PROGRESS" && level.status === "CURRENT" && <button className="button-primary mt-3" onClick={() => submit(level)}>Submit level</button>}{user.role === "CLIENT" && level.status === "SUBMITTED" && <button className="button-primary mt-3" onClick={() => approve(level)}>Confirm level and unlock next</button>}<p className="mt-2 text-[11px] text-slate-500">{submitted && !clientConfirmed ? "Next level remains locked until both confirm." : ""}</p></div>}</li>;
}
