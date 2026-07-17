import { InvitationManager } from "./InvitationManager";
import { InquiryQueue } from "./InquiryQueue";
import { PendingSessionRequests } from "./PendingSessionRequests";
import { StudentList } from "./StudentList";

type TutorWorkspaceProps = {
  csrfToken: string;
  onLogOut: () => void;
};

export function TutorWorkspace({ csrfToken, onLogOut }: TutorWorkspaceProps) {
  return (
    <main><section className="hero">
      <h1>Tutor workspace</h1>
      <StudentList />
      <PendingSessionRequests csrfToken={csrfToken} />
      <InvitationManager csrfToken={csrfToken} />
      <InquiryQueue csrfToken={csrfToken} />
      <button onClick={onLogOut}>Log out</button>
    </section></main>
  );
}
