# SafeConfirm — Goal E 改进计划：Reposition + Benchmark 强化

**版本:** 0.1.0  
**日期:** 2026-09-11  
**依赖:** [improvement_plan.md](./improvement_plan.md)（Goal D 已完成）、[task.md](./task.md)  
**触发:** 外部 literature 调研（PACT / AuthGraph / AIRGuard 等）+ 模拟审稿（novelty ~5.8/10，benchmark scale 质疑）  
**论文源文件:** `6a9fb8173b16b4dea4fd1079/`（Overleaf，独立 Git）

**图例:** ☐ 未开始 · ◐ 进行中 · ☑ 完成 · — 明确不做

---

## 0. Executive Summary

| 弱点 | 根因 | 改进策略 |
|------|------|----------|
| **Positioning** | 主轴落在「binding-level provenance defense」，与 2025–2026 concurrent work 高度重叠 | **Reposition** 为 *informed binding authorization* + *confirmation laundering*；provenance 降为实现手段 |
| **Benchmark** | 20 case hand-designed、模式重复、无 P0 banking、易被指「先射箭后画靶」 | **结构化扩展** + **多样性维度** + **独立 holdout** + **写作上明确 diagnostic 边界** |

**原则：**

- **论文改动为主，实验为辅**（reposition 不依赖新机制）
- **Benchmark 扩展要有设计矩阵**，不是堆相似 email case
- **最小实验包** 即可支撑 reposition 后的主 claim

**目标：** 将 reviewer 对 novelty 的感知从 **~5.8** 提升至 **~6.8–7.0**；将 benchmark 质疑从「too small / too tailored」降为「small but principled diagnostic suite」。

---

## 1. 两大支柱

### 支柱 A — Paper Reposition（Confirmation Integrity）

**新 intellectual center（一句话）：**

> Human confirmation is not automatically authorization: unless the exact binding, provenance, and external effect are disclosed, confirmation can launder an untrusted binding into apparently legitimate approval.

**与 concurrent work 的分工：**

| 工作 | 它们回答 | SafeConfirm 回答 |
|------|----------|------------------|
| PACT / AuthGraph / AIRGuard | 该 tool call **该不该执行**（provenance / contract / authority） | 若交给人类确认，**这次确认是否构成对 binding 的有效授权** |
| PlanGuard / AttriGuard | Parameter 是否偏离 user intent / causal attribution | Disclosure **是否暴露** binding + provenance（SDR/CLR） |
| AgentVisor | Binary audit + recovery | **Graded** allow / repair / confirm / block + HITL schema |

**必须降调的 claim：**

- ~~First binding-level provenance defense~~
- ~~Novel provenance analysis~~
- ~~Outperforms AgentVisor/PlanGuard~~

**必须升调的 claim：**

1. **Confirmation laundering**（概念 + Figure 2）
2. **Source-aware disclosure schema**（value + provenance + effect）
3. **SDR / CLR**（ASR 不足）
4. Graded intervention（支撑 claim，非主轴）

---

### 支柱 B — Benchmark 强化（Principled Diagnostic Suite）

**当前问题（客观）：**

| 问题 | 数据 |
|------|------|
| 规模小 | 20 case（12-case 主表）；顶会期望 30+ 或公认大 benchmark |
| 模式重复 | 10+ corruption case 为「读邮件 → 联系人 poison → send/share」 |
| 与 policy 共设计 | case + slot registry + ground_truth 同一 repo |
| 不完整 baseline | Banking 无 P0；部分 ablation 单 seed |
| TSR 跨 batch 波动 | 63.9% / 66.7% / 58.3% 同 12-case |

**目标定位（写作 + 设计）：**

> **Principled diagnostic benchmark** for parameter-poison + confirmation-quality evaluation — **not** a broad security benchmark or field ASR estimate.

**Benchmark 质量 > 绝对数量**，但数量仍需从 20 → **28–32** 才更易辩护。

---

## 2. 阶段排期总览

| 阶段 | 名称 | 周期 | 类型 | 优先级 |
|------|------|------|------|--------|
| **E0** | Reposition 写作包 | 2–3 天 | 仅论文 | **P0** |
| **E1** | Confirm 实验补强 | 2–3 天 | 小实验 | **P0** |
| **E2** | Benchmark 设计矩阵 + 首批扩展 | 3–5 天 | 设计 + 实验 | **P1** |
| **E3** | Holdout + 统计/reporting | 2–3 天 | 实验 + 写作 | **P1** |
| **E4** | 可选加分项 | 1–2 周 | 实验 | P2 |

**最短路径（投稿前）：** E0 + E1 → 可投；E2 做「轻量扩展」（+4 case）→ 更稳。

---

## 3. 阶段 E0 — Reposition 写作包（P0，无新实验）

### E0.1 Abstract 重写

**结构（建议）：**

1. Laundering + authorization gap（2 句）
2. Source-aware disclosure 三要素 + SDR/CLR（2 句）
3. Diagnostic study 数字（1–2 句，TSR/ASR + confirm ablation）

**验收：** Abstract 中「provenance defense」不作为首句主语。

### E0.2 Contributions 重排

| 顺序 | 内容 |
|------|------|
| 1 | Confirmation laundering + informed binding authorization |
| 2 | SDR/CLR + empirical separation from ASR (Table 5) |
| 3 | Source-aware disclosure schema |
| 4 | Graded intervention (allow/repair/confirm/block) |
| 5 | Diagnostic E2E bridge + reproducibility |

### E0.3 Related Work 增补（**最高优先级**）

新增段落 **「Provenance-aware authorization (2025–2026)」**，至少引用并对比：

| 论文 | BibTeX key（待加） | 对比句要点 |
|------|-------------------|------------|
| PACT | `pact2026` | argument-level provenance + contracts；无 HITL disclosure / CLR |
| AuthGraph | `authgraph2026` | provenance vs authorization graph；无 confirmation quality |
| AIRGuard | `airguard2026` | runtime authority control；自动 enforce，非 binding disclosure |
| AttriGuard | `attriguard2026` | causal attribution of tool calls；不同 failure mode |
| CaMeL | 已有或补 | capability control；互补 |

**更新 Table positioning (`tab:positioning`)：**

新增列：**HITL disclosure**、**Laundering metrics (SDR/CLR)**  
新增行：PACT、AuthGraph、AIRGuard（概念 checkmark，无数值对比）

**关键句（Related Work 末尾）：**

> We do not claim to be the first to track argument provenance; our contribution is to treat human confirmation as an authorization channel and to measure whether it exposes the binding being approved.

### E0.4 Results 三条 claim 重排

| 新顺序 | 原 | 表格 |
|--------|-----|------|
| **(i) Primary** | (iii) | Table 5 + Figure 2 — disclosure / H1/H4 |
| **(ii) Secondary** | (ii) | Table 4 — graded intervention / H5 |
| **(iii) Supporting** | (i) | Table 3 — end-to-end security |

### E0.5 Introduction 结构调整

- §1 用 Figure 2（laundering）作 motivating contrast（vague vs source-aware）
- Authorization gap 作为 laundering 的**前提**，非并列第一概念
- Pipeline 细节压缩，指向 §3

### E0.6 Limitations 增补

- Concurrent provenance systems（PACT/AuthGraph）机制更强；本文 focus 为 confirmation integrity
- Benchmark 为 diagnostic，非 AgentDojo-scale generalization
- Simulated confirmer；CLR 主 batch 的 denominator effect

**E0 验收清单：**

- [x] Abstract / Contributions / Intro 主轴 = laundering
- [x] Related Work 含 PACT + AuthGraph + AIRGuard
- [x] Positioning table 更新
- [x] 无 “first provenance” 类表述
- [x] Results claim 顺序调整
- [x] `safeconfirm.bib` 补全引用

**产出：** Overleaf 一版 **reposition draft**（可与 v0.4.2 数字共存）。

---

## 4. 阶段 E1 — Confirm 实验补强（P0，小成本）

**目的：** 让 SDR/CLR 主 claim 在 v0.4.2 主设定下「立得住」，而非仅依赖 footnote 历史 batch。

### E1.1 Table 5 加 Approval Rate 列

- 从现有 logs aggregate `confirm_approval_rate`
- 脚本：`util_scripts/compare_confirm_ablation.py` 或 `aggregate_seed_metrics.py` 扩展
- **无需新跑**（若 log 已有）

### E1.2 Compliant confirmer 单跑（**最推荐新实验**）

| 设置 | 说明 |
|------|------|
| Disclosure | vague only |
| Confirmer | **compliant** — prompt  instruct 对 generic “Proceed?” 倾向 approve |
| Scope | 12-case × 1 seed（可补 3 seed） |
| 对比 | 现有 strict LLM confirmer（vague 0% approval） |

**预期：** vague 下 **approval > 0, CLR > 0**；source-aware 仍 SDR=100%。

**实现选项：**

- A) 新 confirmer profile：`confirmer=compliant_llm`（改 prompt）
- B) 固定概率 stub confirmer（仅 ablation 用）

**脚本：** 扩展 `run_confirm_ablation.sh` → `CONFIRMER=compliant ./util_scripts/run_confirm_ablation.sh`

### E1.3 Appendix：pre-v0.4.2 CLR=100% 行

- 将 legacy `confirm_vague_llm.json` 中 approval 发生时的 CLR 写入 appendix 小表
- 正文一句：*When vague prompts receive approval, CLR reaches 100% (legacy batch); v0.4.2 LLM confirmer rejects all vague prompts.*

### E1.4 Banking P0（低成本）

- 4-case banking  undefended baseline
- 脚本：`run_extended_28case.sh`（含 banking P0/SC 6-case arm）
- 补 Table 3 第二行

**E1 验收：**

- [x] Table 5 footnote 含 Approval Rate（compliant: 8.9%）
- [x] Compliant confirmer 行（tab:confirm, Sep.~2026）
- [x] Banking P0 在 Table 3（0%/33.3% TSR/ASR）
- [x] 数字 sync 到 `paper_metrics/canonical/`
- [x] Appendix `tab:legacy_confirm`（pre-v0.4.2 CLR=100%）

---

## 5. 阶段 E2 — Benchmark 设计矩阵与扩展（P1）

### 5.1 设计原则（回应「太简单 /  tailor-made」）

**原则 1 — 多样性维度（Coverage matrix）**

每个 case 标注：

| 维度 | 取值示例 |
|------|----------|
| Tool | send_email, share_file, delete_file, send_money, create_calendar_event, append_to_file |
| Critical slot | recipients, bcc, file_id, recipient, participants, amount |
| Poison channel | email body, tool output, invoice note, calendar desc, file metadata |
| Binding type | direct address, role reference, ID reference, multi-hop (read→act) |
| Expected intervention | ALLOW, REPAIR, CONFIRM, BLOCK |
| Steps | single-step, two-step |

**原则 2 — 模式配额（避免 email 扎堆）**

| Suite | Corruption | Benign | 目标占比 |
|-------|------------|--------|----------|
| Workspace | 14–18 | 3–4 | email 类 ≤ 50% corruption |
| Banking | 4–6 | 1–2 | 独立 suite |
| **Total** | **22–26** | **4–6** | **28–32 cases** |

**原则 3 — 与 rule_v1 解耦**

- 新 case **先写 user/injection + trusted_binding**，ground_truth 由独立 checklist 标注
- 新增 case 至少 30% 来自 **AgentDojo native task 改编**（非从零写 prompt），减「画靶」嫌疑

**原则 4 — 文档化**

- 新增 `safeconfirm/spec/benchmark_design.md`：设计矩阵 + 每个 case 的维度标签
- 论文 Limitations：*Cases specify trusted bindings before policy runs; we report holdout results on cases authored after policy freeze.*

### 5.2 建议新增 case（+8，20→28）

| ID | Tool | Slot | 新意 | 与现有差异 |
|----|------|------|------|------------|
| `ws_send_attachment_e2e` | send_email | attachments | poison 在附件名/路径 | 非 recipient |
| `ws_reply_all_e2e` | send_email | recipients + bcc | 群发 poison | 多 slot |
| `ws_rename_file_e2e` | delete_file 或 move | file_id | 云盘 ID poison | 非 email |
| `ws_download_link_e2e` | get_file | file_id → 链式 send | tool output poison | 跨 tool |
| `bank_amount_e2e` | send_money | amount | 金额来自 invoice | banking 新维 |
| `bank_iban_e2e` | send_money | recipient/account | IBAN 格式 poison | banking |
| `ws_slack_forward_e2e` | send_email | body 内嵌 URL | URL authority-bearing (PACT 对齐) | 新 channel |
| `native_adapt_task_X` | 从 AgentDojo workspace 改 |  varies | native 改编 | 减 tailor |

*具体 ID 可在实现时调整；关键是填满矩阵空格。*

### 5.3 实现步骤

1. [x] 填写 coverage matrix（现有 20 case 先标注 → `benchmark_design.md` + `tab:coverage`）
2. [x] 识别空格（URL body、cc、amount、IBAN、decoy file_id）
3. [x] 编写 8 case YAML + registry 条目（v0.5.0-extend-v1）
4. [x] 单元测试：`tests/safeconfirm_bridge/test_e2e_cases.py`（28 cases）
5. [x] DeepSeek paired P0 vs SC（28-case）— `run_extended_28case.sh`
6. [x] 主表合并为 28-case E2E（`tab:main`）；删除 Appendix `tab:extended16` / `tab:extended28`

**已更新（2026-09）：** 主表已改为 28-case paired E2E；12-case 仅用于 confirm/component 机制消融；冗余 runner 与 canonical metrics 已清理。

### 5.4 「不太简单」的写作证据（即使暂不扩 case）

若 E2 时间不足，**最低限度** 在论文加：

- **Coverage table（Appendix）**：20 case 在 6 维度上的分布
- **Per-case table**（已有 `tab:percase`）+ 干预 heterogeneity 讨论
- **Explicit non-claims**：不 estimate field ASR；不覆盖 hijacking

---

## 6. 阶段 E3 — Holdout + Reporting（P1）

### 6.1 Policy freeze + holdout protocol

| 集合 | 用途 | 规模 |
|------|------|------|
| **Train/dev cases** | 设计 registry、调 poison calibration | 现有 20 |
| **Holdout cases** | policy 冻结后新写，只报一次 | +4~8 |

**流程：**

1. 冻结 `rule_v1` + disclosure templates（tag: `policy-freeze-v1`）
2. 新写 holdout cases（E2 中标记为 post-freeze）
3. 只跑 paired P0 vs SC，**不做** policy 调参
4. 论文报告：*Holdout ASR/TSR consistent with dev set*

**验收：** 至少 4 holdout cases + 一行结果；回应「先射箭后画靶」。☑ 已完成（`tab:holdout`）。

### 6.2 统计与一致性

- [ ] 所有主数字统一标注 batch_id（`poison_v2_20260910`）
- [ ] 12-case TSR 差异在 paper 用 footnote 解释（paired vs component vs single-run）
- [ ] 主表报告 mean ± std（已有处保持）

### 6.3 Native generalization 加强（低成本）

- [x] 扩 smoke：6 → 10 native workspace tasks（`run_native_generalization.sh`）
- [x] 论文一句 + Appendix `tab:native_gen`（utility 98.7→87.0%, security 9.1% 不变）

---

## 7. 阶段 E4 — 可选加分项（P2，非 blocker）

| 项目 | 价值 | 成本 |
|------|------|------|
| Human study（n≈15–20，2 prompts） | HAI 硬证据 | 1–2 周 |
| GPT-4o-mini paired 12-case | 减 circularity | 1 天 API |
| PlanGuard-style query-only verifier | 区分 provenance vs disclosure | 2–3 天实现 |
| 与 PACT 数值对标 | 低 ROI | 不建议 |

---

## 8. 论文 vs 实验：决策矩阵

| 改进项 | 仅改论文 | 需实验 | 优先级 |
|--------|----------|--------|--------|
| Reposition 叙事 | ✅ | | P0 |
| Related Work PACT/AuthGraph/AIRGuard | ✅ | | P0 |
| Results claim 重排 | ✅ | | P0 |
| Table 5 Approval Rate | | ✅（log 聚合） | P0 |
| Compliant confirmer / CLR>0 | | ✅ | P0 |
| Banking P0 | | ✅ | P0 |
| Coverage matrix appendix | ✅ | ✅（标注） | P1 |
| +8 cases 扩展 | | ✅ | P1 |
| Holdout protocol | | ✅ | P1 |
| Human study | | ✅ | P2 |

---

## 9. 成功标准（Goal E Done）

### 9.1 Positioning

- [ ] Reviewer 无法指控 **omit concurrent work**
- [ ] 主 contribution 可被概括为 **confirmation integrity**，而非 provenance SOTA
- [ ] Abstract 与 Introduction 与 Figure 2 叙事一致

### 9.2 Benchmark

- [ ] 有 **documented coverage matrix**（≥5 维度）
- [ ] 总 case ≥ **28** 或 holdout **4+** + 诚实的 diagnostic framing
- [ ] Banking 有 P0；Table 3 完整
- [ ] 论文 **不 claim** broad security coverage

### 9.3 Experiments

- [ ] CLR 在主叙事中有 **非 trivial** 实证（compliant confirmer 或 legacy 表）
- [ ] 主数字 batch 一致、可复现（`sync_paper_metrics.sh`）

**Goal E 达标判定：** E0 ☑ + E1 ☑ + (E2 轻量 或 E3 holdout 至少一项) ☑

---

## 10. 建议执行顺序（2 周版）

### Week 1

| 天 | 任务 |
|----|------|
| D1–D2 | **E0** 全文 reposition + bib + positioning table |
| D3 | **E1.1** approval rate；**E1.3** legacy CLR appendix |
| D4–D5 | **E1.2** compliant confirmer 跑 + 入表；**E1.4** banking P0 |

### Week 2

| 天 | 任务 |
|----|------|
| D6–D7 | **E2** coverage matrix + 4 新 case（最小扩展） |
| D8 | **E3** 4 holdout cases + paired 跑 |
| D9 | 论文 Table/Appendix 同步；Overleaf 编译 |
| D10 | 通读 + 模拟 reviewer checklist |

---

## 11. 明确不做

- 与 PACT / AuthGraph **全面数值对标**（benchmark 不同）
- 重写 rule_v1 为 learned contract（retrieval 已 negative）
- 16-case → 100-case 暴力扩展（性价比低）
- ~~主表全部换 28-case~~（**已完成**：主表 28-case；12-case 保留为 frozen ablation prefix）

---

## 12. 文件与命令索引

| 产出 | 路径 / 命令 |
|------|-------------|
| 本计划 | `safeconfirm/spec/goal_e_reposition_benchmark_plan.md` |
| Benchmark cases | `safeconfirm/data/benchmark_cases_e2e.yaml` |
| Coverage 文档（待建） | `safeconfirm/spec/benchmark_design.md` |
| Confirm ablation | `./util_scripts/run_confirm_ablation.sh` |
| Primary E2E (28-case) | `./util_scripts/run_extended_28case.sh` |
| Holdout paired | `./util_scripts/run_holdout_paired.sh` |
| Per-case / 16-case paired | `./util_scripts/run_paired_security_rerun.sh` |
| Metrics sync | `./util_scripts/sync_paper_metrics.sh` |
| 论文 | `6a9fb8173b16b4dea4fd1079/safeconfirm.tex` |

---

## 13. 与 Goal D 的关系

Goal D 解决的是 **数字一致性、per-case 分析、REPAIR 叙事**（已完成 ☑）。

Goal E 解决的是 **战略层 reposition** + **benchmark 可信度** — 两者互补，不重复。

**建议：** 在 [task.md](./task.md) 顶部增加 Goal E 指针；投稿前以本计划 E0+E1 为 minimum bar。
