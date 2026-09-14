import { useEffect, useMemo, useRef, useState } from "react";
import { fetchToday } from "./api";
import { loadDictionary } from "./dictionary";
import { Grid } from "./components/Grid";
import { WordView } from "./components/WordView";
import { Toolbar } from "./components/Toolbar";
import { WinOverlay } from "./components/WinOverlay";
import { useBoard } from "./hooks/useBoard";
import { useTimer } from "./hooks/useTimer";
import { useMedia } from "./hooks/useMedia";
import { loadProgress, useProgress } from "./hooks/useProgress";
import { createEmptyGrid } from "./board";
import { validLines } from "./validate";
import type { Board } from "./types";

function fmt(seconds: number): string {
  const m = Math.floor(seconds / 60);
  const s = seconds % 60;
  return `${m}:${s.toString().padStart(2, "0")}`;
}

export default function App() {
  const [board, setBoard] = useState<Board | null>(null);
  const [dictionary, setDictionary] = useState<Set<string> | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [winDismissed, setWinDismissed] = useState(false);

  useEffect(() => {
    let cancelled = false;
    Promise.all([fetchToday(), loadDictionary()])
      .then(([b, d]) => {
        if (cancelled) return;
        setBoard(b);
        setDictionary(d);
      })
      .catch((e: unknown) => {
        if (!cancelled) setError(e instanceof Error ? e.message : String(e));
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const { state, solved, handleKey, typeChar, clickCell, check, reveal, clear, restore } = useBoard(
    board,
    dictionary,
  );
  const timer = useTimer(0);
  const startedRef = useRef(false);
  const inputRef = useRef<HTMLInputElement>(null);
  const coarsePointer = useMedia("(pointer: coarse)");
  const save = useProgress(board);

  const emptyGrid = useMemo(() => (board ? createEmptyGrid(board) : null), [board]);
  const valid = useMemo(
    () =>
      board && dictionary
        ? validLines(board.size, state.grid, dictionary, board.minWordLength)
        : { rows: new Set<number>(), cols: new Set<number>() },
    [board, state.grid, dictionary],
  );

  // Restore saved progress once the board is known.
  useEffect(() => {
    if (!board) return;
    const saved = loadProgress(board.date, board);
    if (saved) {
      restore(saved.grid);
      timer.setElapsed(saved.elapsed);
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [board]);

  // Start the timer on the first edit.
  useEffect(() => {
    if (!solved && startedRef.current && !timer.running) timer.start();
  }, [timer, solved]);

  useEffect(() => {
    if (solved && timer.running) timer.pause();
  }, [solved, timer.running, timer.pause]);

  useEffect(() => {
    if (!solved) setWinDismissed(false);
  }, [solved]);

  // Persist progress on changes.
  useEffect(() => {
    if (!board) return;
    save(state.grid, timer.elapsed, solved);
  }, [board, state.grid, timer.elapsed, solved, save]);

  // Detect the first edit to kick off the timer.
  useEffect(() => {
    if (!emptyGrid) return;
    const edited = emptyGrid.some((row, r) =>
      row.some((cell, c) => cell !== state.grid[r][c]),
    );
    if (edited) startedRef.current = true;
  }, [state.grid, emptyGrid]);

  const onKeyDown = handleKey;

  useEffect(() => {
    if (board && !coarsePointer) inputRef.current?.focus({ preventScroll: true });
  }, [board, state.cursor, coarsePointer]);

  const onInput = (e: React.FormEvent<HTMLInputElement>) => {
    const input = e.currentTarget;
    const ch = input.value.slice(-1);
    input.value = "";
    if (/^[a-zA-Z]$/.test(ch)) typeChar(ch);
  };

  const clearPuzzle = () => {
    clear();
    timer.reset();
    startedRef.current = false;
    setWinDismissed(true);
  };

  if (error) {
    return <div className="app"><p className="error">{error}</p></div>;
  }
  if (!board || !dictionary) {
    return <div className="app"><p className="loading">Loading…</p></div>;
  }

  return (
    <div className="app">
      <input
        ref={inputRef}
        className="hidden-input"
        type="text"
        autoComplete="off"
        autoCapitalize="characters"
        autoCorrect="off"
        spellCheck={false}
        aria-label="Word square letter input"
        onKeyDown={onKeyDown}
        onInput={onInput}
      />
      <header className="header">
        <h1>Word Square</h1>
        <div className="meta">
          <span>{board.date}</span>
          <span className="timer">{fmt(timer.elapsed)}</span>
        </div>
        <p className="instructions">
          Fill the blank cells so every row and column spells a valid English
          word, read in either direction (the blacked-out corners are skipped).
          Given letters are locked in. The row or column you’re editing is
          highlighted, and any line that forms a complete dictionary word gets
          a green outline.
        </p>
      </header>

      <div
        className={`board-container${solved ? " solved" : ""}`}
        aria-label="Word square grid"
      >
        <Grid
          board={board}
          grid={state.grid}
          cursor={state.cursor}
          direction={state.direction}
          wrong={state.wrong}
          valid={valid}
          onCellClick={(p) => {
            clickCell(p);
            inputRef.current?.focus({ preventScroll: true });
          }}
        />
      </div>

      <WordView
        board={board}
        grid={state.grid}
        cursor={state.cursor}
        direction={state.direction}
        dictionary={dictionary}
      />

      <Toolbar onCheck={check} onReveal={reveal} onClear={clearPuzzle} solved={solved} />

      {solved && !winDismissed && (
        <WinOverlay elapsed={timer.elapsed} onClose={() => setWinDismissed(true)} />
      )}
    </div>
  );
}
