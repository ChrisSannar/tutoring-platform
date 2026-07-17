import { useEffect, useState } from "react";

type Student = { id: string; email: string; display_name: string };
type StudentDetail = Student & {
  funding: { first_session_promotion: "available" | "unavailable"; session_credits: number };
  pending_refund_requests: Array<{ id: string }>;
  upcoming_booking: { id: string } | null;
};

export function StudentList({ csrfToken }: { csrfToken: string }) {
  const [students, setStudents] = useState<Student[]>([]);
  const [search, setSearch] = useState("");
  const [detail, setDetail] = useState<StudentDetail | null>(null);
  const [creditQuantity, setCreditQuantity] = useState("");
  const [creditReason, setCreditReason] = useState("");
  const [complimentaryStart, setComplimentaryStart] = useState("");
  const [complimentaryFocus, setComplimentaryFocus] = useState("");

  useEffect(() => {
    function loadStudents() {
      void fetch("/api/tutor/students")
        .then((response) => response.json())
        .then((body) => setStudents(body.students));
    }
    loadStudents();
    window.addEventListener("students-changed", loadStudents);
    return () => window.removeEventListener("students-changed", loadStudents);
  }, []);

  useEffect(() => {
    if (!detail) return;
    function closeOnEscape(event: KeyboardEvent) {
      if (event.key === "Escape") setDetail(null);
    }
    window.addEventListener("keydown", closeOnEscape);
    return () => window.removeEventListener("keydown", closeOnEscape);
  }, [detail]);

  async function openStudent(student: Student) {
    const response = await fetch(`/api/tutor/students/${student.id}`);
    if (response.ok) setDetail(await response.json());
  }

  async function adjustCredits() {
    if (!detail) return;
    const response = await fetch(`/api/tutor/students/${detail.id}/credits`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify({
        quantity: Number(creditQuantity),
        reason: creditReason,
      }),
    });
    if (!response.ok) return;
    const funding = await response.json();
    setDetail({
      ...detail,
      funding: { ...detail.funding, session_credits: funding.session_credits },
    });
    setCreditQuantity("");
    setCreditReason("");
  }

  async function createComplimentaryBooking() {
    if (!detail) return;
    const response = await fetch(`/api/tutor/students/${detail.id}/bookings`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken, "Idempotency-Key": crypto.randomUUID() },
      body: JSON.stringify({ start_at: new Date(complimentaryStart).toISOString(), focus: complimentaryFocus || null, complimentary: true }),
    });
    if (!response.ok) return;
    const booking = await response.json();
    setDetail({ ...detail, upcoming_booking: { id: booking.id } });
  }

  const query = search.trim().toLowerCase();
  const visibleStudents = students.filter((student) =>
    `${student.display_name} ${student.email}`.toLowerCase().includes(query),
  );

  return (
    <section aria-labelledby="students-heading">
      <h2 id="students-heading">Students</h2>
      <label htmlFor="student-search">Search Students</label>
      <input
        id="student-search"
        type="search"
        value={search}
        onChange={(event) => setSearch(event.target.value)}
      />
      {visibleStudents.length === 0 ? <p>No matching Students.</p> : null}
      {visibleStudents.map((student) => (
        <article key={student.id}>
          <button onClick={() => openStudent(student)}>{student.display_name}</button>
          <p>{student.email}</p>
        </article>
      ))}
      {detail ? (
        <dialog
          open
          aria-labelledby="student-detail-heading"
          onClose={() => setDetail(null)}
        >
          <h2 id="student-detail-heading">Student Detail</h2>
          <label htmlFor="student-detail-name">Name</label>
          <input id="student-detail-name" value={detail.display_name} readOnly />
          <label htmlFor="student-detail-email">Login email</label>
          <input id="student-detail-email" value={detail.email} readOnly />
          <p>
            First Session Promotion: {detail.funding.first_session_promotion === "available" ? "Available" : "Unavailable"}
          </p>
          <p>Session Credits: {detail.funding.session_credits}</p>
          <label htmlFor="credit-adjustment">Credit adjustment</label>
          <input
            id="credit-adjustment"
            type="number"
            value={creditQuantity}
            onChange={(event) => setCreditQuantity(event.target.value)}
          />
          <label htmlFor="credit-reason">Adjustment reason</label>
          <input
            id="credit-reason"
            value={creditReason}
            onChange={(event) => setCreditReason(event.target.value)}
            maxLength={500}
          />
          <button
            disabled={!creditQuantity || !creditReason.trim()}
            onClick={adjustCredits}
          >
            Apply credit adjustment
          </button>
          <p>
            Refund Requests: {detail.pending_refund_requests.length === 0 ? "None" : detail.pending_refund_requests.length}
          </p>
          <p>Upcoming Booking: {detail.upcoming_booking ? "Scheduled" : "None"}</p>
          <label htmlFor="complimentary-start">Complimentary Booking start</label>
          <input id="complimentary-start" type="datetime-local" value={complimentaryStart} onChange={(event) => setComplimentaryStart(event.target.value)} />
          <label htmlFor="complimentary-focus">Complimentary Booking Focus</label>
          <input id="complimentary-focus" maxLength={500} value={complimentaryFocus} onChange={(event) => setComplimentaryFocus(event.target.value)} />
          <button disabled={!complimentaryStart} onClick={createComplimentaryBooking}>Create Complimentary Booking</button>
          <button autoFocus onClick={() => setDetail(null)}>
            Close Student Detail
          </button>
        </dialog>
      ) : null}
    </section>
  );
}
