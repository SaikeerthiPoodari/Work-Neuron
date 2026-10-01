import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { get } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import WorkerSkillGapAnalyzer from "../components/WorkerSkillGapAnalyzer";
import ApplicationComparison from "../components/ApplicationComparison";
import WorkerSkillProgress from "../components/WorkerSkillProgress";
import WorkerLanguageSummary from "../components/WorkerLanguageSummary";
import { useI18n } from "../i18n/I18nContext";

export default function DashboardPage() {
  const { user } = useAuth(); const [data, setData] = useState(null); const [error, setError] = useState("");
  useEffect(() => {
    let active = true;
    const load = async () => {
      try {
        if (user.role === "ADMIN") setData({ analytics: await get("/analytics/summary/") });
        else {
          const requests = [get("/tasks/"), get("/assignments/"), get("/notifications/?unread=true")];
          if (user.role === "CLIENT") requests.push(get("/payments/employer-dashboard/"));
          const [tasks, assignments, notifications, employer] = await Promise.all(requests);
          if (active) setData({ tasks, assignments, notifications, employer });
        }
      } catch (err) { if (active) setError(err.message); }
    };
    load();
    if (user.role !== "WORKER") return () => { active = false; };
    const refreshAssignments = async () => {
      try {
        const assignments = await get("/assignments/");
        if (active) setData((current) => current ? { ...current, assignments } : current);
      } catch (err) { if (active) setError(err.message); }
    };
    const timer = window.setInterval(refreshAssignments, 5000);
    window.addEventListener("focus", refreshAssignments);
    return () => { active = false; window.clearInterval(timer); window.removeEventListener("focus", refreshAssignments); };
  }, [user.role]);
  if (!data) return <div className="py-10 text-slate-500">Loading your workspace...</div>;
  if (user.role === "ADMIN") return <AdminOverview analytics={data.analytics} />;
  const employer = data.employer;
  if (user.role === "WORKER") return <WorkerDashboard user={user} data={data} error={error} />;
  return <div className="space-y-7"><div className="hero-panel"><div className="relative z-10 max-w-xl"><p className="text-sm font-bold text-blue-100">{user.role === "WORKER" ? "Your opportunity cockpit" : "Your delivery cockpit"}</p><h1 className="mt-2 text-3xl font-black tracking-tight text-white sm:text-4xl">Good to see you, {user.first_name || user.email.split("@")[0]}.</h1><p className="mt-3 text-sm leading-6 text-blue-100">{user.role === "WORKER" ? "Turn your strongest skills into your next great project." : "Find the right talent, move faster, and keep every delivery visible."}</p><div className="mt-6 flex flex-wrap gap-3"><Link className="rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-brand shadow-sm" to={user.role === "WORKER" ? "/recommendations" : "/tasks"}>{user.role === "WORKER" ? "See smart matches â†’" : "Publish a task â†’"}</Link><Link className="rounded-xl border border-white/30 px-4 py-2.5 text-sm font-bold text-white" to="/assignments">Open assignments</Link></div></div><div className="hero-orb">âœ¦</div></div><ErrorMessage message={error} />{user.role === "WORKER" && <><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{[["Nearby jobs", "/nearby", "Explore jobs around your location"], ["Reviews", "/reviews", "See your client feedback"], ["Payments & earnings", "/payments", "Review completed and pending payments"], ["Support", "/complaints", "Create or follow a support request"], ["Worker profile", "/profile", "Keep your skills and preferences current"], ["Matched jobs", "/recommendations", "Browse jobs ranked for your profile"]].map(([title, href, detail]) => <Link className="card transition hover:border-blue-200 hover:shadow-md" to={href} key={href}><h2 className="font-bold">{title} <span className="text-brand">â†’</span></h2><p className="mt-1 text-sm text-slate-500">{detail}</p></Link>)}</div><WorkerLanguageSummary /><WorkerSkillProgress /><WorkerSkillGapAnalyzer /></>}{employer && <EmployerOverview dashboard={employer} />}{user.role === "CLIENT" && <ApplicationComparison />}<div className="grid gap-4 sm:grid-cols-3"><Metric label={user.role === "WORKER" ? "Available tasks" : "Your tasks"} value={data.tasks.length} accent="blue" /><Metric label="Active assignments" value={data.assignments.length} accent="mint" /><Metric label="Unread updates" value={data.notifications.length} accent="amber" /></div><div className="grid gap-6 lg:grid-cols-[1.15fr_.85fr]"><section><div className="mb-3 flex items-end justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-slate-400">Fresh opportunities</p><h2 className="mt-1 text-xl font-black">Recent tasks</h2></div><Link className="text-sm font-bold text-brand" to="/tasks">View all â†’</Link></div>{data.tasks.slice(0, 4).map((task) => <Link to={`/tasks/${task.id}`} className="card mb-3 block transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md" key={task.id}><div className="flex justify-between gap-3"><div><div className="mb-2 flex items-center gap-2"><span className="status-dot" /><span className="text-[10px] font-black uppercase tracking-widest text-emerald-700">{task.status.replaceAll("_", " ")}</span></div><h3 className="font-bold">{task.title}</h3><p className="mt-1 line-clamp-2 text-sm text-slate-500">{task.description}</p></div><span className="whitespace-nowrap text-sm font-black text-emerald-700">â‚¹{task.budget}</span></div><div className="mt-4 flex justify-between text-xs font-medium text-slate-400"><span>{task.location || "Remote"}</span><span>{task.deadline ? `Due ${new Date(task.deadline).toLocaleDateString()}` : "Flexible deadline"}</span></div></Link>)}{!data.tasks.length && <EmptyState>No tasks available yet.</EmptyState>}</section><section><div className="mb-3"><p className="text-xs font-bold uppercase tracking-widest text-slate-400">Momentum</p><h2 className="mt-1 text-xl font-black">Active assignments</h2></div>{data.assignments.slice(0, 4).map((item) => <Link to="/assignments" className="card mb-3 block" key={item.id}><div className="flex justify-between"><h3 className="font-bold">{item.task_title}</h3><span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-black text-brand">{item.progress}%</span></div><div className="mt-4 h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-brand transition-all" style={{ width: `${item.progress}%` }} /></div><p className="mt-3 text-xs font-medium text-slate-400">{item.task_status?.replaceAll("_", " ") || "In progress"}</p></Link>)}{!data.assignments.length && <EmptyState>No assignments yet.</EmptyState>}</section></div></div>;
}
function EmployerOverview({ dashboard }) { return <section><div className="mb-3 flex items-center justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-slate-400">Employer operations</p><h2 className="mt-1 text-xl font-black">Business overview</h2></div><Link className="text-sm font-bold text-brand" to="/payments">Financial details â†’</Link></div><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5"><Metric label="Active jobs" value={dashboard.active_jobs.length} accent="blue" /><Metric label="Applications" value={dashboard.application_count} accent="mint" /><Metric label="Selected workers" value={dashboard.selected_worker_count} accent="amber" /><Metric label="Reports" value={dashboard.report_count} accent="rose" /><Metric label="Verification" value={dashboard.verification.status} accent="blue" /></div></section>; }
function Metric({ label, value, accent }) { return <div className={`metric-card metric-${accent}`}><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 text-2xl font-black">{value}</p><div className="mt-3 h-1 w-10 rounded-full bg-current opacity-40" /></div>; }
function AdminOverview({ analytics }) { return <div className="space-y-8"><div><p className="text-sm font-semibold text-brand">Control center</p><h1 className="mt-1 text-3xl font-black tracking-tight">Platform overview</h1><p className="mt-2 text-slate-500">A live snapshot of WorkNeuron activity.</p></div><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Metric label="Users" value={analytics.users.total} accent="blue" /><Metric label="Tasks" value={analytics.tasks.total} accent="mint" /><Metric label="Assignments" value={analytics.assignments.total} accent="amber" /><Metric label="Open complaints" value={analytics.complaints.open} accent="rose" /></div><div className="card"><h2 className="font-bold">Task lifecycle</h2><div className="mt-4 grid gap-3 sm:grid-cols-3">{Object.entries(analytics.tasks.by_status).map(([key, value]) => <div className="rounded-xl bg-slate-50 p-3" key={key}><p className="text-xs font-semibold text-slate-500">{key.replaceAll("_", " ")}</p><p className="mt-1 text-xl font-bold">{value}</p></div>)}</div></div></div>; }

function WorkerDashboard({ user, data, error }) {
  const { t } = useI18n();
  const shortcuts = [["nearbyCard", "/nearby", "exploreNearby"], ["reviewsCard", "/reviews", "viewClientFeedback"], ["earningsCard", "/payments", "paymentHistoryHint"], ["supportCard", "/complaints", "supportTicketHint"], ["profileCard", "/profile", "profileHint"], ["matchesCard", "/recommendations", "matchesHint"]];
  return <div className="space-y-7">
    <div className="hero-panel"><div className="relative z-10 max-w-xl"><p className="text-sm font-bold text-blue-100">{t("workerOpportunityTitle")}</p><h1 className="mt-2 text-3xl font-black tracking-tight text-white sm:text-4xl">{t("workerWelcome")}, {user.first_name || user.email.split("@")[0]}.</h1><p className="mt-3 text-sm leading-6 text-blue-100">{t("workerTagline")}</p><div className="mt-6 flex flex-wrap gap-3"><Link className="rounded-xl bg-white px-4 py-2.5 text-sm font-bold text-brand shadow-sm" to="/recommendations">{t("smartMatches")} ?</Link><Link className="rounded-xl border border-white/30 px-4 py-2.5 text-sm font-bold text-white" to="/assignments">{t("assignments")}</Link></div></div><div className="hero-orb">?</div></div>
    <ErrorMessage message={error} />
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">{shortcuts.map(([title, href, detail]) => <Link className="card transition hover:border-blue-200 hover:shadow-md" to={href} key={href}><h2 className="font-bold">{t(title)} <span className="text-brand">?</span></h2><p className="mt-1 text-sm text-slate-500">{t(detail)}</p></Link>)}</div>
    <WorkerLanguageSummary /><WorkerSkillProgress /><WorkerSkillGapAnalyzer />
    <div className="grid gap-4 sm:grid-cols-3"><Metric label={t("availableTasks")} value={data.tasks.length} accent="blue" /><Metric label={t("activeAssignments")} value={data.assignments.length} accent="mint" /><Metric label={t("unreadUpdates")} value={data.notifications.length} accent="amber" /></div>
    <div className="grid gap-6 lg:grid-cols-[1.15fr_.85fr]">
      <section><div className="mb-3 flex items-end justify-between"><div><p className="text-xs font-bold uppercase tracking-widest text-slate-400">{t("freshOpportunities")}</p><h2 className="mt-1 text-xl font-black">{t("recentTasks")}</h2></div><Link className="text-sm font-bold text-brand" to="/tasks">{t("viewAll")} ?</Link></div>{data.tasks.slice(0, 4).map((task) => <Link to={`/tasks/${task.id}`} className="card mb-3 block transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md" key={task.id}><div className="flex justify-between gap-3"><div><span className="text-[10px] font-black uppercase tracking-widest text-emerald-700">{task.status.replaceAll("_", " ")}</span><h3 className="mt-2 font-bold">{task.title}</h3><p className="mt-1 line-clamp-2 text-sm text-slate-500">{task.description}</p></div><span className="whitespace-nowrap text-sm font-black text-emerald-700">?{task.budget}</span></div><div className="mt-4 flex justify-between text-xs font-medium text-slate-400"><span>{task.location || t("remote")}</span><span>{task.deadline ? `${t("due")} ${new Date(task.deadline).toLocaleDateString()}` : t("flexible")}</span></div></Link>)}{!data.tasks.length && <EmptyState>{t("noTasks")}</EmptyState>}</section>
      <section><div className="mb-3"><p className="text-xs font-bold uppercase tracking-widest text-slate-400">{t("momentum")}</p><h2 className="mt-1 text-xl font-black">{t("activeAssignments")}</h2></div>{data.assignments.slice(0, 4).map((item) => { const levels = item.levels || []; const isCompleted = item.task_status === "COMPLETED"; return <Link to="/assignments" className="card mb-3 block" key={item.id}><div className="flex justify-between gap-3"><div><h3 className="font-bold">{item.task_title}</h3><p className={`mt-1 text-xs font-semibold ${isCompleted ? "text-emerald-700" : "text-slate-500"}`}>{isCompleted ? "Assignment completed" : item.task_status?.replaceAll("_", " ") || t("inProgress")}</p></div><span className="rounded-full bg-blue-50 px-2.5 py-1 text-xs font-black text-brand">{item.progress}%</span></div><div className="mt-3 h-2 rounded-full bg-slate-100"><div className="h-2 rounded-full bg-brand transition-all" style={{ width: `${item.progress}%` }} /></div>{levels.length > 0 && <ol className="mt-4 space-y-2">{levels.map((level) => { const approved = level.status === "COMPLETED"; const pending = level.status === "SUBMITTED"; const unlocked = level.status === "CURRENT"; const label = approved ? "Approved" : pending ? "Pending Client Approval" : unlocked ? "Unlocked" : "Locked"; const icon = approved ? "?" : pending ? "?" : unlocked ? "?" : "??"; const tone = approved ? "text-emerald-700" : pending ? "text-amber-700" : unlocked ? "text-blue-700" : "text-slate-500"; return <WorkerDashboardLevel level={level} key={level.id} />; })}</ol>}</Link>; })}{!data.assignments.length && <EmptyState>{t("noAssignments")}</EmptyState>}</section>
    </div>
  </div>;
}
function WorkerDashboardLevel({ level }) {
  const approved = level.status === "COMPLETED";
  const pending = level.status === "SUBMITTED";
  const unlocked = level.status === "CURRENT";
  const label = approved ? "Approved" : pending ? "Pending Client Approval" : unlocked ? "Unlocked" : "Locked";
  const blocker = level.status === "LOCKED" ? `Complete and get Level ${level.order - 1} approved by the client to unlock this level.` : pending ? "Waiting for the client to approve this level before the next level unlocks." : "";
  const tone = approved ? "text-emerald-700" : pending ? "text-amber-700" : unlocked ? "text-blue-700" : "text-slate-500";
  const icon = approved ? "?" : pending ? "?" : unlocked ? "?" : "??";
  return <li className={`rounded-lg bg-slate-50 p-3 text-sm ${tone}`}>
    <div className="flex items-center justify-between gap-3"><span><span aria-hidden="true" className="mr-2">{icon}</span><strong>Level {level.order} ? {level.title}</strong></span><span className="shrink-0 text-xs font-semibold">{label}</span></div>
    <p className="mt-2 whitespace-pre-wrap text-slate-700">{level.description || "The client has not provided a task description for this level yet."}</p>
    {level.tasks?.length > 0 && <ol className="mt-2 list-decimal space-y-1 pl-5 text-slate-600">{level.tasks.map((task) => <li key={task.id}>{task.title}</li>)}</ol>}
    {level.deliverables && <p className="mt-2 text-xs"><strong>Deliverables:</strong> {level.deliverables}</p>}
    {level.required_materials && <p className="mt-1 text-xs"><strong>Files or data needed:</strong> {level.required_materials}</p>}
    {level.requirements && <p className="mt-1 text-xs"><strong>Submission requirements:</strong> {level.requirements}</p>}
    {blocker && <p className="mt-2 text-xs font-semibold">{blocker}</p>}
  </li>;
}
