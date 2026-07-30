import { useEffect, useState } from "react";

import { LoginAuthentication } from "../auth/LoginAuthentication";
import { InviteeSetup } from "../invitations/InviteeSetup";
import { LandingPage } from "../landing/LandingPage";
import { StudentWorkspace } from "../students/StudentWorkspace";
import { TutorAuthentication } from "../tutor/TutorAuthentication";

type Role = "student" | "tutor";

export function Application() {
  const { pathname } = window.location;
  const knownPath = pathname === "/" ||
    pathname === "/student" ||
    pathname === "/sign-in" ||
    pathname === "/sign-in/confirm" ||
    pathname === "/tutor" ||
    pathname === "/tutor/sign-in" ||
    pathname === "/tutor/sign-in/confirm" ||
    pathname.startsWith("/invite/");
  const requiredRole: Role | null = pathname === "/tutor" ||
    pathname === "/tutor/sign-in" ||
    pathname === "/tutor/sign-in/confirm"
    ? "tutor"
    : pathname === "/student"
      ? "student"
      : null;
  const [checkingRole, setCheckingRole] = useState(requiredRole !== null);

  useEffect(() => {
    if (!knownPath) {
      window.location.replace("/");
      return;
    }
    if (!requiredRole) return;
    void fetch("/api/auth/session").then(async (response) => {
      if (!response.ok) {
        if (requiredRole === "student") window.location.replace("/");
        else setCheckingRole(false);
        return;
      }
      const session = await response.json() as { role?: string };
      const home = session.role === "tutor" ? "/tutor" : session.role === "student" ? "/student" : null;
      if (home !== null && session.role !== requiredRole && !pathname.startsWith(home)) {
        window.location.replace(home);
      } else if (requiredRole === "student" && session.role !== "student") {
        window.location.replace("/");
      } else {
        setCheckingRole(false);
      }
    }).catch(() => {
      if (requiredRole === "student") window.location.replace("/");
      else setCheckingRole(false);
    });
  }, [knownPath, pathname, requiredRole]);

  if (!knownPath || checkingRole) {
    return <main><p>Loading session…</p></main>;
  }

  if (pathname === "/sign-in" || pathname === "/sign-in/confirm") {
    return <LoginAuthentication />;
  }
  if (pathname === "/student") {
    return <StudentWorkspace />;
  }
  if (pathname.startsWith("/invite/")) {
    return <InviteeSetup />;
  }
  if (requiredRole === "tutor") {
    return <TutorAuthentication />;
  }
  return <LandingPage />;
}
