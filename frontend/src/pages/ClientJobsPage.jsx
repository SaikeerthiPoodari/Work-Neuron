import { useEffect, useMemo, useState } from "react";
import { Link, useSearchParams } from "react-router-dom";
import { get, patch, post, remove } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";

const jobTypes = [
  ["FULL_TIME", "Full time"], ["PART_TIME", "Part time"], ["DAILY_WAGE", "Daily wage"],
  ["WEEKEND", "Weekend"], ["EVENT", "Event"], ["FESTIVAL", "Festival"],
  ["CONTRACT", "Contract"], ["FREELANCE", "Freelance"], ["TEMPORARY", "Temporary"],
  ["INTERNSHIP", "Internship"],
];
const salaryTypes = [["MONTHLY", "Monthly"], ["DAILY", "Daily"], ["HOURLY", "Hourly"], ["FIXED", "Fixed"], ["NEGOTIABLE", "Negotiable"]];
const modes = [["REMOTE", "Remote"], ["ONSITE", "On-site"], ["HYBRID", "Hybrid"]];
const tabs = [
  ["ALL", "All jobs"], ["DRAFT", "Drafts"], ["ACTIVE", "Active"], ["APPLICATIONS_RECEIVED", "Applications"],
  ["ASSIGNED", "Assigned"], ["IN_PROGRESS", "In progress"], ["COMPLETED", "Completed"], ["CANCELLED", "Closed"],
];
const emptyForm = {
  title: "", description: "", category: "", skill_ids: [], education_requirement: "",
  experience_requirement: "", working_hours: "", availability_requirements: "", job_type: "FREELANCE",
  salary_type: "FIXED", budget: "", location: "", location_address: "", location_area: "",
  location_city: "", location_state: "", latitude: "", longitude: "", work_mode: "REMOTE",
  start_date: "", end_date: "", deadline: "",
};

export default function ClientJobsPage() {
  const [searchParams, setSearchParams] = useSearchParams();
  const [tasks, setTasks] = useState([]);
  const [applicationCounts, setApplicationCounts] = useState({});
  const [filter, setFilter] = useState("ALL");
  const [showForm, setShowForm] = useState(searchParams.get("create") === "1");
  const [editing, setEditing] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [ownedTasks, applications] = await Promise.all([get("/tasks/"), get("/applications/")]);
      setTasks(ownedTasks);
      setApplicationCounts(applications.reduce((counts, item) => {
        if (["SUBMITTED", "ACCEPTED"].includes(item.status)) counts[item.task] = (counts[item.task] || 0) + 1;
        return counts;
      }, {}));
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);
  useEffect(() => {
    if (searchParams.get("create") === "1") setShowForm(true);
  }, [searchParams]);

  const visibleTasks = useMemo(() => tasks.filter((task) => {
    if (filter === "ALL") return true;
    if (filter === "ACTIVE") return !["DRAFT", "COMPLETED", "CANCELLED"].includes(task.status);
    return task.status === filter;
  }), [filter, tasks]);

  const closeForm = () => {
    setShowForm(false);
    setEditing(null);
    if (searchParams.has("create")) {
      const next = new URLSearchParams(searchParams);
      next.delete("create");
      setSearchParams(next, { replace: true });
    }
  };

  const cancelTask = async (task) => {
    if (!window.confirm(`Close "${task.title}"? This changes the job status to cancelled.`)) return;
    try {
      await post(`/tasks/${task.id}/transition/`, { status: "CANCELLED" });
      setNotice("Job closed.");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const deleteTask = async (task) => {
    if (!window.confirm(`Permanently delete "${task.title}"? This cannot be undone.`)) return;
    try {
      await remove(`/tasks/${task.id}/`);
      setNotice("Job deleted.");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  const publishDraft = async (task) => { try { await post(`/tasks/${task.id}/transition/`, { status: "OPEN" }); setNotice("Draft published."); await load(); } catch (err) { setError(err.message); } };

  return <div className="space-y-6">
    <header className="flex flex-col justify-between gap-4 sm:flex-row sm:items-end">
      <div><p className="text-sm font-semibold text-brand">Employer workspace</p><h1 className="mt-1 text-3xl font-black tracking-tight">My jobs</h1><p className="mt-2 text-sm text-slate-500">Manage postings, review applications, and follow work through completion.</p></div>
      <button className="button-primary" onClick={() => { setEditing(null); setShowForm(true); }}>Post a job</button>
    </header>
    <ErrorMessage message={error} />
    {notice && <p role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
    {(showForm || editing) && <ClientTaskForm task={editing} onCancel={closeForm} onSaved={async () => { closeForm(); setNotice(editing ? "Job updated." : "Job published."); await load(); }} />}
    <div className="flex gap-2 overflow-x-auto pb-1" role="tablist" aria-label="Filter jobs by status">
      {tabs.map(([value, label]) => <button key={value} type="button" role="tab" aria-selected={filter === value} className={`shrink-0 rounded-lg px-3 py-2 text-sm font-semibold ${filter === value ? "bg-brand text-white" : "bg-white text-slate-600 ring-1 ring-slate-200"}`} onClick={() => setFilter(value)}>{label}</button>)}
    </div>
    {loading ? <div className="card text-sm text-slate-500" role="status">Loading your jobs...</div> : visibleTasks.length ? <div className="grid gap-4 lg:grid-cols-2">{visibleTasks.map((task) => <article className="card" key={task.id}>
      <div className="flex items-start justify-between gap-4"><div><p className="text-xs font-bold uppercase tracking-wide text-brand">{task.status.replaceAll("_", " ")}</p><h2 className="mt-1 text-lg font-bold">{task.title}</h2></div><p className="shrink-0 font-bold text-emerald-700">₹{Number(task.budget).toLocaleString("en-IN")} <span className="text-xs font-medium text-slate-500">{task.salary_type.toLowerCase()}</span></p></div>
      <p className="mt-3 line-clamp-2 text-sm text-slate-600">{task.description}</p>
      <div className="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-slate-500"><span>{jobTypes.find(([value]) => value === task.job_type)?.[1] || task.job_type}</span><span>{task.location_city || task.location || (task.work_mode === "REMOTE" ? "Remote" : "Location not set")}</span><span>{applicationCounts[task.id] || 0} applications</span><span>Deadline {task.deadline ? new Date(task.deadline).toLocaleDateString() : "Not set"}</span></div>
      <div className="mt-4 flex flex-wrap gap-2 border-t border-slate-100 pt-4"><Link className="button-secondary" to={`/tasks/${task.id}`}>View job</Link>{["DRAFT", "OPEN", "APPLICATIONS_RECEIVED"].includes(task.status) && <button className="button-secondary" onClick={() => { setEditing(task); setShowForm(false); window.scrollTo({ top: 0, behavior: "smooth" }); }}>Edit</button>}{task.status === "DRAFT" && <button className="button-primary" onClick={() => publishDraft(task)}>Publish</button>}{task.status !== "DRAFT" && <Link className="button-secondary" to={`/applications?task=${task.id}`}>Applications</Link>}{["DRAFT", "OPEN"].includes(task.status) && !applicationCounts[task.id] && <button className="rounded-lg border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50" onClick={() => deleteTask(task)}>Delete</button>}{!["DRAFT", "COMPLETED", "CANCELLED"].includes(task.status) && <button className="rounded-lg border border-rose-200 px-3 py-2 text-sm font-semibold text-rose-700 hover:bg-rose-50" onClick={() => cancelTask(task)}>Close job</button>}</div>
    </article>)}</div> : <EmptyState>{filter === "ALL" ? "No jobs yet. Post your first job to start receiving applications." : "No jobs in this status."}</EmptyState>}
    <p className="text-xs text-slate-500">Drafts are saved privately until you publish them. Salary is stored as one budget amount; separate minimum and maximum values are not supported by the backend.</p>
  </div>;
}

function ClientTaskForm({ task, onCancel, onSaved }) {
  const [step, setStep] = useState(0);
  const [form, setForm] = useState(() => task ? taskToForm(task) : emptyForm);
  const [skills, setSkills] = useState([]);
  const [error, setError] = useState("");
  const [saving, setSaving] = useState(false);
  const steps = ["Basic information", "Requirements", "Job type and salary", "Location", "Schedule", "Preview"];

  useEffect(() => { get("/skills/").then(setSkills).catch((err) => setError(`Skills are unavailable: ${err.message}`)); }, []);
  const change = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  const useCurrentLocation = () => {
    setError("");
    if (!navigator.geolocation) { setError("Location is unavailable in this browser. Enter the address manually."); return; }
    navigator.geolocation.getCurrentPosition(
      ({ coords }) => setForm((current) => ({ ...current, latitude: coords.latitude.toFixed(6), longitude: coords.longitude.toFixed(6) })),
      (err) => setError(err.code === 1 ? "Location permission was denied. Enter the address manually." : "Could not get your location. Enter it manually and try again."),
      { enableHighAccuracy: false, timeout: 10000, maximumAge: 60000 },
    );
  };

  const validateStep = () => {
    if (step === 0 && (!form.title.trim() || !form.description.trim())) return "Add a job title and description to continue.";
    if (step === 2 && (!form.budget || Number(form.budget) < 0)) return "Enter a valid salary or budget amount.";
    if (step === 3 && form.work_mode === "ONSITE" && !(form.location_address || form.location) ) return "Add an address for an on-site job.";
    if (step === 3 && form.work_mode === "ONSITE" && !form.location_city.trim()) return "Add a city for an on-site job.";
    if (step === 4 && !form.deadline) return "Set an application deadline.";
    if (form.start_date && form.end_date && form.end_date < form.start_date) return "End date cannot be before the start date.";
    return "";
  };

  const save = async (event, draft = false) => {
    event.preventDefault();
    const validation = validateStep();
    if (validation) { setError(validation); return; }
    if (step < steps.length - 1) { setError(""); setStep((current) => current + 1); return; }
    setSaving(true);
    setError("");
    const payload = {
      ...form,
      budget: Number(form.budget),
      deadline: new Date(form.deadline).toISOString(),
      start_date: form.start_date || null,
      end_date: form.end_date || null,
      latitude: form.latitude === "" ? null : Number(form.latitude),
      longitude: form.longitude === "" ? null : Number(form.longitude),
      is_remote: form.work_mode === "REMOTE",
      skill_ids: form.skill_ids.map(Number), save_as_draft: draft,
    };
    try {
      if (task) await patch(`/tasks/${task.id}/`, payload);
      else await post("/tasks/", payload);
      await onSaved();
    } catch (err) {
      setError(err.message);
    } finally {
      setSaving(false);
    }
  };

  return <form className="card space-y-5" onSubmit={save}>
    <div className="flex flex-wrap items-start justify-between gap-3"><div><p className="text-xs font-bold uppercase tracking-wide text-brand">{task ? "Edit job" : "New job"}</p><h2 className="mt-1 text-xl font-black">{steps[step]}</h2></div><button className="button-secondary" type="button" onClick={onCancel}>Close</button></div>
    <div className="flex flex-wrap gap-2" aria-label={`Step ${step + 1} of ${steps.length}`}>{steps.map((label, index) => <span key={label} className={`rounded-md px-2 py-1 text-xs font-semibold ${step === index ? "bg-brand text-white" : index < step ? "bg-emerald-50 text-emerald-800" : "bg-slate-100 text-slate-500"}`}>{index + 1}. {label}</span>)}</div>
    {step === 0 && <div className="grid gap-4 sm:grid-cols-2"><TextField label="Job title" required value={form.title} onChange={(value) => change("title", value)} /><TextField label="Category" value={form.category} onChange={(value) => change("category", value)} /><div className="sm:col-span-2"><TextField label="Description" multiline required value={form.description} onChange={(value) => change("description", value)} /></div><SkillPicker skills={skills} selected={form.skill_ids} onChange={(value) => change("skill_ids", value)} /></div>}
    {step === 1 && <div className="grid gap-4 sm:grid-cols-2"><TextField label="Education requirement" value={form.education_requirement} onChange={(value) => change("education_requirement", value)} /><TextField label="Experience requirement" value={form.experience_requirement} onChange={(value) => change("experience_requirement", value)} /><TextField label="Working hours" placeholder="e.g. 9 AM-5 PM, weekends" value={form.working_hours} onChange={(value) => change("working_hours", value)} /><TextField label="Availability requirements" multiline value={form.availability_requirements} onChange={(value) => change("availability_requirements", value)} /></div>}
    {step === 2 && <div className="grid gap-4 sm:grid-cols-2"><SelectField label="Job type" value={form.job_type} options={jobTypes} onChange={(value) => change("job_type", value)} /><SelectField label="Salary type" value={form.salary_type} options={salaryTypes} onChange={(value) => change("salary_type", value)} /><TextField label="Salary / budget (INR)" type="number" min="0" step="0.01" required value={form.budget} onChange={(value) => change("budget", value)} /><p className="self-end text-xs text-slate-500">The current API stores one budget amount, not a minimum/maximum range.</p></div>}
    {step === 3 && <div className="grid gap-4 sm:grid-cols-2"><SelectField label="Work mode" value={form.work_mode} options={modes} onChange={(value) => change("work_mode", value)} /><TextField label="Address" required={form.work_mode === "ONSITE"} value={form.location_address} onChange={(value) => change("location_address", value)} /><TextField label="Area" value={form.location_area} onChange={(value) => change("location_area", value)} /><TextField label="City" required={form.work_mode === "ONSITE"} value={form.location_city} onChange={(value) => change("location_city", value)} /><TextField label="State" value={form.location_state} onChange={(value) => change("location_state", value)} /><TextField label="Location summary" value={form.location} onChange={(value) => change("location", value)} /><TextField label="Latitude" type="number" min="-90" max="90" step="any" value={form.latitude} onChange={(value) => change("latitude", value)} /><TextField label="Longitude" type="number" min="-180" max="180" step="any" value={form.longitude} onChange={(value) => change("longitude", value)} /><div className="sm:col-span-2"><button className="button-secondary" type="button" onClick={useCurrentLocation}>Use my current location</button><p className="mt-2 text-xs text-slate-500">Location is read once only. You can enter or adjust it manually.</p></div></div>}
    {step === 4 && <div className="grid gap-4 sm:grid-cols-2"><TextField label="Start date" type="date" value={form.start_date} onChange={(value) => change("start_date", value)} /><TextField label="End date" type="date" value={form.end_date} onChange={(value) => change("end_date", value)} /><TextField label="Application deadline" type="datetime-local" required value={form.deadline} onChange={(value) => change("deadline", value)} /></div>}
    {step === 5 && <div className="rounded-lg bg-slate-50 p-4"><h3 className="text-lg font-bold">{form.title}</h3><p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{form.description}</p><dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2">{[["Category", form.category], ["Skills", skills.filter((skill) => form.skill_ids.includes(skill.id)).map((skill) => skill.name).join(", ")], ["Requirements", [form.education_requirement, form.experience_requirement].filter(Boolean).join(" · ")], ["Hours", form.working_hours], ["Job type", jobTypes.find(([value]) => value === form.job_type)?.[1]], ["Compensation", `INR ${form.budget} · ${salaryTypes.find(([value]) => value === form.salary_type)?.[1]}`], ["Work mode", modes.find(([value]) => value === form.work_mode)?.[1]], ["Location", [form.location_address, form.location_area, form.location_city, form.location_state].filter(Boolean).join(", ") || form.location || "Not specified"], ["Schedule", [form.start_date, form.end_date].filter(Boolean).join(" to ") || "Flexible"], ["Deadline", form.deadline ? new Date(form.deadline).toLocaleString() : "Not set"]].map(([label, value]) => <div key={label}><dt className="text-xs font-semibold uppercase text-slate-500">{label}</dt><dd className="mt-1">{value || "Not specified"}</dd></div>)}</dl></div>}
    <ErrorMessage message={error} />
    <div className="flex flex-wrap justify-between gap-2 border-t border-slate-100 pt-4"><button type="button" className="button-secondary" disabled={step === 0} onClick={() => { setError(""); setStep((current) => current - 1); }}>Back</button>{step < steps.length - 1 ? <button className="button-primary" type="submit">Continue</button> : <div className="flex flex-wrap gap-2"><button className="button-secondary" type="button" disabled={saving || Boolean(task)} onClick={(event) => save(event, true)}>Save draft</button><button className="button-primary" disabled={saving}>{saving ? "Saving..." : task ? "Save changes" : "Publish job"}</button></div>}</div>
  </form>;
}

function taskToForm(task) {
  const dateTime = task.deadline ? new Date(new Date(task.deadline).getTime() - new Date(task.deadline).getTimezoneOffset() * 60000).toISOString().slice(0, 16) : "";
  return { ...emptyForm, ...task, skill_ids: (task.required_skills || []).map((skill) => skill.id), deadline: dateTime, budget: String(task.budget), latitude: task.latitude ?? "", longitude: task.longitude ?? "" };
}

function TextField({ label, value, onChange, type = "text", required = false, ...props }) {
  const id = `client-job-${label.toLowerCase().replaceAll(/[^a-z0-9]+/g, "-")}`;
  return <div><label className="label" htmlFor={id}>{label}</label>{props.multiline ? <textarea id={id} className="field" rows="4" required={required} value={value || ""} onChange={(event) => onChange(event.target.value)} placeholder={props.placeholder} /> : <input id={id} className="field" type={type} required={required} value={value ?? ""} onChange={(event) => onChange(event.target.value)} min={props.min} max={props.max} step={props.step} placeholder={props.placeholder} />}</div>;
}

function SelectField({ label, value, options, onChange }) {
  return <div><label className="label">{label}<select className="field" value={value} onChange={(event) => onChange(event.target.value)}>{options.map(([optionValue, text]) => <option key={optionValue} value={optionValue}>{text}</option>)}</select></label></div>;
}

function SkillPicker({ skills, selected, onChange }) {
  return <fieldset className="sm:col-span-2"><legend className="label">Required skills</legend>{skills.length ? <div className="grid max-h-48 gap-2 overflow-y-auto rounded-lg border border-slate-200 p-3 sm:grid-cols-2">{skills.map((skill) => <label className="flex items-center gap-2 text-sm" key={skill.id}><input type="checkbox" checked={selected.includes(skill.id)} onChange={(event) => onChange(event.target.checked ? [...selected, skill.id] : selected.filter((id) => id !== skill.id))} />{skill.name}</label>)}</div> : <p className="text-sm text-slate-500">No skill catalog entries available.</p>}</fieldset>;
}
