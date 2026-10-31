import { useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { get, post } from "../services/api";
import SidebarIcon from "./SidebarIcon";

export default function NotificationBell({ prefix, unreadCount, onUnreadChange }) {
  const [open, setOpen] = useState(false);
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");
  const container = useRef(null);
  const navigate = useNavigate();

  useEffect(() => {
    const close = (event) => { if (container.current && !container.current.contains(event.target)) setOpen(false); };
    document.addEventListener("mousedown", close);
    return () => document.removeEventListener("mousedown", close);
  }, []);

  const load = async () => {
    setLoading(true); setError("");
    try { setItems(await get("/notifications/")); } catch (err) { setError(err.message); }
    finally { setLoading(false); }
  };
  const toggle = () => { const next = !open; setOpen(next); if (next) load(); };
  const markRead = async (item) => {
    try { if (!item.read_at) { await post(`/notifications/${item.id}/read/`); setItems((current) => current.map((entry) => entry.id === item.id ? { ...entry, read_at: new Date().toISOString() } : entry)); onUnreadChange(Math.max(0, unreadCount - 1)); } if (item.related_url) navigate(`${prefix}${item.related_url.startsWith("/") ? item.related_url : `/${item.related_url}`}`); setOpen(false); }
    catch (err) { setError(err.message); }
  };
  const markAll = async () => {
    try { await post("/notifications/read-all/"); setItems((current) => current.map((item) => ({ ...item, read_at: item.read_at || new Date().toISOString() }))); onUnreadChange(0); }
    catch (err) { setError(err.message); }
  };

  return <div className="relative" ref={container}>
    <button type="button" onClick={toggle} aria-label="Notifications" aria-expanded={open} className="relative rounded-xl p-2 text-slate-500 hover:bg-blue-50 hover:text-brand"><SidebarIcon name="bell" />{unreadCount > 0 && <span className="absolute -right-1 -top-1 min-w-4 rounded-full bg-red-500 px-1 text-center text-[10px] font-black leading-4 text-white">{unreadCount > 99 ? "99+" : unreadCount}</span>}</button>
    {open && <div className="absolute right-0 top-12 z-50 w-[min(22rem,calc(100vw-2rem))] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-xl"><div className="flex items-center justify-between border-b border-slate-100 px-4 py-3"><div><h2 className="font-black text-ink">Notifications</h2><p className="text-xs text-slate-500">{unreadCount ? `${unreadCount} unread` : "All caught up"}</p></div>{unreadCount > 0 && <button className="text-xs font-bold text-brand hover:underline" onClick={markAll}>Mark all read</button>}</div><div className="max-h-96 overflow-y-auto p-2">{error && <p className="p-3 text-xs text-red-600">{error}</p>}{loading ? <p className="p-4 text-sm text-slate-500">Loading notifications...</p> : items.length ? items.map((item) => <button type="button" key={item.id} onClick={() => markRead(item)} className={`block w-full rounded-xl p-3 text-left hover:bg-blue-50 ${item.read_at ? "" : "bg-blue-50/60"}`}><span className="flex items-start gap-2"><span className={`mt-1.5 h-2 w-2 shrink-0 rounded-full ${item.read_at ? "bg-slate-200" : "bg-brand"}`} /><span><b className="block text-sm text-ink">{item.title}</b><span className="mt-1 block text-xs leading-5 text-slate-500">{item.message}</span><span className="mt-1 block text-[10px] text-slate-400">{item.created_at ? new Date(item.created_at).toLocaleString() : ""}</span></span></span></button>) : <p className="p-4 text-sm text-slate-500">No notifications yet.</p>}</div><button type="button" className="w-full border-t border-slate-100 px-4 py-3 text-center text-xs font-bold text-brand hover:bg-blue-50" onClick={() => { setOpen(false); navigate(`${prefix}/notifications`); }}>View all notifications</button></div>}
  </div>;
}
