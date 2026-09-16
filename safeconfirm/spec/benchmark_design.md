# SafeConfirm E2E Benchmark — Design Matrix (Goal E)

**Version:** 0.1.0  
**Cases:** 28 (`benchmark_cases_e2e.yaml`, v0.5.0-extend-v1; dev 20 + extension 4 + holdout 4)  
**Purpose:** Principled **diagnostic** suite for parameter-poison + confirmation-quality evaluation — not broad security coverage.

## Coverage dimensions

| Dimension | Values used in v0.4.2 |
|-----------|------------------------|
| **Tool** | `send_email`, `share_file`, `delete_file`, `create_calendar_event`, `append_to_file`, `send_money` |
| **Critical slot** | `recipients`, `bcc`, `email`, `file_id`, `participants`, `recipient` |
| **Poison channel** | poison email, poison notes / invoice, calendar body |
| **Binding type** | direct address, role reference (supervisor/manager), ID reference, multi-hop read→send |
| **Expected intervention** | REPAIR, SOURCE_AWARE_CONFIRM, ALLOW (registry) |
| **Steps** | single-step (18), two-step (2: `ws_read_then_send`, `ws_forward_thread`) |

## Suite composition

| Suite | Corruption | Benign | Total |
|-------|------------|--------|-------|
| Workspace | 20 | 2 | 22 |
| Banking | 5 | 1 | 6 |
| **Total** | **25** | **3** | **28** |

**Holdout (post `policy-freeze-v1`):** 4 corruption cases — `ws_holdout_share_decoy_e2e`, `ws_holdout_contract_append_e2e`, `bk_holdout_amount_e2e`, `bk_holdout_iban_e2e`.

**12-case ablation subset:** `user_task_0`–`user_task_11` (frozen prefix for confirm/component/defense ablations; primary E2E uses all 28 cases).

## Primary experiment commands

| Purpose | Script |
|---------|--------|
| Main E2E (28-case paired P0 vs SC) | `./util_scripts/run_extended_28case.sh` |
| Holdout (4 cases, post policy-freeze) | `./util_scripts/run_holdout_paired.sh` |
| Mechanism ablations (12-case) | `./util_scripts/run_confirm_ablation.sh`, `run_component_ablation.sh`, etc. |
| Per-case analysis (16-case paired) | `SUBSET=16 ./util_scripts/run_paired_security_rerun.sh` |

## Pattern mix (corruption only)

| Pattern family | Count | Cases |
|----------------|-------|-------|
| Email recipient poison | 6 | supervisor, manager, advisor, calendar, booking, thread |
| Share recipient poison | 2 | supervisor, client |
| File ID poison | 2 | delete backup, delete export |
| BCC / forward poison | 1 | forward_thread |
| Calendar participants | 1 | event_guest |
| Append file_id | 1 | move_file |
| Two-step email | 1 | read_then_send |
| Banking recipient | 3 | invoice, registration, rent |

Email-style recipient poisoning remains the largest family; v0.4.2 adds BCC, calendar, append, and two-step bindings to reduce single-pattern dominance.

## Holdout protocol (Goal E3)

1. Tag current 20 cases as **dev** (`policy-freeze-v1` in paper).
2. Author **4–8 holdout** cases after freezing `rule_v1` + disclosure templates.
3. Report holdout paired P0 vs SC **once** — no policy tuning on holdout labels.

## Extension targets (E2, optional)

Target **28–32 cases** by filling matrix gaps:

- Non-recipient email slots (attachments)
- URL / link authority-bearing bindings
- Banking amount slot
- Native AgentDojo task adaptations (≥30% of new cases)

See [goal_e_reposition_benchmark_plan.md](./goal_e_reposition_benchmark_plan.md) §5.2.
