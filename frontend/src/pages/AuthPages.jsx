import { useState } from "react";
import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ErrorMessage } from "../components/StatusMessage";

export function LoginPage() {
  const { login } = useAuth(); const navigate = useNavigate(); const [form, setForm] = useState({ email: "", password: "" }); const [error, setError] = useState("");
  const submit = async (e) => { e.preventDefault(); setError(""); try { await login(form); navigate("/"); } catch (err) { setError(err.message); } };
  return <AuthShell title="Welcome back" subtitle="Sign in to your WorkNeuron workspace."><form onSubmit={submit} className="space-y-4"><Field label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} /><Field label="Password" type="password" value={form.password} onChange={(v) => setForm({ ...form, password: v })} /><ErrorMessage message={error} /><button className="button-primary w-full">Sign in</button><p className="text-center text-sm text-slate-500">New here? <Link className="font-semibold text-brand" to="/register">Create an account</Link></p></form></AuthShell>;
}

export function RegisterPage() {
  const { register } = useAuth(); const navigate = useNavigate(); const [form, setForm] = useState({ email: "", password: "", password_confirm: "", first_name: "", last_name: "", role: "WORKER" }); const [error, setError] = useState("");
  const submit = async (e) => { e.preventDefault(); setError(""); try { await register(form); navigate("/"); } catch (err) { setError(err.message); } };
  return <AuthShell title="Build your next opportunity" subtitle="Join the skill marketplace as a client or worker."><form onSubmit={submit} className="space-y-4"><div className="grid grid-cols-2 gap-3"><Field label="First name" value={form.first_name} onChange={(v) => setForm({ ...form, first_name: v })} /><Field label="Last name" value={form.last_name} onChange={(v) => setForm({ ...form, last_name: v })} /></div><Field label="Email" type="email" value={form.email} onChange={(v) => setForm({ ...form, email: v })} /><Field label="Password" type="password" value={form.password} onChange={(v) => setForm({ ...form, password: v })} /><Field label="Confirm password" type="password" value={form.password_confirm} onChange={(v) => setForm({ ...form, password_confirm: v })} /><div><label className="label">I am a</label><select className="field" value={form.role} onChange={(e) => setForm({ ...form, role: e.target.value })}><option value="WORKER">Worker / skill provider</option><option value="CLIENT">Client / task requester</option></select></div><ErrorMessage message={error} /><button className="button-primary w-full">Create account</button><p className="text-center text-sm text-slate-500">Already registered? <Link className="font-semibold text-brand" to="/login">Sign in</Link></p></form></AuthShell>;
}

function AuthShell({ title, subtitle, children }) { return <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-blue-50 via-white to-emerald-50 px-5"><div className="w-full max-w-md"><div className="mb-8 text-center"><div className="mb-5 text-2xl font-black text-brand">work<span className="text-ink">neuron</span></div><h1 className="text-3xl font-black tracking-tight">{title}</h1><p className="mt-2 text-slate-500">{subtitle}</p></div><div className="card">{children}</div></div></div>; }
function Field({ label, type = "text", value, onChange }) { return <div><label className="label">{label}</label><input required type={type} className="field" value={value} onChange={(e) => onChange(e.target.value)} /></div>; }
