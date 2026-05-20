#!/usr/bin/env python3
"""
道层跨库联动验证脚本 v1.0
验证 assessment-catalog.json 四元组与 openmaic/quadruple-actions.json schema 定义一致。
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# ── 道层基准(硬编码, 与 openmaic quadruple-actions.json 保持一致) ─────

STAGE_RANGE = (1, 7)
STAGE_NAMES = {1: "不会", 2: "模糊", 3: "清晰", 4: "框架", 5: "运用", 6: "熟练", 7: "创新"}

EIGHT_STEP_RANGE = (1, 8)
EIGHT_STEP_NAMES = {
    1: "穿透", 2: "提取", 3: "整理", 4: "审题",
    5: "流程",  # ★ ⑤ 绝不是"演示"
    6: "批改", 7: "分析", 8: "估分",
}

FLYWHEEL_RANGE = (1, 6)
FLYWHEEL_NAMES = {
    1: "计划飞轮", 2: "预习飞轮", 3: "复习飞轮",
    4: "听课飞轮", 5: "作业飞轮", 6: "考试飞轮",
}

PASS_COUNT = 0
FAIL_COUNT = 0
ERRORS: list[str] = []


def ok(msg: str) -> None:
    global PASS_COUNT
    PASS_COUNT += 1
    print(f"  ✅ {msg}")


def fail(msg: str) -> None:
    global FAIL_COUNT
    FAIL_COUNT += 1
    ERRORS.append(f"❌ {msg}")
    print(f"  ❌ {msg}")


def check_stage(stage_id: int, stage_name: str, ctx: str) -> None:
    lo, hi = STAGE_RANGE
    if not (lo <= stage_id <= hi):
        fail(f"{ctx}: stage_id={stage_id} 超出范围 [{lo},{hi}]")
        return
    expected = STAGE_NAMES[stage_id]
    if stage_name != expected:
        fail(f"{ctx}: stage_name_zh='{stage_name}' 应为 '{expected}'")
        return
    ok(f"{ctx}: stage {stage_id}={stage_name} ✓")


def check_eight_step(step_id: int, step_name: str, ctx: str) -> None:
    lo, hi = EIGHT_STEP_RANGE
    if not (lo <= step_id <= hi):
        fail(f"{ctx}: eight_step_id={step_id} 超出范围 [{lo},{hi}]")
        return
    expected = EIGHT_STEP_NAMES[step_id]
    if step_name != expected:
        fail(f"{ctx}: eight_step_name_zh='{step_name}' 应为 '{expected}'")
        return
    if step_id == 5 and step_name != "流程":
        fail(f"{ctx}: ⑤ 必须是'流程'，实为'{step_name}'")
        return
    ok(f"{ctx}: eight_step {step_id}={step_name} ✓")


def check_flywheel(fw_id: int, fw_name: str, ctx: str) -> None:
    lo, hi = FLYWHEEL_RANGE
    if not (lo <= fw_id <= hi):
        fail(f"{ctx}: six_flywheel_id={fw_id} 超出范围 [{lo},{hi}]")
        return
    expected = FLYWHEEL_NAMES[fw_id]
    if fw_name != expected:
        fail(f"{ctx}: six_flywheel_name_zh='{fw_name}' 应为 '{expected}'")
        return
    ok(f"{ctx}: flywheel {fw_id}={fw_name} ✓")


def main() -> None:
    catalog_path = REPO_ROOT / "pipeline-data" / "assessment-catalog.json"
    if not catalog_path.exists():
        print(f"❌ 找不到 {catalog_path}")
        sys.exit(1)

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))

    print("=" * 60)
    print("  跨库联动验证 — assessment-catalog ↔ quadruple-actions schema")
    print("=" * 60)

    # ── Schema 级别检查 ──────────────────────────────────────

    print("\n[1] Schema 完整性检查")
    if "$schema" in catalog:
        ok("$schema 字段存在")
    else:
        fail("$schema 字段缺失")

    tools = catalog.get("assessment_tools", [])
    print(f"\n[2] 工具计数: {len(tools)} 个工具")
    if len(tools) == 22:
        ok(f"工具数量 = 22 ✓")
    else:
        fail(f"工具数量 = {len(tools)}，期望 22")

    # ── 四元组逐条验证 ───────────────────────────────────────

    print("\n[3] 四元组联动验证 (22 工具 × 7 阶 = 154 四元组)")
    quad_total = 0
    for tool in tools:
        tid = tool.get("tool_id", "?")
        for q in tool.get("stage_quadruples", []):
            quad_total += 1
            ctx = f"{tid}/stage{q.get('stage_id','?')}"
            check_stage(q["stage_id"], q["stage_name_zh"], ctx)
            check_eight_step(q["eight_step_id"], q["eight_step_name_zh"], ctx)
            check_flywheel(q["six_flywheel_id"], q["six_flywheel_name_zh"], ctx)

    print(f"\n  四元组总数: {quad_total}")
    if quad_total == 154:
        ok(f"四元组数量 = 154 (22×7) ✓")
    else:
        fail(f"四元组数量 = {quad_total}，期望 154")

    # ── ⑤流程守护 ──────────────────────────────────────────

    print("\n[4] ⑤流程专项守护")
    step5_violations = 0
    for tool in tools:
        tid = tool.get("tool_id", "?")
        for q in tool.get("stage_quadruples", []):
            if q.get("eight_step_id") == 5 and q.get("eight_step_name_zh") != "流程":
                step5_violations += 1
                fail(f"{tid}: ⑤ eight_step_name='{q['eight_step_name_zh']}' 非'流程'")
    if step5_violations == 0:
        ok("全部 ⑤ 四元组名称均为'流程' ✓")

    # ── 六飞轮枚举守护 ───────────────────────────────────────

    print("\n[5] 六飞轮枚举守护")
    drift_names = {"错题飞轮", "笔记飞轮", "阅读飞轮", "实践飞轮"}
    drift_violations = 0
    for tool in tools:
        tid = tool.get("tool_id", "?")
        for q in tool.get("stage_quadruples", []):
            fw = q.get("six_flywheel_name_zh", "")
            if fw in drift_names:
                drift_violations += 1
                fail(f"{tid}: 非法飞轮名称 '{fw}'")
    if drift_violations == 0:
        ok("全部飞轮名称合规，无非法变体 ✓")

    # ── 汇总 ─────────────────────────────────────────────────

    print("\n" + "=" * 60)
    total = PASS_COUNT + FAIL_COUNT
    print(f"  结果: {PASS_COUNT}/{total} 通过 | {FAIL_COUNT} 失败")
    print("=" * 60)

    if FAIL_COUNT > 0:
        print("\n失败详情:")
        for e in ERRORS:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("  ✅ 跨库联动验证 PASS — assessment ↔ quadruple-actions schema 一致")
        sys.exit(0)


if __name__ == "__main__":
    main()
