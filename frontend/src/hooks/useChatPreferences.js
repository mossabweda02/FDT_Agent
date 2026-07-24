import { useEffect, useState } from "react";

const STORAGE_KEY = "fdt-agent-chat-preferences";

const DEFAULT_PREFERENCES = {
  contextSuggestions: true,
  showToolCalls: true,
  enterToSend: true,
  language: "auto",
};

export default function useChatPreferences() {
  const [preferences, setPreferences] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      return stored
        ? { ...DEFAULT_PREFERENCES, ...JSON.parse(stored) }
        : DEFAULT_PREFERENCES;
    } catch {
      return DEFAULT_PREFERENCES;
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(preferences));
  }, [preferences]);

  function updatePreference(key, value) {
    setPreferences((prev) => ({
      ...prev,
      [key]: value,
    }));
  }

  return {
    preferences,
    updatePreference,
  };
}