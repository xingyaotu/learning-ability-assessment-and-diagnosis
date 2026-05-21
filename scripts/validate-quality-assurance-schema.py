#!/usr/bin/env python3
"""
道层测评质量保证 schema 验证脚本 v1.0
验证 pipeline-data/assessment-quality-assurance-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. qa_report_schema: required fields + overall_qa_status enum
  3. item_quality_metrics: avg_discrimination_by_irt_model IRT三模型 + _dao_guard
  4. item_quality_metrics: flywheel_item_coverage 六飞轮 + _dao_guard
  5. cat_performance_metrics: 5个性能字段存在
  6. seven_stage_measurement_quality: stage_classification_consistency _dao_guard 含'七阶'
  7. seven_stage_measurement_quality: stage_boundary_se_by_stage 六条边界 + _dao_guard
  8. mece_dimension_qa: dimension_reliability MECE四维度 + _dao_guard
  9. mece_dimension_qa: dimension_discrimination_validity MECE相关 + _dao_guard
  10. qa_flags_and_alerts: halt_conditions 含[HALT-CSO] + stage halt _dao_guard 含'七阶'
  11. validation_rules: 七阶/MECE/六飞轮/IRT模型/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
QA_PATH = REPO_ROOT / "pipeline-data" / "assessment-quality-assurance-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
IRT_MODELS = {"1PL", "2PL", "3PL"}
STAGE_BOUNDARIES = {
    "不会_模糊_boundary", "模糊_清晰_boundary", "清晰_框架_boundary",
    "框架_运用_boundary", "运用_熟练_boundary", "熟练_创新_boundary"
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
    print("  测评质量保证 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not QA_PATH.exists():
        fail(f"找不到文件: {QA_PATH}")
        sys.exit(1)
    data = json.loads(QA_PATH.read_text(encoding="utf-8"))
    ok("assessment-quality-assurance-schema.json 加载成功")

    qa_fields = data.get("qa_report_schema", {}).get("fields", {})
    item_q = data.get("item_quality_metrics", {}).get("fields", {})
    cat_perf = data.get("cat_performance_metrics", {}).get("fields", {})
    stage_mq = data.get("seven_stage_measurement_quality", {}).get("fields", {})
    mece_qa = data.get("mece_dimension_qa", {}).get("fields", {})
    qa_flags = data.get("qa_flags_and_alerts", {})
    vr = data.get("validation_rules", {})

    # [2] qa_report_schema: required fields + overall_qa_status enum
    print("\n[2] qa_report_schema required fields + overall_qa_status enum")
    for fname in ["qa_report_id", "report_period", "total_assessments_qa_reviewed", "overall_qa_status"]:
        if fname in qa_fields:
            ok(f"qa_report_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"qa_report_schema.fields.{fname} 缺失")
    qs_enum = set(qa_fields.get("overall_qa_status", {}).get("enum", []))
    if qs_enum == {"pass", "warning", "fail"}:
        ok("overall_qa_status enum {pass/warning/fail} ✓")
    else:
        fail(f"overall_qa_status enum {qs_enum} ≠ {{pass/warning/fail}}")

    # [3] item_quality_metrics: avg_discrimination IRT三模型 + _dao_guard
    print("\n[3] item_quality_metrics avg_discrimination_by_irt_model IRT三模型 + _dao_guard")
    disc_field = item_q.get("avg_discrimination_by_irt_model", {})
    disc_props = set(disc_field.get("properties", {}).keys())
    if disc_props == IRT_MODELS:
        ok("avg_discrimination_by_irt_model 1PL/2PL/3PL 三模型 ✓")
    else:
        fail(f"avg_discrimination_by_irt_model props {disc_props} ≠ {IRT_MODELS}")
    disc_guard = disc_field.get("_dao_guard", "")
    if "IRT" in disc_guard:
        ok("avg_discrimination_by_irt_model._dao_guard 含'IRT' ✓")
    else:
        fail(f"avg_discrimination_by_irt_model._dao_guard='{disc_guard}' 未含'IRT'")

    # [4] item_quality_metrics: flywheel_item_coverage 六飞轮 + _dao_guard
    print("\n[4] item_quality_metrics flywheel_item_coverage 六飞轮 + _dao_guard")
    fwc_field = item_q.get("flywheel_item_coverage", {})
    fwc_props = set(fwc_field.get("properties", {}).keys())
    if fwc_props == VALID_FLYWHEEL_NAMES:
        ok("flywheel_item_coverage 六飞轮全覆盖 ✓")
    else:
        fail(f"flywheel_item_coverage {fwc_props} ≠ {VALID_FLYWHEEL_NAMES}")
    fwc_guard = fwc_field.get("_dao_guard", "")
    if "六飞轮" in fwc_guard:
        ok("flywheel_item_coverage._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"flywheel_item_coverage._dao_guard='{fwc_guard}' 未含'六飞轮'")

    # [5] cat_performance_metrics: 5个性能字段
    print("\n[5] cat_performance_metrics 5个性能字段")
    cat_fields_required = [
        "avg_items_per_session", "avg_se_at_termination",
        "se_threshold_compliance_rate", "exposure_control_compliance_rate",
        "avg_cat_duration_minutes"
    ]
    for fname in cat_fields_required:
        if fname in cat_perf:
            ok(f"cat_performance_metrics.{fname} 存在 ✓")
        else:
            fail(f"cat_performance_metrics.{fname} 缺失")

    # [6] seven_stage_measurement_quality: stage_classification_consistency _dao_guard 含'七阶'
    print("\n[6] seven_stage_measurement_quality stage_classification_consistency _dao_guard")
    scc_guard = stage_mq.get("stage_classification_consistency", {}).get("_dao_guard", "")
    if "七阶" in scc_guard:
        ok("stage_classification_consistency._dao_guard 含'七阶' ✓")
    else:
        fail(f"stage_classification_consistency._dao_guard='{scc_guard}' 未含'七阶'")

    # [7] stage_boundary_se_by_stage 六条边界 + _dao_guard
    print("\n[7] stage_boundary_se_by_stage 六条边界 + _dao_guard 含'七阶'")
    boundary_field = stage_mq.get("stage_boundary_se_by_stage", {})
    boundary_props = set(boundary_field.get("properties", {}).keys())
    if boundary_props == STAGE_BOUNDARIES:
        ok(f"stage_boundary_se_by_stage 六条边界全覆盖 ✓")
    else:
        missing_b = STAGE_BOUNDARIES - boundary_props
        fail(f"stage_boundary_se_by_stage 缺少边界: {missing_b}")
    boundary_guard = boundary_field.get("_dao_guard", "")
    if "七阶" in boundary_guard:
        ok("stage_boundary_se_by_stage._dao_guard 含'七阶' ✓")
    else:
        fail(f"stage_boundary_se_by_stage._dao_guard='{boundary_guard}' 未含'七阶'")

    # [8] mece_dimension_qa: dimension_reliability MECE四维度 + _dao_guard
    print("\n[8] mece_dimension_qa dimension_reliability MECE四维度 + _dao_guard")
    dr_field = mece_qa.get("dimension_reliability", {})
    dr_props = {k.replace("_alpha", "") for k in dr_field.get("properties", {}).keys() if "_alpha" in k}
    if dr_props == MECE_DIMENSIONS:
        ok("dimension_reliability MECE 四维度 α 全覆盖 ✓")
    else:
        fail(f"dimension_reliability dims {dr_props} ≠ {MECE_DIMENSIONS}")
    dr_guard = dr_field.get("_dao_guard", "")
    if "MECE" in dr_guard:
        ok("dimension_reliability._dao_guard 含'MECE' ✓")
    else:
        fail(f"dimension_reliability._dao_guard='{dr_guard}' 未含'MECE'")

    # [9] dimension_discrimination_validity MECE相关 + _dao_guard
    print("\n[9] dimension_discrimination_validity MECE 相关矩阵 + _dao_guard")
    ddv_field = mece_qa.get("dimension_discrimination_validity", {})
    ddv_props = set(ddv_field.get("properties", {}).keys())
    expected_corr = {
        "M_E_exec_correlation", "M_C_correlation", "M_E_env_correlation",
        "E_exec_C_correlation", "E_exec_E_env_correlation", "C_E_env_correlation"
    }
    if ddv_props == expected_corr:
        ok("dimension_discrimination_validity 6对 MECE 相关 ✓")
    else:
        fail(f"dimension_discrimination_validity props {ddv_props} ≠ {expected_corr}")
    ddv_guard = ddv_field.get("_dao_guard", "")
    if "MECE" in ddv_guard:
        ok("dimension_discrimination_validity._dao_guard 含'MECE' ✓")
    else:
        fail(f"dimension_discrimination_validity._dao_guard='{ddv_guard}' 未含'MECE'")

    # [10] qa_flags_and_alerts: halt_conditions 含[HALT-CSO] + stage halt _dao_guard 含'七阶'
    print("\n[10] qa_flags_and_alerts halt_conditions [HALT-CSO] + 七阶 _dao_guard")
    halt_conditions = qa_flags.get("halt_conditions", [])
    halt_actions = [h.get("action", "") for h in halt_conditions]
    has_halt_cso = any("[HALT-CSO]" in a for a in halt_actions)
    if has_halt_cso:
        ok("qa_flags_and_alerts.halt_conditions 含[HALT-CSO] ✓")
    else:
        fail("qa_flags_and_alerts.halt_conditions 未含[HALT-CSO]")
    stage_halt_guards = [h.get("_dao_guard", "") for h in halt_conditions if "七阶" in h.get("_dao_guard", "")]
    if stage_halt_guards:
        ok("halt_conditions 含七阶道层漂移 _dao_guard ✓")
    else:
        fail("halt_conditions 缺少含'七阶'的 _dao_guard")

    # [11] validation_rules
    print("\n[11] validation_rules 合规")
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
    irt_vr = set(vr.get("irt_model_codes", []))
    if irt_vr == IRT_MODELS:
        ok("validation_rules.irt_model_codes 1PL/2PL/3PL ✓")
    else:
        fail(f"irt_model_codes {irt_vr} ≠ {IRT_MODELS}")
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
        print("  ✅ 测评质量保证 schema 验证 PASS — QA字段/IRT/七阶边界/MECE信效度/六飞轮/HALT-CSO/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
