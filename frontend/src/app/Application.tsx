import { InvitationClaimConfirmation } from "../invitations/InvitationClaimConfirmation";
import { LoginAuthentication } from "../auth/LoginAuthentication";
import { InviteeSetup } from "../invitations/InviteeSetup";
import { LandingPage } from "../landing/LandingPage";
import { StudentWorkspace } from "../students/StudentWorkspace";
import { TutorAuthentication } from "../tutor/TutorAuthentication";

export function Application() {
  const { pathname } = window.location;

  if (pathname === "/student/claim/confirm") {
    return <InvitationClaimConfirmation />;
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
