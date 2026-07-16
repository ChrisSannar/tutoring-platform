import { InvitationManager } from "./InvitationManager";
import { PendingSessionRequests } from "./PendingSessionRequests";

type TutorWorkspaceProps = {
  csrfToken: string;
  onLogOut: () => void;
};

export function TutorWorkspace({ csrfToken, onLogOut }: TutorWorkspaceProps) {
  return (
    <main><section className="hero">
      <h1>Tutor workspace</h1>
      <PendingSessionRequests csrfToken={csrfToken} />
      <InvitationManager csrfToken={csrfToken} />
      <button onClick={onLogOut}>Log out</button>
    </section></main>
  );
}
