import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";

// Local-first build. No runtime network, no CDN, no remote fonts.
// All assets (fonts, icons) are bundled at build time.
export default defineConfig({
  plugins: [react()],
  base: "./",
  build: {
    outDir: "dist",
    sourcemap: false,
  },
  test: {
    globals: true,
    environment: "jsdom",
    setupFiles: ["./src/test/setup.ts"],
    css: true,
  },
});
