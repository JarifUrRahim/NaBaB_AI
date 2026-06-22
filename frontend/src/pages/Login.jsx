import { useLang } from "@/context/LangContext";
import { useT } from "@/lib/i18n";
import { useAuth } from "@/context/AuthContext";
import { Navigate } from "react-router-dom";
import { Navbar } from "@/components/Navbar";
import { NaBaBLogo } from "@/components/NaBaBLogo";
import { Sparkles } from "lucide-react";

export default function Login() {
  const { lang } = useLang();
  const t = useT(lang);
  const { user, loading } = useAuth();

  if (!loading && user) return <Navigate to="/chat" replace />;

  const handleGoogle = () => {
    // REMINDER: DO NOT HARDCODE THE URL, OR ADD ANY FALLBACKS OR REDIRECT URLS, THIS BREAKS THE AUTH
    const redirectUrl = window.location.origin + "/chat";
    window.location.href = `https://auth.emergentagent.com/?redirect=${encodeURIComponent(redirectUrl)}`;
  };

  return (
    <div className="min-h-screen bg-cream paper-grain flex flex-col">
      <Navbar />
      <div className="flex-1 flex items-center justify-center px-4 py-16">
        <div className="w-full max-w-md">
          <div className="text-center mb-8">
            <div className="inline-block">
              <NaBaBLogo size={72} />
            </div>
            <h1 className="font-display text-4xl text-emerald mt-5">{t("login_title")}</h1>
            <p className="text-foreground/60 mt-2 text-sm">{t("login_sub")}</p>
          </div>

          <div className="rounded-3xl bg-cream border border-cream-3 shadow-luxe p-8 space-y-5">
            <button
              onClick={handleGoogle}
              className="w-full inline-flex items-center justify-center gap-3 rounded-full bg-emerald text-gold px-6 py-3.5 text-sm font-semibold hover:bg-emerald-hover transition-all duration-300 hover:-translate-y-0.5"
              data-testid="login-google-button"
            >
              <svg className="w-4 h-4" viewBox="0 0 48 48">
                <path
                  fill="#FFC107"
                  d="M43.611 20.083H42V20H24v8h11.303c-1.649 4.657-6.08 8-11.303 8c-6.627 0-12-5.373-12-12s5.373-12 12-12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C12.955 4 4 12.955 4 24s8.955 20 20 20s20-8.955 20-20c0-1.341-.138-2.65-.389-3.917z"
                />
                <path
                  fill="#FF3D00"
                  d="m6.306 14.691l6.571 4.819C14.655 15.108 18.961 12 24 12c3.059 0 5.842 1.154 7.961 3.039l5.657-5.657C34.046 6.053 29.268 4 24 4C16.318 4 9.656 8.337 6.306 14.691z"
                />
                <path
                  fill="#4CAF50"
                  d="M24 44c5.166 0 9.86-1.977 13.409-5.192l-6.19-5.238A11.91 11.91 0 0 1 24 36c-5.202 0-9.619-3.317-11.283-7.946l-6.522 5.025C9.505 39.556 16.227 44 24 44z"
                />
                <path
                  fill="#1976D2"
                  d="M43.611 20.083H42V20H24v8h11.303a12.04 12.04 0 0 1-4.087 5.571l.003-.002l6.19 5.238C36.971 39.205 44 34 44 24c0-1.341-.138-2.65-.389-3.917z"
                />
              </svg>
              {t("login_google")}
            </button>

            <div className="flex items-center gap-3 text-xs text-foreground/50">
              <div className="flex-1 h-px bg-cream-3" />
              <span>
                <Sparkles className="inline w-3 h-3 text-gold" />{" "}
                {lang === "bn" ? "নিরাপদ ও দ্রুত" : "Secure & instant"}
              </span>
              <div className="flex-1 h-px bg-cream-3" />
            </div>

            <p className="text-center text-xs text-foreground/50">
              {lang === "bn"
                ? "সাইন আপ মানেই আপনি আমাদের সেবা শর্তে সম্মতি দিচ্ছেন।"
                : "By signing in, you agree to our terms of service."}
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}
