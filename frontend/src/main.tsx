import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import "./styles.css";

function LandingPage() {
  return (
    <main>
      <section className="hero" aria-labelledby="hero-heading">
        <p className="eyebrow">One-to-one learning</p>
        <h1 id="hero-heading">Personal tutoring, thoughtfully planned.</h1>
        <p className="intro">
          Focused sessions shaped around your goals, your questions, and the way
          you learn best.
        </p>
        <a href="mailto:tutor@example.com">Ask about tutoring</a>
      </section>
    </main>
  );
}

const root = document.getElementById("root");

if (!root) {
  throw new Error("Application root is missing");
}

createRoot(root).render(
  <StrictMode>
    <LandingPage />
  </StrictMode>,
);
