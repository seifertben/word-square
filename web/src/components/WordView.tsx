import type { Board, Pos } from "../types";
import type { Grid } from "../board";
import { BLOCK } from "../board";
import type { Direction } from "../hooks/useBoard";

interface WordViewProps {
  board: Board;
  grid: Grid;
  cursor: Pos;
  direction: Direction;
  dictionary: Set<string>;
}

function wordLetters(board: Board, grid: Grid, cursor: Pos, direction: Direction): (string | null)[] {
  const letters: (string | null)[] = [];
  if (direction === "across") {
    for (let c = 0; c < board.size; c++) {
      const letter = grid[cursor.row][c];
      if (letter !== BLOCK) letters.push(letter);
    }
  } else {
    for (let r = 0; r < board.size; r++) {
      const letter = grid[r][cursor.col];
      if (letter !== BLOCK) letters.push(letter);
    }
  }
  return letters;
}

function isWord(letters: (string | null)[], dictionary: Set<string>): boolean {
  if (letters.some((letter) => letter == null)) return false;
  return dictionary.has(letters.join(""));
}

function WordTiles({ letters, valid }: { letters: (string | null)[]; valid: boolean }) {
  return (
    <span className="word-tiles">
      {letters.map((letter, i) => (
        <span key={i} className={`word-tile${letter ? "" : " empty"}${valid ? " valid" : ""}`}>
          {letter ?? ""}
        </span>
      ))}
    </span>
  );
}

export function WordView({ board, grid, cursor, direction, dictionary }: WordViewProps) {
  const letters = wordLetters(board, grid, cursor, direction);
  const label =
    direction === "across" ? `Row ${cursor.row + 1}` : `Column ${cursor.col + 1}`;
  const forwardValid = isWord(letters, dictionary);
  const reverseValid = isWord([...letters].reverse(), dictionary);
  return (
    <div className="word-view" aria-live="polite">
      <span className="word-view-label">{label}</span>
      <div className="word-view-line">
        <span className="word-view-name">Forward</span>
        <WordTiles letters={letters} valid={forwardValid} />
      </div>
      <div className="word-view-line">
        <span className="word-view-name">Reverse</span>
        <WordTiles letters={[...letters].reverse()} valid={reverseValid} />
      </div>
    </div>
  );
}