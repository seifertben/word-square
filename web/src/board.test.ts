import { createEmptyGrid, isFixed, moveCursor } from "./board";
import type { Board } from "./types";

const board: Board = {
  date: "2026-09-11",
  size: 6,
  minWordLength: 6,
  grid: [
    [{ blocked: true }, null, { fixed: "T" }, null, null, null],
    [null, null, null, null, null, null],
    [null, null, null, null, null, null],
    [null, null, null, null, null, null],
    [null, null, null, null, null, null],
    [{ fixed: "C" }, null, null, null, null, null],
  ],
  solution: ["SADHES", "AGRAFE", "DRAFFS", "HAFFET", "EFFETE", "SESTET"],
};

describe("board", () => {
  it("pre-fills fixed cells", () => {
    const grid = createEmptyGrid(board);
    expect(grid[0][0]).toBe("#");
    expect(grid[0][2]).toBe("T");
    expect(grid[5][0]).toBe("C");
    expect(grid[1][1]).toBeNull();
  });

  it("reports fixed cells", () => {
    expect(isFixed(board, 0, 2)).toBe(true);
    expect(isFixed(board, 0, 0)).toBe(false);
  });

  it("clamps cursor movement at the edges", () => {
    expect(moveCursor(board, { row: 0, col: 0 }, 0, -1)).toEqual({ row: 0, col: 0 });
    expect(moveCursor(board, { row: 1, col: 1 }, 0, 1)).toEqual({ row: 1, col: 2 });
    expect(moveCursor(board, { row: 0, col: 5 }, 0, 1)).toEqual({ row: 0, col: 5 });
  });
});
