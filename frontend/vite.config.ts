import tailwindcss from "@tailwindcss/vite";
import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

export default defineConfig({
  plugins: [react(), tailwindcss()],
  server: {
    // Gọi /api/* từ frontend sẽ được chuyển sang backend FastAPI.
    proxy: { "/api": "http://localhost:8000" },
  },
});
