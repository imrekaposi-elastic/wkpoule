/// <reference types="vitest/config" />
import { defineConfig, type Plugin } from "vite";
import react from "@vitejs/plugin-react";

const RUNTIME_CONFIG_TAG = '<script src="/runtime-config.js"></script>';

/** Keep runtime-config.js as the first script in head so RUM reads acc/prd before the bundle runs. */
function runtimeConfigFirst(): Plugin {
  return {
    name: "wkpoule-runtime-config-first",
    transformIndexHtml(html) {
      if (!html.includes(RUNTIME_CONFIG_TAG)) return html;
      const without = html.replace(RUNTIME_CONFIG_TAG, "");
      return without.replace("<head>", `<head>\n    ${RUNTIME_CONFIG_TAG}`);
    },
  };
}

export default defineConfig({
  plugins: [react(), runtimeConfigFirst()],
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
        lines: 80,
        statements: 80,
        branches: 60,
        functions: 80,
      },
    },
  },
  server: {
    // Localhost only. Do not use --host / server.host: true unless you need LAN access;
    // several Vite dev-server advisories require network exposure to be exploitable.
    host: false,
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
