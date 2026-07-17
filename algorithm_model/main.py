"""
EVOLUTION AI 算法模型 - 一站式 CLI 入口

用法：
    python main.py build-car                          # 构建默认参数整车
    python main.py build-car --L 4.8 --roof-arc 0.55  # 自定义参数
    python main.py quality --shape sphere             # 评估球面
    python main.py optimize --shape sphere --iter 50  # 优化球面
    python main.py storyboard --template car_promotion --duration 90
    python main.py render --template car_promotion --format html --output story.html
    python main.py all                                 # 跑完整流程
    python main.py test                                # 跑自检
"""
import sys
import argparse
import json
import os
from pathlib import Path

# 允许在 algorithm_model/ 目录下直接 python main.py
sys.path.insert(0, str(Path(__file__).parent.parent))

from algorithm_model.api import (
    build_car, get_car_stats, evaluate_surface, optimize_surface,
    make_storyboard, render_storyboard, run_full_pipeline,
)
from algorithm_model.car_modeling import CarParams


def cmd_build_car(args):
    """构建完整汽车"""
    params = CarParams(
        L=args.L, W=args.W, H=args.H, wheelbase=args.wheelbase,
        hood_length=args.hood_length, cabin_length=args.cabin_length,
        trunk_length=args.trunk_length, ground_clearance=args.ground_clearance,
        roof_arc=args.roof_arc, windshield_rake=args.windshield_rake,
        waist_line=args.waist_line,
    )
    errors = params.validate()
    if errors:
        print("⚠️  参数错误:")
        for e in errors:
            print(f"  - {e}")
        return

    parts = build_car(params)
    stats = get_car_stats(params)
    print(json.dumps({
        "params": params.to_dict(),
        "stats": {
            "total_vertices": stats["total_vertices"],
            "total_faces": stats["total_faces"],
            "components": {k: v["vertices"] for k, v in stats["components"].items()},
            "bounds": stats["bounds"],
        },
    }, ensure_ascii=False, indent=2))

    if args.output:
        # 合并为单个 mesh 导出
        from car_modeling.assembler import merge_all
        merged = merge_all(parts)
        merged.export(args.output)
        print(f"\n✅ 已导出: {args.output}")
        print(f"  {len(merged.vertices)} 顶点, {len(merged.faces)} 面")


def cmd_quality(args):
    """评估曲面质量"""
    if args.shape == "sphere":
        import numpy as np
        u = np.linspace(0, np.pi, 20)
        v = np.linspace(0, np.pi, 20)
        U, V = np.meshgrid(u, v)
        R = 2.0
        X = R * np.sin(U) * np.cos(V)
        Y = R * np.sin(U) * np.sin(V)
        Z = R * np.cos(U)
        surface = np.stack([X, Y, Z], axis=-1)
        panel = "球面"
    elif args.shape == "car":
        parts = build_car()
        body = parts["body"]
        n_long, n_circ = 49, 25
        surface = body.vertices[:n_long * n_circ].reshape(n_long, n_circ, 3)
        panel = "车身侧视"
    else:
        print(f"❌ 未知 shape '{args.shape}'，可选: sphere / car")
        return

    report = evaluate_surface(surface, panel)
    print(json.dumps({
        "panel": report.panel_name,
        "grade": report.grade,
        "g0_count": report.g0_count,
        "g1_count": report.g1_count,
        "g2_count": report.g2_count,
        "g1_ratio": report.g1_ratio,
        "g2_ratio": report.g2_ratio,
        "max_curvature_jump": report.max_curvature_jump,
        "mean_curvature": report.mean_curvature,
        "reflection_score": report.reflection_score,
    }, ensure_ascii=False, indent=2))


def cmd_optimize(args):
    """AI 优化曲面"""
    import numpy as np
    if args.shape == "sphere":
        u = np.linspace(0, np.pi, 20)
        v = np.linspace(0, np.pi, 20)
        U, V = np.meshgrid(u, v)
        R = 2.0
        X = R * np.sin(U) * np.cos(V)
        Y = R * np.sin(U) * np.sin(V)
        Z = R * np.cos(U)
        surface = np.stack([X, Y, Z], axis=-1)
        panel = "球面"
    elif args.shape == "car":
        parts = build_car()
        body = parts["body"]
        n_long, n_circ = 49, 25
        surface = body.vertices[:n_long * n_circ].reshape(n_long, n_circ, 3)
        panel = "车身侧视"
    else:
        print(f"❌ 未知 shape '{args.shape}'，可选: sphere / car")
        return

    import time
    t0 = time.time()
    result = optimize_surface(surface, panel, max_iter=args.iter, seed=args.seed)
    dt = time.time() - t0

    print(json.dumps({
        "panel": panel,
        "elapsed_sec": round(dt, 3),
        "iterations": result.iterations,
        "initial": {
            "grade": result.initial_grade,
            "g2": result.initial_g2,
            "reflection": result.initial_reflection,
        },
        "final": {
            "grade": result.final_grade,
            "g2": result.final_g2,
            "reflection": result.final_reflection,
        },
        "improvement": {
            "g2_delta": result.final_g2 - result.initial_g2,
            "reflection_delta": round(result.final_reflection - result.initial_reflection, 3),
        },
    }, ensure_ascii=False, indent=2))


def cmd_storyboard(args):
    """生成视频脚本"""
    sb = make_storyboard(
        product_name=args.product,
        duration=args.duration,
        template=args.template,
    )
    print(json.dumps({
        "title": sb.title,
        "total_duration": sb.total_duration,
        "scene_count": len(sb.scenes),
        "scenes": [
            {
                "id": s.scene_id,
                "duration": s.duration_sec,
                "name": s.name,
                "shot_type": s.shot_type,
                "camera": s.camera,
            }
            for s in sb.scenes
        ],
    }, ensure_ascii=False, indent=2))


def cmd_render(args):
    """渲染视频脚本为可视化文档"""
    sb = make_storyboard(
        product_name=args.product,
        duration=args.duration,
        template=args.template,
    )
    doc = render_storyboard(sb, args.format)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(doc)
        print(f"✅ 已生成: {args.output} ({len(doc)} 字符)")
    else:
        print(doc[:500] + "..." if len(doc) > 500 else doc)


def cmd_all(args):
    """跑完整流程"""
    result = run_full_pipeline()
    print("=" * 60)
    print(f"🎬 {result['storyboard'].title}")
    print("=" * 60)
    print(f"\n📊 整车统计:")
    print(f"  总顶点: {result['stats']['total_vertices']}")
    print(f"  总面数: {result['stats']['total_faces']}")
    print(f"  部件: {list(result['car_parts'].keys())}")
    print(f"\n🔍 质量评估:")
    print(f"  优化前: {result['quality_before'].grade} 级 "
          f"(G2={result['quality_before'].g2_count}, "
          f"反射线={result['quality_before'].reflection_score})")
    print(f"  优化后: {result['quality_after'].grade} 级 "
          f"(G2={result['quality_after'].g2_count}, "
          f"反射线={result['quality_after'].reflection_score})")
    print(f"\n📈 优化提升:")
    print(f"  G2: {result['optimization']['initial_g2']} → {result['optimization']['final_g2']}")
    print(f"  反射线: {result['optimization']['initial_reflection']} → {result['optimization']['final_reflection']}")
    print(f"  迭代: {result['optimization']['iterations']} 次")
    print(f"\n🎬 视频脚本:")
    print(f"  {result['storyboard'].title}")
    print(f"  {len(result['storyboard'].scenes)} 个分镜, 总时长 {result['storyboard'].total_duration}s")
    print("=" * 60)


def cmd_test(args):
    """跑自检"""
    print("🧪 跑一站式自检...\n")
    from test_all import run_all_tests
    run_all_tests()


def main():
    parser = argparse.ArgumentParser(
        description="EVOLUTION AI 算法模型 - 一站式 CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # build-car
    p1 = subparsers.add_parser("build-car", help="构建完整汽车造型")
    p1.add_argument("--L", type=float, default=4.7)
    p1.add_argument("--W", type=float, default=1.85)
    p1.add_argument("--H", type=float, default=1.45)
    p1.add_argument("--wheelbase", type=float, default=2.8)
    p1.add_argument("--hood-length", type=float, default=1.1)
    p1.add_argument("--cabin-length", type=float, default=2.2)
    p1.add_argument("--trunk-length", type=float, default=1.0)
    p1.add_argument("--ground-clearance", type=float, default=0.18)
    p1.add_argument("--roof-arc", type=float, default=0.35)
    p1.add_argument("--windshield-rake", type=float, default=28.0)
    p1.add_argument("--waist-line", type=float, default=0.85)
    p1.add_argument("--output", "-o", help="导出路径（glb/stl/obj/ply）")
    p1.set_defaults(func=cmd_build_car)

    # quality
    p2 = subparsers.add_parser("quality", help="评估曲面质量")
    p2.add_argument("--shape", default="sphere", choices=["sphere", "car"])
    p2.set_defaults(func=cmd_quality)

    # optimize
    p3 = subparsers.add_parser("optimize", help="AI 模拟退火优化曲面")
    p3.add_argument("--shape", default="sphere", choices=["sphere", "car"])
    p3.add_argument("--iter", type=int, default=80, help="最大迭代次数")
    p3.add_argument("--seed", type=int, default=42)
    p3.set_defaults(func=cmd_optimize)

    # storyboard
    p4 = subparsers.add_parser("storyboard", help="生成视频脚本")
    p4.add_argument("--product", default="EVOLUTION AI")
    p4.add_argument("--duration", type=float, default=90)
    p4.add_argument("--template", default="car_promotion",
                    choices=["car_promotion", "tech_demo", "minimal_showcase"])
    p4.set_defaults(func=cmd_storyboard)

    # render
    p5 = subparsers.add_parser("render", help="渲染视频脚本为 md/html")
    p5.add_argument("--product", default="EVOLUTION AI")
    p5.add_argument("--duration", type=float, default=90)
    p5.add_argument("--template", default="car_promotion",
                    choices=["car_promotion", "tech_demo", "minimal_showcase"])
    p5.add_argument("--format", default="markdown", choices=["markdown", "html"])
    p5.add_argument("--output", "-o", help="输出文件路径")
    p5.set_defaults(func=cmd_render)

    # all
    p6 = subparsers.add_parser("all", help="跑完整流程（建模+评估+优化+脚本+渲染）")
    p6.set_defaults(func=cmd_all)

    # test
    p7 = subparsers.add_parser("test", help="跑一站式自检")
    p7.set_defaults(func=cmd_test)

    args = parser.parse_args()
    if args.command is None:
        parser.print_help()
        return
    args.func(args)


if __name__ == "__main__":
    main()
