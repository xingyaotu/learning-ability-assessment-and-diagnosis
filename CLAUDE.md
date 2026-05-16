# 学习力测评与诊断 — Claude Code 工作协议 v1.0

<!-- 道层 Compliance: v5.0 | 2026-05-16 -->

## 仓库定位

本仓库是 **星耀途因材施教** 平台的学习力测评与诊断知识库。

主仓库: `xingyaotu/xingyaotu-openmaic`

## 道层守护(4 密码)

| 密码 | 正确值 | 常见漂移 |
|---|---|---|
| MECE | M-动力 / E-执行力 / C-能力 / E-环境 | 误用为"Mutually Exclusive" |
| JUMEQ | 升学密码 5 字母 | 误写为动词/短语 |
| CAMIQ | 职业密码 5 字母 | 误写为拼写变体 |
| FIRE-UP | 生涯密码 6 字母(F/I/R/E/U/P) | 误写为 5 字母 |

## 文件结构

```
learning-ability-assessment-and-diagnosis/
├── README.md                       ← 仓库说明
├── CLAUDE.md                       ← 本文件
├── pipeline-data/                  ← 结构化 JSON 数据
│   └── mece-assessment-schema.json ← MECE 测评维度 schema
├── 知识库_学习力测评与诊断_完整版.md  ← 124节课完整知识库
├── 学习力体系知识库（深度完整版）.md  ← 深度理论版
└── [规划师课程目录]/               ← 工具篇/认知篇/理论篇/营销篇
```

## 关键规则

1. 所有 JSON 文件必须含 `$schema` 字段
2. MECE 4 字母含义不得漂移
3. 不涉及个人隐私数据(PIPL 合规)
4. commit 前检查: MECE 正确 / JSON 格式有效
