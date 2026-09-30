import { useI18n } from "../i18n/I18nContext";

export function ErrorMessage({ message }) {
  const { t } = useI18n();
  if (!message) return null;
  const text = message.includes("Unable to connect to the server") ? t("connectionError") : message.startsWith("Request failed") ? t("requestFailed") : message;
  return <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{text}</div>;
}

export function EmptyState({ children }) { return <div className="card py-10 text-center text-sm text-slate-500">{children}</div>; }
