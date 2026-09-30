import { useEffect, useMemo, useState } from "react";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { get, post } from "../services/api";

const categories = ["TASK", "APPLICATION", "ASSIGNMENT", "PAYMENT"];

export default function ClientComplaintsPage() {
  const [items, setItems] = useState([]);
  const [references, setReferences] = useState({ tasks: [], applications: [], assignments: [], payments: [] });
  const [form, setForm] = useState({ category: "TASK", reference: "", description: "" });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    setLoading(true);
    setError("");
    try {
      const [complaints, tasks, applications, assignments, payments] = await Promise.all([
        get("/complaints/"), get("/tasks/"), get("/applications/"), get("/assignments/"), get("/payments/"),
      ]);
      setItems(complaints);
      setReferences({ tasks, applications, assignments, payments });
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const choices = useMemo(() => {
    const values = references[{ TASK: "tasks", APPLICATION: "applications", ASSIGNMENT: "assignments", PAYMENT: "payments" }[form.category]] || [];
    return values.map((item) => ({
      id: item.id,
      label: form.category === "TASK" ? item.title
        : form.category === "APPLICATION" ? `${item.task_title} · ${item.worker_email}`
          : form.category === "ASSIGNMENT" ? `${item.task_title} · ${item.worker_email}`
            : `${item.assignment_title} · ₹${item.amount} · ${item.status}`,
    }));
  }, [form.category, references]);

  useEffect(() => { setForm((current) => ({ ...current, reference: "" })); }, [form.category]);

  const submit = async (event) => {
    event.preventDefault();
    setError("");
    setNotice("");
    const fieldByCategory = { TASK: "task", APPLICATION: "application", ASSIGNMENT: "assignment", PAYMENT: "transaction" };
    try {
      await post("/complaints/", {
        category: form.category,
        [fieldByCategory[form.category]]: Number(form.reference),
        description: form.description,
      });
      setForm((current) => ({ ...current, reference: "", description: "" }));
      setNotice("Complaint submitted to WorkNeuron support.");
      await load();
    } catch (err) {
      setError(err.message);
    }
  };

  return <div className="space-y-6">
    <header><p className="text-sm font-semibold text-brand">Safety and support</p><h1 className="mt-1 text-3xl font-black">Complaints</h1><p className="mt-2 text-sm text-slate-500">Submit a concern linked to one of your jobs, applications, assignments, or payments.</p></header>
    <ErrorMessage message={error} />
    {notice && <p role="status" className="rounded-lg border border-emerald-200 bg-emerald-50 p-3 text-sm text-emerald-800">{notice}</p>}
    <form onSubmit={submit} className="card grid gap-4 md:grid-cols-2">
      <label className="label">Related to<select className="field" value={form.category} onChange={(event) => setForm((current) => ({ ...current, category: event.target.value }))}>{categories.map((category) => <option key={category} value={category}>{category.charAt(0) + category.slice(1).toLowerCase()}</option>)}</select></label>
      <label className="label">Select record<select className="field" required value={form.reference} onChange={(event) => setForm((current) => ({ ...current, reference: event.target.value }))}><option value="">Choose a record</option>{choices.map((choice) => <option value={choice.id} key={choice.id}>{choice.label}</option>)}</select></label>
      <label className="label md:col-span-2">Description<textarea required minLength="5" className="field" rows="4" value={form.description} onChange={(event) => setForm((current) => ({ ...current, description: event.target.value }))} /></label>
      {!choices.length && <p className="text-sm text-slate-500 md:col-span-2">No records are available for this category yet.</p>}
      <div className="md:col-span-2"><button className="button-primary" disabled={!choices.length}>Submit complaint</button></div>
    </form>
    <section className="space-y-3" aria-label="Your complaints"><h2 className="text-lg font-bold">Your submissions</h2>{loading ? <p role="status" className="card text-sm text-slate-500">Loading complaints...</p> : items.length ? items.map((item) => {
      const task = references.tasks.find((record) => record.id === item.task);
      const application = references.applications.find((record) => record.id === item.application);
      const assignment = references.assignments.find((record) => record.id === item.assignment);
      const payment = references.payments.find((record) => record.id === item.transaction);
      const related = task?.title || application?.task_title || assignment?.task_title || payment?.assignment_title || `${item.category} #${item.task || item.application || item.assignment || item.transaction}`;
      return <article className="card" key={item.id}><div className="flex flex-wrap justify-between gap-2"><h3 className="font-bold">{item.category} · {related}</h3><span className="text-xs font-bold uppercase text-brand">{item.status.replaceAll("_", " ")}</span></div><p className="mt-2 whitespace-pre-wrap text-sm text-slate-600">{item.description}</p>{item.resolution_notes && <p className="mt-3 rounded-lg bg-emerald-50 p-3 text-sm text-emerald-800">Support response: {item.resolution_notes}</p>}<p className="mt-3 text-xs text-slate-400">Submitted {new Date(item.created_at).toLocaleString()}</p></article>;
    }) : <EmptyState>No complaints filed.</EmptyState>}</section>
  </div>;
}