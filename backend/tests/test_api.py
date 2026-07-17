"""
后端测试 - pytest + httpx

覆盖 5 大 API + 方案库 CRUD
"""
import pytest
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    # FastAPI TestClient 默认不触发 lifespan，必须用 with 才会调用 init_db
    with TestClient(app) as c:
        yield c


def test_root(client):
    """根路径"""
    r = client.get("/")
    assert r.status_code == 200
    data = r.json()
    assert data["name"] == "EVOLUTION AI"
    assert data["version"] == "0.1.0"
    assert "docs" in data


def test_health(client):
    """健康检查"""
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_car_default_params(client):
    """默认参数"""
    r = client.get("/api/v1/car/params/default")
    assert r.status_code == 200
    data = r.json()
    assert data["L"] == 4.7
    assert data["W"] == 1.85
    assert data["H"] == 1.45


def test_car_validate_ok(client):
    """参数校验 - 合法"""
    r = client.post("/api/v1/car/validate", json={
        "params": {"L": 4.7, "W": 1.85, "H": 1.45, "wheelbase": 2.8}
    })
    assert r.status_code == 200
    assert r.json()["valid"] is True


def test_car_validate_pydantic_fail(client):
    """参数校验 - 越界（Pydantic Field 拦截）"""
    r = client.post("/api/v1/car/validate", json={
        "params": {"L": 10.0}  # 超过 max=5.5
    })
    assert r.status_code == 422  # Pydantic 自动拦截


def test_car_build(client):
    """整车构建"""
    r = client.post("/api/v1/car/build", json={})
    assert r.status_code == 200
    data = r.json()
    assert "glb_url" in data
    assert data["glb_url"].startswith("/static/cars/")
    assert "stats" in data
    assert data["stats"]["total_vertices"] > 0
    assert data["stats"]["total_faces"] > 0
    assert "components" in data["stats"]
    assert data["build_time_ms"] > 0


def test_car_presets(client):
    """预设方案"""
    r = client.get("/api/v1/car/presets")
    assert r.status_code == 200
    data = r.json()
    assert "sport" in data
    assert "luxury" in data
    assert "suv" in data


def test_quality_assess_preset(client):
    """评估球面"""
    r = client.post("/api/v1/quality/assess-preset", json={"shape": "sphere", "resolution": 20})
    assert r.status_code == 200
    data = r.json()
    assert data["panel_name"] == "sphere"
    assert data["grade"] in ("A", "B", "C", "D")
    assert "g2_ratio" in data
    assert "reflection_score" in data


def test_quality_assess_invalid_shape(client):
    """评估 - 非法 shape"""
    r = client.post("/api/v1/quality/assess-preset", json={"shape": "invalid"})
    assert r.status_code == 422


def test_optimize_preset_sphere(client):
    """优化球面（80 步）"""
    r = client.post("/api/v1/optimize/run-preset", json={"shape": "sphere", "max_iter": 30})
    assert r.status_code == 200
    data = r.json()
    assert data["panel_name"] == "sphere"
    assert "task_id" in data
    assert "convergence_curve" in data
    assert data["iterations"] > 0


def test_storyboard_templates(client):
    """分镜模板列表"""
    r = client.get("/api/v1/storyboard/templates")
    assert r.status_code == 200
    data = r.json()
    assert len(data) == 3
    names = {t["name"] for t in data}
    assert "car_promotion" in names


def test_storyboard_generate(client):
    """生成分镜"""
    r = client.post("/api/v1/storyboard/generate", json={
        "product_name": "测试智能汽车",
        "duration": 90,
        "style": "科技感",
        "template": "car_promotion",
    })
    assert r.status_code == 200
    data = r.json()
    assert data["scene_count"] > 0
    assert len(data["markdown"]) > 100
    assert len(data["html"]) > 500
    assert data["template"] == "car_promotion"


def test_project_crud(client):
    """方案库 CRUD"""
    # Create
    r = client.post("/api/v1/project", json={
        "name": "测试方案",
        "description": "用于 pytest",
        "params": {"L": 4.8, "W": 1.9},
        "tags": ["test", "mvp"],
    })
    assert r.status_code == 201
    project = r.json()
    pid = project["id"]
    assert project["name"] == "测试方案"

    # List
    r = client.get("/api/v1/project/list")
    assert r.status_code == 200
    data = r.json()
    items = data.get("items", data) if isinstance(data, dict) else data
    assert any(p["id"] == pid for p in items)

    # Get
    r = client.get(f"/api/v1/project/{pid}")
    assert r.status_code == 200

    # Update
    r = client.patch(f"/api/v1/project/{pid}", json={"name": "改名"})
    assert r.status_code == 200
    assert r.json()["name"] == "改名"

    # Delete
    r = client.delete(f"/api/v1/project/{pid}")
    assert r.status_code == 204

    # 404
    r = client.get(f"/api/v1/project/{pid}")
    assert r.status_code == 404


def test_export_glb(client):
    """导出 GLB"""
    r = client.get("/api/v1/export/glb")
    assert r.status_code == 200
    assert r.headers["content-type"] == "model/gltf-binary"
    assert len(r.content) > 1000  # GLB 至少 1KB


def test_export_invalid_format(client):
    """导出非法格式"""
    r = client.get("/api/v1/export/xyz")
    assert r.status_code == 400
