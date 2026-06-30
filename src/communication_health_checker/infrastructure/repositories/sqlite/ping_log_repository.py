from communication_health_checker.domain.models.ping.ping_log import PingLog
from communication_health_checker.domain.models.target.target_id import TargetId
from communication_health_checker.domain.repositories.i_ping_log_repository import IPingLogRepository
from communication_health_checker.infrastructure.repositories.sqlite.connection import Database
from communication_health_checker.infrastructure.repositories.sqlite.ping_log_mapper import (
    ping_log_to_params,
    row_to_ping_log,
)


class SqlitePingLogRepository(IPingLogRepository):
    """SQLite による IPingLogRepository 実装。"""

    def __init__(self, database: Database) -> None:
        self._db = database

    def append_many(self, logs: list[PingLog]) -> None:
        if not logs:
            return
        params = [ping_log_to_params(log) for log in logs]
        with self._db.cursor() as cur:
            cur.executemany(
                """
                INSERT INTO ping_logs (target_id, seq, sent_at, success, rtt_ms, ttl, error)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                params,
            )

    def find_by_target(self, target_id: TargetId, limit: int = 200) -> list[PingLog]:
        with self._db.cursor() as cur:
            cur.execute(
                "SELECT * FROM ping_logs WHERE target_id = ? ORDER BY id DESC LIMIT ?",
                (str(target_id), limit),
            )
            rows = cur.fetchall()
        return [row_to_ping_log(r) for r in rows]

    def clear_by_target(self, target_id: TargetId) -> None:
        with self._db.cursor() as cur:
            cur.execute("DELETE FROM ping_logs WHERE target_id = ?", (str(target_id),))

    def clear_all(self) -> None:
        with self._db.cursor() as cur:
            cur.execute("DELETE FROM ping_logs")
