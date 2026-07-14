# Freeform Surface Module — NURBS 自由曲面库

纯 Python + NumPy 实现的 NURBS 曲面求值器、自由变形、圆角/倒角、扫描曲面模块。

---

## 模块概览

```
algorithm_model/freeform/
├── nurbs_core.py          # NURBS 核心：基函数、曲线、曲面求值
├── freeform_surface.py    # 自由变形（FFD）：5 预设 + 自定义
├── fillet_surface.py      # 圆角/倒角：两面过渡曲面
├── swept_surface.py       # 扫描曲面：沿路径扫描截面
└── __init__.py
```

| 子模块 | 功能定位 | 核心算法 |
|--------|----------|----------|
| `nurbs_core` | 底层求值引擎 | Cox-de Boor 递归、二分节点查找、曲面网格化 |
| `freeform_surface` | 在车体网格上施加局部变形 | NURBS 曲面 z 偏移 + smoothstep 边界过渡 |
| `fillet_surface` | 两面间圆角/倒角过渡 | 沿交线采样 + 法线间圆弧/直线插值 |
| `swept_surface` | 沿空间曲线扫描 2D 截面 | RMF 双反射法 Frenet 标架 + NURBS 曲面缝合 |

---

## API 速查

### nurbs_core.py

```python
def find_span(n: int, p: int, u: float, U: np.ndarray) -> int
def basis_funs(i: int, u: float, p: int, U: np.ndarray) -> np.ndarray
def curve_point(n: int, p: int, P: np.ndarray, U: np.ndarray, u: float) -> np.ndarray
def surface_point(n_p, n_q, p, q, P, W, U_u, U_v, u, v) -> np.ndarray
def open_uniform_knots(n: int, p: int) -> np.ndarray
def nurbs_surface_from_grid(control_points: np.ndarray, degree_u=3, degree_v=3, weights=None) -> dict
def evaluate_surface(surf: dict, u: float, v: float) -> np.ndarray
def evaluate_surface_mesh(surf: dict, n_u=50, n_v=50) -> Tuple[np.ndarray, np.ndarray]
```

### freeform_surface.py

```python
class FreeformDeformation:
    def __init__(self, preset: str = 'fender_bulge',
                 amplitude: float = None,
                 center: Tuple[float, float] = (0.5, 0.5),
                 size: Tuple[float, float] = None,
                 custom_control_points: np.ndarray = None)
    def apply(self, mesh: trimesh.Trimesh,
              center_x: float = 0.0, center_z: float = 0.0,
              bbox: dict = None) -> trimesh.Trimesh

# 预设: fender_bulge / door_dent / hood_scoop / character_line / roof_sculpt / custom
```

### fillet_surface.py

```python
class IntersectionCurve:
    def __init__(self, points: np.ndarray)          # (N, 3) 交线离散点
    def evaluate(self, t: float) -> np.ndarray

def create_fillet_surface(surface_a, surface_b, intersection,
                          radius: float = 0.01, n_samples: int = 20,
                          variable_radius: Callable = None) -> dict
def create_chamfer_surface(surface_a, surface_b, intersection,
                           angle: float = 45.0, width: float = 0.01,
                           n_samples: int = 20) -> dict
def create_wheel_arch_fillet(center, radius, start_angle, end_angle,
                             fillet_radius=0.005) -> dict
def surface_to_mesh(surf: dict, n_u=20, n_v=20) -> trimesh.Trimesh
```

### swept_surface.py

```python
def generate_circle_section(radius: float, n_points: int = 16) -> np.ndarray
def generate_rectangle_section(width: float, height: float, n_per_side: int = 4) -> np.ndarray

class FrenetFrame:
    def __init__(self, path_points: np.ndarray)     # (N, 3) 路径点
    def evaluate(self, t: float) -> Tuple[np.ndarray, np.ndarray, np.ndarray]  # T, N, B

class SweptSurface:
    def __init__(self, path_points, section_points, section_scale=None)
    def build(self) -> dict                          # 返回 NURBS surface dict

# 路径支持 NURBS 曲线控制点 或 离散点序列
```

### car_modeling/trim.py（关联模块）

```python
class TrimStrip:
    def __init__(self, path_points, section_type='circle', **kwargs)
    def build(self) -> trimesh.Trimesh

def create_chrome_trim(path_points, width=0.008, height=0.003) -> trimesh.Trimesh
def create_rubber_seal(path_points, width=0.005, height=0.006) -> trimesh.Trimesh
def create_body_molding(path_points, width=0.015, height=0.008) -> trimesh.Trimesh
```

---

## 快速使用示例

### 1. NURBS 曲面求值

```python
from algorithm_model.freeform.nurbs_core import nurbs_surface_from_grid, evaluate_surface_mesh
import numpy as np

# 4×4 控制点网格
ctrl = np.array([
    [[0,0,0], [1,0,0], [2,0,0], [3,0,0]],
    [[0,1,0], [1,1,0.5], [2,1,0.5], [3,1,0]],
    [[0,2,0], [1,2,0.3], [2,2,0.3], [3,2,0]],
    [[0,3,0], [1,3,0], [2,3,0], [3,3,0]],
], dtype=float)

surf = nurbs_surface_from_grid(ctrl, degree_u=3, degree_v=3)
vertices, faces = evaluate_surface_mesh(surf, n_u=30, n_v=30)
# vertices: (900, 3), faces: (1682, 3)
```

### 2. 自由变形（FFD）

```python
from algorithm_model.freeform.freeform_surface import FreeformDeformation
import trimesh

mesh = trimesh.load("car_body.glb")
ffd = FreeformDeformation(preset='fender_bulge', amplitude=0.05)
deformed = ffd.apply(mesh, center_x=0.3, center_z=0.5)
# 轮眉区域凸起 5cm
```

### 3. 圆角曲面

```python
from algorithm_model.freeform.fillet_surface import (
    IntersectionCurve, create_fillet_surface, surface_to_mesh
)
import numpy as np

# 定义交线
pts = np.array([[0,0,0], [0.5,0,0], [1,0,0]])
curve = IntersectionCurve(pts)

# 生成 R=0.01 圆角
fillet = create_fillet_surface(
    surface_a=lambda u, v: np.array([u, 0, v]),
    surface_b=lambda u, v: np.array([u, v, 0]),
    intersection=curve,
    radius=0.01, n_samples=20
)
mesh = surface_to_mesh(fillet)
```

### 4. 扫描曲面（装饰条）

```python
from algorithm_model.car_modeling.trim import create_chrome_trim
import numpy as np

# 沿腰线扫描圆形截面
path = np.array([
    [0, 0.5, 0.8], [0.5, 0.5, 0.82], [1.0, 0.5, 0.8],
    [1.5, 0.5, 0.78], [2.0, 0.5, 0.8]
])
mesh = create_chrome_trim(path, width=0.008, height=0.003)
# mesh.vertices ~ 80, mesh.faces ~ 156
```

---

## 性能参考

测试环境：纯 Python 3.11 + NumPy，无 Cython 加速。

| 操作 | 数据规模 | 耗时 |
|------|----------|------|
| B 样条基函数 | 单次 | 0.003ms |
| NURBS 曲线求值 | ×100 | 3.2ms |
| NURBS 曲面求值 | 50×50 | ~84ms |
| FFD 变形 | 50 顶点 | 0.2ms |
| FFD 变形 | 5000 顶点 | 18ms |
| FFD 变形 | 50000 顶点 | ~420ms |
| 圆角曲面 | 20 采样 | 5ms |
| 扫描曲面 | 20 采样 × 16 截面 | 15ms |

---

## 质量指标

| 指标 | 实测值 |
|------|--------|
| Frenet 标架正交误差 | 1.65e-15 |
| G0 连续性 gap | 3.47e-18 |
| G1 法线夹角 | 0.00° |
| FFD 体积变化 | 5.30% |
| 整车网格 | 3475v / 6504f |

---

## 依赖

- `numpy` — 数值计算
- `trimesh` — 网格数据结构
- `scipy` — （可选）弧长参数化加速

---

*Freeform module — 让 22 维参数系统进化到参数化 + 自由曲面双模式。*
