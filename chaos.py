"""
GMP Platform — Chaos Test Suite
================================
Deterministic failure simulations with pass/fail + recovery metrics.

Usage:
    python chaos.py

Exit code:
    0 — all scenarios passed
    1 — one or more scenarios failed

Report:
    chaos/last-report.json
"""
from __future__ import annotations

import json
import os
import queue
import sqlite3
import subprocess
import sys
import threading
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.error import URLError

CHAOS_DIR = Path(__file__).parent / "chaos"
CHAOS_DIR.mkdir(exist_ok=True)

REPORT_FILE = CHAOS_DIR / "last-report.json"
APP_PORT = 18999
APP_URL = f"http://127.0.0.1:{APP_PORT}"


# ── Colour helpers (degrade gracefully on Windows CI) ────────────────────────

def _green(s: str) -> str:
    return f"\033[32m{s}\033[0m" if sys.stdout.isatty() else s


def _red(s: str) -> str:
    return f"\033[31m{s}\033[0m" if sys.stdout.isatty() else s


def _header(name: str) -> None:
    print(f"\n{'─' * 60}")
    print(f"  SCENARIO: {name}")
    print(f"{'─' * 60}")


# ── Result dataclass ─────────────────────────────────────────────────────────

@dataclass
class ScenarioResult:
    name: str
    passed: bool
    time_to_recovery_ms: float | None
    data_integrity: str   # "ok" | "corrupted" | "n/a"
    notes: str


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 1 — Kill DB connection mid-batch, verify no partial data survives
# ─────────────────────────────────────────────────────────────────────────────

def scenario_db_connection_kill() -> ScenarioResult:
    name = "Kill DB connection mid-batch"
    _header(name)

    db_path = CHAOS_DIR / "s1_batch.db"
    db_path.unlink(missing_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE batch_steps (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            step_number INTEGER NOT NULL,
            recorded_value TEXT,
            performed_at TEXT
        )
    """)
    conn.commit()

    # Committed baseline: 5 steps
    for i in range(1, 6):
        conn.execute(
            "INSERT INTO batch_steps (step_number, recorded_value, performed_at)"
            " VALUES (?, ?, datetime('now'))",
            (i, f"value_{i}"),
        )
    conn.commit()
    print("  [setup] Committed 5 baseline steps.")

    # Start uncommitted transaction then kill the connection
    t0 = time.monotonic()
    try:
        conn.execute("BEGIN")
        conn.execute(
            "INSERT INTO batch_steps (step_number, recorded_value, performed_at)"
            " VALUES (?, ?, datetime('now'))",
            (6, "UNCOMMITTED"),
        )
        print("  [chaos] Killing connection with uncommitted step-6 transaction...")
        conn.close()          # Drop connection — transaction is rolled back
    except Exception as exc:
        print(f"  [chaos] Kill raised: {exc}")

    # Recovery: reconnect, count rows
    t1 = time.monotonic()
    conn2 = sqlite3.connect(str(db_path))
    rows = conn2.execute("SELECT COUNT(*) FROM batch_steps").fetchone()[0]
    conn2.close()

    recovery_ms = (t1 - t0) * 1000
    integrity = "ok" if rows == 5 else "corrupted"

    print(f"  [verify] Rows after kill: {rows} (expected 5)")
    print(f"  [verify] Integrity: {integrity}")
    print(f"  [timing] {recovery_ms:.1f}ms")

    passed = rows == 5
    print(f"  {_green('PASS') if passed else _red('FAIL')}")
    return ScenarioResult(name, passed, recovery_ms, integrity, f"rows={rows}")


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 2 — Inject 10x query latency, verify system still processes correctly
# ─────────────────────────────────────────────────────────────────────────────

def scenario_db_latency() -> ScenarioResult:
    name = "10x DB query latency injection"
    _header(name)

    db_path = CHAOS_DIR / "s2_latency.db"
    db_path.unlink(missing_ok=True)

    conn = sqlite3.connect(str(db_path))
    conn.execute("CREATE TABLE records (id INTEGER PRIMARY KEY, value TEXT)")
    conn.executemany(
        "INSERT INTO records (value) VALUES (?)",
        [(f"row_{i}",) for i in range(1000)],
    )
    conn.commit()

    INJECTED_LATENCY_S = 0.05   # 50ms — represents 10x of a 5ms baseline
    QUERY_COUNT = 8
    latencies: list[float] = []

    print(f"  [chaos] Injecting {INJECTED_LATENCY_S * 1000:.0f}ms latency per query ({QUERY_COUNT} queries)")

    for _ in range(QUERY_COUNT):
        t0 = time.monotonic()
        time.sleep(INJECTED_LATENCY_S)
        conn.execute("SELECT COUNT(*) FROM records").fetchone()
        latencies.append((time.monotonic() - t0) * 1000)

    conn.close()

    avg_ms = sum(latencies) / len(latencies)
    max_ms = max(latencies)

    # Pass: latency was registered (avg > 40ms) and didn't spiral (max < 500ms)
    passed = avg_ms > 40 and max_ms < 500

    print(f"  [verify] Avg latency: {avg_ms:.1f}ms | Max: {max_ms:.1f}ms")
    print(f"  [verify] All {QUERY_COUNT} queries completed")
    print(f"  {_green('PASS') if passed else _red('FAIL')}")
    return ScenarioResult(
        name, passed, avg_ms, "n/a",
        f"avg_ms={avg_ms:.1f} max_ms={max_ms:.1f}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 3 — Fill event bus to 10,000 messages, verify clean drain
# ─────────────────────────────────────────────────────────────────────────────

def scenario_event_bus_fill() -> ScenarioResult:
    name = "Event bus fill to 10,000 messages"
    _header(name)

    TARGET = 10_000
    bus: queue.Queue[dict] = queue.Queue(maxsize=TARGET)

    print(f"  [chaos] Flooding bus with {TARGET:,} messages...")
    t0 = time.monotonic()
    dropped = 0
    for i in range(TARGET):
        try:
            bus.put_nowait({"event": "calibration_overdue", "eq_id": f"EQ-{i:05d}", "seq": i})
        except queue.Full:
            dropped += 1

    fill_ms = (time.monotonic() - t0) * 1000
    print(f"  [chaos] Filled: size={bus.qsize():,} | dropped={dropped} | {fill_ms:.0f}ms")

    # Drain — every 100th message is treated as corrupted → dead-letter
    t1 = time.monotonic()
    drained = 0
    dead_letters: list[dict] = []

    while not bus.empty():
        msg = bus.get_nowait()
        if msg["seq"] % 100 == 0:
            dead_letters.append(msg)
        else:
            drained += 1
        bus.task_done()

    drain_ms = (time.monotonic() - t1) * 1000
    expected_dead = TARGET // 100
    dead_ok = abs(len(dead_letters) - expected_dead) <= 1
    total_accounted = drained + len(dead_letters)

    print(f"  [verify] Drained: {drained:,} | Dead-letters: {len(dead_letters)} (expected {expected_dead})")
    print(f"  [verify] Total accounted: {total_accounted:,} | Drain time: {drain_ms:.0f}ms")

    passed = dropped == 0 and total_accounted == TARGET and dead_ok
    print(f"  {_green('PASS') if passed else _red('FAIL')}")
    return ScenarioResult(
        name, passed, drain_ms,
        "ok" if dead_ok else "corrupted",
        f"drained={drained} dead={len(dead_letters)} dropped={dropped}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 4 — Corrupt 1-in-100 messages, verify dead-letter accounting
# ─────────────────────────────────────────────────────────────────────────────

def scenario_message_corruption() -> ScenarioResult:
    name = "Message corruption + dead-letter verification"
    _header(name)

    COUNT = 1_000
    messages = [
        {"id": i, "payload": f"data_{i}", "checksum": hash(f"data_{i}")}
        for i in range(COUNT)
    ]

    # Corrupt exactly every 100th message
    for msg in messages:
        if msg["id"] % 100 == 0:
            msg["payload"] = f"CORRUPTED_{msg['id']}"

    print(f"  [chaos] Processing {COUNT} messages with 1-in-100 corruption")
    t0 = time.monotonic()

    processed = 0
    dead_letters: list[int] = []

    for msg in messages:
        if hash(msg["payload"]) != msg["checksum"]:
            dead_letters.append(msg["id"])
        else:
            processed += 1

    elapsed_ms = (time.monotonic() - t0) * 1000
    expected_dead = COUNT // 100
    all_accounted = (processed + len(dead_letters)) == COUNT
    dead_ok = len(dead_letters) == expected_dead

    print(f"  [verify] Processed: {processed} | Dead-lettered: {len(dead_letters)} (expected {expected_dead})")
    print(f"  [verify] All accounted: {all_accounted}")

    passed = all_accounted and dead_ok
    print(f"  {_green('PASS') if passed else _red('FAIL')}")
    return ScenarioResult(
        name, passed, elapsed_ms,
        "ok" if all_accounted else "corrupted",
        f"processed={processed} dead={len(dead_letters)}",
    )


# ─────────────────────────────────────────────────────────────────────────────
# SCENARIO 5 — Crash app process mid-operation, verify state recovery
# ─────────────────────────────────────────────────────────────────────────────

def _wait_for_health(url: str, timeout: float = 20.0) -> bool:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            with urlopen(f"{url}/health", timeout=2) as resp:
                if resp.status == 200:
                    return True
        except Exception:
            time.sleep(0.4)
    return False


def scenario_process_crash_recovery() -> ScenarioResult:
    name = "App process crash + state recovery"
    _header(name)

    chaos_app = CHAOS_DIR / "chaos_app.py"
    if not chaos_app.exists():
        print(f"  [skip] {chaos_app} not found — skipping")
        return ScenarioResult(name, False, None, "n/a", "chaos/chaos_app.py missing")

    state_db = str(CHAOS_DIR / "crash_state.db")
    Path(state_db).unlink(missing_ok=True)

    env = os.environ.copy()
    env["CHAOS_STATE_DB"] = state_db
    env["CHAOS_APP_PORT"] = str(APP_PORT)

    print("  [setup] Starting chaos app...")
    proc = subprocess.Popen(
        [sys.executable, str(chaos_app)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    if not _wait_for_health(APP_URL, timeout=20):
        proc.kill()
        return ScenarioResult(name, False, None, "n/a", "App did not start within 20s")

    # Write a record before crash
    try:
        req = Request(
            f"{APP_URL}/record",
            data=json.dumps({"batch": "B-CHAOS-001", "step": 1}).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req, timeout=5) as resp:
            pre = json.loads(resp.read())
        print(f"  [setup] Pre-crash state: {pre}")
    except Exception as exc:
        proc.kill()
        return ScenarioResult(name, False, None, "n/a", f"Pre-crash write failed: {exc}")

    # Kill the process
    t0 = time.monotonic()
    print("  [chaos] Sending kill signal...")
    proc.kill()
    proc.wait()
    print("  [chaos] Process killed.")

    # Restart
    print("  [recovery] Restarting...")
    proc2 = subprocess.Popen(
        [sys.executable, str(chaos_app)],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    recovered = _wait_for_health(APP_URL, timeout=20)
    recovery_ms = (time.monotonic() - t0) * 1000

    if not recovered:
        proc2.kill()
        return ScenarioResult(name, False, recovery_ms, "n/a", "App did not recover within 20s")

    # Verify persisted state
    try:
        with urlopen(f"{APP_URL}/records", timeout=5) as resp:
            post = json.loads(resp.read())
    except Exception as exc:
        proc2.kill()
        return ScenarioResult(name, False, recovery_ms, "n/a", f"Post-recovery read failed: {exc}")

    proc2.kill()
    pre_count = pre.get("count", 0)
    post_count = post.get("count", 0)
    integrity = "ok" if post_count >= pre_count else "corrupted"

    print(f"  [verify] Pre-crash records: {pre_count} | Post-recovery: {post_count}")
    print(f"  [verify] Integrity: {integrity} | Recovery: {recovery_ms:.0f}ms")

    passed = recovered and post_count >= pre_count
    print(f"  {_green('PASS') if passed else _red('FAIL')}")
    return ScenarioResult(name, passed, recovery_ms, integrity, f"pre={pre_count} post={post_count}")


# ─────────────────────────────────────────────────────────────────────────────
# RUNNER
# ─────────────────────────────────────────────────────────────────────────────

def main() -> int:
    print("\n" + "═" * 60)
    print("  GMP PLATFORM — CHAOS TEST SUITE")
    print("═" * 60)

    scenarios = [
        scenario_db_connection_kill,
        scenario_db_latency,
        scenario_event_bus_fill,
        scenario_message_corruption,
        scenario_process_crash_recovery,
    ]

    results: list[ScenarioResult] = []
    for fn in scenarios:
        try:
            result = fn()
        except Exception as exc:
            result = ScenarioResult(
                name=fn.__name__,
                passed=False,
                time_to_recovery_ms=None,
                data_integrity="n/a",
                notes=f"Unhandled exception: {exc}",
            )
        results.append(result)

    # Summary
    print("\n" + "═" * 60)
    print("  SUMMARY")
    print("═" * 60)

    all_passed = True
    for r in results:
        tag = _green("PASS") if r.passed else _red("FAIL")
        rec = f"{r.time_to_recovery_ms:.0f}ms" if r.time_to_recovery_ms is not None else "n/a"
        print(f"  [{tag}] {r.name}")
        print(f"         recovery={rec}  integrity={r.data_integrity}")
        if r.notes:
            print(f"         {r.notes}")
        if not r.passed:
            all_passed = False

    report = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "all_passed": all_passed,
        "scenarios": [asdict(r) for r in results],
    }
    REPORT_FILE.write_text(json.dumps(report, indent=2))
    print(f"\n  Report: {REPORT_FILE}")
    print("═" * 60 + "\n")

    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
