/**
 * main.jsx
 * ─────────────────────────────────────────────────────────────────
 * Point d'entrée de Vite.
 * Initialise l'instance MSAL, gère la redirection après authentification pui monte 
 * l'application React avec le provider MSAL.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./styles/index.css";
import { MsalProvider } from "@azure/msal-react";
import { msalInstance } from "./auth/msalInstance";

async function bootstrap() {
  await msalInstance.initialize();

  const response = await msalInstance.handleRedirectPromise();
/* condition de */
  if (response?.account) {
    msalInstance.setActiveAccount(response.account);
  } else {
    const accounts = msalInstance.getAllAccounts();
    if (accounts.length > 0) {
      msalInstance.setActiveAccount(accounts[0]);
    }
  }

  ReactDOM.createRoot(document.getElementById("root")).render(
    <React.StrictMode>
      <MsalProvider instance={msalInstance}>
        <App />
      </MsalProvider>
    </React.StrictMode>
  );
}

bootstrap();