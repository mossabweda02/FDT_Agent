/**
 * main.jsx
 * ─────────────────────────────────────────────────────────────────
 * Vite entry point.
 *
 * Mounts the React tree into #root and imports global base styles.
 * Nothing application-specific lives here; keep this file minimal.
 */

import React from "react";
import ReactDOM from "react-dom/client";
import App from "./App.jsx";
import "./styles/index.css";

ReactDOM.createRoot(document.getElementById("root")).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>
);