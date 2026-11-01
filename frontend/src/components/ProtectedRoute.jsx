import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import BrandLogo from "./BrandLogo";

export default function ProtectedRoute({ roles }) {
  const { user, loading } = useAuth();
  if (loading) return <main className="flex min-h-screen items-center justify-center bg-cloud px-5" role="status" aria-live="polite"><div className="flex flex-col items-center gap-5"><BrandLogo size="large" /><p className="text-sm text-slate-500">Loading your workspace…</p></div></main>;
  if (!user) return <Navigate to={roles?.[0] === "ADMIN" ? "/admin/login" : roles?.[0] === "CLIENT" ? "/client/login" : roles?.[0] === "WORKER" ? "/worker/login" : "/auth"} replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={user.role === "ADMIN" ? "/admin/dashboard" : user.role === "CLIENT" ? "/client/dashboard" : "/worker/dashboard"} replace />;
  return <Outlet />;
}
