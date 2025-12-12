// File: frontend/vite.config.js
// What it does: Vite config for dev server and React plugin.
// Variables to change: server.port (default: 5173) or open: true/false
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    open: true,
  },
});
