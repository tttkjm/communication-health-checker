"""ping 出力パーサの単体テスト（最重要・ロケール非依存性の検証）。"""

from communication_health_checker.infrastructure.adapters.subprocess_ping_adapter import (
    build_ping_command,
    parse_ping_output,
)

# 英語 Windows の出力サンプル（4 回中 4 回成功）
EN_SUCCESS = """
Pinging 8.8.8.8 with 32 bytes of data:
Reply from 8.8.8.8: bytes=32 time=12ms TTL=117
Reply from 8.8.8.8: bytes=32 time=11ms TTL=117
Reply from 8.8.8.8: bytes=32 time<1ms TTL=117
Reply from 8.8.8.8: bytes=32 time=13ms TTL=117

Ping statistics for 8.8.8.8:
    Packets: Sent = 4, Received = 4, Lost = 0 (0% loss),
"""

# 日本語 Windows の出力サンプル（4 回中 2 回成功・2 回タイムアウト）
JP_PARTIAL = """
192.168.0.1 に ping を送信しています 32 バイトのデータ:
192.168.0.1 からの応答: バイト数 =32 時間 =1ms TTL=64
192.168.0.1 からの応答: バイト数 =32 時間 <1ms TTL=64
要求がタイムアウトしました。
要求がタイムアウトしました。

192.168.0.1 の ping 統計:
    パケット数: 送信 = 4、受信 = 2、損失 = 2 (50% の損失)、
"""

# 全失敗（到達不可）
ALL_FAIL = """
Pinging 10.255.255.1 with 32 bytes of data:
Request timed out.
Request timed out.
"""


def test_parse_english_all_success() -> None:
    probes = parse_ping_output(EN_SUCCESS, 4)
    assert len(probes) == 4
    assert all(p.success for p in probes)
    assert all(p.ttl == 117 for p in probes)
    assert probes[0].rtt_ms == 12.0
    assert probes[2].rtt_ms == 1.0  # time<1ms -> 1.0


def test_parse_japanese_partial() -> None:
    probes = parse_ping_output(JP_PARTIAL, 4)
    assert len(probes) == 4
    assert [p.success for p in probes] == [True, True, False, False]
    assert probes[0].ttl == 64
    assert probes[0].rtt_ms == 1.0
    assert probes[3].error == "timeout"


def test_parse_all_fail() -> None:
    probes = parse_ping_output(ALL_FAIL, 2)
    assert len(probes) == 2
    assert not any(p.success for p in probes)


def test_count_padding_when_fewer_replies() -> None:
    # 応答が count より少ない場合は失敗で埋める
    probes = parse_ping_output(EN_SUCCESS, 6)
    assert len(probes) == 6
    assert sum(p.success for p in probes) == 4
    assert all(not p.success for p in probes[4:])


def test_build_ping_command_contains_host_and_count() -> None:
    cmd = build_ping_command("192.168.0.1", 4, 1000)
    assert "192.168.0.1" in cmd
    assert "4" in cmd
