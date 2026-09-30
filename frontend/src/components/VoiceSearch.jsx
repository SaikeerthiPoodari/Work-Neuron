import { useEffect, useRef, useState } from "react";
import { post } from "../services/api";
import { ErrorMessage } from "./StatusMessage";
import { languages } from "../i18n/languages";
import { useI18n } from "../i18n/I18nContext";

export default function VoiceSearch({ onFilters }) {
  const { language, t } = useI18n();
  const [listening, setListening] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState("");
  const recognitionRef = useRef(null);

  const start = () => {
    setError(""); setResult(null);
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) { setError(t("micUnsupported")); return; }
    const recognition = new SpeechRecognition();
    recognition.lang = languages.find((item) => item.code === language)?.locale || "en-IN";
    recognition.interimResults = false; recognition.maxAlternatives = 1;
    recognition.onstart = () => setListening(true);
    recognition.onerror = (event) => { setListening(false); setError(event.error === "not-allowed" ? t("micDenied") : t("voiceError")); };
    recognition.onend = () => setListening(false);
    recognition.onresult = async (event) => {
      try {
        const parsed = await post("/search/voice/", { recognized_text: event.results[0][0].transcript });
        setResult({ ...parsed, message: Object.keys(parsed.filters).length ? t("filtersExtracted") : t("voiceUnclear") });
        onFilters(parsed.filters);
      } catch (err) { setError(err.message); }
    };
    recognitionRef.current = recognition; recognition.start();
  };

  useEffect(() => () => recognitionRef.current?.stop(), []);

  return <div className="card border-blue-100 bg-blue-50/50"><div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-center"><div><p className="text-xs font-black uppercase tracking-widest text-brand">{t("handsFree")}</p><h2 className="mt-1 text-lg font-black">{t("speakRequirement")}</h2><p className="mt-1 text-sm text-slate-500">{t("tryExample")}</p></div><button type="button" className={`rounded-xl px-4 py-2.5 text-sm font-black text-white shadow-sm ${listening ? "bg-rose-500" : "bg-brand"}`} onClick={start}>{listening ? t("listening") : `🎤 ${t("speak")}`}</button></div>{result && <div className="mt-4 rounded-xl bg-white p-3 text-sm ring-1 ring-blue-100"><p className="font-semibold text-ink">{t("recognized")}: “{result.recognized_text}”</p><div className="mt-2 flex flex-wrap gap-2">{Object.entries(result.filters).map(([key, value]) => <span className="rounded-full bg-blue-50 px-3 py-1 text-xs font-bold text-brand" key={key}>{key.replaceAll("_", " ")}: {value}</span>)}</div><p className="mt-2 text-xs text-slate-500">{result.message} {t("confidence")}: {Math.round(result.confidence * 100)}%</p></div>}{error && <ErrorMessage message={error} />}</div>;
}
