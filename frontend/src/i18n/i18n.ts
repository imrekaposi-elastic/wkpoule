import i18n from "i18next";
import { initReactI18next } from "react-i18next";
import en from "./en.json";
import nl from "./nl.json";
import pt from "./pt.json";
import de from "./de.json";
import he from "./he.json";

const LANG_KEY = "wkpoule_lang";

function applyDocumentLang(lng: string) {
  if (typeof document === "undefined") return;
  document.documentElement.lang = lng;
  document.documentElement.dir = lng === "he" ? "rtl" : "ltr";
}

const initialLng = typeof localStorage !== "undefined" ? localStorage.getItem(LANG_KEY) || "en" : "en";

i18n.use(initReactI18next).init({
  resources: {
    en: { translation: en },
    nl: { translation: nl },
    pt: { translation: pt },
    de: { translation: de },
    he: { translation: he },
  },
  lng: initialLng,
  fallbackLng: "en",
  interpolation: { escapeValue: false },
});

applyDocumentLang(initialLng);

i18n.on("languageChanged", (lng) => {
  localStorage.setItem(LANG_KEY, lng);
  applyDocumentLang(lng);
});

export default i18n;
