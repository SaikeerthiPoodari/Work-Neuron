import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../services/api";
import { EmptyState, ErrorMessage } from "./StatusMessage";
import { useI18n } from "../i18n/I18nContext";

export default function WorkerSkillProgress() {
  const { t } = useI18n();
  const [skills, setSkills] = useState([]);
  const [error, setError] = useState("");
  useEffect(() => { get("/skills/mine/").then(setSkills).catch((err) => setError(err.message)); }, []);
  return <section className="card space-y-4">
    <div className="flex items-center justify-between gap-3"><div><p className="text-xs font-black uppercase tracking-widest text-brand">{t("yourSkillGraph")}</p><h2 className="mt-1 text-lg font-black">{t("skillProgressTitle")}</h2></div><Link className="text-sm font-bold text-brand" to="/skill-graph">{t("exploreSkills")} →</Link></div>
    <ErrorMessage message={error} />
    {skills.length ? <div className="space-y-3">{skills.slice(0, 6).map((item) => <div key={item.id}><div className="flex justify-between gap-3 text-sm"><span className="font-semibold">{item.skill_name}</span><span className="text-slate-500">{item.proficiency}/5</span></div><div className="mt-1.5 h-2 overflow-hidden rounded-full bg-slate-100"><div className="h-full rounded-full bg-brand" style={{ width: `${Math.max(0, Math.min(100, Number(item.proficiency) * 20))}%` }} /></div></div>)}</div> : !error && <EmptyState>{t("noSkillsYet")}</EmptyState>}
  </section>;
}
