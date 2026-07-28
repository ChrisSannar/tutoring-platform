import { type FormEvent, useEffect, useState } from "react";

export function BusinessSettings({ csrfToken, onTimezoneChange }: { csrfToken: string; onTimezoneChange: (timezone: string) => void }) {
  const [timezone, setTimezone] = useState("");
  const [meetingDetails, setMeetingDetails] = useState("");
  const [saved, setSaved] = useState(false);

  useEffect(() => {
    void fetch("/api/tutor/settings").then(async (response) => {
      if (!response.ok) return;
      const settings = await response.json();
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
