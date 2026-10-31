import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { get, post } from "../services/api";
import { EmptyState, ErrorMessage } from "../components/StatusMessage";
import { useI18n } from "../i18n/I18nContext";
import { useAuth } from "../context/AuthContext";

export default function NetworkDiscoverPage() {
  const { t } = useI18n();
  const { user } = useAuth();
  const [query, setQuery] = useState("");
  const [people, setPeople] = useState([]);
  const [connections, setConnections] = useState([]);
  const [error, setError] = useState("");
  const load = async () => { try { const [discovered, current] = await Promise.all([get(`/network/discover/${query ? `?q=${encodeURIComponent(query)}` : ""}`), get("/network/connections/")]); setPeople(discovered); setConnections(current); } catch (err) { setError(err.message); } };
  useEffect(() => { const timer = window.setTimeout(load, 250); return () => window.clearTimeout(timer); }, [query]);
  const connect = async (id) => { try { await post("/network/connections/", { user_id: id }); await load(); } catch (err) { setError(err.message); } };
  const follow = async (id) => { try { await post(`/network/users/${id}/follow/`); await load(); } catch (err) { setError(err.message); } };
  const respond = async (id, action) => { try { await post(`/network/connections/${id}/${action}/`); await load(); } catch (err) { setError(err.message); } };
  const statusFor = (id) => connections.find((item) => item.requester.id === id || item.recipient.id === id);
  const incoming = connections.filter((item) => item.status === "PENDING" && item.recipient.id === user.id);
  return <div className="space-y-6"><header><p className="text-sm font-semibold text-brand">{t("network")}</p><h1 className="mt-1 text-3xl font-black">{t("discover")}</h1><p className="mt-2 text-slate-500">Find workers, employers, freelancers, and collaborators by skills, role, and location.</p></header><ErrorMessage message={error} /><input className="field" placeholder="Search people, skills, or location" value={query} onChange={(event) => setQuery(event.target.value)} />{incoming.length > 0 && <section className="card"><h2 className="font-bold">Connection requests</h2><div className="mt-3 space-y-2">{incoming.map((item) => <div className="flex flex-wrap items-center justify-between gap-2 rounded-xl bg-slate-50 p-3" key={item.id}><span className="text-sm">{item.requester.name} wants to connect</span><div className="flex gap-2"><button className="button-primary text-xs" onClick={() => respond(item.id, "accept")}>Accept</button><button className="button-secondary text-xs" onClick={() => respond(item.id, "decline")}>Decline</button></div></div>)}</div></section>}{people.length ? <div className="grid gap-4 md:grid-cols-2">{people.map((person) => { const relation = statusFor(person.id); return <article className="card" key={person.id}><Link to={`../people/${person.id}`} className="flex items-start gap-3 hover:text-brand"><span className="avatar">{(person.name || person.email)[0].toUpperCase()}</span><div><h2 className="font-bold">{person.name}</h2><p className="text-sm text-slate-500">{person.headline || person.role}</p><p className="text-sm text-slate-500">{person.location || "Location not provided"}</p></div></Link><div className="mt-4 flex gap-2"><button className="button-primary text-xs" disabled={Boolean(relation)} onClick={() => connect(person.id)}>{relation ? relation.status.toLowerCase() : t("connect")}</button><button className="button-secondary text-xs" onClick={() => follow(person.id)}>{t("follow")}</button></div><p className="mt-3 text-xs text-slate-400">{person.followers_count} followers · {person.connections_count} connections{person.mutual_connections?.length ? ` · ${person.mutual_connections.length} mutual` : ""}</p></article>; })}</div> : <EmptyState>{t("noPeople")}</EmptyState>}</div>;
}
