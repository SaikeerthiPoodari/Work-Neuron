import { createContext, useContext, useEffect, useMemo, useState } from "react";
import { api, post } from "../services/api";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!localStorage.getItem("workneuron_access")) { setLoading(false); return; }
    api("/auth/me/").then(setUser).catch(() => localStorage.clear()).finally(() => setLoading(false));
  }, []);

  const login = async (credentials) => {
    const data = await post("/auth/login/", credentials);
    localStorage.setItem("workneuron_access", data.access);
    localStorage.setItem("workneuron_refresh", data.refresh);
    setUser(data.user);
  };
  const register = async (payload) => { await post("/auth/register/", payload); await login({ email: payload.email, password: payload.password }); };
  const logout = () => { localStorage.removeItem("workneuron_access"); localStorage.removeItem("workneuron_refresh"); setUser(null); };
  const value = useMemo(() => ({ user, loading, login, register, logout }), [user, loading]);
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export const useAuth = () => useContext(AuthContext);
