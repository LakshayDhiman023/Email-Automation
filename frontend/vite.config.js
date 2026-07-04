import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// Content-Security-Policy is injected here, at BUILD time only — not as a static
// <meta> tag in index.html — so `npm run dev` is unaffected by it. Vite's dev
// server relies on inline <style>/<script> for HMR, which a strict CSP blocks;
// the production build uses only external <link>/<script src>, so this exact
// policy is safe there. connect-src covers same-origin + localhost:8000 (the
// default VITE_API_BASE) — deploying the API on a different origin than the
// frontend requires adding that origin here too, or every API call silently fails.
const CSP =
  "default-src 'self'; " +
  "script-src 'self'; " +
  "style-src 'self' https://fonts.googleapis.com; " +
  "font-src 'self' https://fonts.gstatic.com; " +
  "img-src 'self' data:; " +
  "connect-src 'self' http://localhost:8000; " +
  "object-src 'none'; " +
  "base-uri 'self'; " +
  "frame-ancestors 'none'";

function cspMetaTag() {
  let isBuild = false;
  return {
    name: 'csp-meta-tag',
    config(_config, { command }) {
      isBuild = command === 'build'; // 'serve' for `vite dev`, 'build' for `vite build`
    },
    transformIndexHtml(html) {
      if (!isBuild) return html;
      return html.replace(
        '<meta charset="UTF-8" />',
        `<meta charset="UTF-8" />\n    <meta http-equiv="Content-Security-Policy" content="${CSP}" />`
      );
    },
  };
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), cspMetaTag()],
})
