# Word Square

A 6×6 daily word-grid game: every row and every column of the completed grid
spells a five- or six-letter English word, in either direction. A fraction of the letters are blanked out and
your goal is to fill them back in. Modeled on
[`daily-crossword`](../daily-crossword) — a uv/FastAPI generator plus a
React/Vite/TypeScript SPA, deployable as a fully static site (GitHub Pages) with
no backend.

## How the game works

- The hidden answer is a **double word grid**: a 6×6 grid where all six rows
  *and* all six columns are valid English words, read forward or backward.
- Opposite corners are blacked out, shortening two rows and two columns to five
  letters.
- The generator keeps ~60% of the outer-ring letters as locked **givens** and
  blanks ~50% of the interior cells for you to fill in.
- You win when the grid is fully filled and every row *and* column is a real
  word — validation is open-ended against the dictionary, not a single hidden
  answer.

## Layout

```
generator/          Python board generator (double word square + blanking)
api/                FastAPI serving app (optional; not needed for static)
web/                React + Vite + TypeScript SPA
data/               vendored ESDB American English word list
tests/              pytest (generator + validation parity)
.github/workflows/  CI, daily generation, GitHub Pages deploy
```

## Development

```sh
make install        # uv sync
make gen            # generate today's board (PUZZLE_STORE=local => ./local-data)
make gen-static     # generate a board into web/public/boards for a static build
make dev            # FastAPI on :8000 (serves board JSON + SPA)
make web-dev        # Vite dev server on :5173, proxies /api -> :8000
make build-web      # build the SPA (VITE_PUZZLE_MODE=static for static boards)
make test           # pytest
make web-test       # vitest
make lint           # ruff
make typecheck      # mypy
```

The client dictionary asset (`web/public/dictionary/words.json`) is the ESDB
list trimmed to five- and six-letter alphabetic words. It is committed; regenerate with:

```sh
uv run python -m generator --dictionary-out web/public/dictionary/words.json
```

## Static deployment

Three GitHub Actions workflows:

- **gen-daily.yml** — cron at 03:00 UTC generates tomorrow's board
  (`PUZZLE_STORE=static`), commits `web/public/boards/YYYY-MM-DD.json`, and
  triggers a redeploy.
- **pages.yml** — builds the SPA (`VITE_PUZZLE_MODE=static`) and uploads
  `web/dist` to GitHub Pages.
- **ci.yml** — ruff, mypy, pytest, vitest, and a static build check.

`web/src/api.ts` keeps the same static/API switch as `daily-crossword`, so a
server (FastAPI + Cloud Run) remains an option with zero frontend changes.

## Dictionary

The word list is `data/words.txt`, derived from level 50 of the English Speller
Database (ESDB) American English release 2026.02.25. Only lowercase alphabetic
entries are kept, excluding proper names, abbreviations, special categories,
and entries such as `SPEERS`. See `data/ESDB-LICENSE.txt`. The generator reads
it directly; the client bundle is the trimmed five- and six-letter subset.
