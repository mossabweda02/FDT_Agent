/**
 * Module: auth/tokenProvider
 * ==========================
 * Gestion de l'acquisition des jetons d'accès Microsoft Entra ID (Azure AD).
 *
 * Ce module récupère un access token via MSAL afin d'authentifier les appels
 * au backend FDT Agent et, par extension, aux APIs de l'Integration Hub.
 *
 * Stratégie :
 *  - Utilise l'acquisition silencieuse du token lorsque la session est valide.
 *  - Déclenche une redirection d'authentification si une interaction utilisateur est requise.
 */

import { InteractionRequiredAuthError } from "@azure/msal-browser";
import { msalInstance } from "./msalInstance";
import { loginRequest } from "./msalConfig";

export async function getAccessToken() {

  /*
  * Récupère un access token MSAL pour l'utilisateur connecté.
  * Tente d'abord une récupération silencieuse du token.
  * Si une interaction utilisateur est requise, déclenche une redirection MSAL.
  */
  const activeAccount = msalInstance.getActiveAccount();
  const accounts = msalInstance.getAllAccounts();
  const account = activeAccount || accounts[0];

  if (!account) {
    throw new Error("Aucun utilisateur connecté.");
  }

  const request = {
    ...loginRequest,
    account,
  };

  try {
    const response = await msalInstance.acquireTokenSilent(request);
    return response.accessToken;
  } catch (error) {
    if (error instanceof InteractionRequiredAuthError) {
      await msalInstance.acquireTokenRedirect(request);
      return null;
    }

    throw error;
  }
}