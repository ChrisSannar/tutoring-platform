import { useEffect, useState } from "react";

import { InquiryModal } from "./InquiryModal";

export function LandingPage() {
  const [dashboardPath, setDashboardPath] = useState("");

  useEffect(() => {
    void fetch("/api/auth/session").then(async (response) => {
      if (!response.ok) return;
      const session = await response.json();
      setDashboardPath(session.role === "tutor" ? "/tutor" : "/student");
    });
  }, []);

  return (
    <main>
      <section className="hero" aria-labelledby="hero-heading">
        <p className="eyebrow">One-to-one learning</p>
        <h1 id="hero-heading">Personal tutoring, thoughtfully planned.</h1>
        <p className="intro">
          Focused sessions shaped around your goals, your questions, and the way
          you learn best.
        </p>
        <InquiryModal />
        <a href={dashboardPath || "/sign-in"}>
          {dashboardPath ? "Dashboard" : "Log In"}
        </a>
      </section>
    </main>
  );
}
