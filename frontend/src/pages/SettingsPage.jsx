import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { patch, post } from "../services/api";
import { ErrorMessage } from "../components/StatusMessage";
import { useTheme } from "../context/ThemeContext";

export default function SettingsPage() {
  const { user } = useAuth();
  const { theme, setTheme, palette, setPalette, reducedMotion, setReducedMotion } = useTheme();
  const [profile, setProfile] = useState({ first_name: user.first_name || "", last_name: user.last_name || "" });
  const [password, setPassword] = useState({ current_password: "", new_password: "", new_password_confirm: "" });
  const [notice, setNotice] = useState("");
  const [error, setError] = useState("");

  const saveProfile = async (event) => { event.preventDefault(); setError(""); try { await patch("/auth/me/", profile); setNotice("Account details saved."); } catch (err) { setError(err.message); } };
  const changePassword = async (event) => { event.preventDefault(); setError(""); try { await post("/auth/password/", password); setPassword({ current_password: "", new_password: "", new_password_confirm: "" }); setNotice("Password updated."); } catch (err) { setError(err.message); } };

  return <div className="max-w-3xl space-y-6">
    <header><p className="text-sm font-semibold text-brand">Account preferences</p><h1 className="mt-1 text-3xl font-black tracking-tight">Settings</h1><p className="mt-2 text-slate-500">Manage your account details, appearance, and password securely.</p></header>
    <ErrorMessage message={error} />
    {notice && <p className="rounded-xl bg-emerald-50 p-3 text-sm font-semibold text-emerald-700" role="status">{notice}</p>}
    <section className="card space-y-4"><div><h2 className="font-bold">Appearance</h2><p className="mt-1 text-sm text-slate-500">Preferences are saved on this device.</p></div><div className="grid gap-3 sm:grid-cols-3">
      <label className="label">Theme<select className="field" value={theme} onChange={(event) => setTheme(event.target.value)}><option value="system">System</option><option value="light">Light</option><option value="dark">Dark</option></select></label>
      <label className="label">Colour palette<select className="field" value={palette} onChange={(event) => setPalette(event.target.value)}><option value="blue">Neural blue</option><option value="aurora">Aurora teal</option><option value="indigo">Warm indigo</option></select></label>
      <label className="label">Motion<select className="field" value={reducedMotion} onChange={(event) => setReducedMotion(event.target.value)}><option value="system">System</option><option value="off">Full motion</option><option value="on">Reduced motion</option></select></label>
    </div></section>
    <form className="card space-y-4" onSubmit={saveProfile}><h2 className="font-bold">Account details</h2><div className="grid gap-3 sm:grid-cols-2"><label className="label">First name<input className="field" value={profile.first_name} onChange={(event) => setProfile({ ...profile, first_name: event.target.value })} /></label><label className="label">Last name<input className="field" value={profile.last_name} onChange={(event) => setProfile({ ...profile, last_name: event.target.value })} /></label></div><p className="text-sm text-slate-500">Email: {user.email}</p><button className="button-primary">Save details</button></form>
    <form className="card space-y-4" onSubmit={changePassword}><h2 className="font-bold">Change password</h2>{[["current_password", "Current password"], ["new_password", "New password"], ["new_password_confirm", "Confirm new password"]].map(([key, label]) => <label className="label" key={key}>{label}<input required type="password" className="field" value={password[key]} onChange={(event) => setPassword({ ...password, [key]: event.target.value })} /></label>)}<button className="button-primary">Update password</button></form>
  </div>;
}
