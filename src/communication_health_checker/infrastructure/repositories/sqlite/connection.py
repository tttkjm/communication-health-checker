import sqlite3
import threading
from collections.abc import Iterator
from contextlib import contextmanager

_SCHEMA = """
CREATE TABLE IF NOT EXISTS targets (
    id          TEXT PRIMARY KEY,
    name        TEXT NOT NULL,
    host        TEXT NOT NULL,
    description TEXT NOT NULL DEFAULT '',
    created_at  TEXT NOT NULL,
    updated_at  TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS ping_logs (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    target_id TEXT NOT NULL,
    seq       INTEGER NOT NULL,
    sent_at   TEXT NOT NULL,
    success   INTEGER NOT NULL,
    rtt_ms    REAL,
    ttl       INTEGER,
    error     TEXT
);

CREATE INDEX IF NOT EXISTS idx_ping_logs_target
    ON ping_logs (target_id, id DESC);
"""


class Database:
    """単一接続をロックで保護する SQLite ラッパ。

    desktop アプリ用途のため、1 接続 + threading.Lock で全操作を直列化する。
    定期 ping のバックグラウンドスレッドと REST 要求の同時アクセスを安全に扱える。
    """

    def __init__(self, db_path: str) -> None:
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        if db_path != ":memory:":
            self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.executescript(_SCHEMA)
        self._conn.commit()

    @contextmanager
    def cursor(self) -> Iterator[sqlite3.Cursor]:
        with self._lock:
            cur = self._conn.cursor()
            try:
                yield cur
                self._conn.commit()
            finally:
                cur.close()

    def close(self) -> None:
        with self._lock:
            self._conn.close()
