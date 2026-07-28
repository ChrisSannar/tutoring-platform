import { type FormEvent, useEffect, useState } from "react";

import { InquiryModal } from "./InquiryModal";

export function LandingPage() {
  const [tutorDashboard, setTutorDashboard] = useState(false);
  const [loginOpen, setLoginOpen] = useState(false);
  const [email, setEmail] = useState("");
  const [accepted, setAccepted] = useState(false);

  useEffect(() => {
    void fetch("/api/auth/session").then(async (response) => {
      if (!response.ok) return;
      const session = await response.json();
      if (session.role === "student") {
        window.location.replace("/student");
      } else {
        setTutorDashboard(true);
      }
    });
  }, []);

  async function requestLogin(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/auth/magic-links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    if (response.ok) setAccepted(true);
  }

  return (
    <main>
      <section className="hero landing-hero" aria-labelledby="hero-heading">
        <p className="eyebrow">One-to-one learning</p>
        <h1 id="hero-heading">Personal tutoring, thoughtfully planned.</h1>
        <p className="intro">
          Focused sessions shaped around your goals, your questions, and the way
          you learn best.
        </p>
        <InquiryModal />
        {tutorDashboard ? (
          <a href="/tutor">Dashboard</a>
        ) : (
          <button type="button" onClick={() => setLoginOpen(true)}>
            I’m already a student
          </button>
        )}
      </section>
      {loginOpen ? (
        <dialog open aria-labelledby="student-login-heading">
          <h2 id="student-login-heading">
            {accepted ? "Login Request received" : "Request a Login Link"}
          </h2>
          {accepted ? (
            <>
              <p>The Tutor will send your Login Link to the email on your Student account.</p>
              <button type="button" onClick={() => setLoginOpen(false)}>Close</button>
            </>
          ) : (
            <form onSubmit={requestLogin}>
              <label htmlFor="student-login-email">Email address</label>
              <input
                id="student-login-email"
                type="email"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
              <button type="submit">Request Login Link</button>
              <button type="button" onClick={() => setLoginOpen(false)}>Cancel</button>
            </form>
          )}
        </dialog>
      ) : null}
    </main>
  );
}
