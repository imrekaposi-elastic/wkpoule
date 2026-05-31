import { describe, expect, it } from "vitest";

import {
  browserTimeZone,
  compareLocalDateKeys,
  daysUntilLocalDate,
  formatCalendarDayHeader,
  formatMatchTime,
  formatTimeZoneLabel,
  kickoffToLocalDateKey,
  localDateKey,
  parseLocalDateKey,
  shiftLocalDateKey,
  todayLocalDateKey,
} from "./matchCalendar";

describe("matchCalendar", () => {
  it("formats and parses local date keys", () => {
    const date = new Date(2026, 5, 15);
    expect(localDateKey(date)).toBe("2026-06-15");
    expect(parseLocalDateKey("2026-06-15").getDate()).toBe(15);
    expect(shiftLocalDateKey("2026-06-15", 2)).toBe("2026-06-17");
  });

  it("compares date keys lexicographically", () => {
    expect(compareLocalDateKeys("2026-06-01", "2026-06-02")).toBe(-1);
    expect(compareLocalDateKeys("2026-06-02", "2026-06-02")).toBe(0);
  });

  it("counts days between local dates", () => {
    expect(daysUntilLocalDate("2026-06-01", "2026-06-04")).toBe(3);
  });

  it("formats calendar labels and match times", () => {
    expect(formatCalendarDayHeader("2026-06-15", "en-US")).toContain("2026");
    expect(formatMatchTime("2026-06-15T18:00:00Z", "en-US")).toMatch(/\d/);
  });

  it("derives kickoff date keys in a timezone", () => {
    expect(kickoffToLocalDateKey("2026-06-15T18:00:00Z", "UTC")).toBe("2026-06-15");
  });

  it("returns safe fallbacks for invalid timezone labels", () => {
    expect(formatTimeZoneLabel("Invalid/Zone", "en-US")).toBe("Invalid/Zone");
    expect(formatMatchTime("not-a-date", "en-US")).toBe("not-a-date");
  });

  it("exposes browser timezone and today key", () => {
    expect(browserTimeZone()).toBeTruthy();
    expect(todayLocalDateKey()).toMatch(/^\d{4}-\d{2}-\d{2}$/);
  });
});
