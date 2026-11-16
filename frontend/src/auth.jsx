import { createContext, useCallback, useContext, useEffect, useState } from "react";
import { Navigate, useLocation } from "react-router";
import { api, getToken, setToken, setUnauthorizedHandler } from "./api.js";

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null);
  const [checking, setChecking] = useState(Boolean(getToken()));

  const clear = useCallback(() => {
    setToken(null);
    setUser(null);
  }, []);

  useEffect(() => {
    setUnauthorizedHandler(clear);
    if (!getToken()) return;
    api("/api/auth/me")
      .then((data) => setUser(data.user))
      .catch(clear)
      .finally(() => setChecking(false));
  }, [clear]);

  async function login(login, password) {
    const data = await api("/api/auth/login", { method: "POST", body: { login, password } });
    setToken(data.token);
    setUser(data.user);
  }

  async function logout() {
    await api("/api/auth/logout", { method: "POST" }).catch(() => {});
    clear();
  }

  return (
    <AuthContext.Provider value={{ user, checking, login, logout }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  return useContext(AuthContext);
}

export function RequireAuth({ children }) {
  const { user, checking } = useAuth();
  const location = useLocation();
  if (checking) return <div className="page-message">Загрузка…</div>;
  if (!user) return <Navigate to="/login" replace state={{ from: location.pathname }} />;
  return children;
}
