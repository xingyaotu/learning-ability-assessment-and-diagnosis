#!/usr/bin/env python3
"""
道层测评反馈交付 schema 验证脚本 v1.0
验证 pipeline-data/assessment-feedback-delivery-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. feedback_delivery_schema: 5个必填字段
  3. stage_result enum 七阶 + _dao_guard 含'七阶'
  4. primary_bottleneck enum MECE + _dao_guard
  5. theta_excluded_from_report _dao_guard 含'θ'
  6. portal_access_control: 四门户 IDs 全覆盖 + _dao_guard 含'四门户'
  7. student_portal + parent_portal + coach_portal + ops_portal 存在
  8. parent_portal._halt_if_minor 含'[HALT-CSO]'
  9. feedback_content: stage_narrative._dao_guard 含'七阶'
  10. flywheel_feedback properties 六飞轮 + _dao_guard
  11. mece_feedback properties MECE四维度 + _dao_guard
  12. sop05_recommendation._dao_guard 含'流程' ⑤守护
  13. delivery_notification: recipient_portal enum 四门户 + _dao_guard
  14. validation_rules: sop05_guard/θ排除/PIPL第14条/七阶/MECE/六飞轮/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
FEEDBACK_PATH = REPO_ROOT / "pipeline-data" / "assessment-feedback-delivery-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
PORTAL_IDS = {"prt-student", "prt-parent", "prt-coach", "prt-ops"}
REQUIRED_DELIVERY_FIELDS = {
    "delivery_id", "assessment_session_id", "student_id",
    "delivery_date", "delivery_status"
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
    print("  测评反馈交付 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not FEEDBACK_PATH.exists():
        fail(f"找不到文件: {FEEDBACK_PATH}")
        sys.exit(1)
    data = json.loads(FEEDBACK_PATH.read_text(encoding="utf-8"))
    ok("assessment-feedback-delivery-schema.json 加载成功")

    fd_fields = data.get("feedback_delivery_schema", {}).get("fields", {})
    portals = data.get("portal_access_control", {}).get("portals", {})
    pac_guard = data.get("portal_access_control", {}).get("_dao_guard", "")
    fc_fields = data.get("feedback_content_schema", {}).get("fields", {})
    dn_fields = data.get("delivery_notification_schema", {}).get("fields", {})
    vr = data.get("validation_rules", {})

    # [2] feedback_delivery_schema: 5个必填字段
    print("\n[2] feedback_delivery_schema 5个必填字段")
    for fname in REQUIRED_DELIVERY_FIELDS:
        if fname in fd_fields:
            ok(f"feedback_delivery_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"feedback_delivery_schema.fields.{fname} 缺失")

    # [3] stage_result enum 七阶 + _dao_guard
    print("\n[3] stage_result enum 七阶 + _dao_guard")
    sr_field = fd_fields.get("stage_result", {})
    sr_enum = set(sr_field.get("enum", []))
    if sr_enum == VALID_STAGE_NAMES:
        ok("stage_result enum 七阶全覆盖 ✓")
    else:
        fail(f"stage_result enum {sr_enum} ≠ {VALID_STAGE_NAMES}")
    sr_guard = sr_field.get("_dao_guard", "")
    if "七阶" in sr_guard:
        ok("stage_result._dao_guard 含'七阶' ✓")
    else:
        fail(f"stage_result._dao_guard='{sr_guard}' 未含'七阶'")

    # [4] primary_bottleneck enum MECE + _dao_guard
    print("\n[4] primary_bottleneck enum MECE + _dao_guard")
    pb_field = fd_fields.get("primary_bottleneck", {})
    pb_enum = set(pb_field.get("enum", []))
    if pb_enum == MECE_DIMENSIONS:
        ok("primary_bottleneck enum MECE 四维度 ✓")
    else:
        fail(f"primary_bottleneck enum {pb_enum} ≠ {MECE_DIMENSIONS}")
    pb_guard = pb_field.get("_dao_guard", "")
    if "MECE" in pb_guard:
        ok("primary_bottleneck._dao_guard 含'MECE' ✓")
    else:
        fail(f"primary_bottleneck._dao_guard='{pb_guard}' 未含'MECE'")

    # [5] theta_excluded_from_report _dao_guard 含'θ'
    print("\n[5] theta_excluded_from_report _dao_guard 含'θ'")
    theta_guard = fd_fields.get("theta_excluded_from_report", {}).get("_dao_guard", "")
    if "θ" in theta_guard:
        ok("theta_excluded_from_report._dao_guard 含'θ' ✓")
    else:
        fail(f"theta_excluded_from_report._dao_guard='{theta_guard}' 未含'θ'")

    # [6] portal_access_control: _dao_guard 含'四门户'
    print("\n[6] portal_access_control _dao_guard 含'四门户'")
    if "四门户" in pac_guard:
        ok("portal_access_control._dao_guard 含'四门户' ✓")
    else:
        fail(f"portal_access_control._dao_guard='{pac_guard}' 未含'四门户'")

    # [7] 四门户都存在
    print("\n[7] 四门户 portal_ids 全覆盖")
    portal_keys = set(portals.keys())
    expected_portal_keys = {"student_portal", "parent_portal", "coach_portal", "operations_portal"}
    if portal_keys == expected_portal_keys:
        ok("四门户 portals 全存在 ✓")
    else:
        fail(f"portals {portal_keys} ≠ {expected_portal_keys}")
    portal_id_values = {portals.get(k, {}).get("portal_id") for k in portals}
    if PORTAL_IDS == portal_id_values:
        ok("四门户 portal_id 值全覆盖 ✓")
    else:
        fail(f"portal_id 值 {portal_id_values} ≠ {PORTAL_IDS}")

    # [8] parent_portal._halt_if_minor 含 [HALT-CSO]
    print("\n[8] parent_portal._halt_if_minor 含'[HALT-CSO]'")
    halt_minor = portals.get("parent_portal", {}).get("_halt_if_minor", "")
    if "[HALT-CSO]" in halt_minor:
        ok("parent_portal._halt_if_minor 含[HALT-CSO] ✓")
    else:
        fail(f"parent_portal._halt_if_minor='{halt_minor}' 未含[HALT-CSO]")

    # [9] feedback_content: stage_narrative._dao_guard 含'七阶'
    print("\n[9] feedback_content stage_narrative._dao_guard 含'七阶'")
    sn_guard = fc_fields.get("stage_narrative", {}).get("_dao_guard", "")
    if "七阶" in sn_guard:
        ok("stage_narrative._dao_guard 含'七阶' ✓")
    else:
        fail(f"stage_narrative._dao_guard='{sn_guard}' 未含'七阶'")

    # [10] flywheel_feedback properties 六飞轮 + _dao_guard
    print("\n[10] feedback_content flywheel_feedback 六飞轮 + _dao_guard")
    fwf_field = fc_fields.get("flywheel_feedback", {})
    fwf_props = set(fwf_field.get("properties", {}).keys())
    if fwf_props == VALID_FLYWHEEL_NAMES:
        ok("flywheel_feedback 六飞轮全覆盖 ✓")
    else:
        fail(f"flywheel_feedback {fwf_props} ≠ {VALID_FLYWHEEL_NAMES}")
    fwf_guard = fwf_field.get("_dao_guard", "")
    if "六飞轮" in fwf_guard:
        ok("flywheel_feedback._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"flywheel_feedback._dao_guard='{fwf_guard}' 未含'六飞轮'")

    # [11] mece_feedback properties MECE四维度 + _dao_guard
    print("\n[11] feedback_content mece_feedback MECE四维度 + _dao_guard")
    mf_field = fc_fields.get("mece_feedback", {})
    mf_props = {k.replace("_summary", "") for k in mf_field.get("properties", {}).keys() if "_summary" in k}
    if mf_props == MECE_DIMENSIONS:
        ok("mece_feedback MECE 四维度 summary 全覆盖 ✓")
    else:
        fail(f"mece_feedback dims {mf_props} ≠ {MECE_DIMENSIONS}")
    mf_guard = mf_field.get("_dao_guard", "")
    if "MECE" in mf_guard:
        ok("mece_feedback._dao_guard 含'MECE' ✓")
    else:
        fail(f"mece_feedback._dao_guard='{mf_guard}' 未含'MECE'")

    # [12] sop05_recommendation._dao_guard 含'流程' ⑤守护
    print("\n[12] feedback_content sop05_recommendation ⑤守护 含'流程'")
    sop05_rec_guard = fc_fields.get("sop05_recommendation", {}).get("_dao_guard", "")
    if "流程" in sop05_rec_guard:
        ok("sop05_recommendation._dao_guard 含'流程' ⑤守护 ✓")
    else:
        fail(f"sop05_recommendation._dao_guard='{sop05_rec_guard}' 未含'流程'")

    # [13] delivery_notification: recipient_portal enum 四门户 + _dao_guard
    print("\n[13] delivery_notification recipient_portal enum 四门户 + _dao_guard")
    rp_field = dn_fields.get("recipient_portal", {})
    rp_enum = set(rp_field.get("enum", []))
    if rp_enum == PORTAL_IDS:
        ok("recipient_portal enum 四门户全覆盖 ✓")
    else:
        fail(f"recipient_portal enum {rp_enum} ≠ {PORTAL_IDS}")
    rp_guard = rp_field.get("_dao_guard", "")
    if "四门户" in rp_guard:
        ok("recipient_portal._dao_guard 含'四门户' ✓")
    else:
        fail(f"recipient_portal._dao_guard='{rp_guard}' 未含'四门户'")

    # [14] validation_rules
    print("\n[14] validation_rules 合规")
    sop05_guard_vr = vr.get("sop05_guard", "")
    if "流程" in sop05_guard_vr:
        ok("validation_rules.sop05_guard 含'流程' ⑤守护 ✓")
    else:
        fail(f"validation_rules.sop05_guard='{sop05_guard_vr}' 未含'流程'")
    theta_excl = vr.get("theta_exclusion_rule", "")
    if "θ" in theta_excl:
        ok("validation_rules.theta_exclusion_rule 含'θ' ✓")
    else:
        fail(f"validation_rules.theta_exclusion_rule='{theta_excl}' 未含'θ'")
    pipl14_guard = vr.get("pipl_article14_guard", "")
    if "PIPL" in pipl14_guard and "[HALT-CSO]" in pipl14_guard:
        ok("validation_rules.pipl_article14_guard 含'PIPL'+'[HALT-CSO]' ✓")
    else:
        fail(f"validation_rules.pipl_article14_guard='{pipl14_guard}' 缺少关键词")
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
        print("  ✅ 测评反馈交付 schema 验证 PASS — 四门户/θ排除/七阶/MECE/六飞轮/⑤守护/HALT-CSO/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
