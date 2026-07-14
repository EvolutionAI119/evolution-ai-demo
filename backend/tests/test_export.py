"""
W4-D2: 模型导出测试（GLB / OBJ / STL）
"""
import pytest
import os
from fastapi.testclient import TestClient

from backend.main import app


@pytest.fixture
def client():
    with TestClient(app) as c:
        yield c


class TestExportGLB:
    """GLB 导出"""

    def test_export_glb_default(self, client):
        """默认参数导出 GLB"""
        r = client.post("/api/v1/car/export", json={"format": "glb"})
        assert r.status_code == 200
        data = r.json()
        assert data["format"] == "glb"
        assert data["file_url"].startswith("/static/exports/")
        assert data["file_url"].endswith(".glb")
        assert data["file_size_bytes"] > 0
        assert data["build_time_ms"] > 0

    def test_export_glb_with_params(self, client):
        """自定义参数导出 GLB"""
        r = client.post("/api/v1/car/export", json={
            "params": {"L": 5.0, "W": 1.9, "H": 1.5},
            "format": "glb",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["format"] == "glb"
        assert data["file_size_bytes"] > 1000  # GLB 至少 1KB


class TestExportOBJ:
    """OBJ 导出"""

    def test_export_obj_default(self, client):
        """默认参数导出 OBJ"""
        r = client.post("/api/v1/car/export", json={"format": "obj"})
        assert r.status_code == 200
        data = r.json()
        assert data["format"] == "obj"
        assert data["file_size_bytes"] > 0
        # OBJ 可能是 .obj 或 .obj.zip
        assert ".obj" in data["file_url"]

    def test_export_obj_with_freeform(self, client):
        """带自由变形导出 OBJ"""
        r = client.post("/api/v1/car/export", json={
            "format": "obj",
            "freeform": {
                "preset": "fender_bulge",
                "amplitude": 0.05,
                "center_x": 0.3,
                "center_z": 0.5,
            },
        })
        assert r.status_code == 200
        data = r.json()
        assert data["format"] == "obj"
        assert data["file_size_bytes"] > 0


class TestExportSTL:
    """STL 导出"""

    def test_export_stl_default(self, client):
        """默认参数导出 STL"""
        r = client.post("/api/v1/car/export", json={"format": "stl"})
        assert r.status_code == 200
        data = r.json()
        assert data["format"] == "stl"
        assert data["file_url"].endswith(".stl")
        assert data["file_size_bytes"] > 0

    def test_export_stl_with_params(self, client):
        """SUV 参数导出 STL"""
        r = client.post("/api/v1/car/export", json={
            "params": {"L": 4.8, "H": 1.72, "ground_clearance": 0.22},
            "format": "stl",
        })
        assert r.status_code == 200
        data = r.json()
        assert data["format"] == "stl"
        assert data["file_size_bytes"] > 1000


class TestExportValidation:
    """导出参数校验"""

    def test_export_invalid_format(self, client):
        """不支持的格式 → 422"""
        r = client.post("/api/v1/car/export", json={"format": "fbx"})
        assert r.status_code == 422

    def test_export_empty_body(self, client):
        """空 body → 默认 GLB"""
        r = client.post("/api/v1/car/export", json={})
        assert r.status_code == 200
        assert r.json()["format"] == "glb"

    def test_export_no_body(self, client):
        """无 body → 默认 GLB"""
        r = client.post("/api/v1/car/export", json={})
        assert r.status_code == 200
        data = r.json()
        assert data["file_size_bytes"] > 0


class TestExportConsistency:
    """导出一致性验证"""

    def test_same_params_same_size(self, client):
        """相同参数导出两次，文件大小相同（hash 去重）"""
        body = {"params": {"L": 4.5, "W": 1.85}, "format": "stl"}
        r1 = client.post("/api/v1/car/export", json=body)
        r2 = client.post("/api/v1/car/export", json=body)
        assert r1.status_code == 200
        assert r2.status_code == 200
        assert r1.json()["file_size_bytes"] == r2.json()["file_size_bytes"]

    def test_glb_obj_stl_all_succeed(self, client):
        """三种格式全部导出成功"""
        for fmt in ["glb", "obj", "stl"]:
            r = client.post("/api/v1/car/export", json={"format": fmt})
            assert r.status_code == 200, f"{fmt} export failed: {r.text}"
            assert r.json()["file_size_bytes"] > 0
