/**
 * App.jsx
 * ─────────────────────────────────────────────────────────────────
 * Application shell / root component.
 *
 * Responsibilities:
 *  - Import shared styles (styles/App.css)
 *  - Render the active page (currently ChatPage only)
 */

import AdminDashboard from './pages/AdminDashboard'
import "./styles/App.css";
import ChatPage from "./pages/ChatPage";

export default function App() {
  if (window.location.hash === '#admin') return <AdminDashboard />
  return <ChatPage />;
}