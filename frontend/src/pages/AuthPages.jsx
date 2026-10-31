import { useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { ErrorMessage } from "../components/StatusMessage";
import ThemeToggle from "../components/ThemeToggle";
import NeuralFlowBackground from "../components/NeuralFlowBackground";

const roles = {
  WORKER: { name: "Worker", path: "worker", title: "WORKER LOGIN", description: "Find jobs, apply for tasks, complete work and earn.", icon: "👷" },
  CLIENT: { name: "Client / Employer", path: "client", title: "CLIENT / EMPLOYER LOGIN", description: "Post jobs, find workers, manage tasks and hire talent.", icon: "🏢" },
  ADMIN: { name: "Admin", path: "admin", title: "ADMIN LOGIN", description: "Manage and monitor the WorkNeuron platform.", icon: "🔐" },
};

export function AuthLanding() {
  return <div className="auth-page relative min-h-screen px-5 py-12 sm:py-20"><NeuralFlowBackground intensity="hero" /><div className="absolute right-5 top-5 z-10"><ThemeToggle /></div><div className="relative z-10 mx-auto max-w-5xl"><AuthBrand /><div className="mb-10 text-center"><p className="eyebrow">People · Skills · Intelligence · Work</p><h1 className="mt-3 text-4xl font-black tracking-tight sm:text-6xl">A living network for <span className="text-gradient">meaningful work.</span></h1><p className="mx-auto mt-4 max-w-2xl text-lg text-slate-500">Find work. Hire talent. Get things done — with intelligent connections moving quietly beneath every opportunity.</p></div><div className="grid gap-5 md:grid-cols-3">{["WORKER", "CLIENT", "ADMIN"].map((role) => <RoleCard key={role} role={role} />)}</div><p className="mt-8 text-center text-sm text-slate-500">Forgot your password? <Link className="font-semibold text-brand" to="/password-reset">Recover your account</Link></p></div></div>;
}

function RoleCard({ role }) {
  const config = roles[role];
  return <section className="card neural-card flex flex-col p-6"><div className="mb-5 flex items-center gap-3"><span className="role-icon" aria-hidden="true">{config.icon}</span><h2 className="text-xl font-black">{config.name}</h2></div><p className="min-h-12 text-sm leading-6 text-slate-500">{config.description}</p><div className="mt-auto space-y-3 pt-7"><Link className="button-primary block w-full text-center" to={`/${config.path}/login`}>{role === "ADMIN" ? "Admin Login" : `Login as ${config.name.split(" ")[0]}`}</Link>{role !== "ADMIN" && <Link className="button-secondary block w-full text-center" to={`/${config.path}/register`}>Register as {config.name.split(" ")[0]}</Link>}</div></section>;
}

export function LoginPage({ role }) {
  const config = roles[role];
  const { login } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "" });
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault(); setError("");
    try { const user = await login({ ...form, role }); navigate(user.role === "ADMIN" ? "/admin/dashboard" : user.role === "CLIENT" ? "/client/dashboard" : "/worker/dashboard"); } catch (err) { setError(err.message); }
  };
  return <AuthShell title={config.title} subtitle={`Sign in to your ${config.name.toLowerCase()} workspace.`}><form onSubmit={submit} className="space-y-4"><Field label="Email / Username" type="email" value={form.email} onChange={(value) => setForm({ ...form, email: value })} /><Field label="Password" type="password" value={form.password} onChange={(value) => setForm({ ...form, password: value })} /><ErrorMessage message={error} /><button className="button-primary w-full">Login</button><div className="flex justify-between text-sm"><Link className="font-semibold text-brand" to="/auth">Choose account type</Link><Link className="font-semibold text-brand" to="/password-reset">Forgot Password?</Link></div>{role !== "ADMIN" && <p className="text-center text-sm text-slate-500">{role === "WORKER" ? "Are you a Client/Employer?" : "Are you a Worker?"} <Link className="font-semibold text-brand" to={`/${role === "WORKER" ? "client" : "worker"}/login`}>Login as {role === "WORKER" ? "Client" : "Worker"}</Link></p>}{role !== "ADMIN" && <p className="text-center text-sm text-slate-500">Don't have a {config.name} account? <Link className="font-semibold text-brand" to={`/${config.path}/register`}>Register</Link></p>}</form></AuthShell>;
}

export function RegisterPage({ role }) {
  const config = roles[role];
  const { register } = useAuth();
  const navigate = useNavigate();
  const [form, setForm] = useState({ email: "", password: "", password_confirm: "", first_name: "", last_name: "", phone: "", organization_name: "", employer_type: "" });
  const [error, setError] = useState("");
  const update = (key) => (value) => setForm((current) => ({ ...current, [key]: value }));
  const submit = async (event) => { event.preventDefault(); setError(""); try { await register({ ...form, role }); navigate(`/${config.path}/dashboard`); } catch (err) { setError(err.message); } };
  return <AuthShell title={role === "WORKER" ? "CREATE WORKER ACCOUNT" : "CREATE CLIENT / EMPLOYER ACCOUNT"} subtitle={role === "WORKER" ? "Build your profile and find your next opportunity." : "Create an employer workspace to post jobs and hire talent."}><form onSubmit={submit} className="space-y-4"><div className="grid grid-cols-2 gap-3"><Field label="First name" value={form.first_name} onChange={update("first_name")} /><Field label="Last name" value={form.last_name} onChange={update("last_name")} /></div><Field label="Email" type="email" value={form.email} onChange={update("email")} /><Field label="Phone" type="tel" value={form.phone} onChange={update("phone")} />{role === "CLIENT" && <><Field label="Business / Organization name" value={form.organization_name} onChange={update("organization_name")} /><div><label className="label">Business type</label><select required className="field" value={form.employer_type} onChange={(event) => update("employer_type")(event.target.value)}><option value="">Select business type</option>{["COMPANY", "STORE", "RESTAURANT", "MALL", "SUPERMARKET", "EVENT_ORGANIZER", "CALL_CENTER", "DELIVERY_BUSINESS", "RECRUITER", "LOCAL_BUSINESS"].map((type) => <option key={type} value={type}>{type.replaceAll("_", " ")}</option>)}</select></div></>}<Field label="Password" type="password" value={form.password} onChange={update("password")} /><Field label="Confirm password" type="password" value={form.password_confirm} onChange={update("password_confirm")} /><ErrorMessage message={error} /><button className="button-primary w-full">Create account</button><p className="text-center text-sm text-slate-500">Already have an account? <Link className="font-semibold text-brand" to={`/${config.path}/login`}>{config.name} Login</Link></p></form></AuthShell>;
}

function AuthBrand() { return <div className="mb-8 text-center text-2xl font-black text-brand">work<span className="text-ink">neuron</span></div>; }
function AuthShell({ title, subtitle, children }) { return <div className="auth-page relative flex min-h-screen items-center justify-center px-5 py-10"><NeuralFlowBackground intensity="ambient" /><div className="absolute right-5 top-5 z-10"><ThemeToggle /></div><div className="relative z-10 w-full max-w-md"><AuthBrand /><div className="mb-8 text-center"><p className="eyebrow">Secure workspace access</p><h1 className="mt-2 text-3xl font-black tracking-tight">{title}</h1><p className="mt-2 text-slate-500">{subtitle}</p></div><div className="card auth-card">{children}</div></div></div>; }
function Field({ label, type = "text", value, onChange }) { return <div><label className="label">{label}</label><input required type={type} className="field" value={value} onChange={(event) => onChange(event.target.value)} /></div>; }
