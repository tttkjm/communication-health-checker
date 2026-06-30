from concurrent.futures import ThreadPoolExecutor

from communication_health_checker.application.dto.ping_dto import PingResultResponse, PingRunRequest, ProbeResult
from communication_health_checker.domain.models.ping.ping_log import PingLog
from communication_health_checker.domain.models.ping.ping_probe import PingProbe
from communication_health_checker.domain.models.target.target import Target
from communication_health_checker.domain.models.target.target_id import TargetId
from communication_health_checker.domain.ports.clock_port import ClockPort
from communication_health_checker.domain.ports.ping_port import PingPort
from communication_health_checker.domain.repositories.i_ping_log_repository import IPingLogRepository
from communication_health_checker.domain.repositories.i_target_repository import ITargetRepository

_MAX_PARALLEL = 32


class PingTargetsUseCase:
    """複数ターゲットへ並列に ping を実行し、ログを保存して結果を返す。"""

    def __init__(
        self,
        target_repository: ITargetRepository,
        ping_log_repository: IPingLogRepository,
        ping_port: PingPort,
        clock: ClockPort,
    ) -> None:
        self._target_repository = target_repository
        self._ping_log_repository = ping_log_repository
        self._ping_port = ping_port
        self._clock = clock

    def execute(self, request: PingRunRequest) -> list[PingResultResponse]:
        targets = self._resolve_targets(request.target_ids)
        if not targets:
            return []

        sent_at = self._clock.now()
        workers = min(_MAX_PARALLEL, len(targets))
        with ThreadPoolExecutor(max_workers=workers) as pool:
            probe_lists = list(
                pool.map(
                    lambda t: self._ping_port.ping_once(str(t.host), request.count, request.timeout_ms),
                    targets,
                )
            )

        results: list[PingResultResponse] = []
        for target, probes in zip(targets, probe_lists, strict=True):
            self._persist(target.target_id, sent_at, probes)
            results.append(self._build_response(target, sent_at, probes))
        return results

    def _resolve_targets(self, target_ids: list[str] | None) -> list[Target]:
        if not target_ids:
            return self._target_repository.find_all()
        resolved: list[Target] = []
        for tid in target_ids:
            target = self._target_repository.find_by_id(TargetId(value=tid))
            if target is not None:
                resolved.append(target)
        return resolved

    def _persist(self, target_id: TargetId, sent_at, probes: list[PingProbe]) -> None:
        logs = [
            PingLog(
                target_id=target_id,
                seq=p.seq,
                sent_at=sent_at,
                success=p.success,
                rtt_ms=p.rtt_ms,
                ttl=p.ttl,
                error=p.error,
            )
            for p in probes
        ]
        self._ping_log_repository.append_many(logs)

    def _build_response(self, target: Target, sent_at, probes: list[PingProbe]) -> PingResultResponse:
        sent = len(probes)
        received = sum(1 for p in probes if p.success)
        lost = sent - received
        rtts = [p.rtt_ms for p in probes if p.success and p.rtt_ms is not None]
        return PingResultResponse(
            target_id=str(target.target_id),
            name=target.name,
            host=str(target.host),
            sent_at=sent_at.isoformat(),
            packets_sent=sent,
            packets_received=received,
            packets_lost=lost,
            loss_pct=round((lost / sent) * 100, 1) if sent else 0.0,
            rtt_min_ms=min(rtts) if rtts else None,
            rtt_avg_ms=round(sum(rtts) / len(rtts), 3) if rtts else None,
            rtt_max_ms=max(rtts) if rtts else None,
            success=received > 0,
            probes=[
                ProbeResult(seq=p.seq, success=p.success, rtt_ms=p.rtt_ms, ttl=p.ttl, error=p.error) for p in probes
            ],
        )
