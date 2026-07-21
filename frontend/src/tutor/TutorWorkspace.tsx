import { useCallback, useState } from "react";
import { AvailabilityCalendar } from "./AvailabilityCalendar";
import { BookingCalendar } from "./BookingCalendar";
import { BusinessSettings } from "./BusinessSettings";
import { InquiryQueue } from "./InquiryQueue";
import { InvitationManager } from "./InvitationManager";
import { LoginRequestQueue } from "./LoginRequestQueue";
import { RefundQueue } from "./RefundQueue";
import { StudentList } from "./StudentList";
import { TutorOverview } from "./TutorOverview";

type View = "overview" | "students" | "business" | "requests";

type TutorWorkspaceProps = {
  csrfToken: string;
  onLogOut: () => void;
  theme: "light" | "dark";
  onThemeToggle: () => void;
};

const views: Array<{ id: View; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "students", label: "Students & Calendar" },
  { id: "business", label: "Availability & Business" },
  { id: "requests", label: "Requests" },
];

export function TutorWorkspace({ csrfToken, onLogOut, theme, onThemeToggle }: TutorWorkspaceProps) {
  const [tutorTimezone, setTutorTimezone] = useState("");
  const [openRequests, setOpenRequests] = useState(0);
  const [activeView, setActiveView] = useState<View>("overview");
  const rememberTutorTimezone = useCallback((timezone: string) => setTutorTimezone(timezone), []);

  return <main className="tutor-workspace">
    <aside className="tutor-rail">
      <div className="tutor-identity"><span>ARDEN</span><strong>✦</strong></div>
      <nav aria-label="Tutor workspace">
        {views.map((view) => <button
          key={view.id}
          type="button"
          aria-current={activeView === view.id ? "page" : undefined}
          onClick={() => setActiveView(view.id)}
        >{view.label}{view.id === "requests" && openRequests > 0 ? <span className="request-badge" aria-label={`${openRequests} open requests`}>{openRequests}</span> : null}</button>)}
      </nav>
      <div className="tutor-rail-actions">
        <button type="button" aria-pressed={theme === "dark"} onClick={onThemeToggle}>{theme === "dark" ? "Light mode" : "Dark mode"}</button>
        <button type="button" onClick={onLogOut}>Log out</button>
      </div>
    </aside>
    <section className="tutor-work-area">
      <div hidden={activeView !== "overview"}><TutorOverview onSelectView={setActiveView} onTimezoneChange={rememberTutorTimezone} onOpenRequestsChange={setOpenRequests} /></div>
      {activeView === "students" ? <section className="tutor-detail-grid" aria-label="Students & Calendar">
        <div>{tutorTimezone ? <StudentList csrfToken={csrfToken} tutorTimezone={tutorTimezone} /> : <p role="status">Loading Tutor Timezone…</p>}</div>
        <div>{tutorTimezone ? <BookingCalendar csrfToken={csrfToken} tutorTimezone={tutorTimezone} /> : null}</div>
      </section> : null}
      {activeView === "business" ? <section className="tutor-detail-grid" aria-label="Availability & Business">
        <div>{tutorTimezone ? <AvailabilityCalendar csrfToken={csrfToken} tutorTimezone={tutorTimezone} /> : null}</div>
        <div><BusinessSettings csrfToken={csrfToken} onTimezoneChange={rememberTutorTimezone} /></div>
      </section> : null}
      {activeView === "requests" ? <section className="tutor-requests" aria-label="Requests">
        <InquiryQueue csrfToken={csrfToken} />
        <LoginRequestQueue csrfToken={csrfToken} />
        <RefundQueue csrfToken={csrfToken} />
        <InvitationManager csrfToken={csrfToken} />
      </section> : null}
    </section>
  </main>;
}
