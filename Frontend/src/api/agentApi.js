/**
 * api/agentApi.js
 * ========================
 * Fonctions d'appel à l'API backend pour interagir avec l'agent.
 * Contient les fonctions callAgent et fetchSuggestions qui font des requêtes POST
 * aux endpoints /ask et /suggest respectivement.
 */

const API_BASE_URL = "http://127.0.0.1:8000";

export async function callAgent(question) {
  const r = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ question }),
  });

  if (!r.ok) throw new Error(`HTTP ${r.status}`);

  const d = await r.json();
  return d.answer ?? d.response ?? JSON.stringify(d);
}

export async function fetchSuggestions(question) {
  try {
    const r = await fetch(`${API_BASE_URL}/suggest`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question }),
    });

    if (!r.ok) return [];

    const d = await r.json();
    return d.suggestions ?? [];
  } catch {
    return [];
  }
}