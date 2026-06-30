from pydantic import Field

from communication_health_checker.domain.models.core import ValueObject


class PingProbe(ValueObject):
    """1 回分の ping 応答結果を表す値オブジェクト。"""

    seq: int = Field(..., ge=1, description="シーケンス番号（1 始まり）")
    success: bool = Field(..., description="応答が得られたか")
    rtt_ms: float | None = Field(default=None, ge=0, description="往復遅延 (ms)")
    ttl: int | None = Field(default=None, ge=0, description="TTL")
    error: str | None = Field(default=None, description="失敗理由")
