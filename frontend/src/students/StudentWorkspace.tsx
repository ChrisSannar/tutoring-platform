import { type FormEvent, useEffect, useState } from "react";

import { csrfTokenFromCookie } from "../web/csrfToken";
import type { Student } from "./types";
import { BookableSlots } from "./BookableSlots";
import { LessonNotes } from "./LessonNotes";

type SessionRequest = {
  id: string;
  service: string;
  preferred_start: string;
  timezone: string;
  message: string | null;
  status: "pending";
};

export function StudentWorkspace({ initialStudent }: { initialStudent?: Student }) {
  const [student, setStudent] = useState<Student | null>(initialStudent ?? null);
  const [unavailable, setUnavailable] = useState(false);
  const [service, setService] = useState("");
  const [preferredStart, setPreferredStart] = useState("");
  const [timezone, setTimezone] = useState(
    Intl.DateTimeFormat().resolvedOptions().timeZone,
  );
  const [message, setMessage] = useState("");
  const [idempotencyKey] = useState(() => crypto.randomUUID());
  const [sessionRequest, setSessionRequest] = useState<SessionRequest | null>(
    null,
  );

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

  async function submitSessionRequest(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/student/session-requests", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfTokenFromCookie(),
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify({
        service,
        preferred_start: new Date(preferredStart).toISOString(),
        timezone,
        message: message || null,
      }),
    });
    if (!response.ok) return;
    setSessionRequest(await response.json());
  }

  if (unavailable) return <main><p>Student Session unavailable</p></main>;
  if (!student) return <main><p>Loading Student Session…</p></main>;
  return (
    <main><section className="hero">
      <p className="eyebrow">Your tutoring</p>
      <h1>Student workspace</h1>
      <p>Welcome, {student.display_name}</p>
      <BookableSlots />
      <LessonNotes />
      {sessionRequest ? (
        <section>
          <h2>Pending Session Request</h2>
          <p>{sessionRequest.service}</p>
          {sessionRequest.message ? <p>{sessionRequest.message}</p> : null}
        </section>
      ) : (
        <form onSubmit={submitSessionRequest}>
          <label htmlFor="request-service">Service</label>
          <select
            id="request-service"
            value={service}
            onChange={(event) => setService(event.target.value)}
            required
          >
            <option value="">Select a service</option>
            <option>Algebra tutoring</option>
            <option>Geometry tutoring</option>
          </select>
          <label htmlFor="request-preferred-start">Preferred start</label>
          <input
            id="request-preferred-start"
            type="datetime-local"
            value={preferredStart}
            onChange={(event) => setPreferredStart(event.target.value)}
            required
          />
          <label htmlFor="request-timezone">Timezone</label>
          <input
            id="request-timezone"
            value={timezone}
            onChange={(event) => setTimezone(event.target.value)}
            required
          />
          <label htmlFor="request-message">Optional message</label>
          <textarea
            id="request-message"
            value={message}
            maxLength={1000}
            onChange={(event) => setMessage(event.target.value)}
          />
          <button type="submit">Submit Session Request</button>
        </form>
      )}
    </section></main>
  );
}
