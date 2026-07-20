import { useEffect, useState } from "react";
import { tutorDateTimeInputValue, tutorDateTimeLabel, tutorWallTimeToInstant } from "../tutorTime";

type Booking = { id: string; start_at: string; funding_kind: string; meeting_details: string | null; student: { id: string; display_name: string; email: string } };
type Override = { id: string; start_at: string; warning: string };

export function BookingCalendar({ csrfToken, tutorTimezone }: { csrfToken: string; tutorTimezone: string }) {
  const [bookings, setBookings] = useState<Booking[]>([]);
  const [overrides, setOverrides] = useState<Override[]>([]);
  const [selected, setSelected] = useState<Booking | null>(null);
  const [details, setDetails] = useState("");
  const [start, setStart] = useState("");
  const [overrideId, setOverrideId] = useState("");
  const [acknowledged, setAcknowledged] = useState(false);

  useEffect(() => {
    void Promise.all([fetch("/api/tutor/bookings"), fetch("/api/tutor/overrides")]).then(async ([bookingResponse, overrideResponse]) => {
      if (bookingResponse.ok) setBookings((await bookingResponse.json()).bookings);
      if (overrideResponse.ok) setOverrides(await overrideResponse.json());
    });
  }, []);

  function select(booking: Booking) {
    setSelected(booking);
    setDetails(booking.meeting_details ?? "");
    setStart(tutorDateTimeInputValue(booking.start_at, tutorTimezone));
    window.dispatchEvent(new CustomEvent("highlight-student", { detail: booking.student.id }));
  }

  function replaceBooking(updated: Booking) {
    const merged = { ...selected!, ...updated };
    setSelected(merged);
    setBookings((current) => current.map((booking) => booking.id === updated.id ? { ...booking, ...updated } : booking));
    setStart(tutorDateTimeInputValue(updated.start_at, tutorTimezone));
  }

  async function saveDetails() {
    if (!selected) return;
    const response = await fetch(`/api/tutor/bookings/${selected.id}/meeting-details`, { method: "PUT", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify({ meeting_details: details || null }) });
    if (response.ok) replaceBooking(await response.json());
  }

  async function moveBooking() {
    if (!selected) return;
    const response = await fetch(`/api/tutor/bookings/${selected.id}/schedule`, { method: "PUT", headers: { "Content-Type": "application/json", "X-CSRF-Token": csrfToken }, body: JSON.stringify({ start_at: tutorWallTimeToInstant(start, tutorTimezone), override_id: overrideId || null, warning_acknowledged: acknowledged }) });
    if (response.ok) replaceBooking(await response.json());
  }

  const chosenOverride = overrides.find((item) => item.id === overrideId);
  return <section aria-labelledby="booking-calendar-heading"><h2 id="booking-calendar-heading">Weekly Booking Calendar</h2>{bookings.length === 0 ? <p>No Bookings.</p> : bookings.map((booking) => <button key={booking.id} onClick={() => select(booking)}>{booking.student.display_name} — {tutorDateTimeLabel(booking.start_at, tutorTimezone)}</button>)}{selected ? <section aria-labelledby="calendar-booking-heading"><h3 id="calendar-booking-heading">Selected Booking</h3><p>{selected.student.display_name}</p><p>Funding: {selected.funding_kind}</p><label htmlFor="calendar-meeting-details">Meeting Details</label><textarea id="calendar-meeting-details" value={details} onChange={(event) => setDetails(event.target.value)} /><button onClick={saveDetails}>Save Meeting Details</button><label htmlFor="calendar-booking-start">Move Booking</label><input id="calendar-booking-start" type="datetime-local" value={start} onChange={(event) => setStart(event.target.value)} /><label htmlFor="calendar-override">Tutor Override</label><select id="calendar-override" value={overrideId} onChange={(event) => { const value = event.target.value; setOverrideId(value); setAcknowledged(false); const chosen = overrides.find((item) => item.id === value); if (chosen) setStart(tutorDateTimeInputValue(chosen.start_at, tutorTimezone)); }}><option value="">Normal Bookable Slot</option>{overrides.map((item) => <option key={item.id} value={item.id}>{item.warning}</option>)}</select>{chosenOverride ? <label><input type="checkbox" checked={acknowledged} onChange={(event) => setAcknowledged(event.target.checked)} />I acknowledge: {chosenOverride.warning}</label> : null}<button onClick={moveBooking} disabled={Boolean(chosenOverride) && !acknowledged}>Move Booking</button></section> : null}</section>;
}
