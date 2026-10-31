import { createContext, useContext, useEffect, useMemo, useState } from "react";

const ThemeContext = createContext(null);
const STORAGE_KEY = "workneuron-theme";
const PALETTE_KEY = "workneuron-palette";
const MOTION_KEY = "workneuron-reduced-motion";
const palettes = ["blue", "aurora", "indigo"];

function readStorage(key, fallback) {
  try { return localStorage.getItem(key) || fallback; } catch { return fallback; }
}

function initialTheme() {
  const saved = readStorage(STORAGE_KEY, "system");
  return ["dark", "light", "system"].includes(saved) ? saved : "system";
}

export function ThemeProvider({ children }) {
  const [theme, setThemeState] = useState(initialTheme);
  const [palette, setPaletteState] = useState(() => { const saved = readStorage(PALETTE_KEY, "blue"); return palettes.includes(saved) ? saved : "blue"; });
  const [reducedMotion, setReducedMotionState] = useState(() => readStorage(MOTION_KEY, "system"));
  const [systemDark, setSystemDark] = useState(() => window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false);
  const effectiveTheme = theme === "system" ? (systemDark ? "dark" : "light") : theme;
  useEffect(() => {
    const media = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!media) return undefined;
    const update = (event) => setSystemDark(event.matches);
    media.addEventListener?.("change", update);
    return () => media.removeEventListener?.("change", update);
  }, []);
  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", effectiveTheme === "dark");
    root.dataset.theme = effectiveTheme;
    root.dataset.themePreference = theme;
    root.dataset.palette = palette;
    const systemReduced = window.matchMedia?.("(prefers-reduced-motion: reduce)").matches;
    root.classList.toggle("reduce-motion", reducedMotion === "on" || (reducedMotion === "system" && systemReduced));
    try { localStorage.setItem(STORAGE_KEY, theme); localStorage.setItem(PALETTE_KEY, palette); localStorage.setItem(MOTION_KEY, reducedMotion); } catch { /* storage can be disabled */ }
  }, [effectiveTheme, palette, reducedMotion, theme]);
  const value = useMemo(() => ({
    theme, effectiveTheme, isDark: effectiveTheme === "dark", palette, palettes, reducedMotion,
    toggleTheme: () => setThemeState((current) => current === "light" ? "dark" : current === "dark" ? "system" : "light"),
    setTheme: (value) => setThemeState(["dark", "light", "system"].includes(value) ? value : "system"),
    setPalette: (value) => { if (palettes.includes(value)) setPaletteState(value); },
    setReducedMotion: (value) => { if (["on", "off", "system"].includes(value)) setReducedMotionState(value); },
  }), [theme, effectiveTheme, palette, reducedMotion]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() { const context = useContext(ThemeContext); if (!context) throw new Error("useTheme must be used inside ThemeProvider"); return context; }
