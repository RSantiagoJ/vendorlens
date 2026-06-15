"use client";

import { useEffect, useRef, useState } from "react";
import { Box, Button, Group, Stack, Text } from "@mantine/core";

const COLS = 10;
const ROWS = 20;
const CELL = 22;

const COLORS = [
  "",
  "#00b4d8", // I
  "#ffd60a", // O
  "#9b5de5", // T
  "#2dc653", // S
  "#e63946", // Z
  "#f4a261", // J
  "#0077b6", // L
];

const SHAPES: number[][][] = [
  [],
  [[1, 1, 1, 1]],
  [[2, 2], [2, 2]],
  [[0, 3, 0], [3, 3, 3]],
  [[0, 4, 4], [4, 4, 0]],
  [[5, 5, 0], [0, 5, 5]],
  [[6, 0, 0], [6, 6, 6]],
  [[0, 0, 7], [7, 7, 7]],
];

const SCORE_TABLE = [0, 100, 300, 500, 800];
const GRAVITY_MS = [800, 700, 600, 500, 400, 300, 200, 150, 100, 80];

type Board = number[][];
type Piece = { shape: number[][]; x: number; y: number };
type ScoreEntry = { name: string; score: number };

const FAKE_SCORES: ScoreEntry[] = [
  { name: "Sardinator1337", score: 12350 },
  { name: "ChawlaChampion", score: 9150 },
];

const LS_KEY = "tetris_hs_v1";
const PLAYER = "VendorSlayer";

const MEDALS = ["🥇", "🥈", "🥉"];

function loadRealScores(): ScoreEntry[] {
  if (typeof window === "undefined") return [];
  try {
    return JSON.parse(localStorage.getItem(LS_KEY) || "[]");
  } catch {
    return [];
  }
}

function saveRealScore(score: number): void {
  const stored = loadRealScores();
  stored.push({ name: PLAYER, score });
  localStorage.setItem(LS_KEY, JSON.stringify(stored));
}

function getLeaderboard(): ScoreEntry[] {
  return [...FAKE_SCORES, ...loadRealScores()]
    .sort((a, b) => b.score - a.score)
    .slice(0, 8);
}

function emptyBoard(): Board {
  return Array.from({ length: ROWS }, () => Array(COLS).fill(0));
}

function spawnPiece(): Piece {
  const t = Math.ceil(Math.random() * 7);
  const shape = SHAPES[t].map((r) => [...r]);
  return { shape, x: Math.floor(COLS / 2) - Math.ceil(shape[0].length / 2), y: 0 };
}

function rotateCW(shape: number[][]): number[][] {
  return shape[0].map((_, c) => shape.map((r) => r[c]).reverse());
}

function fits(board: Board, shape: number[][], x: number, y: number): boolean {
  for (let r = 0; r < shape.length; r++)
    for (let c = 0; c < shape[r].length; c++)
      if (shape[r][c]) {
        if (y + r < 0 || y + r >= ROWS || x + c < 0 || x + c >= COLS) return false;
        if (board[y + r][x + c]) return false;
      }
  return true;
}

function merge(board: Board, piece: Piece): Board {
  const b = board.map((r) => [...r]);
  for (let r = 0; r < piece.shape.length; r++)
    for (let c = 0; c < piece.shape[r].length; c++)
      if (piece.shape[r][c]) b[piece.y + r][piece.x + c] = piece.shape[r][c];
  return b;
}

function sweep(board: Board): [Board, number] {
  const kept = board.filter((r) => r.some((v) => v === 0));
  const cleared = ROWS - kept.length;
  return [
    [...Array.from({ length: cleared }, () => Array(COLS).fill(0)), ...kept],
    cleared,
  ];
}

function drawCell(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  color: string,
  alpha = 1
) {
  ctx.globalAlpha = alpha;
  ctx.fillStyle = color;
  ctx.fillRect(x * CELL + 1, y * CELL + 1, CELL - 2, CELL - 2);
  ctx.fillStyle = "rgba(255,255,255,0.22)";
  ctx.fillRect(x * CELL + 1, y * CELL + 1, CELL - 2, 3);
  ctx.globalAlpha = 1;
}

export function TetrisGame() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [score, setScore] = useState(0);
  const [over, setOver] = useState(false);
  const [runId, setRunId] = useState(0);
  const [leaderboard, setLeaderboard] = useState<ScoreEntry[]>([]);

  useEffect(() => {
    setLeaderboard(getLeaderboard());
  }, []);

  useEffect(() => {
    const state = {
      board: emptyBoard(),
      piece: spawnPiece(),
      score: 0,
      lines: 0,
      lastDrop: 0,
      alive: true,
      flashing: false,
      flashRows: [] as number[],
      flashStart: 0,
    };

    let raf = 0;

    function draw() {
      const canvas = canvasRef.current;
      if (!canvas) return;
      const ctx = canvas.getContext("2d")!;
      const { board, piece } = state;

      ctx.fillStyle = "#0f0f1a";
      ctx.fillRect(0, 0, COLS * CELL, ROWS * CELL);

      ctx.strokeStyle = "rgba(255,255,255,0.04)";
      ctx.lineWidth = 0.5;
      for (let r = 0; r <= ROWS; r++) {
        ctx.beginPath();
        ctx.moveTo(0, r * CELL);
        ctx.lineTo(COLS * CELL, r * CELL);
        ctx.stroke();
      }
      for (let c = 0; c <= COLS; c++) {
        ctx.beginPath();
        ctx.moveTo(c * CELL, 0);
        ctx.lineTo(c * CELL, ROWS * CELL);
        ctx.stroke();
      }

      for (let r = 0; r < ROWS; r++)
        for (let c = 0; c < COLS; c++)
          if (board[r][c]) drawCell(ctx, c, r, COLORS[board[r][c]]);

      if (!state.flashing) {
        let gy = piece.y;
        while (fits(board, piece.shape, piece.x, gy + 1)) gy++;
        if (gy > piece.y)
          for (let r = 0; r < piece.shape.length; r++)
            for (let c = 0; c < piece.shape[r].length; c++)
              if (piece.shape[r][c])
                drawCell(ctx, piece.x + c, gy + r, COLORS[piece.shape[r][c]], 0.18);

        for (let r = 0; r < piece.shape.length; r++)
          for (let c = 0; c < piece.shape[r].length; c++)
            if (piece.shape[r][c])
              drawCell(ctx, piece.x + c, piece.y + r, COLORS[piece.shape[r][c]]);
      }

      if (state.flashing) {
        const elapsed = performance.now() - state.flashStart;
        const alpha = elapsed < 60 ? 0.9 : 0.9 * Math.max(0, 1 - (elapsed - 60) / 160);
        ctx.globalAlpha = alpha;
        ctx.fillStyle = "white";
        state.flashRows.forEach(r => ctx.fillRect(0, r * CELL, COLS * CELL, CELL));
        ctx.globalAlpha = 1;
      }
    }

    function loop(ts: number) {
      if (!state.alive) return;

      if (!state.flashing) {
        const level = Math.floor(state.lines / 10);
        const gravity = GRAVITY_MS[Math.min(level, GRAVITY_MS.length - 1)];

        if (ts - state.lastDrop > gravity) {
          state.lastDrop = ts;
          if (fits(state.board, state.piece.shape, state.piece.x, state.piece.y + 1)) {
            state.piece.y++;
          } else {
            state.board = merge(state.board, state.piece);

            const completeRows: number[] = state.board
              .map((row, i) => ({ row, i }))
              .filter(({ row }) => row.every(v => v !== 0))
              .map(({ i }) => i);

            if (completeRows.length > 0) {
              state.flashing = true;
              state.flashRows = completeRows;
              state.flashStart = performance.now();
              setTimeout(() => {
                const [newBoard, cleared] = sweep(state.board);
                state.board = newBoard;
                const lvl = Math.floor(state.lines / 10);
                state.lines += cleared;
                state.score += SCORE_TABLE[cleared] * (lvl + 1);
                setScore(state.score);
                state.piece = spawnPiece();
                state.flashing = false;
                state.flashRows = [];
                if (!fits(state.board, state.piece.shape, state.piece.x, state.piece.y)) {
                  state.alive = false;
                  saveRealScore(state.score);
                  setLeaderboard(getLeaderboard());
                  setOver(true);
                }
              }, 220);
            } else {
              state.piece = spawnPiece();
              if (!fits(state.board, state.piece.shape, state.piece.x, state.piece.y)) {
                state.alive = false;
                saveRealScore(state.score);
                setLeaderboard(getLeaderboard());
                setOver(true);
                draw();
                return;
              }
            }
          }
        }
      }

      draw();
      raf = requestAnimationFrame(loop);
    }

    setOver(false);
    setScore(0);
    raf = requestAnimationFrame(loop);

    function onKey(e: KeyboardEvent) {
      if (!state.alive || state.flashing) return;
      if (!["ArrowLeft", "ArrowRight", "ArrowDown", "ArrowUp", "Space"].includes(e.code)) return;
      e.preventDefault();

      const { piece, board } = state;
      if (e.code === "ArrowLeft" && fits(board, piece.shape, piece.x - 1, piece.y)) piece.x--;
      if (e.code === "ArrowRight" && fits(board, piece.shape, piece.x + 1, piece.y)) piece.x++;
      if (e.code === "ArrowDown") {
        if (fits(board, piece.shape, piece.x, piece.y + 1)) {
          piece.y++;
          state.score++;
        }
      }
      if (e.code === "ArrowUp") {
        const rot = rotateCW(piece.shape);
        for (const dx of [0, -1, 1, -2, 2]) {
          if (fits(board, rot, piece.x + dx, piece.y)) {
            piece.shape = rot;
            piece.x += dx;
            break;
          }
        }
      }
      if (e.code === "Space") {
        while (fits(board, piece.shape, piece.x, piece.y + 1)) {
          piece.y++;
          state.score += 2;
        }
        setScore(state.score);
      }
      draw();
    }

    window.addEventListener("keydown", onKey);
    return () => {
      state.alive = false;
      cancelAnimationFrame(raf);
      window.removeEventListener("keydown", onKey);
    };
  }, [runId]);

  return (
    <Stack gap={6} align="center" p={12} style={{ userSelect: "none" }}>
      <Group w={COLS * CELL} justify="flex-end">
        <Text size="xs" c="yellow.4" fw={700}>{score.toLocaleString()} pts</Text>
      </Group>
      <Box style={{ position: "relative" }}>
        <canvas
          ref={canvasRef}
          width={COLS * CELL}
          height={ROWS * CELL}
          style={{ display: "block", borderRadius: 4, border: "1px solid rgba(255,255,255,0.15)" }}
        />
        {over && (
          <Box
            style={{
              position: "absolute",
              inset: 0,
              display: "flex",
              flexDirection: "column",
              alignItems: "center",
              justifyContent: "center",
              background: "rgba(0,0,0,0.78)",
              borderRadius: 4,
              gap: 8,
            }}
          >
            <Text c="white" fw={800} size="xl">Game Over</Text>
            <Text c="dimmed" size="sm">{score.toLocaleString()} pts</Text>
            <Text size="xs" c="yellow.4">saved as {PLAYER}</Text>
            <Button size="xs" color="umblue" mt={4} onClick={() => setRunId((n) => n + 1)}>
              Play again
            </Button>
          </Box>
        )}
      </Box>
      <Text size="10px" ta="center" w={COLS * CELL} style={{ color: "rgba(255,255,255,0.6)" }}>
        ← → move · ↑ rotate · ↓ drop · space hard drop
      </Text>

      {/* Leaderboard */}
      <Box
        w={COLS * CELL}
        mt={6}
        style={{
          borderTop: "1px solid rgba(255,255,255,0.15)",
          paddingTop: 10,
        }}
      >
        <Text size="xs" c="white" fw={700} mb={8} style={{ letterSpacing: "0.08em", textTransform: "uppercase" }}>
          🏆 High Scores
        </Text>
        <Stack gap={5}>
          {leaderboard.map((entry, i) => (
            <Group key={i} justify="space-between" wrap="nowrap">
              <Group gap={6} wrap="nowrap">
                <Text size="xs" style={{ width: 18, flexShrink: 0 }}>
                  {i < 3 ? MEDALS[i] : `${i + 1}.`}
                </Text>
                <Text
                  size="xs"
                  fw={entry.name === PLAYER ? 700 : 500}
                  c={entry.name === PLAYER ? "yellow.4" : "gray.3"}
                  style={{ fontFamily: "monospace" }}
                >
                  {entry.name}
                </Text>
              </Group>
              <Text
                size="xs"
                fw={entry.name === PLAYER ? 700 : 500}
                c={entry.name === PLAYER ? "yellow.4" : "gray.3"}
                style={{ fontFamily: "monospace", flexShrink: 0 }}
              >
                {entry.score.toLocaleString()}
              </Text>
            </Group>
          ))}
        </Stack>
      </Box>
    </Stack>
  );
}
