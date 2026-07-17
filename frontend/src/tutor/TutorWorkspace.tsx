import { BusinessSettings } from "./BusinessSettings";
import { InvitationManager } from "./InvitationManager";
import { InquiryQueue } from "./InquiryQueue";
import { PendingSessionRequests } from "./PendingSessionRequests";
import { StudentList } from "./StudentList";
import { LoginRequestQueue } from "./LoginRequestQueue";
import { AvailabilityCalendar } from "./AvailabilityCalendar";
import { BookingCalendar } from "./BookingCalendar";

type TutorWorkspaceProps = {
  csrfToken: string;
  onLogOut: () => void;
};

export function TutorWorkspace({ csrfToken, onLogOut }: TutorWorkspaceProps) {
  return (
    <main><section className="hero">
      <h1>Tutor workspace</h1>
      <BusinessSettings csrfToken={csrfToken} />
      <AvailabilityCalendar csrfToken={csrfToken} />
      <BookingCalendar csrfToken={csrfToken} />
      <StudentList csrfToken={csrfToken} />
      <LoginRequestQueue csrfToken={csrfToken} />
      <PendingSessionRequests csrfToken={csrfToken} />
      <InvitationManager csrfToken={csrfToken} />
      <InquiryQueue csrfToken={csrfToken} />
      <button onClick={onLogOut}>Log out</button>
    </section></main>
  );
}
