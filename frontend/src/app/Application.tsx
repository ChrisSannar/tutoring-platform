import { LoginAuthentication } from "../auth/LoginAuthentication";
import { InviteeSetup } from "../invitations/InviteeSetup";
import { LandingPage } from "../landing/LandingPage";
import { StudentWorkspace } from "../students/StudentWorkspace";
import { CheckoutStatus } from "../students/CheckoutStatus";
import { TutorAuthentication } from "../tutor/TutorAuthentication";
import { StylePrototype } from "../style-prototype/StylePrototype";

type ApplicationProps = {
  theme: "light" | "dark";
  onThemeToggle: () => void;
  onTutorWorkspaceChange: (visible: boolean) => void;
};

export function Application({ theme, onThemeToggle, onTutorWorkspaceChange }: ApplicationProps) {
  const { pathname } = window.location;

  const stylePrototype = pathname.match(/^\/style-prototype\/(10|[1-9])$/);
  if (stylePrototype) {
    return <StylePrototype variant={Number(stylePrototype[1])} />;
  }

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
