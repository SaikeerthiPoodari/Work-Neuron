import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { messages } from "./messages";
import { languages } from "./languages";
import { patch } from "../services/api";
import { useAuth } from "../context/AuthContext";

const LanguageContext = createContext(null);
const storageKey = "workneuron_interface_language";
const interfaceLanguages = languages.filter(({ code }) => ["en", "te", "hi", "ta", "kn", "ml", "bn", "mr", "ur", "gu", "pa"].includes(code));
const originalDomText = new WeakMap();
const originalDomAttributes = new WeakMap();

function readPath(source, key) {
  return key.split(".").reduce((value, part) => value?.[part], source);
}

function interpolate(value, params = {}) {
  return String(value).replace(/\{(\w+)\}/g, (_, name) => params[name] ?? `{${name}}`);
}

function translateValue(value, params) {
  if (value && typeof value === "object" && !Array.isArray(value)) {
    const count = Number(params.count);
    if (Number.isFinite(count)) return interpolate(value[count === 1 ? "one" : "other"] ?? value.other ?? value.one, params);
  }
  return interpolate(value, params);
}

function localizeLegacyDom(language, translate) {
  const english = messages.en || {};
  const phraseKeys = new Map(Object.entries(english).filter(([, value]) => typeof value === "string").map(([key, value]) => [value.trim(), key]));
  const root = document.getElementById("root");
  if (!root) return () => {};
  const translateText = (node) => {
    if (!originalDomText.has(node)) originalDomText.set(node, node.nodeValue);
    const original = originalDomText.get(node);
    const trimmed = original.trim();
    const key = phraseKeys.get(trimmed);
    if (!key) return;
    const next = translate(key);
    node.nodeValue = original.replace(trimmed, next);
  };
  const translateAttributes = (element) => {
    ["placeholder", "aria-label", "title"].forEach((attribute) => {
      const value = element.getAttribute(attribute);
      if (!value) return;
      const originals = originalDomAttributes.get(element) || {};
      if (!Object.prototype.hasOwnProperty.call(originals, attribute)) originals[attribute] = value;
      originalDomAttributes.set(element, originals);
      const key = phraseKeys.get(originals[attribute].trim());
      if (key) element.setAttribute(attribute, translate(key));
    });
  };
  const scan = (container) => {
    const walker = document.createTreeWalker(container, NodeFilter.SHOW_TEXT);
    let node;
    while ((node = walker.nextNode())) {
      const parent = node.parentElement;
      if (parent && !["SCRIPT", "STYLE", "TEXTAREA"].includes(parent.tagName) && !parent.closest("[data-user-content]")) translateText(node);
    }
    container.querySelectorAll?.("[placeholder], [aria-label], [title]").forEach(translateAttributes);
  };
  scan(root);
  const observer = new MutationObserver((records) => records.forEach((record) => record.addedNodes.forEach((node) => { if (node.nodeType === Node.TEXT_NODE) translateText(node); else if (node.nodeType === Node.ELEMENT_NODE) scan(node); })));
  observer.observe(root, { childList: true, subtree: true });
  return () => observer.disconnect();
}

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
    return localizeLegacyDom(language, (key) => translateValue(readPath(messages[language], key) ?? readPath(messages.en, key) ?? key));
  }, [language]);
  const value = useMemo(() => ({
    language,
    availableLanguages: interfaceLanguages,
    setLanguage,
    locale: languages.find((item) => item.code === language)?.locale || "en-IN",
    t: (key, params = {}) => translateValue(readPath(messages[language], key) ?? readPath(messages.en, key) ?? key, params),
    formatNumber: (number, options) => new Intl.NumberFormat(languages.find((item) => item.code === language)?.locale || "en-IN", options).format(number),
    formatDate: (date, options) => new Intl.DateTimeFormat(languages.find((item) => item.code === language)?.locale || "en-IN", options).format(new Date(date)),
    formatTime: (date, options) => new Intl.DateTimeFormat(languages.find((item) => item.code === language)?.locale || "en-IN", { timeStyle: "short", ...options }).format(new Date(date)),
  }), [language]);

  return <LanguageContext.Provider value={value}>{children}</LanguageContext.Provider>;
}

export function useI18n() {
  const context = useContext(LanguageContext);
  if (!context) throw new Error("useI18n must be used inside I18nProvider");
  return context;
}
