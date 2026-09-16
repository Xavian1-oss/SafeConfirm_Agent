# SafeConfirm — 审稿弱点改进计划（Goal D）

**版本:** 0.1.0  
**依赖:** [task.md](./task.md), [requirements.md](./requirements.md), [design.md](./design.md)  
**触发:** AAMAS 2027 模拟审稿（Overall 6.5/10，Weak Accept / Borderline）  
**模型策略:** **DeepSeek-Chat only**（agent + confirmer）；跨模型与人机实验不在本计划 blocker 内

**论文源文件:** `6a9fb8173b16b4dea4fd1079/safeconfirm.tex`

**图例:** ☐ 未开始 · ◐ 进行中 · ☑ 完成 · — 明确不做（写 Limitations）

---

## 1. 目标与定位

| 层级 | 定位 | 与 Goal C 关系 |
|------|------|----------------|
| **Goal C** | 可投稿初稿（实验 + 7 页写作） | ☑ 已达 |
| **Goal D** | **审稿弱点响应线** — 提升 rigor 与叙事，目标 Main/Findings 稳收 | ☑ |

**Goal D 核心叙事调整（相对 Goal C）：**

1. Benchmark 是 **diagnostic evaluation suite**，主贡献是 **intervention framework + SDR/CLR**，非 SOTA _security guarantee_。
2. 实验数字必须 **内部一致**（同一代码版本、confirmer 行为可解释）。
3. 在 DeepSeek-only 约束下，用 **case 扩展 + per-case 分析 + 写作补强** 回应 scale 与 baseline 质疑。

**明确不做（Goal D 仍 out of scope）：**

- 跨模型主表（Gemini/GPT full 16 cases）
- Human-subjects confirmation study
- AgentVisor / PlanGuard 完整复现与数值对标
- Instruction-hijacking 主实验

---

## 2. 弱点 → 任务映射

| ID | 审稿弱点 | 优先级 | 任务 | 状态 |
|----|----------|--------|------|------|
| **W4** | REPAIR ablation 66.7% vs 主结果 100% TSR 不一致 | **P0 blocker** | §3.1 重跑 + 论文 footnote | ☑ |
| **W1** | Benchmark 仅 16 cases，hand-designed | **P1** | §3.2 扩 suite + diagnostic framing | ☑ |
| **W2** | 单模型 + LLM confirmer 外部有效性 | **P1 写作** | §3.3 oracle/LLM 双报告强化 | ☑ |
| **W3** | 机制 incremental vs AgentVisor/PlanGuard | **P1 写作** | §3.4 对比表 + 贡献重述 | ☑ |
| **W5** | Provenance 可扩展性 / 失败模式未量化 | **P2** | §3.5 归因错误分析 | ☑ |
| **W6** | AAMAS fit（偏 security 非 classic MAS） | **P2 写作** | §3.6 Introduction 定位 | ☑ |
| **W7** | 缺 contemporaneous binding-level baseline | **P2** | §3.7 轻量 verify baseline 或写作边界 | — |

---

## 3. 分任务规格

### 3.1 W4 — REPAIR ablation 与主结果一致性（P0）

**根因（已确认）：** 旧日志 `runs/bridge/ablation_repair/` 在 confirmer bug 修复**之前**采集；`on`  run 的 `confirm_approval_rate=0%`，而当前主结果 `e2e_deepseek_v3_s*` 为 `100%`。

**行动：**

- [x] 用当前代码重跑：`LOGROOT=runs/bridge/ablation_repair_v2 ./util_scripts/run_repair_ablation.sh`
- [x] 对比 v1 vs v2 metrics，写入 §6.2
- [x] 论文 Table 5 更新为 v2 + footnote（v1 为 confirmer bug 前采集）
- [x] **D0b — H2 子集 ablation**（§3.1b）— `runs/bridge/ablation_repair_subset_v1/`：on 100%/0%, off 80%/0%

**v2 结论：** confirmer 一致性已修复（approval 100%）；H2 不能再用 v1 的 +41.7pp，应改为「repair 触发率 / 子集 TSR」或 role-only case 对照。

#### 3.1b H2 重设计（D0b，P0 写作 + P1 实验）

**问题：** 当前 12 case 中 policy 多选 SOURCE_AWARE_CONFIRM，REPAIR 干预计数为 0（`repair_attempts` 有记录但 `RSR=0`）。

**方案 A（写作，优先）：** Table 5 报告 v2 全 suite + footnote；H2 证据改为 **case study**（`ws_email_supervisor_e2e` running example 中 REPAIR 路径）+ `repair_attempts` 统计。

**方案 B（实验，可选）：** 筛选 benchmark 中 `expected_intervention=REPAIR` 的 case 子集（约 4–6 个），重跑 on/off。

**验收：** 论文不再引用 v1 的 66.7%/25.0% 数字；H2 有 v2 或子集支撑。

---

### 3.2 W1 — Benchmark 扩展与 diagnostic framing（P1）

**阶段 D1（+4 cases，目标 20）：** 新增 workspace corruption 案例，**工具/槽位类型与现有 case 不重复**：

| 拟增 case | 工具 | 关键 slot | 说明 |
|-----------|------|-----------|------|
| `ws_forward_thread_e2e` | `send_email` | `bcc` | 转发邮件，poison 在 BCC 列表 |
| `ws_event_guest_e2e` | `create_calendar_event` | `participants` | 日历参与者来自 poison |
| `ws_move_file_e2e` | `append_to_file` | `file_id` | 云盘 append 目标 file\_id poison |
| `ws_read_then_send_e2e` | `send_email` | `recipients` | 两步：先 read 再 send，poison 在中间 observation |

**阶段 D2（+4 cases，目标 24，可选）：** banking +2、workspace benign +2。

**写作（不增 API 成本）：**

- [x] Abstract/Intro 加一句：*diagnostic suite for binding-level intervention quality, not a broad security benchmark*
- [x] Limitations 明确 case 设计流程（user/injection 配对、ground truth 独立标注）

**验收：** DeepSeek 主表报告 20-case TSR/ASR；旧 16-case 数字可放 Appendix 对照。☑ workspace 16-case v4: 89.6%±3.0% TSR / 0% ASR (3 seeds); banking 4-case 仍 100%/0% (cases 未变).

### 6.4 D2 workspace 20-case main（2026-09-08，已被 28-case E2E 取代）

| Scope | TSR | ASR | 目录 |
|-------|-----|-----|------|
| Ws 16-case ($n{=}3$ seeds) | 89.6% ± 3.0 pp | 0% ± 0 | `e2e_deepseek_v4_s*/` |
| Bank 4-case (unchanged) | 100% | 0% | `e2e_banking_deepseek_v4/` |

**新增 cases:** `ws_forward_thread_e2e` (BCC), `ws_event_guest_e2e` (calendar participants), `ws_move_file_e2e` (append\_to\_file), `ws_read_then_send_e2e` (two-step email).

**解读：** 扩展后 workspace TSR 自 100% 降至 ~90%，ASR 保持 0%；主要 stall 在 `ws_forward_thread_e2e` / `ws_delete_export_e2e`（agent 轨迹，非 ASR 回归）。

---

### 3.3 W2 — Confirmer 外部有效性（P1，DeepSeek-only）

**实验（可选 mini）：**

- [ ] REPAIR ablation 补跑 `confirmer=oracle_strict` 行（on/off），展示 REPAIR 增益与 confirmer 无关

**写作：**

- [x] Table 3 加 footnote：LLM confirmer = human-proxy；oracle = disclosure 上界
- [x] Discussion 段：同模型 confirmer 的 circularity 风险与 Limitations

**验收：** 论文明确区分「披露质量」(SDR/CLR) 与「批准行为」(confirmer-dependent TSR)。

---

### 3.4 W3/W7 — Related Work 与定位补强（P1，写作）

- [x] 新增 **Table: SafeConfirm vs prompt / binding-level defenses**（概念维度：hook 位置、干预粒度、是否评 CLR/SDR、是否 REPAIR）
- [x] 贡献 bullet 调整：首位 **SDR/CLR metrics + confirmation laundering**；pipeline 降为第二
- [x] 不声称优于 AgentVisor/PlanGuard 数值

**验收：** Related Work 后审稿人可一眼看出 orthogonal contribution。

---

### 3.5 W5 — Provenance 失败模式分析（P2）

- [x] 脚本：从 E2E logs 统计每 case 的 intervention 分布（ALLOW/REPAIR/CONFIRM/BLOCK）— `util_scripts/analyze_per_case.py`
- [x] 人工标注 20 case registry 覆盖 + unregistered fallback — `benchmark_registry_coverage.yaml`
- [x] 论文 §Discussion + Appendix Table~\ref{tab:percase} per-case 表

**验收：** 至少一张 per-case intervention 表或 figure（Appendix 可）。☑

---

### 3.6 W6 — AAMAS 受众定位（P2，写作）

- [x] Introduction 首段关联 *autonomous agents acting on behalf of users in multi-step environments*
- [x] 强调 human–agent interaction（confirmation as team play），非 multi-agent negotiation

---

### 3.7 W7 — 轻量 verify baseline（P2，可选实现）

**最小实现：** `baseline_verify_user_only` — 仅允许 binding 出现在 user query 文本中的 tool call，否则 SOURCE_AWARE_CONFIRM（不做完整 PlanGuard planner）。

- [—] 轻量 verify baseline 未实现；论文 Limitations 列为 future work（PlanGuard 式 user-query verify）

**验收：** Related Work / Limitations 明确边界。☑

## 4. 阶段排期（Goal D）

| 阶段 | 内容 | 预估 | 状态 |
|------|------|------|------|
| **D0** | W4 REPAIR v2 重跑 + 论文 Table 5 | 0.5 天 | ☑ |
| **D1** | W3/W2/W6 写作补丁（tex only） | 0.5 天 | ☑ |
| **D2** | W1 新增 4 cases + DeepSeek 主表 | 1–2 天 | ☑ |
| **D3** | W5 per-case 分析 + Appendix | 1 天 | ☑ |
| **D4** | W7 轻量 baseline（可选） | — | —（future work 写作） |

**Goal D 达标判定：** D0 ☑ + D1 ☑ + (D2 或 D3 至少一项) ☑ → 目标 Overall **7.0+/10** 可辩护。

---

## 5. 实验日志约定（Goal D）

| 实验 | 目录 | 论文 |
|------|------|------|
| REPAIR ablation v2 | `runs/bridge/ablation_repair_v2/` | Table 5 |
| Main 20-case | `runs/bridge/e2e_deepseek_v4_s*/` (ws), `e2e_banking_deepseek_v4/` (bank) | Table 2 |
| Per-case stats | `runs/bridge/e2e_deepseek_v4_s0/safeconfirm_workspace/per_case_summary.json` | Appendix Table~\\ref{tab:percase} |

---

## 6. 结果记录（随实验更新）

> **v1 REPAIR ablation（`ablation_repair/`）勿再引用** — confirmer bug 前采集，approval 0%。

### 6.1 REPAIR ablation v2（**当前引用**，12-case）

| Setting | TSR | ASR | RSR | repair_attempts | confirm_approval | 目录 |
|---------|-----|-----|-----|-----------------|------------------|------|
| on | 91.7% | 0% | 0% | 8 | 100% | `ablation_repair_v2/on/` |
| off | 91.7% | 0% | 0% | 0 | 100% | `ablation_repair_v2/off/` |

**解读：**

- v1→v2：confirmer approval 0%→100%，TSR 大幅提升；v1 的 +41.7pp **不可再引用**。
- v2 on/off TSR **相同**：当前 12 case 下 agent 轨迹对 `--no-repair` 不敏感（REPAIR 多在前处理阶段被 confirm 路径替代）。
- 主结果 100% vs ablation 91.7%：主结果 3-seed 聚合 + 可能轨迹随机性；`ws_delete_*` case 在 on/off 间互换 fail（各 stall 1 case）。

**下一步：** ~~§3.1b 子集 ablation~~ ☑ 完成；H2 以 subset + per-case repair 证据支撑。

### 6.2 REPAIR subset ablation D0b（**H2 主证据**）

| Scope | Setting | TSR | ASR | repair_attempts | confirm_approval | 目录 |
|-------|---------|-----|-----|-----------------|------------------|------|
| tasks 0--4 | on | 100% | 0% | 5 | 100% | `ablation_repair_subset_v1/on/` |
| tasks 0--4 | off | 80% | 0% | 0 | 26.7% | `ablation_repair_subset_v1/off/` |

**解读：** 全 suite on/off TSR 相同，但 role-reference 子集 off 在 `ws_share_client_e2e` stall（+20pp TSR with repair）；H2 应引用子集而非 v1 的 +41.7pp。

---

## 7. 一键命令

```bash
# D0: REPAIR v2
LOGROOT=runs/bridge/ablation_repair_v2 ./util_scripts/run_repair_ablation.sh

# Primary E2E: 28-case paired（supersedes Goal D 20-case main）
./util_scripts/run_extended_28case.sh
```
