import { LoginAuthentication } from "../auth/LoginAuthentication";
import { InviteeSetup } from "../invitations/InviteeSetup";
import { LandingPage } from "../landing/LandingPage";
import { StudentWorkspace } from "../students/StudentWorkspace";
import { CheckoutStatus } from "../students/CheckoutStatus";
import { TutorAuthentication } from "../tutor/TutorAuthentication";

type ApplicationProps = {
  theme: "light" | "dark";
  onThemeToggle: () => void;
  onTutorWorkspaceChange: (visible: boolean) => void;
};

export function Application({ theme, onThemeToggle, onTutorWorkspaceChange }: ApplicationProps) {
  const { pathname } = window.location;

  if (pathname.startsWith("/sign-in")) {
    return <LoginAuthentication />;
  }
  if (pathname === "/student") {
    return <StudentWorkspace />;
  }
  if (pathname === "/checkout/return" || pathname.startsWith("/checkout/fake/")) {
    return <CheckoutStatus />;
  }
  if (pathname.startsWith("/invite/")) {
    return <InviteeSetup />;
  }
  if (pathname.startsWith("/tutor")) {
    return <TutorAuthentication theme={theme} onThemeToggle={onThemeToggle} onWorkspaceChange={onTutorWorkspaceChange} />;
  }
  return <LandingPage />;
}
