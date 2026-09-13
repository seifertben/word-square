import { useCallback } from "react";
import type { Grid } from "../board";
import type { Board } from "../types";

export interface Progress {
  grid: Grid;
  elapsed: number;
  solved: boolean;
}

export function loadProgress(date: string, board: Board): Progress | null {
  try {
    const raw = localStorage.getItem(key(date));
    if (!raw) return null;
    const p = JSON.parse(raw) as Progress;
    if (!Array.isArray(p.grid) || p.grid.length !== board.size) return null;
    // Discard stale saves: every given letter must still match the current
    // board, otherwise the save came from an older puzzle for this date.
    const matches = p.grid.every((row, r) =>
      row.every((cell, c) => {
        const fixed = board.grid[r][c];
        if (fixed && "blocked" in fixed) return cell === "#";
        return fixed && "fixed" in fixed ? cell === fixed.fixed : true;
      }),
    );
    if (!matches) return null;
    return p;
  } catch {
    return null;
  }
}

export function saveProgress(date: string, progress: Progress): void {
  try {
    localStorage.setItem(key(date), JSON.stringify(progress));
  } catch {
    /* storage full or unavailable */
  }
}

export function key(date: string): string {
  return `word-square:${date}`;
}

export function useProgress(board: Board | null) {
  return useCallback(
    (grid: Grid, elapsed: number, solved: boolean) => {
      if (!board) return;
      saveProgress(board.date, { grid, elapsed, solved });
    },
    [board],
  );
}
