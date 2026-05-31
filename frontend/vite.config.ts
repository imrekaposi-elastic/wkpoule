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
    coverage: {
      provider: "v8",
      include: ["src/**/*.{ts,tsx}"],
      exclude: [
        "src/**/*.test.{ts,tsx}",
        "src/test/**",
        "src/main.tsx",
        "src/apm-entry.ts",
        "src/vite-env.d.ts",
        "src/types.ts",
        // Large route screens covered better by integration/e2e tests.
        "src/pages/MatchDetail.tsx",
        "src/pages/SubgroupDetail.tsx",
        "src/pages/AdminSettings.tsx",
        "src/components/Navbar.tsx",
      ],
      thresholds: {
        lines: 50,
        statements: 50,
        branches: 45,
        functions: 45,
      },
    },
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
