import { useEffect, useState } from "react";

import { csrfTokenFromCookie } from "../web/csrfToken";

type Slot = { start_at: string; end_at: string };
type Funding = { first_session_promotion: "available" | "unavailable"; session_credits: number };
type Booking = Slot & { id: string; funding_kind: string; focus: string | null; meeting_details: string | null };

export function BookableSlots() {
  const [timezone, setTimezone] = useState("");
  const [slots, setSlots] = useState<Slot[]>([]);
  const [funding, setFunding] = useState<Funding | null>(null);
  const [selected, setSelected] = useState<Slot | null>(null);
  const [focus, setFocus] = useState("");
  const [booking, setBooking] = useState<Booking | null>(null);
  const [idempotencyKey, setIdempotencyKey] = useState(() => crypto.randomUUID());

  useEffect(() => {
    void Promise.all([fetch("/api/student/bookable-slots"), fetch("/api/student/funding"), fetch("/api/student/bookings/upcoming")]).then(async ([slotResponse, fundingResponse, bookingResponse]) => {
      if (slotResponse.ok) {
        const body = await slotResponse.json();
        setTimezone(body.tutor_timezone);
        setSlots(body.slots);
      }
      if (fundingResponse.ok) setFunding(await fundingResponse.json());
      if (bookingResponse.ok) setBooking(await bookingResponse.json());
    });
  }, []);

  async function schedule() {
    if (!selected) return;
    const response = await fetch("/api/student/bookings", {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfTokenFromCookie(), "Idempotency-Key": idempotencyKey },
      body: JSON.stringify({ start_at: selected.start_at, focus: focus || null, confirmed: true }),
    });
    if (!response.ok) return;
    const created = await response.json();
    setBooking(created);
    setSlots((current) => current.filter((slot) => slot.start_at !== created.start_at));
    setIdempotencyKey(crypto.randomUUID());
  }

  if (booking) return <section aria-labelledby="upcoming-booking-heading"><h2 id="upcoming-booking-heading">Upcoming Booking</h2><p>{new Date(booking.start_at).toLocaleString("en-US", { timeZone: timezone })}</p><p>Funding: {booking.funding_kind}</p><p>Meeting Details: {booking.meeting_details || "Pending"}</p>{booking.focus ? <p>Booking Focus: {booking.focus}</p> : null}</section>;
  const fundingLabel = funding?.first_session_promotion === "available" ? "First Session Promotion" : funding && funding.session_credits > 0 ? "Session Credit" : "No funding available";
  return <section aria-labelledby="bookable-slots-heading"><h2 id="bookable-slots-heading">Bookable Slots</h2>{timezone ? <p>Tutor Timezone: {timezone}</p> : null}{slots.length === 0 ? <p>No Bookable Slots.</p> : slots.map((slot) => <button key={slot.start_at} onClick={() => setSelected(slot)}>{new Date(slot.start_at).toLocaleString("en-US", { timeZone: timezone })}</button>)}{selected ? <section aria-labelledby="schedule-confirmation-heading"><h3 id="schedule-confirmation-heading">Confirm session</h3><p>Start: {new Date(selected.start_at).toLocaleString("en-US", { timeZone: timezone })}</p><p>Duration: 60 minutes</p><p>Tutor Timezone: {timezone}</p><p>Funding: {fundingLabel}</p><p>Changes within 24 hours are subject to the cancellation policy.</p><label htmlFor="booking-focus">Optional Booking Focus</label><textarea id="booking-focus" maxLength={500} value={focus} onChange={(event) => setFocus(event.target.value)} /><button onClick={schedule} disabled={fundingLabel === "No funding available"}>Schedule session</button></section> : null}</section>;
}
