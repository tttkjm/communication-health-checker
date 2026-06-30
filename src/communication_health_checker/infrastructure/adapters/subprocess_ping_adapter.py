import platform
import re
import subprocess

from communication_health_checker.domain.models.ping.ping_probe import PingProbe
from communication_health_checker.domain.ports.ping_port import PingPort

# ロケール非依存: "TTL=" と "<n>ms" は日本語/英語 Windows 双方で ASCII 表記される。
_TTL_RE = re.compile(r"TTL=(\d+)", re.IGNORECASE)
_RTT_RE = re.compile(r"[<=]\s*([\d.]+)\s*ms", re.IGNORECASE)

_IS_WINDOWS = platform.system().lower().startswith("win")


def build_ping_command(host: str, count: int, timeout_ms: int) -> list[str]:
    """プラットフォーム別の ping コマンドを構築する。"""
    if _IS_WINDOWS:
        return ["ping", "-n", str(count), "-w", str(timeout_ms), host]
    # Linux/macOS: -c 回数, -W は秒（macOS は -W がミリ秒だが概ね許容）
    timeout_sec = max(1, round(timeout_ms / 1000))
    return ["ping", "-c", str(count), "-W", str(timeout_sec), host]


def parse_ping_output(stdout: str, count: int) -> list[PingProbe]:
    """ping の標準出力から count 回分の PingProbe を構築する。

    成功判定: 応答行（"TTL=" を含む行）を成功とみなし、出現順に seq を割り当てる。
    不足分（タイムアウト/到達不可）は失敗 probe で埋める。
    """
    replies: list[tuple[float | None, int | None]] = []
    for line in stdout.splitlines():
        if "TTL=" not in line.upper():
            continue
        ttl_m = _TTL_RE.search(line)
        rtt_m = _RTT_RE.search(line)
        rtt = float(rtt_m.group(1)) if rtt_m else None
        ttl = int(ttl_m.group(1)) if ttl_m else None
        replies.append((rtt, ttl))

    probes: list[PingProbe] = []
    for i in range(count):
        if i < len(replies):
            rtt, ttl = replies[i]
            probes.append(PingProbe(seq=i + 1, success=True, rtt_ms=rtt, ttl=ttl, error=None))
        else:
            probes.append(PingProbe(seq=i + 1, success=False, rtt_ms=None, ttl=None, error="timeout"))
    return probes


def _decode(raw: bytes) -> str:
    for enc in ("utf-8", "cp932", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("utf-8", errors="replace")


class SubprocessPingAdapter(PingPort):
    """OS の ping コマンドを subprocess 実行する PingPort 実装（管理者権限不要）。"""

    def ping_once(self, host: str, count: int, timeout_ms: int) -> list[PingProbe]:
        cmd = build_ping_command(host, count, timeout_ms)
        # コマンド全体のタイムアウト: 各回の待ち時間合計 + 余裕
        overall_timeout = (timeout_ms / 1000) * count + 5
        try:
            completed = subprocess.run(  # noqa: S603 (固定コマンド + 検証済みホスト)
                cmd,
                capture_output=True,
                timeout=overall_timeout,
            )
            stdout = _decode(completed.stdout)
            return parse_ping_output(stdout, count)
        except subprocess.TimeoutExpired:
            return [PingProbe(seq=i + 1, success=False, rtt_ms=None, ttl=None, error="timeout") for i in range(count)]
        except (OSError, ValueError) as exc:
            return [PingProbe(seq=i + 1, success=False, rtt_ms=None, ttl=None, error=str(exc)) for i in range(count)]
