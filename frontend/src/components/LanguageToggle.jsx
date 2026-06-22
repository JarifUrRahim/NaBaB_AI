import { useLang } from "@/context/LangContext";

export const LanguageToggle = () => {
  const { lang, setLang } = useLang();
  return (
    <div
      className="inline-flex items-center rounded-full bg-cream-2 p-1 shadow-luxe"
      data-testid="language-toggle"
    >
      <button
        onClick={() => setLang("en")}
        className={`px-3 py-1 text-xs uppercase tracking-wider rounded-full transition-all duration-300 ${
          lang === "en"
            ? "bg-emerald text-gold shadow-sm"
            : "text-foreground/60 hover:text-foreground"
        }`}
        data-testid="lang-en-button"
      >
        EN
      </button>
      <button
        onClick={() => setLang("bn")}
        className={`px-3 py-1 text-xs tracking-wider rounded-full transition-all duration-300 font-bangla ${
          lang === "bn"
            ? "bg-emerald text-gold shadow-sm"
            : "text-foreground/60 hover:text-foreground"
        }`}
        data-testid="lang-bn-button"
      >
        বাংলা
      </button>
    </div>
  );
};
