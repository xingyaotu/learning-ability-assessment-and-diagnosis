#!/usr/bin/env python3
"""
道层测评监考 schema 验证脚本 v1.0
验证 pipeline-data/assessment-proctoring-schema.json 的合规性。

验证项:
  1. JSON 文件加载
  2. proctoring_session_schema: 5个必填字段
  3. proctoring_mode enum + _dao_guard
  4. integrity_status enum + _dao_guard
  5. stage_domain_being_assessed enum 七阶 + _dao_guard
  6. flywheel_focus_of_session enum 六飞轮 + _dao_guard
  7. integrity_event_schema: 5个必填字段 + event_type/severity enum
  8. proctoring_rules.cat_session_guards._dao_guard
  9. proctoring_rules.halt_conditions 含[HALT-CSO] + 未成年人 _dao_guard 含'PIPL'
  10. remote_proctoring_pipl_compliance._dao_guard 含'PIPL'+'留存'
  11. validation_rules: 七阶/MECE/六飞轮/监考模式/pipl
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROC_PATH = REPO_ROOT / "pipeline-data" / "assessment-proctoring-schema.json"

VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}
VALID_STAGE_NAMES = {"不会", "模糊", "清晰", "框架", "运用", "熟练", "创新"}
MECE_DIMENSIONS = {"M", "E_exec", "C", "E_env"}
PROCTORING_MODES = {"self-proctored", "remote-automated", "remote-human", "in-person"}
INTEGRITY_STATUS = {"clean", "flagged", "suspended", "invalidated"}
REQUIRED_PROC_FIELDS = {
    "proctoring_session_id", "assessment_session_id", "student_id",
    "proctoring_mode", "session_start_time"
}
REQUIRED_EVENT_FIELDS = {
    "event_id", "proctoring_session_id", "event_type", "event_time", "severity"
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
    print("  测评监考 schema 验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not PROC_PATH.exists():
        fail(f"找不到文件: {PROC_PATH}")
        sys.exit(1)
    data = json.loads(PROC_PATH.read_text(encoding="utf-8"))
    ok("assessment-proctoring-schema.json 加载成功")

    ps_fields = data.get("proctoring_session_schema", {}).get("fields", {})
    ie_fields = data.get("integrity_event_schema", {}).get("fields", {})
    pr = data.get("proctoring_rules", {})
    rpp = data.get("remote_proctoring_pipl_compliance", {})
    vr = data.get("validation_rules", {})

    # [2] proctoring_session_schema: 5个必填字段
    print("\n[2] proctoring_session_schema 5个必填字段")
    for fname in REQUIRED_PROC_FIELDS:
        if fname in ps_fields:
            ok(f"proctoring_session_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"proctoring_session_schema.fields.{fname} 缺失")

    # [3] proctoring_mode enum + _dao_guard
    print("\n[3] proctoring_mode enum + _dao_guard")
    pm_field = ps_fields.get("proctoring_mode", {})
    pm_enum = set(pm_field.get("enum", []))
    if pm_enum == PROCTORING_MODES:
        ok("proctoring_mode enum 四种模式 ✓")
    else:
        fail(f"proctoring_mode enum {pm_enum} ≠ {PROCTORING_MODES}")
    pm_guard = pm_field.get("_dao_guard", "")
    if "self-proctored" in pm_guard:
        ok("proctoring_mode._dao_guard 含枚举值 ✓")
    else:
        fail(f"proctoring_mode._dao_guard='{pm_guard}' 未含枚举值")

    # [4] integrity_status enum + _dao_guard
    print("\n[4] integrity_status enum + _dao_guard")
    is_field = ps_fields.get("integrity_status", {})
    is_enum = set(is_field.get("enum", []))
    if is_enum == INTEGRITY_STATUS:
        ok("integrity_status enum 四等级 ✓")
    else:
        fail(f"integrity_status enum {is_enum} ≠ {INTEGRITY_STATUS}")
    is_guard = is_field.get("_dao_guard", "")
    if "clean" in is_guard:
        ok("integrity_status._dao_guard 含枚举值 ✓")
    else:
        fail(f"integrity_status._dao_guard='{is_guard}' 未含枚举值")

    # [5] stage_domain_being_assessed enum 七阶 + _dao_guard
    print("\n[5] stage_domain_being_assessed enum 七阶 + _dao_guard")
    sdba_field = ps_fields.get("stage_domain_being_assessed", {})
    sdba_enum = set(sdba_field.get("enum", []))
    if sdba_enum == VALID_STAGE_NAMES:
        ok("stage_domain_being_assessed enum 七阶全覆盖 ✓")
    else:
        fail(f"stage_domain_being_assessed enum {sdba_enum} ≠ {VALID_STAGE_NAMES}")
    sdba_guard = sdba_field.get("_dao_guard", "")
    if "七阶" in sdba_guard:
        ok("stage_domain_being_assessed._dao_guard 含'七阶' ✓")
    else:
        fail(f"stage_domain_being_assessed._dao_guard='{sdba_guard}' 未含'七阶'")

    # [6] flywheel_focus_of_session enum 六飞轮 + _dao_guard
    print("\n[6] flywheel_focus_of_session enum 六飞轮 + _dao_guard")
    ffs_field = ps_fields.get("flywheel_focus_of_session", {})
    ffs_enum = set(ffs_field.get("enum", []))
    if ffs_enum == VALID_FLYWHEEL_NAMES:
        ok("flywheel_focus_of_session enum 六飞轮全覆盖 ✓")
    else:
        fail(f"flywheel_focus_of_session enum {ffs_enum} ≠ {VALID_FLYWHEEL_NAMES}")
    ffs_guard = ffs_field.get("_dao_guard", "")
    if "六飞轮" in ffs_guard:
        ok("flywheel_focus_of_session._dao_guard 含'六飞轮' ✓")
    else:
        fail(f"flywheel_focus_of_session._dao_guard='{ffs_guard}' 未含'六飞轮'")

    # [7] integrity_event_schema: 5个必填字段 + event_type/severity enum
    print("\n[7] integrity_event_schema 5个必填字段 + event_type/severity enum")
    for fname in REQUIRED_EVENT_FIELDS:
        if fname in ie_fields:
            ok(f"integrity_event_schema.fields.{fname} 存在 ✓")
        else:
            fail(f"integrity_event_schema.fields.{fname} 缺失")
    sev_enum = set(ie_fields.get("severity", {}).get("enum", []))
    if sev_enum == {"low", "medium", "high", "critical"}:
        ok("severity enum {low/medium/high/critical} ✓")
    else:
        fail(f"severity enum {sev_enum} ≠ {{low/medium/high/critical}}")

    # [8] proctoring_rules.cat_session_guards._dao_guard
    print("\n[8] proctoring_rules.cat_session_guards._dao_guard")
    csg_guard = pr.get("cat_session_guards", {}).get("_dao_guard", "")
    if "CAT" in csg_guard:
        ok("cat_session_guards._dao_guard 含'CAT' ✓")
    else:
        fail(f"cat_session_guards._dao_guard='{csg_guard}' 未含'CAT'")

    # [9] halt_conditions 含[HALT-CSO] + 未成年人 _dao_guard 含'PIPL'
    print("\n[9] proctoring_rules halt_conditions [HALT-CSO] + 未成年人 _dao_guard 含'PIPL'")
    halt_conditions = pr.get("halt_conditions", [])
    halt_actions = [h.get("action", "") for h in halt_conditions]
    has_halt_cso = any("[HALT-CSO]" in a for a in halt_actions)
    if has_halt_cso:
        ok("proctoring_rules.halt_conditions 含[HALT-CSO] ✓")
    else:
        fail("proctoring_rules.halt_conditions 未含[HALT-CSO]")
    minor_guards = [h.get("_dao_guard", "") for h in halt_conditions if "PIPL" in h.get("_dao_guard", "")]
    if minor_guards:
        ok("halt_conditions 含未成年人 PIPL _dao_guard ✓")
    else:
        fail("halt_conditions 缺少含'PIPL'的 _dao_guard")

    # [10] remote_proctoring_pipl_compliance._dao_guard 含'PIPL'+'留存'
    print("\n[10] remote_proctoring_pipl_compliance._dao_guard 含'PIPL'+'留存'")
    rpp_guard = rpp.get("_dao_guard", "")
    if "PIPL" in rpp_guard and "留存" in rpp_guard:
        ok("remote_proctoring_pipl_compliance._dao_guard 含'PIPL'+'留存' ✓")
    else:
        fail(f"remote_proctoring_pipl_compliance._dao_guard='{rpp_guard}' 缺少关键词")

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
    pm_vr = set(vr.get("proctoring_modes", []))
    if pm_vr == PROCTORING_MODES:
        ok("validation_rules.proctoring_modes 四种模式 ✓")
    else:
        fail(f"proctoring_modes {pm_vr} ≠ {PROCTORING_MODES}")
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
        print("  ✅ 测评监考 schema 验证 PASS — 监考字段/完整性/CAT/七阶/六飞轮/HALT-CSO/PIPL 全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
