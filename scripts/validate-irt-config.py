#!/usr/bin/env python3
"""
道层 IRT 配置验证脚本 v1.0
验证 pipeline-data/assessment-catalog.json 中 22 个测评工具的 irt_config 字段合规性。

IRT 模型规范:
  1PL (Rasch): discrimination_default == 1.0; no guessing
  2PL: discrimination_default ∈ (0.5, 2.0]; no guessing
  3PL: discrimination_default ∈ (0.5, 2.0]; guessing_param ∈ [0, 0.35]
"""

import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent

VALID_MODELS = {"1PL", "2PL", "3PL"}
DISC_MIN, DISC_MAX = 0.5, 2.0
GUESS_MAX = 0.35

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


def validate_irt_config(tool_id: str, cfg: dict) -> None:
    # model
    model = cfg.get("model")
    if model not in VALID_MODELS:
        fail(f"{tool_id}: model='{model}' 不在合法值 {{1PL,2PL,3PL}}")
        return
    ok(f"{tool_id}: model={model} ✓")

    # difficulty_range
    dr = cfg.get("difficulty_range")
    if not isinstance(dr, list) or len(dr) != 2:
        fail(f"{tool_id}: difficulty_range 格式错误 (期望 [lo,hi]): {dr}")
    elif dr[0] >= dr[1]:
        fail(f"{tool_id}: difficulty_range[0]={dr[0]} >= difficulty_range[1]={dr[1]}")
    else:
        ok(f"{tool_id}: difficulty_range={dr} ✓")

    # discrimination_default
    disc = cfg.get("discrimination_default")
    if model == "1PL":
        if disc != 1.0:
            fail(f"{tool_id}: 1PL 模型 discrimination_default 必须=1.0, 实为 {disc}")
        else:
            ok(f"{tool_id}: 1PL discrimination_default=1.0 ✓")
    elif disc is None or not isinstance(disc, (int, float)):
        fail(f"{tool_id}: discrimination_default 缺失或类型错误")
    elif not (DISC_MIN <= disc <= DISC_MAX):
        fail(f"{tool_id}: discrimination_default={disc} 超出 [{DISC_MIN},{DISC_MAX}]")
    else:
        ok(f"{tool_id}: discrimination_default={disc} ∈ [{DISC_MIN},{DISC_MAX}] ✓")

    # guessing_param (3PL only)
    if model == "3PL":
        guess = cfg.get("guessing_param")
        if guess is None:
            fail(f"{tool_id}: 3PL 模型缺少 guessing_param 字段")
        elif not (0 <= guess <= GUESS_MAX):
            fail(f"{tool_id}: 3PL guessing_param={guess} 超出 [0,{GUESS_MAX}]")
        else:
            ok(f"{tool_id}: 3PL guessing_param={guess} ∈ [0,{GUESS_MAX}] ✓")
    elif "guessing_param" in cfg:
        fail(f"{tool_id}: {model} 模型不应含 guessing_param 字段")


def main() -> None:
    catalog_path = REPO_ROOT / "pipeline-data" / "assessment-catalog.json"
    if not catalog_path.exists():
        print(f"❌ 找不到 {catalog_path}")
        sys.exit(1)

    catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    tools = catalog.get("assessment_tools", [])

    print("=" * 60)
    print("  IRT 配置合规验证 — assessment-catalog irt_config 字段")
    print("=" * 60)

    # [1] 工具数量
    print(f"\n[1] 工具数量: {len(tools)}")
    if len(tools) == 22:
        ok(f"工具数量 = 22 ✓")
    else:
        fail(f"工具数量 = {len(tools)}，期望 22")

    # [2] irt_config 存在性
    print(f"\n[2] irt_config 字段存在性")
    missing = [t["tool_id"] for t in tools if "irt_config" not in t]
    if missing:
        fail(f"缺少 irt_config 的工具: {missing}")
    else:
        ok(f"全部 22 工具均含 irt_config ✓")

    # [3] 逐工具验证
    print(f"\n[3] 逐工具 IRT 配置验证 (22 工具)")
    for tool in tools:
        tid = tool.get("tool_id", "?")
        cfg = tool.get("irt_config")
        if cfg is None:
            continue
        validate_irt_config(tid, cfg)

    # [4] 模型分布统计
    print(f"\n[4] IRT 模型分布统计")
    from collections import Counter
    dist = Counter(t["irt_config"]["model"] for t in tools if "irt_config" in t)
    for model, count in sorted(dist.items()):
        ok(f"model={model}: {count} 个工具")

    # ── 汇总 ─────────────────────────────────────────────────────
    print(f"\n{'=' * 60}")
    total = PASS_COUNT + FAIL_COUNT
    print(f"  结果: {PASS_COUNT}/{total} 通过 | {FAIL_COUNT} 失败")
    print("=" * 60)

    if FAIL_COUNT > 0:
        print("\n失败详情:")
        for e in ERRORS:
            print(f"  {e}")
        sys.exit(1)
    else:
        print("  ✅ IRT 配置验证 PASS — 22 工具全部合规")
        sys.exit(0)


if __name__ == "__main__":
    main()
