#!/usr/bin/env python3
"""
道层测评会话 schema 验证脚本 v1.0
验证 pipeline-data/assessment-session-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. session_record_schema 核心字段完整性
  3. item_responses 子字段完整
  4. session_type enum 合规
  5. stopping_reason enum 合规
  6. stage_name enum 七阶合规
  7. MECE 四维度字段存在 (mece_profile)
  8. flywheels_result 六飞轮键守护
  9. session_summary_schema 核心字段 + theta_trajectory
  10. flywheel_session_constraints _dao_guard 存在
  11. validation_rules 六飞轮守护 + PIPL
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
SESSION_PATH = REPO_ROOT / "pipeline-data" / "assessment-session-schema.json"

SEVEN_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
VALID_FLYWHEEL_KEYS = {
    "计划_theta", "预习_theta", "复习_theta",
    "听课_theta", "作业_theta", "考试_theta"
}
VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
REQUIRED_SESSION_FIELDS = {
    "session_id", "student_id", "tool_id", "subject", "session_type",
    "start_time", "end_time", "item_responses", "stopping_reason",
    "items_administered", "dimension_results", "tool_result", "data_quality"
}
REQUIRED_SUMMARY_FIELDS = {
    "summary_id", "student_id", "tool_id", "subject",
    "sessions", "theta_trajectory", "stage_history"
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
    print("  测评会话 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not SESSION_PATH.exists():
        fail(f"找不到文件: {SESSION_PATH}")
        sys.exit(1)
    data = json.loads(SESSION_PATH.read_text(encoding="utf-8"))
    ok("assessment-session-schema.json 加载成功")

    srs = data.get("session_record_schema", {}).get("fields", {})

    # [2] session_record_schema 核心字段
    print("\n[2] session_record_schema 核心字段")
    missing_f = REQUIRED_SESSION_FIELDS - set(srs.keys())
    if missing_f:
        fail(f"session_record_schema 缺少字段: {missing_f}")
    else:
        ok(f"session_record_schema {len(srs)}个字段 核心字段全覆盖 ✓")

    # subject enum
    subj_enum = srs.get("subject", {}).get("enum", [])
    if len(subj_enum) >= 9:
        ok(f"subject enum {len(subj_enum)}个科目 ✓")
    else:
        fail(f"subject enum 仅 {len(subj_enum)} 个科目 < 9")

    # [3] item_responses 子字段
    print("\n[3] item_responses 子字段")
    ir_items = srs.get("item_responses", {}).get("items", {})
    required_ir = {"response_seq", "item_id", "dimension_id", "stage_target",
                   "response_value", "theta_estimate_after", "se_after"}
    missing_ir = required_ir - set(ir_items.keys())
    if missing_ir:
        fail(f"item_responses.items 缺少字段: {missing_ir}")
    else:
        ok(f"item_responses.items {len(ir_items)}个字段 核心字段全覆盖 ✓")

    st_min = ir_items.get("stage_target", {}).get("minimum", 0)
    st_max = ir_items.get("stage_target", {}).get("maximum", 0)
    if st_min == 1 and st_max == 7:
        ok("item_responses stage_target range [1,7] ✓")
    else:
        fail(f"item_responses stage_target range [{st_min},{st_max}] ≠ [1,7]")

    # [4] session_type enum
    print("\n[4] session_type enum")
    st_enum = set(srs.get("session_type", {}).get("enum", []))
    required_st = {"initial", "progress", "final", "diagnostic"}
    missing_st = required_st - st_enum
    if missing_st:
        fail(f"session_type enum 缺少: {missing_st}")
    else:
        ok(f"session_type enum {sorted(st_enum)} ✓")

    # [5] stopping_reason enum
    print("\n[5] stopping_reason enum")
    sr_enum = set(srs.get("stopping_reason", {}).get("enum", []))
    required_sr = {"se_threshold_met", "max_items_reached", "min_items_with_se_met", "time_limit"}
    missing_sr = required_sr - sr_enum
    if missing_sr:
        fail(f"stopping_reason enum 缺少: {missing_sr}")
    else:
        ok(f"stopping_reason enum {sorted(sr_enum)} ✓")

    # [6] stage_name enum 七阶
    print("\n[6] stage_name enum 七阶合规")
    tool_result = srs.get("tool_result", {}).get("properties", {})
    sn_enum = set(tool_result.get("stage_name", {}).get("enum", []))
    missing_sn = SEVEN_STAGE_NAMES - sn_enum
    if missing_sn:
        fail(f"stage_name enum 缺少: {missing_sn}")
    elif len(sn_enum) == 7:
        ok(f"stage_name enum 七阶全覆盖 ✓")
    else:
        fail(f"stage_name enum 数量 {len(sn_enum)} ≠ 7")

    # overall_stage range
    os_min = tool_result.get("overall_stage", {}).get("minimum", 0)
    os_max = tool_result.get("overall_stage", {}).get("maximum", 0)
    if os_min == 1 and os_max == 7:
        ok("tool_result.overall_stage range [1,7] ✓")
    else:
        fail(f"tool_result.overall_stage range [{os_min},{os_max}] ≠ [1,7]")

    # [7] MECE mece_profile 四维度
    print("\n[7] mece_profile 四维度字段")
    mece_props = tool_result.get("mece_profile", {}).get("properties", {})
    mece_keys = {"M_theta", "E_exec_theta", "C_theta", "E_env_theta", "composite_theta"}
    missing_mece = mece_keys - set(mece_props.keys())
    if missing_mece:
        fail(f"mece_profile 缺少维度: {missing_mece}")
    else:
        ok(f"mece_profile {len(mece_props)}个维度字段 ✓ {sorted(mece_props.keys())}")

    # [8] flywheels_result 六飞轮键
    print("\n[8] flywheels_result 六飞轮键守护")
    fw_props = srs.get("flywheels_result", {}).get("properties", {})
    found_fw_keys = set(fw_props.keys())
    missing_fw_keys = VALID_FLYWHEEL_KEYS - found_fw_keys
    if missing_fw_keys:
        fail(f"flywheels_result 缺少键: {missing_fw_keys}")
    elif len(found_fw_keys) == 6:
        ok(f"flywheels_result 六飞轮键全覆盖 ✓ {sorted(found_fw_keys)}")
    else:
        fail(f"flywheels_result 键数量 {len(found_fw_keys)} ≠ 6")

    # [9] session_summary_schema
    print("\n[9] session_summary_schema 字段")
    sss = data.get("session_summary_schema", {}).get("fields", {})
    missing_sss = REQUIRED_SUMMARY_FIELDS - set(sss.keys())
    if missing_sss:
        fail(f"session_summary_schema 缺少字段: {missing_sss}")
    else:
        ok(f"session_summary_schema {len(sss)}个字段 核心字段全覆盖 ✓")

    # theta_trajectory properties
    tt_props = sss.get("theta_trajectory", {}).get("properties", {})
    required_tt = {"initial_theta", "latest_theta", "theta_delta", "trend"}
    missing_tt = required_tt - set(tt_props.keys())
    if missing_tt:
        fail(f"theta_trajectory 缺少字段: {missing_tt}")
    else:
        ok(f"theta_trajectory {len(tt_props)}个字段 ✓")

    # stage_history stage_name enum
    sh_items = sss.get("stage_history", {}).get("items", {})
    sh_sn_enum = set(sh_items.get("stage_name", {}).get("enum", []))
    if sh_sn_enum == SEVEN_STAGE_NAMES:
        ok("stage_history.stage_name 七阶枚举 ✓")
    else:
        fail(f"stage_history.stage_name enum 不完整: {sh_sn_enum}")

    # [10] flywheel_session_constraints _dao_guard
    print("\n[10] flywheel_session_constraints 道层守护")
    fsc = data.get("flywheel_session_constraints", {})
    fw_order = fsc.get("six_flywheel_dim_order", [])
    if set(fw_order) == VALID_FLYWHEEL_NAMES and len(fw_order) == 6:
        ok(f"six_flywheel_dim_order 六飞轮完整 ✓ {fw_order}")
    else:
        fail(f"six_flywheel_dim_order 不完整: {fw_order}")
    if "_dao_guard" in fsc:
        ok("flywheel_session_constraints _dao_guard 存在 ✓")
    else:
        fail("flywheel_session_constraints _dao_guard 缺失")

    # [11] validation_rules 六飞轮 + PIPL
    print("\n[11] validation_rules 六飞轮守护 + PIPL")
    vr = data.get("validation_rules", {})
    fw_result_keys = set(vr.get("six_flywheel_result_keys", []))
    missing_fw_vr = VALID_FLYWHEEL_KEYS - fw_result_keys
    if missing_fw_vr:
        fail(f"validation_rules.six_flywheel_result_keys 缺少: {missing_fw_vr}")
    elif len(fw_result_keys) == 6:
        ok("validation_rules.six_flywheel_result_keys 六飞轮全覆盖 ✓")
    else:
        fail(f"six_flywheel_result_keys 数量 {len(fw_result_keys)} ≠ 6")

    stage_enum_vr = set(vr.get("stage_enum", []))
    if stage_enum_vr == SEVEN_STAGE_NAMES:
        ok("validation_rules.stage_enum 七阶完整 ✓")
    else:
        fail(f"validation_rules.stage_enum 不完整: {stage_enum_vr}")

    pipl_vr = vr.get("pipl_constraints", "")
    if "匿名" in pipl_vr or "PIPL" in pipl_vr:
        ok("validation_rules.pipl_constraints 存在 ✓")
    else:
        fail("validation_rules.pipl_constraints 缺失")

    pipl_meta = data.get("_meta", {}).get("pipl_note", "")
    if "PIPL" in pipl_meta and "匿名" in pipl_meta:
        ok("_meta.pipl_note PIPL 合规声明 ✓")
    else:
        fail("_meta.pipl_note 缺少 PIPL 合规声明")

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
        print("  ✅ 测评会话 schema 验证 PASS — CAT 会话结构全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
