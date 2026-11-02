import { useTheme } from "../context/ThemeContext";
import GlobalLanguageSwitcher from "./GlobalLanguageSwitcher";

export default function ThemeToggle() {
  const { theme, isDark, toggleTheme } = useTheme();
  const next = theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
  const label = next === "system" ? "Use system theme" : next === "dark" ? "Switch to dark mode" : "Switch to light mode";
  return <><button type="button" onClick={toggleTheme} className="theme-toggle" aria-label={label} title={`${label} (current: ${theme})`}>{isDark ? "☀️" : "🌙"}</button><GlobalLanguageSwitcher /></>;
}
