#!/usr/bin/env python3
"""
道层测评人口统计 schema 验证脚本 v1.0
验证 pipeline-data/assessment-population-statistics-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. population_stats_schema: stage_distribution 七阶全覆盖 + _dao_guard
  3. mece_population_means: M/E_exec/C/E_env theta_mean/sd 字段 + _dao_guard
  4. flywheel_population_means: 六飞轮 theta_mean 全覆盖 + _dao_guard
  5. primary_bottleneck_distribution: MECE 四维度 + _dao_guard
  6. most_common_stage enum 七阶; weakest_flywheel_platform enum 六飞轮 + _dao_guard
  7. cohort_breakdown: 3基准组 + _dao_guard
  8. trend_analysis: 七阶/MECE/六飞轮 enum_guard + _dao_guard
  9. minimum_cell_size_rule: min=50 + _dao_guard 含'PIPL'
  10. validation_rules: 七阶/MECE/六飞轮/分布归一/最小样本/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
POPSTAT_PATH = REPO_ROOT / "pipeline-data" / "assessment-population-statistics-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
VALID_COHORT_IDS = {"bm-national-avg", "bm-gaokao-ready", "bm-junior-high"}

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
    print("  测评人口统计 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not POPSTAT_PATH.exists():
        fail(f"找不到文件: {POPSTAT_PATH}")
        sys.exit(1)
    data = json.loads(POPSTAT_PATH.read_text(encoding="utf-8"))
    ok("assessment-population-statistics-schema.json 加载成功")

    ps_fields = data.get("population_stats_schema", {}).get("fields", {})
    cohort = data.get("cohort_breakdown", {})
    trend = data.get("trend_analysis", {})
    mcsr = data.get("minimum_cell_size_rule", {})
    vr = data.get("validation_rules", {})

    # [2] stage_distribution 七阶 + _dao_guard
    print("\n[2] stage_distribution 七阶全覆盖 + _dao_guard")
    sd = ps_fields.get("stage_distribution", {})
    sd_props = set(sd.get("properties", {}).keys())
    if sd_props == VALID_STAGE_NAMES:
        ok("stage_distribution 七阶全覆盖 ✓")
    else:
        fail(f"stage_distribution properties {sd_props} ≠ {VALID_STAGE_NAMES}")
    sd_guard = sd.get("_dao_guard", "")
    if "七阶" in sd_guard and "1.0" in sd_guard:
        ok("stage_distribution._dao_guard 含'七阶'+'1.0' ✓")
    else:
        fail(f"stage_distribution._dao_guard='{sd_guard}' 未含'七阶'或'1.0'")

    # [3] mece_population_means MECE 四维度 + _dao_guard
    print("\n[3] mece_population_means MECE 四维度 + _dao_guard")
    mpm = ps_fields.get("mece_population_means", {})
    mpm_props = mpm.get("properties", {})
    mpm_dims = {k.replace("_theta_mean", "").replace("_theta_sd", "")
                for k in mpm_props.keys() if "_theta_mean" in k}
    if mpm_dims == MECE_DIMENSIONS:
        ok("mece_population_means MECE 四维度均值全覆盖 ✓")
    else:
        fail(f"mece_population_means dims {mpm_dims} ≠ {MECE_DIMENSIONS}")
    mpm_guard = mpm.get("_dao_guard", "")
    if "MECE" in mpm_guard:
        ok("mece_population_means._dao_guard 含'MECE' ✓")
    else:
        fail(f"mece_population_means._dao_guard='{mpm_guard}' 未含'MECE'")

    # [4] flywheel_population_means 六飞轮 + _dao_guard
    print("\n[4] flywheel_population_means 六飞轮 + _dao_guard")
    fpm = ps_fields.get("flywheel_population_means", {})
    fpm_props = fpm.get("properties", {})
    fpm_fw = {k.replace("_theta_mean", "") for k in fpm_props.keys() if "_theta_mean" in k}
    if fpm_fw == VALID_FLYWHEEL_NAMES:
        ok("flywheel_population_means 六飞轮均值全覆盖 ✓")
    else:
        fail(f"flywheel_population_means fw {fpm_fw} ≠ {VALID_FLYWHEEL_NAMES}")
    fpm_guard = fpm.get("_dao_guard", "")
    if "六飞轮" in fpm_guard:
        ok("flywheel_population_means._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"flywheel_population_means._dao_guard='{fpm_guard}' 未含'六飞轮'")

    # [5] primary_bottleneck_distribution MECE + _dao_guard
    print("\n[5] primary_bottleneck_distribution MECE + _dao_guard")
    pbd = ps_fields.get("primary_bottleneck_distribution", {})
    pbd_props = set(pbd.get("properties", {}).keys())
    if pbd_props == MECE_DIMENSIONS:
        ok("primary_bottleneck_distribution MECE 四维度 ✓")
    else:
        fail(f"primary_bottleneck_distribution {pbd_props} ≠ {MECE_DIMENSIONS}")
    pbd_guard = pbd.get("_dao_guard", "")
    if "MECE" in pbd_guard and "1.0" in pbd_guard:
        ok("primary_bottleneck_distribution._dao_guard 含'MECE'+'1.0' ✓")
    else:
        fail(f"primary_bottleneck_distribution._dao_guard='{pbd_guard}' 未含'MECE'或'1.0'")

    # [6] most_common_stage enum + weakest_flywheel_platform enum + _dao_guard
    print("\n[6] most_common_stage enum 七阶 + weakest_flywheel_platform 六飞轮 + _dao_guard")
    mcs_enum = set(ps_fields.get("most_common_stage", {}).get("enum", []))
    if mcs_enum == VALID_STAGE_NAMES:
        ok("most_common_stage enum 七阶全覆盖 ✓")
    else:
        fail(f"most_common_stage enum {mcs_enum} ≠ {VALID_STAGE_NAMES}")
    wfp_field = ps_fields.get("weakest_flywheel_platform", {})
    wfp_enum = set(wfp_field.get("enum", []))
    if wfp_enum == VALID_FLYWHEEL_NAMES:
        ok("weakest_flywheel_platform enum 六飞轮全覆盖 ✓")
    else:
        fail(f"weakest_flywheel_platform enum {wfp_enum} ≠ {VALID_FLYWHEEL_NAMES}")
    wfp_guard = wfp_field.get("_dao_guard", "")
    if "六飞轮" in wfp_guard:
        ok("weakest_flywheel_platform._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"weakest_flywheel_platform._dao_guard='{wfp_guard}' 未含'六飞轮'")

    # [7] cohort_breakdown 3基准组 + _dao_guard
    print("\n[7] cohort_breakdown 3基准组 + _dao_guard")
    cohort_ids = set(cohort.get("cohort_ids", []))
    if cohort_ids == VALID_COHORT_IDS:
        ok(f"cohort_breakdown.cohort_ids 3基准组全覆盖 ✓ {sorted(cohort_ids)}")
    else:
        fail(f"cohort_ids {cohort_ids} ≠ {VALID_COHORT_IDS}")
    cohort_guard = cohort.get("_dao_guard", "")
    if "bm-national-avg" in cohort_guard and "bm-gaokao-ready" in cohort_guard:
        ok("cohort_breakdown._dao_guard 含基准组名称 ✓")
    else:
        fail(f"cohort_breakdown._dao_guard='{cohort_guard}' 未含基准组名称")

    # [8] trend_analysis 七阶/六飞轮 enum_guard + _dao_guard
    print("\n[8] trend_analysis 七阶/六飞轮 enum_guard + _dao_guard")
    stage_trend = trend.get("stage_trend", {})
    stage_eg = set(stage_trend.get("stage_enum_guard", []))
    if stage_eg == VALID_STAGE_NAMES:
        ok("trend_analysis.stage_trend.stage_enum_guard 七阶全覆盖 ✓")
    else:
        fail(f"stage_trend.stage_enum_guard {stage_eg} ≠ {VALID_STAGE_NAMES}")
    st_guard = stage_trend.get("_dao_guard", "")
    if "七阶" in st_guard:
        ok("stage_trend._dao_guard 含'七阶' ✓")
    else:
        fail(f"stage_trend._dao_guard='{st_guard}' 未含'七阶'")
    fw_trend = trend.get("flywheel_trend", {})
    fw_eg = set(fw_trend.get("flywheel_enum_guard", []))
    if fw_eg == VALID_FLYWHEEL_NAMES:
        ok("trend_analysis.flywheel_trend.flywheel_enum_guard 六飞轮全覆盖 ✓")
    else:
        fail(f"flywheel_trend.flywheel_enum_guard {fw_eg} ≠ {VALID_FLYWHEEL_NAMES}")
    fw_t_guard = fw_trend.get("_dao_guard", "")
    if "六飞轮" in fw_t_guard:
        ok("flywheel_trend._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"flywheel_trend._dao_guard='{fw_t_guard}' 未含'六飞轮'")

    # [9] minimum_cell_size_rule min=50 + PIPL _dao_guard
    print("\n[9] minimum_cell_size_rule min=50 + _dao_guard 含'PIPL'")
    min_cell = mcsr.get("min_cell_size", 0)
    if min_cell >= 50:
        ok(f"minimum_cell_size_rule.min_cell_size={min_cell} ≥ 50 ✓")
    else:
        fail(f"minimum_cell_size_rule.min_cell_size={min_cell} < 50")
    mcsr_guard = mcsr.get("_dao_guard", "")
    if "PIPL" in mcsr_guard:
        ok("minimum_cell_size_rule._dao_guard 含'PIPL' ✓")
    else:
        fail(f"minimum_cell_size_rule._dao_guard='{mcsr_guard}' 未含'PIPL'")

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
    sd_constraint = vr.get("stage_distribution_sum_constraint", "")
    if "1.0" in sd_constraint:
        ok("validation_rules.stage_distribution_sum_constraint 含 1.0 ✓")
    else:
        fail(f"stage_distribution_sum_constraint='{sd_constraint}' 未含'1.0'")
    min_assess = vr.get("min_assessments_for_output", 0)
    if min_assess >= 50:
        ok(f"validation_rules.min_assessments_for_output={min_assess} ≥ 50 ✓")
    else:
        fail(f"min_assessments_for_output={min_assess} < 50")
    cohort_vr = set(vr.get("cohort_ids", []))
    if cohort_vr == VALID_COHORT_IDS:
        ok("validation_rules.cohort_ids 3基准组 ✓")
    else:
        fail(f"validation_rules.cohort_ids {cohort_vr} ≠ {VALID_COHORT_IDS}")
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
        print("  ✅ 测评人口统计 schema 验证 PASS — 七阶分布/MECE/六飞轮/3基准组/趋势/最小样本/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
