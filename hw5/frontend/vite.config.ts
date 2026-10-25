import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// The Campus Customs desk runs on the Vite default port 5173, which the FastAPI
// backend (http://localhost:8000) allows via CORS.
export default defineConfig({
  plugins: [react()],
  server: { port: 5173 },
});
