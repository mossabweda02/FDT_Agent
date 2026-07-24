/**
 * Module: auth/msalInstance
 * =========================
 * Initialise et exporte l'instance unique de Microsoft Authentication Library (MSAL)
 * utilisée par le frontend.
 *
 * Cette instance centralise la gestion de l'authentification Microsoft Entra ID
 * (connexion, acquisition de jetons et gestion des comptes utilisateurs).
 *
 * Consommé par :
 *  - getAccessToken.js
 *  - AuthPage.jsx
 *  - futurs composants nécessitant MSAL
 */

import { PublicClientApplication } from "@azure/msal-browser";
import { msalConfig } from "./msalConfig";

export const msalInstance = new PublicClientApplication(msalConfig);