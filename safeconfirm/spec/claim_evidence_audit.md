# Claim–Evidence Audit (E-P1-6)

**Version:** 0.2.0 · 2026-09-16  
**Use:** Align Abstract / Intro / Conclusion with available evidence before submission.  
**Numbers:** [paper_experiment_consistency.md](./paper_experiment_consistency.md)

| Claim (paper) | Evidence | Risk if over-written | Status |
|---------------|----------|----------------------|--------|
| Confirmation laundering occurs under generic confirm | Table 1 confirm rows; Fig. 2 (CLR/SDR) | Implies human-subject study | ☑ diagnostic suite |
| Equal ASR can hide different authorization quality | Same ASR, different SDR/CLR (vague vs source-aware) | “All agents / all suites” | ☑ workspace confirm ablation |
| SafeConfirm reduces ASR vs P0 | 28-case paired P0 vs SC (`run_extended_28case.sh`) | Field deployment ASR | ☑ bridge E2E |
| SafeConfirm preserves utility | Workspace TSR / intervention table | **Banking utility** | ◐ banking TSR ~0 — narrow claim |
| Beyond handcrafted diagnostic cases | `evidence_20260916_1531` external aggregates (3 seeds) | Statistical generalization | ☑ report as lineage subset |
| Distinct from provenance-only block/vague | `evidence_20260916_1531/provenance_baselines/*_aggregate.json` | Beat PACT numerically | ☑ 12-case block/vague/rule_v1 |
| Cross-model robustness | — | “All LLM agents” | — **略过**；勿写 multi-model SOTA |
| Registry fail-open honesty | `benchmark_registry_coverage.yaml` + spec E-P2-3 | Perfect coverage | ◐ document gaps |
| Repair helps utility | Repair on/off appendix | Repair always wins | ☐ appendix only |

## Abstract / Conclusion edits (checklist)

- [ ] Remove or soften “banking utility” unless benign + corruption TSR improve after H-D fixes.
- [ ] Say **define / characterize** authorization invariant (E-P1-2), not heavy “formalize”.
- [ ] External block: “AgentDojo-lineage **external** subset” not “AgentDojo benchmark SOTA”.
- [x] Cross-model：**不写**第二模型；Limitations 注明 DeepSeek-only + follow-up priority。
- [x] Generic confirmation（非 human subjects）；registry **fail-open** 表述。

## Metric honesty (E-P1-1)

- SDR/CLR report **N/A** when denominator is zero (code + table footnote).
- CLR denominator: approved confirmations with **binding authorization gap** only.
