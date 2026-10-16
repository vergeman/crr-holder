import React from "react";
import { createRoot } from "react-dom/client";
import { BenchmarkPage } from "./components/benchmark";

if (import.meta.env.DEV) {
  createRoot(document.getElementById("root")).render(<BenchmarkPage />);
}
