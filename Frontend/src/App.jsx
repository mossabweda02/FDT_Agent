/**
 * App.jsx
 * ─────────────────────────────────────────────────────────────────
 * Application shell / root component.
 *
 * Responsibilities:
 *  - Import shared styles (styles/App.css)
 *  - Render the active page (currently ChatPage only)
 * 
 * Auth state is kept in React state only (no localStorage).
 * Replace `user` state management with your MSAL account object
 * once MSAL is integrated in AuthPage.jsx (search MSAL_HOOK).
 */


import { useState } from "react";
import AdminDashboard from "./pages/AdminDashboard";
import ChatPage from "./pages/ChatPage";
import AuthPage from "./pages/AuthPage";
import "./styles/App.css";

export default function App() {
  const [user, setUser] = useState(null);

  const handleAuthenticated = (account) => {
    setUser(account);
  };

  if (window.location.hash === "#admin") {
    return <AdminDashboard />;
  }

  if (!user) {
    return <AuthPage onAuthenticated={handleAuthenticated} />;
  }

  return <ChatPage />;
}