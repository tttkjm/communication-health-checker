from datetime import datetime

from pydantic import Field

from communication_health_checker.domain.models.core import ValueObject
from communication_health_checker.domain.models.target.target_id import TargetId


class PingLog(ValueObject):
    """ターゲット毎に蓄積される ping ログの 1 レコード（不変）。"""

    target_id: TargetId = Field(..., description="対象ターゲットID")
    seq: int = Field(..., ge=1, description="シーケンス番号")
    sent_at: datetime = Field(..., description="送信時刻")
    success: bool = Field(..., description="応答が得られたか")
    rtt_ms: float | None = Field(default=None, ge=0, description="往復遅延 (ms)")
    ttl: int | None = Field(default=None, ge=0, description="TTL")
    error: str | None = Field(default=None, description="失敗理由")
