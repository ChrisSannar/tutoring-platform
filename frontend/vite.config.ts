import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [react()],
  server: {
    strictPort: true,
    headers: {
      "Content-Security-Policy":
        "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'",
      "Permissions-Policy":
        "camera=(), geolocation=(), microphone=(), payment=()",
      "Referrer-Policy": "strict-origin-when-cross-origin",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
    },
    proxy: {
      "/api": "http://127.0.0.1:7311",
    },
  },
  preview: {
    strictPort: true,
    headers: {
      "Content-Security-Policy":
        "default-src 'self'; base-uri 'self'; frame-ancestors 'none'; form-action 'self'; object-src 'none'; script-src 'self'; style-src 'self' 'unsafe-inline'",
      "Permissions-Policy":
        "camera=(), geolocation=(), microphone=(), payment=()",
      "Referrer-Policy": "strict-origin-when-cross-origin",
      "X-Content-Type-Options": "nosniff",
      "X-Frame-Options": "DENY",
    },
    proxy: {
      "/api": "http://127.0.0.1:7311",
    },
  },
});
