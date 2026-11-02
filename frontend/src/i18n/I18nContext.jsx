import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { messages } from "./messages";
import { languages } from "./languages";
import { patch } from "../services/api";
import { useAuth } from "../context/AuthContext";

const LanguageContext = createContext(null);
const storageKey = "workneuron_interface_language";
const interfaceLanguages = languages.filter(({ code }) => ["en", "te", "hi", "ta", "kn", "ml", "bn", "mr", "ur", "gu", "pa"].includes(code));

export function I18nProvider({ children }) {
  const { user } = useAuth();
  const [language, setLanguageState] = useState(() => {
    const stored = localStorage.getItem(storageKey) || localStorage.getItem("workneuron_task_language") || "en";
    return interfaceLanguages.some((item) => item.code === stored) ? stored : "en";
  });

  useEffect(() => {
    if (user?.preferred_language && interfaceLanguages.some((item) => item.code === user.preferred_language)) {
      setLanguageState(user.preferred_language);
      localStorage.setItem(storageKey, user.preferred_language);
    }
  }, [user?.id, user?.preferred_language]);

  const setLanguage = (code) => {
    if (!interfaceLanguages.some((item) => item.code === code)) return;
    setLanguageState(code);
    localStorage.setItem(storageKey, code);
    if (user) patch("/auth/me/", { preferred_language: code }).catch(() => {});
  };

  useEffect(() => {
    document.documentElement.lang = language;
    document.documentElement.dir = ["ar", "ur"].includes(language) ? "rtl" : "ltr";
  }, [language]);
  const value = useMemo(() => ({
    language,
    availableLanguages: interfaceLanguages,
    setLanguage,
    t: (key) => messages[language]?.[key] ?? messages.en[key] ?? key,
  }), [language]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useI18n() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useI18n must be used inside I18nProvider");
  return context;
}
