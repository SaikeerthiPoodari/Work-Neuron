import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { messages } from "./messages";
import { languages } from "./languages";

const LanguageContext = createContext(null);
const storageKey = "workneuron_interface_language";
const interfaceLanguages = languages.filter(({ code }) => messages[code]);

export function I18nProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    const stored = localStorage.getItem(storageKey) || localStorage.getItem("workneuron_task_language") || "en";
    return interfaceLanguages.some((item) => item.code === stored) ? stored : "en";
  });

  const setLanguage = (code) => {
    if (!interfaceLanguages.some((item) => item.code === code)) return;
    setLanguageState(code);
    localStorage.setItem(storageKey, code);
    // Keep compatibility with the previous feed-specific preference key.
    localStorage.setItem("workneuron_task_language", code);
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
