"""FastAPI application: serve the daily board JSON + the SPA.

The serving app only reads immutable board blobs from the store (local disk in
dev, GCS in prod). It never runs the generator. The dev-only
``POST /api/dev/generate`` endpoint (enabled only when ``APP_ENV=dev``) lets you
regenerate a board from the browser.
"""

from __future__ import annotations

import datetime as dt
import json
import os
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator

from generator.pipeline import generate_board
from generator.store import BoardStore, get_store

load_dotenv(Path(__file__).resolve().parents[1] / ".env")

app = FastAPI(title="Word Square")

_STATIC_DIR = Path(__file__).resolve().parents[1] / "web" / "dist"
_STATIC_DIR.mkdir(parents=True, exist_ok=True)

_ET = ZoneInfo("America/New_York")

_DATE_FMT = "%Y-%m-%d"


def _today() -> str:
    now = dt.datetime.now(_ET) - dt.timedelta(hours=6)
    return now.date().strftime(_DATE_FMT)


def _valid_date(s: str) -> str:
    try:
        d = dt.datetime.strptime(s, _DATE_FMT).date()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from exc
    return d.strftime(_DATE_FMT)


def _store() -> BoardStore:
    return get_store()


class HealthResponse(BaseModel):
    status: str
    store: str
    date: str


class DevGenerateRequest(BaseModel):
    date: str | None = None
    outer_keep_ratio: float = 0.5
    inner_blank_ratio: float = 2 / 3

    @field_validator("outer_keep_ratio", "inner_blank_ratio")
    @classmethod
    def _check_ratio(cls, v: float) -> float:
        if not 0.0 <= v <= 1.0:
            raise ValueError("ratio must be between 0 and 1")
        return v


def _is_dev() -> bool:
    return os.environ.get("APP_ENV", "dev").strip().lower() == "dev"


@app.get("/api/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        status="ok",
        store=os.environ.get("PUZZLE_STORE", "local"),
        date=_today(),
    )


@app.get("/api/puzzle")
async def board_today() -> JSONResponse:
    return await _serve_board(_today(), immutable=False)


@app.get("/api/puzzle/{date}")
async def board_dated(date: str) -> JSONResponse:
    return await _serve_board(_valid_date(date), immutable=True)


async def _serve_board(date: str, *, immutable: bool) -> JSONResponse:
    payload = _store().get(date)
    if payload is None:
        raise HTTPException(status_code=404, detail=f"No board generated for {date}.")
    data = json.loads(payload)
    headers = (
        {"Cache-Control": "public, max-age=300, s-maxage=31536000"}
        if immutable
        else {"Cache-Control": "no-cache"}
    )
    return JSONResponse(content=data, headers=headers)


@app.post("/api/dev/generate")
async def dev_generate(req: DevGenerateRequest) -> JSONResponse:
    """Regenerate a board on demand (dev only). Never enabled in prod."""
    if not _is_dev():
        raise HTTPException(status_code=404, detail="Not found")
    date = _valid_date(req.date) if req.date else _today()
    try:
        board = generate_board(
            date,
            outer_keep_ratio=req.outer_keep_ratio,
            inner_blank_ratio=req.inner_blank_ratio,
        )
    except Exception as exc:  # noqa: BLE001 - surface any gen failure to dev
        raise HTTPException(status_code=500, detail=str(exc)) from exc
    from generator.serialize import board_to_dict

    return JSONResponse(content=board_to_dict(board), headers={"Cache-Control": "no-cache"})


@app.get("/")
async def index() -> Response:
    return _serve_index()


def _serve_index() -> Response:
    index_html = _STATIC_DIR / "index.html"
    if index_html.exists():
        return FileResponse(index_html, headers={"Cache-Control": "no-cache"})
    return Response(
        content=_PLACEHOLDER_HTML,
        media_type="text/html",
        headers={"Cache-Control": "no-cache"},
    )


if _STATIC_DIR.exists():
    _ASSETS_DIR = _STATIC_DIR / "assets"
    if _ASSETS_DIR.exists():
        app.mount("/assets", StaticFiles(directory=_ASSETS_DIR), name="assets")
    _DICT_DIR = _STATIC_DIR / "dictionary"
    if _DICT_DIR.exists():
        app.mount("/dictionary", StaticFiles(directory=_DICT_DIR), name="dictionary")


@app.get("/{path:path}")
async def spa(path: str) -> Response:
    if path.startswith("api/"):
        raise HTTPException(status_code=404, detail="Not found")
    return _serve_index()


_PLACEHOLDER_HTML = """<!DOCTYPE html>
<html><head><meta charset='utf-8'><title>Word Square</title>
<style>body{font-family:system-ui,sans-serif;max-width:42rem;margin:2rem auto;padding:0 1rem}
code{background:#eee;padding:.1em .3em;border-radius:3px}</style></head>
<body><h1>Word Square</h1>
<p>The SPA build has not been produced yet. The board API is live:</p>
<ul>
<li><code>GET /api/puzzle</code> &mdash; today's board</li>
<li><code>GET /api/puzzle/YYYY-MM-DD</code> &mdash; a specific date</li>
<li><code>POST /api/dev/generate</code> &mdash; regenerate (dev)</li>
</ul>
<p>Generate a board first: <code>make gen-stub</code></p>
</body></html>
"""
