#!/usr/bin/env python3
"""
道层 MECE 诊断规则验证脚本 v1.0
验证 pipeline-data/mece-diagnosis-rules.json 的合规性。

验证项:
  1. JSON 文件加载
  2. stage_mece_routing: 七阶全覆盖 (stage_id 1-7)
  3. 每阶 stage_name 枚举合规 (七阶名称)
  4. 每阶 mece_dispatch: 四维度 bottleneck 覆盖 (C/M/E_exec/E_env)
  5. flywheel_priority 值均在六飞轮枚举内
  6. ⑤守护: stage_id=5, bottleneck=C → primary_sop=sop-05 + _dao_guard 存在
  7. composite_diagnosis_rules: 四条复合规则存在
  8. flywheel_stage_compatibility: 六飞轮全覆盖
  9. validation_rules: step_id_5_name=流程 + six_flywheel_valid_names 6个
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
RULES_PATH = REPO_ROOT / "pipeline-data" / "mece-diagnosis-rules.json"

SEVEN_STAGE_NAMES = {
    1: "不会", 2: "模糊", 3: "清晰", 4: "框架",
    5: "运用", 6: "熟练", 7: "创新",
}
VALID_BOTTLENECK_DIMS = {"C", "M", "E_exec", "E_env"}
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
    print("  MECE 诊断规则验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not RULES_PATH.exists():
        fail(f"找不到文件: {RULES_PATH}")
        sys.exit(1)
    data = json.loads(RULES_PATH.read_text(encoding="utf-8"))
    ok("mece-diagnosis-rules.json 加载成功")

    routing = data.get("stage_mece_routing", [])

    # [2] 七阶全覆盖
    print("\n[2] stage_mece_routing 七阶全覆盖")
    found_stage_ids = {s.get("stage_id") for s in routing}
    missing_stages = set(range(1, 8)) - found_stage_ids
    if missing_stages:
        fail(f"缺少阶位: {missing_stages}")
    else:
        ok(f"七阶全覆盖 ✓ (stage_id 1-7)")

    extra_stages = found_stage_ids - set(range(1, 8))
    if extra_stages:
        fail(f"未预期的阶位: {extra_stages}")
    else:
        ok("无多余阶位 ✓")

    # [3-6] 逐阶验证
    print("\n[3-6] 逐阶 mece_dispatch 验证")
    dao_guard_stage5_c = None
    for stage in routing:
        sid = stage.get("stage_id")
        sname = stage.get("stage_name", "")
        expected_name = SEVEN_STAGE_NAMES.get(sid, "?")
        label = f"阶{sid}"

        # [3] stage_name 枚举
        if sname == expected_name:
            ok(f"{label}: stage_name='{sname}' 合规 ✓")
        else:
            fail(f"{label}: stage_name='{sname}' 期望 '{expected_name}'")

        # [4] mece_dispatch 四维度覆盖
        dispatches = stage.get("mece_dispatch", [])
        found_bottlenecks = {d.get("bottleneck") for d in dispatches}
        missing_bk = VALID_BOTTLENECK_DIMS - found_bottlenecks
        if missing_bk:
            fail(f"{label}: mece_dispatch 缺少 bottleneck {missing_bk}")
        else:
            ok(f"{label}: 四维度 bottleneck 全覆盖 ✓")

        for d in dispatches:
            bk = d.get("bottleneck", "?")
            fw_list = d.get("flywheel_priority", [])
            psop = d.get("primary_sop", "")
            centry = d.get("coaching_entry", "")

            # [5] flywheel_priority 合规
            invalid_fw = set(fw_list) - VALID_FLYWHEEL_NAMES
            if invalid_fw:
                fail(f"{label}/{bk}: flywheel_priority 含非法飞轮 {invalid_fw}")
            elif fw_list:
                ok(f"{label}/{bk}: flywheel_priority {fw_list} 合规 ✓")
            else:
                fail(f"{label}/{bk}: flywheel_priority 为空")

            # primary_sop 非空
            if psop:
                ok(f"{label}/{bk}: primary_sop='{psop}' 存在 ✓")
            else:
                fail(f"{label}/{bk}: primary_sop 为空")

            # coaching_entry 非空
            if centry:
                ok(f"{label}/{bk}: coaching_entry='{centry}' 存在 ✓")
            else:
                fail(f"{label}/{bk}: coaching_entry 为空")

            # [6] ⑤守护: stage 5, bottleneck C
            if sid == 5 and bk == "C":
                dao_guard_stage5_c = d

    # [6] ⑤守护专项
    print("\n[6] ⑤守护验证 (stage_id=5, bottleneck=C)")
    if dao_guard_stage5_c is None:
        fail("stage_id=5/C dispatch 缺失")
    else:
        psop = dao_guard_stage5_c.get("primary_sop", "")
        centry = dao_guard_stage5_c.get("coaching_entry", "")
        guard = dao_guard_stage5_c.get("_dao_guard", "")
        if psop == "sop-05":
            ok("stage5/C: primary_sop='sop-05' ✓")
        else:
            fail(f"stage5/C: primary_sop='{psop}' ≠ 'sop-05'")
        if centry == "eight_step_5":
            ok("stage5/C: coaching_entry='eight_step_5' ✓")
        else:
            fail(f"stage5/C: coaching_entry='{centry}' ≠ 'eight_step_5'")
        if "_dao_guard" in dao_guard_stage5_c:
            ok(f"stage5/C: _dao_guard 字段存在 ✓")
        else:
            fail("stage5/C: 缺少 _dao_guard 守护字段")
        if "流程" in guard:
            ok("stage5/C: _dao_guard 包含 '流程' ⑤联动守护 ✓")
        else:
            fail(f"stage5/C: _dao_guard='{guard}' 未包含 '流程'")

    # [7] composite_diagnosis_rules
    print("\n[7] composite_diagnosis_rules 验证")
    comp = data.get("composite_diagnosis_rules", {})
    comp_rules = comp.get("composite_rules", [])
    if len(comp_rules) >= 4:
        ok(f"composite_rules {len(comp_rules)}条 ≥ 4 ✓")
    else:
        fail(f"composite_rules 仅 {len(comp_rules)} 条 < 4")
    for r in comp_rules:
        rid = r.get("rule_id", "?")
        if r.get("primary_bottleneck") and r.get("strategy"):
            ok(f"{rid}: primary_bottleneck + strategy 存在 ✓")
        else:
            fail(f"{rid}: 缺少 primary_bottleneck 或 strategy")

    # [8] flywheel_stage_compatibility
    print("\n[8] flywheel_stage_compatibility 六飞轮覆盖")
    fsc = data.get("flywheel_stage_compatibility", {}).get("compatibility_matrix", {})
    found_fw = set(fsc.keys())
    missing_fw = VALID_FLYWHEEL_NAMES - found_fw
    if missing_fw:
        fail(f"compatibility_matrix 缺少飞轮: {missing_fw}")
    else:
        ok(f"六飞轮全覆盖 ✓ {sorted(found_fw)}")
    for fname, compat in fsc.items():
        for key in ["stages_high", "stages_medium", "stages_low"]:
            if key in compat:
                stages = compat[key]
                invalid = [s for s in stages if s not in range(1, 8)]
                if invalid:
                    fail(f"{fname}.{key}: 含非法阶位 {invalid}")
                else:
                    ok(f"{fname}.{key}: {stages} 合规 ✓")
            else:
                fail(f"{fname}: 缺少 {key}")

    # [9] validation_rules
    print("\n[9] validation_rules 合规")
    vr = data.get("validation_rules", {})
    step5_name = vr.get("eight_step_name_constraints", {}).get("step_id_5_name", "")
    if step5_name == "流程":
        ok("validation_rules step_id_5_name='流程' ⑤联动守护 ✓")
    else:
        fail(f"validation_rules step_id_5_name='{step5_name}' ≠ '流程'")

    fw_names = set(vr.get("six_flywheel_valid_names", []))
    if fw_names == VALID_FLYWHEEL_NAMES:
        ok(f"six_flywheel_valid_names 六飞轮完整 ✓")
    else:
        missing = VALID_FLYWHEEL_NAMES - fw_names
        fail(f"six_flywheel_valid_names 缺少: {missing}")

    seven_names = vr.get("seven_stage_names", [])
    if len(seven_names) == 7 and set(seven_names) == set(SEVEN_STAGE_NAMES.values()):
        ok(f"seven_stage_names 七阶完整 ✓")
    else:
        fail(f"seven_stage_names 不完整: {seven_names}")

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
        print("  ✅ MECE 诊断规则验证 PASS — 七阶×四维度路由全合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
