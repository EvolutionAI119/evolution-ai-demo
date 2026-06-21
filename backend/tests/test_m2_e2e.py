"""M2 端到端测试。

验证验收标准："保存方案 → 异步优化 → 完成后查询结果"。

策略：
- Celery 走 eager 模式（同步执行，不真起 worker）
- 用独立 in-memory DB，避免污染主 DB
"""
import uuid

import pytest
from fastapi.testclient import TestClient


@pytest.fixture(autouse=True)
def celery_eager(monkeypatch):
    """所有测试默认走 Celery eager 模式（同步执行任务）。"""
    monkeypatch.setenv("EVOLUTION_DATABASE_URL", "sqlite:///:memory:")
    from backend.config import settings
    settings.database_url = "sqlite:///:memory:"  # 覆盖默认值
    from backend.db.session import reload_engine
    reload_engine()
    from backend.tasks import celery_app
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True
    yield


@pytest.fixture
def client():
    from backend.main import app
    from backend.db import init_db
    init_db()  # 显式初始化（in-memory 不会跨请求）
    with TestClient(app) as c:
        yield c


def _create_project(client) -> int:
    r = client.post("/api/v1/project", json={
        "name": f"测试方案-{uuid.uuid4().hex[:6]}",
        "description": "M2 E2E",
        "params": {"L": 4.7, "W": 1.85, "H": 1.45, "wheelbase": 2.8},
        "tags": ["m2", "e2e"],
        "preset": "luxury",
    })
    assert r.status_code == 201, r.text
    return r.json()["id"]


def test_e2e_save_optimize_poll(client):
    """端到端：保存方案 → 异步优化 → 轮询结果。"""
    project_id = _create_project(client)

    # 2. 启动异步优化（关联 project_id）
    r = client.post("/api/v1/optimize/start", json={
        "panel_name": "测试面板",
        "surface_type": "sphere",
        "max_iter": 30,  # 测试用，减少耗时
        "project_id": project_id,
    })
    assert r.status_code == 202, r.text
    data = r.json()
    task_id = data["task_id"]
    assert data["status"] in ("PENDING", "STARTED", "PROGRESS", "SUCCESS")
    assert data["status_url"] == f"/api/v1/task/{task_id}"

    # 3. 轮询任务状态（eager 模式：第一次就 SUCCESS）
    r = client.get(f"/api/v1/task/{task_id}")
    assert r.status_code == 200, r.text
    final = r.json()
    assert final["task_id"] == task_id
    assert final["status"] == "SUCCESS", f"任务未成功: {final}"
    assert final["progress"] == 1.0
    assert final["current_iter"] == 30
    assert "result" in final
    result = final["result"]
    assert result["initial_grade"] in ("A", "B", "C", "D")
    assert result["final_grade"] in ("A", "B", "C", "D")
    assert "elapsed_sec" in result
    assert result["iterations"] == 30
    print(f"✅ 优化完成: {result['initial_grade']} → {result['final_grade']}, 耗时 {result['elapsed_sec']:.2f}s")

    # 4. 查方案关联的任务
    r = client.get(f"/api/v1/task/by-project/{project_id}")
    assert r.status_code == 200
    items = r.json()["items"]
    assert any(t["task_id"] == task_id for t in items)


def test_optimize_preset_async(client):
    """预设曲面异步优化。"""
    project_id = _create_project(client)

    r = client.post("/api/v1/optimize/start-preset", json={
        "shape": "plane_with_noise",
        "max_iter": 30,
        "project_id": project_id,
    })
    assert r.status_code == 202, r.text
    task_id = r.json()["task_id"]

    r = client.get(f"/api/v1/task/{task_id}")
    assert r.status_code == 200
    assert r.json()["status"] == "SUCCESS"


def test_task_not_found(client):
    """任务不存在 404。"""
    r = client.get("/api/v1/task/nonexistent_task_id_xxxxx")
    assert r.status_code == 404


def test_project_persists_across_requests(client):
    """方案持久化：创建后能查回（ORM 验证）。"""
    pid = _create_project(client)
    r = client.get(f"/api/v1/project/{pid}")
    assert r.status_code == 200
    data = r.json()
    assert data["id"] == pid
    assert data["preset"] == "luxury"
    assert "m2" in data["tags"]
    assert data["params"]["L"] == 4.7
