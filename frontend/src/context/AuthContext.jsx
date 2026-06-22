import { createContext, useContext, useEffect, useState, useCallback } from "react";
import { api } from "@/lib/api";

const AuthContext = createContext({});

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  const fetchMe = useCallback(async () => {
    try {
      const { data } = await api.get("/auth/me");
      setUser(data);
      return data;
    } catch {
      setUser(null);
      return null;
    }
  }, []);

  useEffect(() => {
    // CRITICAL: if returning from OAuth callback, skip /me check.
    // AuthCallback handles session exchange first.
    if (window.location.hash?.includes("session_id=")) {
      setLoading(false);
      return;
    }
    fetchMe().finally(() => setLoading(false));
  }, [fetchMe]);

  const logout = async () => {
    try {
      await api.post("/auth/logout");
    } catch {}
    setUser(null);
  };

  const refresh = async () => {
    return await fetchMe();
  };

  return (
    <AuthContext.Provider value={{ user, setUser, loading, logout, refresh }}>
      {children}
    </AuthContext.Provider>
  );
};

export const useAuth = () => useContext(AuthContext);
