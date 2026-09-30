import { useTheme } from "../context/ThemeContext";

export default function ThemeToggle() {
  const { isDark, toggleTheme } = useTheme();
  return <button type="button" onClick={toggleTheme} className="theme-toggle" aria-label={isDark ? "Switch to light mode" : "Switch to dark mode"} title={isDark ? "Switch to light mode" : "Switch to dark mode"}>{isDark ? "☀️" : "🌙"}</button>;
}
