import { useEffect, useState } from "react";
import { BookableSlots } from "./BookableSlots";
import { LessonNotes } from "./LessonNotes";

type Student = {
  role: "student";
  email: string;
  display_name: string;
};

export function StudentWorkspace() {
  const [student, setStudent] = useState<Student | null>(null);
  const [unavailable, setUnavailable] = useState(false);

  useEffect(() => {
    if (student) return;
    void fetch("/api/student/session").then(async (response) => {
      if (!response.ok) {
        setUnavailable(true);
        return;
      }
      setStudent(await response.json());
    });
  }, [student]);

  if (unavailable) return <main><p>Student Session unavailable</p></main>;
  if (!student) return <main><p>Loading Student Session…</p></main>;
  return (
    <main><section className="hero">
      <p className="eyebrow">Your tutoring</p>
      <h1>Student workspace</h1>
      <p>Welcome, {student.display_name}</p>
      <p className="intro">Choose one available tutoring time, keep your calendar export, and return here for notes the Tutor has published after each lesson.</p>
      <section className="student-dashboard-grid" aria-label="Tutoring calendar and Shared Lesson Notes">
        <div className="student-calendar"><BookableSlots /></div>
        <div className="student-notes"><LessonNotes /></div>
      </section>
    </section></main>
  );
}
