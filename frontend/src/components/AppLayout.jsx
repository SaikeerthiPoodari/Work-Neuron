import { useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useI18n } from "../i18n/I18nContext";
import ThemeToggle from "./ThemeToggle";
import AIAssistant from "./ai/AIAssistant";
import NeuralFlowBackground from "./NeuralFlowBackground";

const common = [["/", "overview", "⌂"], ["/tasks", "exploreTasks", "◈"], ["/nearby", "nearbyJobs", "⌖"], ["/assignments", "assignments", "↗"], ["/recommendations", "smartMatches", "✦"], ["/skill-graph", "skillGraph", "⌁"]];
const account = [["/reviews", "reviews", "★"], ["/payments", "payments", "◌"], ["/complaints", "support", "!"], ["/profile", "profile", "○"], ["/notifications", "notifications", "•"]];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { t, language, setLanguage, availableLanguages } = useI18n();
  const navigate = useNavigate();
  useEffect(() => {
    const token = localStorage.getItem("workneuron_access");
    if (!token) return undefined;
    const socketUrl = import.meta.env.VITE_WS_URL || "ws://127.0.0.1:8000/ws/notifications/";
    const socket = new WebSocket(`${socketUrl}?token=${encodeURIComponent(token)}`);
    socket.onmessage = (event) => { try { window.dispatchEvent(new CustomEvent("workneuron-notification", { detail: JSON.parse(event.data) })); } catch { /* ignore malformed socket data */ } };
    return () => socket.close();
  }, []);
  const prefix = `/${user.role.toLowerCase()}`;
  const scope = (items) => items.map(([to, label, icon]) => [`${prefix}${to === "/" ? "/dashboard" : to}`, label, icon]);
  const links = scope(user.role === "ADMIN" ? [["/", "overview", "⌂"], ["/complaints", "complaints", "!"], ["/notifications", "notifications", "•"]] : user.role === "CLIENT" ? [["/", "overview", "⌂"], ["/tasks", "taskManagement", "◈"], ["/applications", "applications", "▤"], ["/workers", "findWorkers", "♙"], ["/messages", "messages", "✉"], ["/recommendations", "recommendedWorkers", "✦"], ["/assignments", "assignments", "↗"], ["/payments", "payments", "◌"], ["/analytics", "analytics", "◫"]] : common);
  const accountLinks = scope(user.role === "CLIENT" ? [["/verification", "verification", "✓"], ["/reviews", "reviews", "★"], ["/complaints", "support", "!"], ["/profile", "profile", "○"], ["/notifications", "notifications", "•"], ["/settings", "settings", "⚙"]] : [...account, ["/settings", "settings", "⚙"]]);
  return <div className="app-shell min-h-screen bg-cloud">
    <NeuralFlowBackground intensity="minimal" />
    <header className="app-header border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <button onClick={() => navigate(`${prefix}/dashboard`)} className="flex items-center gap-2 text-left"><span className="brand-mark">N</span><span className="text-xl font-black tracking-tight text-brand">work<span className="text-ink">neuron</span></span></button>
        <div className="flex items-center gap-2 text-sm sm:gap-3"><ThemeToggle />{user.role === "WORKER" && <label className="sr-only" htmlFor="interface-language">{t("interfaceLanguage")}</label>}{user.role === "WORKER" && <select id="interface-language" aria-label={t("interfaceLanguage")} className="field mt-0 max-w-[9.5rem] py-2 text-xs sm:max-w-none sm:text-sm" value={language} onChange={(event) => setLanguage(event.target.value)}>{availableLanguages.map((item) => <option value={item.code} key={item.code}>{item.label}</option>)}</select>}<div className="hidden text-right sm:block"><p className="font-semibold text-ink">{user.first_name || user.email.split("@")[0]}</p><p className="text-xs text-slate-400">{t(user.role === "WORKER" ? "independentWorker" : user.role === "CLIENT" ? "taskPublisher" : "platformAdmin")}</p></div><span className="avatar">{(user.first_name || user.email)[0].toUpperCase()}</span><button onClick={logout} className="hidden font-semibold text-slate-500 hover:text-ink sm:block">{t("logout")}</button></div>
      </div>
    </header>
    <div className="workspace-layout mx-auto flex max-w-7xl gap-8 px-5 py-8">
      <aside className="app-sidebar hidden w-56 shrink-0 md:block"><div className="sidebar-flow" aria-hidden="true" /><div className="relative z-10"><div className="mb-5 px-3 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">{t("workspace")}</div><nav className="space-y-1">{links.map(([to, label, icon]) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}><span className="nav-icon">{icon}</span>{t(label)}</NavLink>)}</nav>{user.role !== "ADMIN" && <><div className="mb-3 mt-8 px-3 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">{t("account")}</div><nav className="space-y-1">{accountLinks.map(([to, label, icon]) => <NavLink key={to} to={to} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}><span className="nav-icon">{icon}</span>{t(label)}</NavLink>)}</nav></>}</div></aside>
      <main className="page-content min-w-0 flex-1"><Outlet /></main>
    </div>
    <nav className="mobile-nav md:hidden" aria-label="Primary navigation">{(user.role === "CLIENT" ? [...links, ...accountLinks] : links.slice(0, 5)).map(([to, label, icon]) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => isActive ? "text-brand" : "text-slate-400"}><span>{icon}</span><small>{t(label).split(" ")[0]}</small></NavLink>)}</nav>
    <AIAssistant /></div>;
}
