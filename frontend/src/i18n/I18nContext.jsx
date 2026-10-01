import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { messages } from "./messages";
import { languages } from "./languages";

const LanguageContext = createContext(null);
const storageKey = "workneuron_interface_language";
// Every locale in the Indian language registry is available to the interface.
// Existing catalogs are used where present; missing entries fall back to English.
const interfaceLanguages = languages;

export function I18nProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    const stored = localStorage.getItem(storageKey) || localStorage.getItem("workneuron_task_language") || "en";
    return interfaceLanguages.some((item) => item.code === stored) ? stored : "en";
  });

  const setLanguage = (code) => {
    if (!interfaceLanguages.some((item) => item.code === code)) return;
    setLanguageState(code);
    localStorage.setItem(storageKey, code);
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
