import type { Grid } from "./board";
import { BLOCK } from "./board";

// Win/check rules for the word-square game — mirrored from generator/validate.py.
// A grid is solved when every cell is filled and every row and column is a
// dictionary word.

const cellKey = (r: number, c: number) => `${r}-${c}`;

export function isComplete(size: number, grid: Grid): boolean {
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      if (grid[r][c] == null) return false;
    }
  }
  return true;
}

export function isWordSquare(
  size: number,
  grid: Grid,
  dictionary: Set<string>,
  minLen: number,
): boolean {
  if (!isComplete(size, grid)) return false;
  const valid = (word: string) =>
    word.length >= minLen && (dictionary.has(word) || dictionary.has([...word].reverse().join("")));
  for (let r = 0; r < size; r++) {
    let word = "";
    for (let c = 0; c < size; c++) if (grid[r][c] !== BLOCK) word += grid[r][c];
    if (!valid(word)) return false;
  }
  for (let c = 0; c < size; c++) {
    let word = "";
    for (let r = 0; r < size; r++) if (grid[r][c] !== BLOCK) word += grid[r][c];
    if (!valid(word)) return false;
  }
  return true;
}

export interface ValidLines {
  rows: Set<number>;
  cols: Set<number>;
}

/** Indices of rows/columns that currently form a complete dictionary word. */
export function validLines(
  size: number,
  grid: Grid,
  dictionary: Set<string>,
  minLen: number,
): ValidLines {
  const valid = (word: string) =>
    word.length >= minLen && (dictionary.has(word) || dictionary.has([...word].reverse().join("")));
  const rows = new Set<number>();
  const cols = new Set<number>();
  for (let r = 0; r < size; r++) {
    let word = "";
    let complete = true;
    for (let c = 0; c < size; c++) {
      const letter = grid[r][c];
      if (letter === BLOCK) continue;
      if (letter == null) {
        complete = false;
        break;
      }
      word += letter;
    }
    if (complete && valid(word)) rows.add(r);
  }
  for (let c = 0; c < size; c++) {
    let word = "";
    let complete = true;
    for (let r = 0; r < size; r++) {
      const letter = grid[r][c];
      if (letter === BLOCK) continue;
      if (letter == null) {
        complete = false;
        break;
      }
      word += letter;
    }
    if (complete && valid(word)) cols.add(c);
  }
  return { rows, cols };
}

/** Filled cells that do not match the puzzle solution. */
export function incorrectCells(
  size: number,
  grid: Grid,
  solution: string[],
): Set<string> {
  const wrong = new Set<string>();
  for (let r = 0; r < size; r++) {
    for (let c = 0; c < size; c++) {
      const letter = grid[r][c];
      if (letter != null && letter !== BLOCK && letter !== solution[r]?.[c]) {
        wrong.add(cellKey(r, c));
      }
    }
  }
  return wrong;
}
