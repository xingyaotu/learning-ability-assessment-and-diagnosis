#!/usr/bin/env python3
"""
道层学生进度 schema 验证脚本 v1.0
验证 pipeline-data/student-progress-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. 四种 schema_definitions 完整性 (4个类型)
  3. ⑤守护: validation_rules.eight_step_name_constraints.five == '流程'
  4. 八步名称枚举完整性 (1-8 全量)
  5. 六飞轮 valid_names 枚举 (6个) + illegal_names 非法项存在
  6. MECE 四维度代码完整 (M/E_exec/C/E_env)
  7. stage_transition_constraints 非空
  8. PIPL 合规声明存在 (_meta.privacy_note)
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SCHEMA_PATH = REPO_ROOT / "pipeline-data" / "student-progress-schema.json"

REQUIRED_SCHEMA_TYPES = {
    "student_assessment_record",
    "stage_transition_record",
    "coaching_effectiveness_record",
    "student_progress_summary",
}
REQUIRED_EIGHT_STEP_NAMES = {
    "1": "穿透", "2": "提取", "3": "整理", "4": "审题",
    "5": "流程", "6": "批改", "7": "分析", "8": "估分",
}
REQUIRED_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
ILLEGAL_FLYWHEEL_NAMES = {"错题飞轮", "笔记飞轮", "阅读飞轮", "实践飞轮"}
REQUIRED_MECE_CODES = {"M", "E_exec", "C", "E_env"}

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


def main() -> None:
    print("=" * 60)
    print("  学生进度 schema 验证 v1.0")
    print("=" * 60)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not SCHEMA_PATH.exists():
        fail(f"找不到文件: {SCHEMA_PATH}")
        sys.exit(1)
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    ok("student-progress-schema.json 加载成功")

    # [2] schema_definitions 完整性
    print("\n[2] schema_definitions 四类型完整性")
    defs = set(schema.get("schema_definitions", {}).keys())
    missing = REQUIRED_SCHEMA_TYPES - defs
    extra = defs - REQUIRED_SCHEMA_TYPES
    if missing:
        fail(f"缺少 schema 类型: {missing}")
    else:
        ok(f"四种 schema 类型全量覆盖: {sorted(defs)} ✓")

    # [3] ⑤守护
    print("\n[3] ⑤守护验证")
    vr = schema.get("validation_rules", {})
    eight_constraints = vr.get("eight_step_name_constraints", {})
    five_note = eight_constraints.get("five", "")
    if "流程" in five_note:
        ok(f"⑤守护: eight_step_id=5 标注 '流程' ✓")
    else:
        fail(f"⑤守护: five 字段内容='{five_note}' 未包含 '流程'")

    # [4] 八步名称枚举 (1-8)
    print("\n[4] 八步名称枚举 1-8 全量")
    all_names = eight_constraints.get("all_names", {})
    for sid, expected_name in REQUIRED_EIGHT_STEP_NAMES.items():
        actual = all_names.get(sid, "?")
        if actual == expected_name:
            ok(f"步 {sid} = '{actual}' ✓")
        else:
            fail(f"步 {sid} = '{actual}' 期望 '{expected_name}'")

    # [5] 六飞轮合规
    print("\n[5] 六飞轮 valid_names + illegal_names")
    fw_constraints = vr.get("six_flywheel_name_constraints", {})
    valid = set(fw_constraints.get("valid_names", []))
    illegal = set(fw_constraints.get("illegal_names", []))
    missing_valid = REQUIRED_FLYWHEEL_NAMES - valid
    if missing_valid:
        fail(f"valid_names 缺少: {missing_valid}")
    elif len(valid) == 6:
        ok(f"六飞轮 valid_names 6个全覆盖 ✓")
    else:
        fail(f"valid_names 数量 {len(valid)} ≠ 6")
    if ILLEGAL_FLYWHEEL_NAMES.issubset(illegal):
        ok(f"illegal_names 包含全部 4 个非法变体 ✓")
    else:
        missing_ill = ILLEGAL_FLYWHEEL_NAMES - illegal
        fail(f"illegal_names 缺少: {missing_ill}")

    # [6] MECE 四维度代码
    print("\n[6] MECE 四维度代码完整性")
    mece_codes = set(vr.get("mece_dimension_codes", {}).keys())
    missing_mece = REQUIRED_MECE_CODES - mece_codes
    if missing_mece:
        fail(f"mece_dimension_codes 缺少: {missing_mece}")
    else:
        ok(f"MECE 四维度代码 M/E_exec/C/E_env 全量 ✓")

    # [7] stage_transition_constraints 非空
    print("\n[7] stage_transition_constraints 非空")
    stc = vr.get("stage_transition_constraints", [])
    if len(stc) >= 3:
        ok(f"stage_transition_constraints 含 {len(stc)} 条约束 ✓")
    else:
        fail(f"stage_transition_constraints 仅 {len(stc)} 条，期望 ≥ 3")

    # [8] PIPL 合规声明
    print("\n[8] PIPL 合规声明")
    privacy = schema.get("_meta", {}).get("privacy_note", "")
    if "PIPL" in privacy and "匿名" in privacy:
        ok(f"PIPL 合规声明存在: '{privacy[:50]}...' ✓")
    else:
        fail(f"_meta.privacy_note 缺少 PIPL 合规声明")

    # ── 结果 ──────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    total = PASS_COUNT + FAIL_COUNT
    print(f"  结果: {PASS_COUNT}/{total} 通过 | {FAIL_COUNT} 失败")
    print("=" * 60)
    if FAIL_COUNT > 0:
        print("\n失败详情:")
        for e in ERRORS:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("  ✅ 学生进度 schema 验证 PASS — 全部道层规范合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
