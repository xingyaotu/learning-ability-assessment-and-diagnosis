#!/usr/bin/env python3
"""
道层测评分数解读规则 schema 验证脚本 v1.0
验证 pipeline-data/assessment-score-interpretation-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. theta_to_stage_mapping: 7个阶位映射 + stage_enum_guard 七阶全覆盖
  3. 每个阶位映射含 _dao_guard
  4. mece_dimension_interpretation: 4维度全覆盖 + mece_enum_guard
  5. 每个 MECE 维度含 _dao_guard + coaching_focus_when_low
  6. flywheel_interpretation: 六飞轮全覆盖 + _dao_guard
  7. cir-mid-stage-low-E_exec 含'流程' ⑤守护
  8. interpretation_output_schema: stage enum 七阶 + dimension enum MECE
  9. theta_values_excluded_from_output 字段存在
  10. validation_rules: 七阶/MECE/六飞轮/theta排除规则/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
INTERP_PATH = REPO_ROOT / "pipeline-data" / "assessment-score-interpretation-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}

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
    print("  测评分数解读规则 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not INTERP_PATH.exists():
        fail(f"找不到文件: {INTERP_PATH}")
        sys.exit(1)
    data = json.loads(INTERP_PATH.read_text(encoding="utf-8"))
    ok("assessment-score-interpretation-schema.json 加载成功")

    tsm = data.get("theta_to_stage_mapping", {})
    mdi = data.get("mece_dimension_interpretation", {})
    fi = data.get("flywheel_interpretation", {})
    cir = data.get("composite_interpretation_rules", {}).get("rules", [])
    ios = data.get("interpretation_output_schema", {}).get("fields", {})
    vr = data.get("validation_rules", {})

    # [2] theta_to_stage_mapping 7个阶位 + stage_enum_guard
    print("\n[2] theta_to_stage_mapping 7个阶位 + stage_enum_guard")
    mapping_rules = tsm.get("mapping_rules", [])
    mapped_stages = {r.get("stage") for r in mapping_rules}
    missing_stages = VALID_STAGE_NAMES - mapped_stages
    if missing_stages:
        fail(f"theta→stage 映射缺少阶位: {missing_stages}")
    else:
        ok(f"theta→stage 7个阶位映射全覆盖 ✓")
    stage_guard = set(tsm.get("stage_enum_guard", []))
    if stage_guard == VALID_STAGE_NAMES:
        ok("theta_to_stage_mapping.stage_enum_guard 七阶全覆盖 ✓")
    else:
        fail(f"stage_enum_guard {stage_guard} ≠ {VALID_STAGE_NAMES}")

    # [3] 每个阶位映射含 _dao_guard
    print("\n[3] 每个阶位映射含 _dao_guard")
    for r in mapping_rules:
        stage = r.get("stage", "?")
        guard = r.get("_dao_guard", "")
        if guard:
            ok(f"stage '{stage}': _dao_guard 存在 ✓")
        else:
            fail(f"stage '{stage}': _dao_guard 缺失")

    # [4] mece_dimension_interpretation 4维度 + mece_enum_guard
    print("\n[4] mece_dimension_interpretation 4维度 + mece_enum_guard")
    dims = mdi.get("dimensions", {})
    found_dims = set(dims.keys())
    missing_dims = MECE_DIMENSIONS - found_dims
    if missing_dims:
        fail(f"MECE 解读缺少维度: {missing_dims}")
    else:
        ok(f"MECE 四维度解读全覆盖 ✓ {sorted(found_dims)}")
    mece_guard = set(mdi.get("mece_enum_guard", []))
    if mece_guard == MECE_DIMENSIONS:
        ok("mece_dimension_interpretation.mece_enum_guard 四维度全覆盖 ✓")
    else:
        fail(f"mece_enum_guard {mece_guard} ≠ {MECE_DIMENSIONS}")

    # [5] 每个 MECE 维度含 _dao_guard + coaching_focus_when_low
    print("\n[5] 每个 MECE 维度含 _dao_guard + coaching_focus_when_low")
    for dim_key, dim_obj in dims.items():
        guard = dim_obj.get("_dao_guard", "")
        focus = dim_obj.get("coaching_focus_when_low", "")
        if guard:
            ok(f"MECE {dim_key}: _dao_guard 存在 ✓")
        else:
            fail(f"MECE {dim_key}: _dao_guard 缺失")
        if focus:
            ok(f"MECE {dim_key}: coaching_focus_when_low 存在 ✓")
        else:
            fail(f"MECE {dim_key}: coaching_focus_when_low 缺失")

    # [6] flywheel_interpretation 六飞轮 + _dao_guard
    print("\n[6] flywheel_interpretation 六飞轮 + _dao_guard")
    fw_keys = set(fi.get("flywheels", {}).keys())
    missing_fw = VALID_FLYWHEEL_NAMES - fw_keys
    if missing_fw:
        fail(f"飞轮解读缺少飞轮: {missing_fw}")
    else:
        ok(f"飞轮解读六飞轮全覆盖 ✓ {sorted(fw_keys)}")
    fi_guard = fi.get("_dao_guard", "")
    if "六飞轮" in fi_guard:
        ok("flywheel_interpretation._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"flywheel_interpretation._dao_guard='{fi_guard}' 未含'六飞轮'")

    # [7] cir-mid-stage-low-E_exec 含'流程' ⑤守护
    print("\n[7] cir-mid-stage-low-E_exec ⑤守护 — _dao_guard 含'流程'")
    exec_rule = next((r for r in cir if r.get("rule_id") == "cir-mid-stage-low-E_exec"), None)
    if exec_rule:
        exec_guard = exec_rule.get("_dao_guard", "")
        if "流程" in exec_guard:
            ok("cir-mid-stage-low-E_exec._dao_guard 含'流程' ⑤守护 ✓")
        else:
            fail(f"cir-mid-stage-low-E_exec._dao_guard='{exec_guard}' 未含'流程'")
    else:
        fail("composite_interpretation_rules 缺少 cir-mid-stage-low-E_exec")

    # [8] interpretation_output_schema stage enum 七阶 + dimension enum MECE
    print("\n[8] interpretation_output_schema stage/dimension enum")
    stage_enum = set(ios.get("stage_interpretation", {}).get("properties", {}).get("stage", {}).get("enum", []))
    if stage_enum == VALID_STAGE_NAMES:
        ok("interpretation_output.stage_interpretation.stage enum 七阶全覆盖 ✓")
    else:
        fail(f"stage_interpretation.stage enum {stage_enum} ≠ {VALID_STAGE_NAMES}")
    dim_enum = set(ios.get("primary_bottleneck_interpretation", {}).get("properties", {}).get("dimension", {}).get("enum", []))
    if dim_enum == MECE_DIMENSIONS:
        ok("interpretation_output.primary_bottleneck_interpretation.dimension enum MECE 四维度 ✓")
    else:
        fail(f"dimension enum {dim_enum} ≠ {MECE_DIMENSIONS}")

    # [9] theta_values_excluded_from_output 字段
    print("\n[9] theta_values_excluded_from_output 字段")
    if "theta_values_excluded_from_output" in ios:
        ok("interpretation_output.theta_values_excluded_from_output 字段存在 ✓")
    else:
        fail("interpretation_output.theta_values_excluded_from_output 字段缺失")

    # [10] validation_rules
    print("\n[10] validation_rules 合规")
    stage_vr = set(vr.get("seven_stage_valid_names", []))
    if stage_vr == VALID_STAGE_NAMES:
        ok("validation_rules.seven_stage_valid_names 七阶全覆盖 ✓")
    else:
        fail(f"seven_stage_valid_names {stage_vr} ≠ {VALID_STAGE_NAMES}")
    mece_vr = set(vr.get("mece_dimension_codes", []))
    if mece_vr == MECE_DIMENSIONS:
        ok("validation_rules.mece_dimension_codes MECE 四维度 ✓")
    else:
        fail(f"mece_dimension_codes {mece_vr} ≠ {MECE_DIMENSIONS}")
    fw_vr = set(vr.get("six_flywheel_valid_names", []))
    if fw_vr == VALID_FLYWHEEL_NAMES:
        ok("validation_rules.six_flywheel_valid_names 六飞轮全覆盖 ✓")
    else:
        fail(f"six_flywheel_valid_names {fw_vr} ≠ {VALID_FLYWHEEL_NAMES}")
    stage_count = vr.get("stage_count", 0)
    if stage_count == 7:
        ok(f"validation_rules.stage_count={stage_count} = 7 ✓")
    else:
        fail(f"validation_rules.stage_count={stage_count} ≠ 7")
    theta_rule = vr.get("theta_exclusion_rule", "")
    if "theta_values_excluded_from_output" in theta_rule:
        ok("validation_rules.theta_exclusion_rule θ排除规则存在 ✓")
    else:
        fail(f"validation_rules.theta_exclusion_rule='{theta_rule}' 未含排除规则")
    pipl_meta = data.get("_meta", {}).get("pipl_note", "")
    if "PIPL" in pipl_meta and "匿名" in pipl_meta:
        ok("_meta.pipl_note PIPL 合规声明 ✓")
    else:
        fail("_meta.pipl_note 缺少 PIPL 合规声明")
    pipl_vr = vr.get("pipl_constraints", "")
    if "PIPL" in pipl_vr and "匿名" in pipl_vr:
        ok("validation_rules.pipl_constraints 存在 ✓")
    else:
        fail("validation_rules.pipl_constraints 缺失或不完整")

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
        print("  ✅ 测评分数解读规则 schema 验证 PASS — 七阶映射/MECE解读/六飞轮/⑤守护/θ排除/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
