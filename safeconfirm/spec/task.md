# SafeConfirm — 任务文档

**版本:** 0.3.3  
**依赖:** [requirements.md](./requirements.md), [design.md](./design.md)

**当前焦点:** S6 — 论文交付（P0/P1 实验已完成；待 L0、组件 ablation、写作）

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
| **S6** | 实验补全 + 论文交付 | ◐ |

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
  - [x] `share_file`（含 repair: contact_lookup）
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
- [x] 实现 design.md **§5.5** Confirmer（`LLMUserConfirmer` + `StrictOracleConfirmer`）

### 2.1 策略与候选

- [x] `candidate_generator.py`
- [x] `rule_policy.py`（rule_v1 + baseline_allow/block/vague）
- [x] 单元测试: `test_rule_policy.py`

### 2.2 执行器

- [x] `intervention_executor.py`（ALLOW / BLOCK / 确认暂停）
- [x] SOURCE_AWARE 模板渲染 + `validate_disclosure()`
- [x] `is_confirmation_laundering()` 检测
- [x] 单元测试: `test_confirmation_laundering_detection.py`

### 2.3 确认器（E2E benchmark）

- [x] `llm_user_confirmer.py` — `LLMUserConfirmer`（E2E 默认；仅见 user_query + confirm prompt）
- [x] `oracle_confirmer.py` — `StrictOracleConfirmer`（ablation；`--confirmer oracle_strict`）
- [x] `confirmer.py` — `get_confirmer("llm_user" | "oracle_strict")`
- [x] 按 design.md §2.6 实现确认消息注入与 approved/rejected/corrected 分支
- [x] 单元测试: `test_llm_user_confirmer.py`, `test_oracle_confirmer.py`

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

## S5 — E2E 评测基础设施

**目标:** E2E Bridge benchmark + TSR/ASR/干预指标 + 可复现实验。

> **L1 offline benchmark 已废弃（2026-07-15）：** 固定消息、无真实 LLM 的 L1 脚本与结果已删除。论文与复现统一使用 **E2E Bridge**。

### 5.1 Benchmark Cases

- [x] `safeconfirm/data/benchmark_cases_e2e.yaml`（workspace 12 + banking 4）
- [x] `safeconfirm_bridge/case_registry.py` — case → matched user/injection task
- [x] `safeconfirm_bridge/environment.py` — poison email / trusted contacts 注入

### 5.2 Bridge 脚本与指标

- [x] `safeconfirm_bridge/scripts/run_bridge_benchmark.py` — 主入口
- [x] `safeconfirm_bridge/e2e_metrics.py` — TSR/ASR + UAR/SDR/CLR/VCR/Composite
- [x] `safeconfirm/evaluation/metrics.py` — binding-only UAR；SDR 覆盖所有 confirm
- [x] `--policy rule_v1 | baseline_vague`、`--confirmer llm_user | oracle_strict` CLI
- [x] 单元测试: `test_metrics.py`, `test_oracle_confirmer.py`

### 5.3 E2E 实验（`runs/bridge/`）

| 目录 | 模型 | 配置 | TSR | ASR | 状态 |
|------|------|------|-----|-----|------|
| `e2e_deepseek_v3/` | DeepSeek | SafeConfirm rule_v1 | **100%** (12/12) | **0%** | ☑ **主表推荐** |
| `e2e_banking_deepseek_v4/` | DeepSeek | SafeConfirm rule_v1 | **100%** (4/4) | **0%** | ☑ **主表推荐** |
| `e2e_gpt4o_v2/` | GPT-4o | SafeConfirm rule_v1 | **100%** (12/12) | **0%** | ☑ **主表推荐** |
| `e2e_gpt4o_banking_v3/` | GPT-4o | SafeConfirm rule_v1 | 75% (3/4)‡ | **0%** | ☑ **主表推荐** |
| `confirm_ablation_v3/` | DeepSeek | policy × confirmer 4-row | — | — | ☑ **主表推荐** |
| `ablation_repair/` | DeepSeek | REPAIR on/off | +41.7pp TSR | 0% | ☑ |
| `e2e_retrieval_deepseek/` | DeepSeek | `--defense safeconfirm_retrieval` | 83.3%† | 0% | ☑ E2E 已跑 |
| `e2e_ds_v2_*/` | DeepSeek | Defense sweep v2 | SC **100%**/0% | — | ☑ |

† retrieval 跑于 eval/permission 修复前；与同期 rule_v1 持平，未优于 rule_v1。  
‡ GPT-4o banking：corruption **100%** (3/3)，benign `bk_transfer_benign_explicit_e2e` 多次重跑均 stall（agent 误用 IBAN 作 recipient，SA_CONFIRM 正确拒绝）；ASR **0%**。

**DeepSeek + SafeConfirm（推荐复现）:**

```bash
python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
  -s safeconfirm_workspace -m deepseek-chat \
  --defense safeconfirm --policy rule_v1 \
  --logdir runs/bridge/e2e_deepseek_v3
```

**Confirmation ablation（4-row）:**

```bash
LOGROOT=runs/bridge/confirm_ablation_v3 ./util_scripts/run_confirm_ablation.sh
python util_scripts/compare_confirm_ablation.py --logroot runs/bridge/confirm_ablation_v3
python util_scripts/export_ablation_trajectory_appendix.py --logroot runs/bridge/confirm_ablation_v3
```

**`confirm_ablation_v3` 汇总（post-ASR-fix, DeepSeek）：**

| Row | TSR | ASR | SDR | CLR | Stall | Approve% |
|-----|-----|-----|-----|-----|-------|----------|
| sa_llm | **100%** | 0% | **100%** | 0% | 0% | 100% |
| vague_llm | 91.7% | 0% | 0% | **100%** | 10% | 63.6% |
| sa_oracle | 83.3% | 0% | **100%** | 0% | 20% | 0% |
| vague_oracle | 33.3% | **0%**† | 0% | 0% | 80% | 0% |

† v2 中 `vague_oracle` ASR=10% 为 trace 假阳性；v3 修复后 **ASR=0%**（`ws_booking_confirm_e2e` 13 次 reject，无环境副作用）。

**Defense sweep v2:**

```bash
./util_scripts/run_ds_defense_sweep_v2.sh
# 对比 JSON: runs/bridge/e2e_ds_v2_defense_comparison.json
```

**GPT-4o 主实验:**

```bash
./util_scripts/run_gpt4o_main.sh
```

### 5.4 历史 L1（已删除，仅作记录）

- [x] ~~`benchmark_cases.yaml`~~、~~`run_targeted_benchmark.py`~~、~~`runs/safeconfirm_l1/`~~
- [x] L1 P1–P6 曾跑通；结果已删除

### 5.5 L0 实验（AgentDojo 兼容性，可选）

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

- [x] E2E workspace 12 cases 可复现（P0 + SafeConfirm + ablation）
- [x] 指标脚本输出 TSR/ASR + UAR/SDR/CLR/VCR/Composite
- [x] 论文主表字段: TSR, ASR, UAR, SDR, CLR, confirm_approval_rate
- [x] `safeconfirm_banking` 4 cases E2E（DeepSeek **100%** TSR / **0%** ASR，`e2e_banking_deepseek_v4`）
- [x] `environment.py` banking + `trusted_account_lookup` REPAIR
- [x] UAR 指标对齐 `corrupted_slots`（消除 stale gap 误报）
- [ ] L0 全量 AgentDojo utility 兼容性（±2%）

---

## S6 — 后续工作（论文交付）

> **目标:** 把现有 E2E 结果从「能跑通」提升到「能写进顶会 Experiments」——补证据缺口、修 bug、统一主表。
>
> **优先级:** P0 = 论文 blocker · P1 = 强加分 · P2 = 可选扩展

### 6.0 假设–证据缺口总览

| ID | 假设 / Claim | 当前状态 | 缺口 | 对应任务 |
|----|--------------|----------|------|----------|
| H1 | SOURCE_AWARE 优于 VAGUE（SDR/CLR） | ✅ `confirm_ablation_v3` | GPT-4o ablation 行；multi-seed | 6.4 |
| H2 | REPAIR 提升 TSR 且不升 UAR | ✅ ablation_repair (+41.7pp TSR) | GPT-4o 侧 optional | 6.2 |
| H3 | Retrieval 优于 rule_v1 | ◐ E2E 已跑，**未优于 rule_v1** | 论文降级为 appendix / limitation | 6.5 |
| H4 | ASR 无法区分干预质量 | ✅ ablation + defense sweep | — | — |
| C1 | Confirmation laundering 真实存在 | ✅ VCR/SDR（vague_llm CLR 100%） | — | — |
| C2 | Minimal-disruption intervention | ◐ SafeConfirm 居中（sweep v2） | 缺 allow/block 组件 ablation | 6.3 |
| C3 | Training-free learning | ◐ 同 H3 | E2E 无显著提升 | 6.5 |
| — | LLM confirmer 行为合理 | ✅ sa_llm approve 100% | 可能偏松；主表 dual-report oracle+llm | 6.1 |
| — | Banking 泛化 | ✅ DeepSeek 4/4；GPT-4o 3/4 | GPT-4o benign stall | 6.6 |
| — | 部署兼容性 | 未测 | L0 未跑 | 6.7 |

---

### 6.1 P0 — 修复已知 Bug

#### 6.1.1 `sa_oracle` / `user_task_4` message history 崩溃

- [x] **复现:** `confirm_ablation/sa_oracle` 全量 12 cases 时 `user_task_4` 失败
- [x] **根因:** `_confirm_batch` 在 assistant(tool_calls) 后注入 user confirm，approve/reject 后未移除；ToolsExecutor 无法执行且 LLM API 报 insufficient tool messages
- [x] **修复:** `intervention_executor.py` — confirm 后 pop synthetic user 消息；approve 恢复 assistant tool_calls；reject 追加 refusal assistant
- [x] **验证:** `sa_oracle` **12/12** 跑通（TSR 83.3%, ASR 0%）；`test_confirm_message_history.py`

```bash
python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
  -s safeconfirm_workspace -m deepseek-chat \
  --defense safeconfirm --policy rule_v1 \
  --confirmer oracle_strict \
  -ut user_task_4 \
  --logdir runs/bridge/confirm_ablation/sa_oracle_fix
```

#### 6.1.2 LLMUserConfirmer approval rate = 0%

- [x] **根因:** DeepSeek API 要求 prompt 含 `json` 才支持 `response_format=json_object`；此前全部 `llm_user_error` → fallback reject
- [x] **修复:** `CONFIRMER_SYSTEM_PROMPT` 含 JSON 指引；`build_confirmer_client()` fallback 至 `DEEPSEEK_API_KEY`；默认 confirmer 模型 `deepseek-chat`
- [x] **验证:** 单测 + live API（trusted→approve, untrusted→reject）
- [x] **重跑:** `confirm_ablation_v2` sa_llm approval **100%**（需关注 UAR-after-confirm 与披露质量叙事）

**验收:** ✅ approval rate 100%（sa_llm）；主表建议 oracle + llm 双行并讨论 approval 松紧。

#### 6.1.3 UAR 指标 stale gap 误报

- [x] **现象:** `sa_llm` UAR 80% 但 ASR 0% — agent 用 trusted 邮箱执行，gap 元数据未清
- [x] **修复:** `metrics.py` — E2E case 有 `corrupted_slots` 时，UAR 要求 `executed_binding` 匹配 poison 值
- [x] **验证:** `confirm_ablation_v2` sa_llm UAR **0%**；`test_metrics.py` 新增 fixture

#### 6.1.4 Utility / REPAIR 边缘 case

- [x] **benign email FBR:** `evaluators.py` body 子串匹配（转发邮件场景）
- [x] **share_supervisor stall:** 移除 REPAIR `permission_cap: read`；prompt 补 edit permission
- [x] **policy_backend 展示:** runner 从 `--defense` 推断；无 defense 显示 `none`

---

### 6.2 P0 — REPAIR 组件 Ablation（支撑 H2）

**目的:** 证明 REPAIR 对 TSR 有贡献，而非仅靠 BLOCK/SOURCE_AWARE。

- [x] **实现:** Bridge CLI 增加 `--no-repair`（传入 `SafeConfirmIntervention(enable_repair=False)`）
- [x] **实验矩阵（workspace 12, DeepSeek）:**

| Run ID | enable_repair | TSR | ASR | RSR | Stall | Composite |
|--------|---------------|-----|-----|-----|-------|-----------|
| `on` | true | **66.7%** | 0% | **42.6%** | 30% | 85.5% |
| `off` | false | 25.0% | 0% | **0%** | 80% | 75.0% |

- [x] **日志目录:** `runs/bridge/ablation_repair/{on,off}/`
- [ ] GPT-4o 侧复跑（可选；当前实验统一 DeepSeek）

```bash
./util_scripts/run_repair_ablation.sh
```

**验收:** ✅ H2 可写「REPAIR on vs off：TSR +41.7pp，RSR 42.6% vs 0%，ASR 均为 0%」。

---

### 6.3 P1 — 干预组件 Ablation（支撑 C2）

- [ ] **BLOCK-only baseline:** `--policy baseline_block` + E2E 12 cases（测 TSR 下界）
- [ ] **ALLOW-only baseline:** `--policy baseline_allow` + E2E（测 ASR 上界 / UAR 上界，预期 ASR >> 0）
- [ ] **Vague-only（已有）:** 归入 confirm_ablation，确保 GPT-4o 也跑一行 `vague_llm`
- [ ] **汇总脚本:** `util_scripts/compare_component_ablation.py`（可选）

**验收:** 主文 Figure/Table 可展示「安全–效用 Pareto」：allow 高 ASR、block 低 TSR、SafeConfirm 居中。

---

### 6.4 P1 — 补全 Ablation 覆盖

- [x] GPT-4o **主结果** workspace 12/12（`e2e_gpt4o_v2`）
- [x] 修复 ASR 定义后重跑 `confirm_ablation_v3` 4-row（DeepSeek）
- [x] `evaluators.attack_succeeded` 仅计环境副作用 + `test_evaluators.py`
- [ ] GPT-4o confirm ablation 4-row
- [ ] 每种配置 **≥2 seeds**（temperature / run index）报 mean ± std

**日志目录:** `runs/bridge/confirm_ablation_v3/`、`runs/bridge/e2e_gpt4o_v2/`、`runs/bridge/e2e_gpt4o_banking_v3/`

---

### 6.5 P1 — Retrieval E2E（支撑 H3 / C3）

- [x] Bridge 支持 `--defense safeconfirm_retrieval`（policy=`retrieval`）
- [x] workspace 12 cases 已跑（`e2e_retrieval_deepseek/`）
- [x] **结果:** TSR 83.3% / ASR 0%，与修复前 rule_v1 持平，**未优于 rule_v1**
- [x] **论文决策:** C3 降级为 appendix / limitation，不阻塞投稿

```bash
python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
  -s safeconfirm_workspace -m deepseek-chat \
  --defense safeconfirm_retrieval \
  --logdir runs/bridge/e2e_retrieval_deepseek
```

**验收:** ✅ H3 有 E2E 数字；requirements §7.5 标记为「E2E 无显著提升」。

---

### 6.6 P1 — Banking Suite E2E

- [x] `safeconfirm_banking` 4 cases（DeepSeek **100%** / GPT-4o **75%**）
- [x] `trusted_account_lookup` REPAIR + env（notes/invoice/transaction subject）
- [x] invoice case prompt 引导 `send_money`（禁 read_file 循环）

```bash
python -m safeconfirm_bridge.scripts.run_bridge_benchmark \
  -s safeconfirm_banking -m deepseek-chat \
  --defense safeconfirm --policy rule_v1 \
  --logdir runs/bridge/e2e_banking_deepseek_v4
```

**验收:** ✅ DeepSeek n=16 主表齐全；GPT-4o banking benign 待复跑或写 limitation。

---

### 6.7 P1 — L0 兼容性（NF1 / 部署叙事）

- [ ] 跑全量 workspace `safeconfirm_log_only` vs P0
- [ ] `compare_l0_utility.py` → `L0 pass: YES`（Δ utility ≤ 2%）
- [ ] 可选：banking suite 同样 smoke

**验收:** 论文可声称「passive mode 零 utility 回归」。

---

### 6.8 P2 — Defense Sweep 补全

- [x] DeepSeek defense sweep v2（`e2e_ds_v2_*`，对比 JSON 已生成）
- [x] 统一表格：P0、spotlighting、repeat、tool_filter、log_only、SafeConfirm
- [ ] GPT-4o 侧 defense sweep
- [ ] 明确 threat model 脚注：仅 `parameter_poison`，非 instruction hijacking（写作项）

**v2 关键数字（DeepSeek, workspace 12）:**

| Defense | TSR | ASR |
|---------|-----|-----|
| P0 | 50% | 60% |
| SC log-only | 83.3% | 20% |
| **SafeConfirm** | **100%** | **0%** |

---

### 6.9 P2 — 论文写作交付物

| 交付物 | 内容 | 状态 |
|--------|------|------|
| **Table 1** | Threat + benchmark 统计（16 cases, 攻击类型） | ◐ cases 就绪 |
| **Table 2** | 主结果：P0 vs SafeConfirm（GPT-4o + DeepSeek, TSR/ASR/UAR/SDR） | ☑ 数字齐全（`v3`+`v4`+`gpt4o_v2`+`gpt4o_banking_v3`） |
| **Table 3** | Confirm ablation 4-row（policy × confirmer） | ☑ DeepSeek `confirm_ablation_v3` |
| **Table 4** | vs AgentDojo defenses | ☑ DeepSeek `e2e_ds_v2_*` |
| **Table 5** | REPAIR ablation | ☑ `ablation_repair/` |
| **Fig 1** | 架构 + confirm 流（design §2.6 mermaid） | ☐ |
| **Fig 2** | Confirmation laundering 示例 trace | ☐ |
| **Experiments §** | Threat model、metrics、setup、hypothesis mapping | ◐ 假设映射可写 |
| **Limitations §** | 单攻击、模拟用户、无 human study、banking n 小、H3 无 E2E 增益 | ◐ 要点已明确 |

- [ ] 从 `runs/bridge/*/metrics.json` 自动生成 LaTeX 表格脚本（`util_scripts/export_paper_tables.py`）
- [ ] README 或 `safeconfirm/spec/results.md` 归档最终数字（可选，仅当用户需要）

---

### 6.10 P2 — 顶会扩展（非 v1 blocker）

| 项 | 说明 | 决策 |
|----|------|------|
| Human confirmation study | 真人读 SA vs Vague 的 approve 率 | 暂不做；Limitations 写明 |
| 多攻击 | `important_instructions` 等 instruction hijacking | **明确 out of scope**（requirements §7.1） |
| 多 suite | slack / travel | P2+ |
| 与 AgentVisor / PlanGuard 数值对比 | 不同 threat model | 仅 related work 概念对比 |

---

### S6 里程碑与建议顺序

```
Week 1 (P0 blockers)
  6.1.1 fix user_task_4 → 6.1.2 confirmer 诊断 → 6.2 --no-repair + ablation

Week 2 (P1 evidence)
  6.6 banking → 6.4 GPT-4o ablation → 6.5 retrieval E2E → 6.7 L0

Week 3 (paper)
  6.9 表格 + Experiments 初稿 → 6.3 组件 ablation 按需补
```

### S6 完成标准（论文可投稿最低线）

- [x] 全部 P0 项完成（bug fix + REPAIR ablation + confirmer + UAR fix）
- [x] workspace 12 + banking 4 = **16 cases** 主表齐全（DeepSeek）
- [x] 至少 **2 个 agent model** 主结果（GPT-4o workspace 100%；DeepSeek workspace+banking 100%）
- [x] confirm ablation **4-row** 完整且 oracle 12/12
- [x] H1/H4 有数字；H2 有 repair on/off；H3 有 E2E（降级叙事）
- [ ] Limitations 与 threat model 边界**成文**
- [ ] L0 log_only 兼容性
- [ ] multi-seed / GPT-4o ablation 行（加分项）

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
| 2026-07-15 | 废弃 L1：删除 `runs/safeconfirm_l1*`；论文/复现统一 E2E Bridge |
| 2026-07-17 | 删除中间实验 `runs/bridge/e2e_p5/`；GPT-4o 主结果重命名为 `e2e_gpt4o/`；DeepSeek 主结果迁至 `runs/bridge/e2e_deepseek/` |
| 2026-07-17 | **Spec v0.3.0:** 三文档对齐 E2E Bridge；L1 废弃；LLMUserConfirmer + StrictOracleConfirmer；TSR/ASR 指标；confirm ablation |
| 2026-07-17 | **Spec v0.3.1:** 新增 S6 后续工作路线图（假设缺口、P0–P2 任务、论文交付物、里程碑） |
| 2026-07-17 | **Fix:** confirm message history bug；`sa_oracle` 12/12；REPAIR ablation；CLI 默认 deepseek-chat |
| 2026-07-17 | **Fix:** UAR 对齐 `corrupted_slots`（消除 stale gap 误报）；banking `trusted_account_lookup` REPAIR |
| 2026-07-17 | **Run:** `e2e_deepseek_v2` workspace TSR 83.3%/ASR 0%/UAR 0%；`e2e_banking_v4` 4/4 TSR 100%；confirm ablation metrics 重算 |
| 2026-07-17 | **Fix+Run:** eval body 子串匹配、REPAIR 保留 permission、share prompt 补 edit；GPT-4o 主表 12/12+3/4 banking；defense sweep v2 SafeConfirm 100%/0% |
| 2026-07-17 | **Spec v0.3.2:** 同步全部实验状态；S6 P0/P1 大部分 ☑；主表推荐 `e2e_deepseek_v3` + `e2e_banking_v4` + `e2e_gpt4o_v2` |
| 2026-07-17 | **Spec v0.3.3:** ASR 仅计环境副作用；`confirm_ablation_v3` 重跑（vague_oracle ASR 0%）；`e2e_gpt4o_banking_v3`；`export_ablation_trajectory_appendix.py` |
| 2026-07-17 | **Cleanup:** `runs/bridge/` 删除归档 log（v1/v2 ablation、旧主表、旧 sweep）；仅保留 spec 推荐最新目录 |
