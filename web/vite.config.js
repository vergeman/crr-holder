import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

export default defineConfig({
  plugins: [
    react(),
    {
      name: "benchmark-latency",
      configureServer(server) {
        server.middlewares.use((request, response, next) => {
          if (!request.url.startsWith("/api/")) return next();
          const marked = request.url.match(/^\/api\/_benchmark\/(\d+)\//);
          const latencyMs = Number(
            marked?.[1] ?? request.headers["x-benchmark-latency-ms"] ?? 0
          );
          if (marked || request.headers["x-benchmark-latency-ms"] !== undefined)
            response.setHeader("Cache-Control", "no-store");
          if (marked) request.url = request.url.replace(marked[0], "/api/");
          delete request.headers["x-benchmark-latency-ms"];

          // Delay only explicitly marked requests; normal app traffic is untouched.
          if (Number.isFinite(latencyMs) && latencyMs > 0) {
            const timer = setTimeout(next, latencyMs);
            response.once("close", () => clearTimeout(timer));
          } else {
            next();
          }
        });
      },
    },
  ],
  optimizeDeps: {
    exclude: ["@sqlite.org/sqlite-wasm", "sqlite-wasm-http"],
  },
  server: {
    proxy: {
      "/api": "http://api:8000",
    },
  },
});
