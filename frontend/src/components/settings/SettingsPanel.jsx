import {
  X,
  Settings,
//   Bell,
//   SlidersHorizontal,
//   Grid3X3,
//   Database,
//   Shield,
  Check,
  User,
  Keyboard,
  Monitor,
  Moon,
  Sun,
  ChevronDown,
} from "lucide-react";

import { useState } from "react";
import { useTheme } from "../../context/ThemeContext";
import "./SettingsPanel.css";

export default function SettingsPanel({
  open,
  onClose,
  preferences,
  updatePreference,
}) {

  const [languageOpen, setLanguageOpen] = useState(false);
  const { theme, setTheme } = useTheme();

  if (!open) return null;

  const menuItems = [
    { id: "general", label: "Général", icon: Settings, active: true },
    // { id: "notifications", label: "Notifications", icon: Bell },
    // { id: "personalisation", label: "Personnalisation", icon: SlidersHorizontal },
    // { id: "applications", label: "Applications", icon: Grid3X3 },
    // { id: "data", label: "Gestion des données", icon: Database },
    // { id: "security", label: "Sécurité et connexion", icon: Shield },
    { id: "account", label: "Compte", icon: User },
    { id: "keyboard", label: "Clavier", icon: Keyboard },
  ];

  const appearanceOptions = [
    { value: "light", label: "Clair", icon: Sun },
    { value: "dark", label: "Sombre", icon: Moon },
    { value: "system", label: "Système", icon: Monitor },
  ];

  const languageOptions = [
    { value: "auto", label: "Détection automatique" },
    { value: "fr", label: "Français (France)" },
    { value: "en", label: "English (United States)" },
    ];

    const selectedLanguage =
    languageOptions.find((option) => option.value === preferences.language) ||
    languageOptions[0];

  return (
    <div className="settings-overlay" onMouseDown={onClose}>
      <section
        className="settings-modal"
        onMouseDown={(event) => event.stopPropagation()}
      >
        <aside className="settings-sidebar">
          <button
            type="button"
            className="settings-close-button"
            onClick={onClose}
            aria-label="Fermer les paramètres"
          >
            <X size={20} />
          </button>

          <nav className="settings-nav">
            {menuItems.map((item) => {
              const Icon = item.icon;

              return (
                <button
                  key={item.id}
                  type="button"
                  className={`settings-nav-item ${item.active ? "is-active" : ""}`}
                >
                  <Icon size={19} />
                  <span>{item.label}</span>
                </button>
              );
            })}
          </nav>
        </aside>

        <main className="settings-content">
          <header className="settings-content-header">
            <h2>Général</h2>
          </header>

          <div className="settings-list">
            <div className="settings-row">
              <span>Thème</span>

              <div className="settings-segment">
                {appearanceOptions.map((option) => {
                  const Icon = option.icon;
                  const active = theme === option.value;

                  return (
                    <button
                      key={option.value}
                      type="button"
                      className={`settings-segment-button ${active ? "is-active" : ""}`}
                      onClick={() => setTheme(option.value)}
                    >
                      <Icon size={15} />
                      {option.label}
                    </button>
                  );
                })}
              </div>
            </div>
             <div className="settings-row">
            <span>Langue</span>

            <div className="settings-dropdown">
                <button
                type="button"
                className="settings-dropdown-trigger"
                onClick={() => setLanguageOpen((open) => !open)}
                >
                {selectedLanguage.label}
                <ChevronDown size={16} />
                </button>

                {languageOpen && (
                <div className="settings-dropdown-menu">
                    {languageOptions.map((option) => (
                    <button
                        key={option.value}
                        type="button"
                        className="settings-dropdown-option"
                        onClick={() => {
                        updatePreference("language", option.value);
                        setLanguageOpen(false);
                        }}
                    >
                        <span>{option.label}</span>

                        {selectedLanguage.value === option.value && (
                        <Check size={16} />
                        )}
                    </button>
                    ))}
                </div>
                )}
            </div>
            </div>

            <div className="settings-row">
              <span>Suggestions contextuelles</span>

              <SettingsSwitch
                checked={preferences.contextSuggestions}
                onChange={(value) => updatePreference("contextSuggestions", value)}
              />
            </div>

            <div className="settings-row">
              <div>
                <span>Tool calls</span>
                <small>Afficher le bloc d’analyse pendant le traitement.</small>
              </div>

              <SettingsSwitch
                checked={preferences.showToolCalls}
                onChange={(value) => updatePreference("showToolCalls", value)}
              />
            </div>

            <div className="settings-row">
              <div>
                <span>Entrée pour envoyer</span>
                <small>Shift + Entrée permet d’ajouter une nouvelle ligne.</small>
              </div>

              <SettingsSwitch
                checked={preferences.enterToSend}
                onChange={(value) => updatePreference("enterToSend", value)}
              />
            </div>

            
          </div>
        </main>
      </section>
    </div>
  );
}

function SettingsSwitch({ checked, onChange }) {
  return (
    <button
      type="button"
      className={`settings-switch ${checked ? "is-on" : ""}`}
      onClick={() => onChange(!checked)}
      aria-pressed={checked}
    >
      <span />
    </button>
  );
}