# SafeConfirm spec — 文档地图

**论文:** `6a9fb8173b16b4dea4fd1079/safeconfirm.tex` · **指标:** `paper_metrics/canonical/` · **跑数:** `runs/bridge/`  
**回归:** `uv run python util_scripts/verify_paper_metrics.py`（需先 `./util_scripts/sync_paper_metrics.sh`）

## 维护必读

| 文档 | 用途 |
|------|------|
| [paper_experiment_consistency.md](./paper_experiment_consistency.md) | **逻辑闭环 + 表 ↔ JSON ↔ 脚本**（单一事实源） |
| [submission_consistency_audit.md](./submission_consistency_audit.md) | 提交前 claim–evidence 与 footnote 审计 |
| [post_submission_experiment_plan.md](./post_submission_experiment_plan.md) | E1–E3 已完成；E4 cross-model 可选 |
| [benchmark_design.md](./benchmark_design.md) | 28 diagnostic + 12 external 双轨与脚本入口 |
| [banking_tsr_root_cause.md](./banking_tsr_root_cause.md) | Banking utility 边界（不 claim TSR） |
| [reviewer_closeout_plan_1_5.md](./reviewer_closeout_plan_1_5.md) | 收口 Steps 1–5（已完成，备查） |
| [evidence_strength_plan.md](./evidence_strength_plan.md) | S8 / MV5 历史任务清单（多数 ☑） |

## 实现参考

| 文档 | 用途 |
|------|------|
| [requirements.md](./requirements.md) | 指标定义、实验矩阵 |
| [design.md](./design.md) | 架构、Bridge、表–脚本映射（较长） |
| [task.md](./task.md) | 一键复现命令与主结果摘要 |

已删除冗余计划：`improvement_plan.md`、`goal_e_reposition_benchmark_plan.md`、`claim_evidence_audit.md`（内容并入上表两份审计/一致性文档；完整历史见 git）。
