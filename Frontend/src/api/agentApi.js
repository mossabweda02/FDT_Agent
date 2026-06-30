/**
 * Module: api/agentApi
 * ====================
 * Fournit les fonctions utilisées par le frontend pour communiquer
 * avec l'API du FDT Agent.
 *
 * Responsabilités :
 *  - récupérer un access token Microsoft Entra ID ;
 *  - construire les en-têtes HTTP authentifiés ;
 *  - envoyer les requêtes aux endpoints backend ;
 *  - gérer les erreurs HTTP et retourner les réponses de l'agent.
 *
 * Endpoints utilisés :
 *  - POST /ask
 *  - POST /suggest
 */

import { getAccessToken } from "../auth/getAccessToken.js";

const API_BASE_URL = "http://127.0.0.1:8000";

/* Récuperation de l'en-tête d'authentification */
async function getAuthHeaders() {
  const token = await getAccessToken();

  if (!token) {
    throw new Error("Token non disponible.");
  }

  return {
    "Content-Type": "application/json",
    Authorization: `Bearer ${token}`,
  };
}

export async function callAgent(question, conversationId = null, history = []) {
  const r = await fetch(`${API_BASE_URL}/ask`, {
    method: "POST",
    headers: await getAuthHeaders(),
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
      headers: await getAuthHeaders(),
      body: JSON.stringify({ question }),
    });

    if (!r.ok) return [];

    const d = await r.json();
    return d.suggestions ?? [];
  } catch {
    return [];
  }
}