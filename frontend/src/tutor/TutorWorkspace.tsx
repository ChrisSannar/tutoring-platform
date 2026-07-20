import { useCallback, useState } from "react";
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
  const [tutorTimezone, setTutorTimezone] = useState("");
  const rememberTutorTimezone = useCallback((timezone: string) => setTutorTimezone(timezone), []);
  return (
    <main><section className="hero">
      <h1>Tutor workspace</h1>
      <BusinessSettings csrfToken={csrfToken} onTimezoneChange={rememberTutorTimezone} />
      {tutorTimezone ? <AvailabilityCalendar key={tutorTimezone} csrfToken={csrfToken} tutorTimezone={tutorTimezone} /> : null}
      <section className="tutor-dashboard-grid" aria-label="Students and weekly Booking calendar">
        <div className="tutor-students">{tutorTimezone ? <StudentList key={tutorTimezone} csrfToken={csrfToken} tutorTimezone={tutorTimezone} /> : null}</div>
        <div className="tutor-calendar">{tutorTimezone ? <BookingCalendar key={tutorTimezone} csrfToken={csrfToken} tutorTimezone={tutorTimezone} /> : null}</div>
      </section>
      <RefundQueue csrfToken={csrfToken} />
      <LoginRequestQueue csrfToken={csrfToken} />
      <InvitationManager csrfToken={csrfToken} />
      <InquiryQueue csrfToken={csrfToken} />
      <button onClick={onLogOut}>Log out</button>
    </section></main>
  );
}
