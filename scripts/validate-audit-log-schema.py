#!/usr/bin/env python3
"""
道层测评审计日志 schema 验证脚本 v1.0
验证 pipeline-data/assessment-audit-log-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. audit_event_categories: 5个分类全覆盖
  3. 每个分类 event_types 非空
  4. aac-compliance 含 dao_layer_drift 事件 + _dao_guard 含'道层'
  5. aac-compliance 含 pipl_halt 事件 (aat-co-02)
  6. aac-data-write 含 mece_profile_updated + _dao_guard 含 MECE
  7. audit_log_record_schema 8个核心字段 + event_category_id enum 5个 + risk_level enum 4级
  8. audit_retention_rules: standard_retention_years ≥ 7 + critical_event_retention_years ≥ 10 + _dao_guard
  9. integrity_controls: 4个完整性控制字段
  10. validation_rules: 5类/dao_layer/pipl_halt/留存年限/六飞轮/七阶/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
AUDIT_PATH = REPO_ROOT / "pipeline-data" / "assessment-audit-log-schema.json"

REQUIRED_CATEGORY_IDS = {"aac-data-access", "aac-data-write", "aac-data-deletion",
                          "aac-compliance", "aac-authentication"}
VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
SEVERITY_LEVELS = {"low", "medium", "high", "critical"}

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
    print("  测评审计日志 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not AUDIT_PATH.exists():
        fail(f"找不到文件: {AUDIT_PATH}")
        sys.exit(1)
    data = json.loads(AUDIT_PATH.read_text(encoding="utf-8"))
    ok("assessment-audit-log-schema.json 加载成功")

    categories = data.get("audit_event_categories", [])

    # [2] 5个分类全覆盖
    print("\n[2] audit_event_categories 5个分类全覆盖")
    found_cats = {c.get("category_id") for c in categories}
    missing_cats = REQUIRED_CATEGORY_IDS - found_cats
    if missing_cats:
        fail(f"缺少审计分类: {missing_cats}")
    else:
        ok(f"5个审计分类全覆盖 ✓ {sorted(found_cats)}")

    # [3] 每个分类 event_types 非空
    print("\n[3] 每个分类 event_types 非空")
    for c in categories:
        cid = c.get("category_id", "?")
        et = c.get("event_types", [])
        if et:
            ok(f"{cid}: event_types {len(et)}个 ✓")
        else:
            fail(f"{cid}: event_types 为空")

    # [4] aac-compliance 道层漂移事件 + _dao_guard 含'道层'
    print("\n[4] aac-compliance 道层漂移审计 + _dao_guard")
    aac_comp = next((c for c in categories if c.get("category_id") == "aac-compliance"), None)
    if aac_comp is None:
        fail("aac-compliance 分类缺失")
    else:
        comp_events = aac_comp.get("event_types", [])
        drift_event = next((e for e in comp_events if "dao_layer" in e.get("name", "")), None)
        if drift_event:
            ok(f"aac-compliance 含 dao_layer 事件 '{drift_event['name']}' ✓")
            guard_d = drift_event.get("_dao_guard", "")
            if "道层" in guard_d:
                ok("dao_layer_drift 事件 _dao_guard 含'道层' ✓")
            else:
                fail(f"dao_layer_drift 事件 _dao_guard='{guard_d}' 未含'道层'")
            if drift_event.get("risk_level") == "critical":
                ok("dao_layer_drift 事件 risk_level=critical ✓")
            else:
                fail(f"dao_layer_drift 事件 risk_level={drift_event.get('risk_level')} ≠ critical")
        else:
            fail("aac-compliance 未含 dao_layer_drift 事件")

    # [5] aac-compliance pipl_halt 事件
    print("\n[5] aac-compliance pipl_halt 审计")
    if aac_comp:
        halt_event = next((e for e in aac_comp.get("event_types", []) if "pipl_halt" in e.get("name", "")), None)
        if halt_event:
            ok(f"aac-compliance 含 pipl_halt 事件 '{halt_event['name']}' ✓")
            if halt_event.get("risk_level") == "critical":
                ok("pipl_halt 事件 risk_level=critical ✓")
            else:
                fail(f"pipl_halt 事件 risk_level={halt_event.get('risk_level')} ≠ critical")
        else:
            fail("aac-compliance 未含 pipl_halt 事件")

    # [6] aac-data-write mece_profile_updated + _dao_guard 含 MECE
    print("\n[6] aac-data-write mece_profile 更新审计")
    aac_write = next((c for c in categories if c.get("category_id") == "aac-data-write"), None)
    if aac_write:
        mece_event = next((e for e in aac_write.get("event_types", []) if "mece" in e.get("name", "").lower()), None)
        if mece_event:
            ok(f"aac-data-write 含 mece 更新事件 '{mece_event['name']}' ✓")
            mece_guard = mece_event.get("_dao_guard", "")
            if "MECE" in mece_guard:
                ok("mece_profile_updated 事件 _dao_guard 含'MECE' ✓")
            else:
                fail(f"mece_profile_updated 事件 _dao_guard='{mece_guard}' 未含'MECE'")
        else:
            fail("aac-data-write 未含 mece_profile 更新事件")
    else:
        fail("aac-data-write 分类缺失")

    # [7] audit_log_record_schema 核心字段
    print("\n[7] audit_log_record_schema 核心字段")
    log_fields = data.get("audit_log_record_schema", {}).get("fields", {})
    required_log = {"audit_id", "event_category_id", "event_type_id", "actor_id",
                    "actor_role", "timestamp", "risk_level", "success"}
    vr_required = set(data.get("validation_rules", {}).get("required_log_fields", []))
    if vr_required == required_log:
        ok("validation_rules.required_log_fields 8字段全覆盖 ✓")
    else:
        missing_rl = required_log - vr_required
        fail(f"required_log_fields 缺少: {missing_rl}")
    for fname in required_log:
        if fname in log_fields:
            ok(f"audit_log_record_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"audit_log_record_schema.fields.{fname} 缺失")

    cat_enum = set(log_fields.get("event_category_id", {}).get("enum", []))
    if cat_enum == REQUIRED_CATEGORY_IDS:
        ok("event_category_id enum 5分类全覆盖 ✓")
    else:
        fail(f"event_category_id enum {cat_enum} ≠ {REQUIRED_CATEGORY_IDS}")

    risk_enum = set(log_fields.get("risk_level", {}).get("enum", []))
    if risk_enum == SEVERITY_LEVELS:
        ok("risk_level enum 4级全覆盖 ✓")
    else:
        fail(f"risk_level enum {risk_enum} ≠ {SEVERITY_LEVELS}")

    # [8] audit_retention_rules
    print("\n[8] audit_retention_rules 留存规则")
    arr = data.get("audit_retention_rules", {})
    std_ret = arr.get("standard_retention_years", 0)
    if std_ret >= 7:
        ok(f"standard_retention_years={std_ret} ≥ 7 ✓")
    else:
        fail(f"standard_retention_years={std_ret} < 7")
    crit_ret = arr.get("critical_event_retention_years", 0)
    if crit_ret >= 10:
        ok(f"critical_event_retention_years={crit_ret} ≥ 10 ✓")
    else:
        fail(f"critical_event_retention_years={crit_ret} < 10")
    arr_guard = arr.get("_dao_guard", "")
    if "道层" in arr_guard and "PIPL" in arr_guard:
        ok("audit_retention_rules._dao_guard 含'道层'+'PIPL' ✓")
    else:
        fail(f"audit_retention_rules._dao_guard='{arr_guard}' 不完整")

    # [9] integrity_controls
    print("\n[9] integrity_controls 4个完整性控制")
    ic = data.get("integrity_controls", {})
    required_ic = {"tamper_detection", "immutability", "encryption", "access_control"}
    missing_ic = required_ic - set(ic.keys())
    if missing_ic:
        fail(f"integrity_controls 缺少: {missing_ic}")
    else:
        ok(f"integrity_controls {len(ic)}个控制项 全覆盖 ✓")

    # [10] validation_rules
    print("\n[10] validation_rules 合规")
    vr = data.get("validation_rules", {})
    cat_count = vr.get("audit_event_categories_count", 0)
    if cat_count == 5:
        ok("validation_rules.audit_event_categories_count=5 ✓")
    else:
        fail(f"validation_rules.audit_event_categories_count={cat_count} ≠ 5")

    if vr.get("dao_layer_audit_required") is True:
        ok("validation_rules.dao_layer_audit_required=true ✓")
    else:
        fail("validation_rules.dao_layer_audit_required 未设为 true")

    if vr.get("pipl_halt_audit_required") is True:
        ok("validation_rules.pipl_halt_audit_required=true ✓")
    else:
        fail("validation_rules.pipl_halt_audit_required 未设为 true")

    ret_min = vr.get("retention_years_minimum", 0)
    if ret_min >= 7:
        ok(f"validation_rules.retention_years_minimum={ret_min} ≥ 7 ✓")
    else:
        fail(f"validation_rules.retention_years_minimum={ret_min} < 7")

    fw_names = set(vr.get("six_flywheel_valid_names", []))
    if fw_names == VALID_FLYWHEEL_NAMES:
        ok("validation_rules.six_flywheel_valid_names 六飞轮全覆盖 ✓")
    else:
        fail(f"six_flywheel_valid_names {fw_names} ≠ {VALID_FLYWHEEL_NAMES}")

    stage_names = set(vr.get("seven_stage_valid_names", []))
    if stage_names == VALID_STAGE_NAMES:
        ok("validation_rules.seven_stage_valid_names 七阶全覆盖 ✓")
    else:
        fail(f"seven_stage_valid_names {stage_names} ≠ {VALID_STAGE_NAMES}")

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
        print("  ✅ 测评审计日志 schema 验证 PASS — 5类审计/道层守护/PIPL/7年留存 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
