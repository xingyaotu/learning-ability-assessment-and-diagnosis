#!/usr/bin/env python3
"""
道层 MECE 科目画像验证脚本 v1.0
验证 pipeline-data/mece-subject-profiles.json 的合规性。

验证项:
  1. JSON 文件加载
  2. 9个科目全覆盖 (math/chinese/english/physics/chemistry/biology/history/geography/politics)
  3. mece_weights 四维度之和 == 1.0 (每个科目)
  4. primary_bottleneck_dimension ∈ {M, E_exec, C, E_env}
  5. stage_threshold_adjustment ∈ [-0.5, 0.5]
  6. cat_ability_emphasis ∈ {high_discrimination, balanced, low_discrimination}
  7. recommended_assessment_tools 非空
  8. key_capability_dimensions 非空
  9. mece_weights 各维度值 ∈ (0, 1)
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
PROFILES_PATH = REPO_ROOT / "pipeline-data" / "mece-subject-profiles.json"

REQUIRED_SUBJECT_IDS = {
    "math", "chinese", "english", "physics", "chemistry",
    "biology", "history", "geography", "politics"
}

VALID_BOTTLENECK_DIMS = {"M", "E_exec", "C", "E_env"}
VALID_EMPHASIS = {"high_discrimination", "balanced", "low_discrimination"}
MECE_DIM_KEYS = ["M", "E_exec", "C", "E_env"]

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
    print("  MECE 科目画像验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    if not PROFILES_PATH.exists():
        fail(f"找不到文件: {PROFILES_PATH}")
        sys.exit(1)
    data = json.loads(PROFILES_PATH.read_text(encoding="utf-8"))
    ok("mece-subject-profiles.json 加载成功")

    profiles = data.get("subject_profiles", [])

    # [2] 9科目全覆盖
    print("\n[2] 9科目全覆盖验证")
    found_ids = {p.get("subject_id") for p in profiles}
    missing = REQUIRED_SUBJECT_IDS - found_ids
    if missing:
        fail(f"缺少科目: {missing}")
    else:
        ok(f"9科目全覆盖 ✓ ({sorted(found_ids)})")

    extra = found_ids - REQUIRED_SUBJECT_IDS
    if extra:
        fail(f"未预期的科目 ID: {extra}")
    else:
        ok("无多余科目 ✓")

    # [3-9] 逐科目验证
    print("\n[3-9] 逐科目字段验证")
    for p in profiles:
        sid = p.get("subject_id", "?")
        sname = p.get("subject_name", "?")
        label = f"{sid}({sname})"

        # [3] mece_weights 之和 == 1.0
        weights = p.get("mece_weights", {})
        missing_keys = [k for k in MECE_DIM_KEYS if k not in weights]
        if missing_keys:
            fail(f"{label}: mece_weights 缺少维度 {missing_keys}")
        else:
            total = sum(weights[k] for k in MECE_DIM_KEYS)
            if abs(total - 1.0) < 1e-9:
                ok(f"{label}: mece_weights 之和 = {total:.2f} ✓")
            else:
                fail(f"{label}: mece_weights 之和 = {total:.4f} ≠ 1.0")

            # [9] 各维度值 ∈ (0, 1)
            for k in MECE_DIM_KEYS:
                v = weights.get(k, 0)
                if 0 < v < 1:
                    ok(f"{label}: {k}={v} ∈ (0,1) ✓")
                else:
                    fail(f"{label}: {k}={v} 超出 (0,1) 范围")

        # [4] primary_bottleneck_dimension
        pbd = p.get("primary_bottleneck_dimension", "")
        if pbd in VALID_BOTTLENECK_DIMS:
            ok(f"{label}: primary_bottleneck_dimension='{pbd}' 合规 ✓")
        else:
            fail(f"{label}: primary_bottleneck_dimension='{pbd}' 非法 (应为 {VALID_BOTTLENECK_DIMS})")

        # [5] stage_threshold_adjustment ∈ [-0.5, 0.5]
        sta = p.get("stage_threshold_adjustment")
        if sta is None:
            fail(f"{label}: 缺少 stage_threshold_adjustment")
        elif -0.5 <= sta <= 0.5:
            ok(f"{label}: stage_threshold_adjustment={sta} ∈ [-0.5,0.5] ✓")
        else:
            fail(f"{label}: stage_threshold_adjustment={sta} 超出 [-0.5,0.5]")

        # [6] cat_ability_emphasis
        cae = p.get("cat_ability_emphasis", "")
        if cae in VALID_EMPHASIS:
            ok(f"{label}: cat_ability_emphasis='{cae}' 合规 ✓")
        else:
            fail(f"{label}: cat_ability_emphasis='{cae}' 非法")

        # [7] recommended_assessment_tools 非空
        tools = p.get("recommended_assessment_tools", [])
        if tools:
            ok(f"{label}: recommended_assessment_tools {len(tools)}个 ✓")
        else:
            fail(f"{label}: recommended_assessment_tools 为空")

        # [8] key_capability_dimensions 非空
        kcd = p.get("key_capability_dimensions", [])
        if kcd:
            ok(f"{label}: key_capability_dimensions {len(kcd)}个 ✓")
        else:
            fail(f"{label}: key_capability_dimensions 为空")

    # [10] validation_rules 存在
    print("\n[10] validation_rules 合规")
    vr = data.get("validation_rules", {})
    if "weight_sum_constraint" in vr:
        ok("validation_rules.weight_sum_constraint 存在 ✓")
    else:
        fail("validation_rules.weight_sum_constraint 缺失")
    if "mece_dimension_codes" in vr:
        codes = vr["mece_dimension_codes"]
        if set(codes) == set(MECE_DIM_KEYS):
            ok(f"mece_dimension_codes 四维度合规 ✓ {codes}")
        else:
            fail(f"mece_dimension_codes 不匹配: {codes}")
    else:
        fail("validation_rules.mece_dimension_codes 缺失")

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
        print("  ✅ MECE 科目画像验证 PASS — 全部 9 科目配置合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
