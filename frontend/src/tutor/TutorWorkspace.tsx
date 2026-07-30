import { useCallback, useState } from "react";
import { LogoutButton } from "../auth/LogoutButton";
import { AvailabilityCalendar } from "./AvailabilityCalendar";
import { BookingCalendar } from "./BookingCalendar";
import { BusinessSettings } from "./BusinessSettings";
import { InquiryQueue } from "./InquiryQueue";
import { InvitationManager } from "./InvitationManager";
import { LoginRequestQueue } from "./LoginRequestQueue";
import { StudentList } from "./StudentList";
import { TutorOverview } from "./TutorOverview";

type View = "overview" | "students" | "business" | "requests";

type TutorWorkspaceProps = {
  csrfToken: string;
};

const views: Array<{ id: View; label: string }> = [
  { id: "overview", label: "Overview" },
  { id: "students", label: "Students & Calendar" },
  { id: "business", label: "Availability & Business" },
  { id: "requests", label: "Requests" },
];

const themeKey = "theme";

export function TutorWorkspace({ csrfToken }: TutorWorkspaceProps) {
  const [tutorTimezone, setTutorTimezone] = useState("");
  const [openRequests, setOpenRequests] = useState(0);
  const [activeView, setActiveView] = useState<View>("overview");
  const [darkMode, setDarkMode] = useState(() =>
    localStorage.getItem(themeKey) === "dark" ||
    (!localStorage.getItem(themeKey) && matchMedia("(prefers-color-scheme: dark)").matches),
  );
  const rememberTutorTimezone = useCallback((timezone: string) => setTutorTimezone(timezone), []);

  // ponytail: writes theme directly instead of prop drilling; the footer
  // toggle label can lag one render if theme changes here then the footer
  // reappears — shared state module if that ever matters.
  function toggleTheme() {
    const enabled = !darkMode;
    setDarkMode(enabled);
    const theme = enabled ? "dark" : "light";
    document.documentElement.dataset.theme = theme;
    localStorage.setItem(themeKey, theme);
  }

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
        <button type="button" aria-pressed={darkMode} onClick={toggleTheme}>{darkMode ? "Light mode" : "Dark mode"}</button>
        <LogoutButton />
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
        <InvitationManager csrfToken={csrfToken} />
      </section> : null}
    </section>
  </main>;
}
