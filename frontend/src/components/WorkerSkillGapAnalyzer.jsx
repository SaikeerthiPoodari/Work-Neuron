import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../services/api";
import { EmptyState, ErrorMessage } from "./StatusMessage";

export default function WorkerSkillGapAnalyzer() {
  const [analysis, setAnalysis] = useState(null);
  const [category, setCategory] = useState("");
  const [task, setTask] = useState("");
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const load = async (nextCategory = category, nextTask = task) => {
    setLoading(true);
    const params = new URLSearchParams();
    if (nextCategory) params.set("category", nextCategory);
    if (nextTask) params.set("task", nextTask);
    try {
      const result = await get(`/recommendations/skill-gap/${params.size ? `?${params}` : ""}`);
      setAnalysis(result);
      setError("");
    } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };

  useEffect(() => { load("", ""); }, []);

  const updateCategory = (value) => { setCategory(value); setTask(""); load(value, ""); };
  const updateTask = (value) => { setTask(value); load(category, value); };

  return <section className="card space-y-5" aria-labelledby="skill-gap-title">
    <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-start">
      <div><p className="text-xs font-black uppercase tracking-widest text-brand">Career development</p><h2 id="skill-gap-title" className="mt-1 text-xl font-black">🧠 AI Skill Gap Analyzer</h2><p className="mt-1 text-sm text-slate-500">Compare your profile with skills listed in current WorkNeuron jobs.</p></div>
      <Link to="/skill-graph" className="text-sm font-bold text-brand hover:underline">Explore skill graph →</Link>
    </div>
    <ErrorMessage message={error} />
    <div className="grid gap-3 md:grid-cols-2">
      <label className="text-sm font-semibold text-slate-600">Target category
        <select className="field" value={category} onChange={(event) => updateCategory(event.target.value)}>
          <option value="">{loading && !analysis ? "Loading categories…" : "Select a job category"}</option>
          {(analysis?.categories || []).map((item) => <option value={item} key={item}>{item}</option>)}
        </select>
      </label>
      <label className="text-sm font-semibold text-slate-600">Specific current job (optional)
        <select className="field" value={task} onChange={(event) => updateTask(event.target.value)} disabled={!category || loading}>
          <option value="">{loading && category ? "Loading jobs…" : "All jobs in selected category"}</option>
          {(analysis?.target_tasks || []).map((item) => <option value={item.id} key={item.id}>{item.title}</option>)}
        </select>
      </label>
    </div>
    {!loading && !error && analysis && !analysis.categories.length && <p className="text-sm text-slate-500">No active jobs have a category yet. Add a category when creating or editing a task.</p>}
    {!loading && !error && category && analysis && !analysis.target_tasks.length && <p className="text-sm text-slate-500">No active jobs are listed in this category.</p>}
    {loading ? <div className="rounded-xl bg-slate-50 p-6 text-center text-sm text-slate-500" role="status">Analyzing your skills against current jobs…</div> : analysis && <>
      <div><h3 className="text-sm font-bold text-slate-700">Your current skills</h3>{analysis.current_skills.length ? <div className="mt-2 flex flex-wrap gap-2">{analysis.current_skills.map((skill) => <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-blue-800" key={skill.id}>{skill.name} · {skill.proficiency}/5</span>)}</div> : <p className="mt-2 text-sm text-slate-500">No skills are listed yet. Add skills in your <Link to="/profile" className="font-semibold text-brand underline">worker profile</Link> to get a personalized comparison.</p>}</div>
      {!analysis.target.category && !analysis.target.task ? <EmptyState>{analysis.message}</EmptyState> : !analysis.data_available ? <EmptyState>{analysis.message}</EmptyState> : <>
        <div className="rounded-2xl bg-slate-50 p-4 sm:flex sm:items-center sm:gap-5">
          <div className="flex h-24 w-24 shrink-0 flex-col items-center justify-center rounded-full border-4 border-brand bg-white"><span className="text-2xl font-black text-brand">{analysis.match_percentage}%</span><span className="text-[10px] font-bold uppercase text-slate-400">skill match</span></div>
          <div className="mt-3 flex-1 sm:mt-0"><div className="flex justify-between text-xs text-slate-500"><span>{analysis.matched_count} of {analysis.required_count} required skills matched</span><span>{analysis.matching_task_count} active jobs analyzed</span></div><div className="mt-2 h-2.5 overflow-hidden rounded-full bg-slate-200"><div className="h-full rounded-full bg-brand transition-all" style={{ width: `${analysis.match_percentage}%` }} /></div><p className="mt-3 text-sm leading-6 text-slate-600">{analysis.explanation}</p></div>
        </div>
        <div className="grid gap-4 md:grid-cols-2">
          <SkillList title="Matched skills" skills={analysis.matched_skills} tone="green" empty="No listed job requirements match your current skills yet." />
          <SkillList title="Skills to improve" skills={analysis.improve_skills || []} tone="violet" empty="Your current matching skills are at proficiency level 3 or above." />
          <SkillList title="Skills to build" skills={analysis.missing_skills} tone="amber" empty="Great work — you match all listed skills for this target." />
        </div>
        <div className="rounded-xl border border-violet-100 bg-violet-50/60 p-4"><p className="text-xs font-black uppercase tracking-widest text-violet-700">Recommended next skills</p>{analysis.recommendations.length ? <div className="mt-3 space-y-2">{analysis.recommendations.map((skill) => <div className="flex flex-wrap items-center justify-between gap-2" key={skill.id}><div><span className="font-bold text-slate-800">{skill.name}</span><span className="ml-2 rounded-full bg-white px-2 py-0.5 text-[10px] font-black uppercase text-violet-700">{skill.priority} priority</span></div><span className="text-xs text-slate-500">Required by {skill.frequency_percent}% of matching jobs</span></div>)}</div> : <p className="mt-2 text-sm text-slate-600">No skill gaps found for the selected target.</p>}<Link className="mt-4 inline-block text-sm font-bold text-brand hover:underline" to="/recommendations">See your existing job recommendations →</Link></div>
      </>}
    </>}
  </section>;
}

function SkillList({ title, skills, tone, empty }) {
  const colors = tone === "green" ? "bg-emerald-50 text-emerald-800" : tone === "violet" ? "bg-violet-50 text-violet-800" : "bg-amber-50 text-amber-900";
  return <div className="rounded-xl border border-slate-100 p-4"><h3 className="font-bold">{title}</h3>{skills.length ? <ul className="mt-3 space-y-2">{skills.map((skill) => <li className={`flex flex-wrap items-center justify-between gap-2 rounded-lg px-3 py-2 text-sm ${colors}`} key={skill.id}><span className="font-semibold">{tone === "green" ? "✓" : tone === "violet" ? "↗" : "＋"} {skill.name}</span>{tone === "violet" ? <span className="text-xs">Level {skill.proficiency}/5 · needed in {skill.frequency_percent}% of target jobs</span> : tone === "amber" && <span className="text-xs">{skill.frequency_percent}% of jobs · {skill.priority}</span>}</li>)}</ul> : <p className="mt-2 text-sm text-slate-500">{empty}</p>}</div>;
}
