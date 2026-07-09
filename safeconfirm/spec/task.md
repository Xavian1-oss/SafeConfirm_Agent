# SafeConfirm — 任务文档

**版本:** 0.2.0  
**依赖:** [requirements.md](./requirements.md), [design.md](./design.md)

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

---

## S0 — SPEC（已完成）

- [x] 编写 requirements.md
- [x] 编写 design.md
- [x] 编写 task.md
- [x] 合并原 00–08 文档，删除冗余

---

## S1 — 被动日志模式

**目标:** 插入 pipeline，分析并记录，**不改变** tool 执行结果。

**前置:** design.md §2.6（确认流）、§2.7（日志写入）已在 SPEC 中定义；S1 仅实现 log 路径，确认流在 S2 实现。

### 1.1 项目骨架

- [x] 创建 `safeconfirm/` 包结构（见 design.md §3）
- [x] 实现 `safeconfirm/types/models.py`（核心 dataclass / Pydantic）
- [x] 实现 `safeconfirm/config/defaults.yaml` 加载

### 1.2 数据资产（最小集）

- [x] `safeconfirm/data/tool_slot_registry.yaml`（条目见 design.md §7）
  - [x] `send_email`（含 repair: contact_lookup）
  - [x] `share_file`（含 repair + permission_cap）
  - [x] `send_money`
  - [x] `delete_file`（含 repair: file_id_resolve）
- [x] `safeconfirm/data/confirmation_templates.yaml`（占位即可）

### 1.3 提取与归因

- [x] `registry_loader.py` — 加载 YAML
- [x] `slot_extractor.py` — 按 registry 提取 + normalize
- [x] `trust_index.py` — 预建 user 文本 / observation 索引
- [x] `source_analyzer.py` — 规则版归因（user 扫描 + tool message 扫描）
- [x] 单元测试: `test_slot_extractor.py`, `test_source_analyzer.py`

### 1.4 Pipeline 接入

- [x] `SafeConfirmPipeline` 编排器（analyze only，stage 1–4）
- [x] `SafeConfirmIntervention(mode="log_only")`
- [x] 写入 `extra_args["safeconfirm"]["intervention_log"]`
- [x] 在 `agent_pipeline.py` 注册 `safeconfirm_log_only`
- [x] 集成测试: `test_pipeline_integration.py`

### S1 完成标准

- [x] `--defense safeconfirm_log_only` 可运行
- [x] env 结果与无 defense 一致（passive）
- [x] 日志含 `tool_name`, `critical_slots`, `slot_records`, `selected_intervention`

---

## S2 — 主动干预 + SOURCE_AWARE

**目标:** 灰区 risky call 触发 SOURCE_AWARE 或 BLOCK；VAGUE 作 baseline。

**前置（SPEC 已就绪，实现时须遵守）:**

- [x] 阅读并实现 design.md **§2.6** 确认流（synthetic user + 同轮 Confirmer + 保守多 call 策略）
- [x] 实现 design.md **§6.4** laundering 检测
- [x] 实现 design.md **§5.5** Confirmer 表（至少 Oracle / AlwaysYes / AlwaysNo）

### 2.1 策略与候选

- [x] `candidate_generator.py`
- [x] `rule_policy.py`（rule_v1 + baseline_allow/block/vague）
- [x] 单元测试: `test_rule_policy.py`

### 2.2 执行器

- [x] `intervention_executor.py`（ALLOW / BLOCK / 确认暂停）
- [x] SOURCE_AWARE 模板渲染 + `validate_disclosure()`
- [x] `is_confirmation_laundering()` 检测
- [x] 单元测试: `test_confirmation_laundering_detection.py`

### 2.3 确认器（benchmark）

- [x] `confirmer.py` — `OracleConfirmer`, `AlwaysYesConfirmer`, `AlwaysNoConfirmer`
- [x] 按 design.md §2.6 实现确认消息注入与 approved/rejected/corrected 分支

### 2.4 Active 模式

- [x] `SafeConfirmIntervention(mode="active")`
- [x] 注册 `--defense safeconfirm`
- [x] 手工 fixture: untrusted recipient → 不执行或 SOURCE_AWARE

### S2 完成标准

- [x] BLOCK 时 env 不被该 tool call 改变
- [x] SOURCE_AWARE 确认文案含 exact 值 + 来源
- [x] baseline_vague 可切换用于 ablation

---

## S3 — REPAIR

**目标:** role-binding 场景从通讯录修复参数。

- [x] `repair_engine.py` — `contact_lookup` 策略
- [x] registry 补充 repair 元数据（send_email, share_file）
- [x] REPAIR 后重跑分析 pipeline
- [x] 单元测试: `test_repair_engine.py`
- [x] 集成: supervisor role + 污染邮箱 → 修复为联系人邮箱

### S3 完成标准

- [x] 至少 1 个 designed case RSR > 0
- [x] 修复失败时 fallback SOURCE_AWARE 或 BLOCK

---

## S4 — 经验学习

**目标:** 组内比较 → 蒸馏经验 → retrieval 策略优于 rule_v1。

- [x] `intervention_verifier.py`（rule oracle）
- [x] `group_comparator.py`
- [x] `experience_distiller.py` + `experience_store.py`
- [x] `retrieval_policy.py`
- [x] `safeconfirm/scripts/learn_interventions.py`
- [x] 单元测试: `test_experience_retrieval.py`

### S4 完成标准

- [x] ≥10 条 experiences 从 workspace cases 蒸馏
- [x] hold-out 上 retrieval 改变 ≥2 个决策 vs rule_v1

---

## S5 — 评测基础设施

**目标:** L1 benchmark + 指标脚本 + 可复现实验。

### 5.1 Benchmark Cases

- [x] `safeconfirm/data/benchmark_cases.yaml`
  - [x] ws_email_* ×3
  - [x] ws_share_* ×3
  - [x] ws_delete_* ×3
  - [x] bk_transfer_* ×3
  - [x] （扩展至 24 cases + 3 benign FBR cases）

### 5.2 脚本

- [x] `safeconfirm/scripts/run_targeted_benchmark.py`
- [x] `safeconfirm/scripts/evaluate_interventions.py`（UAR/CLR/SDR/TPR/FBR/RSR/Composite）
- [x] benchmark JSON 合并 `safeconfirm` 字段（TraceLogger + `merge_safeconfirm_into_benchmark_log`）

### 5.3 实验

- [x] L1: P1–P6 跑通（targeted benchmark 脚本）
- [x] L2: P3×AlwaysYes vs P4×Oracle（CLR 对比：P3 CLR=1.0, P4 CLR=0.0）
- [x] 结果表 + trace 样例（`runs/safeconfirm_l1/metrics.json`）
- [ ] L0: native AgentDojo 兼容性（±2% utility）— 见下方 L0 实验命令

### L0 实验（AgentDojo 兼容性）

**目标:** P0（无 defense）与 `safeconfirm_log_only` 的 utility 差距 ≤ 2%。

**1. 配置 API Key**

```bash
cd /Users/xiexiejianxiang/PycharmProjects/agentdojo
cp .env.example .env
# 编辑 .env，填入 OPENAI_API_KEY=sk-...
```

`benchmark.py` 启动时会自动 `load_dotenv(".env")`；OpenAI SDK 读取 `OPENAI_API_KEY`。

**2. 冒烟（2 个 task，约 1–2 分钟）**

```bash
export L0_USER_TASKS="-ut user_task_0 -ut user_task_1"
export L0_MODEL="gpt-4o-mini-2024-07-18"
./safeconfirm/scripts/run_l0_compatibility.sh
```

**3. 全量 workspace（正式 L0）**

```bash
unset L0_USER_TASKS   # 跑 suite 内全部 user tasks
./safeconfirm/scripts/run_l0_compatibility.sh
```

**4. 手动分步（可选）**

```bash
# P0 baseline
.venv/bin/python -m agentdojo.scripts.benchmark \
  --model gpt-4o-mini-2024-07-18 \
  -s workspace \
  --benchmark-version v1.2.2 \
  --logdir runs/l0/p0_baseline

# P0 + SafeConfirm passive
.venv/bin/python -m agentdojo.scripts.benchmark \
  --model gpt-4o-mini-2024-07-18 \
  -s workspace \
  --defense safeconfirm_log_only \
  --benchmark-version v1.2.2 \
  --logdir runs/l0/p0_safeconfirm_log_only

# 对比
.venv/bin/python safeconfirm/scripts/compare_l0_utility.py \
  --baseline runs/l0/p0_baseline \
  --candidate runs/l0/p0_safeconfirm_log_only \
  --tolerance 0.02
```

**5. 扩展（多 suite / 更强模型）**

```bash
.venv/bin/python -m agentdojo.scripts.benchmark \
  --model gpt-4o-2024-05-13 \
  -s workspace -s banking \
  --defense safeconfirm_log_only \
  --logdir runs/l0/full_safeconfirm_log_only
```

**判定:** `compare_l0_utility.py` 输出 `L0 pass: YES` 即通过。

**注意:** L0 仅测 **无 attack** 的 utility（不要加 `--attack`）。`safeconfirm_log_only` 不应改变 tool 执行结果。

### S5 完成标准

- [x] 指标脚本在 3 个 fixture log 上复现手算值
- [x] 论文主表: UAR, CLR, SDR, TPR, Composite

---

## 当前建议的下一步

**S5 已完成。** SafeConfirm S0–S5 全部实现完毕。可选后续：L0 全量 AgentDojo utility 兼容性 run。

```bash
# S5 验证命令
.venv/bin/pytest tests/safeconfirm -v

python safeconfirm/scripts/run_targeted_benchmark.py --output runs/safeconfirm_l1
python safeconfirm/scripts/evaluate_interventions.py --logdir runs/safeconfirm_l1

python -m agentdojo.scripts.benchmark \
  --defense safeconfirm \
  -s workspace -ut user_task_0 \
  --model GPT_4O_MINI_2024_07_18 \
  --logdir runs/safeconfirm_full
```

---

## 变更记录

| 日期 | 变更 |
|------|------|
| 2026-06-06 | S0: 九份文档合并为 requirements / design / task 三文档 |
| 2026-06-06 | 补充：确认流协议、指标精确定义、Confirmer、laundering 规则、日志字段、定位章节 |
| 2026-06-07 | S1: log_only 实现、AgentDojo 注册、单元/集成测试 |
| 2026-07-07 | S2: active 干预、SOURCE_AWARE 确认流、Confirmer、laundering 检测、15 项测试 |
| 2026-07-07 | S3: REPAIR/contact_lookup、role-binding 检测、重分析 pipeline、21 项测试 |
| 2026-07-07 | S4: verifier/comparator/distiller/retrieval、12 条 experiences、26 项测试 |
| 2026-07-07 | S5: 27 L1 cases、metrics 脚本、P1–P6 targeted benchmark、32 项测试 |
