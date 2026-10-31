import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { get, post } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { useI18n } from "../i18n/I18nContext";

async function requestRefund(payment, load, setError) {
  if (!window.confirm(`Refund ${payment.currency} ${payment.amount} for ${payment.assignment_title}?`)) return;
  try { await post(`/payments/${payment.id}/refund/`); await load(); } catch (err) { setError(err.message); }
}

export default function PaymentsPage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const worker = user.role === "WORKER";
  const [payments, setPayments] = useState([]);
  const [assignments, setAssignments] = useState([]);
  const [dashboard, setDashboard] = useState(null);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [range, setRange] = useState("all");
  const [analytics, setAnalytics] = useState(null);
  const [analyticsRange, setAnalyticsRange] = useState("6m");

  const load = async () => {
    setLoading(true); setError("");
    try {
      const [transactions, allAssignments] = await Promise.all([get("/payments/"), get("/assignments/")]);
      setPayments(transactions); setAssignments(allAssignments.filter((item) => ["ASSIGNED", "IN_PROGRESS", "SUBMITTED", "COMPLETED"].includes(item.task_status)));
      if (worker) setAnalytics(await get(`/payments/analytics/?range=${analyticsRange}`));
      if (user.role === "CLIENT") setDashboard(await get("/payments/employer-dashboard/"));
    } catch (err) { setError(err.message); } finally { setLoading(false); }
  };
  useEffect(() => { load(); }, [user.role, analyticsRange]);

  const workerEarnings = payments.reduce((sum, payment) => payment.status === "VERIFIED" ? sum + Number(payment.amount) : sum, 0);
  const pendingEarnings = payments.reduce((sum, payment) => payment.status === "CREATED" ? sum + Number(payment.amount) : sum, 0);
  const withinDays = (days) => payments.reduce((sum, payment) => payment.status === "VERIFIED" && (Date.now() - new Date(payment.created_at).getTime()) <= days * 86400000 ? sum + Number(payment.amount) : sum, 0);
  const visiblePayments = payments.filter((payment) => (statusFilter === "ALL" || payment.status === statusFilter) && (range === "all" || Date.now() - new Date(payment.created_at).getTime() <= (range === "week" ? 7 : 30) * 86400000));

  const createOrder = async (assignment) => {
    try {
      const data = await post("/payments/create-order/", { assignment: assignment.id });
      if (window.Razorpay && data.order) {
        const checkout = new window.Razorpay({ key: data.key_id, amount: data.order.amount, currency: data.order.currency, name: "WorkNeuron", description: assignment.task_title, order_id: data.order.id, handler: async (response) => { try { await post("/payments/verify/", { transaction_id: data.transaction.id, razorpay_order_id: response.razorpay_order_id, razorpay_payment_id: response.razorpay_payment_id, razorpay_signature: response.razorpay_signature }); await load(); } catch (err) { setError(err.message); } } });
        checkout.open();
      } else { setError("Razorpay checkout is unavailable. The TEST MODE order was created."); await load(); }
    } catch (err) { setError(err.message); }
  };

  return <div className="space-y-6">
    <header><p className="text-sm font-semibold text-brand">{worker ? t("payments") : "Secure checkout"}</p><h1 className="mt-1 text-3xl font-black tracking-tight">{worker ? t("paymentsEarnings") : "Payments"}</h1><p className="mt-2 text-slate-500">{worker ? t("earningsIntro") : "Razorpay integration is restricted to TEST MODE."}</p></header>
    <ErrorMessage message={error} />
    {worker && <section><h2 className="mb-3 text-xl font-black">{t("paymentsEarnings")}</h2><div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><Metric label={t("verifiedTotal")} value={`₹${workerEarnings.toFixed(2)}`} /><Metric label={t("pendingPayments")} value={`₹${pendingEarnings.toFixed(2)}`} /><Metric label={t("last7Days")} value={`₹${withinDays(7).toFixed(2)}`} /><Metric label={t("last30Days")} value={`₹${withinDays(30).toFixed(2)}`} /></div></section>}
    {worker && analytics && <PaymentAnalytics analytics={analytics} />}
    {worker && <label className="flex items-center gap-2 text-sm font-semibold text-slate-600">Analytics range<select className="field mt-0 w-auto" value={analyticsRange} onChange={(event) => setAnalyticsRange(event.target.value)}><option value="7d">Last 7 days</option><option value="30d">Last 30 days</option><option value="3m">Last 3 months</option><option value="6m">Last 6 months</option></select></label>}
    {dashboard && <EmployerSummary dashboard={dashboard} />}
    {user.role === "CLIENT" && assignments.map((assignment) => <div className="card flex flex-col justify-between gap-4 sm:flex-row sm:items-center" key={assignment.id}><div><h2 className="font-bold">{assignment.task_title}</h2><p className="mt-1 text-sm text-slate-500">Pay after work starts. Funds remain held until the worker and client confirm every level.</p></div><button className="button-primary" onClick={() => createOrder(assignment)}>Fund escrow in test mode</button></div>)}
    {worker && <div className="flex flex-wrap gap-2"><label><span className="sr-only">{t("filterStatus")}</span><select aria-label={t("filterStatus")} className="field mt-0 w-auto" value={statusFilter} onChange={(event) => setStatusFilter(event.target.value)}>{["ALL", "VERIFIED", "CREATED", "FAILED", "REFUNDED"].map((value) => <option key={value} value={value}>{value === "ALL" ? t("allStatuses") : value}</option>)}</select></label><label><span className="sr-only">{t("filterDate")}</span><select aria-label={t("filterDate")} className="field mt-0 w-auto" value={range} onChange={(event) => setRange(event.target.value)}><option value="all">{t("allDates")}</option><option value="week">{t("lastWeek")}</option><option value="month">{t("last30Days")}</option></select></label></div>}
    {loading ? <div className="card text-sm text-slate-500" role="status">{worker ? t("loadingPayments") : "Loading payments…"}</div> : visiblePayments.length ? <PaymentHistory payments={visiblePayments} worker={worker} user={user} load={load} setError={setError} t={t} /> : <EmptyState>{worker ? t("noTransactions") : "No transactions yet."}</EmptyState>}
  </div>;
}

function EmployerSummary({ dashboard }) { return <section><h2 className="mb-3 text-xl font-black">Employer financial overview</h2><div className="grid gap-4 sm:grid-cols-3"><Metric label="Verified earnings" value={`₹${dashboard.summary.total_earnings}`} /><Metric label="Completed-job earnings" value={`₹${dashboard.summary.completed_job_earnings}`} /><Metric label="Pending payments" value={`₹${dashboard.summary.pending_payments}`} /></div><div className="card mt-4"><h3 className="font-bold">Completed jobs</h3>{dashboard.completed_jobs.length ? <div className="mt-3 divide-y divide-slate-100">{dashboard.completed_jobs.map((job) => <div className="flex flex-wrap justify-between gap-2 py-3 text-sm" key={job.assignment_id}><span><b>{job.job_title}</b><span className="ml-2 text-slate-500">{job.worker}</span></span><span>₹{job.amount} · {job.completion_date ? new Date(job.completion_date).toLocaleDateString() : "Completed"}</span></div>)}</div> : <p className="mt-3 text-sm text-slate-500">No completed jobs yet.</p>}</div></section>; }

function PaymentHistory({ payments, worker, user, load, setError, t }) { return <div className="card"><h2 className="font-bold">{worker ? t("paymentHistory") : "Payment history"}</h2><div className="mt-4 divide-y divide-slate-100">{payments.map((payment) => <article className="py-4" key={payment.id}><div className="flex flex-wrap justify-between gap-2"><div><p className="font-bold">{payment.assignment_title}</p>{worker && <p className="mt-1 text-sm text-slate-500">{t("clientLabel")}: {payment.client_name || payment.client_email}</p>}</div><span className="font-black text-brand">{payment.currency} {payment.amount} · {payment.status}</span></div><div className="mt-2 flex flex-wrap items-center gap-x-4 gap-y-2 text-xs text-slate-500"><span>{t("transaction")} #{payment.id}</span><span>{payment.provider}</span>{payment.provider_payment_id && <span>Payment ID: {payment.provider_payment_id}</span>}<span>{new Date(payment.created_at).toLocaleString()}</span>{["CLIENT", "ADMIN"].includes(user.role) && payment.status === "VERIFIED" && <button className="button-secondary text-xs" onClick={() => requestRefund(payment, load, setError)}>{user.role === "ADMIN" ? "Refund payment" : "Request full refund"}</button>}</div></article>)}</div></div>; }

function Metric({ label, value }) { return <div className="metric-card"><p className="text-sm font-medium text-slate-500">{label}</p><p className="mt-2 text-2xl font-black">{value}</p></div>; }

function PaymentAnalytics({ analytics }) {
  const max = Math.max(...(analytics.monthly || []).map((row) => Number(row.amount)), 1);
  const verified = analytics.status_breakdown?.find((item) => item.status === "VERIFIED")?.count || 0; const pending = analytics.status_breakdown?.find((item) => item.status === "CREATED")?.count || 0; const total = Math.max(verified + pending, 1); const circumference = 2 * Math.PI * 42;
  return <section className="card space-y-4"><div className="flex flex-wrap items-end justify-between gap-3"><div><p className="text-xs font-black uppercase tracking-widest text-brand">Verified transaction records</p><h2 className="mt-1 text-xl font-black">Earnings analytics</h2></div><span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-brand">{analytics.range}</span></div><div className="grid gap-3 sm:grid-cols-3"><Metric label="Analytics total" value={`${analytics.currency} ${analytics.summary.total_earnings}`} /><Metric label="Pending" value={`${analytics.currency} ${analytics.summary.pending_payments}`} /><Metric label="Verified payments" value={analytics.summary.completed_payments} /></div><div className="grid gap-5 lg:grid-cols-[1fr_12rem]"><div><h3 className="text-sm font-bold">Monthly earnings</h3><div className="mt-3 flex min-h-36 items-end gap-3 border-b border-slate-200 px-2">{analytics.monthly?.length ? analytics.monthly.map((row) => <div className="flex flex-1 flex-col items-center gap-1" key={row.period}><span className="text-[10px] font-bold text-slate-500">{Number(row.amount).toLocaleString()}</span><div className="w-full max-w-10 rounded-t-lg bg-brand" style={{ height: `${Math.max(8, Number(row.amount) / max * 110)}px` }} title={`${row.period}: ${row.amount}`} /><span className="text-[10px] text-slate-400">{new Date(row.period).toLocaleDateString(undefined, { month: "short" })}</span></div>) : <p className="py-8 text-sm text-slate-500">No verified payments in this period.</p>}</div></div><div className="flex flex-col items-center justify-center"><h3 className="text-sm font-bold">Payment status</h3><div className="relative mt-3 h-28 w-28"><svg viewBox="0 0 100 100" className="h-full w-full -rotate-90"><circle cx="50" cy="50" r="42" fill="none" stroke="#f59e0b" strokeWidth="12" /><circle cx="50" cy="50" r="42" fill="none" stroke="#10b981" strokeWidth="12" strokeDasharray={`${verified / total * circumference} ${circumference}`} /></svg><span className="absolute inset-0 flex items-center justify-center text-lg font-black text-brand">{verified}</span></div><p className="mt-2 text-xs text-slate-500">{verified} verified · {pending} pending</p></div></div></section>;
}
