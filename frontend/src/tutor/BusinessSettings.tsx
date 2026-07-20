import { type FormEvent, useEffect, useState } from "react";

export function BusinessSettings({ csrfToken, onTimezoneChange }: { csrfToken: string; onTimezoneChange: (timezone: string) => void }) {
  const [price, setPrice] = useState("");
  const [timezone, setTimezone] = useState("");
  const [meetingDetails, setMeetingDetails] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    void fetch("/api/tutor/settings").then(async (response) => {
      if (!response.ok) return;
      const settings = await response.json();
      setPrice((settings.session_price_cents / 100).toFixed(2));
      setTimezone(settings.tutor_timezone);
      onTimezoneChange(settings.tutor_timezone);
      setMeetingDetails(settings.default_meeting_details ?? "");
    });
  }, [onTimezoneChange]);

  async function saveSettings(event: FormEvent) {
    event.preventDefault();
    const response = await fetch("/api/tutor/settings", {
      method: "PUT",
      headers: {
        "Content-Type": "application/json",
        "X-CSRF-Token": csrfToken,
      },
      body: JSON.stringify({
        currency: "USD",
        session_price_cents: Math.round(Number(price) * 100),
        tutor_timezone: timezone,
        default_meeting_details: meetingDetails || null,
      }),
    });
    if (response.ok) {
      setSaved(true);
      onTimezoneChange(timezone);
    }
  }

  return (
    <section aria-labelledby="business-settings-heading">
      <h2 id="business-settings-heading">Business settings</h2>
      <form onSubmit={saveSettings}>
        <label htmlFor="session-price">Session price (USD)</label>
        <input
          id="session-price"
          type="number"
          min="0.01"
          step="0.01"
          value={price}
          onChange={(event) => setPrice(event.target.value)}
          required
        />
        <label htmlFor="tutor-timezone">Tutor timezone</label>
        <input
          id="tutor-timezone"
          value={timezone}
          onChange={(event) => setTimezone(event.target.value)}
          required
        />
        <label htmlFor="default-meeting-details">
          Default remote Meeting Details
        </label>
        <textarea
          id="default-meeting-details"
          value={meetingDetails}
          onChange={(event) => setMeetingDetails(event.target.value)}
          maxLength={5000}
        />
        <button type="submit">Save business settings</button>
      </form>
      {saved ? <p>Business settings saved</p> : null}
    </section>
  );
}
