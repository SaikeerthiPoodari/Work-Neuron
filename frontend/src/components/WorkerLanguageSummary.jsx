import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get } from "../services/api";
import { languageLabels } from "../i18n/languages";
import { useI18n } from "../i18n/I18nContext";

export default function WorkerLanguageSummary() {
  const { t } = useI18n();
  const [selected, setSelected] = useState([]);
  useEffect(() => { get("/profiles/me/").then((profile) => setSelected(profile.languages || [])).catch(() => {}); }, []);
  return <section className="card"><div className="flex items-center justify-between gap-3"><div><h2 className="font-bold">{t("languagesForWork")}</h2><p className="mt-1 text-sm text-slate-500">{t("languagePreferenceHint")}</p></div><Link to="/profile" className="text-sm font-bold text-brand">{t("editProfile")} →</Link></div><div className="mt-3 flex flex-wrap gap-2">{selected.length ? selected.map((code) => <span key={code} className="rounded-full bg-blue-50 px-3 py-1.5 text-xs font-semibold text-brand">{languageLabels[code] || code}</span>) : <span className="text-sm text-slate-500">{t("noLanguages")}</span>}</div></section>;
}
