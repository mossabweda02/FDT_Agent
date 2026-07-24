/**
 * App.jsx
 * ─────────────────────────────────────────────────────────────────
 * Gère l'affichage conditionnel entre :
 * - AuthPage si l'utilisateur n'est pas authentifié ;
 * - ChatPage si l'utilisateur est connecté ;
 * - AdminDashboard via le hash #admin.
 */

import { useEffect } from "react";
import { useIsAuthenticated, useMsal } from "@azure/msal-react";
import AdminDashboard from "./pages/AdminDashboard";
import ChatPage from "./pages/ChatPage";
import AuthPage from "./pages/AuthPage";
import "./styles/App.css";

export default function App() {
  const isAuthenticated = useIsAuthenticated();
  const { instance, accounts } = useMsal();

  useEffect(() => {
    if (accounts.length > 0 && !instance.getActiveAccount()) {
      instance.setActiveAccount(accounts[0]);
    }
  }, [accounts, instance]);

  async function handleLogout() {
    await instance.logoutRedirect({
      account: instance.getActiveAccount(),
      postLogoutRedirectUri: window.location.origin,
    });
  }

  if (window.location.hash === "#admin") {
    return <AdminDashboard />;
  }

  if (!isAuthenticated) {
    return <AuthPage />;
  }

  const activeAccount = instance.getActiveAccount() || accounts[0];

  return (
    <ChatPage
      onLogout={handleLogout}
      user={{
        name: activeAccount?.name || "Utilisateur",
        email: activeAccount?.username || "",
      }}
    />
  );
}