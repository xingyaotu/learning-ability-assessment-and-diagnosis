#!/usr/bin/env python3
"""
道层学习力纵向追踪 schema 验证脚本 v1.0
验证 pipeline-data/assessment-longitudinal-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. longitudinal_record_schema 核心字段: 9个必填字段
  3. mece_trajectory 4个 MECE 维度 + _dao_guard
  4. flywheel_trajectory 6个飞轮键 + _dao_guard 含'六飞轮'
  5. stage_history items 含 stage_estimate enum = 七阶
  6. summary_stats 字段: initial/current_stage + dominant_bottleneck + flywheel
  7. trajectory_analysis_rules: minimum_sessions=3 + plateau_detection + _dao_guard 含七阶
  8. cohort_comparison_schema: norm_group enum 4个 + mece_dimension_percentiles 四维度
  9. validation_rules: mece_dimension_codes/flywheel_valid_names/seven_stage_valid_names/pipl_constraints
  10. PIPL 合规声明
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
LONGITUDINAL_PATH = REPO_ROOT / "pipeline-data" / "assessment-longitudinal-schema.json"

REQUIRED_LONGITUDINAL_FIELDS = {
    "longitudinal_id", "student_id", "enrollment_date", "total_sessions",
    "assessment_history", "mece_trajectory", "flywheel_trajectory",
    "stage_history", "summary_stats"
}
VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
NORM_GROUP_IDS = {"ng-junior-high", "ng-senior-high", "ng-math-focused", "ng-gaokao-prep"}

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
    print("  学习力纵向追踪 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not LONGITUDINAL_PATH.exists():
        fail(f"找不到文件: {LONGITUDINAL_PATH}")
        sys.exit(1)
    data = json.loads(LONGITUDINAL_PATH.read_text(encoding="utf-8"))
    ok("assessment-longitudinal-schema.json 加载成功")

    rec_schema = data.get("longitudinal_record_schema", {})
    fields = rec_schema.get("fields", {})

    # [2] 核心字段
    print("\n[2] longitudinal_record_schema 9个核心字段")
    vr_fields = data.get("validation_rules", {}).get("required_fields", [])
    missing_f = REQUIRED_LONGITUDINAL_FIELDS - set(vr_fields)
    if missing_f:
        fail(f"validation_rules.required_fields 缺少: {missing_f}")
    else:
        ok(f"validation_rules.required_fields 9个字段全覆盖 ✓")

    for fname in REQUIRED_LONGITUDINAL_FIELDS:
        if fname in fields:
            ok(f"longitudinal_record_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"longitudinal_record_schema.fields.{fname} 缺失")

    # [3] mece_trajectory 4维度 + _dao_guard
    print("\n[3] mece_trajectory MECE 四维度 + _dao_guard")
    mt = fields.get("mece_trajectory", {})
    mt_props = mt.get("properties", {})
    mece_trajectory_keys = {k.replace("_theta", "") for k in mt_props.keys() if k.endswith("_theta")}
    missing_mece = MECE_DIMENSIONS - mece_trajectory_keys
    if missing_mece:
        fail(f"mece_trajectory 缺少维度: {missing_mece}")
    else:
        ok(f"mece_trajectory 四维度全覆盖 {sorted(mece_trajectory_keys)} ✓")
    mt_guard = mt.get("_dao_guard", "")
    if "MECE" in mt_guard and "M/E_exec/C/E_env" in mt_guard:
        ok("mece_trajectory._dao_guard MECE 守护 ✓")
    else:
        fail(f"mece_trajectory._dao_guard='{mt_guard}' 未含完整 MECE 代码")

    # [4] flywheel_trajectory 六飞轮 + _dao_guard
    print("\n[4] flywheel_trajectory 六飞轮 + _dao_guard")
    ft = fields.get("flywheel_trajectory", {})
    ft_props = ft.get("properties", {})
    fw_keys = {k.replace("_theta", "") for k in ft_props.keys() if k.endswith("_theta")}
    missing_fw = VALID_FLYWHEEL_NAMES - fw_keys
    if missing_fw:
        fail(f"flywheel_trajectory 缺少飞轮: {missing_fw}")
    elif len(fw_keys) == 6:
        ok(f"flywheel_trajectory 六飞轮全覆盖 {sorted(fw_keys)} ✓")
    else:
        fail(f"flywheel_trajectory 飞轮数量 {len(fw_keys)} ≠ 6")
    ft_guard = ft.get("_dao_guard", "")
    if "六飞轮" in ft_guard and "计划" in ft_guard and "考试" in ft_guard:
        ok("flywheel_trajectory._dao_guard 六飞轮守护 ✓")
    else:
        fail(f"flywheel_trajectory._dao_guard='{ft_guard}' 六飞轮守护不完整")

    # [5] stage_history stage_estimate enum = 七阶
    print("\n[5] stage_history stage_estimate 七阶枚举")
    sh = fields.get("stage_history", {})
    sh_items = sh.get("items", {})
    se_enum = set(sh_items.get("stage_estimate", {}).get("enum", []))
    missing_st = VALID_STAGE_NAMES - se_enum
    if missing_st:
        fail(f"stage_history.stage_estimate enum 缺少: {missing_st}")
    elif len(se_enum) == 7:
        ok("stage_history.stage_estimate enum 七阶全覆盖 ✓")
    else:
        fail(f"stage_history.stage_estimate enum 数量 {len(se_enum)} ≠ 7")

    # [6] summary_stats 字段
    print("\n[6] summary_stats 字段验证")
    ss = fields.get("summary_stats", {})
    ss_props = ss.get("properties", {})
    required_ss = {"initial_stage", "current_stage", "stage_advancement_count",
                   "dominant_bottleneck_dimension", "strongest_flywheel", "weakest_flywheel"}
    missing_ss = required_ss - set(ss_props.keys())
    if missing_ss:
        fail(f"summary_stats 缺少字段: {missing_ss}")
    else:
        ok(f"summary_stats {len(ss_props)}个字段 核心字段全覆盖 ✓")

    bn_enum = set(ss_props.get("dominant_bottleneck_dimension", {}).get("enum", []))
    if bn_enum == MECE_DIMENSIONS:
        ok("summary_stats.dominant_bottleneck_dimension enum MECE 四维度 ✓")
    else:
        fail(f"summary_stats.dominant_bottleneck_dimension enum {bn_enum} ≠ {MECE_DIMENSIONS}")

    fw_enum_ss = set(ss_props.get("strongest_flywheel", {}).get("enum", []))
    if fw_enum_ss == VALID_FLYWHEEL_NAMES:
        ok("summary_stats.strongest_flywheel enum 六飞轮 ✓")
    else:
        fail(f"summary_stats.strongest_flywheel enum {fw_enum_ss} ≠ {VALID_FLYWHEEL_NAMES}")

    # [7] trajectory_analysis_rules
    print("\n[7] trajectory_analysis_rules 分析规则")
    tar = data.get("trajectory_analysis_rules", {})
    min_sess = tar.get("minimum_sessions_for_trend", 0)
    if min_sess >= 3:
        ok(f"minimum_sessions_for_trend={min_sess} ≥ 3 ✓")
    else:
        fail(f"minimum_sessions_for_trend={min_sess} < 3")
    plateau = tar.get("plateau_detection", {})
    if plateau.get("consecutive_sessions") and plateau.get("plateau_delta") is not None:
        ok(f"plateau_detection 配置完整 (n={plateau['consecutive_sessions']}, delta={plateau['plateau_delta']}) ✓")
    else:
        fail("plateau_detection 配置不完整")
    tar_guard = tar.get("_dao_guard", "")
    if "七阶" in tar_guard:
        ok("trajectory_analysis_rules._dao_guard 含'七阶' ✓")
    else:
        fail(f"trajectory_analysis_rules._dao_guard='{tar_guard}' 未含'七阶'")

    # [8] cohort_comparison_schema
    print("\n[8] cohort_comparison_schema 常模组对比")
    ccs = data.get("cohort_comparison_schema", {})
    ccs_fields = ccs.get("fields", {})
    ng_enum = set(ccs_fields.get("norm_group_id", {}).get("enum", []))
    if ng_enum == NORM_GROUP_IDS:
        ok(f"cohort_comparison_schema.norm_group_id enum 4个常模组 ✓")
    else:
        fail(f"norm_group_id enum {ng_enum} ≠ {NORM_GROUP_IDS}")
    mece_pct = ccs_fields.get("mece_dimension_percentiles", {})
    mece_pct_keys = {k.replace("_percentile", "") for k in mece_pct.keys() if k.endswith("_percentile")}
    if mece_pct_keys == MECE_DIMENSIONS:
        ok("cohort_comparison_schema.mece_dimension_percentiles 四维度 ✓")
    else:
        fail(f"mece_dimension_percentiles 维度 {mece_pct_keys} ≠ {MECE_DIMENSIONS}")

    # [9] validation_rules
    print("\n[9] validation_rules 合规")
    vr = data.get("validation_rules", {})
    mece_codes = set(vr.get("mece_dimension_codes", []))
    if mece_codes == MECE_DIMENSIONS:
        ok("validation_rules.mece_dimension_codes MECE 四维度 ✓")
    else:
        fail(f"validation_rules.mece_dimension_codes {mece_codes} ≠ {MECE_DIMENSIONS}")

    fw_names_vr = set(vr.get("flywheel_valid_names", []))
    missing_fw_vr = VALID_FLYWHEEL_NAMES - fw_names_vr
    if missing_fw_vr:
        fail(f"validation_rules.flywheel_valid_names 缺少: {missing_fw_vr}")
    elif len(fw_names_vr) == 6:
        ok("validation_rules.flywheel_valid_names 六飞轮全覆盖 ✓")
    else:
        fail(f"validation_rules.flywheel_valid_names 数量 {len(fw_names_vr)} ≠ 6")

    stage_names_vr = set(vr.get("seven_stage_valid_names", []))
    missing_st_vr = VALID_STAGE_NAMES - stage_names_vr
    if missing_st_vr:
        fail(f"validation_rules.seven_stage_valid_names 缺少: {missing_st_vr}")
    elif len(stage_names_vr) == 7:
        ok("validation_rules.seven_stage_valid_names 七阶全覆盖 ✓")
    else:
        fail(f"validation_rules.seven_stage_valid_names 数量 {len(stage_names_vr)} ≠ 7")

    traj_constraint = vr.get("trajectory_length_constraint", "")
    if "total_sessions" in traj_constraint and "assessment_history" in traj_constraint:
        ok("validation_rules.trajectory_length_constraint 存在 ✓")
    else:
        fail("validation_rules.trajectory_length_constraint 缺失或不完整")

    # [10] PIPL 合规
    print("\n[10] PIPL 合规")
    pipl_meta = data.get("_meta", {}).get("pipl_note", "")
    if "PIPL" in pipl_meta and "匿名" in pipl_meta:
        ok("_meta.pipl_note PIPL 合规声明 ✓")
    else:
        fail("_meta.pipl_note 缺少 PIPL 合规声明")
    pipl_vr = vr.get("pipl_constraints", "")
    if "PIPL" in pipl_vr and "匿名" in pipl_vr:
        ok("validation_rules.pipl_constraints 存在 ✓")
    else:
        fail("validation_rules.pipl_constraints 缺失")
    student_id_field = fields.get("student_id", {})
    if "匿名" in str(student_id_field):
        ok("student_id 字段含匿名 ID 说明 ✓")
    else:
        fail("student_id 字段未含匿名 ID 说明")

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
        print("  ✅ 学习力纵向追踪 schema 验证 PASS — MECE/七阶/六飞轮纵向追踪全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
