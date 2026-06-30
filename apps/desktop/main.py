import io
import os
import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path


def _ensure_std_streams() -> None:
    """標準ストリームを安全化する。

    - windowed ビルド（--noconsole）では sys.stdout/stderr が None になり、
      uvicorn のログ formatter が None.isatty() を呼んでクラッシュする。
      None の場合はログファイル（無ければ破棄ストリーム）へ向ける。
    - 既存ストリームが cp932 等の場合、非 ASCII 出力で UnicodeEncodeError に
      なるため errors="replace" の UTF-8 に再設定する。
    """
    if sys.stdout is None or sys.stderr is None:
        try:
            log_path = Path.home() / ".communication_health_checker" / "communication_health_checker.log"
            log_path.parent.mkdir(parents=True, exist_ok=True)
            stream: object = open(log_path, "a", buffering=1, encoding="utf-8")  # noqa: SIM115
        except OSError:
            stream = io.StringIO()
        if sys.stdout is None:
            sys.stdout = stream  # type: ignore[assignment]
        if sys.stderr is None:
            sys.stderr = stream  # type: ignore[assignment]

    for stream_obj in (sys.stdout, sys.stderr):
        reconfigure = getattr(stream_obj, "reconfigure", None)
        if reconfigure is not None:
            try:
                reconfigure(encoding="utf-8", errors="replace")
            except (OSError, ValueError):
                pass


def _configure_db_path() -> None:
    """書き込み用 SQLite をユーザー領域に置く（_MEIPASS は読取専用のため）。"""
    if os.getenv("SQLITE_DB_PATH"):
        return
    db_path = Path.home() / ".communication_health_checker" / "communication_health_checker.db"
    db_path.parent.mkdir(parents=True, exist_ok=True)
    os.environ["SQLITE_DB_PATH"] = str(db_path)


def _find_free_port(preferred: int = 8765) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        try:
            s.bind(("127.0.0.1", preferred))
            return preferred
        except OSError:
            s.bind(("127.0.0.1", 0))
            return s.getsockname()[1]


def _open_browser_when_ready(host: str, port: int) -> None:
    url = f"http://{host}:{port}/"
    for _ in range(50):  # 最大 ~5 秒待機
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex((host, port)) == 0:
                webbrowser.open(url)
                return
        time.sleep(0.1)
    webbrowser.open(url)


def main() -> None:
    _ensure_std_streams()

    import uvicorn

    from apps.desktop import instance
    from apps.desktop.app import create_app

    _configure_db_path()
    host = os.getenv("COMMUNICATION_HEALTH_CHECKER_HOST", "127.0.0.1")
    preferred = int(os.getenv("COMMUNICATION_HEALTH_CHECKER_PORT", "8765"))
    no_browser = os.getenv("COMMUNICATION_HEALTH_CHECKER_NO_BROWSER") == "1"

    # --- シングルインスタンス: 既に起動中なら新規サーバを立てずブラウザだけ開く ---
    if os.getenv("COMMUNICATION_HEALTH_CHECKER_FORCE_NEW") != "1":
        existing = instance.existing_instance_url(host, preferred)
        if existing is not None:
            print(f"communication_health_checker is already running at {existing} - opening browser only.")
            if not no_browser:
                webbrowser.open(existing)
            return

    port = _find_free_port(preferred)

    app = create_app()

    # GUI からの終了 API（/api/v1/system/shutdown）で should_exit を立てられるよう、
    # Server インスタンスを app.state に束ねる。
    config = uvicorn.Config(app, host=host, port=port, log_level="info")
    server = uvicorn.Server(config)
    app.state.server = server

    if not no_browser:
        threading.Thread(target=_open_browser_when_ready, args=(host, port), daemon=True).start()

    instance.write_instance(host, port)
    try:
        server.run()
    except KeyboardInterrupt:
        # Ctrl+C。uvicorn は graceful shutdown 後に KeyboardInterrupt を
        # 再送出するため、ここで握りつぶして Traceback を出さずに終了する。
        pass
    finally:
        instance.clear_instance()


if __name__ == "__main__":
    main()
