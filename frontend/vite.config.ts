/// <reference types="vitest/config" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: "./src/test/setup.ts",
    include: ["src/**/*.test.{ts,tsx}"],
  },
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
