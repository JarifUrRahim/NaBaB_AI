import { Link, useNavigate, useLocation } from "react-router-dom";
import { useLang } from "@/context/LangContext";
import { useAuth } from "@/context/AuthContext";
import { useT } from "@/lib/i18n";
import { LanguageToggle } from "./LanguageToggle";
import { NaBaBLogo } from "./NaBaBLogo";
import { Coins, LogOut, LayoutDashboard, MessageSquare, ShieldCheck, Menu, X } from "lucide-react";
import { useState } from "react";

export const Navbar = ({ variant = "public" }) => {
  const { lang } = useLang();
  const t = useT(lang);
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [mobileOpen, setMobileOpen] = useState(false);

  const handleLogout = async () => {
    await logout();
    navigate("/");
  };

  const isActive = (p) => location.pathname === p;

  return (
    <header className="sticky top-0 z-50 backdrop-blur-xl bg-cream/70 border-b border-cream-3">
      <div className="max-w-7xl mx-auto px-4 md:px-8 h-16 flex items-center justify-between">
        <Link to="/" className="flex items-center gap-2" data-testid="brand-link">
          <NaBaBLogo size={36} withText />
        </Link>

        {/* Desktop */}
        <nav className="hidden md:flex items-center gap-6">
          {variant === "public" && !user && (
            <>
              <a href="#features" className="text-sm text-foreground/70 hover:text-emerald transition-colors">
                {t("nav_features")}
              </a>
              <a href="#pricing" className="text-sm text-foreground/70 hover:text-emerald transition-colors">
                {t("nav_pricing")}
              </a>
            </>
          )}

          {user && (
            <>
              <Link
                to="/chat"
                className={`text-sm flex items-center gap-1.5 transition-colors ${
                  isActive("/chat") ? "text-emerald font-semibold" : "text-foreground/70 hover:text-emerald"
                }`}
                data-testid="nav-chat-link"
              >
                <MessageSquare className="w-4 h-4" /> {t("nav_chat")}
              </Link>
              <Link
                to="/dashboard"
                className={`text-sm flex items-center gap-1.5 transition-colors ${
                  isActive("/dashboard") ? "text-emerald font-semibold" : "text-foreground/70 hover:text-emerald"
                }`}
                data-testid="nav-dashboard-link"
              >
                <LayoutDashboard className="w-4 h-4" /> {t("nav_dashboard")}
              </Link>
              <Link
                to="/buy"
                className={`text-sm flex items-center gap-1.5 transition-colors ${
                  isActive("/buy") ? "text-emerald font-semibold" : "text-foreground/70 hover:text-emerald"
                }`}
                data-testid="nav-buy-link"
              >
                <Coins className="w-4 h-4" /> {t("nav_buy")}
              </Link>
              {user.is_admin && (
                <Link
                  to="/admin"
                  className={`text-sm flex items-center gap-1.5 transition-colors ${
                    isActive("/admin") ? "text-emerald font-semibold" : "text-foreground/70 hover:text-emerald"
                  }`}
                  data-testid="nav-admin-link"
                >
                  <ShieldCheck className="w-4 h-4" /> {t("nav_admin")}
                </Link>
              )}
            </>
          )}

          <LanguageToggle />

          {user ? (
            <div className="flex items-center gap-3 pl-3 border-l border-cream-3">
              <div
                className="flex items-center gap-2 rounded-full bg-emerald text-gold px-3 py-1.5 shadow-luxe"
                data-testid="credit-balance-display"
              >
                <Coins className="w-3.5 h-3.5" />
                <span className="text-sm font-semibold tracking-tight">
                  {user.credits}
                </span>
                <span className="text-[10px] uppercase tracking-widest opacity-80">
                  {t("credits_label")}
                </span>
              </div>
              <button
                onClick={handleLogout}
                className="p-2 rounded-full hover:bg-cream-2 transition-colors text-foreground/60"
                title={t("nav_logout")}
                data-testid="logout-button"
              >
                <LogOut className="w-4 h-4" />
              </button>
            </div>
          ) : (
            <Link
              to="/login"
              className="rounded-full bg-emerald text-gold px-5 py-2 text-sm font-semibold hover:bg-emerald-hover transition-all duration-300 hover:-translate-y-0.5 shadow-luxe"
              data-testid="nav-login-button"
            >
              {t("nav_login")}
            </Link>
          )}
        </nav>

        {/* Mobile toggle */}
        <button
          className="md:hidden p-2 rounded-full hover:bg-cream-2"
          onClick={() => setMobileOpen((s) => !s)}
          data-testid="mobile-menu-toggle"
        >
          {mobileOpen ? <X className="w-5 h-5" /> : <Menu className="w-5 h-5" />}
        </button>
      </div>

      {/* Mobile menu */}
      {mobileOpen && (
        <div className="md:hidden border-t border-cream-3 bg-cream">
          <div className="px-4 py-4 space-y-3">
            {user && (
              <div
                className="flex items-center gap-2 rounded-full bg-emerald text-gold px-3 py-2 w-fit"
                data-testid="credit-balance-display-mobile"
              >
                <Coins className="w-3.5 h-3.5" />
                <span className="text-sm font-semibold">{user.credits}</span>
                <span className="text-[10px] uppercase tracking-widest opacity-80">{t("credits_label")}</span>
              </div>
            )}
            {user ? (
              <>
                <Link to="/chat" onClick={() => setMobileOpen(false)} className="block text-sm py-2">
                  {t("nav_chat")}
                </Link>
                <Link to="/dashboard" onClick={() => setMobileOpen(false)} className="block text-sm py-2">
                  {t("nav_dashboard")}
                </Link>
                <Link to="/buy" onClick={() => setMobileOpen(false)} className="block text-sm py-2">
                  {t("nav_buy")}
                </Link>
                {user.is_admin && (
                  <Link to="/admin" onClick={() => setMobileOpen(false)} className="block text-sm py-2">
                    {t("nav_admin")}
                  </Link>
                )}
                <button onClick={handleLogout} className="block text-sm py-2 text-foreground/60">
                  {t("nav_logout")}
                </button>
              </>
            ) : (
              <Link
                to="/login"
                onClick={() => setMobileOpen(false)}
                className="inline-block rounded-full bg-emerald text-gold px-5 py-2 text-sm font-semibold"
              >
                {t("nav_login")}
              </Link>
            )}
            <div className="pt-2">
              <LanguageToggle />
            </div>
          </div>
        </div>
      )}
    </header>
  );
};
