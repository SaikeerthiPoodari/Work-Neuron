import { useEffect, useState } from "react";
import { get, post } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { useAuth } from "../context/AuthContext";

export default function NetworkMessagesPage() {
  const { user } = useAuth();
  const [connections, setConnections] = useState([]);
  const [selected, setSelected] = useState(null);
  const [messages, setMessages] = useState([]);
  const [body, setBody] = useState("");
  const [error, setError] = useState("");
  const loadConnections = async () => { try { const data = await get("/network/connections/"); setConnections(data.filter((item) => item.status === "ACCEPTED")); } catch (err) { setError(err.message); } };
  const loadMessages = async (person) => { setSelected(person); if (!person) return; try { const data = await get(`/network/direct-messages/?user=${person.id}`); setMessages(data); } catch (err) { setError(err.message); } };
  useEffect(() => { loadConnections(); }, []);
  useEffect(() => { const handler = () => selected && loadMessages(selected); window.addEventListener("workneuron-notification", handler); return () => window.removeEventListener("workneuron-notification", handler); }, [selected]);
  const send = async (event) => { event.preventDefault(); if (!selected || !body.trim()) return; try { await post("/network/direct-messages/", { recipient: selected.id, body }); setBody(""); await loadMessages(selected); } catch (err) { setError(err.message); } };
  const personFor = (connection) => connection.requester.id === user.id ? connection.recipient : connection.requester;
  return <div className="space-y-6"><header><p className="text-sm font-semibold text-brand">Network</p><h1 className="mt-1 text-3xl font-black">Direct messages</h1><p className="mt-2 text-slate-500">Talk with accepted connections about projects, work, and collaboration.</p></header><ErrorMessage message={error} /><div className="grid gap-6 lg:grid-cols-[18rem_1fr]"><aside className="card"><h2 className="font-bold">Connections</h2>{connections.length ? <div className="mt-3 space-y-1">{connections.map((item) => { const person = personFor(item); return <button key={item.id} className={`w-full rounded-xl p-3 text-left ${selected?.id === person.id ? "bg-blue-50 text-brand" : "hover:bg-slate-50"}`} onClick={() => loadMessages(person)}><span className="font-semibold">{person.name}</span><span className="block text-xs text-slate-500">{person.headline || person.role}</span></button>; })}</div> : <EmptyState>No accepted connections yet.</EmptyState>}</aside><section className="card min-h-[28rem]"><h2 className="font-bold">{selected ? selected.name : "Select a connection"}</h2>{selected ? <><div className="mt-4 space-y-3">{messages.length ? messages.map((item) => { const mine = item.sender?.id === user.id; return <div key={item.id} className={`flex ${mine ? "justify-end" : "justify-start"}`}><div className={`max-w-[80%] rounded-2xl px-4 py-3 text-sm ${mine ? "bg-blue-600 text-white" : "bg-slate-100 text-slate-800"}`}><p>{item.body}</p><time className={`mt-1 block text-[10px] ${mine ? "text-blue-100" : "text-slate-400"}`}>{new Date(item.created_at).toLocaleString()}</time></div></div>; }) : <EmptyState>No messages yet.</EmptyState>}</div><form className="mt-6 flex gap-2" onSubmit={send}><input className="field mt-0" placeholder="Write a message..." value={body} onChange={(event) => setBody(event.target.value)} /><button className="button-primary">Send</button></form></> : <div className="flex min-h-[20rem] items-center justify-center text-sm text-slate-500">Choose a connection to start a conversation.</div>}</section></div></div>;
}
