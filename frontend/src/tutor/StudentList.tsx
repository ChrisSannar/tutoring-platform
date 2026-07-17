import { useEffect, useState } from "react";

type Student = { id: string; email: string; display_name: string };
type StudentDetail = Student & {
  funding: { first_session_promotion: "available" | "unavailable"; session_credits: number };
  pending_refund_requests: Array<{ id: string }>;
  upcoming_booking: { id: string } | null;
};

export function StudentList() {
  const [students, setStudents] = useState<Student[]>([]);
  const [search, setSearch] = useState("");
  const [detail, setDetail] = useState<StudentDetail | null>(null);

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

  async function openStudent(student: Student) {
    const response = await fetch(`/api/tutor/students/${student.id}`);
    if (response.ok) setDetail(await response.json());
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
          onKeyDown={(event) => {
            if (event.key === "Escape") setDetail(null);
          }}
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
          <p>
            Refund Requests: {detail.pending_refund_requests.length === 0 ? "None" : detail.pending_refund_requests.length}
          </p>
          <p>Upcoming Booking: {detail.upcoming_booking ? "Scheduled" : "None"}</p>
          <button autoFocus onClick={() => setDetail(null)}>
            Close Student Detail
          </button>
        </dialog>
      ) : null}
    </section>
  );
}
