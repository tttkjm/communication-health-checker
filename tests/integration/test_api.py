import time

import pytest
from apps.desktop.app import create_app
from fastapi.testclient import TestClient


@pytest.fixture
def client():
    app = create_app()
    with TestClient(app) as c:
        yield c


def test_target_crud_flow(client):
    # 作成
    r = client.post("/api/v1/targets", json={"name": "R1", "host": "127.0.0.1", "description": "lo"})
    assert r.status_code == 201
    tid = r.json()["id"]

    # 一覧 / 取得
    assert len(client.get("/api/v1/targets").json()) == 1
    assert client.get(f"/api/v1/targets/{tid}").json()["name"] == "R1"

    # 更新
    r = client.put(f"/api/v1/targets/{tid}", json={"name": "R2", "host": "10.0.0.1", "description": ""})
    assert r.status_code == 200
    assert r.json()["host"] == "10.0.0.1"

    # 削除
    assert client.delete(f"/api/v1/targets/{tid}").status_code == 204
    assert client.get("/api/v1/targets").json() == []


def test_create_invalid_host_returns_422_or_400(client):
    r = client.post("/api/v1/targets", json={"name": "bad", "host": "not a host"})
    assert r.status_code in (400, 422)


def test_get_missing_target_returns_404(client):
    r = client.get("/api/v1/targets/tgt_00000000000000000000000000000000")
    assert r.status_code == 404


def test_delete_all(client):
    client.post("/api/v1/targets", json={"name": "A", "host": "127.0.0.1"})
    client.post("/api/v1/targets", json={"name": "B", "host": "127.0.0.2"})
    assert client.delete("/api/v1/targets").status_code == 204
    assert client.get("/api/v1/targets").json() == []


def test_schedule_status_default_stopped(client):
    assert client.get("/api/v1/ping/schedule/status").json()["running"] is False


def test_spa_fallback_serves_index(client):
    # 任意のフロントルートは index.html（200）を返す
    r = client.get("/some/spa/route")
    assert r.status_code == 200
    assert "<!doctype html>" in r.text.lower() or "<html" in r.text.lower()


def test_unknown_api_returns_404_not_index(client):
    r = client.get("/api/v1/does-not-exist")
    assert r.status_code == 404


def test_websocket_sends_initial_status(client):
    with client.websocket_connect("/ws/ping") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "schedule_status"
        assert msg["running"] is False


def test_health_endpoint(client):
    r = client.get("/api/v1/system/health")
    assert r.status_code == 200
    assert r.json() == {"app": "communication_health_checker", "status": "ok"}


def test_shutdown_endpoint_without_bound_server(client):
    # TestClient ではサーバ未束縛のため shutting_down=False を返す（クラッシュしない）
    r = client.post("/api/v1/system/shutdown")
    assert r.status_code == 200
    assert r.json()["shutting_down"] is False


def test_periodic_start_then_stop(client):
    tid = client.post("/api/v1/targets", json={"name": "lo", "host": "127.0.0.1"}).json()["id"]
    started = client.post("/api/v1/ping/schedule/periodic", json={"target_ids": [tid], "interval_sec": 1}).json()
    assert started["running"] is True
    assert started["mode"] == "periodic"
    stopped = client.post("/api/v1/ping/schedule/stop").json()
    assert stopped["running"] is False


@pytest.mark.slow
def test_oneshot_sends_once_against_loopback(client):
    tid = client.post("/api/v1/targets", json={"name": "lo", "host": "127.0.0.1"}).json()["id"]
    r = client.post("/api/v1/ping/run", json={"target_ids": [tid]})
    assert r.status_code == 200
    result = r.json()[0]
    assert result["packets_sent"] == 1  # ワンショット = 1 回だけ
    logs = client.get(f"/api/v1/ping/logs/{tid}").json()
    assert len(logs) == 1


@pytest.mark.slow
def test_repeat_auto_stops_after_count(client):
    tid = client.post("/api/v1/targets", json={"name": "lo", "host": "127.0.0.1"}).json()["id"]
    started = client.post("/api/v1/ping/schedule/repeat", json={"target_ids": [tid], "count": 3}).json()
    assert started["running"] is True
    assert started["mode"] == "repeat"
    assert started["total_count"] == 3
    # 1 秒間隔 × 3 回 ≒ 3 秒で自動終了する
    deadline = time.time() + 15
    while time.time() < deadline:
        if client.get("/api/v1/ping/schedule/status").json()["running"] is False:
            break
        time.sleep(0.2)
    assert client.get("/api/v1/ping/schedule/status").json()["running"] is False
    # 3 回ぶんのログが残る
    logs = client.get(f"/api/v1/ping/logs/{tid}").json()
    assert len(logs) == 3
