import { defineConfig, mergeConfig } from "vitest/config";

import viteConfig from "./vite.config.ts";

// Fuso de um cliente no Brasil: um "2026-03-01" lido como meia-noite UTC viraria 28/02 aqui,
// então os testes de data pegam esse deslocamento. Definido antes de os workers subirem.
process.env.TZ = "America/Sao_Paulo";

export default mergeConfig(
  viteConfig,
  defineConfig({
    test: {
      environment: "jsdom",
      setupFiles: ["./src/test/setup.ts"],
      include: ["src/**/*.test.{ts,tsx}"],
      restoreMocks: true,
      unstubGlobals: true,
    },
  }),
);
