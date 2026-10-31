import { useEffect, useState } from "react";
import { get, post } from "../services/api";
import { ErrorMessage, EmptyState } from "../components/StatusMessage";
import { useAuth } from "../context/AuthContext";

export default function ClientCommunicationPage() {
  const { user } = useAuth();
  const client = user.role === "CLIENT";
  const [messages, setMessages] = useState([]);
  const [interviews, setInterviews] = useState([]);
  const [applications, setApplications] = useState([]);
  const [message, setMessage] = useState({ application: "", body: "" });
  const [interview, setInterview] = useState({ application: "", starts_at: "", ends_at: "", location: "", notes: "" });
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");

  const load = async () => {
    try {
      const [messageData, interviewData, applicationData] = await Promise.all([get("/messaging/messages/"), get("/messaging/interviews/"), get("/applications/")]);
      setMessages(messageData); setInterviews(interviewData); setApplications(applicationData);
    } catch (err) { setError(err.message); }
  };
  useEffect(() => { load(); const refresh = () => load(); window.addEventListener("workneuron-notification", refresh); return () => window.removeEventListener("workneuron-notification", refresh); }, []);

  const send = async (event) => {
    event.preventDefault(); setError("");
    try {
      const selected = applications.find((item) => String(item.id) === message.application);
      if (!selected || !message.body.trim()) throw new Error("Select an application and enter a message first.");
      await post("/messaging/messages/", { task: selected.task, application: selected.id, recipient: client ? selected.worker_id : selected.task_owner_id, body: message.body });
      setMessage({ application: "", body: "" }); setNotice("Message sent."); await load();
    } catch (err) { setError(err.message); }
  };

  const schedule = async (event) => {
    event.preventDefault(); setError("");
    try {
      await post("/messaging/interviews/", { ...interview, application: Number(interview.application), starts_at: new Date(interview.starts_at).toISOString(), ends_at: new Date(interview.ends_at).toISOString() });
      setInterview({ application: "", starts_at: "", ends_at: "", location: "", notes: "" }); setNotice("Interview scheduled."); await load();
    } catch (err) { setError(err.message); }
  };

  const markRead = async (item) => { try { await post(`/messaging/messages/${item.id}/read/`); await load(); } catch (err) { setError(err.message); } };
  const eligibleApplications = applications.filter((item) => client || ["SUBMITTED", "ACCEPTED"].includes(item.status));

  return <div className="space-y-6"><header><p className="text-sm font-semibold text-brand">{client ? "Hiring communication" : "Work communication"}</p><h1 className="mt-1 text-3xl font-black tracking-tight">Messages{client ? " & interviews" : ""}</h1><p className="mt-2 text-slate-500">Keep conversations connected to authorized applications and assignments.</p></header><ErrorMessage message={error} />{notice && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-700">{notice}</p>}<div className={`grid gap-6 ${client ? "xl:grid-cols-2" : "max-w-2xl"}`}><form className="card space-y-4" onSubmit={send}><h2 className="font-bold">{client ? "Message an applicant" : "Message the client"}</h2><select required className="field" value={message.application} onChange={(event) => setMessage({ ...message, application: event.target.value })}><option value="">Select application</option>{eligibleApplications.map((item) => <option value={item.id} key={item.id}>#{item.id} · {item.task_title} · {client ? item.worker_email : item.task_owner_email}</option>)}</select><textarea required className="field" rows="4" placeholder="Write a message..." value={message.body} onChange={(event) => setMessage({ ...message, body: event.target.value })} /><button className="button-primary">Send message</button><p className="text-xs text-slate-500">The server verifies that you are a participant in the selected application.</p></form>{client && <form className="card space-y-4" onSubmit={schedule}><h2 className="font-bold">Schedule an interview</h2><select required className="field" value={interview.application} onChange={(event) => setInterview({ ...interview, application: event.target.value })}><option value="">Select application</option>{applications.filter((item) => ["SUBMITTED", "ACCEPTED"].includes(item.status)).map((item) => <option value={item.id} key={item.id}>#{item.id} · {item.task_title} · {item.worker_email}</option>)}</select><div className="grid gap-3 sm:grid-cols-2"><label className="label">Starts<input required type="datetime-local" className="field" value={interview.starts_at} onChange={(event) => setInterview({ ...interview, starts_at: event.target.value })} /></label><label className="label">Ends<input required type="datetime-local" className="field" value={interview.ends_at} onChange={(event) => setInterview({ ...interview, ends_at: event.target.value })} /></label></div><input className="field" placeholder="Meeting link or location" value={interview.location} onChange={(event) => setInterview({ ...interview, location: event.target.value })} /><textarea className="field" rows="2" placeholder="Interview notes" value={interview.notes} onChange={(event) => setInterview({ ...interview, notes: event.target.value })} /><button className="button-primary">Schedule interview</button></form>}</div><section className="card"><h2 className="font-bold">Conversation history</h2>{messages.length ? <div className="mt-3 space-y-2">{messages.map((item) => <article className={`rounded-xl p-3 ${item.read_at ? "bg-slate-50" : "border border-blue-200 bg-blue-50"}`} key={item.id}><div className="flex items-start justify-between gap-3"><div><p className="text-xs font-semibold text-brand">{item.sender_name} · Job #{item.task}</p><p className="mt-1 text-sm">{item.body}</p><p className="mt-1 text-xs text-slate-400">{new Date(item.created_at).toLocaleString()}</p></div>{!item.read_at && item.recipient === user.id && <button className="button-secondary shrink-0 text-xs" onClick={() => markRead(item)}>Mark read</button>}</div></article>)}</div> : <EmptyState>No messages yet.</EmptyState>}</section><section className="card"><h2 className="font-bold">Scheduled interviews</h2>{interviews.length ? <div className="mt-3 divide-y divide-slate-100">{interviews.map((item) => <div className="py-3 text-sm" key={item.id}><p className="font-semibold">Application #{item.application}</p><p className="text-slate-500">{new Date(item.starts_at).toLocaleString()} – {new Date(item.ends_at).toLocaleTimeString()}</p><p className="text-xs text-slate-400">{item.location || "Online / location to be shared"}</p></div>)}</div> : <EmptyState>No interviews scheduled.</EmptyState>}</section></div>;
}
