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
            const classes = [
              "cell",
              blocked ? "blocked" : "",
              fixed ? "fixed" : "",
              isCursor ? "current" : "",
              selected && !isCursor && !blocked ? "selected" : "",
              isWrong ? "wrong" : "",
            ]
              .filter(Boolean)
              .join(" ");
            return (
              <button
                key={key}
                role="gridcell"
                className={classes}
                style={{ gridRow: r + 1, gridColumn: c + 1 }}
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
        {[...valid.rows].map((row) => {
          const first = board.grid[row].findIndex((cell) => !(cell && "blocked" in cell));
          const last = board.grid[row]
            .map((cell) => !(cell && "blocked" in cell))
            .lastIndexOf(true);
          return first < 0 ? null : (
            <span
              key={`valid-row-${row}`}
              className="valid-word-line across"
              style={{ gridRow: row + 1, gridColumn: `${first + 1} / ${last + 2}` }}
              aria-hidden="true"
            >
              {Array.from({ length: last - first + 1 }, (_, index) => (
                <i key={index} />
              ))}
            </span>
          );
        })}
        {[...valid.cols].map((col) => {
          const first = board.grid.findIndex((row) => {
            const cell = row[col];
            return !(cell && "blocked" in cell);
          });
          const last = board.grid
            .map((row) => {
              const cell = row[col];
              return !(cell && "blocked" in cell);
            })
            .lastIndexOf(true);
          return first < 0 ? null : (
            <span
              key={`valid-col-${col}`}
              className="valid-word-line down"
              style={{ gridRow: `${first + 1} / ${last + 2}`, gridColumn: col + 1 }}
              aria-hidden="true"
            >
              {Array.from({ length: last - first + 1 }, (_, index) => (
                <i key={index} />
              ))}
            </span>
          );
        })}
      </div>
    </div>
  );
}
