import type { Board, Pos } from "../types";
import type { Grid } from "../board";
import type { Direction } from "../hooks/useBoard";
import type { ValidLines } from "../validate";

interface GridProps {
  board: Board;
  grid: Grid;
  cursor: Pos;
  direction: Direction;
  wrong: Set<string>;
  valid: ValidLines;
  onCellClick: (p: Pos) => void;
}

export function Grid({ board, grid, cursor, direction, wrong, valid, onCellClick }: GridProps) {

  return (
    <div className="board-wrap">
      <div
        className="board"
        role="grid"
        style={{ gridTemplateColumns: `repeat(${board.size}, var(--cell))` }}
      >
        {grid.map((row, r) =>
          row.map((letter, c) => {
            const cell = board.grid[r][c];
            const blocked = cell !== null && "blocked" in cell;
            const fixed = cell !== null && "fixed" in cell;
            const isCursor = cursor.row === r && cursor.col === c;
            const key = `${r}-${c}`;
            const selected = direction === "across" ? cursor.row === r : cursor.col === c;
            const isWrong = wrong.has(key);
            const inValidRow = !blocked && valid.rows.has(r);
            const inValidCol = !blocked && valid.cols.has(c);
            const classes = [
              "cell",
              blocked ? "blocked" : "",
              fixed ? "fixed" : "",
              isCursor ? "current" : "",
              selected && !isCursor && !blocked ? "selected" : "",
              isWrong ? "wrong" : "",
              inValidRow ? "valid-row" : "",
              inValidCol ? "valid-col" : "",
            ]
              .filter(Boolean)
              .join(" ");
            return (
              <button
                key={key}
                role="gridcell"
                className={classes}
                tabIndex={-1}
                disabled={blocked}
                onClick={() => onCellClick({ row: r, col: c })}
                aria-label={`row ${r + 1} column ${c + 1}${blocked ? ", blocked" : fixed ? ", given letter" : ""}`}
              >
                <span className="letter">{letter ?? ""}</span>
              </button>
            );
          }),
        )}
      </div>
    </div>
  );
}
