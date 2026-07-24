/**
 * Module: auth/msalConfig
 * =======================
 * Définit la configuration Microsoft Authentication Library (MSAL) utilisée par le frontend.
 *
 * Ce module :
 *  - charge les paramètres d'authentification depuis les variables d'environnement.
 *  - configure le client Microsoft Entra ID.
 *  - définit les paramètres de cache de session.
 *  - expose la liste des scopes demandés lors de l'authentification.
 */

const clientId = import.meta.env.VITE_ENTRA_CLIENT_ID;
const tenantId = import.meta.env.VITE_ENTRA_TENANT_ID;
const scope = import.meta.env.VITE_API_SCOPE;

// Debug only
// console.log({ clientId, tenantId, scope });

export const msalConfig = {
  auth: {
    clientId,
    authority: `https://login.microsoftonline.com/${tenantId}`,
    redirectUri: `${window.location.origin}/authentication/login-callback`,
    postLogoutRedirectUri: window.location.origin,
  },
  cache: {
    cacheLocation: "sessionStorage",
    storeAuthStateInCookie: false,
  },
};

export const loginRequest = {
  scopes: [scope, "User.Read"],
};