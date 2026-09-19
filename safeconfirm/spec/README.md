# SafeConfirm spec — 文档地图（瘦身版）

**论文:** `6a9fb8173b16b4dea4fd1079/safeconfirm.tex` · **指标归档:** `paper_metrics/canonical/` · **跑数:** `runs/bridge/`

## 当前必读（投稿维护）

| 文档 | 用途 |
|------|------|
| [reviewer_closeout_plan_1_5.md](./reviewer_closeout_plan_1_5.md) | **审稿收口 Steps 1–5** — 一致性、CLR 口径、fail-open、baseline 叙事、Table 1 |
| [evidence_strength_plan.md](./evidence_strength_plan.md) | **S8 证据强度** — 任务状态、MV5、external/provenance/banking |
| [paper_experiment_consistency.md](./paper_experiment_consistency.md) | **论文 ↔ 实验** 逐表核对与逻辑闭环 |
| [post_submission_experiment_plan.md](./post_submission_experiment_plan.md) | **投稿后实验加强**（external / sensitivity / banking 诊断 / 最后 cross-model） |
| [submission_consistency_audit.md](./submission_consistency_audit.md) | **提交前** 全文 consistency + claim–evidence 审计 |
| [claim_evidence_audit.md](./claim_evidence_audit.md) | Claim 索引（与 submission audit 同步） |
| [benchmark_design.md](./benchmark_design.md) | 28 diagnostic + 8 external 双轨、脚本入口 |
| [banking_tsr_root_cause.md](./banking_tsr_root_cause.md) | Banking TSR/utility 根因与叙事边界 |

## 长期参考（实现与指标定义）

| 文档 | 用途 |
|------|------|
| [requirements.md](./requirements.md) | 需求、指标定义、实验矩阵 |
| [design.md](./design.md) | 架构、Bridge CLI、表–脚本映射（较长） |
| [task.md](./task.md) | 阶段总览与一键复现命令 |

## 归档（已完成，勿再扩 scope）

| 文档 | 说明 |
|------|------|
| [improvement_plan.md](./improvement_plan.md) | Goal D（审稿弱点 v1）— 已被 S8 吸收 |
| [goal_e_reposition_benchmark_plan.md](./goal_e_reposition_benchmark_plan.md) | 叙事 reposition + 28-case 扩展 — 叙事已在 tex |

新增 spec 请挂到 **evidence_strength_plan** 或 **benchmark_design**，避免再开平行计划文档。
