import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { get } from "../services/api";

export default function ClientDashboard({ user, data }) {
  const [recommendedTask, setRecommendedTask] = useState("");
  const [workers, setWorkers] = useState([]);
  const [workerError, setWorkerError] = useState("");
  const [loadingWorkers, setLoadingWorkers] = useState(false);
  const employer = data.employer;
  const tasks = data.tasks || [];
  const assignments = data.assignments || [];
  const notifications = data.notifications || [];
  const applications = data.applications || [];
  const reviews = data.reviews || [];
  const active = employer?.active_jobs || [];
  const completed = employer?.completed_jobs || [];
  const payments = employer?.payment_history || [];
  const receivedReviews = reviews.filter((review) => review.reviewed_user_email === user.email);
  const averageRating = receivedReviews.length
    ? (receivedReviews.reduce((sum, review) => sum + Number(review.rating), 0) / receivedReviews.length).toFixed(1)
    : "No ratings";
  const ongoing = assignments.filter((item) => item.task_status === "IN_PROGRESS").length;
  const portal = (path) => `/client${path}`;

  useEffect(() => {
    if (!recommendedTask) { setWorkers([]); return; }
    let current = true;
    setLoadingWorkers(true);
    setWorkerError("");
    get(`/recommendations/workers/?task=${recommendedTask}`).then((items) => {
      if (current) setWorkers(items);
    }).catch((err) => {
      if (current) { setWorkers([]); setWorkerError(err.message); }
    }).finally(() => { if (current) setLoadingWorkers(false); });
    return () => { current = false; };
  }, [recommendedTask]);

  const metrics = [
    ["Active jobs", active.length], ["Applications", employer?.application_count ?? applications.length],
    ["Selected workers", employer?.selected_worker_count ?? 0], ["Ongoing tasks", ongoing],
    ["Completed jobs", completed.length], ["Pending payments", `₹${Number(employer?.summary?.pending_payments || 0).toLocaleString("en-IN")}`],
    ["Total paid", `₹${Number(employer?.summary?.total_earnings || 0).toLocaleString("en-IN")}`],
    ["Average rating", averageRating], ["Verification", employer?.verification?.status || "UNVERIFIED"],
  ];

  return <div className="space-y-7">
    <section className="hero-panel"><div className="relative z-10 max-w-2xl"><p className="text-sm font-bold text-blue-100">Client and employer workspace</p><h1 className="mt-2 text-3xl font-black text-white sm:text-4xl">Good to see you, {user.first_name || user.email.split("@")[0]}.</h1><p className="mt-3 max-w-xl text-sm leading-6 text-blue-100">Post work, review applicants, and keep assignments and payments moving.</p><div className="mt-6 flex flex-wrap gap-3"><Link className="rounded-lg bg-white px-4 py-2.5 text-sm font-bold text-brand" to={portal("/tasks?create=1")}>Post a job</Link><Link className="rounded-lg border border-white/40 px-4 py-2.5 text-sm font-bold text-white" to={portal("/applications")}>View applications</Link><Link className="rounded-lg border border-white/40 px-4 py-2.5 text-sm font-bold text-white" to={portal("/verification")}>Verification</Link></div></div></section>
    <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-3">{metrics.map(([label, value]) => <article className="metric-card metric-blue" key={label}><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 break-words text-2xl font-black">{value}</p></article>)}</div>
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="card"><div className="mb-4 flex items-center justify-between gap-3"><div><h2 className="text-lg font-bold">Recent jobs</h2><p className="text-sm text-slate-500">Your currently active postings</p></div><Link to="/tasks" className="text-sm font-bold text-brand">Manage jobs</Link></div>{active.length ? <div className="divide-y divide-slate-100">{active.slice(0, 5).map((job) => <Link className="flex items-center justify-between gap-3 py-3 first:pt-0" to={`/tasks/${job.id}`} key={job.id}><span><span className="block font-semibold">{job.title}</span><span className="mt-1 block text-xs text-slate-500">{job.status.replaceAll("_", " ")} · {job.applications} applications</span></span><span className="text-brand" aria-hidden="true">→</span></Link>)}</div> : <EmptyState>No active jobs yet.</EmptyState>}</section>
      <section className="card"><div className="mb-4 flex items-center justify-between gap-3"><div><h2 className="text-lg font-bold">Recent applications</h2><p className="text-sm text-slate-500">Latest applicants across your jobs</p></div><Link to="/applications" className="text-sm font-bold text-brand">Review all</Link></div>{applications.length ? <div className="divide-y divide-slate-100">{applications.slice(0, 5).map((application) => <Link className="flex items-center justify-between gap-3 py-3 first:pt-0" to={`/applications?task=${application.task}`} key={application.id}><span><span className="block font-semibold">{application.worker_email}</span><span className="mt-1 block text-xs text-slate-500">{application.task_title} · {application.status.replaceAll("_", " ")}</span></span><span className="text-brand" aria-hidden="true">→</span></Link>)}</div> : <EmptyState>No applications received yet.</EmptyState>}</section>
    </div>
    <section className="card space-y-4"><div><h2 className="text-lg font-bold">AI recommended workers</h2><p className="mt-1 text-sm text-slate-500">Scores and explanations come from WorkNeuron’s existing worker-task matching API.</p></div>{tasks.length ? <label className="block max-w-xl text-sm font-semibold text-slate-600">Choose a job<select className="field" value={recommendedTask} onChange={(event) => setRecommendedTask(event.target.value)}><option value="">Select one of your jobs</option>{tasks.map((task) => <option value={task.id} key={task.id}>{task.title}</option>)}</select></label> : <EmptyState>Create a job before requesting worker recommendations.</EmptyState>}<ErrorMessage message={workerError} />{loadingWorkers ? <p role="status" className="text-sm text-slate-500">Loading recommended workers...</p> : workers.length ? <div className="grid gap-3 md:grid-cols-2">{workers.slice(0, 4).map((item) => <article className="rounded-lg border border-slate-200 p-4" key={item.worker.id}><div className="flex items-start justify-between gap-3"><div><h3 className="font-bold">{[item.worker.first_name, item.worker.last_name].filter(Boolean).join(" ") || "WorkNeuron worker"}</h3><p className="mt-1 text-sm text-slate-500">{item.worker.email}</p></div><span className="rounded-md bg-blue-50 px-2.5 py-1 text-sm font-black text-blue-800">AI match {Math.round(item.match.overall_score)}%</span></div><p className="mt-3 text-sm text-slate-600">{item.match.explanation}</p></article>)}</div> : recommendedTask ? <EmptyState>No worker matches were returned for this job.</EmptyState> : null}</section>
    <div className="grid gap-6 xl:grid-cols-2">
      <section className="card"><div className="mb-4 flex items-center justify-between"><div><h2 className="text-lg font-bold">Active tasks</h2><p className="text-sm text-slate-500">Assignments and current status</p></div><Link to="/assignments" className="text-sm font-bold text-brand">Track tasks</Link></div>{assignments.filter((item) => !["COMPLETED", "CANCELLED"].includes(item.task_status)).length ? <div className="divide-y divide-slate-100">{assignments.filter((item) => !["COMPLETED", "CANCELLED"].includes(item.task_status)).slice(0, 5).map((item) => <Link className="flex items-center justify-between gap-3 py-3 first:pt-0" to="/assignments" key={item.id}><span className="font-semibold">{item.task_title}</span><span className="text-xs font-bold text-slate-500">{item.task_status.replaceAll("_", " ")} · {item.progress}%</span></Link>)}</div> : <EmptyState>No active assignments.</EmptyState>}</section>
      <section className="card"><div className="mb-4 flex items-center justify-between"><div><h2 className="text-lg font-bold">Recent payments</h2><p className="text-sm text-slate-500">Transaction status from the payment ledger</p></div><Link to="/payments" className="text-sm font-bold text-brand">Payment history</Link></div>{payments.length ? <div className="divide-y divide-slate-100">{payments.slice(0, 5).map((payment) => <div className="flex items-center justify-between gap-3 py-3 first:pt-0" key={payment.id}><span><span className="block font-semibold">{payment.assignment_title}</span><span className="mt-1 block text-xs text-slate-500">{new Date(payment.created_at).toLocaleDateString()}</span></span><span className="text-right"><span className="block font-bold">₹{Number(payment.amount).toLocaleString("en-IN")}</span><span className="text-xs text-slate-500">{payment.status}</span></span></div>)}</div> : <EmptyState>No payment transactions yet.</EmptyState>}</section>
    </div>
    <section className="card"><div className="mb-4 flex items-center justify-between"><div><h2 className="text-lg font-bold">Notifications</h2><p className="text-sm text-slate-500">Unread updates for your account</p></div><Link to="/notifications" className="text-sm font-bold text-brand">View notifications</Link></div>{notifications.length ? <div className="divide-y divide-slate-100">{notifications.slice(0, 5).map((item) => <div className="py-3 first:pt-0" key={item.id}><p className="font-semibold">{item.title}</p><p className="mt-1 text-sm text-slate-500">{item.message}</p></div>)}</div> : <EmptyState>You are up to date.</EmptyState>}</section>
  </div>;
}
