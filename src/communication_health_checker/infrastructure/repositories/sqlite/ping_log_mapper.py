import sqlite3
from datetime import datetime

from communication_health_checker.domain.models.ping.ping_log import PingLog
from communication_health_checker.domain.models.target.target_id import TargetId


def row_to_ping_log(row: sqlite3.Row) -> PingLog:
    return PingLog(
        target_id=TargetId(value=row["target_id"]),
        seq=row["seq"],
        sent_at=datetime.fromisoformat(row["sent_at"]),
        success=bool(row["success"]),
        rtt_ms=row["rtt_ms"],
        ttl=row["ttl"],
        error=row["error"],
    )


def ping_log_to_params(log: PingLog) -> tuple:
    return (
        str(log.target_id),
        log.seq,
        log.sent_at.isoformat(),
        1 if log.success else 0,
        log.rtt_ms,
        log.ttl,
        log.error,
    )
