import { useEffect, useState } from "react";
import { useAuth } from "../context/AuthContext";
import { get, patch, post, remove } from "../services/api";
import { ErrorMessage } from "../components/StatusMessage";
import { languages, languageLabels } from "../i18n/languages";
import { useI18n } from "../i18n/I18nContext";

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
  const save = async (event) => {
    event.preventDefault(); setError("");
    try {
      const { email, id, updated_at, profile_photo, profile_photo_url, ...payload } = profile;
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
  return <div className="space-y-6">
    <div><p className="text-sm font-semibold text-brand">{user.role === "WORKER" ? t("profile") : "Your identity"}</p><h1 className="mt-1 text-3xl font-black">{user.role === "WORKER" ? t("profile") : "Profile"}</h1><p className="mt-2 text-slate-500">{user.role === "WORKER" ? t("profileHint") : "Keep your worker profile and job matching information up to date."}</p></div>
    {user.role === "WORKER" && <div className="card flex flex-col items-start gap-4 sm:flex-row sm:items-center"><div className="flex h-20 w-20 shrink-0 items-center justify-center overflow-hidden rounded-full bg-blue-50 text-xl font-black text-brand">{photoPreview || profile.profile_photo || profile.profile_photo_url ? <img src={photoPreview || profile.profile_photo || profile.profile_photo_url} alt="Worker profile" className="h-full w-full object-cover" /> : `${user.first_name?.[0] || "W"}${user.last_name?.[0] || ""}`}</div><div className="w-full"><h2 className="font-bold">Profile photo</h2><p className="mt-1 text-sm text-slate-500">Upload a JPG, PNG or WebP image, up to 5 MB.</p><input className="field mt-3 max-w-md" type="file" accept="image/jpeg,image/png,image/webp" onChange={(event) => { const file = event.target.files?.[0]; if (!file) return; if (!["image/jpeg", "image/png", "image/webp"].includes(file.type) || file.size > 5 * 1024 * 1024) { setError("Choose a JPG, PNG or WebP image up to 5 MB."); event.target.value = ""; return; } setError(""); setPhotoFile(file); }} /></div></div>}
    <form onSubmit={save} className="card grid gap-4 md:grid-cols-2"><div className="md:col-span-2"><label className="label">Email</label><p className="mt-2 text-sm text-slate-600">{profile.email}</p></div>{fields.map(([key, value]) => <div key={key}><label className="label" htmlFor={`profile-${key}`}>{key.replaceAll("_", " ")}</label>{key === "bio" || key === "interests" ? <textarea id={`profile-${key}`} className="field" rows="4" value={value || ""} onChange={(event) => setProfile({ ...profile, [key]: event.target.value })} /> : key === "availability" ? <select id={`profile-${key}`} className="field" value={value || "FLEXIBLE"} onChange={(event) => setProfile({ ...profile, [key]: event.target.value })}><option value="FLEXIBLE">Flexible</option><option value="FULL_TIME">Full time</option><option value="PART_TIME">Part time</option><option value="WEEKENDS">Weekends</option></select> : <input id={`profile-${key}`} className="field" type={key.endsWith("url") ? "url" : "text"} value={value || ""} onChange={(event) => setProfile({ ...profile, [key]: event.target.value })} />}</div>)}{user.role === "WORKER" && <div className="md:col-span-2"><label className="label" htmlFor="profile-languages">Languages</label><p className="mb-2 text-xs text-slate-500">Select all languages you can use for work. Use Ctrl or Command to select multiple.</p><select id="profile-languages" multiple size="7" className="field" value={profile.languages || []} onChange={(event) => setProfile({ ...profile, languages: [...event.target.selectedOptions].map((option) => option.value) })}>{languages.map(({ code, label }) => <option value={code} key={code}>{label}</option>)}</select><div className="mt-2 flex flex-wrap gap-2">{(profile.languages || []).map((code) => <span key={code} className="rounded-full bg-blue-50 px-3 py-1 text-xs font-semibold text-brand">{languageLabels[code] || code}</span>)}</div></div>}<div className="md:col-span-2"><ErrorMessage message={error} /><button className="button-primary mt-3">Save profile</button></div></form>
    {user.role === "WORKER" && <section className="card"><h2 className="text-lg font-bold">Skills</h2><div className="mt-4 flex flex-wrap gap-2">{skills.map((item) => <span className="rounded-full bg-blue-50 px-3 py-1.5 text-sm font-semibold text-brand" key={item.id}>{item.skill_name}<button type="button" aria-label={`Remove ${item.skill_name}`} className="ml-2 text-blue-400" onClick={() => remove(`/skills/mine/${item.id}/`).then(load).catch((err) => setError(err.message))}>×</button></span>)}</div><div className="mt-5 flex flex-col gap-2 sm:flex-row"><select className="field mt-0 max-w-xs" value={skillId} onChange={(event) => setSkillId(event.target.value)}><option value="">Add a skill…</option>{catalog.filter((skill) => !skills.some((mine) => mine.skill === skill.id)).map((skill) => <option value={skill.id} key={skill.id}>{skill.name}</option>)}</select><button type="button" className="button-secondary" disabled={!skillId} onClick={addSkill}>Add skill</button></div></section>}
  </div>;
}
