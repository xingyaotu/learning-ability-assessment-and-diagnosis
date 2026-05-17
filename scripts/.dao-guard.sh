#!/usr/bin/env bash
# ============================================================
# 星耀途道层零漂移守护脚本 v5.1
# Compliance: v5.1 | grep 6 漂移=0 命中 | 2026-05-13
# ============================================================
# 用途:每次 commit 前(pre-commit hook)+ CI 时跑一次,
#       grep 6 类 v4.1 漂移关键词,任一命中 exit 1 阻止 merge。
#
# 用法:bash scripts/.dao-guard.sh [扫描根目录,默认当前目录]
# 例:bash scripts/.dao-guard.sh .
# ============================================================
set -euo pipefail

ROOT="${1:-. }"
RED='\033[0;31m'
GRN='\033[0;32m'
YLW='\033[0;33m'
NC='\033[0m' # No Color

# 6 类 v4.1 漂移正则(对应 dao-layer-anti-drift.md § 0.6)
declare -A DRIFT_PATTERNS=(
  [01_MECE咨询误]="Mutually[[:space:]]+Exclusive|Collectively[[:space:]]+Exhaustive"
  [02_JUMEQ动词误]="Judge.*Understand.*Match|Execute.*Qualify(?![a-z])"
  [03_CAMIQ误]="Competence.*Aspiration.*Market.*Integration.*Quantify"
  [04_FIREUP5字母]="Foundation.*Identity.*Roadmap.*Execute.*UP[^a-zA-Z]"
  [05_八步演示]="导入.*拆解.*讲解.*类比.*演示.*练习.*反馈.*巩固|⑤[[:space:]]*演示|第五步[[:space:]]*演示"
  [06_六飞轮错题笔记]="F-错题|F-笔记|F-阅读|F-实践|错题飞轮|笔记飞轮|阅读飞轮|实践飞轮"
)

# 扫描目录
SCAN_DIRS=(
  "$ROOT/docs"
  "$ROOT/pipeline-data"
  "$ROOT/pipelines"
  "$ROOT/services"
  "$ROOT/apps"
  "$ROOT/scripts"
  "$ROOT/schemas"
  "$ROOT/coaching-sops"
  "$ROOT/.github"
)

# 扫描文件类型
FILE_GLOBS=(
  "--include=*.md"
  "--include=*.json"
  "--include=*.yml"
  "--include=*.yaml"
  "--include=*.sh"
)

# 排除目录
EXCLUDE_DIRS=(
  "--exclude-dir=node_modules"
  "--exclude-dir=.git"
  "--exclude-dir=dist"
  "--exclude-dir=build"
  "--exclude-dir=vendor"
)

echo -e "${YLW}===========================================${NC}"
echo -e "${YLW}  星耀途道层零漂移守护 v5.1${NC}"
echo -e "${YLW}  扫描根目录:$ROOT${NC}"
echo -e "${YLW}  扫描时间:$(date -u +%Y-%m-%dT%H:%M:%SZ)${NC}"
echo -e "${YLW}===========================================${NC}"

EXIT_CODE=0
TOTAL_HITS=0

# 收集存在的扫描目录
ACTUAL_DIRS=()
for d in "${SCAN_DIRS[@]}"; do
  if [[ -d "$d" ]]; then
    ACTUAL_DIRS+=("$d")
  fi
done

if [[ ${#ACTUAL_DIRS[@]} -eq 0 ]]; then
  echo -e "${YLW}⚠️  没有可扫描目录(可能是初次启动)${NC}"
  echo -e "${GRN}✅ Compliance PASS(空目录视为通过)${NC}"
  exit 0
fi

for pattern_name in "${!DRIFT_PATTERNS[@]}"; do
  pattern="${DRIFT_PATTERNS[$pattern_name]}"

  HIT=$(grep -rnE "$pattern" \
    "${FILE_GLOBS[@]}" \
    "${EXCLUDE_DIRS[@]}" \
    "${ACTUAL_DIRS[@]}" 2>/dev/null \
    | grep -v ".dao-guard.sh" \
    | grep -v "validate.yml" \
    || true)

  if [[ -z "$HIT" ]]; then
    echo -e "${GRN}✅ [$pattern_name] 0 命中${NC}"
  else
    HIT_COUNT=$(echo "$HIT" | wc -l)
    TOTAL_HITS=$((TOTAL_HITS + HIT_COUNT))
    echo -e "${RED}❌ [$pattern_name] $HIT_COUNT 处漂移:${NC}"
    echo "$HIT" | sed 's/^/    /'
    echo ""
    EXIT_CODE=1
  fi
done

echo -e "${YLW}===========================================${NC}"
if [[ $EXIT_CODE -eq 0 ]]; then
  echo -e "${GRN}✅ Compliance PASS (6/6 0 命中)${NC}"
  echo -e "${GRN}   可以 commit / merge${NC}"
else
  echo -e "${RED}❌ Compliance FAIL (共 $TOTAL_HITS 处漂移)${NC}"
  echo -e "${RED}   commit / merge 被阻止${NC}"
fi
echo -e "${YLW}===========================================${NC}"

exit $EXIT_CODE
