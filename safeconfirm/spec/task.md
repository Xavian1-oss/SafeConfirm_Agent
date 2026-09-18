# SafeConfirm — 任务文档

**版本:** 0.6.0  
**依赖:** [spec/README.md](./README.md)（文档地图）

**当前焦点:** **S8 — 证据强度（Goal F）** → [evidence_strength_plan.md](./evidence_strength_plan.md)

**论文:** `6a9fb8173b16b4dea4fd1079/safeconfirm.tex` · **一致性:** [paper_experiment_consistency.md](./paper_experiment_consistency.md)

**模型:** DeepSeek-Chat（agent + confirmer）；cross-model scope-out

---

## 阶段总览

| 阶段 | 目标 | 状态 |
|------|------|------|
| S0–S5 | SPEC + 实现 + Bridge | ☑ |
| S6 | Goal C 实验与初稿 | ☑ |
| S7 | Goal D 审稿弱点 | ☑（归档 [improvement_plan.md](./improvement_plan.md)） |
| S8 | 证据强度 + external/provenance | ☑ 实验；◐ tex 维护 |

---

## 一键复现（投稿主路径）

```bash
./util_scripts/run_extended_28case.sh      # Table 1 E2E workspace + banking ASR
./util_scripts/run_confirm_ablation.sh     # Table 1 confirm rows
./util_scripts/run_provenance_baselines.sh # Table 1 provenance / rule_v1 TSR
./util_scripts/run_external_eval.sh        # Table 2 external
./util_scripts/run_holdout_paired.sh       # Holdout footnote
./util_scripts/sync_paper_metrics.sh       # → paper_metrics/canonical/
```

脚本索引：[util_scripts/README.md](../util_scripts/README.md)

---

## 主结果摘要（与 tex 一致）

| 块 | 要点 |
|----|------|
| Confirm 12-case | 同 0% ASR，SDR 100% vs 0%；compliant vague CLR 66.7% |
| Provenance 12-case | block/vague ~22–25% TSR vs rule_v1 **75%** @ 0% ASR |
| E2E 28 ws | SC **39.4%/0%** vs P0 **27.3%/38.3%** TSR/ASR |
| E2E banking | SC **0%/0%**；P0 ASR **40%**；P0 TSR **5.6%**（paired Sep.~2026，见 consistency doc） |
| External 8 | P0 ASR **61.9%** → SC **9.5%**（13/21 vs 2/21 pooled） |

**Out of scope:** human study、instruction hijacking、cross-model 主表、banking utility claim。

---

## 实现细节

架构与 CLI：[design.md](./design.md) · 指标定义：[requirements.md](./requirements.md)
