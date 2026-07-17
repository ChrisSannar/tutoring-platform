import { useEffect, useState } from "react";

type Student = { id: string; email: string; display_name: string };

export function StudentList() {
  const [students, setStudents] = useState<Student[]>([]);

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

  return (
    <section aria-labelledby="students-heading">
      <h2 id="students-heading">Students</h2>
      {students.length === 0 ? <p>No Students yet.</p> : null}
      {students.map((student) => (
        <article key={student.id} aria-label={student.display_name}>
          <h3>{student.display_name}</h3>
          <p>{student.email}</p>
        </article>
      ))}
    </section>
  );
}
