import { useState } from "react";

const apiOrigin = (import.meta.env.VITE_API_URL || "http://127.0.0.1:8000/api").replace(/\/api\/?$/, "");

function imageUrl(src) {
  if (!src) return "";
  if (/^https?:\/\//i.test(src) || src.startsWith("data:")) return src;
  return `${apiOrigin}${src.startsWith("/") ? src : `/${src}`}`;
}

export default function ProfileAvatar({ src, name, className = "h-10 w-10", alt = "", ...props }) {
  const [failed, setFailed] = useState(false);
  const initials = (name || "WorkNeuron member").trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join("").toUpperCase() || "W";
  const url = imageUrl(src);
  return <span className={`inline-flex shrink-0 items-center justify-center overflow-hidden rounded-full bg-blue-50 font-black text-brand ${className}`} {...props}>
    {url && !failed ? <img src={url} alt={alt || name || "Profile"} className="h-full w-full object-cover" onError={() => setFailed(true)} /> : <span aria-hidden="true">{initials}</span>}
  </span>;
}
