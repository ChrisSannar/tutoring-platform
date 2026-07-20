const localDateTimeFormatter = (timeZone: string) => new Intl.DateTimeFormat("en-US", {
  timeZone,
  year: "numeric",
  month: "2-digit",
  day: "2-digit",
  hour: "2-digit",
  minute: "2-digit",
  second: "2-digit",
  hourCycle: "h23",
});

function dateTimeParts(value: Date, timeZone: string) {
  return Object.fromEntries(
    localDateTimeFormatter(timeZone).formatToParts(value)
      .filter((part) => part.type !== "literal")
      .map((part) => [part.type, part.value]),
  );
}

export function tutorDateTimeLabel(value: string, timeZone: string) {
  return new Date(value).toLocaleString("en-US", { timeZone });
}

export function tutorDateTimeInputValue(value: string, timeZone: string) {
  const parts = dateTimeParts(new Date(value), timeZone);
  return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
}

export function tutorWallTimeToInstant(value: string, timeZone: string) {
  const match = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})$/.exec(value);
  if (!match) throw new Error("Tutor wall time must be a datetime-local value");
  const [, year, month, day, hour, minute] = match;
  const wallTimeAsUtc = Date.UTC(Number(year), Number(month) - 1, Number(day), Number(hour), Number(minute));

  const offsetAt = (instant: number) => {
    const parts = dateTimeParts(new Date(instant), timeZone);
    const representedAsUtc = Date.UTC(Number(parts.year), Number(parts.month) - 1, Number(parts.day), Number(parts.hour), Number(parts.minute), Number(parts.second));
    return representedAsUtc - instant;
  };

  let instant = wallTimeAsUtc - offsetAt(wallTimeAsUtc);
  instant = wallTimeAsUtc - offsetAt(instant);
  const result = new Date(instant);
  if (tutorDateTimeInputValue(result.toISOString(), timeZone) !== value) {
    throw new Error("Tutor wall time does not exist in the configured Tutor Timezone");
  }
  return result.toISOString();
}
