import { type FormEvent, useState } from "react";

type Screen = "request" | "sent" | "confirm" | "invalid";

function initialScreen(): Screen {
  return window.location.pathname === "/sign-in/confirm" ? "confirm" : "request";
}

export function LoginAuthentication() {
  const [screen, setScreen] = useState<Screen>(initialScreen);
  const [email, setEmail] = useState("");

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
    if (!response.ok) return setScreen("invalid");
    const authenticated = await response.json();
    window.location.assign(authenticated.role === "tutor" ? "/tutor" : "/student");
  }

  if (screen === "sent") return <main><h1>Login Request received</h1><p>If the address is eligible, the Tutor will send a Login Link.</p></main>;
  if (screen === "invalid") return <main><h1>Login Link unavailable</h1></main>;
  if (screen === "confirm") return <main><h1>Confirm sign-in</h1><button onClick={confirmSignIn}>Confirm sign-in</button></main>;
  return <main><h1>Log In</h1><form onSubmit={requestLink}><label htmlFor="login-email">Email address</label><input id="login-email" type="email" value={email} onChange={(event) => setEmail(event.target.value)} required /><button type="submit">Request Login Link</button></form></main>;
}
