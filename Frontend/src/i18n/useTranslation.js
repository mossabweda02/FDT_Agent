/**
 * i18n/useTranslation.js
 * ========================
 * Hook de traduction simple pour l'application. Permet de charger les traductions
 * en fonction de la langue sélectionnée. Les fichiers de traduction sont au format JSON.
 */
import fr from "./fr.json";
import en from "./en.json";

const translations = { fr, en };

export function useTranslation(lang = "fr") {
  const t = translations[lang] ?? translations.fr;
  return { t };
}
