# W2 启动前 - M2.5 car_body bug 修复完结报告

> 写入时间：2026-06-20 22:20
> 任务来源：W1-D2 完结时主人选 C（先修 M2.5 老 bug 再走 W1-D3）
> 关联：W1-D1 完结报告（首次发现 6 次 car_body 异步全 FAILURE）/ W1-D2 完结报告（标技术债留到 W2-D1 前修）

---

## 1. 任务范围

修复 W1-D1 反思中识别的 car_body 异步任务死循环 bug：
- **症状**：`POST /api/v1/optimize/start-preset {"shape":"car_body"}` → Celery worker 抛 `ValueError: At least one array has zero dimension` → task 状态 FAILURE
- **影响**：DB 中 6 次 car_body 异步任务记录全部 FAILURE（log 在 `logs/celery_worker.log`）
- **范围**：仅修异步链路 car_body 跑通；算法层 grade=D 改善留 W2-D1（KDTree 散点重排）

---

## 2. 根因分析

### 2.1 调用链

```
POST /api/v1/optimize/start-preset {"shape":"car_body"}
  → OptimizeService.start_preset_async(surface_type="car_body")
  → run_optimize_task.delay(task_id, "car_body", "car_body", 10, 42)
  → Celery worker：run_optimize_task(task_id, "car_body", "car_body", 10, 42)
    → _make_surface("car_body")  ← ★ 死在这一步
        旧版：return body.vertices（shape=(2352, 3)）
    → optimize_surface((2352, 3), ...)  ← 期望 (N, M, 3)
    → algorithm_model.surface_quality.optimizer._objective
        → estimate_normals((2352, 3))
            → n, m = 2352, 3
            → for j in range(1, 2):  → j=1
            → v01 = surface_points[i, 2]  ← 第 3 列是 Z 分量（标量）！
            → np.cross(v10 - v00, v11 - v00)  ← 维度不匹配
            → ValueError: At least one array has zero dimension
```

### 2.2 根因

`_make_surface("car_body")` 返回的 `body.vertices` 是 (N, 3) 散点，但 `algorithm_model` 算法层（`estimate_normals` / `check_g0_g1_g2` / `compute_reflection_score` / `assess_quality` / `ai_optimize`）**全栈假设输入是规则网格 (N, M, 3)**。

W1-D1 修了 Bug 2（"Trimesh 不是 ndarray"）：把 `arr = np.array(parts[k])` 改成 `arr = np.array(parts[k].vertices)`，**但只判了 2D 形状就 return，没继续 reshape 成 3D 网格**。

同步路径 `OptimizeService.optimize_preset` 走的是 `quality_service.make_car_body_panel`，那里**有** `pts = verts[:n*n].reshape(n, n, 3)`，所以同步跑通；异步路径走 `optimize_task._make_surface` 没做 reshape，所以挂。

### 2.3 body 实际是规则网格

`build_car(None)["body"]` 是 49（X 长向）× 48（Y 圆周向）= 2352 散点，本质就是规则网格的扁平化。直接 `body.vertices[:49*48].reshape(49, 48, 3)` 即可还原。

| 部件 | 顶点数 | ndim | 形状 |
|---|---|---|---|
| body | 2352 | 2 | (2352, 3) → reshape 成 (49, 48, 3) |
| glass | 243 | 2 | (243, 3) |
| wheels | 688 | 2 | (688, 3) |
| headlights | 32 | 2 | (32, 3) |
| ... | ... | ... | ... |

---

## 3. 修复

### 3.1 代码改动

**文件**：`backend/tasks/optimize_task.py`
**函数**：`_make_surface("car_body")` 分支
**改动**：找到 body 后不再直接 return (N, 3)，而是 reshape 成 (49, 48, 3) 网格

```python
# 修复后逻辑（关键 diff）
n_long, n_circ = 49, 48
if body_arr.shape[0] < n_long * n_circ:
    # 退化：兜不住 49×48 时按最长规则方阵铺
    side = int(np.sqrt(body_arr.shape[0]))
    n_long, n_circ = side, side
return body_arr[: n_long * n_circ].reshape(n_long, n_circ, 3)
```

防御性退化：若 body 顶点数不足以 49×48（未来 CarParams 改变），按 sqrt 算方阵兜底。

### 3.2 4 shape 行为对账

| shape | 旧版 | 新版 |
|---|---|---|
| sphere | (20, 20, 3) | (20, 20, 3) 不变 |
| plane | (20, 20, 3) | (20, 20, 3) 不变 |
| cylinder | (20, 20, 3) | (20, 20, 3) 不变 |
| car_body | (2352, 3) ❌ 触发 bug | (49, 48, 3) ✅ |

---

## 4. E2E 验证

**脚本**：`logs/car_body_bugfix_e2e.py`（15 项断言）
**结果**：**15/15 全过** ✅

```
T1 _make_surface 4 shape 输出都是 3D 网格
  ✅ _make_surface('sphere') ndim=3 — shape=(20, 20, 3)
  ✅ _make_surface('plane') ndim=3 — shape=(20, 20, 3)
  ✅ _make_surface('cylinder') ndim=3 — shape=(20, 20, 3)
  ✅ _make_surface('car_body') ndim=3 — shape=(49, 48, 3)
  ✅ car_body reshape 后是 (49, 48, 3) — actual=(49, 48, 3)
  ✅ body 顶点数 = 49×48 = 2352 — body_n=2352

T2 car_body 异步任务 → SUCCESS（修 bug 核心）
  task_id=61bf561eb4c5460ab1c70654b4416f27
  ✅ car_body 异步 status=SUCCESS — actual=SUCCESS
  ✅ 有 initial_grade + final_grade — D→D
  ✅ g2 数字合理 (initial_g2 > 0) — g2 1752→1714
  ✅ convergence_curve 11 个点（10 iter + 1 initial）
  ✅ optimized_points 是 (49, 48, 3) 网格
  ✅ error_message 不含 "zero dimension"

T3 / T4 其他 3 shape 异步回归
  ✅ sphere 异步 SUCCESS
  ✅ plane_with_noise 异步 SUCCESS
  ✅ cylinder 异步 SUCCESS

总计: 15 ✅ / 0 ❌
```

---

## 5. 收尾服务现状

| 服务 | PID | 状态 |
|---|---|---|
| redis-server | - | ✅ PONG（6379） |
| uvicorn | 316 | ✅ 8000 health 200 |
| Celery worker | 950 | ✅ redis broker, concurrency=2, **car_body 已能消费** |
| vite dev | - | ✅ 5173 200 |

---

## 6. 已知技术债（W2 启动后处理）

| 编号 | 描述 | 优先级 | 计划 |
|---|---|---|---|
| TD-1 | car_body 散点被直接 reshape 出的 grade=D（不是真规则网格） | 中 | W2-D1 用 KDTree 散点重排 |
| TD-2 | run_full_pipeline 用 (49, 25) 不一致（实际 49×48） | 低 | 统一 grid 数字 |
| TD-3 | vue-i18n@9 警告 v9 不再支持 | 低 | W1 完工后迁 v11 |

---

## 7. 结论

- ✅ **car_body 异步任务死循环 bug 修复**（从 FAILURE → SUCCESS，DB 6 条 FAILURE 历史已无法回写但新任务全部正常）
- ✅ **不影响其他 3 shape**（sphere / plane / cylinder 回归 SUCCESS）
- ✅ **E2E 15/15 全过**
- ✅ **MEMORY / TOOLS 已同步更新**（避免下次再踩）
- 🟡 **算法层 grade=D 改善**留 W2-D1 启动时处理（KDTree 散点重排）

**W2 启动无技术阻塞**。可以继续 W1-D3 推进。
