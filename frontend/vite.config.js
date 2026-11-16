import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// В режиме разработки Vite проксирует /api на бэкенд FastAPI.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      "/api": "http://127.0.0.1:8000",
    },
  },
});
