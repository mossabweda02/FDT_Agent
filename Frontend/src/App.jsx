/**
 * App.jsx
 * ─────────────────────────────────────────────────────────────────
 * Application shell / root component.
 *
 * Responsibilities:
 *  - Import shared styles (styles/App.css)
 *  - Render the active page (currently ChatPage only)
 */

import "./styles/App.css";
import ChatPage from "./pages/ChatPage";

export default function App() {
  return <ChatPage />;
}