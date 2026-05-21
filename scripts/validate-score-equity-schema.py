#!/usr/bin/env python3
"""
道层测评分数公平性 schema 验证脚本 v1.0
验证 pipeline-data/assessment-score-equity-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. equity_report_schema: 4个必填字段 + overall_equity_status enum
  3. dif_analysis_schema: dif_by_flywheel 六飞轮 + _dao_guard
  4. stage_threshold_equity: stage_thresholds_invariant _dao_guard 含'七阶'
  5. stage_threshold_equity: stage_distribution_equity_by_cohort 3基准组 + 七阶 + _dao_guard
  6. mece_dimension_equity: mece_invariance_by_dimension MECE四维度 + _dao_guard
  7. mece_dimension_equity: bottleneck_identification_equity MECE相关 + _dao_guard
  8. equity_remediation: halt_conditions 含[HALT-CSO] + 七阶 HALT _dao_guard
  9. validation_rules: 七阶/MECE/六飞轮/3基准组/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
EQUITY_PATH = REPO_ROOT / "pipeline-data" / "assessment-score-equity-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
VALID_COHORT_IDS = {"bm-national-avg", "bm-gaokao-ready", "bm-junior-high"}
MECE_INVARIANCE_KEYS = {"M_invariant", "E_exec_invariant", "C_invariant", "E_env_invariant"}

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
    print("  测评分数公平性 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not EQUITY_PATH.exists():
        fail(f"找不到文件: {EQUITY_PATH}")
        sys.exit(1)
    data = json.loads(EQUITY_PATH.read_text(encoding="utf-8"))
    ok("assessment-score-equity-schema.json 加载成功")

    eq_fields = data.get("equity_report_schema", {}).get("fields", {})
    dif = data.get("dif_analysis_schema", {}).get("fields", {})
    ste = data.get("stage_threshold_equity", {}).get("fields", {})
    mece_eq = data.get("mece_dimension_equity", {}).get("fields", {})
    remediation = data.get("equity_remediation", {})
    vr = data.get("validation_rules", {})

    # [2] equity_report_schema: 4个必填字段 + overall_equity_status enum
    print("\n[2] equity_report_schema 4个必填字段 + overall_equity_status enum")
    for fname in ["equity_report_id", "report_period", "total_respondents_analyzed", "overall_equity_status"]:
        if fname in eq_fields:
            ok(f"equity_report_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"equity_report_schema.fields.{fname} 缺失")
    oes_enum = set(eq_fields.get("overall_equity_status", {}).get("enum", []))
    if oes_enum == {"pass", "warning", "fail"}:
        ok("overall_equity_status enum {pass/warning/fail} ✓")
    else:
        fail(f"overall_equity_status enum {oes_enum} ≠ {{pass/warning/fail}}")

    # [3] dif_analysis_schema: dif_by_flywheel 六飞轮 + _dao_guard
    print("\n[3] dif_analysis_schema dif_by_flywheel 六飞轮 + _dao_guard")
    dbf_field = dif.get("dif_by_flywheel", {})
    dbf_props = set(dbf_field.get("properties", {}).keys())
    if dbf_props == VALID_FLYWHEEL_NAMES:
        ok("dif_by_flywheel 六飞轮全覆盖 ✓")
    else:
        fail(f"dif_by_flywheel {dbf_props} ≠ {VALID_FLYWHEEL_NAMES}")
    dbf_guard = dbf_field.get("_dao_guard", "")
    if "六飞轮" in dbf_guard:
        ok("dif_by_flywheel._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"dif_by_flywheel._dao_guard='{dbf_guard}' 未含'六飞轮'")

    # [4] stage_threshold_equity: stage_thresholds_invariant _dao_guard 含'七阶'
    print("\n[4] stage_threshold_equity stage_thresholds_invariant _dao_guard 含'七阶'")
    sti_guard = ste.get("stage_thresholds_invariant", {}).get("_dao_guard", "")
    if "七阶" in sti_guard:
        ok("stage_thresholds_invariant._dao_guard 含'七阶' ✓")
    else:
        fail(f"stage_thresholds_invariant._dao_guard='{sti_guard}' 未含'七阶'")

    # [5] stage_distribution_equity_by_cohort: 3基准组 + 七阶 + _dao_guard
    print("\n[5] stage_distribution_equity_by_cohort 3基准组 + 七阶 + _dao_guard")
    sdec_field = ste.get("stage_distribution_equity_by_cohort", {})
    sdec_cohorts = set(sdec_field.get("properties", {}).keys())
    if sdec_cohorts == VALID_COHORT_IDS:
        ok("stage_distribution_equity_by_cohort 3基准组全覆盖 ✓")
    else:
        fail(f"stage_distribution_equity_by_cohort cohorts {sdec_cohorts} ≠ {VALID_COHORT_IDS}")
    # Check that each cohort has 七阶 properties
    cohort_props = sdec_field.get("properties", {})
    for cohort_id in VALID_COHORT_IDS:
        cohort_stage_props = set(cohort_props.get(cohort_id, {}).get("properties", {}).keys())
        if cohort_stage_props == VALID_STAGE_NAMES:
            ok(f"{cohort_id} 七阶全覆盖 ✓")
        else:
            fail(f"{cohort_id} 七阶 {cohort_stage_props} ≠ {VALID_STAGE_NAMES}")
    sdec_guard = sdec_field.get("_dao_guard", "")
    if "七阶" in sdec_guard and "bm-national-avg" in sdec_guard:
        ok("stage_distribution_equity_by_cohort._dao_guard 含'七阶'+'bm-national-avg' ✓")
    else:
        fail(f"stage_distribution_equity_by_cohort._dao_guard='{sdec_guard}' 缺少关键词")

    # [6] mece_dimension_equity: mece_invariance_by_dimension MECE四维度 + _dao_guard
    print("\n[6] mece_dimension_equity mece_invariance_by_dimension MECE四维度 + _dao_guard")
    mid_field = mece_eq.get("mece_invariance_by_dimension", {})
    mid_props = set(mid_field.get("properties", {}).keys())
    if mid_props == MECE_INVARIANCE_KEYS:
        ok("mece_invariance_by_dimension MECE四维度 invariant 键全覆盖 ✓")
    else:
        fail(f"mece_invariance_by_dimension {mid_props} ≠ {MECE_INVARIANCE_KEYS}")
    mid_guard = mid_field.get("_dao_guard", "")
    if "MECE" in mid_guard:
        ok("mece_invariance_by_dimension._dao_guard 含'MECE' ✓")
    else:
        fail(f"mece_invariance_by_dimension._dao_guard='{mid_guard}' 未含'MECE'")

    # [7] bottleneck_identification_equity MECE相关 + _dao_guard
    print("\n[7] mece_dimension_equity bottleneck_identification_equity MECE + _dao_guard")
    bie_field = mece_eq.get("bottleneck_identification_equity", {})
    bie_props = set(bie_field.get("properties", {}).keys())
    expected_bie = {"M_rate_by_cohort", "E_exec_rate_by_cohort", "C_rate_by_cohort", "E_env_rate_by_cohort"}
    if bie_props == expected_bie:
        ok("bottleneck_identification_equity MECE四维度 rate_by_cohort ✓")
    else:
        fail(f"bottleneck_identification_equity {bie_props} ≠ {expected_bie}")
    bie_guard = bie_field.get("_dao_guard", "")
    if "MECE" in bie_guard:
        ok("bottleneck_identification_equity._dao_guard 含'MECE' ✓")
    else:
        fail(f"bottleneck_identification_equity._dao_guard='{bie_guard}' 未含'MECE'")

    # [8] equity_remediation: halt_conditions 含[HALT-CSO] + 七阶 HALT _dao_guard
    print("\n[8] equity_remediation halt_conditions [HALT-CSO] + 七阶 _dao_guard")
    halt_conditions = remediation.get("halt_conditions", [])
    halt_actions = [h.get("action", "") for h in halt_conditions]
    has_halt_cso = any("[HALT-CSO]" in a for a in halt_actions)
    if has_halt_cso:
        ok("equity_remediation.halt_conditions 含[HALT-CSO] ✓")
    else:
        fail("equity_remediation.halt_conditions 未含[HALT-CSO]")
    stage_halt_guards = [h.get("_dao_guard", "") for h in halt_conditions if "七阶" in h.get("_dao_guard", "")]
    if stage_halt_guards:
        ok("halt_conditions 含七阶公平 _dao_guard ✓")
    else:
        fail("halt_conditions 缺少含'七阶'的 _dao_guard")

    # [9] validation_rules
    print("\n[9] validation_rules 合规")
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
    cohort_vr = set(vr.get("benchmark_cohort_ids", []))
    if cohort_vr == VALID_COHORT_IDS:
        ok("validation_rules.benchmark_cohort_ids 3基准组 ✓")
    else:
        fail(f"benchmark_cohort_ids {cohort_vr} ≠ {VALID_COHORT_IDS}")
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
        print("  ✅ 测评分数公平性 schema 验证 PASS — DIF分析/七阶阈值/MECE不变性/3基准组/六飞轮/HALT-CSO/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
