#!/usr/bin/env python3
"""
道层测评报告 schema 验证脚本 v1.0
验证 pipeline-data/report-output-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. report_schema.assessment_report 完整性 (核心字段存在)
  3. report_type 枚举 (initial/progress/comprehensive)
  4. portal 枚举 (4个门户)
  5. MECE 四维度字段完整 (M/E_execution/C/E_environment)
  6. ⑤守护: report_generation_rules.stage_name_constraints.eight_step_name_for_5 == '流程'
  7. 七阶名称枚举合规
  8. 六飞轮名称枚举合规
  9. portal_field_visibility 4门户全覆盖
 10. PIPL 合规声明
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REPORT_PATH = REPO_ROOT / "pipeline-data" / "report-output-schema.json"

VALID_PORTALS = {"xyt-student", "xyt-parent", "xyt-coach", "xyt-hq"}
VALID_STAGE_NAMES = ["不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"]
VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_REPORT_TYPES = {"initial", "progress", "comprehensive"}
REQUIRED_MECE_DIMS = {"M_motivation", "E_execution", "C_capability", "E_environment"}

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
    print("=" * 62)
    print("  测评报告 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not REPORT_PATH.exists():
        fail(f"找不到文件: {REPORT_PATH}")
        sys.exit(1)
    schema = json.loads(REPORT_PATH.read_text(encoding="utf-8"))
    ok("report-output-schema.json 加载成功")

    # [2] assessment_report 核心字段存在性
    print("\n[2] assessment_report 核心字段")
    ar = schema.get("report_schema", {}).get("assessment_report", {})
    fields = ar.get("fields", {})
    required_fields = {"report_id", "student_id", "report_type", "portal", "subject",
                       "overall_stage", "mece_profile", "coaching_recommendations"}
    for f in required_fields:
        if f in fields:
            ok(f"字段 '{f}' 存在 ✓")
        else:
            fail(f"字段 '{f}' 缺失")

    # [3] report_type 枚举
    print("\n[3] report_type 枚举")
    rt_field = fields.get("report_type", {})
    actual_enum = set(rt_field.get("enum", []))
    if actual_enum == VALID_REPORT_TYPES:
        ok(f"report_type 枚举合规: {sorted(actual_enum)} ✓")
    else:
        fail(f"report_type 枚举 {actual_enum} ≠ {VALID_REPORT_TYPES}")

    # [4] portal 枚举
    print("\n[4] portal 枚举 (4门户)")
    portal_field = fields.get("portal", {})
    actual_portals = set(portal_field.get("enum", []))
    if actual_portals == VALID_PORTALS:
        ok(f"portal 枚举合规: {sorted(actual_portals)} ✓")
    else:
        fail(f"portal 枚举 {actual_portals} ≠ {VALID_PORTALS}")

    # [5] MECE 四维度完整
    print("\n[5] MECE 四维度完整性")
    mece = fields.get("mece_profile", {}).get("fields", {})
    for dim in REQUIRED_MECE_DIMS:
        if dim in mece:
            ok(f"MECE 维度 '{dim}' 存在 ✓")
        else:
            fail(f"MECE 维度 '{dim}' 缺失")

    # [6] ⑤守护
    print("\n[6] ⑤守护验证")
    grr = schema.get("report_generation_rules", {})
    stage_constraints = grr.get("stage_name_constraints", {})
    step5_name = stage_constraints.get("eight_step_name_for_5", "")
    if step5_name == "流程":
        ok("eight_step_name_for_5='流程' ⑤守护 ✓")
    else:
        fail(f"eight_step_name_for_5='{step5_name}' ≠ '流程'")

    # [7] 七阶名称枚举
    print("\n[7] 七阶名称枚举")
    actual_stage_names = stage_constraints.get("valid_stage_names", [])
    if actual_stage_names == VALID_STAGE_NAMES:
        ok(f"七阶名称枚举合规: {actual_stage_names} ✓")
    else:
        fail(f"七阶名称枚举 {actual_stage_names} ≠ {VALID_STAGE_NAMES}")

    # [8] 六飞轮名称枚举
    print("\n[8] 六飞轮名称枚举")
    fw_constraints = grr.get("flywheel_name_constraints", {})
    actual_fw = set(fw_constraints.get("valid_flywheel_names", []))
    missing_fw = VALID_FLYWHEEL_NAMES - actual_fw
    if missing_fw:
        fail(f"valid_flywheel_names 缺少: {missing_fw}")
    elif len(actual_fw) == 6:
        ok(f"六飞轮 6个全覆盖 ✓")
    else:
        fail(f"valid_flywheel_names 数量 {len(actual_fw)} ≠ 6")

    # [9] portal_field_visibility 4门户
    print("\n[9] portal_field_visibility 4门户全覆盖")
    pfv = grr.get("portal_field_visibility", {})
    for portal in VALID_PORTALS:
        if portal in pfv:
            ok(f"portal '{portal}' 有字段可见性配置 ✓")
        else:
            fail(f"portal '{portal}' 缺少字段可见性配置")

    # [10] PIPL 合规声明
    print("\n[10] PIPL 合规声明")
    privacy = schema.get("_meta", {}).get("privacy_note", "")
    if "PIPL" in privacy:
        ok(f"PIPL 合规声明存在 ✓")
    else:
        fail("_meta.privacy_note 缺少 PIPL 合规声明")

    # ── 结果 ──────────────────────────────────────────────────────
    print(f"\n{'=' * 62}")
    total = PASS_COUNT + FAIL_COUNT
    print(f"  结果: {PASS_COUNT}/{total} 通过 | {FAIL_COUNT} 失败")
    print("=" * 62)
    if FAIL_COUNT > 0:
        print("\n失败详情:")
        for e in ERRORS:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("  ✅ 测评报告 schema 验证 PASS — 全部道层规范合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
