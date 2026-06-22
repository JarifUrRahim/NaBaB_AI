import { BrowserRouter, Routes, Route, useLocation } from "react-router-dom";
import { Toaster } from "sonner";
import "@/App.css";

import { AuthProvider } from "@/context/AuthContext";
import { LangProvider } from "@/context/LangContext";
import { AuthCallback } from "@/components/AuthCallback";
import { ProtectedRoute } from "@/components/ProtectedRoute";

import Landing from "@/pages/Landing";
import Login from "@/pages/Login";
import Chat from "@/pages/Chat";
import BuyCredits from "@/pages/BuyCredits";
import Dashboard from "@/pages/Dashboard";
import Admin from "@/pages/Admin";

function AppRouter() {
  const location = useLocation();
  // CRITICAL: handle session_id in URL fragment synchronously during render
  // This runs BEFORE any /auth/me checks to prevent race conditions
  if (location.hash?.includes("session_id=")) {
    return <AuthCallback />;
  }
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route
        path="/chat"
        element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        }
      />
      <Route
        path="/chat/:conversationId"
        element={
          <ProtectedRoute>
            <Chat />
          </ProtectedRoute>
        }
      />
      <Route
        path="/buy"
        element={
          <ProtectedRoute>
            <BuyCredits />
          </ProtectedRoute>
        }
      />
      <Route
        path="/dashboard"
        element={
          <ProtectedRoute>
            <Dashboard />
          </ProtectedRoute>
        }
      />
      <Route
        path="/admin"
        element={
          <ProtectedRoute adminOnly>
            <Admin />
          </ProtectedRoute>
        }
      />
    </Routes>
  );
}

function App() {
  return (
    <div className="App">
      <LangProvider>
        <AuthProvider>
          <BrowserRouter>
            <AppRouter />
            <Toaster
              position="top-center"
              toastOptions={{
                style: {
                  background: "#FDFBF7",
                  color: "#1C1917",
                  border: "1px solid #EAE5D9",
                  borderRadius: "12px",
                },
              }}
            />
          </BrowserRouter>
        </AuthProvider>
      </LangProvider>
    </div>
  );
}

export default App;
