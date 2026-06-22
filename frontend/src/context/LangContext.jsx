import { createContext, useContext, useEffect, useState } from "react";

const LangContext = createContext({ lang: "en", setLang: () => {} });

export const LangProvider = ({ children }) => {
  const [lang, setLang] = useState(() => localStorage.getItem("nabab_lang") || "bn");

  useEffect(() => {
    localStorage.setItem("nabab_lang", lang);
    document.body.setAttribute("data-lang", lang);
  }, [lang]);

  return (
    <LangContext.Provider value={{ lang, setLang }}>{children}</LangContext.Provider>
  );
};

export const useLang = () => useContext(LangContext);
