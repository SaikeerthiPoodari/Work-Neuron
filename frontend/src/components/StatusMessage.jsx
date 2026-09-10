export function ErrorMessage({ message }) { return message ? <div className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{message}</div> : null; }
export function EmptyState({ children }) { return <div className="card py-10 text-center text-sm text-slate-500">{children}</div>; }
