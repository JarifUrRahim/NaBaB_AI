import { useLang } from "@/context/LangContext";
import { useT } from "@/lib/i18n";
import { NaBaBLogo } from "./NaBaBLogo";

export const Footer = () => {
  const { lang } = useLang();
  const t = useT(lang);
  return (
    <footer className="border-t border-cream-3 bg-cream-2 paper-grain">
      <div className="max-w-7xl mx-auto px-4 md:px-8 py-10 flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-center gap-3">
          <NaBaBLogo size={32} withText />
        </div>
        <div className="text-center md:text-right">
          <p className="text-xs text-foreground/60">{t("footer_made")}</p>
          <p className="text-xs text-foreground/40 mt-1">
            © {new Date().getFullYear()} NaBaB. {t("footer_rights")}
          </p>
        </div>
      </div>
    </footer>
  );
};
