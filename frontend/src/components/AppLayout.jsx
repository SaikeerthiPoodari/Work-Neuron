import { useEffect, useState } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { useI18n } from "../i18n/I18nContext";
import ThemeToggle from "./ThemeToggle";
import AIAssistant from "./ai/AIAssistant";
import NeuralFlowBackground from "./NeuralFlowBackground";
import SidebarIcon from "./SidebarIcon";
import NotificationBell from "./NotificationBell";
import { get, refreshAccessToken } from "../services/api";

const common = [["/", "overview", "home"], ["/feed", "feed", "notes"], ["/discover", "discover", "workers"], ["/tasks", "exploreTasks", "tasks"], ["/nearby", "nearbyJobs", "nearby"], ["/assignments", "assignments", "work"], ["/network-messages", "messages", "mail"], ["/messages", "workMessages", "work"], ["/recommendations", "smartMatches", "matches"], ["/skill-graph", "skillGraph", "skills"]];
const account = [["/wallet", "walletPayments", "payments"], ["/reviews", "reviews", "reviews"], ["/payments", "payments", "payments"], ["/complaints", "support", "support"], ["/profile", "profile", "profile"], ["/notifications", "notifications", "bell"]];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const { t, language, setLanguage, availableLanguages } = useI18n();
  const navigate = useNavigate();
  const [unreadCount, setUnreadCount] = useState(0);
  const [profilePhoto, setProfilePhoto] = useState("");
  const [socketConnected, setSocketConnected] = useState(false);

  useEffect(() => {
    get("/profiles/me/").then((profile) => setProfilePhoto(profile.profile_photo || profile.profile_photo_url || "")).catch(() => setProfilePhoto(""));
  }, [user.role]);

  useEffect(() => {
    let accessToken = localStorage.getItem("workneuron_access");
    if (!accessToken) return undefined;
    let socket;
    let retryTimer;
    let stopped = false;
    let retryDelay = 1000;
    const configured = import.meta.env.VITE_WS_URL;
    const socketUrl = configured || `${window.location.protocol === "https:" ? "wss" : "ws"}://${window.location.host.replace(/:\d+$/, ":8000")}/ws/notifications/`;
    const refreshUnread = () => get("/notifications/?unread=true").then((items) => setUnreadCount(items.length)).catch(() => {});
    const handleNotification = (event) => { if (event.detail?.type === "notification") { setUnreadCount((count) => count + 1); } };
    const handleSocket = (event) => setSocketConnected(Boolean(event.detail?.connected));
    refreshUnread();
    window.addEventListener("workneuron-notification", handleNotification);
    window.addEventListener("workneuron-notification-refresh", refreshUnread);
    window.addEventListener("workneuron-socket", handleSocket);
    const connect = () => {
      if (stopped) return;
      socket = new WebSocket(`${socketUrl}${socketUrl.includes("?") ? "&" : "?"}token=${encodeURIComponent(accessToken)}`);
      socket.onopen = () => { retryDelay = 1000; window.dispatchEvent(new CustomEvent("workneuron-socket", { detail: { connected: true } })); };
      socket.onmessage = (event) => { try { window.dispatchEvent(new CustomEvent("workneuron-notification", { detail: JSON.parse(event.data) })); } catch { /* Ignore malformed frames. */ } };
      socket.onclose = (event) => {
        window.dispatchEvent(new CustomEvent("workneuron-socket", { detail: { connected: false } }));
        if (!stopped && event.code === 4401) refreshAccessToken().then((token) => { accessToken = token; retryDelay = 1000; connect(); }).catch(() => { logout(); navigate("/auth"); });
        else if (!stopped) { retryTimer = window.setTimeout(connect, retryDelay); retryDelay = Math.min(retryDelay * 2, 30000); }
      };
    };
    connect();
    return () => { stopped = true; window.clearTimeout(retryTimer); socket?.close(); window.removeEventListener("workneuron-notification", handleNotification); window.removeEventListener("workneuron-notification-refresh", refreshUnread); window.removeEventListener("workneuron-socket", handleSocket); };
  }, []);

  const prefix = `/${user.role.toLowerCase()}`;
  const scope = (items) => items.map(([to, label, icon]) => [`${prefix}${to === "/" ? "/dashboard" : to}`, label, icon]);
  const links = scope(user.role === "ADMIN" ? [["/", "overview", "home"], ["/admin", "adminConsole", "admin"], ["/complaints", "support", "support"], ["/payments", "payments", "payments"], ["/notifications", "notifications", "bell"]] : user.role === "CLIENT" ? [["/", "overview", "home"], ["/feed", "feed", "notes"], ["/discover", "discover", "workers"], ["/tasks", "taskManagement", "tasks"], ["/applications", "applications", "apps"], ["/workers", "findWorkers", "workers"], ["/network-messages", "messages", "mail"], ["/messages", "workMessages", "work"], ["/recommendations", "recommendedWorkers", "matches"], ["/assignments", "assignments", "work"], ["/payments", "payments", "payments"], ["/analytics", "analytics", "stats"]] : common);
  const accountLinks = scope(user.role === "CLIENT" ? [["/wallet", "walletPayments", "payments"], ["/verification", "verification", "verified"], ["/reviews", "reviews", "reviews"], ["/complaints", "support", "support"], ["/profile", "profile", "profile"], ["/notifications", "notifications", "bell"], ["/settings", "settings", "settings"]] : [...account.map(([to, label, icon]) => to === "/notifications" ? [to, label, "bell"] : [to, label, icon]), ["/settings", "settings", "settings"]]);
  const renderLink = ([to, label, icon]) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `nav-item ${isActive ? "nav-item-active" : ""}`}><span className="nav-icon"><SidebarIcon name={icon} /></span>{t(label)}</NavLink>;
  const avatar = profilePhoto ? <img src={profilePhoto} alt="Your profile" className="h-full w-full object-cover" /> : (user.first_name?.[0] || user.email?.[0] || "U").toUpperCase();

  return <div className="app-shell min-h-screen bg-cloud"><NeuralFlowBackground intensity="minimal" /><header className="app-header border-b border-slate-200 bg-white"><div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4"><button onClick={() => navigate(`${prefix}/dashboard`)} className="flex items-center gap-2 text-left"><span className="brand-mark">N</span><span className="text-xl font-black tracking-tight text-brand">work<span className="text-ink">neuron</span></span></button><div className="flex items-center gap-2 text-sm sm:gap-3"><span className={`hidden items-center gap-1.5 rounded-full px-2 py-1 text-[10px] font-bold sm:flex ${socketConnected ? "bg-emerald-50 text-emerald-700" : "bg-amber-50 text-amber-700"}`} aria-live="polite"><span className={`h-1.5 w-1.5 rounded-full ${socketConnected ? "bg-emerald-500" : "bg-amber-500"}`} />{socketConnected ? "Live" : "Reconnecting"}</span><ThemeToggle /><NotificationBell prefix={prefix} unreadCount={unreadCount} onUnreadChange={setUnreadCount} />{user.role === "WORKER" && <label className="sr-only" htmlFor="interface-language">{t("interfaceLanguage")}</label>}{user.role === "WORKER" && <select id="interface-language" aria-label={t("interfaceLanguage")} className="field mt-0 max-w-[9.5rem] py-2 text-xs sm:max-w-none sm:text-sm" value={language} onChange={(event) => setLanguage(event.target.value)}>{availableLanguages.map((item) => <option value={item.code} key={item.code}>{item.label}</option>)}</select>}<div className="hidden text-right sm:block"><p className="font-semibold text-ink">{user.first_name || user.email.split("@")[0]}</p><p className="text-xs text-slate-400">{t(user.role === "WORKER" ? "independentWorker" : user.role === "CLIENT" ? "taskPublisher" : "platformAdmin")}</p></div><NavLink to={`${prefix}/profile`} aria-label="Profile" className="avatar overflow-hidden ring-2 ring-white transition hover:ring-blue-300">{avatar}</NavLink><button onClick={logout} className="hidden font-semibold text-slate-500 hover:text-ink sm:block">{t("logout")}</button></div></div></header><div className="workspace-layout mx-auto flex max-w-7xl gap-8 px-5 py-8"><aside className="app-sidebar hidden w-56 shrink-0 md:block"><div className="sidebar-flow" aria-hidden="true" /><div className="relative z-10"><div className="mb-5 px-3 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">{t("workspace")}</div><nav className="space-y-1">{links.map(renderLink)}</nav>{user.role !== "ADMIN" && <><div className="mb-3 mt-8 px-3 text-[10px] font-black uppercase tracking-[0.18em] text-slate-400">{t("account")}</div><nav className="space-y-1">{accountLinks.map(renderLink)}</nav></>}</div></aside><main className="page-content min-w-0 flex-1"><Outlet /></main></div><nav className="mobile-nav md:hidden" aria-label="Primary navigation">{(user.role === "CLIENT" ? [...links, ...accountLinks] : links.slice(0, 5)).map(([to, label, icon]) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => isActive ? "text-brand" : "text-slate-400"}><SidebarIcon name={icon} /><small>{t(label).split(" ")[0]}</small></NavLink>)}</nav><AIAssistant /></div>;
}
