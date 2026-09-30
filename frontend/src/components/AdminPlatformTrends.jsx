import { useEffect, useState } from "react";
import { get } from "../services/api";
import { ErrorMessage } from "./StatusMessage";

const ranges = [["7d", "Last 7 days"], ["30d", "Last 30 days"], ["3m", "Last 3 months"], ["6m", "Last 6 months"], ["1y", "Last 1 year"]];
const number = (value) => Number(value || 0).toLocaleString();

export default function AdminPlatformTrends({ initialData }) {
  const [range, setRange] = useState("30d");
  const [data, setData] = useState(initialData || null);
  const [loading, setLoading] = useState(!initialData);
  const [error, setError] = useState("");

  useEffect(() => {
    let alive = true;
    if (range === "30d" && initialData) {
      setData(initialData);
      setError("");
      setLoading(false);
      return () => { alive = false; };
    }
    setLoading(true);
    get(`/analytics/summary/?range=${range}`).then((result) => {
      if (alive) { setData(result); setError(""); }
    }).catch((err) => { if (alive) setError(err.message); })
      .finally(() => { if (alive) setLoading(false); });
    return () => { alive = false; };
  }, [range, initialData]);

  return <section className="card space-y-6" aria-labelledby="platform-trends-title">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div><p className="text-xs font-black uppercase tracking-widest text-brand">Platform insights</p><h2 id="platform-trends-title" className="mt-1 text-2xl font-black">Platform trends</h2><p className="mt-1 text-sm text-slate-500">Growth, marketplace activity and verified transaction volume.</p></div>
      <label className="text-sm font-semibold text-slate-600">Time period<select className="field min-w-44" value={range} onChange={(event) => setRange(event.target.value)}>{ranges.map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select></label>
    </div>
    <ErrorMessage message={error} />
    {loading && <div className="rounded-xl bg-slate-50 p-8 text-center text-sm text-slate-500" role="status">Loading platform trends…</div>}
    {!loading && data && <>
      <div className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">{[
        ["Total users", data.users.total, data.users.new.users], ["Workers", data.users.workers, data.users.new.workers], ["Clients", data.users.clients, data.users.new.clients], ["Total tasks", data.tasks.total, null], ["Completed tasks", data.assignments.completed, null], ["Applications", data.applications.total, null], ["Transactions", data.transactions.total, null], ["Completed transactions", data.transactions.verified, null],
      ].map(([label, value, change]) => <div key={label} className="rounded-xl border border-slate-100 bg-slate-50/70 p-4"><p className="text-xs font-semibold text-slate-500">{label}</p><p className="mt-1 text-2xl font-black text-slate-900">{number(value)}</p>{change && <p className={`mt-1 text-xs font-bold ${change.change_percent >= 0 ? "text-emerald-700" : "text-rose-700"}`}>{change.change_percent >= 0 ? "↑" : "↓"} {Math.abs(change.change_percent)}% vs previous period <span className="font-normal text-slate-400">({number(change.current)} new)</span></p>}</div>)}</div>
      <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-4">{[
        ["Active tasks", (data.tasks.by_status.OPEN || 0) + (data.tasks.by_status.APPLICATIONS_RECEIVED || 0) + (data.tasks.by_status.ASSIGNED || 0) + (data.tasks.by_status.IN_PROGRESS || 0) + (data.tasks.by_status.SUBMITTED || 0)],
        ["Cancelled tasks", data.tasks.by_status.CANCELLED || 0], ["Accepted applications", data.applications.period_accepted], ["Pending transactions", data.transactions.pending],
      ].map(([label, value]) => <div key={label} className="rounded-lg bg-blue-50/60 px-3 py-2"><span className="text-xs text-slate-500">{label}</span><span className="float-right font-bold text-slate-800">{number(value)}</span></div>)}</div>
      <div className="grid gap-4 xl:grid-cols-2">
        <Chart title="User growth" subtitle="New accounts per day" series={[{ name: "Users", color: "#3657d6", data: data.users.growth.users }, { name: "Workers", color: "#10b981", data: data.users.growth.workers }, { name: "Clients", color: "#f59e0b", data: data.users.growth.clients }]} />
        <Chart title="Tasks posted and completed" subtitle={`Completion rate ${data.tasks.completion_rate}%`} series={[{ name: "Posted", color: "#3657d6", data: data.tasks.trend.map((item) => ({ ...item, count: item.posted })) }, { name: "Completed", color: "#10b981", data: data.tasks.trend.map((item) => ({ ...item, count: item.completed })) }]} />
        <Chart title="Applications" subtitle={`${number(data.applications.period_accepted)} accepted · ${number(data.applications.period_pending)} pending · ${number(data.applications.period_rejected)} rejected · ${data.applications.acceptance_rate}% acceptance`} series={[{ name: "Applications", color: "#8b5cf6", data: data.applications.trend }]} />
        <Chart title="Verified transaction volume" subtitle={`₹${number(data.transactions.period_amount)} in selected period · ${number(data.transactions.pending)} pending overall`} series={[{ name: "Amount (₹)", color: "#0d9488", data: data.transactions.trend.map((item) => ({ date: item.date, count: Number(item.amount) })) }]} />
      </div>
      <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-5">{[["Active users", data.activity.active_users], ["Completed assignments", data.activity.completed_assignments], ["Reviews submitted", data.activity.reviews], ["Complaints / reports", data.activity.complaints], ["Fraud alerts", data.activity.fraud_alerts]].map(([label, value]) => <div className="rounded-xl border border-slate-100 p-3" key={label}><p className="text-xs text-slate-500">{label}</p><p className="mt-1 text-xl font-bold">{number(value)}</p></div>)}</div>
    </>}
    {!loading && !data && !error && <div className="rounded-xl bg-slate-50 p-8 text-center text-sm text-slate-500">No analytics data is available for this period yet.</div>}
  </section>;
}

function Chart({ title, subtitle, series }) {
  const width = 600, height = 190, left = 34, right = 10, top = 12, bottom = 27;
  const values = series.flatMap((item) => item.data.map((point) => Number(point.count || 0)));
  const max = Math.max(1, ...values);
  const pointCount = Math.max(1, ...series.map((item) => item.data.length));
  const x = (index) => left + (pointCount < 2 ? 0 : index * (width - left - right) / (pointCount - 1));
  const y = (value) => height - bottom - (value / max) * (height - top - bottom);
  const hasData = values.some((value) => value > 0);
  return <div className="rounded-xl border border-slate-200 p-4"><div className="flex flex-wrap items-start justify-between gap-2"><div><h3 className="font-bold">{title}</h3><p className="mt-1 text-xs text-slate-500">{subtitle}</p></div><div className="flex flex-wrap gap-x-3 gap-y-1">{series.map((item) => <span className="flex items-center gap-1 text-[11px] text-slate-500" key={item.name}><i className="h-2 w-2 rounded-full" style={{ background: item.color }} />{item.name}</span>)}</div></div>
    {!hasData ? <div className="flex h-48 items-center justify-center text-sm text-slate-400">No activity in this period.</div> : <div className="mt-3 w-full overflow-hidden"><svg viewBox={`0 0 ${width} ${height}`} role="img" aria-label={`${title} chart`} className="w-full"><line x1={left} y1={height - bottom} x2={width - right} y2={height - bottom} stroke="#e2e8f0" />{series.map((item) => { const points = item.data.map((point, index) => `${x(index)},${y(Number(point.count || 0))}`).join(" "); return <g key={item.name}><polyline points={points} fill="none" stroke={item.color} strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />{item.data.map((point, index) => <circle key={point.date} cx={x(index)} cy={y(Number(point.count || 0))} r={pointCount > 60 ? 1.5 : 3} fill={item.color}><title>{point.date}: {number(point.count)}</title></circle>)}</g>; })}<text x={left} y={height - 6} fill="#94a3b8" fontSize="10">{series[0]?.data[0]?.date || ""}</text><text x={width - right} y={height - 6} textAnchor="end" fill="#94a3b8" fontSize="10">{series[0]?.data.at(-1)?.date || ""}</text></svg></div>}
  </div>;
}
