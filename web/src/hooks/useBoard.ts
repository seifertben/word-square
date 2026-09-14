import { useCallback, useMemo, useReducer, useState } from "react";
import type { KeyboardEvent as ReactKeyboardEvent } from "react";
import { BLOCK, cloneGrid, createEmptyGrid, isBlocked, isFixed, letterAt } from "../board";
import type { Grid } from "../board";
import { incorrectCells, isWordSquare } from "../validate";
import type { Board, Pos } from "../types";

export interface BoardState {
  grid: Grid;
  cursor: Pos;
  direction: Direction;
  typingDelta: 1 | -1;
  wrong: Set<string>; // "r-c" cells flagged invalid by Check
}

export type Direction = "across" | "down";

type Action =
  | { type: "type"; ch: string }
  | { type: "backspace" }
  | { type: "move"; dr: number; dc: number; axis: Direction }
  | { type: "toggleDirection" }
  | { type: "nextLine"; delta: number }
  | { type: "clickCell"; pos: Pos }
  | { type: "check" }
  | { type: "reveal" }
  | { type: "clear" }
  | { type: "load"; grid: Grid; cursor: Pos; direction?: Direction };

function cellKey(p: Pos): string {
  return `${p.row}-${p.col}`;
}

function inBoundsAt(size: number, p: Pos): boolean {
  return p.row >= 0 && p.row < size && p.col >= 0 && p.col < size;
}

function step(pos: Pos, direction: Direction, delta: number): Pos {
  return {
    row: pos.row + (direction === "down" ? delta : 0),
    col: pos.col + (direction === "across" ? delta : 0),
  };
}

function nextEditable(
  board: Board,
  grid: Grid,
  start: Pos,
  direction: Direction,
  delta: number,
  blankOnly = false,
): Pos | null {
  let pos = step(start, direction, delta);
  while (inBoundsAt(board.size, pos)) {
    if (
      !isBlocked(board, pos.row, pos.col) &&
      !isFixed(board, pos.row, pos.col) &&
      (!blankOnly || letterAt(grid, pos) == null)
    ) {
      return pos;
    }
    pos = step(pos, direction, delta);
  }
  return null;
}

function typingDeltaForClick(
  board: Board,
  grid: Grid,
  pos: Pos,
  direction: Direction,
): 1 | -1 {
  const forward = nextEditable(board, grid, pos, direction, 1, true);
  const reverse = nextEditable(board, grid, pos, direction, -1, true);
  return !forward && reverse ? -1 : 1;
}

function nextPlayable(board: Board, start: Pos, direction: Direction, delta: number): Pos | null {
  let pos = step(start, direction, delta);
  while (inBoundsAt(board.size, pos)) {
    if (!isBlocked(board, pos.row, pos.col)) return pos;
    pos = step(pos, direction, delta);
  }
  return null;
}

function firstPlayable(board: Board): Pos {
  for (let row = 0; row < board.size; row++) {
    for (let col = 0; col < board.size; col++) {
      if (!isBlocked(board, row, col)) return { row, col };
    }
  }
  return { row: 0, col: 0 };
}

export function makeReducer(board: Board) {
  function reduce(state: BoardState, action: Action): BoardState {
    switch (action.type) {
      case "type": {
        if (
          isFixed(board, state.cursor.row, state.cursor.col) ||
          isBlocked(board, state.cursor.row, state.cursor.col)
        ) return state;
        const grid = cloneGrid(state.grid);
        grid[state.cursor.row][state.cursor.col] = action.ch;
        const wrong = new Set(state.wrong);
        wrong.delete(cellKey(state.cursor));
        const cursor =
          nextEditable(board, grid, state.cursor, state.direction, state.typingDelta, true) ??
          state.cursor;
        return { ...state, grid, cursor, wrong };
      }
      case "backspace": {
        if (isBlocked(board, state.cursor.row, state.cursor.col)) return state;
        if (isFixed(board, state.cursor.row, state.cursor.col)) {
          const cursor =
            nextEditable(
              board,
              state.grid,
              state.cursor,
              state.direction,
              -state.typingDelta,
            ) ?? state.cursor;
          return { ...state, cursor };
        }
        const grid = cloneGrid(state.grid);
        let cursor = state.cursor;
        if (letterAt(grid, cursor) != null) {
          grid[cursor.row][cursor.col] = null;
        } else {
          const prev = nextEditable(
            board,
            grid,
            cursor,
            state.direction,
            -state.typingDelta,
          );
          if (prev) {
            cursor = prev;
            grid[prev.row][prev.col] = null;
          }
        }
        const wrong = new Set(state.wrong);
        wrong.delete(cellKey(cursor));
        return { ...state, grid, cursor, wrong };
      }
      case "move": {
        if (state.direction !== action.axis) {
          return { ...state, direction: action.axis, typingDelta: 1 };
        }
        const delta = action.dr || action.dc;
        const cursor = nextPlayable(board, state.cursor, action.axis, delta) ?? state.cursor;
        return { ...state, cursor };
      }
      case "toggleDirection":
        return {
          ...state,
          direction: state.direction === "across" ? "down" : "across",
          typingDelta: 1,
        };
      case "nextLine": {
        const line = state.direction === "across" ? state.cursor.row : state.cursor.col;
        const next = (line + action.delta + board.size) % board.size;
        let cursor = state.direction === "across"
          ? { row: next, col: 0 }
          : { row: 0, col: next };
        if (isBlocked(board, cursor.row, cursor.col)) {
          cursor = nextPlayable(board, cursor, state.direction, 1) ?? cursor;
        }
        return { ...state, cursor, typingDelta: 1 };
      }
      case "clickCell": {
        if (isBlocked(board, action.pos.row, action.pos.col)) return state;
        const same = state.cursor.row === action.pos.row && state.cursor.col === action.pos.col;
        const direction = same
          ? state.direction === "across" ? "down" : "across"
          : state.direction;
        return {
          ...state,
          cursor: action.pos,
          direction,
          typingDelta: typingDeltaForClick(board, state.grid, action.pos, direction),
        };
      }
      case "check": {
        const wrong = incorrectCells(board.size, state.grid, board.solution);
        return { ...state, wrong };
      }
      case "reveal": {
        const grid = cloneGrid(state.grid);
        for (let r = 0; r < board.size; r++) {
          for (let c = 0; c < board.size; c++) {
            grid[r][c] = board.solution[r][c] === BLOCK ? BLOCK : board.solution[r][c];
          }
        }
        return { ...state, grid, wrong: new Set<string>() };
      }
      case "clear":
        return { ...state, grid: createEmptyGrid(board), wrong: new Set<string>() };
      case "load":
        return {
          ...state,
          grid: action.grid,
          cursor: action.cursor,
          direction: action.direction ?? state.direction,
          typingDelta: 1,
          wrong: new Set<string>(),
        };
      default:
        return state;
    }
  }

  return reduce;
}

const EMPTY_BOARD: Board = {
  date: "",
  size: 6,
  minWordLength: 6,
  grid: Array.from({ length: 6 }, () => Array.from({ length: 6 }, () => null)),
  solution: [],
};

export interface UseBoard {
  state: BoardState;
  solved: boolean;
  handleKey: (e: ReactKeyboardEvent) => void;
  typeChar: (ch: string) => void;
  clickCell: (p: Pos) => void;
  check: () => void;
  reveal: () => void;
  clear: () => void;
  restore: (grid: Grid) => void;
}

export function useBoard(board: Board | null, dictionary: Set<string> | null): UseBoard {
  const b = board ?? EMPTY_BOARD;
  const reducer = useMemo(() => makeReducer(b), [b]);
  const [state, dispatch] = useReducer(reducer, {
    grid: createEmptyGrid(b),
    cursor: firstPlayable(b),
    direction: "across",
    typingDelta: 1,
    wrong: new Set<string>(),
  });

  // Reset state synchronously when the board (date/size) changes so the Grid
  // never renders a grid whose dimensions disagree with the board.
  const [prevBoard, setPrevBoard] = useState<Board | null>(board);
  if (prevBoard !== board) {
    setPrevBoard(board);
    dispatch({
      type: "load",
      grid: createEmptyGrid(b),
      cursor: firstPlayable(b),
    });
  }

  const solved = useMemo(
    () =>
      dictionary ? isWordSquare(b.size, state.grid, dictionary, b.minWordLength) : false,
    [state.grid, dictionary, b],
  );

  const handleKey = useCallback((e: ReactKeyboardEvent) => {
    const k = e.key;
    if (/^[a-zA-Z]$/.test(k)) {
      e.preventDefault();
      dispatch({ type: "type", ch: k.toUpperCase() });
    } else if (k === "Backspace") {
      e.preventDefault();
      dispatch({ type: "backspace" });
    } else if (k === " ") {
      e.preventDefault();
      dispatch({ type: "toggleDirection" });
    } else if (k === "Tab" || k === "Enter") {
      e.preventDefault();
      dispatch({ type: "nextLine", delta: e.shiftKey ? -1 : 1 });
    } else {
      switch (k) {
        case "ArrowRight":
          e.preventDefault();
          dispatch({ type: "move", dr: 0, dc: 1, axis: "across" });
          break;
        case "ArrowLeft":
          e.preventDefault();
          dispatch({ type: "move", dr: 0, dc: -1, axis: "across" });
          break;
        case "ArrowDown":
          e.preventDefault();
          dispatch({ type: "move", dr: 1, dc: 0, axis: "down" });
          break;
        case "ArrowUp":
          e.preventDefault();
          dispatch({ type: "move", dr: -1, dc: 0, axis: "down" });
          break;
        default:
          break;
      }
    }
  }, []);

  return {
    state,
    solved,
    handleKey,
    typeChar: (ch) => dispatch({ type: "type", ch: ch.toUpperCase() }),
    clickCell: (p) => dispatch({ type: "clickCell", pos: p }),
    check: () => dispatch({ type: "check" }),
    reveal: () => dispatch({ type: "reveal" }),
    clear: () => dispatch({ type: "clear" }),
    restore: (grid) =>
      dispatch({ type: "load", grid, cursor: firstPlayable(b) }),
  };
}
