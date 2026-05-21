#!/usr/bin/env python3
"""
道层测评题库 schema 验证脚本 v1.0
验证 pipeline-data/assessment-item-bank-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. item_schema 核心字段完整性
  3. item_type enum 合规
  4. irt_model enum 合规
  5. tool_item_counts: 22工具全覆盖
  6. total_items 求和 == 368
  7. total_dimensions 求和 == 92
  8. IRT 模型一致性 (jumeq_economy/camiq_monetary → 1PL; mastery_stages → 3PL)
  9. flywheel_dimension_names 六飞轮完整覆盖
  10. validation_rules IRT 约束完整
  11. validation_rules 六飞轮守护
  12. PIPL 合规声明
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ITEM_BANK_PATH = REPO_ROOT / "pipeline-data" / "assessment-item-bank-schema.json"

REQUIRED_22_TOOLS = {
    "assess_mece_motivation", "assess_mece_execution",
    "assess_mece_capability", "assess_mece_environment",
    "assess_mastery_stages",
    "assess_jumeq_jobplacement", "assess_jumeq_university",
    "assess_jumeq_major", "assess_jumeq_economy", "assess_jumeq_qualification",
    "assess_camiq_character", "assess_camiq_aptitude",
    "assess_camiq_monetary", "assess_camiq_interest", "assess_camiq_qualification",
    "assess_flywheels_self_eval",
    "assess_fireup_family", "assess_fireup_individual",
    "assess_fireup_resources", "assess_fireup_ecosystem",
    "assess_fireup_usability", "assess_fireup_pathways",
}
TOOLS_1PL = {"assess_jumeq_economy", "assess_camiq_monetary"}
TOOLS_3PL = {"assess_mastery_stages"}
VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
REQUIRED_ITEM_TYPES = {"likert_5", "likert_7", "multiple_choice", "forced_choice", "open_ended_scored"}
REQUIRED_IRT_MODELS = {"1PL", "2PL", "3PL"}

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
    print("  测评题库 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not ITEM_BANK_PATH.exists():
        fail(f"找不到文件: {ITEM_BANK_PATH}")
        sys.exit(1)
    data = json.loads(ITEM_BANK_PATH.read_text(encoding="utf-8"))
    ok("assessment-item-bank-schema.json 加载成功")

    schema_fields = data.get("item_schema", {}).get("fields", {})

    # [2] item_schema 核心字段
    print("\n[2] item_schema 核心字段完整性")
    required_fields = {"item_id", "tool_id", "dimension_id", "item_type", "irt_model", "irt_params", "stage_target", "content"}
    found_fields = set(schema_fields.keys())
    missing_f = required_fields - found_fields
    if missing_f:
        fail(f"item_schema 缺少字段: {missing_f}")
    else:
        ok(f"item_schema {len(schema_fields)}个字段 核心字段全覆盖 ✓")

    # irt_params properties
    irt_props = schema_fields.get("irt_params", {}).get("properties", {})
    for pname in ["a", "b", "c"]:
        if pname in irt_props:
            ok(f"irt_params.{pname} 存在 ✓")
        else:
            fail(f"irt_params.{pname} 缺失")

    # stage_target range
    st_min = schema_fields.get("stage_target", {}).get("minimum", 0)
    st_max = schema_fields.get("stage_target", {}).get("maximum", 0)
    if st_min == 1 and st_max == 7:
        ok("stage_target range [1,7] ✓")
    else:
        fail(f"stage_target range [{st_min},{st_max}] ≠ [1,7]")

    # [3] item_type enum
    print("\n[3] item_type enum 合规")
    item_type_enum = set(schema_fields.get("item_type", {}).get("enum", []))
    missing_types = REQUIRED_ITEM_TYPES - item_type_enum
    if missing_types:
        fail(f"item_type enum 缺少: {missing_types}")
    else:
        ok(f"item_type enum {len(item_type_enum)}个 全覆盖 ✓")

    # [4] irt_model enum
    print("\n[4] irt_model enum 合规")
    irt_model_enum = set(schema_fields.get("irt_model", {}).get("enum", []))
    missing_models = REQUIRED_IRT_MODELS - irt_model_enum
    if missing_models:
        fail(f"irt_model enum 缺少: {missing_models}")
    else:
        ok(f"irt_model enum {sorted(irt_model_enum)} ✓")

    # [5] tool_item_counts 22工具覆盖
    print("\n[5] tool_item_counts 22工具全覆盖")
    tool_list = data.get("tool_item_counts", {}).get("tools", [])
    found_tools = {t.get("tool_id") for t in tool_list}
    missing_tools = REQUIRED_22_TOOLS - found_tools
    if missing_tools:
        fail(f"tool_item_counts 缺少工具: {missing_tools}")
    else:
        ok(f"22工具全覆盖 ✓")

    extra_tools = found_tools - REQUIRED_22_TOOLS
    if extra_tools:
        fail(f"tool_item_counts 含未预期工具: {extra_tools}")
    else:
        ok("无多余工具 ✓")

    # [6] total_items 求和 == 368
    print("\n[6] total_items 求和验证")
    computed_total = sum(t.get("total_items", 0) for t in tool_list)
    declared_total = data.get("tool_item_counts", {}).get("totals", {}).get("total_items", 0)
    if computed_total == 368:
        ok(f"tool total_items 求和 = {computed_total} == 368 ✓")
    else:
        fail(f"tool total_items 求和 = {computed_total} ≠ 368")
    if declared_total == 368:
        ok(f"totals.total_items = {declared_total} ✓")
    else:
        fail(f"totals.total_items = {declared_total} ≠ 368")
    if computed_total == declared_total:
        ok("求和与声明一致 ✓")
    else:
        fail(f"求和({computed_total}) ≠ 声明({declared_total})")

    # [7] total_dimensions 求和 == 92
    print("\n[7] total_dimensions 求和验证")
    computed_dims = sum(t.get("dimensions", 0) for t in tool_list)
    declared_dims = data.get("tool_item_counts", {}).get("totals", {}).get("total_dimensions", 0)
    if computed_dims == 92:
        ok(f"dimensions 求和 = {computed_dims} == 92 ✓")
    else:
        fail(f"dimensions 求和 = {computed_dims} ≠ 92")
    if declared_dims == 92:
        ok(f"totals.total_dimensions = {declared_dims} ✓")
    else:
        fail(f"totals.total_dimensions = {declared_dims} ≠ 92")

    # [8] IRT 模型一致性
    print("\n[8] IRT 模型一致性验证")
    for t in tool_list:
        tid = t.get("tool_id")
        model = t.get("irt_model")
        if tid in TOOLS_1PL:
            if model == "1PL":
                ok(f"{tid}: irt_model='1PL' ✓")
            else:
                fail(f"{tid}: irt_model='{model}' 期望 '1PL'")
        elif tid in TOOLS_3PL:
            if model == "3PL":
                ok(f"{tid}: irt_model='3PL' ✓")
            else:
                fail(f"{tid}: irt_model='{model}' 期望 '3PL'")
        else:
            if model == "2PL":
                ok(f"{tid}: irt_model='2PL' ✓")
            else:
                fail(f"{tid}: irt_model='{model}' 期望 '2PL'")

    # [9] flywheel_dimension_names 六飞轮覆盖
    print("\n[9] flywheel_dimension_names 六飞轮守护")
    fw_mapping = data.get("flywheel_dimension_names", {}).get("mapping", {})
    fw_dim_names = set(fw_mapping.values())
    missing_fw = VALID_FLYWHEEL_NAMES - fw_dim_names
    if missing_fw:
        fail(f"flywheel_dimension_names 缺少飞轮: {missing_fw}")
    elif len(fw_dim_names) == 6:
        ok(f"六飞轮维度名称全覆盖 ✓ {sorted(fw_dim_names)}")
    else:
        fail(f"flywheel_dimension_names 数量 {len(fw_dim_names)} ≠ 6")

    # 六维度 key 检查
    if len(fw_mapping) == 6 and all(f"fw_dim_{i}" in fw_mapping for i in range(1, 7)):
        ok("fw_dim_1 ~ fw_dim_6 六个 key 全覆盖 ✓")
    else:
        fail(f"fw_dim 键不完整: {sorted(fw_mapping.keys())}")

    fw_guard = data.get("flywheel_dimension_names", {}).get("_dao_guard", "")
    if fw_guard and "六飞轮" in fw_guard:
        ok("flywheel_dimension_names _dao_guard 存在 ✓")
    else:
        fail("flywheel_dimension_names _dao_guard 缺失")

    # [10] validation_rules IRT 约束
    print("\n[10] validation_rules IRT 约束")
    vr = data.get("validation_rules", {})
    irt_constraints = vr.get("irt_model_constraints", {})
    for model in ["1PL", "2PL", "3PL"]:
        if model in irt_constraints:
            ok(f"irt_model_constraints.{model} 存在 ✓")
        else:
            fail(f"irt_model_constraints.{model} 缺失")

    # 1PL a_fixed=1.0 check
    a_fixed = irt_constraints.get("1PL", {}).get("a_fixed")
    if a_fixed == 1.0:
        ok("1PL a_fixed=1.0 ✓")
    else:
        fail(f"1PL a_fixed={a_fixed} ≠ 1.0")

    # 3PL c_range
    c_range = irt_constraints.get("3PL", {}).get("c_range", [])
    if c_range == [0.0, 0.35]:
        ok(f"3PL c_range={c_range} ✓")
    else:
        fail(f"3PL c_range={c_range} ≠ [0.0, 0.35]")

    # [11] six_flywheel_dim_names 守护
    print("\n[11] validation_rules 六飞轮守护")
    fw_valid = set(vr.get("six_flywheel_dim_names", []))
    missing_vr_fw = VALID_FLYWHEEL_NAMES - fw_valid
    if missing_vr_fw:
        fail(f"validation_rules.six_flywheel_dim_names 缺少: {missing_vr_fw}")
    elif len(fw_valid) == 6:
        ok("validation_rules.six_flywheel_dim_names 六飞轮全覆盖 ✓")
    else:
        fail(f"validation_rules.six_flywheel_dim_names 数量 {len(fw_valid)} ≠ 6")

    total_tools_check = vr.get("total_tools_constraint", "")
    if "22" in total_tools_check:
        ok("total_tools_constraint 包含 22 ✓")
    else:
        fail(f"total_tools_constraint='{total_tools_check}' 未包含 22")

    total_items_check = vr.get("total_items_constraint", "")
    if "368" in total_items_check:
        ok("total_items_constraint 包含 368 ✓")
    else:
        fail(f"total_items_constraint='{total_items_check}' 未包含 368")

    # [12] PIPL 合规
    print("\n[12] PIPL 合规")
    pipl = data.get("_meta", {}).get("pipl_note", "")
    if "PIPL" in pipl and "匿名" in pipl:
        ok("_meta.pipl_note PIPL 合规声明存在 ✓")
    else:
        fail("_meta.pipl_note 缺少 PIPL 合规声明")

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
        print("  ✅ 测评题库 schema 验证 PASS — 22工具×368题全配置合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
