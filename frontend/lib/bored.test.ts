import { describe, it, expect } from "vitest";
import { pickRandom } from "./bored";

describe("pickRandom", () => {
  it("always returns a valid index", () => {
    for (let i = 0; i < 50; i++) {
      const idx = pickRandom(10, 3);
      expect(idx).toBeGreaterThanOrEqual(0);
      expect(idx).toBeLessThan(10);
    }
  });

  it("never returns the current index when length > 1", () => {
    for (let i = 0; i < 100; i++) {
      expect(pickRandom(15, 7)).not.toBe(7);
      expect(pickRandom(2, 0)).not.toBe(0);
      expect(pickRandom(2, 1)).not.toBe(1);
    }
  });

  it("returns 0 when length is 1", () => {
    expect(pickRandom(1, 0)).toBe(0);
  });

  it("covers the full range (not stuck on one value)", () => {
    const seen = new Set<number>();
    for (let i = 0; i < 200; i++) seen.add(pickRandom(5, 0));
    // With 200 draws from [1..4], all four non-zero values should appear
    expect(seen.size).toBeGreaterThanOrEqual(4);
  });
});
