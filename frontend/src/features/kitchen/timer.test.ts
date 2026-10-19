import { describe, expect, it } from "vitest";

import { formatElapsed, timerLevel } from "@/features/kitchen/timer";

describe("cronômetro da cozinha", () => {
  it("muda de cor conforme a meta de preparo", () => {
    expect(timerLevel(0, 20)).toBe("on_time");
    expect(timerLevel(14 * 60 + 59, 20)).toBe("on_time");
    expect(timerLevel(15 * 60, 20)).toBe("attention");
    expect(timerLevel(20 * 60, 20)).toBe("late");
  });

  it("formata como cronômetro", () => {
    expect(formatElapsed(0)).toBe("00:00");
    expect(formatElapsed(65)).toBe("01:05");
    expect(formatElapsed(3725)).toBe("1:02:05");
    expect(formatElapsed(-5)).toBe("00:00");
  });
});
