# SafeConfirm — 证据强度与贡献边界改进计划（Post-Reposition）

**版本:** 0.2.0  
**日期:** 2026-09-16  
**变更 (v0.2.0):** 导师反馈 — 执行顺序（baseline 先于 cross-model）、external **3 seeds**、banking 修复优先级、**authorization invariant** 表述、**Claim–Evidence Audit**、MV5 顺序、防计划膨胀  
**依赖:** [task.md](./task.md), [benchmark_design.md](./benchmark_design.md), [post_submission_experiment_plan.md](./post_submission_experiment_plan.md)  
**触发:** 7 页稿模拟 AAMAS 审稿（~6–6.5/10 borderline）；**叙事已清晰，瓶颈在证据强度与贡献边界**  
**论文:** `6a9fb8173b16b4dea4fd1079/safeconfirm.tex`

**图例:** ☐ 未开始 · ◐ 进行中 · ☑ 完成 · — 明确不做（Limitations / rebuttal only）

**计划原则:** 不堆 SafeConfirm 模块（无 RL / learned gate / 新 architecture）。最强形态 = **新 failure mode + authorization abstraction + SDR/CLR + 简单 hierarchy + 外部证据**。防止计划膨胀，**P0 + 前几个 P1 做扎实即可**。

---

## 0. 对反馈的总体判断

| 反馈主题 | 是否有道理 | 说明 |
|----------|------------|------|
| P0 28-case 自设计、external validity 弱 | **是** | 需 **AgentDojo-lineage external** 子集，**≥3 seeds** |
| P0 Banking 0 TSR | **是** | 根因优先：**evaluator / prompt / step limit → 换模型 → 修 case（仅 bug）** |
| P0 vs PACT 等 novelty | **是** | **P0-3 baseline** + positioning + confirmation-channel 实证；**formalization 主要提升 rigor，不是 novelty 主证据** |
| P1 SDR/CLR 口径 / denominator=0 | **是** | denominator=0 → **N/A**，不写机械 0% |
| P1 formalization | **是** | **Authorization invariant**，勿包装成 heavy theorem |
| P1 cross-model | **是** | **Signature only**（SDR/CLR pattern + P0 vs SC ASR）；非全表重跑 |
| P1 Claim–Evidence Audit | **是（新增）** | 防止 claim 比 evidence 多走半步 |
| P2 Results RQ / registry / retrieval | **是** | 写作与诚实性 |

**AC 三问（meta-review 靶心）:**

| 问题 | 主要证据（非 formalization） |
|------|------------------------------|
| (1) Laundering 是否与 provenance 失败足够区分？ | **E-P0-3** baselines + Related Work + confirm/SDR/CLR |
| (2) 28 hand-crafted 是否支撑 claims？ | **E-P0-1** external（3 seeds）+ raw counts |
| (3) 是否 preserve utility（banking 0 TSR、单模型）？ | **E-P0-2** 根因 + **收窄 claim**（E-P1-3 略过） |

---

## 1. 目标与成功标准

| 层级 | 目标 | 验收 |
|------|------|------|
| **G1 叙事** | confirmation laundering + informed binding authorization | ☑ 已达（7 页稿） |
| **G2 证据** | 外部效度 + novelty 实证 + utility 可辩护 | 本计划 |
| **G3 严谨** | metrics 可审计、invariant 定义、claim–evidence 对齐 | 本计划 |

**成功标准（投稿前）:**

- **External:** 8–12 AgentDojo-derived cases，policy-freeze-v2 后编写；**1 model × 3 seeds** paired P0 vs SC（优先于 3 model × 1 seed 用于此 block）
- **Banking:** 根因文档；优先修 evaluator/prompt/limit；**不**为 TSR 简化 task，除非证明 unsatisfiable/bug
- **Novelty empirical:** provenance_block + provenance_vague vs SafeConfirm（同 suite）
- **SDR/CLR:** 公式 + N/A 规则（代码 + 论文）
- **Cross-model:** — 投稿略过（Limitations：DeepSeek-only）
- **E-P1-6:** Claim–Evidence Audit 表完成，Abstract/Conclusion 与 evidence 对齐

**明确不做（out of scope）:**

- 100+ 自造 case；RL / policy network / 新 defense architecture
- 全量 cross-model 重跑所有 ablation
- Human-subjects（可选 P2+）；instruction-hijacking 主实验
- Retrieval 竞赛；external 上调 `rule_v1`

---

## 2. 优先级任务映射

| ID | 审稿项 | Pri | 工作包 | 状态 |
|----|--------|-----|--------|------|
| **E-P0-1** | External / native-lineage eval | P0 | §3.1 | ☑ 代码+3-seed 跑数；论文表待写 |
| **E-P0-2** | Banking 0 TSR 根因与修复 | P0 | §3.2 | ☑ 根因+诊断+loop=12；TSR 未修、叙事收窄 |
| **E-P0-3** | Provenance-only + generic-confirm baseline | P0 | §3.3 | ☑ 12-case 3-seed 跑数；正文 prose 待写 |
| **E-P1-1** | SDR/CLR 严格定义与 N/A | P1 | §3.4 | ☑ |
| **E-P1-2** | Authorization invariant（半页） | P1 | §3.5 | ☑ Problem § + Method 引用 |
| **E-P1-3** | Cross-model signature only | P1 | §3.6 | — (略过 OpenAI；Limitations 写单模型) |
| **E-P1-4** | Human → generic confirmation 措辞 | P1 | §3.7 | ☐ |
| **E-P1-5** | Bootstrap CI / raw attack counts | P1 | §3.8 | ☐ |
| **E-P1-6** | **Claim–Evidence Audit** | P1 | §3.13 | ◐ 表已填；Abstract/tex 待同步 |
| **E-P2-1** | Results 重写为 RQ1–RQ4 | P2 | §3.9 | ☑ |
| **E-P2-2** | Contributions 合并为 3 条 | P2 | §3.10 | ☑ |
| **E-P2-3** | Registry fail-open 论文与代码一致 | P2 | §3.11 | ☐ |
| **E-P2-4** | 删/缩 retrieval 附录 | P2 | §3.12 | ☐ |

---

## 3. 分任务规格

### 3.1 E-P0-1 — AgentDojo-derived external suite（8–12 cases）

**目的:** Diagnostic（28）→ mechanism validity；**External lineage** → external validity。

**设计原则:** 同 v0.1（native prompt 语义、parameter poison only、policy-freeze-v2、不调 `rule_v1`）。

**实现路径:** 同 v0.1（`benchmark_cases_external.yaml`、`run_external_eval.sh`、分开报告）。

**验收（加严）:**

- [x] 8–12 cases 单元测试 + ground_truth 校验
- [x] **≥3 seeds**（同一 agent model，默认 DeepSeek）paired P0 vs SC on external only（`evidence_20260916_1531`）
- [x] 报告 mean±std（`aggregate_seed_metrics`）；12-case external SC ASR ≤ P0（0% vs 39.4%，batch `external_v2_12case_20260919`）
- [x] 论文：Table~\ref{tab:external} + Limitations 区分 diagnostic vs external

**API 预算原则:** external block 优先 **1 model × 3 seeds**，再考虑加第二 model 做 signature（§3.6）。

---

### 3.2 E-P0-2 — Banking 0 TSR 根因

**现象:** Banking SC/P0 **0% TSR**；P0 **40% ASR**。

**修复优先级（严格顺序）:**

1. **H-D / infrastructure:** `utility_satisfied`、ground_truth、prompt template、**step limit**、poison 是否破坏 benign 路径  
2. **H-B / H-C:** poison calibration、confirmer/planner loop（logs）  
3. **H-A model:** 仅 banking 子集换 **更强 model**（可与 E-P1-3 合并预算）  
4. **Case 变更（最后手段）:** 仅当证明 **benchmark bug / unsatisfiable task**；文档化「修 bug」而非「降难度换 TSR」

**禁止默认方案:** ~~简化 1–2 banking case 为 minimal transfer~~（除非 written 根因为 unsatisfiable）。

**行动:**

- [x] `util_scripts/run_banking_benign_check.sh`：benign-only banking，P0 TSR  
- [x] 根因报告：`safeconfirm/spec/banking_tsr_root_cause.md`  
- [x] 论文：banking 不写 utility claim；SC **0% ASR**；P0 TSR 5.6%

---

### 3.3 E-P0-3 — Provenance-only / generic-confirm baselines

**目的:** 实证回答：「Perfect gap detection + generic confirm 够吗？」→ **不是 novelty 的 Related Work  alone**。

| Baseline | 行为 |
|----------|------|
| **provenance_block** | Trusted → allow；gap → **block**（无 repair，无 source-aware confirm） |
| **provenance_vague** | Gap → generic confirm（`baseline_vague`；可选 compliant confirmer） |
| **SafeConfirm rule_v1** | 已有 |

**验收:**

- [x] 12-case 或 28-case 上已有/重跑脚本 **provenance_block**（=`baseline_block`；vague=`baseline_vague`）
- [x] prose：Results RQ2 + provenance 行（75/22/25% TSR）

**优先级:** 在 cross-model 之前完成（novelty > robustness）。

---

### 3.4 E-P1-1 — SDR / CLR 定义与 N/A

- **SDR** = valid source-aware disclosures / all confirm interventions (`VAGUE_CONFIRM` + `SOURCE_AWARE_CONFIRM`); denominator 0 → **N/A** (not 0%).
- **CLR** = approved confirmations with laundering risk / approved confirmations with **binding authorization gap**; denominator 0 → **N/A**.
- Implementation: `safeconfirm/evaluation/metrics.py`; bridge prints `N/A`; composite uses 0 when N/A for scoring only.

---

### 3.5 E-P1-2 — Authorization invariant（非 Theorem 1）

**位置:** §2 末或 §3 首。

**对象:** `C_f`, `c=(f,a)`, `A_u(s,v)`, `G(c)`, informed confirm predicate.

**Authorization invariant（系统安全不变量）:**

```text
∀ c ∈ ExecutedCalls, ∀ s ∈ C_f:
  A_u(s, a_s)  ∨  Reauthorized(s, a_s)
```

其中 `Reauthorized` = trusted repair 路径，或 full disclosure 后 explicit approve。

**正文说明:** SafeConfirm 四条路径（allow / repair / disclose+confirm / block）如何 **maintain** 该 invariant；**不**称「Proposition 1」或完整证明，避免「定义推出结论」观感。

**验收:**

- [ ] Abstract 用 **define** / **characterize**，少用 heavy **formalize** 若 invariant 已写清

---

### 3.6 E-P1-3 — Cross-model validation（signature only）

**只验证核心 claim，不重跑全部 ablation:**

| Signature pattern | 实验 |
|-------------------|------|
| **A** | Source-aware vs vague：**同 ASR 附近，SDR/CLR 分化**（confirm 子集） |
| **B** | P0 vs SafeConfirm：**ASR 下降**（12-case 或 28-case 子集即可） |

**模型:** DeepSeek（主表）+ **1 额外 model**（GPT-4o-mini / Gemini Flash / Claude Haiku 择一）；若预算允许再 +1。

**不做:** 三模型 × 全表；external 上的 multi-model 可 Phase 2。

**验收:**

- [ ] 附录小表 2–3 行 × 2 models，qualitative 同向  
- [ ] Limitations：主表 DeepSeek；cross-model = **robustness**，非 novelty 主证据

---

### 3.7 E-P1-4 — 措辞：human → generic confirmation

（同 v0.1。）

---

### 3.8 E-P1-5 — 统计：CI 与 raw counts

（同 v0.1。）

---

### 3.9 E-P2-1 — Results 结构（RQ）

```text
RQ1 — Laundering independent of ASR?        → confirm + Fig 2
RQ2 — Hierarchy vs provenance-only?         → intervention + E-P0-3 baselines
RQ3 — E2E + external lineage?               → 28-case + external block
RQ4 — Repair contributes?                  → appendix repair on/off（短）
```

---

### 3.10 E-P2-2 — Contributions 三条

（同 v0.1。）

---

### 3.11 E-P2-3 — Registry fail-open

（同 v0.1。）

---

### 3.12 E-P2-4 — 删缩 retrieval

（同 v0.1。）

---

### 3.13 E-P1-6 — Claim–Evidence Audit（投稿前必做）

**目的:** 每个 strong claim 对应唯一 evidence；删掉或收窄 **无证据** 的半步。

**产物:** [submission_consistency_audit.md](./submission_consistency_audit.md) §2 claim 表

**模板（填完并驱动 tex 修改）:**

| Claim（Abstract / Intro / Conclusion） | Evidence | 风险若过写 |
|----------------------------------------|----------|------------|
| Confirmation laundering occurs | Table 1 confirm + Fig 2 | 勿写 human subjects 已证 |
| ASR insufficient for HITL eval | Equal ASR, different SDR/CLR | 勿写所有 settings |
| SafeConfirm improves utility | Workspace intervention/E2E | **勿写 banking utility** 若仍 0 TSR |
| Beyond handcrafted cases | **E-P0-1** external, 3 seeds | 勿写 field ASR / statistical generalization |
| Distinct from provenance-only | **E-P0-3** + SDR/CLR | 勿写 beat PACT numerically |
| Works across models | **E-P1-3** signature only | 勿写「tool-using LLM agents」= 全模型 SOTA |
| Preserve utility / least-disruptive | rule_v1 vs block/allow | 对齐 banking 实际数字 |

**验收:**

- [ ] 每一 Abstract 句至少一行 evidence 或改措辞  
- [ ] Conclusion 删除无 evidence 的 domain-general 句

---

## 4. 推荐执行顺序（v0.2 — 导师调整）

```text
 1. E-P0-2   Banking 根因
 2. E-P0-1   External **12** cases（3 seeds）☑
 3. E-P0-3   Provenance / generic-confirm baseline   ← novelty，先于 cross-model
 4. E-P1-1   SDR/CLR + N/A
 5. E-P1-3   Cross-model signature only
 6. E-P1-2   Authorization invariant（低成本，可并行写作）
 7. E-P1-6   Claim–Evidence Audit → 驱动 tex 收窄
 8. E-P2-1   Results RQ 结构
 9. E-P1-4   Generic confirmation 措辞
10. E-P2-3   Registry honesty
11. E-P1-5 / E-P2-2 / E-P2-4 收尾
```

**Minimum viable（投稿前 5 项）:**

1. **E-P0-2** Banking  
2. **E-P0-1** External（**3 seeds**）  
3. **E-P0-3** Provenance/generic baseline  
4. **E-P1-1** SDR/CLR  
5. ~~**E-P1-3** Cross-model signature~~ **投稿前略过**（无第二模型 API 预算；主表 DeepSeek + Limitations）

→ 目标 reviewer **7–7.5/10**；**E-P1-2**、**E-P1-6** 强烈建议同 sprint 完成（低成本、防 overclaim）。

**Formalization / invariant:** 排在 cross-model 之后亦可，**不**作为 novelty 主证据。

---

## 5. 论文 / 代码 / 脚本清单

| 产物 | 路径 |
|------|------|
| External cases | `safeconfirm/data/benchmark_cases_external.yaml` |
| External runner | `util_scripts/run_external_eval.sh`（`SEEDS=s0 s1 s2`） |
| Banking diagnostic | `util_scripts/run_banking_benign_check.sh` |
| Banking 根因 | `safeconfirm/spec/banking_tsr_root_cause.md` |
| Claim audit | `safeconfirm/spec/submission_consistency_audit.md` |
| Baseline policies | bridge / `baseline_block`, `baseline_vague` |
| Metrics | `safeconfirm/evaluation/metrics.py` + tests |
| 论文 | `6a9fb8173b16b4dea4fd1079/safeconfirm.tex` |

---

## 6. 与现有 spec 关系

| 文档 | 关系 |
|------|------|
| [post_submission_experiment_plan.md](./post_submission_experiment_plan.md) | E1–E3 已完成 |
| [reviewer_closeout_plan_1_5.md](./reviewer_closeout_plan_1_5.md) | Goal D 收口（已完成） |
| [benchmark_design.md](./benchmark_design.md) | 待更新：diagnostic vs external 双轨 + 3-seed 协议 |

**task.md:** 阶段 **S8 — Evidence strength (Goal F)** → 本文档。

---

## 7. 开放问题

1. External：**独立 Table** vs Table 1 第四 block — 建议 **独立小表** 以免稀释 diagnostic 叙事。  
2. Banking：48h 内根因分支（修 infra / 换模型 / narrative-only ASR）。  
3. ~~Cross-model~~ 已 scope-out（OpenAI 略过）。  
4. **Scope freeze:** 本 v0.2 之后 **不新增** P0 任务 unless AC-level 新 blocker。

---

*End of evidence_strength_plan.md v0.2.0*
