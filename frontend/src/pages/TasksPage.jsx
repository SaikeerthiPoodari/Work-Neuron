import { useEffect, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { get, post } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import VoiceSearch from "../components/VoiceSearch";
import { useI18n } from "../i18n/I18nContext";

const jobTypes = [["", "allJobTypes"], ["PART_TIME", "partTime"], ["DAILY_WAGE", "dailyWage"], ["WEEKEND", "weekend"], ["EVENT", "event"], ["FESTIVAL", "festival"], ["INTERNSHIP", "internship"], ["FULL_TIME", "fullTime"], ["FREELANCE", "freelance"]];

export default function TasksPage() {
  const { user } = useAuth();
  const { language, setLanguage, availableLanguages, t } = useI18n();
  const [searchParams] = useSearchParams();
  const [tasks, setTasks] = useState([]);
  const [search, setSearch] = useState("");
  const [filters, setFilters] = useState({ job_type: "", location: searchParams.get("location") || "" });
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [showForm, setShowForm] = useState(false);

  const load = (nextFilters = filters) => {
    setLoading(true); setError("");
    const params = new URLSearchParams();
    if (search) params.set("search", search);
    Object.entries(nextFilters).forEach(([key, value]) => value && params.set(key, value));
    return get(`/tasks/${params.toString() ? `?${params.toString()}` : ""}`).then(setTasks).catch((err) => setError(err.message)).finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);
  const applyVoice = (voiceFilters) => { const next = { ...filters, ...voiceFilters }; setFilters(next); load(next); };
  const statusText = (status) => t(status === "OPEN" ? "open" : status === "APPLICATIONS_RECEIVED" ? "applicationsReceived" : status.replaceAll("_", " ").toLowerCase());

  return <div className="space-y-6">
    <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div><p className="text-sm font-semibold text-brand">{user.role === "WORKER" ? t("opportunityFeed") : t("taskManagement")}</p><h1 className="mt-1 text-3xl font-black tracking-tight">{user.role === "WORKER" ? t("findWork") : t("yourTasks")}</h1></div>
      {user.role === "WORKER" ? <label className="text-sm font-semibold text-slate-600">{t("interfaceLanguage")}<select id="interface-language" className="field mt-1" value={language} onChange={(event) => setLanguage(event.target.value)} aria-label={t("interfaceLanguage")}>{availableLanguages.map((item) => <option value={item.code} key={item.code}>{item.label}</option>)}</select></label> : <button className="button-primary" onClick={() => setShowForm(!showForm)}>{showForm ? t("closeForm") : t("createTask")}</button>}
    </div>
    {showForm && <CreateTask onCreated={() => { setShowForm(false); load(); }} />}
    {user.role === "WORKER" && <VoiceSearch onFilters={applyVoice} />}
    {user.role === "WORKER" && <div className="card flex flex-col gap-3 sm:flex-row"><input className="field mt-0" placeholder={t("searchPlaceholder")} aria-label={t("searchPlaceholder")} value={search} onChange={(event) => setSearch(event.target.value)} onKeyDown={(event) => event.key === "Enter" && load()} /><select className="field mt-0 sm:max-w-xs" aria-label={t("allJobTypes")} value={filters.job_type} onChange={(event) => { const next = { ...filters, job_type: event.target.value }; setFilters(next); load(next); }}>{jobTypes.map(([value, key]) => <option value={value} key={value || "all"}>{t(key)}</option>)}</select><button className="button-secondary" onClick={() => load()}>{t("search")}</button></div>}
    {error && <ErrorMessage message={error} />}
    {loading ? <div className="card text-sm text-slate-500" role="status">{t("loadingTasks")}</div> : tasks.length ? <div className="grid gap-4 lg:grid-cols-2">{tasks.map((task) => <Link to={`/tasks/${task.id}`} className="card block transition hover:-translate-y-0.5 hover:border-blue-200 hover:shadow-md" key={task.id}><div className="flex items-start justify-between gap-4"><div><span className="text-xs font-bold uppercase tracking-wide text-brand">{statusText(task.status)}</span><h2 className="mt-2 text-lg font-bold">{task.title}</h2></div><span className="whitespace-nowrap font-bold text-emerald-700">₹{task.budget}</span></div><div className="mt-3 flex flex-wrap gap-2 text-xs font-bold text-slate-500"><span>{t(jobTypes.find(([value]) => value === task.job_type)?.[1] || "freelance")}</span>{task.category && <span>· {task.category}</span>}{task.employer_verification?.status === "VERIFIED" && <span className="text-emerald-700">✓ {t("verifiedEmployer")}</span>}</div><p className="mt-3 line-clamp-2 text-sm text-slate-500">{task.description}</p><div className="mt-4 flex justify-between text-xs text-slate-500"><span>{task.location || t("remote")}</span><span>{task.deadline ? `${t("due")} ${new Date(task.deadline).toLocaleDateString(language)}` : t("flexible")}</span></div></Link>)}</div> : <EmptyState>{user.role === "CLIENT" ? t("noOwnTasks") : t("noTasks")}</EmptyState>}
  </div>;
}

function CreateTask({ onCreated }) {
  const { t } = useI18n();
  const [form, setForm] = useState({ title: "", description: "", budget: "", category: "", job_type: "FREELANCE", salary_type: "FIXED", deadline: "", location: "", availability_requirements: "", skill_ids: [] });
  const [skills, setSkills] = useState([]); const [error, setError] = useState("");
  useEffect(() => { get("/skills/").then(setSkills).catch((err) => setError(`Unable to load skills: ${err.message}`)); }, []);
  const submit = async (event) => { event.preventDefault(); setError(""); try { await post("/tasks/", { ...form, budget: Number(form.budget), deadline: new Date(form.deadline).toISOString() }); onCreated(); } catch (err) { setError(err.message); } };
  return <form onSubmit={submit} className="card grid gap-4 md:grid-cols-2"><div className="md:col-span-2"><h2 className="text-lg font-bold">Publish a task</h2><p className="mt-1 text-sm text-slate-500">Add the job type and requirements so matching can rank it accurately.</p></div><Field label="Title" value={form.title} onChange={(value) => setForm({ ...form, title: value })} /><Field label="Budget (INR)" type="number" value={form.budget} onChange={(value) => setForm({ ...form, budget: value })} /><Field label="Category" value={form.category} onChange={(value) => setForm({ ...form, category: value })} /><div><label className="label">Job type</label><select className="field" value={form.job_type} onChange={(event) => setForm({ ...form, job_type: event.target.value })}>{jobTypes.slice(1).map(([value, key]) => <option value={value} key={value}>{t(key)}</option>)}</select></div><Field label="Deadline" type="datetime-local" value={form.deadline} onChange={(value) => setForm({ ...form, deadline: value })} /><Field label="Location" value={form.location} onChange={(value) => setForm({ ...form, location: value })} /><div><label className="label">Required skills</label><select multiple required className="field min-h-32" value={form.skill_ids} onChange={(event) => setForm({ ...form, skill_ids: [...event.target.selectedOptions].map((option) => Number(option.value)) })}>{skills.map((skill) => <option value={skill.id} key={skill.id}>{skill.name}</option>)}</select></div><div className="md:col-span-2"><label className="label">Description</label><textarea required className="field" rows="4" value={form.description} onChange={(event) => setForm({ ...form, description: event.target.value })} /></div><div className="md:col-span-2"><ErrorMessage message={error} /><button className="button-primary mt-3">Publish task</button></div></form>;
}

function Field({ label, type = "text", value, onChange }) { return <div><label className="label">{label}</label><input required className="field" type={type} value={value} onChange={(event) => onChange(event.target.value)} /></div>; }
