import type { Board } from "./types";

// Two serving modes, chosen at build time:
//   "api"    (default) — the FastAPI app serves the SPA and reads board blobs
//   "static"           — boards are static files shipped next to the SPA
const STATIC = import.meta.env.VITE_PUZZLE_MODE === "static";
const BOARD_DIR = `${import.meta.env.BASE_URL}boards`;

// The daily role over at 6:00 AM Eastern, not midnight.
const EASTERN_DAILY_START = 6;
export function todayEastern(now: number = Date.now()): string {
  const parts = new Intl.DateTimeFormat("en-US", {
    timeZone: "America/New_York",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(new Date(now - EASTERN_DAILY_START * 60 * 60 * 1000));
  const byType = (t: string) => parts.find((p) => p.type === t)?.value ?? "";
  return `${byType("year")}-${byType("month")}-${byType("day")}`;
}

async function fetchJson(url: string): Promise<Board> {
  const res = await fetch(url);
  if (!res.ok) {
    if (STATIC) throw new Error(`Failed to load board (${res.status})`);
    const body = await res.json().catch(() => null);
    throw new Error(body?.detail ?? `Failed to load board (${res.status})`);
  }
  return (await res.json()) as Board;
}

export async function fetchBoard(date: string): Promise<Board> {
  return fetchJson(STATIC ? `${BOARD_DIR}/${date}.json` : `/api/puzzle/${date}`);
}

export async function fetchToday(): Promise<Board> {
  if (STATIC) return fetchBoard(todayEastern());
  return fetchJson("/api/puzzle");
}
