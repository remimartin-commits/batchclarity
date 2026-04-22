"""
Chaos App — lightweight FastAPI + SQLite process for crash/restart testing.

Run via:
    python chaos/chaos_app.py

Environment variables:
    CHAOS_STATE_DB   — SQLite path (default: chaos/chaos_state.db)
    CHAOS_APP_PORT   — port (default: 18999)
"""
from __future__ import annotations

import os
import sqlite3
from pathlib import Path

import uvicorn
from fastapi import FastAPI
from pydantic import BaseModel

STATE_DB = os.environ.get("CHAOS_STATE_DB", "chaos/chaos_state.db")
PORT = int(os.environ.get("CHAOS_APP_PORT", "18999"))

app = FastAPI(title="Chaos Test App")


def _conn() -> sqlite3.Connection:
    Path(STATE_DB).parent.mkdir(parents=True, exist_ok=True)
    c = sqlite3.connect(STATE_DB)
    c.execute("""
        CREATE TABLE IF NOT EXISTS records (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            batch       TEXT    NOT NULL,
            step        INTEGER NOT NULL,
            recorded_at TEXT    DEFAULT (datetime('now'))
        )
    """)
    c.commit()
    return c


class RecordIn(BaseModel):
    batch: str
    step: int


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/record")
def write_record(body: RecordIn) -> dict:
    c = _conn()
    c.execute(
        "INSERT INTO records (batch, step) VALUES (?, ?)",
        (body.batch, body.step),
    )
    c.commit()
    count = c.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    c.close()
    return {"status": "written", "count": count}


@app.get("/records")
def read_records() -> dict:
    c = _conn()
    count = c.execute("SELECT COUNT(*) FROM records").fetchone()[0]
    c.close()
    return {"count": count}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=PORT, log_level="warning")
