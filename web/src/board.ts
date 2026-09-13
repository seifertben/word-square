import type { Board, Pos } from "./types";

export type Grid = (string | null)[][];
export const BLOCK = "#";

/** Initial grid: fixed cells pre-filled with their given letter, rest empty. */
export function createEmptyGrid(board: Board): Grid {
  return board.grid.map((row) =>
    row.map((cell) => {
      if (cell && "blocked" in cell) return BLOCK;
      return cell && "fixed" in cell ? cell.fixed : null;
    }),
  );
}

export function isFixed(board: Board, r: number, c: number): boolean {
  const cell = board.grid[r][c];
  return cell !== null && "fixed" in cell;
}

export function isBlocked(board: Board, r: number, c: number): boolean {
  const cell = board.grid[r][c];
  return cell !== null && "blocked" in cell;
}

export function inBounds(board: Board, r: number, c: number): boolean {
  return r >= 0 && r < board.size && c >= 0 && c < board.size;
}

export function moveCursor(board: Board, from: Pos, dr: number, dc: number): Pos {
  const row = from.row + dr;
  const col = from.col + dc;
  return inBounds(board, row, col) ? { row, col } : from;
}

export function cloneGrid(grid: Grid): Grid {
  return grid.map((row) => [...row]);
}

export function letterAt(grid: Grid, p: Pos): string | null {
  return grid[p.row]?.[p.col] ?? null;
}
