import { useEffect, useState } from "react";
import { Link, useParams } from "react-router-dom";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { get } from "../services/api";

export default function TaskDecompositionPage() {
  const { id } = useParams();
  const [data, setData] = useState(null);
  const [error, setError] = useState("");
  useEffect(() => { get(`/tasks/${id}/decomposition/`).then(setData).catch((err) => setError(err.message)); }, [id]);
  return <div className="space-y-6"><Link className="text-sm font-semibold text-brand" to={`/tasks/${id}`}>← Back to task</Link><div><p className="text-sm font-semibold text-brand">Explainable AI assistance</p><h1 className="mt-1 text-3xl font-black">Task decomposition</h1><p className="mt-2 text-slate-500">The description is split into actionable sentences and matched against required catalog skills.</p></div><ErrorMessage message={error} />{data?.steps?.length ? <div className="space-y-3">{data.steps.map((step) => <div className="card" key={step.order}><div className="flex gap-4"><span className="flex h-8 w-8 shrink-0 items-center justify-center rounded-full bg-blue-50 text-sm font-black text-brand">{step.order}</span><div><p className="font-semibold text-slate-800">{step.description}</p><div className="mt-3 flex flex-wrap gap-2">{step.matched_skills.length ? step.matched_skills.map((skill) => <span className="rounded-full bg-mint px-3 py-1 text-xs font-bold text-emerald-800" key={skill.id}>{skill.name}</span>) : <span className="text-xs text-slate-400">No direct required-skill phrase detected</span>}</div></div></div></div>)}<p className="text-xs text-slate-400">Method: {data.method}</p></div> : data && <EmptyState>No actionable sentences were detected.</EmptyState>}</div>;
}
