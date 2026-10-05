import { createContext, useContext, useEffect, useMemo, useState } from "react";

const ThemeContext = createContext(null);
const STORAGE_KEY = "workneuron-theme";

function initialTheme() {
  const saved = localStorage.getItem(STORAGE_KEY);
  if (saved === "dark" || saved === "light") return saved;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function ThemeProvider({ children }) {
  const [theme, setTheme] = useState(initialTheme);
  useEffect(() => { document.documentElement.classList.toggle("dark", theme === "dark"); document.documentElement.dataset.theme = theme; localStorage.setItem(STORAGE_KEY, theme); }, [theme]);
  const value = useMemo(() => ({ theme, isDark: theme === "dark", toggleTheme: () => setTheme((current) => current === "dark" ? "light" : "dark"), setTheme }), [theme]);
  return <ThemeContext.Provider value={value}>{children}</ThemeContext.Provider>;
}

export function useTheme() { const context = useContext(ThemeContext); if (!context) throw new Error("useTheme must be used inside ThemeProvider"); return context; }
