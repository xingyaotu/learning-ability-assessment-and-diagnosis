#!/usr/bin/env python3
"""
道层 IRT 题目参数校准更新 schema 验证脚本 v1.0
验证 pipeline-data/assessment-item-calibration-update-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. calibration_trigger_conditions: 4个触发 + cat-drift-detected _dao_guard
  3. calibration_process: 8步 + _dao_guard 含'MECE'+'七阶'
  4. calibration_quality_gates: 5个门控 + 关键门控 _dao_guard
  5. qg-stage-threshold._dao_guard 含'七阶'; qg-mece-dimension._dao_guard 含'MECE'
  6. qg-flywheel-tool._dao_guard 含'六飞轮'
  7. calibration_record_schema 6个必填字段
  8. trigger_id enum 4个; irt_model_used enum [1PL/2PL/3PL/mixed]
  9. version_management _dao_guard 含'七阶'+'MECE'
  10. validation_rules: 七阶/MECE/六飞轮/匿名化/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CALIB_PATH = REPO_ROOT / "pipeline-data" / "assessment-item-calibration-update-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
VALID_TRIGGER_IDS = {
    "cat-sample-threshold", "cat-scheduled-quarterly",
    "cat-drift-detected", "cat-new-items"
}
VALID_GATE_IDS = {
    "qg-param-range", "qg-fit", "qg-stage-threshold",
    "qg-mece-dimension", "qg-flywheel-tool"
}
REQUIRED_CALIB_FIELDS = {
    "calibration_id", "trigger_id", "calibration_date",
    "items_recalibrated_count", "irt_model_used", "all_quality_gates_passed"
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


def main() -> None:
    print("=" * 62)
    print("  IRT 题目参数校准更新 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not CALIB_PATH.exists():
        fail(f"找不到文件: {CALIB_PATH}")
        sys.exit(1)
    data = json.loads(CALIB_PATH.read_text(encoding="utf-8"))
    ok("assessment-item-calibration-update-schema.json 加载成功")

    triggers = data.get("calibration_trigger_conditions", {}).get("triggers", [])
    process = data.get("calibration_process", {})
    gates = data.get("calibration_quality_gates", {}).get("gates", [])
    rec_fields = data.get("calibration_record_schema", {}).get("fields", {})
    vm = data.get("version_management", {})
    vr = data.get("validation_rules", {})

    # [2] calibration_trigger_conditions 4个 + cat-drift-detected _dao_guard
    print("\n[2] calibration_trigger_conditions 4个触发 + cat-drift-detected _dao_guard")
    found_triggers = {t.get("trigger_id") for t in triggers}
    missing_triggers = VALID_TRIGGER_IDS - found_triggers
    if missing_triggers:
        fail(f"缺少触发条件: {missing_triggers}")
    else:
        ok(f"4个触发条件全覆盖 ✓ {sorted(found_triggers)}")
    drift = next((t for t in triggers if t.get("trigger_id") == "cat-drift-detected"), None)
    if drift and drift.get("_dao_guard"):
        ok("cat-drift-detected._dao_guard 存在 ✓")
    else:
        fail("cat-drift-detected._dao_guard 缺失")

    # [3] calibration_process 8步 + _dao_guard
    print("\n[3] calibration_process 8步 + _dao_guard 含'MECE'+'七阶'")
    steps = process.get("steps", [])
    if len(steps) >= 8:
        ok(f"calibration_process.steps {len(steps)}步 ≥ 8 ✓")
    else:
        fail(f"calibration_process.steps {len(steps)} < 8")
    proc_guard = process.get("_dao_guard", "")
    for kw in ["MECE", "七阶"]:
        if kw in proc_guard:
            ok(f"calibration_process._dao_guard 含'{kw}' ✓")
        else:
            fail(f"calibration_process._dao_guard='{proc_guard}' 未含'{kw}'")

    # [4] calibration_quality_gates 5个门控
    print("\n[4] calibration_quality_gates 5个门控")
    found_gates = {g.get("gate_id") for g in gates}
    missing_gates = VALID_GATE_IDS - found_gates
    if missing_gates:
        fail(f"缺少质量门控: {missing_gates}")
    else:
        ok(f"5个质量门控全覆盖 ✓ {sorted(found_gates)}")

    # [5] 关键门控 _dao_guard
    print("\n[5] 关键门控 _dao_guard")
    gate_map = {g.get("gate_id"): g for g in gates}
    stage_gate = gate_map.get("qg-stage-threshold", {})
    if "七阶" in stage_gate.get("_dao_guard", ""):
        ok("qg-stage-threshold._dao_guard 含'七阶' ✓")
    else:
        fail(f"qg-stage-threshold._dao_guard 未含'七阶'")
    mece_gate = gate_map.get("qg-mece-dimension", {})
    if "MECE" in mece_gate.get("_dao_guard", ""):
        ok("qg-mece-dimension._dao_guard 含'MECE' ✓")
    else:
        fail(f"qg-mece-dimension._dao_guard 未含'MECE'")

    # [6] qg-flywheel-tool._dao_guard 含'六飞轮'
    print("\n[6] qg-flywheel-tool._dao_guard 含'六飞轮'")
    fw_gate = gate_map.get("qg-flywheel-tool", {})
    if "六飞轮" in fw_gate.get("_dao_guard", ""):
        ok("qg-flywheel-tool._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"qg-flywheel-tool._dao_guard 未含'六飞轮'")
    fw_valid = set(fw_gate.get("valid_flywheels", []))
    if fw_valid == VALID_FLYWHEEL_NAMES:
        ok("qg-flywheel-tool.valid_flywheels 六飞轮全覆盖 ✓")
    else:
        fail(f"qg-flywheel-tool.valid_flywheels {fw_valid} ≠ {VALID_FLYWHEEL_NAMES}")

    # [7] calibration_record_schema 6个必填字段
    print("\n[7] calibration_record_schema 6个必填字段")
    vr_req = set(vr.get("required_calibration_fields", []))
    if vr_req == REQUIRED_CALIB_FIELDS:
        ok("validation_rules.required_calibration_fields 6字段全覆盖 ✓")
    else:
        missing_rf = REQUIRED_CALIB_FIELDS - vr_req
        fail(f"required_calibration_fields 缺少: {missing_rf}")
    for fname in REQUIRED_CALIB_FIELDS:
        if fname in rec_fields:
            ok(f"calibration_record_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"calibration_record_schema.fields.{fname} 缺失")

    # [8] trigger_id enum + irt_model_used enum
    print("\n[8] trigger_id enum + irt_model_used enum")
    trig_enum = set(rec_fields.get("trigger_id", {}).get("enum", []))
    if trig_enum == VALID_TRIGGER_IDS:
        ok("trigger_id enum 4个触发全覆盖 ✓")
    else:
        fail(f"trigger_id enum {trig_enum} ≠ {VALID_TRIGGER_IDS}")
    irt_enum = set(rec_fields.get("irt_model_used", {}).get("enum", []))
    expected_irt = {"1PL", "2PL", "3PL", "mixed"}
    if irt_enum == expected_irt:
        ok("irt_model_used enum [1PL/2PL/3PL/mixed] ✓")
    else:
        fail(f"irt_model_used enum {irt_enum} ≠ {expected_irt}")

    # [9] version_management _dao_guard 含'七阶'+'MECE'
    print("\n[9] version_management _dao_guard 含'七阶'+'MECE'")
    vm_guard = vm.get("_dao_guard", "")
    for kw in ["七阶", "MECE"]:
        if kw in vm_guard:
            ok(f"version_management._dao_guard 含'{kw}' ✓")
        else:
            fail(f"version_management._dao_guard='{vm_guard}' 未含'{kw}'")

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
    anon_rule = vr.get("anonymization_rule", "")
    if "匿名" in anon_rule or "anonymiz" in anon_rule.lower():
        ok("validation_rules.anonymization_rule 匿名化规则存在 ✓")
    else:
        fail(f"validation_rules.anonymization_rule='{anon_rule}' 缺少匿名化规则")
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
        print("  ✅ IRT 题目参数校准更新 schema 验证 PASS — 4触发/8步/5门控/七阶/MECE/六飞轮/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
