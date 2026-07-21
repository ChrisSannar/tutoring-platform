import { useCallback, useEffect, useState } from "react";

type Booking = {
  id: string;
  start_at: string;
  focus: string | null;
  status: "upcoming" | "completed" | "cancelled";
  student: { display_name: string };
};

type Student = { id: string; display_name: string };
type View = "students" | "requests";

type OverviewData = {
  bookings: Booking[];
  students: Student[];
  inquiries: Array<{ status: "new" | "invited" }>;
  loginRequests: Array<{ status: "pending" | "generated" }>;
  refundRequests: Array<{ status: "pending" | "declined" | "refunded" }>;
  timezone: string;
};

type TutorOverviewProps = {
  onSelectView: (view: View) => void;
  onTimezoneChange: (timezone: string) => void;
  onOpenRequestsChange: (count: number) => void;
};

function localDateKey(value: Date, timezone: string) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat("en-US", {
    timeZone: timezone,
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(value).filter((part) => part.type !== "literal").map((part) => [part.type, part.value]));
  return `${parts.year}-${parts.month}-${parts.day}`;
}

function dayNumber(dateKey: string) {
  return Date.parse(`${dateKey}T00:00:00Z`) / 86_400_000;
}

export function summarizeTutorOverview(data: OverviewData, now = new Date()) {
  const today = localDateKey(now, data.timezone);
  const todayNumber = dayNumber(today);
  const monday = todayNumber - ((new Date(`${today}T00:00:00Z`).getUTCDay() + 6) % 7);
  const activeBookings = data.bookings.filter((booking) => booking.status !== "cancelled");
  const futureBookings = activeBookings
    .filter((booking) => new Date(booking.start_at) > now)
    .sort((left, right) => Date.parse(left.start_at) - Date.parse(right.start_at));
  const newInquiries = data.inquiries.filter((item) => item.status === "new").length;
  const pendingLoginRequests = data.loginRequests.filter((item) => item.status === "pending").length;
  const pendingRefundRequests = data.refundRequests.filter((item) => item.status === "pending").length;

  return {
    weekday: new Intl.DateTimeFormat("en-US", { weekday: "long", timeZone: data.timezone }).format(now),
    sessionsToday: activeBookings.filter((booking) => localDateKey(new Date(booking.start_at), data.timezone) === today).length,
    bookingsThisWeek: activeBookings.filter((booking) => {
      const bookingDay = dayNumber(localDateKey(new Date(booking.start_at), data.timezone));
      return bookingDay >= monday && bookingDay <= monday + 6;
    }).length,
    upcomingToday: futureBookings.filter((booking) => localDateKey(new Date(booking.start_at), data.timezone) === today),
    nextBooking: futureBookings[0] ?? null,
    students: [...data.students].sort((left, right) => left.display_name.localeCompare(right.display_name)),
    newInquiries,
    pendingLoginRequests,
    pendingRefundRequests,
    openRequests: newInquiries + pendingLoginRequests + pendingRefundRequests,
  };
}

async function json(response: Response) {
  if (!response.ok) throw new Error("Tutor overview request failed");
  return response.json();
}

export function TutorOverview({ onSelectView, onTimezoneChange, onOpenRequestsChange }: TutorOverviewProps) {
  const [data, setData] = useState<OverviewData | null>(null);
  const [failed, setFailed] = useState(false);

  const load = useCallback(async () => {
    setFailed(false);
    setData(null);
    try {
      const [bookings, students, inquiries, loginRequests, refundRequests, settings] = await Promise.all([
        fetch("/api/tutor/bookings").then(json),
        fetch("/api/tutor/students").then(json),
        fetch("/api/tutor/inquiries").then(json),
        fetch("/api/tutor/login-requests").then(json),
        fetch("/api/tutor/refund-requests").then(json),
        fetch("/api/tutor/settings").then(json),
      ]);
      const loaded = {
        bookings: bookings.bookings,
        students: students.students,
        inquiries: inquiries.inquiries,
        loginRequests: loginRequests.login_requests,
        refundRequests: refundRequests.refund_requests,
        timezone: settings.tutor_timezone,
      };
      setData(loaded);
      onTimezoneChange(loaded.timezone);
      onOpenRequestsChange(
        loaded.inquiries.filter((item: { status: string }) => item.status === "new").length
        + loaded.loginRequests.filter((item: { status: string }) => item.status === "pending").length
        + loaded.refundRequests.filter((item: { status: string }) => item.status === "pending").length,
      );
    } catch {
      setFailed(true);
    }
  }, [onOpenRequestsChange, onTimezoneChange]);

  useEffect(() => { void load(); }, [load]);

  if (failed) return <section className="tutor-overview-state" role="alert"><p>Could not load the overview.</p><button type="button" onClick={load}>Retry</button></section>;
  if (!data) return <section className="tutor-overview-state" role="status"><p>Loading overview…</p></section>;

  const summary = summarizeTutorOverview(data);
  const time = (value: string) => new Intl.DateTimeFormat("en-US", { timeZone: data.timezone, hour: "numeric", minute: "2-digit" }).format(new Date(value));

  return <div className="tutor-overview" aria-live="polite">
    <header className="tutor-day"><h1>{summary.weekday}</h1></header>
    <section className="tutor-metrics" aria-label="Daily metrics">
      <div><span>Sessions today</span><strong>{summary.sessionsToday}</strong></div>
      <div><span>Bookings this week</span><strong>{summary.bookingsThisWeek}</strong></div>
      <div><span>Active Students</span><strong>{summary.students.length}</strong></div>
      <div><span>Open requests</span><strong>{summary.openRequests}</strong></div>
    </section>
    <section className="tutor-overview-grid">
      <article className="overview-upcoming">
        <header><h2>Upcoming Bookings</h2><button type="button" onClick={() => onSelectView("students")}>Open calendar</button></header>
        {summary.upcomingToday.length === 0 ? <p className="overview-empty">No more Bookings today.</p> : <div className="booking-ledger">
          {summary.upcomingToday.map((booking) => <div key={booking.id}>
            <time dateTime={booking.start_at}>{time(booking.start_at)}</time>
            <span><strong>{booking.student.display_name}</strong><small>{booking.focus || "No Booking Focus"}</small></span>
            <i>Scheduled</i>
          </div>)}
        </div>}
      </article>
      <article className="overview-next"><span>Next Booking</span>{summary.nextBooking ? <><strong>{time(summary.nextBooking.start_at)}</strong><h2>{summary.nextBooking.student.display_name}</h2><p>{summary.nextBooking.focus || "No Booking Focus"}</p></> : <p className="overview-empty">No upcoming Bookings.</p>}</article>
      <article className="overview-students"><header><h2>Students</h2><button type="button" onClick={() => onSelectView("students")}>All {summary.students.length}</button></header>{summary.students.length === 0 ? <p className="overview-empty">No Students yet.</p> : <ul>{summary.students.slice(0, 4).map((student) => <li key={student.id}>{student.display_name}</li>)}</ul>}</article>
      <article className="overview-requests"><header><h2>Request Queue</h2><button type="button" onClick={() => onSelectView("requests")}>{summary.openRequests} open</button></header>{summary.openRequests === 0 ? <p className="overview-empty">No open requests.</p> : <dl><div><dt>New Inquiries</dt><dd>{summary.newInquiries}</dd></div><div><dt>Pending Login Requests</dt><dd>{summary.pendingLoginRequests}</dd></div><div><dt>Pending Refund Requests</dt><dd>{summary.pendingRefundRequests}</dd></div></dl>}</article>
    </section>
  </div>;
}
