import { useEffect, useState } from "react";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { get } from "../services/api";

export default function SkillGraphPage() {
  const [graph, setGraph] = useState({ nodes: [], edges: [] });
  const [error, setError] = useState("");

  useEffect(() => {
    get("/skills/graph/").then(setGraph).catch((err) => setError(err.message));
  }, []);

  const popular = [...graph.nodes].sort((a, b) => b.worker_count - a.worker_count || a.name.localeCompare(b.name));
  return <div className="space-y-6">
    <div><p className="text-sm font-semibold text-brand">Advanced discovery</p><h1 className="mt-1 text-3xl font-black">Skill Graph</h1><p className="mt-2 text-slate-500">Skills are connected when workers list them together. Edge weight shows the number of workers sharing that pair.</p></div>
    <ErrorMessage message={error} />
    {popular.length ? <div className="grid gap-4 lg:grid-cols-2"><div className="card"><h2 className="font-bold">Skill nodes</h2><div className="mt-4 space-y-3">{popular.map((skill) => <div className="flex items-center justify-between rounded-xl bg-slate-50 px-4 py-3" key={skill.id}><div><p className="font-semibold">{skill.name}</p><p className="text-xs text-slate-500">{skill.category || "Uncategorized"}</p></div><span className="text-sm font-bold text-brand">{skill.worker_count} worker{skill.worker_count === 1 ? "" : "s"}</span></div>)}</div></div><div className="card"><h2 className="font-bold">Related skill pairs</h2>{graph.edges.length ? <div className="mt-4 space-y-3">{graph.edges.map((edge) => { const source = graph.nodes.find((node) => node.id === edge.source); const target = graph.nodes.find((node) => node.id === edge.target); return <div className="flex items-center justify-between rounded-xl border border-slate-100 px-4 py-3" key={`${edge.source}-${edge.target}`}><span className="text-sm font-semibold">{source?.name} <span className="text-slate-400">↔</span> {target?.name}</span><span className="text-sm font-bold text-emerald-700">{edge.weight} shared</span></div>; })}</div> : <p className="mt-4 text-sm text-slate-500">Add multiple skills to worker profiles to create connections.</p>}</div></div> : <EmptyState>No active skills are available for the graph yet.</EmptyState>}
  </div>;
}
