import React from "react";
import ReactDOM from "react-dom/client";
import { BrowserRouter } from "react-router-dom";
import App from "./App";
import { AuthProvider } from "./context/AuthContext";
import { I18nProvider } from "./i18n/I18nContext";
import { ThemeProvider } from "./context/ThemeContext";
import "./index.css";

class AppErrorBoundary extends React.Component {
  state = { error: null };
  static getDerivedStateFromError(error) { return { error }; }
  componentDidCatch(error, info) { console.error("WorkNeuron render error", error, info); }
  render() {
    if (!this.state.error) return this.props.children;
    return <main className="flex min-h-screen items-center justify-center bg-cloud px-5"><section className="card max-w-lg text-center"><p className="text-sm font-bold text-rose-600">Something went wrong</p><h1 className="mt-2 text-2xl font-black">WorkNeuron could not render this page</h1><p className="mt-3 text-sm text-slate-500">Reload the page to retry. If the problem continues, sign out and sign in again.</p><p className="mt-3 rounded-lg bg-rose-50 p-3 text-left text-xs text-rose-700">{this.state.error.message}</p><button className="button-primary mt-5" onClick={() => window.location.reload()}>Reload page</button></section></main>;
  }
}

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <AppErrorBoundary><BrowserRouter>
      <ThemeProvider><AuthProvider><I18nProvider><App /></I18nProvider></AuthProvider></ThemeProvider>
    </BrowserRouter></AppErrorBoundary>
  </React.StrictMode>,
);
