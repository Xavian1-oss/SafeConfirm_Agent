# SafeConfirm — 任务文档

**版本:** 0.5.0  
**依赖:** [requirements.md](./requirements.md), [design.md](./design.md), [improvement_plan.md](./improvement_plan.md)

**当前焦点:** **S7 — Goal D 审稿弱点响应**（见 [improvement_plan.md](./improvement_plan.md)）

**投稿目标:** Goal C ☑ → **Goal D**（审稿弱点改进，DeepSeek-only）

**模型策略:** 主实验统一 **DeepSeek-Chat**（agent + confirmer）；跨模型验证 optional（见 §S6）

**论文源文件:** `6a9fb8173b16b4dea4fd1079/safeconfirm.tex`（AAMAS 2027 模板；DeepSeek-only 稿面）

**图例:** ☐ 未开始 · ◐ 进行中 · ☑ 完成

---

## 阶段总览

| 阶段 | 目标 | 状态 |
|------|------|------|
| **S0** | SPEC 三文档 | ☑ |
| **S1** | 被动日志（log_only） | ☑ |
| **S2** | 规则策略 + SOURCE_AWARE active | ☑ |
| **S3** | REPAIR | ☑ |
| **S4** | 经验学习 + retrieval | ☑ |
| **S5** | 完整 benchmark + 指标 | ☑ |
| **S6** | 实验补全 + 论文交付（Goal C） | ☑ |
| **S7** | 审稿弱点响应（Goal D） | ☑ |

---

## S7 — Goal D 审稿弱点响应

> **完整规格:** [improvement_plan.md](./improvement_plan.md)  
> **模型:** DeepSeek-only（与 Goal C 一致）

| 阶段 | 任务 | 状态 |
|------|------|------|
| **D0** | W4 REPAIR ablation v2 重跑 + 论文 Table 5 | ☑ |
| **D0b** | H2 role-reference 子集 ablation (tasks 0--4) | ☑ |
| **D1** | W2/W3/W6 写作补丁（diagnostic framing、对比表） | ☑ |
| **D2** | W1 benchmark +4 cases（→20）+ 主表 | ☑ |
| **D3** | W5 per-case intervention 分析 | ☑ |
| **D4** | W7 轻量 verify baseline（future work 写作） | — |

---

## S0–S5 — 已实现（摘要）

系统实现已完成（SPEC → log_only → active 干预 → REPAIR → retrieval → E2E Bridge）。架构见 [design.md](./design.md)，指标见 [requirements.md](./requirements.md)。

**复现：** `python -m safeconfirm_bridge.scripts.run_bridge_benchmark`；批量脚本见 [design.md §13](./design.md#13-实验与论文归档)。

---

## S6 — Goal C 实验与论文交付（已完成 ☑）

Goal C 已全部完成；详细 checklist 不再在此维护，避免与 [improvement_plan.md](./improvement_plan.md) / [design.md §13](./design.md#13-实验与论文归档) 重复。

**权威来源：**

| 内容 | 文档 |
|------|------|
| 假设–证据、实验矩阵、指标定义 | [requirements.md §7](./requirements.md#7-e2e-评估与实验) |
| 日志目录、CLI、论文–表映射 | [design.md §13](./design.md#13-实验与论文归档) |
| 20-case 扩展、REPAIR v2、per-case 分析 | [improvement_plan.md](./improvement_plan.md) |

**一键复现：**

```bash
./util_scripts/run_goal_c_all.sh          # Goal C blocker 批量（12-case ablation + L0 + multi-seed）
./util_scripts/run_extended_28case.sh     # 主表 E2E（22 ws + 6 bk，paired P0 vs SC，3 seeds）
./util_scripts/run_holdout_paired.sh      # Holdout 4 cases（Appendix）
```

**当前主结果（DeepSeek-only，28-case paired）：** workspace **39.4%/0%** TSR/ASR（SC）vs **27.3%/38.3%**（P0）；banking **0%/0%** vs **0%/40%**。机制消融（confirm/component）仍用 12-case frozen prefix。

**明确 out of scope：** human study、instruction hijacking、新 suite、与 AgentVisor/PlanGuard 数值对标。跨模型子集验证：`./util_scripts/run_cross_model_validation.sh`（optional，非 blocker）。
