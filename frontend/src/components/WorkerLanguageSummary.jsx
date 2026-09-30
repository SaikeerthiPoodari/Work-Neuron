import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../services/api";
import { languageLabels } from "../i18n/languages";

export default function WorkerLanguageSummary() {
  const [selected, setSelected] = useState([]);
  useEffect(() => { get("/profiles/me/").then((profile) => setSelected(profile.languages || [])).catch(() => {}); }, []);

  return <section className="card"><div className="flex items-center justify-between gap-3"><div><h2 className="font-bold">Languages for work</h2><p className="mt-1 text-sm text-slate-500">Your language preferences are included in worker matching.</p></div><Link to="/profile" className="text-sm font-bold text-brand">Edit profile →</Link></div><div className="mt-3 flex flex-wrap gap-2">{selected.length ? selected.map((code) => <span key={code} className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-semibold text-brand">{languageLabels[code] || code}</span>) : <span className="text-sm text-slate-500">No languages selected yet.</span>}</div></section>;
}
