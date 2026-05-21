#!/usr/bin/env python3
"""
道层四元组联动验证脚本 v1.0
验证 pipeline-data/assessment-catalog.json 的 stage_quadruples 字段
与星耀途道层基准（七阶/八步/六飞轮）的一致性。
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

# ── 道层基准 ──────────────────────────────────────────────────

SEVEN_STAGES = {1: "不会", 2: "模糊", 3: "清晰", 4: "框架", 5: "运用", 6: "熟练", 7: "创新"}

EIGHT_STEPS = {
    1: "穿透", 2: "提取", 3: "整理", 4: "审题",
    5: "流程",  # ★ 绝不是"演示"
    6: "批改", 7: "分析", 8: "估分",
}

SIX_FLYWHEELS = {
    1: "计划飞轮", 2: "预习飞轮", 3: "复习飞轮",
    4: "听课飞轮", 5: "作业飞轮", 6: "考试飞轮",
}

# 禁用的漂移名称
FLYWHEEL_DRIFT = {"错题飞轮", "笔记飞轮", "阅读飞轮", "实践飞轮"}
STEP5_DRIFT = {"演示", "demo", "demonstration"}

FAIL = False
ERRORS: list[str] = []


def err(msg: str) -> None:
    global FAIL
    FAIL = True
    ERRORS.append(f"❌ {msg}")
    print(f"❌ {msg}", file=sys.stderr)


def ok(msg: str) -> None:
    print(f"✅ {msg}")


def validate_catalog() -> None:
    catalog_path = REPO_ROOT / "pipeline-data" / "assessment-catalog.json"
    if not catalog_path.exists():
        err(f"assessment-catalog.json 不存在: {catalog_path}")
        return

    with open(catalog_path, encoding="utf-8") as f:
        catalog = json.load(f)

    tools = catalog.get("assessment_tools", [])
    if not tools:
        err("assessment_tools 为空")
        return

    ok(f"找到 {len(tools)} 个测评工具")

    if len(tools) != 22:
        err(f"工具数量期望 22，实际 {len(tools)}")
    else:
        ok("工具数量 22 ✓")

    total_quadruples = 0
    for tool in tools:
        tool_id = tool.get("tool_id", "unknown")
        quadruples = tool.get("stage_quadruples", [])

        if len(quadruples) != 7:
            err(f"{tool_id}: stage_quadruples 期望 7 条，实际 {len(quadruples)}")

        for q in quadruples:
            total_quadruples += 1
            stage_id = q.get("stage_id")
            eight_step_id = q.get("eight_step_id")
            six_flywheel_id = q.get("six_flywheel_id")
            eight_step_name = q.get("eight_step_name_zh", "")
            flywheel_name = q.get("six_flywheel_name_zh", "")

            if stage_id not in SEVEN_STAGES:
                err(f"{tool_id} stage_id={stage_id} 不在七阶 [1,7]")

            if eight_step_id not in EIGHT_STEPS:
                err(f"{tool_id} stage={stage_id} eight_step_id={eight_step_id} 不在八步 [1,8]")

            if eight_step_id == 5:
                if eight_step_name != "流程":
                    err(f"{tool_id} stage={stage_id} ⑤的名称='{eight_step_name}'，期望'流程'")
                for drift in STEP5_DRIFT:
                    if drift in (eight_step_name or ""):
                        err(f"{tool_id} stage={stage_id} ⑤含漂移词'{drift}'")

            if six_flywheel_id not in SIX_FLYWHEELS:
                err(f"{tool_id} stage={stage_id} six_flywheel_id={six_flywheel_id} 不在六飞轮 [1,6]")

            if flywheel_name in FLYWHEEL_DRIFT:
                err(f"{tool_id} stage={stage_id} 飞轮名='{flywheel_name}' 是漂移词")

            stage_name = q.get("stage_name_zh", "")
            if stage_id in SEVEN_STAGES and stage_name != SEVEN_STAGES[stage_id]:
                err(
                    f"{tool_id} stage_id={stage_id} stage_name_zh='{stage_name}'，"
                    f"期望'{SEVEN_STAGES[stage_id]}'"
                )

    ok(f"共验证 {total_quadruples} 条四元组")


def validate_eight_step_baseline() -> None:
    assert EIGHT_STEPS[5] == "流程", "内部错误: 八步第5步必须是流程"
    ok("道层基准: 八步⑤=流程 ✓")


def validate_six_flywheel_count() -> None:
    assert len(SIX_FLYWHEELS) == 6, f"内部错误: 六飞轮应有6个，实际{len(SIX_FLYWHEELS)}"
    ok(f"道层基准: 六飞轮 {len(SIX_FLYWHEELS)} 个 ✓")


def validate_seven_stage_count() -> None:
    assert len(SEVEN_STAGES) == 7, f"内部错误: 七阶应有7个，实际{len(SEVEN_STAGES)}"
    ok(f"道层基准: 七阶 {len(SEVEN_STAGES)} 个 ✓")


if __name__ == "__main__":
    print("=" * 50)
    print("  星耀途四元组联动验证 v1.0")
    print("=" * 50)

    validate_eight_step_baseline()
    validate_six_flywheel_count()
    validate_seven_stage_count()
    validate_catalog()

    print("=" * 50)
    if FAIL:
        print(f"❌ 验证失败，共 {len(ERRORS)} 个错误")
        sys.exit(1)
    else:
        print("✅ 四元组联动验证全部通过")
        sys.exit(0)
