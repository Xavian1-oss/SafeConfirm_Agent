# Claim–Evidence Audit (E-P1-6)

**Version:** 0.3.0 · 2026-09-18 (submission pass)  
**Full audit:** [submission_consistency_audit.md](./submission_consistency_audit.md)  
**Numbers:** [paper_experiment_consistency.md](./paper_experiment_consistency.md) · `uv run python util_scripts/verify_paper_metrics.py`

| Claim (paper) | Evidence | Risk if over-written | Status |
|---------------|----------|----------------------|--------|
| Confirmation laundering under generic confirm | Table 1 RQ1; Fig. 2; CLR 66.7% compliant row | Human-subject study | ☑ channel + LLM confirmer |
| Equal ASR, different authorization quality | Same ASR, SDR 100% vs 0% (vague vs SA) | All agents / all suites | ☑ 12-case diagnostic |
| Hierarchy vs contract-style block/vague | Table 1 RQ2 (75 vs 22.2/25 TSR) | Beat PACT numerically | ☑ abstraction wording |
| SafeConfirm reduces ASR vs P0 | RQ3 workspace/banking + Table 2 external | Field ASR; small lineage set | ☑ qualitative + 13/33 vs 0/33 |
| Workspace utility can improve | 27.3→39.4% TSR | Banking utility | ☑ no banking TSR claim |
| External lineage without retuning | Table 2, 8 cases, 3 seeds | Wilson as population CI | ☑ descriptive CI footnote |
| Repair helps utility | Appendix 50 vs 25% TSR | Repair always wins | ☑ RQ4 appendix only |
| Registry / unknown tools | conservative_confirm in code; benchmarks in registry | Silent allow | ☑ Method + Limitations |
| Cross-model robustness | — | “All LLM agents” | — scope-out |
| Native tool_knowledge | native_gen JSON; §discussion-native | SC fixes hijacking | ☑ 9.1% both arms |

## Abstract / Conclusion checklist

- [x] No banking utility claim
- [x] External: “lineage subset” / pattern, not SC ASR = 0 globally
- [x] Generic confirmation / confirmation channel (not human subjects)
- [x] No multi-model claim
- [x] Authorization invariant = design goal, not theorem

## Metric honesty (E-P1-1)

- SDR/CLR **n/a** when denominator zero (table caption + Setup operational rules)
- CLR: approved in \(\mathcal{R}_{\mathrm{conf}}\) with **gap remaining at approval** (code: `laundering_risk_at_approval`)
