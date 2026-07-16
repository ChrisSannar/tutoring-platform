import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { Application } from "./app/Application";
import "./styles.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Application root is missing");
}

createRoot(root).render(
  <StrictMode>
    <Application />
  </StrictMode>,
);
