import { StrictMode, useEffect, useState } from "react";
import { createRoot } from "react-dom/client";

import { Application } from "./app/Application";
import "./styles.css";

const root = document.getElementById("root");

if (!root) {
  throw new Error("Application root is missing");
}

const themeKey = "theme";

function App() {
  const [darkMode, setDarkMode] = useState(() =>
    localStorage.getItem(themeKey) === "dark" ||
    (!localStorage.getItem(themeKey) && matchMedia("(prefers-color-scheme: dark)").matches),
  );

  useEffect(() => {
    const theme = darkMode ? "dark" : "light";
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(themeKey, theme);
  }, [darkMode]);

  return (
    <div className="app-shell">
      <Application />
      <footer className="app-footer">
        <small>© 2026 Tutoring Platform</small>
        <button
          type="button"
          aria-pressed={darkMode}
          className="theme-toggle"
          onClick={() => setDarkMode((enabled) => !enabled)}
        >
          {darkMode ? "Light mode" : "Dark mode"}
        </button>
      </footer>
    </div>
  );
}

createRoot(root).render(
  <StrictMode>
    <App />
  </StrictMode>,
);
