import { useEffect, useRef } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import { api } from "@/lib/api";
import { useAuth } from "@/context/AuthContext";
import { NaBaBLogo } from "./NaBaBLogo";

export const AuthCallback = () => {
  const navigate = useNavigate();
  const location = useLocation();
  const { setUser } = useAuth();
  const hasProcessed = useRef(false);

  useEffect(() => {
    if (hasProcessed.current) return;
    hasProcessed.current = true;

    const hash = location.hash || window.location.hash;
    const params = new URLSearchParams(hash.replace("#", ""));
    const sessionId = params.get("session_id");

    if (!sessionId) {
      navigate("/login", { replace: true });
      return;
    }

    (async () => {
      try {
        const { data } = await api.post("/auth/session", { session_id: sessionId });
        setUser(data.user);
        // Clean URL fragment & navigate
        window.history.replaceState({}, document.title, window.location.pathname);
        navigate("/chat", { replace: true, state: { user: data.user } });
      } catch (e) {
        console.error("Auth exchange failed", e);
        navigate("/login", { replace: true });
      }
    })();
  }, [location.hash, navigate, setUser]);

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-cream gap-4">
      <NaBaBLogo size={64} />
      <div className="flex gap-2">
        <span className="typing-dot w-2 h-2 rounded-full" style={{ animationDelay: "0ms" }} />
        <span className="typing-dot w-2 h-2 rounded-full" style={{ animationDelay: "200ms" }} />
        <span className="typing-dot w-2 h-2 rounded-full" style={{ animationDelay: "400ms" }} />
      </div>
    </div>
  );
};
