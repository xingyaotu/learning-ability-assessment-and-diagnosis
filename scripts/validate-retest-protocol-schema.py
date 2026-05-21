#!/usr/bin/env python3
"""
道层测评复测协议 schema 验证脚本 v1.0
验证 pipeline-data/assessment-retest-protocol-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. retest_trigger_conditions: 5个触发条件 + _dao_guard
  3. retest_interval_rules: 最短间隔 ≥ 14天 + 3种 IRT 模型
  4. retest_record_schema 8个必填字段
  5. original_stage/retest_stage enum 七阶全覆盖
  6. trigger_id enum 5个触发
  7. flywheel_improvements enum 六飞轮 + _dao_guard
  8. retest_comparison_rules: regression_alert 含'七阶' + plateau_diagnosis 含'MECE'
  9. minor_retest_rules: [HALT-CSO] + _dao_guard
  10. validation_rules: 七阶/MECE/六飞轮/间隔/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
RETEST_PATH = REPO_ROOT / "pipeline-data" / "assessment-retest-protocol-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
VALID_TRIGGER_IDS = {
    "rtt-stage-advance", "rtt-scheduled", "rtt-coaching-milestone",
    "rtt-plateau-detection", "rtt-student-request"
}
REQUIRED_RETEST_FIELDS = {
    "retest_id", "student_id", "original_session_id", "retest_session_id",
    "trigger_id", "days_since_original", "original_stage", "retest_stage"
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
    print("  测评复测协议 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not RETEST_PATH.exists():
        fail(f"找不到文件: {RETEST_PATH}")
        sys.exit(1)
    data = json.loads(RETEST_PATH.read_text(encoding="utf-8"))
    ok("assessment-retest-protocol-schema.json 加载成功")

    triggers = data.get("retest_trigger_conditions", {}).get("triggers", [])
    intervals = data.get("retest_interval_rules", {})
    rec_fields = data.get("retest_record_schema", {}).get("fields", {})
    comparison = data.get("retest_comparison_rules", {})
    minor_rules = data.get("minor_retest_rules", {}).get("under_14_requirements", {})
    vr = data.get("validation_rules", {})

    # [2] retest_trigger_conditions 5个 + _dao_guard
    print("\n[2] retest_trigger_conditions 5个触发 + _dao_guard")
    found_triggers = {t.get("trigger_id") for t in triggers}
    missing_triggers = VALID_TRIGGER_IDS - found_triggers
    if missing_triggers:
        fail(f"缺少触发条件: {missing_triggers}")
    else:
        ok(f"5个触发条件全覆盖 ✓ {sorted(found_triggers)}")
    for t in triggers:
        tid = t.get("trigger_id", "?")
        guard = t.get("_dao_guard", "")
        if guard:
            ok(f"{tid}: _dao_guard 存在 ✓")

    # [3] retest_interval_rules 最短间隔 + 3种 IRT
    print("\n[3] retest_interval_rules 最短间隔 ≥ 14天 + IRT 模型")
    min_intervals = intervals.get("minimum_intervals", {})
    default_min = min_intervals.get("default_min_days", 0)
    if default_min >= 14:
        ok(f"default_min_days={default_min} ≥ 14 ✓")
    else:
        fail(f"default_min_days={default_min} < 14")
    irt_models = min_intervals.get("by_irt_model", {})
    for model in ["1PL", "2PL", "3PL"]:
        if model in irt_models:
            ok(f"by_irt_model.{model} 存在 ✓")
        else:
            fail(f"by_irt_model.{model} 缺失")

    # [4] retest_record_schema 8个必填字段
    print("\n[4] retest_record_schema 8个必填字段")
    vr_req = set(vr.get("required_retest_fields", []))
    if vr_req == REQUIRED_RETEST_FIELDS:
        ok("validation_rules.required_retest_fields 8字段全覆盖 ✓")
    else:
        missing_rf = REQUIRED_RETEST_FIELDS - vr_req
        fail(f"required_retest_fields 缺少: {missing_rf}")
    for fname in REQUIRED_RETEST_FIELDS:
        if fname in rec_fields:
            ok(f"retest_record_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"retest_record_schema.fields.{fname} 缺失")

    # [5] original_stage/retest_stage enum 七阶
    print("\n[5] original_stage/retest_stage enum 七阶全覆盖")
    orig_enum = set(rec_fields.get("original_stage", {}).get("enum", []))
    ret_enum = set(rec_fields.get("retest_stage", {}).get("enum", []))
    if orig_enum == VALID_STAGE_NAMES:
        ok("original_stage enum 七阶全覆盖 ✓")
    else:
        fail(f"original_stage enum {orig_enum} ≠ {VALID_STAGE_NAMES}")
    if ret_enum == VALID_STAGE_NAMES:
        ok("retest_stage enum 七阶全覆盖 ✓")
    else:
        fail(f"retest_stage enum {ret_enum} ≠ {VALID_STAGE_NAMES}")

    # [6] trigger_id enum 5个
    print("\n[6] trigger_id enum 5个触发")
    trig_enum = set(rec_fields.get("trigger_id", {}).get("enum", []))
    if trig_enum == VALID_TRIGGER_IDS:
        ok("trigger_id enum 5个触发全覆盖 ✓")
    else:
        fail(f"trigger_id enum {trig_enum} ≠ {VALID_TRIGGER_IDS}")

    # [7] flywheel_improvements enum 六飞轮 + _dao_guard
    print("\n[7] flywheel_improvements enum 六飞轮 + _dao_guard")
    fw_items = rec_fields.get("flywheel_improvements", {}).get("items", {})
    fw_enum = set(fw_items.get("enum", []))
    if fw_enum == VALID_FLYWHEEL_NAMES:
        ok("flywheel_improvements.items enum 六飞轮全覆盖 ✓")
    else:
        fail(f"flywheel_improvements enum {fw_enum} ≠ {VALID_FLYWHEEL_NAMES}")
    fw_guard = rec_fields.get("flywheel_improvements", {}).get("_dao_guard", "")
    if "六飞轮" in fw_guard:
        ok("flywheel_improvements._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"flywheel_improvements._dao_guard='{fw_guard}' 未含'六飞轮'")

    # [8] retest_comparison_rules _dao_guard
    print("\n[8] retest_comparison_rules 退步预警+停滞诊断 _dao_guard")
    regress_guard = comparison.get("regression_alert_rule", {}).get("_dao_guard", "")
    if "七阶" in regress_guard:
        ok("regression_alert_rule._dao_guard 含'七阶' ✓")
    else:
        fail(f"regression_alert_rule._dao_guard='{regress_guard}' 未含'七阶'")
    plateau_guard = comparison.get("plateau_diagnosis_rule", {}).get("_dao_guard", "")
    if "MECE" in plateau_guard:
        ok("plateau_diagnosis_rule._dao_guard 含'MECE' ✓")
    else:
        fail(f"plateau_diagnosis_rule._dao_guard='{plateau_guard}' 未含'MECE'")

    # [9] minor_retest_rules [HALT-CSO] + _dao_guard
    print("\n[9] minor_retest_rules [HALT-CSO] + _dao_guard")
    halt = minor_rules.get("halt_if_not_confirmed", "")
    if "[HALT-CSO]" in halt:
        ok("minor_retest_rules.halt_if_not_confirmed 含'[HALT-CSO]' ✓")
    else:
        fail(f"halt_if_not_confirmed='{halt}' 未含'[HALT-CSO]'")
    mrr_guard = minor_rules.get("_dao_guard", "")
    if "PIPL" in mrr_guard and "[HALT-CSO]" in mrr_guard:
        ok("minor_retest_rules._dao_guard 含'PIPL'+'[HALT-CSO]' ✓")
    else:
        fail(f"minor_retest_rules._dao_guard='{mrr_guard}' 未含'PIPL'或'[HALT-CSO]'")

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
    min_int = vr.get("min_interval_days", 0)
    if min_int >= 14:
        ok(f"validation_rules.min_interval_days={min_int} ≥ 14 ✓")
    else:
        fail(f"validation_rules.min_interval_days={min_int} < 14")
    pipl14 = vr.get("pipl_article14_guard", "")
    if "[HALT-CSO]" in pipl14:
        ok("validation_rules.pipl_article14_guard 含'[HALT-CSO]' ✓")
    else:
        fail(f"validation_rules.pipl_article14_guard='{pipl14}' 未含'[HALT-CSO]'")
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
        print("  ✅ 测评复测协议 schema 验证 PASS — 触发条件/间隔规则/七阶/MECE/六飞轮/HALT-CSO/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
