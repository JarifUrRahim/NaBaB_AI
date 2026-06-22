import { Navigate } from "react-router-dom";
import { useAuth } from "@/context/AuthContext";

export const ProtectedRoute = ({ children, adminOnly = false }) => {
  const { user, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-cream">
        <div className="flex gap-2">
          <span className="typing-dot w-2 h-2 rounded-full" style={{ animationDelay: "0ms" }} />
          <span className="typing-dot w-2 h-2 rounded-full" style={{ animationDelay: "200ms" }} />
          <span className="typing-dot w-2 h-2 rounded-full" style={{ animationDelay: "400ms" }} />
        </div>
      </div>
    );
  }

  if (!user) return <Navigate to="/login" replace />;
  if (adminOnly && !user.is_admin) return <Navigate to="/chat" replace />;
  return children;
};
