# SafeConfirm — 复现入口

**地图:** [spec/README.md](./README.md) · **一致性:** [paper_experiment_consistency.md](./paper_experiment_consistency.md)

## 一键复现（主表 + Table 2 + 附录）

```bash
./util_scripts/run_extended_28case.sh           # Table 1 RQ3 E2E
./util_scripts/run_confirm_ablation.sh          # Table 1 RQ1
./util_scripts/run_provenance_baselines.sh      # Table 1 RQ2
./util_scripts/run_external_eval.sh             # Table 2（12 external cases）
./util_scripts/run_holdout_paired.sh            # Banking footnote h
./util_scripts/run_provenance_sensitivity.sh    # Appendix tab:prov-flip
./util_scripts/sync_paper_metrics.sh
uv run python util_scripts/verify_paper_metrics.py
```

诊断（非主表）：`./util_scripts/run_banking_benign_check.sh`

## 主结果摘要（与 canonical JSON / tex 一致）

| 块 | 要点 |
|----|------|
| Confirm 12-case | 0% ASR；SDR 100% vs 0%；compliant CLR 66.7% |
| Provenance 12-case | block/vague ~22–25% TSR vs rule_v1 **75%** @ 0% ASR |
| E2E 28 ws | SC **39.4/0%** vs P0 **27.3/38.3%** TSR/ASR |
| E2E banking | SC **0/0%**；P0 paired TSR **5.6%**，ASR **40%** |
| External 12 | P0 ASR **39.4%** → SC **0%**；pooled **13/33 vs 0/33** |

**Out of scope:** human study、cross-model 主表、banking utility claim、field ASR。
