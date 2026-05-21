#!/usr/bin/env python3
"""
道层测评自适应路由 schema 验证脚本 v1.0
验证 pipeline-data/assessment-adaptive-routing-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. routing_decision_schema: 4个必填字段
  3. stage_estimated enum 七阶 + _dao_guard 含'七阶'+'θ'
  4. flywheel_being_assessed enum 六飞轮 + _dao_guard 含'六飞轮'
  5. mece_dimension_being_assessed enum MECE + _dao_guard 含'MECE'
  6. routing_action enum 六动作 + _dao_guard
  7. theta_to_stage_routing_rules: stage_sequence 七阶 + _dao_guard 含'七阶'+'θ'
  8. flywheel_routing_matrix: flywheel_sequence 六飞轮 + _dao_guard 含'六飞轮'
  9. mece_dimension_routing: dimension_sequence_default MECE + _dao_guard 含'MECE'
  10. stopping_rules: se_threshold_by_stage 七阶 + _dao_guard 含'七阶'
  11. exposure_control_config._dao_guard 含'Sympson-Hetter'
  12. validation_rules: stage_sequence/flywheel_sequence/七阶/MECE/六飞轮/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
ROUTING_PATH = REPO_ROOT / "pipeline-data" / "assessment-adaptive-routing-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
ROUTING_ACTIONS = {
    "continue-same-flywheel", "switch-flywheel", "switch-mece-dimension",
    "terminate-se-met", "terminate-max-items", "terminate-time-limit"
}
REQUIRED_ROUTING_FIELDS = {
    "routing_decision_id", "assessment_session_id", "item_number", "routing_action"
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
    print("  测评自适应路由 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not ROUTING_PATH.exists():
        fail(f"找不到文件: {ROUTING_PATH}")
        sys.exit(1)
    data = json.loads(ROUTING_PATH.read_text(encoding="utf-8"))
    ok("assessment-adaptive-routing-schema.json 加载成功")

    rd_fields = data.get("routing_decision_schema", {}).get("fields", {})
    tts_rules = data.get("theta_to_stage_routing_rules", {})
    fw_matrix = data.get("flywheel_routing_matrix", {})
    mece_routing = data.get("mece_dimension_routing", {})
    stopping = data.get("stopping_rules", {})
    exposure = data.get("exposure_control_config", {})
    vr = data.get("validation_rules", {})

    # [2] routing_decision_schema: 4个必填字段
    print("\n[2] routing_decision_schema 4个必填字段")
    for fname in REQUIRED_ROUTING_FIELDS:
        if fname in rd_fields:
            ok(f"routing_decision_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"routing_decision_schema.fields.{fname} 缺失")

    # [3] stage_estimated enum 七阶 + _dao_guard 含'七阶'+'θ'
    print("\n[3] stage_estimated enum 七阶 + _dao_guard 含'七阶'+'θ'")
    se_field = rd_fields.get("stage_estimated", {})
    se_enum = set(se_field.get("enum", []))
    if se_enum == VALID_STAGE_NAMES:
        ok("stage_estimated enum 七阶全覆盖 ✓")
    else:
        fail(f"stage_estimated enum {se_enum} ≠ {VALID_STAGE_NAMES}")
    se_guard = se_field.get("_dao_guard", "")
    if "七阶" in se_guard and "θ" in se_guard:
        ok("stage_estimated._dao_guard 含'七阶'+'θ' ✓")
    else:
        fail(f"stage_estimated._dao_guard='{se_guard}' 缺少关键词")

    # [4] flywheel_being_assessed enum 六飞轮 + _dao_guard
    print("\n[4] flywheel_being_assessed enum 六飞轮 + _dao_guard")
    fba_field = rd_fields.get("flywheel_being_assessed", {})
    fba_enum = set(fba_field.get("enum", []))
    if fba_enum == VALID_FLYWHEEL_NAMES:
        ok("flywheel_being_assessed enum 六飞轮全覆盖 ✓")
    else:
        fail(f"flywheel_being_assessed enum {fba_enum} ≠ {VALID_FLYWHEEL_NAMES}")
    fba_guard = fba_field.get("_dao_guard", "")
    if "六飞轮" in fba_guard:
        ok("flywheel_being_assessed._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"flywheel_being_assessed._dao_guard='{fba_guard}' 未含'六飞轮'")

    # [5] mece_dimension_being_assessed enum MECE + _dao_guard
    print("\n[5] mece_dimension_being_assessed enum MECE + _dao_guard")
    mdba_field = rd_fields.get("mece_dimension_being_assessed", {})
    mdba_enum = set(mdba_field.get("enum", []))
    if mdba_enum == MECE_DIMENSIONS:
        ok("mece_dimension_being_assessed enum MECE 四维度 ✓")
    else:
        fail(f"mece_dimension_being_assessed enum {mdba_enum} ≠ {MECE_DIMENSIONS}")
    mdba_guard = mdba_field.get("_dao_guard", "")
    if "MECE" in mdba_guard:
        ok("mece_dimension_being_assessed._dao_guard 含'MECE' ✓")
    else:
        fail(f"mece_dimension_being_assessed._dao_guard='{mdba_guard}' 未含'MECE'")

    # [6] routing_action enum 六动作 + _dao_guard
    print("\n[6] routing_action enum 六动作 + _dao_guard")
    ra_field = rd_fields.get("routing_action", {})
    ra_enum = set(ra_field.get("enum", []))
    if ra_enum == ROUTING_ACTIONS:
        ok("routing_action enum 六种动作全覆盖 ✓")
    else:
        fail(f"routing_action enum {ra_enum} ≠ {ROUTING_ACTIONS}")
    ra_guard = ra_field.get("_dao_guard", "")
    if "飞轮" in ra_guard and "MECE" in ra_guard:
        ok("routing_action._dao_guard 含'飞轮'+'MECE' ✓")
    else:
        fail(f"routing_action._dao_guard='{ra_guard}' 缺少关键词")

    # [7] theta_to_stage_routing_rules: stage_sequence 七阶 + _dao_guard
    print("\n[7] theta_to_stage_routing_rules stage_sequence 七阶 + _dao_guard")
    stage_seq = set(tts_rules.get("stage_sequence", []))
    if stage_seq == VALID_STAGE_NAMES:
        ok("theta_to_stage_routing_rules.stage_sequence 七阶全覆盖 ✓")
    else:
        fail(f"stage_sequence {stage_seq} ≠ {VALID_STAGE_NAMES}")
    tts_guard = tts_rules.get("_dao_guard", "")
    if "七阶" in tts_guard and "θ" in tts_guard:
        ok("theta_to_stage_routing_rules._dao_guard 含'七阶'+'θ' ✓")
    else:
        fail(f"theta_to_stage_routing_rules._dao_guard='{tts_guard}' 缺少关键词")

    # [8] flywheel_routing_matrix: flywheel_sequence 六飞轮 + _dao_guard
    print("\n[8] flywheel_routing_matrix flywheel_sequence 六飞轮 + _dao_guard")
    fw_seq = set(fw_matrix.get("flywheel_sequence", []))
    if fw_seq == VALID_FLYWHEEL_NAMES:
        ok("flywheel_routing_matrix.flywheel_sequence 六飞轮全覆盖 ✓")
    else:
        fail(f"flywheel_sequence {fw_seq} ≠ {VALID_FLYWHEEL_NAMES}")
    fw_guard = fw_matrix.get("_dao_guard", "")
    if "六飞轮" in fw_guard:
        ok("flywheel_routing_matrix._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"flywheel_routing_matrix._dao_guard='{fw_guard}' 未含'六飞轮'")

    # [9] mece_dimension_routing: dimension_sequence MECE + _dao_guard
    print("\n[9] mece_dimension_routing dimension_sequence MECE + _dao_guard")
    mece_seq = set(mece_routing.get("dimension_sequence_default", []))
    if mece_seq == MECE_DIMENSIONS:
        ok("mece_dimension_routing.dimension_sequence_default MECE 四维度 ✓")
    else:
        fail(f"dimension_sequence_default {mece_seq} ≠ {MECE_DIMENSIONS}")
    mece_guard = mece_routing.get("_dao_guard", "")
    if "MECE" in mece_guard:
        ok("mece_dimension_routing._dao_guard 含'MECE' ✓")
    else:
        fail(f"mece_dimension_routing._dao_guard='{mece_guard}' 未含'MECE'")

    # [10] stopping_rules: se_threshold_by_stage 七阶 + _dao_guard
    print("\n[10] stopping_rules se_threshold_by_stage 七阶全覆盖 + _dao_guard")
    se_by_stage = set(stopping.get("se_threshold_by_stage", {}).keys())
    if se_by_stage == VALID_STAGE_NAMES:
        ok("stopping_rules.se_threshold_by_stage 七阶全覆盖 ✓")
    else:
        fail(f"se_threshold_by_stage {se_by_stage} ≠ {VALID_STAGE_NAMES}")
    stop_guard = stopping.get("_dao_guard", "")
    if "七阶" in stop_guard:
        ok("stopping_rules._dao_guard 含'七阶' ✓")
    else:
        fail(f"stopping_rules._dao_guard='{stop_guard}' 未含'七阶'")

    # [11] exposure_control_config._dao_guard 含'Sympson-Hetter'
    print("\n[11] exposure_control_config._dao_guard 含'Sympson-Hetter'")
    exp_guard = exposure.get("_dao_guard", "")
    if "Sympson-Hetter" in exp_guard:
        ok("exposure_control_config._dao_guard 含'Sympson-Hetter' ✓")
    else:
        fail(f"exposure_control_config._dao_guard='{exp_guard}' 未含'Sympson-Hetter'")

    # [12] validation_rules
    print("\n[12] validation_rules 合规")
    stage_seq_c = vr.get("stage_sequence_constraint", "")
    if "七阶" in stage_seq_c:
        ok("validation_rules.stage_sequence_constraint 含'七阶' ✓")
    else:
        fail(f"validation_rules.stage_sequence_constraint='{stage_seq_c}' 未含'七阶'")
    fw_seq_c = vr.get("flywheel_sequence_constraint", "")
    if "六飞轮" in fw_seq_c:
        ok("validation_rules.flywheel_sequence_constraint 含'六飞轮' ✓")
    else:
        fail(f"validation_rules.flywheel_sequence_constraint='{fw_seq_c}' 未含'六飞轮'")
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
        print("  ✅ 测评自适应路由 schema 验证 PASS — θ路由/七阶/MECE/六飞轮/停止规则/曝光控制/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
