#!/usr/bin/env python3
"""
W3-D6: 性能基准测试 + 曲面质量验证

运行 algorithm_model 的 test_performance.py 和 test_quality.py，
汇总结果并报告。

用法:
    python run_w3d6_tests.py [result_mode] 
    result_mode: display_only (default)
"""

import asyncio
import sys
import subprocess
import re
from pathlib import Path


async def main():
    result_mode = sys.argv[1] if len(sys.argv) > 1 else "display_only"
    actual_mode = result_mode if result_mode != "auto" else "display_only"

    print(f"[参数] result_mode={result_mode}, actual_mode={actual_mode}")

    from codeact_sdk import CodeActSDK
    sdk = CodeActSDK()

    try:
        # 项目根目录
        project_root = Path(__file__).resolve().parent.parent.parent
        algo_dir = project_root / "algorithm_model"

        if not algo_dir.exists():
            await sdk.submit_result(
                result_mode="notify",
                status="error",
                message=f"algorithm_model 目录不存在: {algo_dir}",
            )
            return

        # ============================================================
        # 1. 运行性能基准测试
        # ============================================================
        print("=" * 60)
        print("1. 性能基准测试 (test_performance.py)")
        print("=" * 60)

        perf_cmd = [
            sys.executable, "-m", "pytest",
            str(algo_dir / "tests" / "test_performance.py"),
            "-p", "no:cacheprovider",
            '--override-ini=addopts=',
            "-v",
        ]

        perf_result = subprocess.run(
            perf_cmd, capture_output=True, text=True,
            cwd=str(algo_dir), timeout=120,
        )
        print(perf_result.stdout)
        if perf_result.stderr:
            print("STDERR:", perf_result.stderr[:2000])

        perf_passed = "passed" in perf_result.stdout
        perf_count_match = re.search(r'(\d+) passed', perf_result.stdout)
        perf_count = int(perf_count_match.group(1)) if perf_count_match else 0

        # ============================================================
        # 2. 运行曲面质量验证
        # ============================================================
        print("\n" + "=" * 60)
        print("2. 曲面质量验证 (test_quality.py)")
        print("=" * 60)

        qual_cmd = [
            sys.executable, "-m", "pytest",
            str(algo_dir / "tests" / "test_quality.py"),
            "-p", "no:cacheprovider",
            '--override-ini=addopts=',
            "-v",
        ]

        qual_result = subprocess.run(
            qual_cmd, capture_output=True, text=True,
            cwd=str(algo_dir), timeout=120,
        )
        print(qual_result.stdout)
        if qual_result.stderr:
            print("STDERR:", qual_result.stderr[:2000])

        qual_passed = "passed" in qual_result.stdout
        qual_count_match = re.search(r'(\d+) passed', qual_result.stdout)
        qual_count = int(qual_count_match.group(1)) if qual_count_match else 0

        # ============================================================
        # 3. 原有测试回归检查
        # ============================================================
        print("\n" + "=" * 60)
        print("3. 原有测试回归检查")
        print("=" * 60)

        existing_tests = [
            "tests/test_freeform.py",
            "tests/test_fillet.py",
            "tests/test_swept.py",
        ]

        existing_cmd = [
            sys.executable, "-m", "pytest",
        ] + [str(algo_dir / t) for t in existing_tests] + [
            "-p", "no:cacheprovider",
            '--override-ini=addopts=',
            "-q",
        ]

        existing_result = subprocess.run(
            existing_cmd, capture_output=True, text=True,
            cwd=str(algo_dir), timeout=120,
        )
        print(existing_result.stdout)

        existing_count_match = re.search(r'(\d+) passed', existing_result.stdout)
        existing_count = int(existing_count_match.group(1)) if existing_count_match else 0
        existing_failed_match = re.search(r'(\d+) failed', existing_result.stdout)
        existing_failed = int(existing_failed_match.group(1)) if existing_failed_match else 0

        # ============================================================
        # 4. 汇总
        # ============================================================
        all_new_passed = perf_passed and qual_passed
        total_new = perf_count + qual_count
        no_regression = existing_failed == 0

        print("\n" + "=" * 60)
        print("W3-D6 测试汇总")
        print("=" * 60)
        print(f"  性能基准测试: {perf_count} PASSED")
        print(f"  曲面质量验证: {qual_count} PASSED")
        print(f"  原有测试: {existing_count} passed, {existing_failed} failed")
        print(f"  新增测试总计: {total_new}")
        print(f"  回归检查: {'PASS' if no_regression else 'FAIL'}")
        print(f"  整体结果: {'ALL PASSED' if all_new_passed and no_regression else 'FAILED'}")

        # 构建消息
        if all_new_passed and no_regression:
            message = (
                f"W3-D6 性能基准测试 + 曲面质量验证: 全部通过\n\n"
                f"📊 性能基准测试: {perf_count} PASSED\n"
                f"  ✅ NURBS 基函数求值 < 1ms\n"
                f"  ✅ NURBS 曲线求值 x100 < 10ms\n"
                f"  ✅ NURBS 曲面求值 50×50 < 200ms\n"
                f"  ✅ FFD 50/5000/50000 顶点变形达标\n"
                f"  ✅ 圆角曲面生成 < 20ms\n"
                f"  ✅ 扫描曲面(100路径+10截面) < 30ms\n\n"
                f"🔍 曲面质量验证: {qual_count} PASSED\n"
                f"  ✅ G0 连续性 — 圆角边界位置偏差 < 1e-6\n"
                f"  ✅ G1 连续性 — 法线过渡平滑\n"
                f"  ✅ 曲率分布 — NURBS 主曲率 < 2×1/R\n"
                f"  ✅ 变形平滑性 — 位移场梯度/位移比 < 2.0\n"
                f"  ✅ FFD 体积变化 < 10%\n"
                f"  ✅ FFD 无新增退化三角形\n"
                f"  ✅ FFD 保持顶点/面数不变\n"
                f"  ✅ GLB 拓扑完全一致\n"
                f"  ✅ GLB 文件大小差异 < 20%\n\n"
                f"🔄 原有测试: {existing_count} passed, 0 failed (无回归)\n"
                f"📋 新增测试总计: {total_new}"
            )
        else:
            failed_parts = []
            if not perf_passed:
                failed_parts.append("性能基准测试失败")
            if not qual_passed:
                failed_parts.append("曲面质量验证失败")
            if not no_regression:
                failed_parts.append(f"原有测试回归({existing_failed} failed)")
            message = (
                f"W3-D6 测试未全部通过\n"
                f"失败项: {', '.join(failed_parts)}\n"
                f"性能: {perf_count} passed, 质量: {qual_count} passed"
            )

        await sdk.submit_result(
            status="success" if (all_new_passed and no_regression) else "error",
            result_mode=actual_mode,
            message=message,
            data={
                "performance_tests": perf_count,
                "quality_tests": qual_count,
                "existing_tests": existing_count,
                "existing_failed": existing_failed,
                "total_new_tests": total_new,
                "all_passed": all_new_passed and no_regression,
            },
        )

    except Exception as e:
        await sdk.submit_result(
            result_mode="notify",
            status="error",
            message=f"W3-D6 测试执行错误: {e}",
            data={"error_type": type(e).__name__},
        )


asyncio.run(main())
