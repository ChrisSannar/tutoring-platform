import { useEffect, useState } from "react";

import { csrfTokenFromCookie } from "../web/csrfToken";

type Slot = { start_at: string; end_at: string };
type Funding = { session_credits: number };
type Booking = Slot & {
  id: string;
  funding_kind: "session_credit" | "complimentary";
  focus: string | null;
  meeting_details: string | null;
};

export function BookableSlots() {
  const [timezone, setTimezone] = useState("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [funding, setFunding] = useState<Funding | null>(null);
  const [selected, setSelected] = useState<Slot | null>(null);
  const [focus, setFocus] = useState("");
  const [booking, setBooking] = useState<Booking | null>(null);
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());
  const [cancelled, setCancelled] = useState(false);

  async function reload() {
    const [slotResponse, bookingResponse, fundingResponse] = await Promise.all([
      fetch("/api/student/bookable-slots"),
      fetch("/api/student/bookings/upcoming"),
      fetch("/api/student/funding"),
    ]);
    if (slotResponse.ok) {
      const body = await slotResponse.json();
      setTimezone(body.tutor_timezone);
      setSlots(body.slots);
    }
    setBooking(bookingResponse.ok ? await bookingResponse.json() : null);
    if (fundingResponse.ok) setFunding(await fundingResponse.json());
  }

  useEffect(() => {
    void reload();
  }, []);

  async function schedule() {
    if (!selected) return;
    const response = await fetch("/api/student/bookings", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfTokenFromCookie(),
        "Idempotency-Key": idempotencyKey,
      },
      body: JSON.stringify({
        start_at: selected.start_at,
        focus: focus || null,
        confirmed: true,
      }),
    });
    if (!response.ok) return;
    setIdempotencyKey(crypto.randomUUID());
    await reload();
  }

  async function reschedule(slot: Slot) {
    if (!booking) return;
    const response = await fetch(`/api/student/bookings/${booking.id}/schedule`, {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfTokenFromCookie(),
        "Idempotency-Key": crypto.randomUUID(),
      },
      body: JSON.stringify({ start_at: slot.start_at }),
    });
    if (response.ok) await reload();
  }

  async function cancelBooking() {
    if (!booking) return;
    const response = await fetch(`/api/student/bookings/${booking.id}/cancel`, {
      method: "POST",
      headers: {
        "X-CSRF-Token": csrfTokenFromCookie(),
        "Idempotency-Key": crypto.randomUUID(),
      },
    });
    if (!response.ok) return;
    setCancelled(true);
    await reload();
  }

  if (booking) {
    const early =
      new Date(booking.start_at).getTime() - Date.now() >= 24 * 60 * 60 * 1000;
    return (
      <section aria-labelledby="upcoming-booking-heading">
        <h2 id="upcoming-booking-heading">Upcoming Booking</h2>
        <p>{new Date(booking.start_at).toLocaleString("en-US", { timeZone: timezone })}</p>
        <p>Funding: {booking.funding_kind === "session_credit" ? "Session Credit" : "Complimentary"}</p>
        <p>Meeting Details: {booking.meeting_details || "Pending"}</p>
        {booking.focus ? <p>Booking Focus: {booking.focus}</p> : null}
        <a href={`/api/student/bookings/${booking.id}/calendar.ics`}>Download Calendar (.ics)</a>
        {early ? (
          <section aria-labelledby="reschedule-heading">
            <h3 id="reschedule-heading">Reschedule Booking</h3>
            {slots.map((slot) => (
              <button key={slot.start_at} onClick={() => reschedule(slot)}>
                Move to {new Date(slot.start_at).toLocaleString("en-US", { timeZone: timezone })}
              </button>
            ))}
          </section>
        ) : (
          <p>Self-service rescheduling is unavailable inside 24 hours. Contact the Tutor by normal email.</p>
        )}
        <button onClick={cancelBooking}>Cancel Booking</button>
      </section>
    );
  }

  return (
    <section aria-labelledby="bookable-slots-heading">
      <h2 id="bookable-slots-heading">Bookable Slots</h2>
      {cancelled ? <p role="status">Booking cancelled</p> : null}
      {timezone ? <p>Tutor Timezone: {timezone}</p> : null}
      <p>Session Credits: {funding?.session_credits ?? 0}</p>
      {slots.length === 0 ? (
        <p>No Bookable Slots.</p>
      ) : (
        slots.map((slot) => (
          <button key={slot.start_at} onClick={() => setSelected(slot)}>
            {new Date(slot.start_at).toLocaleString("en-US", { timeZone: timezone })}
          </button>
        ))
      )}
      {selected ? (
        <section aria-labelledby="schedule-confirmation-heading">
          <h3 id="schedule-confirmation-heading">Confirm session</h3>
          <p>Start: {new Date(selected.start_at).toLocaleString("en-US", { timeZone: timezone })}</p>
          <p>Duration: 60 minutes</p>
          <p>Tutor Timezone: {timezone}</p>
          <p>Funding: {funding && funding.session_credits > 0 ? "Session Credit" : "No Session Credit available"}</p>
          <p>Rescheduling is unavailable inside 24 hours.</p>
          <label htmlFor="booking-focus">Optional Booking Focus</label>
          <textarea id="booking-focus" maxLength={500} value={focus} onChange={(event) => setFocus(event.target.value)} />
          <button disabled={!funding || funding.session_credits < 1} onClick={schedule}>Schedule session</button>
        </section>
      ) : null}
    </section>
  );
}
