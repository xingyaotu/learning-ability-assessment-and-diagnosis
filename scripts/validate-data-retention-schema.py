#!/usr/bin/env python3
"""
道层测评数据留存 schema 验证脚本 v1.0
验证 pipeline-data/assessment-data-retention-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. data_categories: 5个分类全覆盖
  3. 每个分类: retention_policy 含必填字段 + pipl_basis 存在
  4. dc-calibration: anonymization_at_expiry=false + archival_at_expiry=true
  5. dc-session/_dao_guard 含'MECE'/'七阶'
  6. dc-longitudinal/_dao_guard 含'六飞轮'/'七阶'
  7. deletion_workflow: 5步 + deletion_record_schema 核心字段
  8. minor_data_special_rules._dao_guard 含 'HALT-CSO' + PIPL 第14条
  9. validation_rules: 5类/pipl_article17/六飞轮/七阶/pipl
  10. PIPL 合规声明
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
RETENTION_PATH = REPO_ROOT / "pipeline-data" / "assessment-data-retention-schema.json"

REQUIRED_CATEGORY_IDS = {"dc-session", "dc-longitudinal", "dc-consent", "dc-adverse-event", "dc-calibration"}
VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
REQUIRED_RETENTION_FIELDS = {"standard_retention_months", "anonymization_at_expiry", "deletion_at_extended_expiry"}

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
    print("  测评数据留存 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not RETENTION_PATH.exists():
        fail(f"找不到文件: {RETENTION_PATH}")
        sys.exit(1)
    data = json.loads(RETENTION_PATH.read_text(encoding="utf-8"))
    ok("assessment-data-retention-schema.json 加载成功")

    categories = data.get("data_categories", [])

    # [2] 5个分类全覆盖
    print("\n[2] data_categories 5个分类全覆盖")
    found_cats = {c.get("category_id") for c in categories}
    missing_cats = REQUIRED_CATEGORY_IDS - found_cats
    if missing_cats:
        fail(f"缺少数据分类: {missing_cats}")
    else:
        ok(f"5个数据分类全覆盖 ✓ {sorted(found_cats)}")

    # [3] 每个分类 retention_policy 必填字段 + pipl_basis
    print("\n[3] 每个分类 retention_policy 必填字段")
    for c in categories:
        cid = c.get("category_id", "?")
        rp = c.get("retention_policy", {})
        pipl_b = c.get("pipl_basis", "")
        missing_rp = REQUIRED_RETENTION_FIELDS - set(rp.keys())
        if missing_rp:
            fail(f"{cid}: retention_policy 缺少字段: {missing_rp}")
        else:
            ok(f"{cid}: retention_policy 必填字段全覆盖 ✓")
        if pipl_b:
            ok(f"{cid}: pipl_basis 存在 ✓")
        else:
            fail(f"{cid}: pipl_basis 缺失")
        srm = rp.get("standard_retention_months", 0)
        if srm > 0:
            ok(f"{cid}: standard_retention_months={srm} > 0 ✓")
        else:
            fail(f"{cid}: standard_retention_months={srm} ≤ 0")

    # [4] dc-calibration 特殊规则
    print("\n[4] dc-calibration 统计数据特殊规则")
    calib = next((c for c in categories if c.get("category_id") == "dc-calibration"), None)
    if calib is None:
        fail("dc-calibration 分类缺失")
    else:
        rp_c = calib.get("retention_policy", {})
        if rp_c.get("anonymization_at_expiry") is False:
            ok("dc-calibration: anonymization_at_expiry=false (统计数据无需匿名) ✓")
        else:
            fail(f"dc-calibration: anonymization_at_expiry={rp_c.get('anonymization_at_expiry')} ≠ false")
        if rp_c.get("archival_at_expiry") is True:
            ok("dc-calibration: archival_at_expiry=true ✓")
        else:
            fail(f"dc-calibration: archival_at_expiry={rp_c.get('archival_at_expiry')} ≠ true")
        calib_guard = calib.get("_dao_guard", "")
        if "PIPL" in calib_guard and "匿名" in calib_guard:
            ok("dc-calibration: _dao_guard 含 PIPL 豁免说明 ✓")
        else:
            fail(f"dc-calibration: _dao_guard='{calib_guard}' 不完整")

    # [5] dc-session _dao_guard 含 MECE/七阶
    print("\n[5] dc-session _dao_guard 道层守护")
    dc_sess = next((c for c in categories if c.get("category_id") == "dc-session"), None)
    if dc_sess:
        guard_s = dc_sess.get("_dao_guard", "")
        if "MECE" in guard_s:
            ok("dc-session: _dao_guard 含'MECE' ✓")
        else:
            fail(f"dc-session: _dao_guard='{guard_s}' 未含'MECE'")
        if "七阶" in guard_s:
            ok("dc-session: _dao_guard 含'七阶' ✓")
        else:
            fail(f"dc-session: _dao_guard='{guard_s}' 未含'七阶'")
    else:
        fail("dc-session 分类缺失")

    # [6] dc-longitudinal _dao_guard 含 六飞轮/七阶
    print("\n[6] dc-longitudinal _dao_guard 道层守护")
    dc_long = next((c for c in categories if c.get("category_id") == "dc-longitudinal"), None)
    if dc_long:
        guard_l = dc_long.get("_dao_guard", "")
        if "六飞轮" in guard_l:
            ok("dc-longitudinal: _dao_guard 含'六飞轮' ✓")
        else:
            fail(f"dc-longitudinal: _dao_guard='{guard_l}' 未含'六飞轮'")
        if "七阶" in guard_l:
            ok("dc-longitudinal: _dao_guard 含'七阶' ✓")
        else:
            fail(f"dc-longitudinal: _dao_guard='{guard_l}' 未含'七阶'")
    else:
        fail("dc-longitudinal 分类缺失")

    # [7] deletion_workflow
    print("\n[7] deletion_workflow 删除工作流")
    dw = data.get("deletion_workflow", {})
    steps = dw.get("steps", [])
    if len(steps) >= 5:
        ok(f"deletion_workflow.steps {len(steps)}步 ≥ 5 ✓")
    else:
        fail(f"deletion_workflow.steps {len(steps)} < 5")
    drs = dw.get("deletion_record_schema", {})
    required_drs = {"deletion_log_id", "data_category_id", "records_affected_count",
                    "deletion_type", "deletion_date", "pipl_compliance_confirmed"}
    missing_drs = required_drs - set(drs.keys())
    if missing_drs:
        fail(f"deletion_record_schema 缺少字段: {missing_drs}")
    else:
        ok(f"deletion_record_schema {len(drs)}个字段 核心字段全覆盖 ✓")
    dtype_enum = set(drs.get("deletion_type", {}).get("enum", []))
    if "anonymization" in dtype_enum and "permanent_deletion" in dtype_enum:
        ok(f"deletion_type enum 含 anonymization 和 permanent_deletion ✓")
    else:
        fail(f"deletion_type enum {dtype_enum} 不完整")

    # [8] minor_data_special_rules HALT-CSO + PIPL 第14条
    print("\n[8] minor_data_special_rules HALT-CSO + PIPL 第14条")
    mdsr = data.get("minor_data_special_rules", {})
    if mdsr.get("rules"):
        ok(f"minor_data_special_rules.rules {len(mdsr['rules'])}条 ✓")
    else:
        fail("minor_data_special_rules.rules 为空")
    mdsr_guard = mdsr.get("_dao_guard", "")
    if "HALT-CSO" in mdsr_guard:
        ok("minor_data_special_rules._dao_guard 含 [HALT-CSO] ✓")
    else:
        fail(f"minor_data_special_rules._dao_guard='{mdsr_guard}' 未含 HALT-CSO")
    if "PIPL" in mdsr_guard and "14" in mdsr_guard:
        ok("minor_data_special_rules._dao_guard 含 PIPL 第14条 ✓")
    else:
        fail(f"minor_data_special_rules._dao_guard='{mdsr_guard}' 未含 PIPL 第14条")

    # [9] validation_rules
    print("\n[9] validation_rules 合规")
    vr = data.get("validation_rules", {})
    dc_count = vr.get("data_categories_count", 0)
    if dc_count == 5:
        ok("validation_rules.data_categories_count=5 ✓")
    else:
        fail(f"validation_rules.data_categories_count={dc_count} ≠ 5")

    pipl17 = vr.get("pipl_article17_compliance", "")
    if "PIPL" in pipl17 and "17" in pipl17:
        ok("validation_rules.pipl_article17_compliance 存在 ✓")
    else:
        fail("validation_rules.pipl_article17_compliance 缺失")

    anon_before_del = vr.get("anonymization_before_deletion", False)
    if anon_before_del is True:
        ok("validation_rules.anonymization_before_deletion=true ✓")
    else:
        fail("validation_rules.anonymization_before_deletion 未设为 true")

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

    # [10] PIPL 合规
    print("\n[10] PIPL 合规")
    pipl_meta = data.get("_meta", {}).get("pipl_note", "")
    if "PIPL" in pipl_meta and "第17条" in pipl_meta:
        ok("_meta.pipl_note PIPL 第17条合规声明 ✓")
    else:
        fail("_meta.pipl_note 缺少 PIPL 第17条声明")
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
        print("  ✅ 测评数据留存 schema 验证 PASS — PIPL第17条/留存周期/删除工作流 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
