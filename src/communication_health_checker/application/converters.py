"""ドメインモデル → DTO への変換ヘルパ（application 層に閉じる）。"""

from communication_health_checker.application.dto.ping_dto import PingLogResponse
from communication_health_checker.application.dto.target_dto import TargetResponse
from communication_health_checker.domain.models.ping.ping_log import PingLog
from communication_health_checker.domain.models.target.target import Target

__all__ = ["target_to_response", "ping_log_to_response"]


def target_to_response(target: Target) -> TargetResponse:
    return TargetResponse(
        id=str(target.target_id),
        name=target.name,
        host=str(target.host),
        description=target.description,
        created_at=target.created_at.isoformat(),
        updated_at=target.updated_at.isoformat(),
    )


def ping_log_to_response(log: PingLog) -> PingLogResponse:
    return PingLogResponse(
        target_id=str(log.target_id),
        seq=log.seq,
        sent_at=log.sent_at.isoformat(),
        success=log.success,
        rtt_ms=log.rtt_ms,
        ttl=log.ttl,
        error=log.error,
    )
