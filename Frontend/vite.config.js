/**
 * vite.config.js : Configuration Vite du frontend FDT Agent.
 * ================================================
 * Ce fichier configure :
 *  - le serveur de développement local ;
 *  - l'intégration de React et Tailwind CSS ;
 *  - les alias de résolution de modules.
 *
 * Notes :
 *  - Le serveur est fixé sur le port 3000 afin de correspondre à la Redirect URI configurée dans Microsoft Entra ID.
 *  - strictPort évite que Vite change automatiquement de port.
 */

import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import { fileURLToPath, URL } from "node:url";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    port: 3000,
    strictPort: true,
    host: "localhost",
  },
  resolve: {
    alias: {
      "@": fileURLToPath(new URL("./src", import.meta.url)),
    },
  },
});