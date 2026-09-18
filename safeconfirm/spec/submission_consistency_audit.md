# Submission consistency + claim–evidence audit

**Date:** 2026-09-18  
**Paper:** `6a9fb8173b16b4dea4fd1079/safeconfirm.tex`  
**Numbers:** `6a9fb8173b16b4dea4fd1079/paper_metrics/canonical/`  
**Automated check:** `uv run python util_scripts/verify_paper_metrics.py` → **40/40 OK** (this run)

---

## 1. Executive summary

| Area | Verdict | Notes |
|------|---------|--------|
| Table 1 / Table 2 numerics | **PASS** | All rows traced to canonical JSON |
| Appendix `tab:supp` | **PASS** | Repair + prompt-defense match JSON |
| Footnotes vs body | **FIXED** | Footnote `h` had no table marker (see §4) |
| Stale claims (learned/retrieval/fail-open ALLOW) | **PASS** | Removed in closeout; Limitations updated |
| Claim–evidence mapping | **PASS** | Every main claim has table/figure/appendix |
| Wording (human vs channel) | **MINOR FIX** | Abstract/Intro softened (§4) |
| Internal spec drift | **FIXED** | `paper_experiment_consistency.md` §6, `claim_evidence_audit.md` |

**Submit gate:** Re-run `verify_paper_metrics.py` after any number change; re-read §3 claim table before camera-ready.

---

## 2. Claim → evidence matrix

| # | Claim (where) | Evidence | Overclaim risk | Status |
|---|---------------|----------|----------------|--------|
| C1 | Confirmation laundering exists (Abstract, RQ1) | Table 1 RQ1; Fig. 2; compliant row CLR 66.7% | Implies human users | ☑ LLM confirmer + channel wording |
| C2 | Same ASR, different authorization quality (SDR/CLR) | SA vs vague 0% ASR, 100% vs 0% SDR | All agents / all suites | ☑ 12-case diagnostic |
| C3 | Recovery hierarchy beats contract-style block/vague (RQ2) | rule_v1 75% TSR vs block 22.2% / vague 25% | Beats PACT numerically | ☑ abstraction language in Setup |
| C4 | SafeConfirm reduces ASR vs P0 (RQ3) | Workspace 38.3→0%; banking 40→0%; external 61.9→9.5% | Field ASR; SC external ≠ 0 | ☑ qualitative + raw counts |
| C5 | Workspace utility can improve | 27.3→39.4% TSR | Banking utility | ☑ no banking TSR claim |
| C6 | External lineage without retuning | Table 2; 13/21→2/21 | Independent-case CI | ☑ Wilson = descriptive only |
| C7 | Repair helps TSR (RQ4) | Appendix 25→50%, ASR 0 | Always wins | ☑ appendix only |
| C8 | Prompt defenses mixed | Related: spotlight stall 90%; appendix TSR 25% | “90% TSR” | ☑ stall_rate not TSR |
| C9 | Native tool_knowledge not fixed | §discussion-native 9.1% security both | SC replaces prompt defense | ☑ stated |
| C10 | Unknown tools not silent allow | Method conservative fallback | Old fail-open text | ☑ code + Limitations |
| C11 | Cross-model robustness | — | Multi-model SOTA | ☑ out of scope / Limitations |
| C12 | Human comprehension | — | User study | ☑ simulated confirmer only |

---

## 3. Table / footnote / appendix cross-check

### Table 1 (`tab:results`)

| Block | Rows | JSON source | Footnotes |
|-------|------|-------------|-----------|
| RQ1 | SA, vague, compliant | `confirm_*_poison_v2.json`, `confirm_vague_compliant_llm.json` | `c` = 8.9% approval (`confirm_approval_rate_mean`) ☑ |
| RQ2 | rule_v1, block, vague, allow | `provenance_*_aggregate.json`, `component_12case` allow | SDR/CLR `---` documented as n/a ☑ |
| RQ3 | ws/bk P0 vs SC | `extended28_*`, `banking_paired_p0_aggregate` for **5.6%** TSR | Banking TSR ≠ extended28 banking TSR 0% — **explained in consistency doc** ☑ |

### Table 2 (`tab:external`)

| Field | Paper | JSON |
|-------|-------|------|
| P0 ASR | 61.9 ± 6.7 | `external_p0_aggregate.json` |
| SC ASR | 9.5 ± 6.7 | `external_sc_aggregate.json` |
| SC TSR | 20.8 ± 5.9 | same |
| Pooled | 13/21 vs 2/21 | 7 corruption × 3 seeds |

### Appendix

| Label | Content vs JSON | Cross-table |
|-------|-----------------|-------------|
| `tab:coverage` | 28 cases / tools list | Matches `benchmark_cases_e2e.yaml` |
| `tab:supp` repair | 50 / 25 | `repair_full_on/off_poison_v2.json` |
| `tab:supp` spotlight / repeat | 25/0, 25/50 | `defense_sweep_12case_poison_v2.json` |
| Footnote `h` | holdout banking P0 ASR 50% | `holdout_banking_p0.json` — **marker added on banking P0 row** |

---

## 4. Issues found and fixes (this audit)

| ID | Issue | Severity | Action |
|----|--------|----------|--------|
| A1 | Footnote `h` in tablenotes but no `\tnote{h}` in table body; Limitations cites “footnote h” | Medium | Add marker on Banking (6)/P0 row |
| A2 | Abstract/Intro “user may approve” vs no human study | Low | Rephrase to confirmation-channel |
| A3 | `paper_experiment_consistency.md` §6 still said registry ALLOW | Doc | Updated to conservative_confirm |
| A4 | `claim_evidence_audit.md` stale (fail-open, repair ☐) | Doc | Refreshed v0.3 |
| A5 | Appendix `v0.5.0` version label | Low | Removed (align with main table style) |

**Not issues:** Related work “90% stall” = `stall_rate` 0.9 in defense sweep, not TSR 90%. Provenance 75% vs old component 66.7% — different batches; not cited together in tex.

---

## 5. Stale-language grep (tex)

| Pattern | Result |
|---------|--------|
| learned policy / retrieval-learned | **None** in `safeconfirm.tex` |
| fail-open / ALLOW without analysis | **None** (Limitations updated) |
| Appendix Table 4 / 58.3 rule_v1 | **None** |
| repo paths / `runs/` | **None** in body |

---

## 6. Pre-submission checklist

- [x] `uv run python util_scripts/verify_paper_metrics.py`
- [x] Claim table §2 reviewed
- [x] Footnote `h` wired
- [ ] Overleaf PDF manual skim (figures, table alignment)
- [ ] `\acmSubmissionID{XXX}` → real ID before upload
- [ ] Optional: cross-model (scope-out — do not add claim)

---

## 7. Related docs

- [claim_evidence_audit.md](./claim_evidence_audit.md) — short claim index  
- [paper_experiment_consistency.md](./paper_experiment_consistency.md) — row-level JSON map  
- [reviewer_closeout_plan_1_5.md](./reviewer_closeout_plan_1_5.md) — Steps 1–5 done
