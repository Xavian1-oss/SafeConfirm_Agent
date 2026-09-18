# SafeConfirm — 审稿收口计划（Steps 1–5）

**版本:** 0.2.0（Steps 1–5 已执行，2026-09-18）  
**日期:** 2026-09-18  
**范围:** 仅 **Step 1–5**（一致性 → 指标口径 → fail-open → baseline 叙事 → Table 1/Results 呈现）。Step 6–8（扩 external、detector 假设段、cross-model）见 [evidence_strength_plan.md](./evidence_strength_plan.md) 与文末「后续队列」。  
**论文:** `6a9fb8173b16b4dea4fd1079/safeconfirm.tex`（Overleaf 独立仓库，同步用 `git push` 至 Overleaf，**不**进 GitHub）  
**原则:** 不新增 RL/GNN/learned routing；在现有叙事上 **收口 + 增强可审计性**，不做新模块竞赛。

**图例:** ☐ 未开始 · ◐ 进行中 · ☑ 完成

---

## 0. 背景与优先级

当前稿主线已成立：**confirmation laundering → SDR/CLR → SafeConfirm hierarchy → contract-style baselines → E2E → external → scope**。  
模拟审稿约 **6/10 borderline**：概念与诊断实验有价值，主要扣分在 **文稿一致性、指标可操作定义、fail-open 架构、表格阅读成本**。

| Step | 类型 | 价值 |
|------|------|------|
| **1** | 硬一致性 | 低工作量，高信任度（删残留 claim） |
| **2** | 指标审计 | 防 “概念好、判定模糊” |
| **3** | 系统安全 | 最真实的 architecture weakness |
| **4** | 定位叙事 | 防 “缺 PACT 类 baseline” 又不冒 faithful reproduction |
| **5** | 呈现 | 降 reviewer 认知负荷，Table 1 自成证据地图 |

**建议执行顺序:** 1 → 2 → 5（纯 tex）可并行准备；**3 需代码+测试** 后再改 Limitations；**4 以 tex 为主**（baseline 已跑完）。

---

## Step 1 — 正文与 Appendix 一致性审计

### 要解决的 reviewer concern

- “Appendix 引用了不存在的实验” → 怀疑删表忘删 claim、数字不可信。

### 已知问题（2026-09-18）

- Method §（`rule_v1` 段）仍可能写：**“Alternative learned policies match `rule_v1` on our suite (Appendix Table~\ref{tab:supp})”**。
- Appendix `tab:supp` **已删除** retrieval-learned / rule_v1 58.3 行，仅留 repair + prompt-defense。
- 叙事决策：**不恢复** retrieval negative；贡献是 **hierarchy**，不是 selector 竞赛。

### 具体工作

| ID | 动作 | 位置 |
|----|------|------|
| **S1-1** | 删除 learned-policy 整句；若需保留一句，改为 “hierarchy is the contribution, not a hand-written rule name” （已有类似表述则合并去重） | `safeconfirm.tex` §Method |
| **S1-2** | 全文检索并清零：`learned policy`, `retrieval-learned`, `retrieval policy`, `Alternative learned`, `Appendix Table 4`（无 label 时搜 `tab:supp` + learned） | tex + `safeconfirm/spec/*.md` 若引用 |
| **S1-3** | 核对 **claim → 表/图**：[claim_evidence_audit.md](./claim_evidence_audit.md) 与 [paper_experiment_consistency.md](./paper_experiment_consistency.md) 各一行对应 Table 1/2、Appendix | spec |
| **S1-4** | 核对数字：主表 `rule_v1` 75.0（12-case, 3-seed provenance batch）**不得**与附录 repair 快照混比；附录 caption 已有 “do not compare across tables” — 正文 Method 勿再指向附录证明 “learned tie” | tex |

### 论文同步点

- §Method `Intervention hierarchy and policy selection`
- §Discussion（若仍提 retrieval ties）
- Appendix `tab:supp` caption（保持 “separate snapshot”）

### 完成标准（可停）

- [ ] 任意 `grep -i retrieval\|learned policy` 在 tex 中仅剩 Related/Limitations 中 **明确 out-of-scope** 或代码路径说明（理想：tex 零命中）。
- [ ] 每条带 “Appendix Table” 的句子在附录中 **有对应行或已删句**。
- [ ] Overleaf `main` push 一次；GitHub **不含** Overleaf 目录（已 gitignore）。

### 工作量

**~30–60 min**（以 tex + spec 为主）。

---

## Step 2 — CLR / laundering risk 可操作定义写死

### 要解决的 reviewer concern

- SDR/CLR “概念好，但某个 confirmation event 算 0 还是 1 要靠读作者脑子”。
- 混淆 **detector error** vs **metric definition**。

### 具体工作

| ID | 动作 | 位置 |
|----|------|------|
| **S2-1** | 在 §Setup **Metrics**（式 (SDR)/(CLR) 之后）增加 **Operational rules** 小段（英文，约 6–8 句），建议包含： | `safeconfirm.tex` |
| | • **Gap remaining（批准时点）:** 至少一个 critical slot 既无 trusted authorization，也未被 trusted repair/user correction 替换为 authorized binding → gap 仍在。 | |
| | • **CLR:** `approved(r)` 且批准时点 **gap remaining** → laundering risk（计 CLR 分子）；与 disclosure 是否完整 **独立**（不完整 → 降 SDR，不自动等价 CLR）。 | |
| | • **Repair / correction:** repair 或 confirmer 返回的 corrected binding 经 **re-analyze** 后若无 gap → 该次批准不计 laundering；若仍 untrusted → 仍计。 | |
| | • **Partial disclosure:** SDR 侧 `disclosure complete`=false；若用户仍批准且 gap 在 → CLR 可计 1。 | |
| | • **Detector error:** provenance 误标属于 **upstream detector limitation**，不是 CLR 阈值定义的一部分（Limitations 可交叉引用）。 | |
| **S2-2** | 与实现对齐：阅读 `safeconfirm/evaluation/metrics.py` 中 SDR/CLR 判定函数，列出与上述规则 **一致 / 需改** 的分支 | 代码 |
| **S2-3** | 若代码与文案不一致：**以文案规则为准改代码**，或收窄文案至代码真实行为；补 **1–2 个单元测试**（合成 `InterventionRecord`：repair 后 gap 清除 → CLR 不计） | `tests/safeconfirm/test_metrics.py` |
| **S2-4** | 更新 [requirements.md](./requirements.md) 指标小节（与 tex 同段 operational 摘要） | spec |

### 论文同步点

- §Setup Metrics（主定义）
- 可选：§Method `Intervention execution` 一句 “re-analyze after repair/correction”（与 gap 更新一致）

### 完成标准（可停）

- [ ] 给定一条脱敏 intervention record，团队可用 **检查表**（gap? disclosure complete? approved?）唯一确定 SDR/CLR 贡献，无需口头解释。
- [ ] `uv run pytest tests/safeconfirm/test_metrics.py -q` 通过。
- [ ] [paper_experiment_consistency.md](./paper_experiment_consistency.md) 中 SDR/CLR 行引用 “operational rules in §Setup”。

### 工作量

**~2–4 h**（文案 + 代码对齐 + 小测试）。

---

## Step 3 — Unknown tool fail-open → conservative fallback

### 要解决的 reviewer concern

- “Registry 未覆盖的工具 silent ALLOW” 与 “binding authorization” 叙事矛盾（open-world / MCP 场景）。

### 当前实现（事实源）

- `safeconfirm/pipeline/orchestrator.py`：`get_tool_entry(...) is None` → 构造 record，`selected_intervention=ALLOW`，`executed=True`，**无 slot 分析**。

### 推荐方案（计划采用 **方案 B**）

| 方案 | 行为 | 成本 |
|------|------|------|
| A | unknown → BLOCK | 低；utility 可能差 |
| **B（推荐）** | unknown → **conservative SOURCE_AWARE_CONFIRM**（或 `CONSERVATIVE_CONFIRM` 别名）：披露 “tool not in registry” + 全 args + 外部效应提示；默认 **不 executed** 直至确认路径完成 | 中 |
| C | schema 启发式推断 critical slots | 高；放 Future work |

**配置建议:** `SafeConfirmConfig.unknown_tool_policy: allow | conservative_confirm | block`，默认 **`conservative_confirm`**（论文与 E2E 一致）；benchmark 28+8 case 均在 registry 内，行为不变，需 **新增 2–3 synthetic unknown-tool cases** 证明 fallback 非 silent allow。

### 具体工作

| ID | 动作 | 位置 |
|----|------|------|
| **S3-1** | 实现 unknown-tool 分支：不 `executed=True` 直放；走与 gap 类似的 confirm/block 路径 | `orchestrator.py`, 可能 `rule_policy.py` / executor |
| **S3-2** | Bridge E2E：unknown tool 时 ASR/TSR 与 log 字段一致 | `safeconfirm_bridge/runner.py` |
| **S3-3** | 新增 minimal cases（YAML 或 pytest 直接调 pipeline）：`unknown_tool_*` 2–3 个 | `tests/safeconfirm/` 或 `tests/safeconfirm_bridge/` |
| **S3-4** | **不重跑** 主表 28-case（registry 全覆盖）；可选 smoke：unknown case 一条 | |
| **S3-5** | 论文：删 Limitations “unknown → ALLOW”；改 Method 一句 fallback；Discussion 一句 deployment（MCP/schema drift） | `safeconfirm.tex` |

### 论文同步点

- §Method（registry + unknown handling）
- §Limitations（删除 fail-open 自曝 **或** 改为 “prior versions”; 改后写清 default conservative）
- 不必改 Table 1 数字（若 benchmark 无 unknown tool）

### 完成标准（可停）

- [ ] 代码默认 **非 silent ALLOW** on unknown tool（测试证明）。
- [ ] 正文 **不再** 写 “missing registry → ALLOW without analysis”。
- [ ] 主 benchmark 结果数字 **无需** 因本步重跑（除非发现 registry 漏标 tool — 则修 registry 而非改 fallback）。

### 工作量

**~4–8 h**（实现 + 测试 + tex）。

---

## Step 4 — Provenance-block 升格为 contract-style baseline 叙事

### 要解决的 reviewer concern

- “为何不与 PACT/AuthGraph 比？” vs “你没 faithful 复现 PACT”。

### 现状（已有资产）

- 代码/实验：`baseline_block` / `provenance-block`，12-case × 3 seeds，ASR 0、TSR ~22.2（Table 1）。
- 实验设计：**gap detection 给定** 后比较 **binary deny-on-gap** vs **recovery hierarchy**。

### 具体工作（**以写作为主**，无需新跑数）

| ID | 动作 | 位置 |
|----|------|------|
| **S4-1** | §Setup **Models and defenses** 或 Baselines 段增加 **Contract-style provenance-block** 定义（3–4 句）：critical binding 违反 trusted-source contract → block；**behavior-level abstraction** of PACT/AuthGraph-style enforcement，**非** full reproduction | tex |
| **S4-2** | §Related Work（Provenance-aware 段）加 **对比句**：并发系统问 “should execute?”；本 baseline 隔离 “once gap detected, binary block only” | tex |
| **S4-3** | §Results **RQ2** 首句强调 claim：**同 gap detection 下，binary enforcement vs authorization recovery → TSR 22.2 vs 75.0，ASR 均为 0**；**不** claim 数值优于 PACT | tex |
| **S4-4** | Table 1 行标签可选：`Provenance-block (contract-style)` — 保持可辨，勿改名 PACT | tex |
| **S4-5** | [claim_evidence_audit.md](./claim_evidence_audit.md) RQ2 行：evidence = Table 1 provenance block + hierarchy rows；wording = contract abstraction | spec |

### 完成标准（可停）

- [ ] Reviewer 能回答：“baseline 对应 literature 哪类 alternative？”→ **contract-style deny-on-gap**。
- [ ] 全文 **无** “we implement PACT” / “we beat PACT” 类表述。

### 工作量

**~1–2 h**（纯 tex/spec）。

---

## Step 5 — Table 1 与 Results 作为「证据地图」

### 要解决的 reviewer concern

- Table 1 块多、“—” 多、12 vs 28 混排 → 第一遍读不懂每块为何存在。

### 具体工作

| ID | 动作 | 位置 |
|----|------|------|
| **S5-1** | Table 1 三个 `\multicolumn` 标题改为与 RQ 对齐： | `safeconfirm.tex` `tab:results` |
| | • **RQ1 — Confirmation quality**（原 confirmation ablation） | |
| | • **RQ2 — Authorization recovery policy**（provenance-only vs hierarchy） | |
| | • **RQ3 — End-to-end security**（28-case paired） | |
| **S5-2** | Caption 增加 **两行 metric 族**：Task-level（TSR, ASR）；Authorization-channel（SDR, CLR） | caption |
| **S5-3** | 将 “--- not measured” 改为 **“--- (n/a)”** + footnote 解释：**block 无 confirmation → SDR/CLR n/a**；**CLR 分母 0 → n/a**；**E2E 主报告 task-level，channel metrics 未聚合** | caption + tablenotes |
| **S5-4** | §Results：每个 **RQ* 首段只答一个问题**（RQ4 repair 仍指 Appendix）；删 RQ 段内重复 ASR/TSR 串述 | §Results |
| **S5-5** | Figure 2 与 RQ1 绑定；Table 2 external 明确 **RQ3 子块**（lineage），非 RQ1 | §Results 一句 |
| **S5-6** | [paper_experiment_consistency.md](./paper_experiment_consistency.md) Table 1 块名与 RQ 标签一致 | spec |

### 完成标准（可停）

- [ ] **只读 Table 1 + caption** 可理解三块对应 RQ1–3 及为何有 n/a 列。
- [ ] §Results 与 Table 1 块标题 **一一对应**（RQ4 仅 Appendix）。

### 工作量

**~2–3 h**（tex 排版 + 通读）。

---

## 汇总 checklist（Steps 1–5）

| Step | 代码 | 论文 | 测试/跑数 | 状态 |
|------|------|------|-----------|------|
| 1 一致性 | — | ☑ | grep audit | ☑ |
| 2 CLR 口径 | metrics.py | §Setup | test_metrics | ☑ |
| 3 fail-open | orchestrator + unknown_tool | §Method/Lim | test_unknown_tool | ☑ |
| 4 baseline 叙事 | — | Setup/Related/Results | — | ☑ |
| 5 证据地图 | — | Table 1 + Results | — | ☑ |

**Steps 1–5 全部完成后预期效果:** 稿面 **更干净**（6 → 6.5+ 可读性/可信度），**不依赖** Step 6–8 也能 rebuttal 大部分 consistency/metric/baseline 类意见。

---

## 后续队列（本计划 **不** 包含）

| Step | 内容 | 参考 |
|------|------|------|
| 6 | External 8 → 12–16 cases，policy frozen | [benchmark_design.md](./benchmark_design.md), `benchmark_cases_external.yaml` |
| 7 | Provenance detector interface + error boundary 段 | §Method 假设段；可选 label-flip sensitivity |
| 8 | Cross-model signature only（RQ1 + E2E ASR） | `util_scripts/run_cross_model_signature.sh`, evidence_strength_plan E-P1-3 |

---

## 同步与发布

| 产物 | GitHub (`SafeConfirm_Agent`) | Overleaf |
|------|------------------------------|----------|
| Step 3 代码/测试 | commit + push | — |
| Step 1–2, 4–5 tex | —（目录 gitignore） | commit + push |
| Spec 本文件 + consistency/audit | commit + push | — |

**维护:** 完成某 Step 后将上表 **状态** 改为 ☑，并在 [task.md](./task.md) S8 小节加一行指针（可选）。
