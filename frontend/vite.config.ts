import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["icon.svg"],
      manifest: {
        name: "dimgaai 點解",
        short_name: "dimgaai",
        description: "粵語會議即時轉錄與事實核查",
        theme_color: "#0d9488",
        background_color: "#f8fafc",
        display: "standalone",
        lang: "zh-HK",
        icons: [
          {
            src: "/icon.svg",
            sizes: "512x512",
            type: "image/svg+xml",
            purpose: "any maskable",
          },
        ],
      },
      workbox: {
        globPatterns: ["**/*.{js,css,html,ico,svg,woff2}"],
        navigateFallback: "/index.html",
      },
    }),
  ],
  server: {
    port: 5173,
    proxy: {
      "/ws": { target: "ws://127.0.0.1:8000", ws: true },
      "/documents": { target: "http://127.0.0.1:8000" },
      "/export": { target: "http://127.0.0.1:8000" },
      "/session": { target: "http://127.0.0.1:8000" },
      "/health": { target: "http://127.0.0.1:8000" },
    },
  },
});
