import { BusinessSettings } from "./BusinessSettings";
import { InvitationManager } from "./InvitationManager";
import { InquiryQueue } from "./InquiryQueue";
import { StudentList } from "./StudentList";
import { LoginRequestQueue } from "./LoginRequestQueue";
import { AvailabilityCalendar } from "./AvailabilityCalendar";
import { BookingCalendar } from "./BookingCalendar";
import { RefundQueue } from "./RefundQueue";

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
      <section className="tutor-dashboard-grid" aria-label="Students and weekly Booking calendar">
        <div className="tutor-students"><StudentList csrfToken={csrfToken} /></div>
        <div className="tutor-calendar"><BookingCalendar csrfToken={csrfToken} /></div>
      </section>
      <RefundQueue csrfToken={csrfToken} />
      <LoginRequestQueue csrfToken={csrfToken} />
      <InvitationManager csrfToken={csrfToken} />
      <InquiryQueue csrfToken={csrfToken} />
      <button onClick={onLogOut}>Log out</button>
    </section></main>
  );
}
