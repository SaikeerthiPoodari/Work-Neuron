import { useState } from "react";
import { Link, useParams } from "react-router-dom";
import { post } from "../services/api";
import { ErrorMessage } from "../components/StatusMessage";
import ThemeToggle from "../components/ThemeToggle";
import NeuralFlowBackground from "../components/NeuralFlowBackground";

export function PasswordResetRequestPage() {
  const [email, setEmail] = useState("");
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault(); setError(""); setNotice("");
    try { const response = await post("/auth/password-reset/", { email }); setNotice(response.detail); } catch (err) { setError(err.message); }
  };
  return <RecoveryShell title="Reset your password" subtitle="Enter your account email and we will send recovery instructions."><form onSubmit={submit} className="space-y-4"><label className="label" htmlFor="reset-email">Email<input id="reset-email" required type="email" className="field" value={email} onChange={(event) => setEmail(event.target.value)} /></label><ErrorMessage message={error} />{notice && <p role="status" className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p>}<button className="button-primary w-full">Send reset instructions</button><Link className="block text-center text-sm font-semibold text-brand" to="/auth">Back to login</Link></form></RecoveryShell>;
}

export function PasswordResetConfirmPage() {
  const { uid, token } = useParams();
  const [form, setForm] = useState({ new_password: "", new_password_confirm: "" });
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");
  const submit = async (event) => {
    event.preventDefault(); setError(""); setNotice("");
    try { const response = await post("/auth/password-reset/confirm/", { uid, token, ...form }); setNotice(response.detail); } catch (err) { setError(err.message); }
  };
  return <RecoveryShell title="Choose a new password" subtitle="Use at least eight characters, then sign in again."><form onSubmit={submit} className="space-y-4"><label className="label" htmlFor="new-password">New password<input id="new-password" required minLength="8" type="password" className="field" value={form.new_password} onChange={(event) => setForm({ ...form, new_password: event.target.value })} /></label><label className="label" htmlFor="confirm-password">Confirm password<input id="confirm-password" required minLength="8" type="password" className="field" value={form.new_password_confirm} onChange={(event) => setForm({ ...form, new_password_confirm: event.target.value })} /></label><ErrorMessage message={error} />{notice ? <><p role="status" className="rounded-xl bg-emerald-50 p-3 text-sm text-emerald-700">{notice}</p><Link className="button-primary block w-full text-center" to="/auth">Continue to login</Link></> : <button className="button-primary w-full">Reset password</button>}</form></RecoveryShell>;
}

function RecoveryShell({ title, subtitle, children }) { return <div className="auth-page relative flex min-h-screen items-center justify-center px-5 py-10"><NeuralFlowBackground intensity="ambient" /><div className="absolute right-5 top-5 z-10"><ThemeToggle /></div><div className="relative z-10 w-full max-w-md"><div className="mb-8 text-center text-2xl font-black text-brand">work<span className="text-ink">neuron</span></div><div className="mb-8 text-center"><p className="eyebrow">Secure workspace access</p><h1 className="mt-2 text-3xl font-black tracking-tight">{title}</h1><p className="mt-2 text-slate-500">{subtitle}</p></div><div className="card auth-card">{children}</div></div></div>; }
