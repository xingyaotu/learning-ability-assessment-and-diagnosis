#!/usr/bin/env python3
"""
道层测评→教练转介 schema 验证脚本 v1.0
验证 pipeline-data/assessment-referral-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. referral_trigger_rules: 4个触发规则 + _dao_guard
  3. referral_priority_levels: 3个优先级 + 响应时间
  4. referral_record_schema 8个必填字段
  5. initial_stage enum 七阶全覆盖
  6. trigger_id enum 4个触发
  7. priority_id enum 3个优先级
  8. primary_bottleneck enum MECE 四维度
  9. recommended_flywheel_focus enum 六飞轮 + _dao_guard
  10. coach_matching_rules 七阶→证书等级联动 + _dao_guard
  11. minor_referral_rules: [HALT-CSO] + _dao_guard
  12. validation_rules: 七阶/MECE/六飞轮/theta禁止/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
REFERRAL_PATH = REPO_ROOT / "pipeline-data" / "assessment-referral-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
VALID_TRIGGER_IDS = {"rt-low-stage", "rt-mece-gap", "rt-flywheel-weak", "rt-student-request"}
VALID_PRIORITY_IDS = {"rp-high", "rp-medium", "rp-standard"}
REQUIRED_REFERRAL_FIELDS = {
    "referral_id", "student_id", "source_session_id", "referral_date",
    "trigger_id", "priority_id", "initial_stage", "referral_status"
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
    print("  测评→教练转介 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not REFERRAL_PATH.exists():
        fail(f"找不到文件: {REFERRAL_PATH}")
        sys.exit(1)
    data = json.loads(REFERRAL_PATH.read_text(encoding="utf-8"))
    ok("assessment-referral-schema.json 加载成功")

    triggers = data.get("referral_trigger_rules", {}).get("triggers", [])
    priorities = data.get("referral_priority_levels", {}).get("levels", [])
    rec_fields = data.get("referral_record_schema", {}).get("fields", {})
    vr = data.get("validation_rules", {})

    # [2] referral_trigger_rules 4个触发 + _dao_guard
    print("\n[2] referral_trigger_rules 4个触发规则 + _dao_guard")
    found_trigger_ids = {t.get("trigger_id") for t in triggers}
    missing_triggers = VALID_TRIGGER_IDS - found_trigger_ids
    if missing_triggers:
        fail(f"缺少触发规则: {missing_triggers}")
    else:
        ok(f"4个触发规则全覆盖 ✓ {sorted(found_trigger_ids)}")
    for t in triggers:
        tid = t.get("trigger_id", "?")
        guard = t.get("_dao_guard", "")
        if guard:
            ok(f"{tid}: _dao_guard 存在 ✓")
        else:
            fail(f"{tid}: _dao_guard 缺失")

    # [3] referral_priority_levels 3个优先级
    print("\n[3] referral_priority_levels 3个优先级")
    found_priority_ids = {p.get("priority_id") for p in priorities}
    missing_priorities = VALID_PRIORITY_IDS - found_priority_ids
    if missing_priorities:
        fail(f"缺少优先级: {missing_priorities}")
    else:
        ok(f"3个优先级全覆盖 ✓ {sorted(found_priority_ids)}")
    for p in priorities:
        pid = p.get("priority_id", "?")
        if p.get("max_assignment_hours"):
            ok(f"{pid}: max_assignment_hours={p['max_assignment_hours']} ✓")
        else:
            fail(f"{pid}: max_assignment_hours 缺失")

    # [4] referral_record_schema 8个必填字段
    print("\n[4] referral_record_schema 8个必填字段")
    vr_req = set(vr.get("required_referral_fields", []))
    if vr_req == REQUIRED_REFERRAL_FIELDS:
        ok("validation_rules.required_referral_fields 8字段全覆盖 ✓")
    else:
        missing_rf = REQUIRED_REFERRAL_FIELDS - vr_req
        fail(f"required_referral_fields 缺少: {missing_rf}")
    for fname in REQUIRED_REFERRAL_FIELDS:
        if fname in rec_fields:
            ok(f"referral_record_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"referral_record_schema.fields.{fname} 缺失")

    # [5] initial_stage enum 七阶
    print("\n[5] initial_stage enum 七阶全覆盖")
    stage_enum = set(rec_fields.get("initial_stage", {}).get("enum", []))
    if stage_enum == VALID_STAGE_NAMES:
        ok("initial_stage enum 七阶全覆盖 ✓")
    else:
        fail(f"initial_stage enum {stage_enum} ≠ {VALID_STAGE_NAMES}")

    # [6] trigger_id enum
    print("\n[6] trigger_id enum 4个触发")
    trig_enum = set(rec_fields.get("trigger_id", {}).get("enum", []))
    if trig_enum == VALID_TRIGGER_IDS:
        ok("trigger_id enum 4个触发全覆盖 ✓")
    else:
        fail(f"trigger_id enum {trig_enum} ≠ {VALID_TRIGGER_IDS}")

    # [7] priority_id enum
    print("\n[7] priority_id enum 3个优先级")
    prio_enum = set(rec_fields.get("priority_id", {}).get("enum", []))
    if prio_enum == VALID_PRIORITY_IDS:
        ok("priority_id enum 3个优先级全覆盖 ✓")
    else:
        fail(f"priority_id enum {prio_enum} ≠ {VALID_PRIORITY_IDS}")

    # [8] primary_bottleneck enum MECE
    print("\n[8] primary_bottleneck enum MECE 四维度")
    bn_enum = set(rec_fields.get("primary_bottleneck", {}).get("enum", []))
    if bn_enum == MECE_DIMENSIONS:
        ok("primary_bottleneck enum MECE 四维度 ✓")
    else:
        fail(f"primary_bottleneck enum {bn_enum} ≠ {MECE_DIMENSIONS}")

    # [9] recommended_flywheel_focus enum 六飞轮 + _dao_guard
    print("\n[9] recommended_flywheel_focus enum 六飞轮 + _dao_guard")
    fw_field = rec_fields.get("recommended_flywheel_focus", {})
    fw_enum = set(fw_field.get("enum", []))
    if fw_enum == VALID_FLYWHEEL_NAMES:
        ok("recommended_flywheel_focus enum 六飞轮全覆盖 ✓")
    else:
        fail(f"recommended_flywheel_focus enum {fw_enum} ≠ {VALID_FLYWHEEL_NAMES}")
    fw_guard = fw_field.get("_dao_guard", "")
    if "六飞轮" in fw_guard:
        ok("recommended_flywheel_focus._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"recommended_flywheel_focus._dao_guard='{fw_guard}' 未含'六飞轮'")

    # [10] coach_matching_rules 七阶→证书联动 + _dao_guard
    print("\n[10] coach_matching_rules 七阶→证书等级联动 + _dao_guard")
    cmr = data.get("coach_matching_rules", {}).get("matching_criteria", [])
    cert_rule = next((c for c in cmr if c.get("criterion") == "certification_level"), None)
    if cert_rule:
        rules = cert_rule.get("rules", {})
        stage_keys = set(rules.keys())
        if stage_keys == VALID_STAGE_NAMES:
            ok("coach_matching_rules.certification_level 七阶全覆盖 ✓")
        else:
            fail(f"certification_level rules 阶位 {stage_keys} ≠ {VALID_STAGE_NAMES}")
        cert_guard = cert_rule.get("_dao_guard", "")
        if "七阶" in cert_guard:
            ok("certification_level._dao_guard 含'七阶' ✓")
        else:
            fail(f"certification_level._dao_guard='{cert_guard}' 未含'七阶'")
    else:
        fail("coach_matching_rules 缺少 certification_level 规则")

    # [11] minor_referral_rules HALT-CSO + _dao_guard
    print("\n[11] minor_referral_rules [HALT-CSO] + _dao_guard")
    mrr = data.get("minor_referral_rules", {}).get("under_14_requirements", {})
    halt_action = mrr.get("halt_action", "")
    if "[HALT-CSO]" in halt_action:
        ok("minor_referral_rules.halt_action 含'[HALT-CSO]' ✓")
    else:
        fail(f"minor_referral_rules.halt_action='{halt_action}' 未含'[HALT-CSO]'")
    mrr_guard = mrr.get("_dao_guard", "")
    if "PIPL" in mrr_guard and "[HALT-CSO]" in mrr_guard:
        ok("minor_referral_rules._dao_guard 含'PIPL'+'[HALT-CSO]' ✓")
    else:
        fail(f"minor_referral_rules._dao_guard='{mrr_guard}' 未含'PIPL'或'[HALT-CSO]'")

    # [12] validation_rules
    print("\n[12] validation_rules 合规")
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
    theta_rule = vr.get("theta_sharing_rule", "")
    if "θ" in theta_rule or "theta" in theta_rule.lower():
        ok("validation_rules.theta_sharing_rule θ禁止共享规则存在 ✓")
    else:
        fail(f"validation_rules.theta_sharing_rule='{theta_rule}' 未含θ禁止规则")
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
        print("  ✅ 测评→教练转介 schema 验证 PASS — 触发规则/优先级/七阶/MECE/六飞轮/HALT-CSO/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
