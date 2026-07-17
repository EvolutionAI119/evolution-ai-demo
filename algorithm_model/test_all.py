"""
算法模型 - 一站式自检脚本

跑通 4 大模块的所有关键能力：
1. car_modeling - 整车 8 部件建模
2. surface_quality - 球面/车身曲面质量评估
3. surface_quality - AI 模拟退火优化
4. storyboard - 视频脚本生成
5. storyboard_viewer - 文档渲染
"""
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithm_model.api import (
    build_car, get_car_stats, evaluate_surface, optimize_surface,
    make_storyboard, render_storyboard,
)


def test_car_modeling():
    """测试整车造型建模"""
    print("\n" + "=" * 60)
    print("【1/5】car_modeling - 整车造型建模")
    print("=" * 60)
    from car_modeling import CarParams, build_full_car, compute_stats

    # 默认参数
    parts = build_full_car(CarParams())
    stats = compute_stats(parts)
    print(f"✅ 默认参数整车: {stats['total_vertices']} 顶点, {stats['total_faces']} 面")
    for name, info in stats["components"].items():
        print(f"   - {name}: {info['vertices']:>4d} verts, {info['faces']:>4d} faces, color={info['color']}")

    # 自定义参数
    custom = CarParams(L=4.9, W=1.92, H=1.50, roof_arc=0.55, windshield_rake=32.0)
    errors = custom.validate()
    assert not errors, f"参数校验失败: {errors}"
    parts2 = build_full_car(custom)
    stats2 = compute_stats(parts2)
    print(f"\n✅ 自定义参数整车: L={custom.L} W={custom.W} H={custom.H} roof_arc={custom.roof_arc}")
    print(f"   总顶点: {stats2['total_vertices']}, 总面数: {stats2['total_faces']}")

    # 边界检查
    bad = CarParams(L=10.0)  # 超出范围
    errs = bad.validate()
    assert len(errs) > 0, "应该捕获越界"
    print(f"✅ 参数校验: 越界参数被正确捕获 ({len(errs)} 个错误)")

    return stats


def test_quality_assessment():
    """测试曲面质量评估"""
    print("\n" + "=" * 60)
    print("【2/5】surface_quality - 曲面质量评估")
    print("=" * 60)
    import numpy as np

    # 球面（公认难优化曲面）
    u = np.linspace(0, np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    U, V = np.meshgrid(u, v)
    R = 2.0
    X = R * np.sin(U) * np.cos(V)
    Y = R * np.sin(U) * np.sin(V)
    Z = R * np.cos(U)
    sphere = np.stack([X, Y, Z], axis=-1)

    report = evaluate_surface(sphere, "球面")
    print(f"✅ 球面评估:")
    print(f"   等级: {report.grade} | G2 比率: {report.g2_ratio} | 反射线: {report.reflection_score}")
    print(f"   G0={report.g0_count} G1={report.g1_count} G2={report.g2_count} | 最大跳变={report.max_curvature_jump}°")

    # 车身网格
    parts = build_car()
    body = parts["body"]
    n_long, n_circ = 49, 25
    surface = body.vertices[:n_long * n_circ].reshape(n_long, n_circ, 3)
    report2 = evaluate_surface(surface, "车身侧视")
    print(f"\n✅ 车身侧视评估:")
    print(f"   等级: {report2.grade} | G2 比率: {report2.g2_ratio} | 反射线: {report2.reflection_score}")
    print(f"   G0={report2.g0_count} G1={report2.g1_count} G2={report2.g2_count} | 最大跳变={report2.max_curvature_jump}°")

    return report, report2


def test_ai_optimization():
    """测试 AI 模拟退火优化"""
    print("\n" + "=" * 60)
    print("【3/5】surface_quality - AI 模拟退火优化")
    print("=" * 60)
    import numpy as np

    # 球面
    u = np.linspace(0, np.pi, 20)
    v = np.linspace(0, np.pi, 20)
    U, V = np.meshgrid(u, v)
    R = 2.0
    X = R * np.sin(U) * np.cos(V)
    Y = R * np.sin(U) * np.sin(V)
    Z = R * np.cos(U)
    sphere = np.stack([X, Y, Z], axis=-1)

    t0 = time.time()
    result = optimize_surface(sphere, "球面", max_iter=80, seed=42)
    dt = time.time() - t0

    print(f"✅ 球面优化 ({result.iterations} 次迭代, {dt:.3f}s):")
    print(f"   等级: {result.initial_grade} → {result.final_grade}")
    print(f"   G2: {result.initial_g2} → {result.final_g2} "
          f"(Δ={result.final_g2 - result.initial_g2:+d})")
    print(f"   反射线: {result.initial_reflection} → {result.final_reflection} "
          f"(Δ={result.final_reflection - result.initial_reflection:+.3f})")
    assert result.iterations > 0
    assert result.best_surface is not None

    # 车身
    parts = build_car()
    body = parts["body"]
    surface = body.vertices[:49 * 25].reshape(49, 25, 3)
    t0 = time.time()
    result2 = optimize_surface(surface, "车身侧视", max_iter=80, seed=42)
    dt = time.time() - t0

    print(f"\n✅ 车身侧视优化 ({result2.iterations} 次迭代, {dt:.3f}s):")
    print(f"   等级: {result2.initial_grade} → {result2.final_grade}")
    print(f"   G2: {result2.initial_g2} → {result2.final_g2} "
          f"(Δ={result2.final_g2 - result2.initial_g2:+d})")
    print(f"   反射线: {result2.initial_reflection} → {result2.final_reflection} "
          f"(Δ={result2.final_reflection - result2.initial_reflection:+.3f})")
    print("   ⚠️  车身是分段拼接曲面（5 段不同高度），优化空间有限")
    print("   💡 工业场景：优化前先做曲面拼接光滑（CAD 阶段）")

    # 平面 + 噪声（最佳优化演示）
    print("\n✅ 平面+噪声 - 优化效果最显著的演示")
    np.random.seed(42)
    n = 25
    plane = np.zeros((n, n, 3))
    for i in range(n):
        for j in range(n):
            plane[i, j] = [i * 0.1, j * 0.1, np.random.randn() * 0.15]
    t0 = time.time()
    result3 = optimize_surface(plane, "带噪声平面", max_iter=120, seed=42)
    dt = time.time() - t0
    print(f"   ({result3.iterations} 次迭代, {dt:.3f}s):")
    print(f"   等级: {result3.initial_grade} → {result3.final_grade}")
    print(f"   G2: {result3.initial_g2} → {result3.final_g2} "
          f"(Δ={result3.final_g2 - result3.initial_g2:+d})")
    print(f"   反射线: {result3.initial_reflection} → {result3.final_reflection} "
          f"(Δ={result3.final_reflection - result3.initial_reflection:+.3f})")

    return result


def test_storyboard_generation():
    """测试视频脚本生成"""
    print("\n" + "=" * 60)
    print("【4/5】storyboard - 视频脚本生成")
    print("=" * 60)

    # 3 套模板
    for template in ["car_promotion", "tech_demo", "minimal_showcase"]:
        sb = make_storyboard(template=template, duration=90)
        print(f"✅ {template}: {len(sb.scenes)} 镜, 总时长 {sb.total_duration}s")
        for s in sb.scenes[:2]:
            print(f"   [{s.scene_id}] {s.duration_sec:>4.1f}s | {s.name}")
        if len(sb.scenes) > 2:
            print(f"   ... 共 {len(sb.scenes)} 镜")

    # 自定义
    sb = make_storyboard(
        product_name="My Car",
        duration=60,
        template="tech_demo",
        audience="投资人",
    )
    print(f"\n✅ 自定义: '{sb.title}', 观众={sb.audience}, 时长={sb.total_duration}s")

    return sb


def test_storyboard_render():
    """测试视频脚本渲染"""
    print("\n" + "=" * 60)
    print("【5/5】storyboard_viewer - 视频脚本渲染")
    print("=" * 60)
    sb = make_storyboard(template="car_promotion", duration=90)

    # Markdown
    md = render_storyboard(sb, "markdown")
    md_path = Path(__file__).parent / "outputs" / "example_storyboard.md"
    md_path.parent.mkdir(exist_ok=True)
    md_path.write_text(md, encoding="utf-8")
    print(f"✅ Markdown 渲染: {len(md)} 字符 → {md_path}")

    # HTML
    html_doc = render_storyboard(sb, "html")
    html_path = Path(__file__).parent / "outputs" / "example_storyboard.html"
    html_path.write_text(html_doc, encoding="utf-8")
    print(f"✅ HTML 渲染: {len(html_doc)} 字符 → {html_path}")

    return md_path, html_path


def run_all_tests():
    """跑全部自检"""
    print("\n" + "🧪" * 30)
    print(" EVOLUTION AI 算法模型 - 一站式自检")
    print("🧪" * 30)

    t_start = time.time()
    try:
        test_car_modeling()
        test_quality_assessment()
        test_ai_optimization()
        test_storyboard_generation()
        test_storyboard_render()
    except Exception as e:
        print(f"\n❌ 自检失败: {e}")
        import traceback
        traceback.print_exc()
        return False

    dt = time.time() - t_start
    print("\n" + "=" * 60)
    print(f"✅ 全部自检通过!  总耗时: {dt:.2f}s")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
