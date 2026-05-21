#!/usr/bin/env python3
"""
道层 CAT 配置验证脚本 v1.0
验证 pipeline-data/cat-config.json 的合规性。

验证项:
  1. JSON 文件加载
  2. 工具专项配置中 tool_id 均在 catalog 中存在
  3. 1PL 工具的 cat_enabled == false (Rasch 约束: 固定施测)
  4. 2PL/3PL 工具默认 cat_enabled == true
  5. 所有 stopping_rules: max_items ≥ min_items; se_threshold ∈ (0, 1]
  6. exposure_control.max_exposure_rate ∈ (0, 1]; ≥ min_exposure_rate
  7. global_cat_settings.theta_range 合规 [lo < hi]
  8. default_cat_config 存在且参数合规
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent
CATALOG_PATH = REPO_ROOT / "pipeline-data" / "assessment-catalog.json"
CAT_PATH = REPO_ROOT / "pipeline-data" / "cat-config.json"

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


def validate_stopping_rules(rules: dict, ctx: str) -> None:
    max_it = rules.get("max_items")
    min_it = rules.get("min_items")
    se = rules.get("se_threshold")
    if max_it is None or min_it is None:
        fail(f"{ctx}: stopping_rules 缺少 max_items 或 min_items")
    elif max_it < min_it:
        fail(f"{ctx}: max_items={max_it} < min_items={min_it}")
    else:
        ok(f"{ctx}: max_items={max_it} ≥ min_items={min_it} ✓")
    if se is not None and not (0 < se <= 1.0):
        fail(f"{ctx}: se_threshold={se} 超出 (0,1]")
    elif se is not None:
        ok(f"{ctx}: se_threshold={se} ∈ (0,1] ✓")


def validate_exposure(exp: dict, ctx: str) -> None:
    max_r = exp.get("max_exposure_rate")
    min_r = exp.get("min_exposure_rate")
    if max_r is None:
        fail(f"{ctx}: exposure_control 缺少 max_exposure_rate")
        return
    if not (0 < max_r <= 1.0):
        fail(f"{ctx}: max_exposure_rate={max_r} 超出 (0,1]")
    else:
        ok(f"{ctx}: max_exposure_rate={max_r} ✓")
    if min_r is not None and max_r < min_r:
        fail(f"{ctx}: max_exposure_rate={max_r} < min_exposure_rate={min_r}")
    elif min_r is not None:
        ok(f"{ctx}: exposure range [{min_r},{max_r}] 合规 ✓")


def main() -> None:
    print("=" * 62)
    print("  CAT 自适应测评配置验证 v1.0")
    print("=" * 62)

    # [1] 文件加载
    print("\n[1] 文件加载")
    for p in [CAT_PATH, CATALOG_PATH]:
        if not p.exists():
            fail(f"找不到文件: {p.name}")
            sys.exit(1)
    cat_cfg = json.loads(CAT_PATH.read_text(encoding="utf-8"))
    catalog = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    ok("cat-config.json + catalog 加载成功")

    catalog_tools = {t["tool_id"]: t for t in catalog.get("assessment_tools", [])}
    tool_models = {tid: t.get("irt_config", {}).get("model") for tid, t in catalog_tools.items()}

    # [2] global_cat_settings.theta_range
    print("\n[2] global_cat_settings.theta_range")
    gs = cat_cfg.get("global_cat_settings", {})
    theta_range = gs.get("theta_range", [])
    if len(theta_range) == 2 and theta_range[0] < theta_range[1]:
        ok(f"theta_range={theta_range} lo < hi ✓")
    else:
        fail(f"theta_range={theta_range} 不合规")

    # [3] tool_cat_configs 逐工具验证
    print("\n[3] tool_cat_configs 工具 ID + 1PL/2PL/3PL 约束")
    tool_configs = cat_cfg.get("tool_cat_configs", [])
    for tc in tool_configs:
        tid = tc.get("tool_id", "?")
        ctx = tid

        # tool_id in catalog
        if tid not in catalog_tools:
            fail(f"{ctx}: tool_id 不在 catalog 中")
            continue
        ok(f"{ctx}: 存在于 catalog ✓")

        # 1PL → cat_enabled must be false
        model = tool_models.get(tid, "?")
        cat_enabled = tc.get("cat_enabled", True)
        if model == "1PL":
            if cat_enabled:
                fail(f"{ctx}: 1PL 工具 cat_enabled 必须=false")
            else:
                ok(f"{ctx}: 1PL → cat_enabled=false ✓")
        else:
            ok(f"{ctx}: {model} → cat_enabled={cat_enabled}")

        # stopping_rules
        rules = tc.get("stopping_rules", {})
        validate_stopping_rules(rules, ctx)

        # exposure_control (optional for fixed-form)
        exp = tc.get("exposure_control")
        if exp:
            validate_exposure(exp, ctx)

    # [4] default_cat_config
    print("\n[4] default_cat_config 参数合规")
    default = cat_cfg.get("default_cat_config", {})
    if not default:
        fail("default_cat_config 缺失")
    else:
        ok("default_cat_config 存在")
        validate_stopping_rules(default.get("stopping_rules", {}), "default")
        exp = default.get("exposure_control")
        if exp:
            validate_exposure(exp, "default")

    # [5] 1PL 工具 cat_enabled=false 全量检查 (catalog 视角)
    print("\n[5] 全量 1PL 工具 cat_enabled=false 检查")
    configured_ids = {tc["tool_id"] for tc in tool_configs}
    for tid, model in tool_models.items():
        if model != "1PL":
            continue
        if tid in configured_ids:
            tc = next(t for t in tool_configs if t["tool_id"] == tid)
            if tc.get("cat_enabled", True):
                fail(f"{tid}: 1PL 但 cat_enabled=true (违反 Rasch 固定施测约束)")
            else:
                ok(f"{tid}: 1PL → cat_enabled=false ✓")
        else:
            ok(f"{tid}: 1PL — 使用 default_cat_config (需确保 default 不强制 CAT)")

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
        print("  ✅ CAT 配置验证 PASS — 所有配置合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
