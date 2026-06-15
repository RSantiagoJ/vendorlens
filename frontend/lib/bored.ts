/**
 * Returns a random index in [0, length) that is different from currentIdx.
 * Falls back to 0 when length <= 1.
 */
export function pickRandom(length: number, currentIdx: number): number {
  if (length <= 1) return 0;
  let next: number;
  do {
    next = Math.floor(Math.random() * length);
  } while (next === currentIdx);
  return next;
}
