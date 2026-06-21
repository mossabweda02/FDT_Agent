/**
 * api/agentApi.js
 * ========================
 * Fonctions d'appel à l'API backend pour interagir avec l'agent.
 * Contient les fonctions callAgent et fetchSuggestions qui font des requêtes POST
 * aux endpoints /ask et /suggest respectivement.
 */

const API_BASE_URL = "http://127.0.0.1:8000";

export async function callAgent(question, conversationId = null, history = []) {
  const r = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      question: String(question ?? ""),
      conversation_id: conversationId ? String(conversationId) : null,
      history: Array.isArray(history) ? history : [],
    }),
  });

  if (!r.ok) {
    const errorText = await r.text();
    throw new Error(`HTTP ${r.status}: ${errorText}`);
  }

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