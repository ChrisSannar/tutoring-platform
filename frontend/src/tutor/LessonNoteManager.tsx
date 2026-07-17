import { useEffect, useState } from "react";

type Note = { id: string; booking_id: string; title: string; markdown_source: string; status: "draft" | "published" };
type WorkspaceItem = { booking_id: string; booking_date: string; note: Note | null };

function NoteEditor({ item, csrfToken }: { item: WorkspaceItem; csrfToken: string }) {
  const [note, setNote] = useState(item.note);
  const [title, setTitle] = useState(item.note?.title ?? "");
  const [source, setSource] = useState(item.note?.markdown_source ?? "");
  const [confirmDelete, setConfirmDelete] = useState(false);
  const headers = { "Content-Type": "application/json", "X-CSRF-Token": csrfToken };
  async function save() {
    const response = await fetch(`/api/tutor/bookings/${item.booking_id}/lesson-note`, { method: "PUT", headers, body: JSON.stringify({ title, markdown_source: source }) });
    if (response.ok) setNote(await response.json());
  }
  async function publish() {
    const response = await fetch(`/api/tutor/bookings/${item.booking_id}/lesson-note/publish`, { method: "POST", headers });
    if (response.ok) setNote(await response.json());
  }
  async function remove() {
    const response = await fetch(`/api/tutor/bookings/${item.booking_id}/lesson-note`, { method: "DELETE", headers, body: JSON.stringify({ confirmed: true }) });
    if (response.ok) { setNote(null); setTitle(""); setSource(""); }
  }
  return <article><h4>{item.booking_date} Lesson Note Draft</h4><p>Status: {note?.status ?? "Not started"}</p><label htmlFor={`note-title-${item.booking_id}`}>Lesson Note title</label><input id={`note-title-${item.booking_id}`} value={title} onChange={(event) => setTitle(event.target.value)} maxLength={200} /><label htmlFor={`note-source-${item.booking_id}`}>Markdown source</label><textarea id={`note-source-${item.booking_id}`} value={source} onChange={(event) => setSource(event.target.value)} /><button onClick={save}>Save Draft</button><button onClick={publish} disabled={!note}>Publish Lesson Note</button>{note ? <><label><input type="checkbox" checked={confirmDelete} onChange={(event) => setConfirmDelete(event.target.checked)} />Confirm Lesson Note deletion</label><button disabled={!confirmDelete} onClick={remove}>Delete Lesson Note</button></> : null}</article>;
}

export function LessonNoteManager({ studentId, csrfToken }: { studentId: string; csrfToken: string }) {
  const [items, setItems] = useState<WorkspaceItem[]>([]);
  useEffect(() => {
    void fetch(`/api/tutor/students/${studentId}/lesson-note-workspace`).then(async (response) => {
      if (response.ok) setItems(await response.json());
    });
  }, [studentId]);
  return <section aria-labelledby="lesson-note-drafts-heading"><h3 id="lesson-note-drafts-heading">Lesson Note Drafts</h3>{items.length === 0 ? <p>No eligible Past Bookings.</p> : items.map((item) => <NoteEditor key={item.booking_id} item={item} csrfToken={csrfToken} />)}</section>;
}
