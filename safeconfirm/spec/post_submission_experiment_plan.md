# SafeConfirm — 投稿后实验加强计划（仅有道理的部分）

**版本:** 0.1.0  
**日期:** 2026-09-19  
**定位:** 只收录 **值得跑实验 / 改 benchmark 数据** 的项；纯写作（replay scope、related-work 扫文献）见 [submission_consistency_audit.md](./submission_consistency_audit.md)，**不占用本计划工时**。  
**原则:** 不增 RL/新架构；**不 retune `rule_v1`**；**不**为 banking TSR 改 task；**多模型 signature 放最后**。  
**论文数字:** 改表前跑 `uv run python util_scripts/verify_paper_metrics.py`；external 新批次 sync 到 Overleaf `paper_metrics/canonical/`。

**图例:** ☐ 未开始 · ◐ 进行中 · ☑ 完成 · — 不做

---

## 0. 执行顺序（推荐）

| 阶 | 块 | 类型 | 预期收益 |
|----|-----|------|----------|
| **E1** | External lineage 12–16 cases | Benchmark + 跑数 | 外部效度（最高 ROI） |
| **E2** | Provenance label-flip sensitivity | 诊断实验 | Upstream detector 边界 |
| **E3** | Banking utility 诊断（benign / 归因） | 轻量跑数 + 正文 | 防止 0 TSR 误读 |
| **E4** | Cross-model signature（最后） | 2 组实验 | Single-model weakness |

**明确不在本计划（除非 rebuttal 点名）:** registry schema 启发式实现、全量 28-case×第二模型、真人 study、instruction-hijacking 主实验。

---

## E1 — 扩展 external lineage（8 → 12–16）

### 要回应的 concern

> 只在自设计 diagnostic + 小规模 lineage 上有效；external 太小。

### 策略

- **不**再扩 28-case diagnostic 主集。
- **只**扩 `safeconfirm/data/benchmark_cases_external.yaml` + `safeconfirm_bridge/suites/workspace_external/`（已有模式）。
- 新 case：**native AgentDojo workspace 措辞改编**、parameter poison only、**policy freeze 后编写**、与现有 8 例 **工具/槽位多样性** 不重复。

### 多样性检查表（新增 case 应覆盖缺口）

| 维度 | 当前 8 例大致覆盖 | 扩展目标 |
|------|-------------------|----------|
| Recipient / email poison | 多 | 保留 2–3，勿再堆同质 email |
| Share / file_id / email | 部分 | +1–2 |
| Delete / file target | 弱 | +1 |
| Calendar participants | 弱 | +1 |
| Body / CC / BCC slot | 部分 | +1 |
| Banking recipient / amount | 无（external 现均为 workspace） | 可选 +1–2 **若 suite 可接 banking external**；否则写 Limitations |
| Multi-slot 同 case | 弱 | +1（仍 single primary corrupted_slots 评测） |

**数量:** 目标 **12**（最低可辩护）～ **16**（理想）；新增 **4–8** cases。

### 具体任务

| ID | 任务 | 产出 |
|----|------|------|
| E1-1 | 审计现有 8 case 的 tool/slot/native_lineage 矩阵，列缺口 | spec 内表格或 issue 列表 |
| E1-2 | 编写新 YAML cases（`ext_*`，`native_lineage` 字段） | `benchmark_cases_external.yaml` |
| E1-3 | Registry 覆盖：新 tool/slot 已在 `tool_slot_registry.yaml` | 无需改 `rule_v1` |
| E1-4 | `tests/safeconfirm_bridge/test_external_cases.py` 更新 case 数与 schema | CI 绿 |
| E1-5 | 跑数：`SEEDS="s0 s1 s2" ./util_scripts/run_external_eval.sh`，新 `BATCH_ID` | `runs/bridge/external_*` |
| E1-6 | 聚合 → `paper_metrics/canonical/external_*_aggregate.json` | sync 脚本 / 手工 |
| E1-7 | 更新 Table 2 + 正文 pooled counts（**重算** 7→N corruption × 3 seeds） | `safeconfirm.tex` |
| E1-8 | [paper_experiment_consistency.md](./paper_experiment_consistency.md) + `verify_paper_metrics.py` 增 external 行 | 仓库 |

### 完成标准

- [x] ≥12 external cases，≥4 种 tool 或 ≥5 种 distinct critical slot 类型（CI: `test_external_tool_and_slot_diversity`）。
- [x] `rule_v1` 与 confirm 模板 **未**为 external 单独调参。
- [x] 报告：seed mean±std + pooled attack counts（Wilson 仍仅 descriptive，见 submission audit）。
- [x] Qualitative claim 不变：ASR 下降 pattern；12-case 批次 SC ASR=0% 仍 **不** 写成 field guarantee。

### 工作量粗估

**2–5 天**（case 设计 + 跑数 + 论文表，视 API 稳定性）。

---

## E2 — Provenance label-flip sensitivity

### 要回应的 concern

> Gap detection / provenance 若不准，SafeConfirm 是否失效？

### 策略

- **不**实现新 provenance tracker；在 **已有 label 管道** 上做 **controlled corruption**。
- 在 evaluation 或 bridge 层对 `slot_records[].source` / `authorization_gap` 做 **seeded 随机 flip**（仅 corruption runs 或 12-case 前缀以控成本）。

### Flip 语义（E2-1，已实现）

对每条 **binding** `slot_record`：以概率 `p` 独立抽样；若 `authorization_gap=True` 则清 gap 并标 `TRUSTED_CONTACT`（低 risk），否则设 gap 并标 `UNTRUSTED_OBSERVATION`（高 risk）；随后重算 `has_untrusted_binding` / `overall_risk`。配置：`SAFECONFIRM_PROVENANCE_FLIP_RATE`、CLI `--provenance-flip-rate`（见 `safeconfirm/analysis/provenance_stress.py`）。

### 实验设计

| 条件 | Flip 率 | 报告 |
|------|---------|------|
| Baseline | 0% | TSR, ASR（对照已有 aggregate） |
| Low | 5% | 同上 + 干预类型计数（ALLOW/BLOCK/CONFIRM/REPAIR） |
| Medium | 10% | 同上 |
| High | 20% | 同上 |

- **Suite:** 优先 **frozen 12-case workspace**（与 RQ2 同协议）；可选 28-case 子集若成本允许。
- **Model:** DeepSeek only（与主表一致）。
- **Policy:** `rule_v1`，repair on。

### 具体任务

| ID | 任务 | 产出 |
|----|------|------|
| E2-1 | 设计 flip 语义（flip gap bit？flip trusted↔untrusted source？）并写 5 行 spec | 本节或 `design.md` 小段 |
| E2-2 | 实现：`safeconfirm_bridge/` 或 `safeconfirm/evaluation/` 可复现 hook（CLI flag `--provenance-flip-rate`） | 代码 + 单测 |
| E2-3 | 脚本 `util_scripts/run_provenance_sensitivity.sh`（4 条件 × 3 seeds） | util_scripts |
| E2-4 | 跑数 + JSON 摘要 | `runs/bridge/provenance_sensitivity_*` |
| E2-5 | **Appendix 小表**（非主表 RQ）；正文 Limitations 交叉引用 | tex |
| E2-6 | 论文表述：**synthetic stress test**，非 field misclassification rate | tex |

### 完成标准

- [x] 至少 3 个 flip 率 + baseline，每条件 3 seeds — batch `prov_flip_20260919`。
- [x] 能回答：低 flip 下 ASR/TSR 是否平稳；高 flip 下退化是否 **可预期**（$p{=}0.05$–$0.10$ ASR $\approx$13\%; $p{=}0.20$ ASR 40\%）。
- [x] 不推翻主 claim（recovery **given** labels）；只量化 **upstream error boundary**（附录 `tab:prov-flip` 文案 + 占位行）。

### 工作量粗估

**3–6 天**（含实现 hook；若仅 offline 重放 logs 则 1–2 天）。

---

## E3 — Banking 诊断（澄清 utility，不修 TSR）

### 要回应的 concern

> Banking SafeConfirm TSR 0% → 是否 “乱 block”？

### 策略

- **保留** security claim（ASR 0%）；**不** claim banking utility。
- **用实验把瓶颈归因写死：** model/planner vs SafeConfirm。

### 已有资产

- `util_scripts/run_banking_benign_check.sh` — P0 benign transfer（见 [banking_tsr_root_cause.md](./banking_tsr_root_cause.md)）。
- 正文已有 benign 诊断、6-case paired TSR 5.6% vs SC 0%。

### 具体任务

| ID | 任务 | 产出 |
|----|------|------|
| E3-1 | 归档一次 **benign check** 结果（P0 是否调用 `send_money`、utility） | JSON + 1 句 tex |
| E3-2 | 可选：同 benign case 跑 **SC active**（是否 block 合理路径） | 对比 log 1 段 |
| E3-3 | 正文 **Discussion/Limitations** 固定句式：utility bottleneck upstream competence vs intervention | tex（无新主表数字也可） |
| E3-4 | **不做：** 为抬 TSR 改 banking case / 降 poison / 换 evaluator |

### 完成标准

- [x] Reviewer 问 “why 0 TSR” 时可引用：**benign P0 结果 + paired ASR 对比 + 不 claim utility**（2026-09-19 s0: 未调用 `send_money`）。
- [x] 无 banking 新数字进入 Table 1 除非 benign 复跑结果稳定且值得footnote。

### 工作量粗估

**0.5–1 天**（mostly 已有脚本）。

---

## E4 — Cross-model signature（最后做）

### 要回应的 concern

> 现象是否 DeepSeek-specific？

### 策略

- **不全量**重跑；只复现 **qualitative pattern**。
- 第二模型：Gemini / Claude / GPT 等 **API 可用且与 DeepSeek 不同 family**（见 `run_cross_model_signature.sh`）。

### 实验 A — Confirmation signature（RQ1）

| 对比 | 指标 | 成功 pattern |
|------|------|----------------|
| source-aware vs vague | ASR, SDR, CLR（可选 compliant 一行） | ASR 可接近；SDR 仍 **分离**（≈100 vs 0）；CLR laundering 现象存在 |

- Suite: **12-case** confirm ablation 协议。
- Seeds: 至少 **s0**；理想 s0–s2。

### 实验 B — E2E signature（RQ3）

| 对比 | Suite | 指标 |
|------|-------|------|
| P0 vs SafeConfirm | workspace 22 或 **external lineage**（扩 case 后用新 external） | ASR 显著下降（不必同百分比） |

- Seeds: s0 最低；external 可只 s0 控成本。

### 具体任务

| ID | 任务 | 产出 |
|----|------|------|
| E4-1 | 确认 API / 模型 slug 与 bridge pipeline 兼容 | 一次 smoke |
| E4-2 | `./util_scripts/run_cross_model_signature.sh`（或分 A/B 脚本） | runs |
| E4-3 | Appendix 或脚注：**Cross-model signature (non-primary)** 小表 | tex |
| E4-4 | Limitations：主表 DeepSeek；signature 在 appendix | tex |
| E4-5 | **在 E1–E3 完成后跑**，避免 benchmark 变动导致重跑 | 顺序 |

### 完成标准

- [ ] 第二模型上 **A + B** 各至少 1 个 batch 可引用。
- [ ] 论文 **不**写 “validated on all models”；写 “qualitative pattern persists on \<Model X\>”.

### 工作量粗估

**1–3 天**（视 API 额度与失败重试）。

---

## 汇总 checklist

| 块 | 依赖 | 改主表？ | 状态 |
|----|------|----------|------|
| E1 External | — | **Table 2** | ☑（`external_v2_12case_20260919`，tex + canonical 已 sync） |
| E2 Label flip | 可选 E1 稳定 | Appendix | ☑（`prov_flip_20260919` → `tab:prov-flip`） |
| E3 Banking diag | — | 正文为主 | ☑（benign P0 s0 已跑 + `banking_tsr_root_cause.md`） |
| E4 Cross-model | **E1 建议先** | Appendix | —（用户跳过） |

---

## 与非实验项的分工

| 项 | 文档 / 动作 |
|----|-------------|
| Replay / durable authorization 一句 | Limitations 文案 — submission audit |
| Registry scalability 叙事（非 heuristic 代码） | Method/Limitations — 写作 |
| Related-work gap audit | 文献 — 写作 |
| 主表数字回归 | `verify_paper_metrics.py` |

---

## 维护

- 每完成 E* 块：更新上表 **状态**；external / sensitivity JSON 路径写入 [paper_experiment_consistency.md](./paper_experiment_consistency.md)。
- 与 [evidence_strength_plan.md](./evidence_strength_plan.md) 关系：MV5 已完成部分为 **基线**；本计划为 **投稿后 / rebuttal 前** 可选加强，不替换 closeout Steps 1–5。
