from pydantic import BaseModel, Field


class PingRunRequest(BaseModel):
    """PingTargetsUseCase への内部入力。target_ids が空/未指定なら全ターゲット。

    1 サイクル（= 1 回の送信）あたりの実行単位。count は通常 1。
    """

    target_ids: list[str] | None = Field(default=None, description="対象ターゲットID（未指定=全件）")
    count: int = Field(default=1, ge=1, le=100, description="1 サイクルあたりの送信回数")
    timeout_ms: int = Field(default=1000, ge=100, le=60000, description="応答待ちタイムアウト (ms)")


class OneShotRequest(BaseModel):
    """ワンショット実行リクエスト（パラメータなし・1 回だけ送信）。"""

    target_ids: list[str] | None = Field(default=None, description="対象ターゲットID（未指定=全件）")
    timeout_ms: int = Field(default=1000, ge=100, le=60000, description="応答待ちタイムアウト (ms)")


class PeriodicStartRequest(BaseModel):
    """定期実行リクエスト（周期のみ設定・周期ごとに 1 回送信・停止まで継続）。"""

    target_ids: list[str] | None = Field(default=None, description="対象ターゲットID（未指定=全件）")
    interval_sec: float = Field(default=5.0, ge=1.0, le=3600.0, description="送信周期 (秒)")
    timeout_ms: int = Field(default=1000, ge=100, le=60000, description="応答待ちタイムアウト (ms)")


class RepeatStartRequest(BaseModel):
    """複数回実行リクエスト（回数のみ設定・1 秒ごとに送信・指定回数で終了）。"""

    target_ids: list[str] | None = Field(default=None, description="対象ターゲットID（未指定=全件）")
    count: int = Field(default=4, ge=1, le=1000, description="送信回数（1 秒間隔）")
    timeout_ms: int = Field(default=1000, ge=100, le=60000, description="応答待ちタイムアウト (ms)")


class ProbeResult(BaseModel):
    """1 回分の ping 結果。"""

    seq: int = Field(..., description="シーケンス番号")
    success: bool = Field(..., description="応答が得られたか")
    rtt_ms: float | None = Field(default=None, description="往復遅延 (ms)")
    ttl: int | None = Field(default=None, description="TTL")
    error: str | None = Field(default=None, description="失敗理由")


class PingResultResponse(BaseModel):
    """1 ターゲット・1 サイクル分の集計結果。"""

    target_id: str = Field(..., description="ターゲットID")
    name: str = Field(..., description="表示名")
    host: str = Field(..., description="ホスト")
    sent_at: str = Field(..., description="サイクル送信時刻 (ISO8601)")
    packets_sent: int = Field(..., description="送信パケット数")
    packets_received: int = Field(..., description="受信パケット数")
    packets_lost: int = Field(..., description="ロストパケット数")
    loss_pct: float = Field(..., description="パケットロス率 (%)")
    rtt_min_ms: float | None = Field(default=None, description="最小 RTT")
    rtt_avg_ms: float | None = Field(default=None, description="平均 RTT")
    rtt_max_ms: float | None = Field(default=None, description="最大 RTT")
    success: bool = Field(..., description="1 回以上応答があったか")
    probes: list[ProbeResult] = Field(default_factory=list, description="各回の結果")


class PingLogResponse(BaseModel):
    """ターゲット毎ログの 1 レコード。"""

    target_id: str = Field(..., description="ターゲットID")
    seq: int = Field(..., description="シーケンス番号")
    sent_at: str = Field(..., description="送信時刻 (ISO8601)")
    success: bool = Field(..., description="応答が得られたか")
    rtt_ms: float | None = Field(default=None, description="往復遅延 (ms)")
    ttl: int | None = Field(default=None, description="TTL")
    error: str | None = Field(default=None, description="失敗理由")


class ScheduleStatusResponse(BaseModel):
    """スケジュール実行（定期 / 複数回）の状態。"""

    running: bool = Field(..., description="稼働中か")
    mode: str | None = Field(default=None, description="実行モード: periodic | repeat")
    interval_sec: float | None = Field(default=None, description="送信周期 (秒)")
    target_ids: list[str] | None = Field(default=None, description="対象ターゲットID")
    total_count: int | None = Field(default=None, description="複数回モードの総回数（定期は null）")
    completed_cycles: int = Field(default=0, description="送信済みサイクル数")
