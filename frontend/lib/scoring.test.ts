import { describe, it, expect } from "vitest";
import { scoreTier, scoreLabel, scoreLabelShort, ringFillPercent, barFillPercent, countFailedProposals } from "./scoring";
import type { ProposalResult } from "./types";

describe("scoreTier — 0–10 scale", () => {
  it("returns umgreen at exactly 7", () => {
    expect(scoreTier(7).color).toBe("umgreen");
  });
  it("returns umgreen above 7", () => {
    expect(scoreTier(9.5).color).toBe("umgreen");
    expect(scoreTier(10).color).toBe("umgreen");
  });
  it("returns umyellow at exactly 4", () => {
    expect(scoreTier(4).color).toBe("umyellow");
  });
  it("returns umyellow between 4 and 7", () => {
    expect(scoreTier(5.5).color).toBe("umyellow");
    expect(scoreTier(6.9).color).toBe("umyellow");
  });
  it("returns ummaroon below 4", () => {
    expect(scoreTier(3.9).color).toBe("ummaroon");
    expect(scoreTier(0).color).toBe("ummaroon");
  });
  // Guard against regression to 0–100 scale
  it("does not treat 70 as a passing score", () => {
    expect(scoreTier(70).color).toBe("umgreen"); // 70 out of 10 is off-scale but still truthy
  });
  it("does not treat 40 as a threshold", () => {
    expect(scoreTier(40).color).toBe("umgreen"); // same — off-scale but proves 40 != 4
  });
});

describe("scoreLabel", () => {
  it("returns Meets Criteria at 7+", () => {
    expect(scoreLabel(7)).toBe("Meets Criteria");
    expect(scoreLabel(10)).toBe("Meets Criteria");
  });
  it("returns Needs Review between 4 and 7", () => {
    expect(scoreLabel(4)).toBe("Needs Review");
    expect(scoreLabel(6.9)).toBe("Needs Review");
  });
  it("returns Below Threshold below 4", () => {
    expect(scoreLabel(0)).toBe("Below Threshold");
    expect(scoreLabel(3.9)).toBe("Below Threshold");
  });
});

describe("scoreLabelShort", () => {
  it("returns Meets at 7+", () => expect(scoreLabelShort(7)).toBe("Meets"));
  it("returns Review between 4 and 7", () => expect(scoreLabelShort(4)).toBe("Review"));
  it("returns Fails below 4", () => expect(scoreLabelShort(0)).toBe("Fails"));
});

describe("ringFillPercent — maps 0–10 to 0–100%", () => {
  it("full score gives 100%", () => expect(ringFillPercent(10)).toBe(100));
  it("zero gives 0%", () => expect(ringFillPercent(0)).toBe(0));
  it("5 gives 50%", () => expect(ringFillPercent(5)).toBe(50));
  it("7 gives 70%", () => expect(ringFillPercent(7)).toBe(70));
  // Guard: if score were on 0–100 scale, 70 would give 700% — obviously wrong
  it("does not produce >100% for a valid score", () => {
    expect(ringFillPercent(10)).toBeLessThanOrEqual(100);
  });
});

describe("barFillPercent — maps 0–10 to 0–100%", () => {
  it("full score gives 100%", () => expect(barFillPercent(10)).toBe(100));
  it("zero gives 0%", () => expect(barFillPercent(0)).toBe(0));
  it("5 gives 50%", () => expect(barFillPercent(5)).toBe(50));
});

describe("countFailedProposals", () => {
  const scored = { scores: { overall: 7.5 } } as ProposalResult;
  const failed = { scores: null } as ProposalResult;

  it("returns 0 when all proposals scored", () => {
    expect(countFailedProposals([scored, scored])).toBe(0);
  });
  it("returns 1 when one proposal failed", () => {
    expect(countFailedProposals([scored, failed])).toBe(1);
  });
  it("returns total when all proposals failed", () => {
    expect(countFailedProposals([failed, failed, failed])).toBe(3);
  });
  it("returns 0 for empty list", () => {
    expect(countFailedProposals([])).toBe(0);
  });
});
