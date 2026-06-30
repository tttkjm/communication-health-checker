"""シングルインスタンス制御用のヘルパ。

起動中インスタンスの情報を `~/.communication_health_checker/instance.json` に記録し、
再起動時にヘルスチェックで既存サーバの生存を確認する。
"""

import json
import os
import urllib.request
from pathlib import Path

_INSTANCE_FILE = Path.home() / ".communication_health_checker" / "instance.json"


def write_instance(host: str, port: int) -> None:
    try:
        _INSTANCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        _INSTANCE_FILE.write_text(
            json.dumps({"host": host, "port": port, "pid": os.getpid()}),
            encoding="utf-8",
        )
    except OSError:
        pass


def read_instance() -> dict | None:
    try:
        return json.loads(_INSTANCE_FILE.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def clear_instance() -> None:
    try:
        _INSTANCE_FILE.unlink(missing_ok=True)
    except OSError:
        pass


def is_communication_health_checker_alive(host: str, port: int, timeout: float = 1.0) -> bool:
    """指定 host:port で communication_health_checker サーバが応答するか確認する。

    社内プロキシ環境でも localhost へ確実に到達するためプロキシを無効化する。
    """
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    url = f"http://{host}:{port}/api/v1/system/health"
    try:
        with opener.open(url, timeout=timeout) as resp:
            data = json.loads(resp.read().decode())
            return isinstance(data, dict) and data.get("app") == "communication_health_checker"
    except Exception:
        return False


def existing_instance_url(host: str, preferred_port: int) -> str | None:
    """既に起動中の communication_health_checker があればその URL を返す（なければ None）。

    記録ファイルのポートと、既定ポートの両方を確認する。
    """
    candidates: list[tuple[str, int]] = []
    info = read_instance()
    if info and "host" in info and "port" in info:
        candidates.append((str(info["host"]), int(info["port"])))
    if (host, preferred_port) not in candidates:
        candidates.append((host, preferred_port))

    for h, p in candidates:
        if is_communication_health_checker_alive(h, p):
            return f"http://{h}:{p}/"
    return None
