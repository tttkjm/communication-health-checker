from datetime import UTC, datetime

from communication_health_checker.domain.ports.clock_port import ClockPort


class SystemClock(ClockPort):
    """システム時計（UTC）。"""

    def now(self) -> datetime:
        return datetime.now(UTC)
