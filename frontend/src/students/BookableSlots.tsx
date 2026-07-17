import { useEffect, useState } from "react";

type Slot = { start_at: string; end_at: string };

export function BookableSlots() {
  const [timezone, setTimezone] = useState("");
  const [slots, setSlots] = useState<Slot[]>([]);
  useEffect(() => {
    void fetch("/api/student/bookable-slots").then(async (response) => {
      if (!response.ok) return;
      const body = await response.json();
      setTimezone(body.tutor_timezone);
      setSlots(body.slots);
    });
  }, []);
  return <section aria-labelledby="bookable-slots-heading"><h2 id="bookable-slots-heading">Bookable Slots</h2>{timezone ? <p>Tutor Timezone: {timezone}</p> : null}{slots.length === 0 ? <p>No Bookable Slots.</p> : slots.map((slot) => <button key={slot.start_at}>{new Date(slot.start_at).toLocaleString("en-US", { timeZone: timezone })}</button>)}</section>;
}
