#!/usr/bin/env python3
"""
道层测评知情同意 schema 验证脚本 v1.0
验证 pipeline-data/assessment-consent-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. consent_categories: 3个分类全覆盖 + 各分类字段完整
  3. cc-minor-under14: cso_notification_required=true + _dao_guard 含'PIPL 第14条'
  4. cc-minor-under14: _dao_guard 含 'HALT' 或 'CSO'
  5. consent_record_schema: 8个必填字段 + status enum 含 cso_blocked
  6. student_age_group enum 3个 + guardian_consent_required 字段存在
  7. consent_validation_workflow: under14_halt_rule 含 '[HALT-CSO]' + _dao_guard
  8. consent_types_registry: 8个同意类型 + guardian_written_consent 含 guardian signature
  9. validation_rules: 3个分类/pipl_article14_guard/halt_trigger/data_not_stored/pipl
  10. PIPL 合规声明 (多层)
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CONSENT_PATH = REPO_ROOT / "pipeline-data" / "assessment-consent-schema.json"

REQUIRED_CATEGORY_IDS = {"cc-adult", "cc-minor-14plus", "cc-minor-under14"}
REQUIRED_AGE_GROUPS = {"adult_18plus", "minor_14to17", "minor_under14"}
REQUIRED_CONSENT_FIELDS = {
    "consent_id", "student_id", "consent_category_id", "student_age_group",
    "consent_types_granted", "consent_granted_at", "consent_expires_at", "status"
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
    print("  测评知情同意 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not CONSENT_PATH.exists():
        fail(f"找不到文件: {CONSENT_PATH}")
        sys.exit(1)
    data = json.loads(CONSENT_PATH.read_text(encoding="utf-8"))
    ok("assessment-consent-schema.json 加载成功")

    categories = data.get("consent_categories", [])

    # [2] 3个分类全覆盖 + 字段完整
    print("\n[2] consent_categories 3个分类全覆盖")
    found_cats = {c.get("category_id") for c in categories}
    missing_cats = REQUIRED_CATEGORY_IDS - found_cats
    if missing_cats:
        fail(f"缺少同意分类: {missing_cats}")
    else:
        ok(f"3个同意分类全覆盖 ✓ {sorted(found_cats)}")

    for c in categories:
        cid = c.get("category_id", "?")
        pipl_req = c.get("pipl_requirement", "")
        consent_types = c.get("required_consent_types", [])
        validity = c.get("consent_validity_months", 0)
        if pipl_req:
            ok(f"{cid}: pipl_requirement 存在 ✓")
        else:
            fail(f"{cid}: pipl_requirement 缺失")
        if consent_types:
            ok(f"{cid}: required_consent_types {len(consent_types)}个 ✓")
        else:
            fail(f"{cid}: required_consent_types 为空")
        if validity > 0:
            ok(f"{cid}: consent_validity_months={validity} > 0 ✓")
        else:
            fail(f"{cid}: consent_validity_months={validity} ≤ 0")

    # [3] cc-minor-under14 CSO 通知 + _dao_guard 含'PIPL'
    print("\n[3] cc-minor-under14 PIPL 第14条 + CSO 守护")
    u14 = next((c for c in categories if c.get("category_id") == "cc-minor-under14"), None)
    if u14 is None:
        fail("cc-minor-under14 分类缺失")
    else:
        if u14.get("cso_notification_required") is True:
            ok("cc-minor-under14: cso_notification_required=true ✓")
        else:
            fail(f"cc-minor-under14: cso_notification_required={u14.get('cso_notification_required')} ≠ true")
        if u14.get("guardian_verification_required") is True:
            ok("cc-minor-under14: guardian_verification_required=true ✓")
        else:
            fail("cc-minor-under14: guardian_verification_required 未设为 true")
        guard_u14 = u14.get("_dao_guard", "")
        if "PIPL" in guard_u14:
            ok("cc-minor-under14: _dao_guard 含'PIPL' ✓")
        else:
            fail(f"cc-minor-under14: _dao_guard='{guard_u14}' 未含'PIPL'")

    # [4] cc-minor-under14 _dao_guard 含 'HALT' 或 'CSO'
    print("\n[4] cc-minor-under14 HALT/CSO 守护")
    if u14:
        guard_u14 = u14.get("_dao_guard", "")
        if "HALT" in guard_u14 or "CSO" in guard_u14:
            ok("cc-minor-under14: _dao_guard 含 HALT/CSO 守护 ✓")
        else:
            fail(f"cc-minor-under14: _dao_guard='{guard_u14}' 未含 HALT 或 CSO")
        # Check required consent types include guardian_written_consent
        rc_types = u14.get("required_consent_types", [])
        if "guardian_written_consent" in rc_types:
            ok("cc-minor-under14: required_consent_types 含 guardian_written_consent ✓")
        else:
            fail("cc-minor-under14: required_consent_types 未含 guardian_written_consent")

    # [5] consent_record_schema 核心字段
    print("\n[5] consent_record_schema 8个必填字段")
    rec_fields = data.get("consent_record_schema", {}).get("fields", {})
    vr_fields = set(data.get("validation_rules", {}).get("required_fields", []))
    if vr_fields == REQUIRED_CONSENT_FIELDS:
        ok(f"validation_rules.required_fields 8字段全覆盖 ✓")
    else:
        missing_rf = REQUIRED_CONSENT_FIELDS - vr_fields
        fail(f"required_fields 缺少: {missing_rf}")
    for fname in REQUIRED_CONSENT_FIELDS:
        if fname in rec_fields:
            ok(f"consent_record_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"consent_record_schema.fields.{fname} 缺失")
    status_enum = set(rec_fields.get("status", {}).get("enum", []))
    if "cso_blocked" in status_enum:
        ok("status enum 含 cso_blocked ✓")
    else:
        fail("status enum 未含 cso_blocked")

    # [6] student_age_group enum + guardian_consent_required
    print("\n[6] student_age_group enum 3个 + guardian 字段")
    age_enum = set(rec_fields.get("student_age_group", {}).get("enum", []))
    if age_enum == REQUIRED_AGE_GROUPS:
        ok(f"student_age_group enum 3个年龄组 ✓")
    else:
        fail(f"student_age_group enum {age_enum} ≠ {REQUIRED_AGE_GROUPS}")
    if "guardian_consent_required" in rec_fields:
        ok("consent_record_schema.guardian_consent_required 字段存在 ✓")
    else:
        fail("consent_record_schema.guardian_consent_required 字段缺失")
    if "guardian_consent_received" in rec_fields:
        ok("consent_record_schema.guardian_consent_received 字段存在 ✓")
    else:
        fail("consent_record_schema.guardian_consent_received 字段缺失")

    # [7] consent_validation_workflow under14_halt_rule
    print("\n[7] consent_validation_workflow HALT 规则")
    cvw = data.get("consent_validation_workflow", {})
    halt_rule = cvw.get("under14_halt_rule", {})
    action = halt_rule.get("action", "")
    if "[HALT-CSO]" in action:
        ok("under14_halt_rule.action 含 [HALT-CSO] ✓")
    else:
        fail(f"under14_halt_rule.action='{action}' 未含 [HALT-CSO]")
    halt_guard = halt_rule.get("_dao_guard", "")
    if "PIPL" in halt_guard and "14" in halt_guard:
        ok("under14_halt_rule._dao_guard PIPL 第14条守护 ✓")
    else:
        fail(f"under14_halt_rule._dao_guard='{halt_guard}' 未含 PIPL 第14条")
    pre_check = cvw.get("pre_session_check", {})
    if pre_check.get("steps"):
        ok(f"pre_session_check steps {len(pre_check['steps'])}步 ✓")
    else:
        fail("pre_session_check.steps 为空")

    # [8] consent_types_registry
    print("\n[8] consent_types_registry 8个同意类型")
    ctr = data.get("consent_types_registry", {})
    if len(ctr) >= 8:
        ok(f"consent_types_registry {len(ctr)}个同意类型 ≥ 8 ✓")
    else:
        fail(f"consent_types_registry 仅 {len(ctr)} 个同意类型 < 8")
    gwc = ctr.get("guardian_written_consent", {})
    if gwc.get("requires_guardian_signature") is True:
        ok("guardian_written_consent.requires_guardian_signature=true ✓")
    else:
        fail("guardian_written_consent.requires_guardian_signature 未设为 true")
    if gwc.get("requires_guardian_identity_verification") is True:
        ok("guardian_written_consent.requires_guardian_identity_verification=true ✓")
    else:
        fail("guardian_written_consent.requires_guardian_identity_verification 未设为 true")

    # [9] validation_rules
    print("\n[9] validation_rules 合规")
    vr = data.get("validation_rules", {})
    cc_count = vr.get("consent_categories_count", 0)
    if cc_count == 3:
        ok("validation_rules.consent_categories_count=3 ✓")
    else:
        fail(f"validation_rules.consent_categories_count={cc_count} ≠ 3")

    pipl14_guard = vr.get("pipl_article14_guard", "")
    if "guardian_consent_received" in pipl14_guard and "cso_notified" in pipl14_guard:
        ok("validation_rules.pipl_article14_guard 完整 ✓")
    else:
        fail(f"validation_rules.pipl_article14_guard='{pipl14_guard}' 不完整")

    halt_trigger = vr.get("halt_trigger", "")
    if "[HALT-CSO]" in halt_trigger:
        ok("validation_rules.halt_trigger 含 [HALT-CSO] ✓")
    else:
        fail(f"validation_rules.halt_trigger='{halt_trigger}' 未含 [HALT-CSO]")

    not_stored = vr.get("data_not_stored", [])
    if "guardian_real_name" in not_stored and "student_real_name" in not_stored:
        ok(f"validation_rules.data_not_stored {len(not_stored)}项 含 guardian/student 真实姓名 ✓")
    else:
        fail(f"validation_rules.data_not_stored={not_stored} 未列出真实姓名禁止存储")

    cat_ids = set(vr.get("consent_category_ids", []))
    if cat_ids == REQUIRED_CATEGORY_IDS:
        ok("validation_rules.consent_category_ids 3分类 ✓")
    else:
        fail(f"validation_rules.consent_category_ids {cat_ids} ≠ {REQUIRED_CATEGORY_IDS}")

    # [10] PIPL 合规 (多层)
    print("\n[10] PIPL 合规 (多层)")
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
    student_id_field = data.get("consent_record_schema", {}).get("fields", {}).get("student_id", {})
    if "匿名" in str(student_id_field):
        ok("consent_record_schema.student_id 含匿名 ID 说明 ✓")
    else:
        fail("consent_record_schema.student_id 未含匿名 ID 说明")

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
        print("  ✅ 测评知情同意 schema 验证 PASS — PIPL第14条/HALT-CSO/匿名化 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
