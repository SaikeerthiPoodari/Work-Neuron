import { Navigate, Outlet } from "react-router-dom";
import { useAuth } from "../context/AuthContext";

export default function ProtectedRoute({ roles }) {
  const { user, loading } = useAuth();
  if (loading) return <div className="p-8 text-slate-500">Loading WorkNeuron…</div>;
  if (!user) return <Navigate to={roles?.[0] === "ADMIN" ? "/admin/login" : roles?.[0] === "CLIENT" ? "/client/login" : roles?.[0] === "WORKER" ? "/worker/login" : "/auth"} replace />;
  if (roles && !roles.includes(user.role)) return <Navigate to={user.role === "ADMIN" ? "/admin/dashboard" : user.role === "CLIENT" ? "/client/dashboard" : "/worker/dashboard"} replace />;
  return <Outlet />;
}
