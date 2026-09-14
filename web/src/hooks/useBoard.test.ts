import { createEmptyGrid } from "../board";
import type { Board } from "../types";
import { makeReducer } from "./useBoard";

const board: Board = {
  date: "2026-09-14",
  size: 4,
  minWordLength: 4,
  grid: Array.from({ length: 4 }, () => Array.from({ length: 4 }, () => null)),
  solution: ["ABCD", "BCDA", "CDAB", "DABC"],
};

function initialState() {
  return {
    grid: createEmptyGrid(board),
    cursor: { row: 0, col: 0 },
    direction: "across" as const,
    typingDelta: 1 as const,
    wrong: new Set<string>(),
  };
}

describe("useBoard typing direction", () => {
  it("types in reverse when only earlier cells are open", () => {
    const reduce = makeReducer(board);
    let state = reduce(initialState(), { type: "clickCell", pos: { row: 0, col: 3 } });

    expect(state.typingDelta).toBe(-1);
    state = reduce(state, { type: "type", ch: "D" });
    expect(state.cursor).toEqual({ row: 0, col: 2 });
  });

  it("keeps the forward default when cells are open on both sides", () => {
    const reduce = makeReducer(board);
    let state = reduce(initialState(), { type: "clickCell", pos: { row: 0, col: 1 } });

    expect(state.typingDelta).toBe(1);
    state = reduce(state, { type: "type", ch: "B" });
    expect(state.cursor).toEqual({ row: 0, col: 2 });
  });

  it("backspaces opposite to the selected reverse typing direction", () => {
    const reduce = makeReducer(board);
    let state = reduce(initialState(), { type: "clickCell", pos: { row: 0, col: 3 } });
    state = reduce(state, { type: "type", ch: "D" });
    state = reduce(state, { type: "type", ch: "C" });
    state = reduce(state, { type: "backspace" });

    expect(state.cursor).toEqual({ row: 0, col: 2 });
    expect(state.grid[0][2]).toBeNull();
  });
});
