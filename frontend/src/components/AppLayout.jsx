import { useEffect } from "react";
import { NavLink, Outlet, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

const common = [
  ["/", "Overview"], ["/tasks", "Tasks"], ["/assignments", "Assignments"], ["/recommendations", "Recommendations"], ["/skill-graph", "Skill graph"], ["/reviews", "Reviews"], ["/payments", "Payments"], ["/complaints", "Complaints"], ["/profile", "Profile"], ["/notifications", "Notifications"],
];

export default function AppLayout() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  useEffect(() => {
    const token = localStorage.getItem("workneuron_access");
    if (!token) return undefined;
    const socketUrl = import.meta.env.VITE_WS_URL || "ws://localhost:8000/ws/notifications/";
    const socket = new WebSocket(`${socketUrl}?token=${encodeURIComponent(token)}`);
    socket.onmessage = (event) => { try { window.dispatchEvent(new CustomEvent("workneuron-notification", { detail: JSON.parse(event.data) })); } catch { /* ignore malformed socket data */ } };
    return () => socket.close();
  }, []);
  const links = user.role === "ADMIN" ? [["/", "Overview"], ["/admin", "Admin monitor"], ["/complaints", "Complaints"], ["/notifications", "Notifications"]] : common;
  return <div className="min-h-screen bg-cloud">
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-7xl items-center justify-between px-5 py-4">
        <button onClick={() => navigate("/")} className="text-xl font-black tracking-tight text-brand">work<span className="text-ink">neuron</span></button>
        <div className="flex items-center gap-4 text-sm"><span className="hidden text-slate-500 sm:block">{user.email}</span><span className="rounded-full bg-mint px-3 py-1 text-xs font-bold text-emerald-800">{user.role}</span><button onClick={logout} className="font-semibold text-slate-600 hover:text-ink">Log out</button></div>
      </div>
    </header>
    <div className="mx-auto flex max-w-7xl gap-8 px-5 py-8">
      <aside className="hidden w-48 shrink-0 md:block"><nav className="space-y-1">{links.map(([to, label]) => <NavLink key={to} to={to} end={to === "/"} className={({ isActive }) => `block rounded-xl px-3 py-2.5 text-sm font-semibold ${isActive ? "bg-blue-50 text-brand" : "text-slate-500 hover:bg-white hover:text-ink"}`}>{label}</NavLink>)}</nav></aside>
      <main className="min-w-0 flex-1"><Outlet /></main>
    </div>
  </div>;
}
