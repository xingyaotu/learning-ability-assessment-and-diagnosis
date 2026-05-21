#!/usr/bin/env python3
"""
道层测评信效度配置验证脚本 v1.0
验证 pipeline-data/assessment-reliability-config.json 的合规性。

验证项:
  1. JSON 文件加载
  2. tool_reliability_specs: 22工具全覆盖
  3. 1PL 工具两个 (jumeq_economy, camiq_monetary)
  4. 3PL 工具一个 (mastery_stages)
  5. 每工具 min_alpha ≥ 0.65 (全局地板值)
  6. target_alpha > min_alpha (每工具)
  7. min_test_retest_r > 0 且 ≤ 1
  8. flywheels 工具 special_notes 含六飞轮名称
  9. validation_rules tool_count=22 + six_flywheel_names 6个
  10. PIPL 合规声明
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
RELIABILITY_PATH = REPO_ROOT / "pipeline-data" / "assessment-reliability-config.json"

REQUIRED_22_TOOLS = {
    "assess_mece_motivation", "assess_mece_execution",
    "assess_mece_capability", "assess_mece_environment",
    "assess_mastery_stages",
    "assess_jumeq_jobplacement", "assess_jumeq_university",
    "assess_jumeq_major", "assess_jumeq_economy", "assess_jumeq_qualification",
    "assess_camiq_character", "assess_camiq_aptitude",
    "assess_camiq_monetary", "assess_camiq_interest", "assess_camiq_qualification",
    "assess_flywheels_self_eval",
    "assess_fireup_family", "assess_fireup_individual",
    "assess_fireup_resources", "assess_fireup_ecosystem",
    "assess_fireup_usability", "assess_fireup_pathways",
}
TOOLS_1PL = {"assess_jumeq_economy", "assess_camiq_monetary"}
TOOLS_3PL = {"assess_mastery_stages"}
VALID_FLYWHEEL_NAMES = {"计划", "预习", "复习", "听课", "作业", "考试"}

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
    print("  测评信效度配置验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not RELIABILITY_PATH.exists():
        fail(f"找不到文件: {RELIABILITY_PATH}")
        sys.exit(1)
    data = json.loads(RELIABILITY_PATH.read_text(encoding="utf-8"))
    ok("assessment-reliability-config.json 加载成功")

    specs = data.get("tool_reliability_specs", [])
    global_t = data.get("global_thresholds", {})

    # [2] 22工具全覆盖
    print("\n[2] 22工具全覆盖")
    found_tools = {s.get("tool_id") for s in specs}
    missing = REQUIRED_22_TOOLS - found_tools
    if missing:
        fail(f"缺少工具: {missing}")
    else:
        ok(f"22工具全覆盖 ✓")
    extra = found_tools - REQUIRED_22_TOOLS
    if extra:
        fail(f"多余工具: {extra}")
    else:
        ok("无多余工具 ✓")

    # [3] 1PL 工具检查
    print("\n[3] 1PL 工具验证")
    found_1pl = {s.get("tool_id") for s in specs if s.get("irt_model") == "1PL"}
    if found_1pl == TOOLS_1PL:
        ok(f"1PL 工具准确: {sorted(found_1pl)} ✓")
    else:
        fail(f"1PL 工具: 期望 {sorted(TOOLS_1PL)}, 实际 {sorted(found_1pl)}")

    for s in specs:
        if s.get("tool_id") in TOOLS_1PL:
            if "1PL" in s.get("special_notes", "") or "Rasch" in s.get("special_notes", ""):
                ok(f"{s['tool_id']}: special_notes 提及 1PL/Rasch ✓")
            else:
                fail(f"{s['tool_id']}: special_notes 未提及 1PL/Rasch")

    # [4] 3PL 工具检查
    print("\n[4] 3PL 工具验证")
    found_3pl = {s.get("tool_id") for s in specs if s.get("irt_model") == "3PL"}
    if found_3pl == TOOLS_3PL:
        ok(f"3PL 工具准确: {sorted(found_3pl)} ✓")
    else:
        fail(f"3PL 工具: 期望 {sorted(TOOLS_3PL)}, 实际 {sorted(found_3pl)}")

    # [5-7] 逐工具参数验证
    print("\n[5-7] 逐工具参数范围验证")
    global_alpha_floor = global_t.get("min_cronbach_alpha", 0.70)
    ok(f"全局 Cronbach α 最低阈值 = {global_alpha_floor}")

    for s in specs:
        tid = s.get("tool_id", "?")
        ma = s.get("min_alpha", 0)
        ta = s.get("target_alpha", 0)
        mtr = s.get("min_test_retest_r", 0)

        # [5] min_alpha ≥ 0.65
        local_floor = 0.65
        if ma >= local_floor:
            ok(f"{tid}: min_alpha={ma} ≥ {local_floor} ✓")
        else:
            fail(f"{tid}: min_alpha={ma} < {local_floor}")

        # [6] target_alpha > min_alpha
        if ta > ma:
            ok(f"{tid}: target_alpha={ta} > min_alpha={ma} ✓")
        else:
            fail(f"{tid}: target_alpha={ta} ≤ min_alpha={ma}")

        # [7] min_test_retest_r ∈ (0, 1]
        if 0 < mtr <= 1.0:
            ok(f"{tid}: min_test_retest_r={mtr} ∈ (0,1] ✓")
        else:
            fail(f"{tid}: min_test_retest_r={mtr} 超出 (0,1]")

    # [8] flywheels_self_eval special_notes 六飞轮
    print("\n[8] assess_flywheels_self_eval 六飞轮守护")
    fw_spec = next((s for s in specs if s.get("tool_id") == "assess_flywheels_self_eval"), None)
    if fw_spec is None:
        fail("assess_flywheels_self_eval spec 缺失")
    else:
        notes = fw_spec.get("special_notes", "")
        fw_in_notes = [fw for fw in VALID_FLYWHEEL_NAMES if fw in notes]
        if len(fw_in_notes) >= 6:
            ok(f"flywheels_self_eval special_notes 包含六飞轮名称 ✓")
        else:
            found_in = [fw for fw in VALID_FLYWHEEL_NAMES if fw in notes]
            fail(f"flywheels_self_eval special_notes 仅包含 {len(found_in)} 个飞轮名称: {found_in}")

    # [9] validation_rules
    print("\n[9] validation_rules 合规")
    vr = data.get("validation_rules", {})
    tc = vr.get("tool_count", 0)
    if tc == 22:
        ok(f"validation_rules.tool_count=22 ✓")
    else:
        fail(f"validation_rules.tool_count={tc} ≠ 22")

    fw_names = set(vr.get("six_flywheel_names", []))
    missing_fw = VALID_FLYWHEEL_NAMES - fw_names
    if missing_fw:
        fail(f"six_flywheel_names 缺少: {missing_fw}")
    elif len(fw_names) == 6:
        ok("validation_rules.six_flywheel_names 六飞轮全覆盖 ✓")
    else:
        fail(f"six_flywheel_names 数量 {len(fw_names)} ≠ 6")

    irt_assign = vr.get("irt_model_assignment", {})
    tools_1pl_vr = set(irt_assign.get("1PL_tools", []))
    if tools_1pl_vr == TOOLS_1PL:
        ok(f"validation_rules.1PL_tools 准确 ✓")
    else:
        fail(f"validation_rules.1PL_tools={tools_1pl_vr} ≠ {TOOLS_1PL}")

    tools_3pl_vr = set(irt_assign.get("3PL_tools", []))
    if tools_3pl_vr == TOOLS_3PL:
        ok(f"validation_rules.3PL_tools 准确 ✓")
    else:
        fail(f"validation_rules.3PL_tools={tools_3pl_vr} ≠ {TOOLS_3PL}")

    # global_thresholds sanity
    ok(f"global_thresholds.min_cronbach_alpha={global_t.get('min_cronbach_alpha')} ✓" if global_t.get('min_cronbach_alpha') else "")
    ok(f"global_thresholds.min_calibration_sample_n={global_t.get('min_calibration_sample_n')} ✓" if global_t.get('min_calibration_sample_n') else "")

    # [10] PIPL 合规
    print("\n[10] PIPL 合规")
    pipl_meta = data.get("_meta", {}).get("pipl_note", "")
    if "PIPL" in pipl_meta:
        ok("_meta.pipl_note PIPL 合规声明 ✓")
    else:
        fail("_meta.pipl_note 缺少 PIPL 合规声明")
    pipl_vr = vr.get("pipl_constraints", "")
    if "PIPL" in pipl_vr or "student_id" in pipl_vr:
        ok("validation_rules.pipl_constraints 存在 ✓")
    else:
        fail("validation_rules.pipl_constraints 缺失")

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
        print("  ✅ 测评信效度配置验证 PASS — 22工具信效度配置全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
