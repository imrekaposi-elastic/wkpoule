import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    proxy: {
      "/api": "http://localhost:8000",
      "/rum": {
        target:
          "https://0a07eb70c1a6425b92f4246e00d43cfe.ece.kaposi.net:9243",
        changeOrigin: true,
        secure: true,
        rewrite: (path) => path.replace(/^\/rum/, ""),
      },
    },
  },
});
