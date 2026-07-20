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
  const [activeTab, setActiveTab] = useState(0);
  const rememberTutorTimezone = useCallback((timezone: string) => setTutorTimezone(timezone), []);

  return (
    <main className="workspace-shell"><section className="hero">
      <h1>Tutor workspace</h1>
      <div className="workspace-tabs" role="tablist" aria-label="Tutor workspace sections">
        {["Students & Calendar", "Availability & Business", "Requests"].map((label, index) => (
          <button
            key={label}
            id={`workspace-tab-${index}`}
            role="tab"
            aria-controls={`workspace-panel-${index}`}
            aria-selected={activeTab === index}
            onClick={() => setActiveTab(index)}
          >
            {label}
          </button>
        ))}
      </div>
      <section
        id="workspace-panel-0"
        role="tabpanel"
        aria-labelledby="workspace-tab-0"
        className="tutor-dashboard-grid"
        hidden={activeTab !== 0}
      >
        <div className="tutor-students">{tutorTimezone ? <StudentList key={tutorTimezone} csrfToken={csrfToken} tutorTimezone={tutorTimezone} /> : null}</div>
        <div className="tutor-calendar">{tutorTimezone ? <BookingCalendar key={tutorTimezone} csrfToken={csrfToken} tutorTimezone={tutorTimezone} /> : null}</div>
      </section>
      <section
        id="workspace-panel-1"
        role="tabpanel"
        aria-labelledby="workspace-tab-1"
        className="tutor-dashboard-grid"
        hidden={activeTab !== 1}
      >
        <div className="tutor-students">{tutorTimezone ? <AvailabilityCalendar key={tutorTimezone} csrfToken={csrfToken} tutorTimezone={tutorTimezone} /> : null}</div>
        <div className="tutor-calendar"><BusinessSettings csrfToken={csrfToken} onTimezoneChange={rememberTutorTimezone} /></div>
      </section>
      <div id="workspace-panel-2" role="tabpanel" aria-labelledby="workspace-tab-2" hidden={activeTab !== 2}>
        <InquiryQueue csrfToken={csrfToken} />
        <LoginRequestQueue csrfToken={csrfToken} />
        <RefundQueue csrfToken={csrfToken} />
        <InvitationManager csrfToken={csrfToken} />
      </div>
      <button onClick={onLogOut}>Log out</button>
    </section></main>
  );
}
