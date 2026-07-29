import { useEffect, useState } from "react";

import { LoginAuthentication } from "../auth/LoginAuthentication";
import { InviteeSetup } from "../invitations/InviteeSetup";
import { LandingPage } from "../landing/LandingPage";
import { StudentWorkspace } from "../students/StudentWorkspace";
import { TutorAuthentication } from "../tutor/TutorAuthentication";

type Role = "student" | "tutor";

export function Application() {
  const { pathname } = window.location;
  const requiredRole: Role | null = pathname.startsWith("/tutor")
    ? "tutor"
    : pathname === "/student" || pathname.startsWith("/student/")
      ? "student"
      : null;
  const [checkingRole, setCheckingRole] = useState(requiredRole !== null);

  useEffect(() => {
    if (!requiredRole) return;
    void fetch("/api/auth/session").then(async (response) => {
      if (!response.ok) return setCheckingRole(false);
      const session = await response.json() as { role?: string };
      const home = session.role === "tutor" ? "/tutor" : session.role === "student" ? "/student" : null;
      // ponytail: unknown roles fail open (each API call 401s on its own) — never redirect to our own URL
      if (home !== null && session.role !== requiredRole && !pathname.startsWith(home)) {
        window.location.replace(home);
      } else {
        setCheckingRole(false);
      }
    }).catch(() => setCheckingRole(false));
  }, [requiredRole]);

  if (checkingRole) {
    return <main><p>Loading session…</p></main>;
  }

  if (pathname.startsWith("/sign-in")) {
    return <LoginAuthentication />;
  }
  if (pathname === "/student") {
    return <StudentWorkspace />;
  }
  if (pathname.startsWith("/invite/")) {
    return <InviteeSetup />;
  }
  if (pathname.startsWith("/tutor")) {
    return <TutorAuthentication />;
  }
  return <LandingPage />;
}
