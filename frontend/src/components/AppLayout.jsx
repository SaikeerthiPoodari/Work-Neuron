import { useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useI18n } from "../i18n/I18nContext";

const common = [["/", "overview", "⌂"], ["/tasks", "exploreTasks", "◈"], ["/nearby", "nearbyJobs", "⌖"], ["/assignments", "assignments", "↗"], ["/recommendations", "smartMatches", "✦"], ["/skill-graph", "skillGraph", "⌁"]];
const account = [["/reviews", "reviews", "★"], ["/payments", "payments", "◌"], ["/complaints", "support", "!"], ["/profile", "profile", "○"], ["/notifications", "notifications", "•"]];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { t } = useI18n();
  const navigate = useNavigate();
  useEffect(() => {
    const token = localStorage.getItem("workneuron_access");
    if (!token) return undefined;
    const socketUrl = import.meta.env.VITE_WS_URL || "ws://127.0.0.1:8000/ws/notifications/";
    const socket = new WebSocket(`${socketUrl}?token=${encodeURIComponent(token)}`);
    socket.onmessage = (event) => { try { window.dispatchEvent(new CustomEvent("workneuron-notification", { detail: JSON.parse(event.data) })); } catch { /* ignore malformed socket data */ } };
    return () => socket.close();
  }, []);
  const links = user.role === "ADMIN" ? [["/", "overview", "⌂"], ["/admin", "adminMonitor", "▦"], ["/complaints", "complaints", "!"], ["/notifications", "notifications", "•"]] : common;
  const accountLinks = user.role === "CLIENT" ? [["/verification", "verification", "✓"], ...account] : account;
  return <div className="min-h-screen bg-cloud">
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <button onClick={() => navigate("/")} className="flex items-center gap-2 text-left"><span className="brand-mark">N</span><span className="text-xl font-black tracking-tight text-brand">work<span className="text-ink">neuron</span></span></button>
        <div className="flex items-center gap-3 text-sm"><div className="hidden text-right sm:block"><p className="font-semibold text-ink">{user.first_name || user.email.split("@")[0]}</p><p className="text-xs text-slate-400">{t(user.role === "WORKER" ? "independentWorker" : user.role === "CLIENT" ? "taskPublisher" : "platformAdmin")}</p></div><span className="avatar">{(user.first_name || user.email)[0].toUpperCase()}</span><button onClick={logout} className="hidden font-semibold text-slate-500 hover:text-ink sm:block">{t("logout")}</button></div>
      </div>
    </header>
    <div className="mx-auto flex max-w-7xl gap-8 px-5 py-8">
      <aside className="hidden w-56 shrink-0 md:block"><div className="mb-5 px-3 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">{t("workspace")}</div><nav className="space-y-1">{links.map(([to, label, icon]) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}><span className="nav-icon">{icon}</span>{t(label)}</NavLink>)}</nav>{user.role !== "ADMIN" && <><div className="mb-3 mt-8 px-3 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">{t("account")}</div><nav className="space-y-1">{accountLinks.map(([to, label, icon]) => <NavLink key={to} to={to} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}><span className="nav-icon">{icon}</span>{t(label)}</NavLink>)}</nav></>}</aside>
      <main className="min-w-0 flex-1"><Outlet /></main>
    </div>
    <nav className="mobile-nav md:hidden">{links.slice(0, 5).map(([to, label, icon]) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => isActive ? "text-brand" : "text-slate-400"}><span>{icon}</span><small>{t(label).split(" ")[0]}</small></NavLink>)}</nav>
  </div>;
}
