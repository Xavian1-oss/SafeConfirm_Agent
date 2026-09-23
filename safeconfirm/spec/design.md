# SafeConfirm — 设计文档（精简）

> **历史长版已退役。** 实现与模块边界以 **[architecture.md](./architecture.md)** 为准；实验与表数字以 **[paper_experiment_consistency.md](./paper_experiment_consistency.md)** 为准。

## 运行时流水线（5 步，无副作用直到 executor）

```text
LLM tool_calls
  → SafeConfirmIntervention
      [1] Tool-slot extraction (registry, per-tool schema)
      [2] Provenance + authorization analysis (ProvenanceProvider)
      [3] AuthorizationState
      [4] Policy core (ALLOW / REPAIR / CONFIRM / BLOCK / REPLAN)
      [5] InterventionExecutor (active mode only)
  → ToolsExecutor
```

## AgentDojo 集成

- **Adapter:** `safeconfirm_bridge` + `safeconfirm/benchmark/agentdojo_adapter.py` → `TaskContext`
- **Hook:** `SafeConfirmIntervention` 在 assistant `tool_calls` 之后、工具执行之前
- **评测:** `safeconfirm_bridge/e2e_metrics.py` + `safeconfirm/evaluation/metrics.py`（SDR/CLR/UAR）

## 配置入口

- `safeconfirm/config/defaults.yaml` · 环境变量 `SAFECONFIRM_*`
- 主 policy：`rule_v1` → `authorization/policy_core.policy_from_state`

## 相关文档

| 文档 | 内容 |
|------|------|
| [architecture.md](./architecture.md) | 分层与包路径 |
| [requirements.md](./requirements.md) | 指标定义 |
| [benchmark_design.md](./benchmark_design.md) | 28 + 12 case 与脚本 |
| [task.md](./task.md) | 复现命令 |
