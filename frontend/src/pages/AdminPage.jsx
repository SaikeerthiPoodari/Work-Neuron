import { useEffect, useState } from "react";
import { get, patch, post } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import AdminPlatformTrends from "../components/AdminPlatformTrends";

export default function AdminPage() {
  const [summary, setSummary] = useState(null);
  const [users, setUsers] = useState([]);
  const [verifications, setVerifications] = useState([]);
  const [reports, setReports] = useState([]);
  const [auditEvents, setAuditEvents] = useState([]);
  const [userSearch, setUserSearch] = useState("");
  const [userRole, setUserRole] = useState("");
  const [userActive, setUserActive] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);

  const load = async () => {
    const userParams = new URLSearchParams();
    if (userSearch.trim()) userParams.set("search", userSearch.trim());
    if (userRole) userParams.set("role", userRole);
    if (userActive) userParams.set("active", userActive);
    const results = await Promise.allSettled([
      get("/analytics/summary/"),
      get(`/admin/users/${userParams.toString() ? `?${userParams}` : ""}`),
      get("/admin/verifications/?status=PENDING"),
      get("/complaints/?category=JOB_REPORT"),
      get("/admin/audit-events/"),
    ]);
    const [stats, people, queue, jobReports, audit] = results;
    const failures = [];
    if (stats.status === "fulfilled") setSummary(stats.value); else failures.push(stats.reason.message);
    if (people.status === "fulfilled") setUsers(people.value); else failures.push(people.reason.message);
    if (queue.status === "fulfilled") setVerifications(queue.value); else failures.push(queue.reason.message);
    if (jobReports.status === "fulfilled") setReports(jobReports.value); else failures.push(jobReports.reason.message);
    if (audit.status === "fulfilled") setAuditEvents(audit.value); else failures.push(audit.reason.message);
    setError(failures.join(" "));
    setLoading(false);
  };

  useEffect(() => { load(); }, []);

  const review = async (id, action) => {
    try {
      await post(`/admin/verifications/${id}/action/`, {
        action,
        admin_notes: action === "approve" ? "Verification details reviewed." : "Please review the submitted details and contact support if needed.",
      });
      load();
    } catch (err) { setError(err.message); }
  };

  const updateReport = async (id, status) => {
    try {
      await patch(`/complaints/${id}/`, {
        status,
        resolution_notes: status === "RESOLVED" ? "Reviewed by moderation." : "Report dismissed after review.",
      });
      load();
    } catch (err) { setError(err.message); }
  };

  const updateUser = async (person) => {
    try {
      await patch(`/admin/users/${person.id}/`, { is_active: !person.is_active });
      await load();
    } catch (err) { setError(err.message); }
  };

  if (loading) return <div className="py-10 text-slate-500">Loading admin monitor...</div>;

  return <div className="space-y-8">
    <div><p className="text-sm font-semibold text-brand">Administration</p><h1 className="mt-1 text-3xl font-black">Platform monitor</h1><p className="mt-2 text-slate-500">Review trust signals, reports and marketplace activity.</p></div>
    <ErrorMessage message={error} />
    <AdminPlatformTrends initialData={summary} />
    {summary ? <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-5">
      <Metric label="Users" value={summary.users.total} />
      <Metric label="Open tasks" value={summary.tasks.by_status.OPEN || 0} />
      <Metric label="Verified amount" value={`₹${summary.transactions.verified_amount}`} />
      <Metric label="Fraud alerts" value={summary.fraud_alerts.open} />
      <Metric label="Job reports" value={reports.length} />
    </div> : <div className="grid gap-4 sm:grid-cols-2"><Metric label="Job reports" value={reports.length} /></div>}
    <section className="card">
      <QueueHeader title="Pending employer verification" count={verifications.length} />
      {verifications.length ? <div className="mt-4 space-y-3">{verifications.map((item) => <div className="rounded-2xl border border-slate-200 p-4" key={item.id}><div className="flex flex-col justify-between gap-3 sm:flex-row"><div><h3 className="font-bold">{item.business_name || item.legal_name}</h3><p className="mt-1 text-sm text-slate-500">{item.employer_email} · {item.employer_type.replaceAll("_", " ")}</p><p className="mt-2 text-sm text-slate-600">{item.business_address}</p></div><div className="flex gap-2"><button className="button-primary text-xs" onClick={() => review(item.id, "approve")}>Approve</button><button className="button-secondary text-xs" onClick={() => review(item.id, "reject")}>Reject</button><button className="button-secondary text-xs" onClick={() => review(item.id, "suspend")}>Suspend</button></div></div></div>)}</div> : <EmptyState>No pending verification requests.</EmptyState>}
    </section>
    <section className="card">
      <QueueHeader title="Recent admin activity" count={auditEvents.length} />
      {auditEvents.length ? <div className="mt-4 divide-y divide-slate-100">{auditEvents.slice(0, 10).map((event) => <div className="py-3" key={event.id}><div className="flex flex-wrap justify-between gap-2"><p className="font-semibold">{event.action.replaceAll("_", " ")}</p><time className="text-xs text-slate-400">{new Date(event.created_at).toLocaleString()}</time></div><p className="mt-1 text-sm text-slate-500">{event.actor_email} · {event.target_type} #{event.target_id}</p></div>)}</div> : <EmptyState>No admin activity recorded yet.</EmptyState>}
    </section>
    <section className="card">
      <QueueHeader title="Reported jobs" count={reports.length} />
      {reports.length ? <div className="mt-4 space-y-3">{reports.map((report) => <div className="rounded-2xl border border-amber-200 bg-amber-50 p-4" key={report.id}><div className="flex flex-wrap justify-between gap-2"><div><p className="font-bold">Job #{report.task} · {report.category}</p><p className="mt-1 text-sm text-slate-700">{report.description}</p><p className="mt-1 text-xs text-slate-500">Reported by {report.complainant_email}</p></div><span className="text-xs font-black uppercase text-amber-800">{report.status}</span></div>{report.status !== "RESOLVED" && report.status !== "DISMISSED" && <div className="mt-3 flex gap-2"><button className="button-primary text-xs" onClick={() => updateReport(report.id, "RESOLVED")}>Resolve</button><button className="button-secondary text-xs" onClick={() => updateReport(report.id, "DISMISSED")}>Dismiss</button></div>}</div>)}</div> : <EmptyState>No reported jobs.</EmptyState>}
    </section>
    <section className="card">
      <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end"><div><h2 className="text-lg font-bold">Users</h2><p className="mt-1 text-sm text-slate-500">Search accounts and manage access without leaving the control center.</p></div><div className="flex flex-wrap gap-2"><label className="sr-only" htmlFor="admin-user-search">Search users</label><input id="admin-user-search" className="field mt-0 min-w-52" placeholder="Search email or name" value={userSearch} onChange={(event) => setUserSearch(event.target.value)} /><select className="field mt-0" value={userRole} onChange={(event) => setUserRole(event.target.value)} aria-label="Filter by role"><option value="">All roles</option><option value="WORKER">Workers</option><option value="CLIENT">Clients</option><option value="ADMIN">Admins</option></select><select className="field mt-0" value={userActive} onChange={(event) => setUserActive(event.target.value)} aria-label="Filter by account status"><option value="">All status</option><option value="true">Active</option><option value="false">Inactive</option></select><button className="button-secondary" onClick={load}>Filter</button></div></div>
      {users.length ? <div className="mt-4 divide-y divide-slate-100">{users.map((person) => <div className="flex flex-col justify-between gap-3 py-3 sm:flex-row sm:items-center" key={person.id}><div><p className="font-semibold">{person.email}</p><p className="text-xs text-slate-500">{person.role} · joined {new Date(person.date_joined).toLocaleDateString()}</p></div><div className="flex items-center gap-2"><span className={`rounded-full px-2.5 py-1 text-xs font-bold ${person.is_active ? "bg-emerald-50 text-emerald-700" : "bg-red-50 text-red-700"}`}>{person.is_active ? "Active" : "Inactive"}</span><button className="button-secondary text-xs" onClick={() => updateUser(person)}>{person.is_active ? "Deactivate" : "Reactivate"}</button></div></div>)}</div> : <EmptyState>No users found.</EmptyState>}
    </section>
  </div>;
}

function QueueHeader({ title, count }) { return <div className="flex items-center justify-between"><div><p className="text-xs font-black uppercase tracking-widest text-slate-400">Trust and safety</p><h2 className="mt-1 text-lg font-bold">{title}</h2></div><span className="rounded-full bg-amber-50 px-3 py-1 text-xs font-black text-amber-700">{count}</span></div>; }
function Metric({ label, value }) { return <div className="card"><p className="text-sm text-slate-500">{label}</p><p className="mt-2 text-2xl font-black">{value}</p></div>; }
