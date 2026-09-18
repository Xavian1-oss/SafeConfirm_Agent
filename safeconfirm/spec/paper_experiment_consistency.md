# 论文 ↔ 实验一致性核对（SafeConfirm AAMAS 2027）

**版本:** 0.2.0 · 2026-09-18  
**论文:** `6a9fb8173b16b4dea4fd1079/safeconfirm.tex`  
**刷新:** `./util_scripts/sync_paper_metrics.sh` 后对照 `paper_metrics/canonical/`

---

## 1. 逻辑闭环（叙事链）

```text
Problem: authorization gap + generic confirmation can launder bindings
    → Metrics: SDR/CLR (same ASR, different channel quality)     [RQ1, Table confirm]
    → vs provenance-only block/vague at same gap detection       [RQ2, Table provenance rows]
    → E2E: P0 vs SafeConfirm on 28 diagnostic + 8 external       [RQ3, Table E2E + tab:external]
    → Repair ablation (utility, not novelty)                       [RQ4, Appendix tab:supp]
Limitations: DeepSeek-only, LLM confirmer proxy, conservative unknown-tool fallback, no banking utility claim
Metrics: SDR/CLR operational rules in paper §Setup (gap remaining at approval; detector errors upstream)
```

**Claim 边界（必须与实验一致）**

| Claim | 支持 | 禁止写 |
|-------|------|--------|
| Laundering / SDR–CLR | 12-case confirm ablation | Human subjects 已证 |
| ASR ↓ vs P0 | extended28 workspace + external 8 | Field ASR / 全 settings |
| Provenance vs hierarchy | provenance baselines Sep.~2026 | Beat PACT 数值 |
| Banking security | extended28 + paired: SC ASR 0% | Banking TSR / utility |
| External validity | 8 lineage, 3 seeds, 13/21→2/21 pooled | “Robust prevention” / SC ASR=0 |

---

## 2. Table 1 (`tab:results`) 行级来源

**块标签（证据地图）:** RQ1 confirmation quality · RQ2 authorization recovery · RQ3 end-to-end security. SDR/CLR `---` = n/a (block/allow rows or E2E task-level only).

| 论文行 | TSR | ASR | SDR | CLR | Canonical JSON | 脚本 / 批次 |
|--------|-----|-----|-----|-----|----------------|-------------|
| Source-aware disclosure | 55.6 | 0 | 100 | 0 | `confirm_sa_llm_poison_v2.json` | `run_confirm_ablation.sh` (v0.4.2) |
| Vague disclosure | 22.2 | 0 | 0 | 0 | `confirm_vague_llm_poison_v2.json` | 同上 |
| Vague + compliant | 22.2 | 6.7 | 0 | 66.7 | `confirm_vague_compliant_llm.json` | `CONFIRMER=compliant_llm` |
| SafeConfirm rule_v1 (provenance block) | **75.0** | 0 | 100 | 0 | `provenance_rule_v1_aggregate.json` | `run_provenance_baselines.sh`, `evidence_20260916_1531` |
| Provenance-block | 22.2 | 0 | — | — | `provenance_block_aggregate.json` | 同上 |
| Provenance-vague | 25.0 | 0 | 0 | — | `provenance_vague_aggregate.json` | 同上 |
| Allow all gap (ablation) | 19.4 | 46.7 | — | — | `component_12case_poison_v2.json` → `allow_ds` | `run_component_ablation.sh` |
| Workspace SC / P0 | 39.4 / 27.3 | 0 / 38.3 | — | — | `extended28_ws_sc.json` / `extended28_ws_p0.json` | `run_extended_28case.sh` (20260911) |
| Banking SC | 0 | 0 | — | — | `extended28_banking_sc.json` | 同上 |
| Banking P0 TSR | **5.6** | 40 | — | — | `banking_paired_p0_aggregate.json` | `evidence_20260916_1531/banking_paired` |
| Banking P0 ASR | (同上行) | 40 | — | — | `extended28_banking_p0.json` ASR 40% | extended28（与 paired ASR 一致） |

**Banking TSR 双批次说明（避免“矛盾”）**

- **Table 1 banking P0 TSR 5.6%** 来自 Sep.~2026 **paired 复跑**（6 case × 3 seed，1/18 成功）。
- **extended28** 同批 banking P0 **TSR 0%**（`extended28_banking_p0.json`）— 更早/同 suite 全量脚本下的聚合；**ASR 40%** 与 paired 一致。
- 正文已区分：**benign 诊断 0%** vs **6-case aggregate 5.6%**。

**Provenance 75% vs 旧 component 66.7%**

- 主表 **75% TSR** 用 Sep.~2026 `run_provenance_baselines.sh`（LLM confirmer，完整 E2E 路径）。
- `component_12case_poison_v2.json` 中 `rule_v1` 仍为 **66.7%** — 旧 component 批次；**勿混进主表**。

---

## 3. Table 2 (`tab:external`)

| 字段 | 论文 | JSON | 备注 |
|------|------|------|------|
| P0 ASR | 61.9 ± 6.7 | `external_p0_aggregate.json` | 7 corruption / seed |
| SC ASR | 9.5 ± 6.7 | `external_sc_aggregate.json` | 非 0%，叙事用 qualitative pattern |
| Pooled attacks | 13/21 vs 2/21 | 手算自 `evidence_20260916_1531/p0_s*` / `sc_s*` | Wilson CI 见 tex 脚注 |

脚本：`run_external_eval.sh` · 用例：`benchmark_cases_external.yaml`

---

## 4. Appendix

| 表 | 来源 | 脚本 |
|----|------|------|
| `tab:coverage` | `benchmark_cases_e2e.yaml` 结构 | — |
| `tab:supp` repair | `repair_*_poison_v2.json` | `run_repair_ablation.sh` |
| Holdout 脚注 h | `holdout_banking_*.json` | `run_holdout_paired.sh` |
| Native gen § | `native_gen_10task_tool_knowledge.json` | `run_native_generalization.sh` |

---

## 5. 自动核对命令

```bash
./util_scripts/sync_paper_metrics.sh
uv run python util_scripts/verify_paper_metrics.py
```

提交前完整审计清单：[submission_consistency_audit.md](./submission_consistency_audit.md)

---

## 6. 已知未闭环项（诚实保留）

| 项 | 状态 |
|----|------|
| Cross-model signature | Scope-out；Limitations 写 follow-up |
| Human confirmer | LLM proxy only |
| Bootstrap CI（主表） | External 脚注有 Wilson；主表仍为 mean±std |
| Registry unknown tool | 默认 `conservative_confirm`（2026-09 closeout）；benchmark 均在 registry 内 |
