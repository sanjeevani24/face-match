import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";
import tailwindcss from "@tailwindcss/vite";
import path from "path";

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    // Camera access (getUserMedia) requires a secure context.
    // Vite's dev server on localhost is treated as secure by browsers,
    // but if you need to test over LAN/mobile, enable HTTPS below.
    host: true,
    port: 5173,
    // https: true, // uncomment + run `vite --https` setup if testing camera from another device on your network
  },
});
