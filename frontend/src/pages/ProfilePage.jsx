import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { get, patch, post, remove } from "../services/api";
import { ErrorMessage } from "../components/StatusMessage";
import { languages, languageLabels } from "../i18n/languages";
import { useI18n } from "../i18n/I18nContext";
import ProfileNetworkPanel from "../components/ProfileNetworkPanel";

export default function ProfilePage() {
  const { user } = useAuth();
  const { t } = useI18n();
  const [profile, setProfile] = useState(null);
  const [skills, setSkills] = useState([]);
  const [catalog, setCatalog] = useState([]);
  const [skillId, setSkillId] = useState("");
  const [photoFile, setPhotoFile] = useState(null);
  const [photoPreview, setPhotoPreview] = useState("");
  const [error, setError] = useState("");
  const load = async () => {
    try {
      setProfile(await get("/profiles/me/"));
      if (user.role === "WORKER") {
        const [mine, all] = await Promise.all([get("/skills/mine/"), get("/skills/")]);
        setSkills(mine); setCatalog(all);
      }
    } catch (err) { setError(err.message); }
  };
  useEffect(() => { load(); }, []);
  useEffect(() => { if (!photoFile) { setPhotoPreview(""); return undefined; } const url = URL.createObjectURL(photoFile); setPhotoPreview(url); return () => URL.revokeObjectURL(url); }, [photoFile]);
  if (!profile) return <div className="py-10 text-slate-500" role="status">Loading profile…</div>;
  if (user.role === "CLIENT") return <div className="mx-auto w-full max-w-7xl space-y-6"><ProfileShowcaseHeader user={user} profile={profile} /><div className="grid items-start gap-6 lg:grid-cols-[minmax(0,1fr)_20rem]"><div className="min-w-0 space-y-6"><ClientProfilePhoto profile={profile} onSaved={setProfile} /><CoverImageEditor profile={profile} onSaved={setProfile} /><ClientProfileEditor profile={profile} onSaved={setProfile} /><PayoutDetails profile={profile} onSaved={setProfile} client /></div><aside className="min-w-0"><ProfileNetworkPanel user={user} /></aside></div></div>;
  const save = async (event) => {
    event.preventDefault(); setError("");
    try {
      // File fields are uploaded separately as multipart FormData. The API
      // returns their URLs in profile responses, so never send those URLs back
      // as if they were new files during a normal JSON profile update.
      const { email, id, updated_at, profile_photo, profile_photo_url, cover_image, ...payload } = profile;
      let saved = await patch("/profiles/me/", payload);
      if (photoFile) { const upload = new FormData(); upload.append("profile_photo", photoFile); saved = await patch("/profiles/me/", upload); setPhotoFile(null); }
      setProfile(saved);
    } catch (err) { setError(err.message); }
  };
  const addSkill = async () => {
    try { await post("/skills/mine/", { skill: Number(skillId), proficiency: 3, years_experience: 0 }); setSkillId(""); await load(); }
    catch (err) { setError(err.message); }
  };
  const fields = Object.entries(profile).filter(([key]) => !["id", "email", "updated_at", "profile_photo", "profile_photo_url"].includes(key) && typeof profile[key] !== "object");
  return <div className="mx-auto w-full max-w-7xl space-y-6">
    <ProfileShowcaseHeader user={user} profile={profile} />
    <CoverImageEditor profile={profile} onSaved={setProfile} />
    <div><p className="text-sm font-semibold text-brand">{user.role === "WORKER" ? t("profile") : "Your identity"}</p><h1 className="mt-1 text-3xl font-black">{user.role === "WORKER" ? t("profile") : "Profile"}</h1><p className="mt-2 text-slate-500">{user.role === "WORKER" ? t("profileHint") : "Keep your worker profile and job matching information up to date."}</p></div>
    {user.role === "WORKER" && <div className="card flex flex-col items-start gap-4 sm:flex-row sm:items-center"><div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full bg-blue-50 text-xl font-black text-brand">{photoPreview || profile.profile_photo || profile.profile_photo_url ? <img src={photoPreview || profile.profile_photo || profile.profile_photo_url} alt="Worker profile" className="h-full w-full object-cover" /> : `${user.first_name?.[0] || "W"}${user.last_name?.[0] || ""}`}</div><div className="w-full"><h2 className="font-bold">Profile photo</h2><p className="mt-1 text-sm text-slate-500">Upload a JPG, PNG or WebP image, up to 5 MB.</p><input className="field mt-3 max-w-md" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => { const file = event.target.files?.[0]; if (!file) return; if (!["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > 5 * 1024 * 1024) { setError("Choose a JPG, PNG or WebP image up to 5 MB."); event.target.value = ""; return; } setError(""); setPhotoFile(file); }} /></div></div>}
    <form onSubmit={save} className="card grid gap-4 md:grid-cols-2"><div className="md:col-span-2"><label className="label">Email</label><p className="mt-2 text-sm text-slate-600">{profile.email}</p></div>{fields.map(([key, value]) => <div key={key}><label className="label" htmlFor={`profile-${key}`}>{key.replaceAll("_", " ")}</label>{key === "bio" || key === "interests" ? <textarea id={`profile-${key}`} className="field" rows="4" value={value || ""} onChange={(event) => setProfile({ ...profile, [key]: event.target.value })} /> : key === "availability" ? <select id={`profile-${key}`} className="field" value={value || "FLEXIBLE"} onChange={(event) => setProfile({ ...profile, [key]: event.target.value })}><option value="FLEXIBLE">Flexible</option><option value="FULL_TIME">Full time</option><option value="PART_TIME">Part time</option><option value="WEEKENDS">Weekends</option></select> : <input id={`profile-${key}`} className="field" type={key.endsWith("url") ? "url" : "text"} value={value || ""} onChange={(event) => setProfile({ ...profile, [key]: event.target.value })} />}</div>)}{user.role === "WORKER" && <div className="md:col-span-2"><label className="label" htmlFor="profile-languages">Languages</label><p className="mb-2 text-xs text-slate-500">Select all languages you can use for work. Use Ctrl or Command to select multiple.</p><select id="profile-languages" multiple size="7" className="field" value={profile.languages || []} onChange={(event) => setProfile({ ...profile, languages: [...event.target.selectedOptions].map((option) => option.value) })}>{languages.map(({ code, label }) => <option value={code} key={code}>{label}</option>)}</select><div className="mt-2 flex flex-wrap gap-2">{(profile.languages || []).map((code) => <span key={code} className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-brand">{languageLabels[code] || code}</span>)}</div></div>}<div className="md:col-span-2"><ErrorMessage message={error} /><button className="button-primary mt-3">Save profile</button></div></form>
    {user.role === "WORKER" && <section className="card"><h2 className="text-lg font-bold">Skills</h2><div className="mt-4 flex flex-wrap gap-2">{skills.map((item) => <span className="rounded-full bg-blue-50 px-3 py-1.5 text-sm font-semibold text-brand" key={item.id}>{item.skill_name}<button type="button" aria-label={`Remove ${item.skill_name}`} className="ml-2 text-blue-400" onClick={() => remove(`/skills/mine/${item.id}/`).then(load).catch((err) => setError(err.message))}>×</button></span>)}</div><div className="mt-5 flex flex-col gap-2 sm:flex-row"><select className="field mt-0 max-w-xs" value={skillId} onChange={(event) => setSkillId(event.target.value)}><option value="">Add a skill…</option>{catalog.filter((skill) => !skills.some((mine) => mine.skill === skill.id)).map((skill) => <option value={skill.id} key={skill.id}>{skill.name}</option>)}</select><button type="button" className="button-secondary" disabled={!skillId} onClick={addSkill}>Add skill</button></div></section>}
    {user.role === "WORKER" && <PayoutDetails profile={profile} onSaved={setProfile} />}
    <ProfileNetworkPanel user={user} />
  </div>;
}

function ProfileShowcaseHeader({ user, profile }) {
  const image = profile.profile_photo || profile.profile_photo_url;
  const displayName = user.role === "CLIENT" ? profile.organization_name || user.email : [user.first_name, user.last_name].filter(Boolean).join(" ") || user.email;
  return <section className="card overflow-hidden p-0 shadow-sm"><div className="relative h-40 overflow-hidden bg-[radial-gradient(circle_at_20%_20%,rgba(255,255,255,.3),transparent_28%),linear-gradient(120deg,#0b3b91,#155eef_55%,#06b6d4)]">{profile.cover_image && <img src={profile.cover_image} alt="" className="h-full w-full object-cover" />}<div className="absolute inset-0 bg-gradient-to-t from-slate-950/50 to-transparent" /></div><div className="relative px-5 pb-5 sm:px-8"><div className="-mt-14 flex flex-col gap-4 sm:flex-row sm:items-end"><div className="flex h-28 w-28 shrink-0 items-center justify-center overflow-hidden rounded-full border-4 border-white bg-blue-50 text-3xl font-black text-brand shadow-lg">{image ? <img src={image} alt={displayName} className="h-full w-full object-cover" /> : displayName?.[0]?.toUpperCase()}</div><div className="min-w-0 flex-1"><p className="text-xs font-black uppercase tracking-widest text-brand">{user.role === "WORKER" ? "WorkNeuron professional" : "WorkNeuron employer"}</p><h1 className="mt-1 truncate text-2xl font-black">{displayName}</h1><p className="mt-1 text-slate-600">{profile.headline || profile.employer_type || "Build your professional presence"}</p><p className="mt-1 text-sm text-slate-500">{profile.location || profile.current_city || "Location not provided"}</p></div><span className="rounded-full bg-blue-50 px-3 py-2 text-xs font-black text-brand">{profile.profile_completion || 0}% complete</span></div></div></section>;
}

function ClientProfileEditor({ profile, onSaved }) {
  const [form, setForm] = useState(profile);
  const [error, setError] = useState("");
  const [saved, setSaved] = useState(false);
  const employerTypes = [
    ["COMPANY", "Company"], ["STORE", "Store"], ["RESTAURANT", "Restaurant"], ["MALL", "Mall"],
    ["SUPERMARKET", "Supermarket"], ["EVENT_ORGANIZER", "Event organizer"], ["CALL_CENTER", "Call center"],
    ["DELIVERY_BUSINESS", "Delivery business"], ["RECRUITER", "Recruiter"], ["LOCAL_BUSINESS", "Local business"],
  ];
  const save = async (event) => {
    event.preventDefault();
    setError("");
    setSaved(false);
    try {
      // Keep the existing file URL out of the JSON update; cover uploads use
      // the dedicated multipart upload control below.
      const { id, email, updated_at, profile_photo, cover_image, ...payload } = form;
      const updated = await patch("/profiles/me/", payload);
      setForm(updated);
      onSaved(updated);
      setSaved(true);
    } catch (err) {
      setError(err.message);
    }
  };
  const update = (key, value) => setForm((current) => ({ ...current, [key]: value }));
  return <div className="max-w-3xl space-y-6"><header><p className="text-sm font-semibold text-brand">Business identity</p><h1 className="mt-1 text-3xl font-black">Employer profile</h1><p className="mt-2 text-sm text-slate-500">These profile details are used on your employer account. Verification records are managed separately.</p></header><form onSubmit={save} className="card grid gap-4 md:grid-cols-2"><div className="md:col-span-2"><label className="label">Email</label><p className="mt-2 text-sm text-slate-600">{profile.email}</p></div><label className="label">Organization / business name<input className="field" value={form.organization_name || ""} onChange={(event) => update("organization_name", event.target.value)} /></label><label className="label">Business type<select className="field" value={form.employer_type || ""} onChange={(event) => update("employer_type", event.target.value)}><option value="">Choose a business type</option>{employerTypes.map(([value, label]) => <option value={value} key={value}>{label}</option>)}</select></label><label className="label">Contact phone<input className="field" type="tel" value={form.phone || ""} onChange={(event) => update("phone", event.target.value)} /></label><label className="label">Website<input className="field" type="url" value={form.website || ""} onChange={(event) => update("website", event.target.value)} /></label><label className="label md:col-span-2">Business location<input className="field" value={form.location || ""} onChange={(event) => update("location", event.target.value)} placeholder="Address or city" /></label><label className="label md:col-span-2">Description<textarea className="field" rows="4" value={form.bio || ""} onChange={(event) => update("bio", event.target.value)} /></label><div className="md:col-span-2"><ErrorMessage message={error} />{saved && <p role="status" className="mb-3 text-sm text-emerald-700">Profile saved.</p>}<button className="button-primary">Save profile</button></div></form><p className="text-xs text-slate-500">The current profile API does not support a logo upload, separate name editing, or structured address fields.</p></div>;
}

function ClientProfilePhoto({ profile, onSaved }) {
  const [file, setFile] = useState(null);
  const [error, setError] = useState("");
  const [preview, setPreview] = useState("");
  const upload = async () => {
    if (!file) return;
    try { const body = new FormData(); body.append("profile_photo", file); const saved = await patch("/profiles/me/", body); onSaved(saved); setFile(null); setPreview(""); } catch (err) { setError(err.message); }
  };
  return <section className="card flex flex-col items-start gap-4 sm:flex-row sm:items-center"><div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full bg-blue-50 text-xl font-black text-brand">{preview || profile.profile_photo ? <img src={preview || profile.profile_photo} alt="Profile" className="h-full w-full object-cover" /> : "U"}</div><div className="w-full"><h2 className="font-bold">Profile photo</h2><p className="mt-1 text-sm text-slate-500">Upload a JPG, PNG or WebP image, up to 5 MB.</p><div className="mt-3 flex flex-wrap gap-2"><input className="field mt-0 max-w-md" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => { const selected = event.target.files?.[0]; if (!selected) return; if (!["image/jpeg", "image/png", "image/webp"].includes(selected.type) || selected.size > 5 * 1024 * 1024) { setError("Choose a JPG, PNG or WebP image up to 5 MB."); return; } setFile(selected); setPreview(URL.createObjectURL(selected)); }} /><button type="button" className="button-secondary" disabled={!file} onClick={upload}>Save photo</button></div><ErrorMessage message={error} /></div></section>;
}

function CoverImageEditor({ profile, onSaved }) {
  const [file, setFile] = useState(null); const [error, setError] = useState("");
  const upload = async () => { if (!file) return; try { const body = new FormData(); body.append("cover_image", file); onSaved(await patch("/profiles/me/", body)); setFile(null); } catch (err) { setError(err.message); } };
  return <section className="card overflow-hidden p-0"><div className="h-28 bg-gradient-to-r from-blue-700 via-brand to-cyan-500" style={profile.cover_image ? { backgroundImage: `url(${profile.cover_image})`, backgroundPosition: "center", backgroundSize: "cover" } : undefined} /><div className="p-4"><h2 className="font-bold">Cover image</h2><p className="mt-1 text-sm text-slate-500">Upload a professional banner image, up to 8 MB.</p><div className="mt-3 flex flex-wrap gap-2"><input className="field mt-0 max-w-md" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => { const selected = event.target.files?.[0]; if (!selected) return; if (!["image/jpeg", "image/png", "image/webp"].includes(selected.type) || selected.size > 8 * 1024 * 1024) { setError("Choose a JPG, PNG or WebP image up to 8 MB."); return; } setError(""); setFile(selected); }} /><button type="button" className="button-secondary" disabled={!file} onClick={upload}>Save cover</button></div><ErrorMessage message={error} /></div></section>;
}

function PayoutDetails({ profile, onSaved, client = false }) {
  const [form, setForm] = useState(profile); const [saved, setSaved] = useState(false); const [error, setError] = useState("");
  const save = async (event) => { event.preventDefault(); setError(""); try { const { id, email, updated_at, profile_photo, profile_photo_url, cover_image, profile_completion, ...payload } = form; onSaved(await patch("/profiles/me/", payload)); setSaved(true); } catch (err) { setError(err.message); } };
  return <form className="card space-y-4" onSubmit={save}><div><p className="text-xs font-black uppercase tracking-widest text-brand">{client ? "Payment method" : "Worker payout setup"}</p><h2 className="mt-1 text-lg font-black">Bank account and UPI</h2><p className="mt-1 text-sm text-slate-500">Demo-safe payout details used to display escrow release readiness. Never enter real credentials in demo mode.</p></div><div className="grid gap-3 md:grid-cols-2">{[["bank_account_name", "Account holder name"], ["bank_account_number", "Account number"], ["bank_ifsc", "IFSC code"], ["upi_id", "UPI ID"]].map(([key, label]) => <label className="label" key={key}>{label}<input className="field" value={form[key] || ""} onChange={(event) => setForm({ ...form, [key]: event.target.value })} /></label>)}</div>{!client && <div className="rounded-xl bg-blue-50 p-4"><p className="text-sm font-bold text-brand">Unique payout QR</p><p className="mt-1 break-all font-mono text-xs text-slate-600">{form.payout_qr_token || "Generated when demo profile is seeded"}</p><p className="mt-1 text-xs text-slate-500">Use this WorkNeuron token as the worker payout destination in test mode.</p></div>}<ErrorMessage message={error} />{saved && <p className="text-sm text-emerald-700">Payout details saved.</p>}<button className="button-primary">Save payout details</button></form>;
}
