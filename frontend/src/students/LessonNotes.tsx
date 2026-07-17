import { useEffect, useState } from "react";

type Note = { booking_id: string; booking_date: string; title: string; markdown_source: string };

function SafeMarkdown({ source }: { source: string }) {
  return <div style={{ maxHeight: "20rem", overflow: "auto" }}>{source.split("\n").map((line, index) => line.startsWith("# ") ? <h4 key={index}>{line.slice(2)}</h4> : line.startsWith("- ") ? <li key={index}>{line.slice(2)}</li> : <p key={index}>{line}</p>)}</div>;
}

export function LessonNotes() {
  const [notes, setNotes] = useState<Note[]>([]);
  useEffect(() => {
    void fetch("/api/student/lesson-notes").then(async (response) => {
      if (response.ok) setNotes((await response.json()).lesson_notes);
    });
  }, []);
  return <section aria-labelledby="shared-notes-heading"><h2 id="shared-notes-heading">Shared Lesson Notes</h2>{notes.length === 0 ? <p>No published Lesson Notes.</p> : notes.map((note) => <details key={note.booking_id}><summary>{note.booking_date} — {note.title}</summary><SafeMarkdown source={note.markdown_source} /><a href={`/api/student/lesson-notes/${note.booking_id}/download`}>Download original Markdown</a></details>)}</section>;
}
