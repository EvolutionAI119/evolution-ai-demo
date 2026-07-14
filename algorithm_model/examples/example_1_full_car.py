"""
示例 1: 完整汽车造型构建 + 导出

演示：
- 默认参数建模
- 自定义参数建模
- 单独操作某个部件
- 合并导出为 GLB / STL / OBJ
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from api import build_car, get_car_stats
from car_modeling import CarParams
from car_modeling.assembler import merge_all, export


def main():
    # 1) 默认参数
    print("=" * 60)
    print("1) 默认参数整车")
    print("=" * 60)
    parts = build_car()
    stats = get_car_stats()
    print(f"总顶点: {stats['total_vertices']}")
    print(f"总面数: {stats['total_faces']}")
    print(f"部件: {list(parts.keys())}")

    # 2) 自定义参数（运动型轿车）
    print("\n" + "=" * 60)
    print("2) 自定义参数 - 运动型轿车")
    print("=" * 60)
    sport_params = CarParams(
        L=4.6, W=1.90, H=1.32,  # 矮宽
        wheelbase=2.75,
        roof_arc=0.65,  # 高拱车顶
        windshield_rake=32.0,  # 大倾角
        rear_glass_angle=38.0,
        fender_prominence=0.25,  # 突出轮眉
        wheel_radius=0.36,  # 大轮
        wheel_spoke_count=7,  # 多辐
        headlight_width=0.50,  # 宽大灯
    )
    sport_parts = build_car(sport_params)
    sport_stats = get_car_stats(sport_params)
    print(f"车长: {sport_params.L}m / 车宽: {sport_params.W}m / 车高: {sport_params.H}m")
    print(f"车顶弧度: {sport_params.roof_arc} / 轮: {sport_params.wheel_radius}m × {sport_params.wheel_spoke_count} 辐")
    print(f"整车: {sport_stats['total_vertices']} 顶点, {sport_stats['total_faces']} 面")

    # 3) 单独访问部件
    print("\n" + "=" * 60)
    print("3) 单独操作部件")
    print("=" * 60)
    body = sport_parts["body"]
    print(f"车壳 mesh: {len(body.vertices)} 顶点")
    print(f"包围盒: {body.bounds.tolist()}")
    print(f"体积: {body.volume:.3f} m³")
    print(f"表面积: {body.area:.3f} m²")

    wheels = sport_parts["wheels"]
    print(f"\n车轮 mesh: {len(wheels.vertices)} 顶点")

    # 4) 合并并导出
    print("\n" + "=" * 60)
    print("4) 合并并导出 3D 文件")
    print("=" * 60)
    output_dir = Path(__file__).parent.parent / "outputs"
    output_dir.mkdir(exist_ok=True)

    merged = merge_all(sport_parts)
    print(f"合并 mesh: {len(merged.vertices)} 顶点, {len(merged.faces)} 面")

    # 导出多种格式
    for ext in ["glb", "stl"]:
        out_path = output_dir / f"sport_car.{ext}"
        export(sport_parts, str(out_path))
        print(f"  ✅ {out_path.name} ({out_path.stat().st_size:,} bytes)")

    # 5) 参数校验
    print("\n" + "=" * 60)
    print("5) 参数边界校验")
    print("=" * 60)
    bad_params = CarParams(L=10.0, W=0.5)  # 越界
    errors = bad_params.validate()
    for e in errors:
        print(f"  ❌ {e}")
    if not errors:
        print("  ✅ 全部参数合法")


if __name__ == "__main__":
    main()
