import { type FormEvent, useEffect, useState } from "react";
import { tutorDateTimeInputValue, tutorWallTimeToInstant } from "../tutorTime";

type WindowRule = { id: string; weekday: number; start_time: string; end_time: string };
type BlockedTime = { id: string; start_at: string; end_at: string; reason: string | null };
type Override = { id: string; start_at: string; warning: string };
const weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"];

function mutationHeaders(csrfToken: string) {
  return { "Content-Type": "application/json", "X-CSRF-Token": csrfToken };
}

function WindowRow({ rule, csrfToken, onDelete }: { rule: WindowRule; csrfToken: string; onDelete: () => void }) {
  const [weekday, setWeekday] = useState(rule.weekday);
  const [start, setStart] = useState(rule.start_time);
  const [end, setEnd] = useState(rule.end_time);
  async function save() {
    await fetch(`/api/tutor/availability-windows/${rule.id}`, { method: "PUT", headers: mutationHeaders(csrfToken), body: JSON.stringify({ weekday, start_time: start, end_time: end }) });
  }
  async function remove() {
    if ((await fetch(`/api/tutor/availability-windows/${rule.id}`, { method: "DELETE", headers: mutationHeaders(csrfToken) })).ok) onDelete();
  }
  return <article aria-label={`${weekdays[rule.weekday]} Availability`}><select aria-label="Availability weekday" value={weekday} onChange={(event) => setWeekday(Number(event.target.value))}>{weekdays.map((day, index) => <option value={index} key={day}>{day}</option>)}</select><input aria-label="Availability start" type="time" value={start} onChange={(event) => setStart(event.target.value)} /><input aria-label="Availability end" type="time" value={end} onChange={(event) => setEnd(event.target.value)} /><button onClick={save}>Save Availability</button><button onClick={remove}>Delete Availability</button></article>;
}

function BlockedRow({ blocked, csrfToken, tutorTimezone, onDelete }: { blocked: BlockedTime; csrfToken: string; tutorTimezone: string; onDelete: () => void }) {
  const [start, setStart] = useState(tutorDateTimeInputValue(blocked.start_at, tutorTimezone));
  const [end, setEnd] = useState(tutorDateTimeInputValue(blocked.end_at, tutorTimezone));
  const [reason, setReason] = useState(blocked.reason ?? "");
  async function save() {
    await fetch(`/api/tutor/blocked-times/${blocked.id}`, { method: "PUT", headers: mutationHeaders(csrfToken), body: JSON.stringify({ start_at: tutorWallTimeToInstant(start, tutorTimezone), end_at: tutorWallTimeToInstant(end, tutorTimezone), reason: reason || null }) });
  }
  async function remove() {
    if ((await fetch(`/api/tutor/blocked-times/${blocked.id}`, { method: "DELETE", headers: mutationHeaders(csrfToken) })).ok) onDelete();
  }
  return <article aria-label="Blocked Time"><input aria-label="Blocked start" type="datetime-local" value={start} onChange={(event) => setStart(event.target.value)} /><input aria-label="Blocked end" type="datetime-local" value={end} onChange={(event) => setEnd(event.target.value)} /><input aria-label="Private blocked reason" value={reason} onChange={(event) => setReason(event.target.value)} /><button onClick={save}>Save Blocked Time</button><button onClick={remove}>Delete Blocked Time</button></article>;
}

export function AvailabilityCalendar({ csrfToken, tutorTimezone }: { csrfToken: string; tutorTimezone: string }) {
  const [windows, setWindows] = useState<WindowRule[]>([]);
  const [blocked, setBlocked] = useState<BlockedTime[]>([]);
  const [overrides, setOverrides] = useState<Override[]>([]);
  const [weekday, setWeekday] = useState(0);
  const [start, setStart] = useState("09:00");
  const [end, setEnd] = useState("10:00");
  const [blockedStart, setBlockedStart] = useState("");
  const [blockedEnd, setBlockedEnd] = useState("");
  const [reason, setReason] = useState("");
  const [overrideStart, setOverrideStart] = useState("");
  const [warning, setWarning] = useState("");

  useEffect(() => {
    void Promise.all([fetch("/api/tutor/availability-windows"), fetch("/api/tutor/blocked-times"), fetch("/api/tutor/overrides")]).then(async ([windowResponse, blockedResponse, overrideResponse]) => {
      if (windowResponse.ok) setWindows(await windowResponse.json());
      if (blockedResponse.ok) setBlocked(await blockedResponse.json());
      if (overrideResponse.ok) setOverrides(await overrideResponse.json());
    });
  }, []);

  async function addWindow(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/tutor/availability-windows", { method: "POST", headers: mutationHeaders(csrfToken), body: JSON.stringify({ weekday, start_time: start, end_time: end }) });
    if (response.ok) {
      const created = await response.json();
      setWindows((current) => [...current, created]);
    }
  }
  async function addBlocked(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/tutor/blocked-times", { method: "POST", headers: mutationHeaders(csrfToken), body: JSON.stringify({ start_at: tutorWallTimeToInstant(blockedStart, tutorTimezone), end_at: tutorWallTimeToInstant(blockedEnd, tutorTimezone), reason: reason || null }) });
    if (response.ok) {
      const created = await response.json();
      setBlocked((current) => [...current, created]);
    }
  }
  async function addOverride(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/tutor/overrides", { method: "POST", headers: mutationHeaders(csrfToken), body: JSON.stringify({ start_at: tutorWallTimeToInstant(overrideStart, tutorTimezone), warning }) });
    if (response.ok) {
      const created = await response.json();
      setOverrides((current) => [...current, created]);
    }
  }

  return <section aria-labelledby="availability-heading"><h2 id="availability-heading">Availability Calendar</h2><form aria-label="Add Availability" onSubmit={addWindow}><select aria-label="Weekday" value={weekday} onChange={(event) => setWeekday(Number(event.target.value))}>{weekdays.map((day, index) => <option value={index} key={day}>{day}</option>)}</select><input aria-label="Start time" type="time" value={start} onChange={(event) => setStart(event.target.value)} required /><input aria-label="End time" type="time" value={end} onChange={(event) => setEnd(event.target.value)} required /><button type="submit">Add Availability</button></form>{windows.map((rule) => <WindowRow key={rule.id} rule={rule} csrfToken={csrfToken} onDelete={() => setWindows((current) => current.filter((item) => item.id !== rule.id))} />)}<form aria-label="Add Blocked Time" onSubmit={addBlocked}><input aria-label="Blocked start" type="datetime-local" value={blockedStart} onChange={(event) => setBlockedStart(event.target.value)} required /><input aria-label="Blocked end" type="datetime-local" value={blockedEnd} onChange={(event) => setBlockedEnd(event.target.value)} required /><input aria-label="Private blocked reason" value={reason} onChange={(event) => setReason(event.target.value)} /><button type="submit">Add Blocked Time</button></form>{blocked.map((item) => <BlockedRow key={item.id} blocked={item} csrfToken={csrfToken} tutorTimezone={tutorTimezone} onDelete={() => setBlocked((current) => current.filter((entry) => entry.id !== item.id))} />)}<form aria-label="Add Tutor Override" onSubmit={addOverride}><input aria-label="Override start" type="datetime-local" value={overrideStart} onChange={(event) => setOverrideStart(event.target.value)} required /><input aria-label="Override warning" value={warning} onChange={(event) => setWarning(event.target.value)} required /><button type="submit">Add Tutor Override</button></form>{overrides.map((item) => <article key={item.id}><p>{item.warning}</p><button onClick={async () => { if ((await fetch(`/api/tutor/overrides/${item.id}`, { method: "DELETE", headers: mutationHeaders(csrfToken) })).ok) setOverrides((current) => current.filter((entry) => entry.id !== item.id)); }}>Delete Tutor Override</button></article>)}</section>;
}
