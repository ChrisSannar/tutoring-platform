import { type FormEvent, useEffect, useState } from "react";

import { csrfTokenFromCookie } from "../web/csrfToken";
import { TutorWorkspace } from "./TutorWorkspace";

type Screen = "loading" | "sign-in" | "sent" | "confirm" | "workspace";

function initialScreen(): Screen {
  if (window.location.pathname === "/tutor/sign-in/confirm") return "confirm";
  if (window.location.pathname === "/tutor") return "loading";
  return "sign-in";
}

export function TutorAuthentication() {
  const [screen, setScreen] = useState<Screen>(initialScreen);
  const [email, setEmail] = useState("");
  const [csrfToken, setCsrfToken] = useState("");

  useEffect(() => {
    if (screen !== "loading") return;
    void fetch("/api/tutor/session").then((response) => {
      if (!response.ok) {
        setScreen("sign-in");
        return;
      }
      setCsrfToken(csrfTokenFromCookie());
      setScreen("workspace");
    });
  }, [screen]);

  async function requestLink(event: FormEvent) {
    event.preventDefault();
    await fetch("/api/auth/magic-links", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email }),
    });
    setScreen("sent");
  }

  async function confirmSignIn() {
    const token = new URLSearchParams(window.location.search).get("token");
    const response = await fetch("/api/auth/magic-links/confirm", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ token }),
    });
    if (!response.ok) return;
    const authenticated = await response.json();
    setCsrfToken(authenticated.csrf_token);
    window.history.replaceState({}, "", "/tutor");
    setScreen("workspace");
  }

  async function logOut() {
    const response = await fetch("/api/auth/logout", {
      method: "POST",
      headers: { "X-CSRF-Token": csrfToken },
    });
    if (!response.ok) return;
    window.history.replaceState({}, "", "/tutor/sign-in");
    setScreen("sign-in");
  }

  if (screen === "sent") {
    return (
      <main><section className="hero"><h1>Check the development outbox</h1></section></main>
    );
  }
  if (screen === "loading") {
    return <main><p>Loading Tutor session…</p></main>;
  }
  if (screen === "confirm") {
    return (
      <main><section className="hero">
        <h1>Confirm Tutor sign-in</h1>
        <button onClick={confirmSignIn}>Confirm sign-in</button>
      </section></main>
    );
  }
  if (screen === "workspace") {
    return <TutorWorkspace csrfToken={csrfToken} onLogOut={logOut} />;
  }
  return (
    <main><section className="hero">
      <h1>Tutor sign-in</h1>
      <form onSubmit={requestLink}>
        <label htmlFor="tutor-email">Email address</label>
        <input
          id="tutor-email"
          type="email"
          value={email}
          onChange={(event) => setEmail(event.target.value)}
          required
        />
        <button type="submit">Email me a sign-in link</button>
      </form>
    </section></main>
  );
}
