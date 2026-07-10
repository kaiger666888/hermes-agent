# Roadmap: Hermes Agent — Kai's Personal Agent Platform

## Milestones

| Version | Name | Phases | Shipped | Tag | Audit |
|---------|------|--------|---------|-----|-------|
| v1 | Movie-Experts Suite v2 | 0-6 | 2026-06-15 | `v1` | passed (deferred live run) |
| v2.0 | PRFP Pipeline Design (design-only) | 7-12 | 2026-06-16 | `v2.0-prfp-design` | design-only |
| v3.0 | Skills-to-DAG Alignment | 13-18 | 2026-06-17 | `v3.0` | tech_debt |
| v4.0 | Methodology Backfill | 19-21 | 2026-06-18 | `v4.0` | passed |
| v5.0 | kais-movie-agent V8.6 Adaptation | 22-27 | 2026-06-19 | `v5.0` | passed |
| v6.0 | Self-Evolution Feedback Loop | 28-33 | 2026-06-24 | `v6.0` | passed |
| v7.0 | openclaw → hermes Migration | 34-37 | 2026-06-25 | `v7.0` | passed |
| v9.0 | kais-movie-pipeline 闭环深化 | 38-43 | 2026-06-27 | `v9.0` | passed |
| v10.0 | 编排架构第一性原理推导(设计型) | 44-51 | 2026-07-07 | `v10.0` | passed (zero code) |
| v11.0 | Hermes-Native Expert Agents PoC | 52-56 | 2026-07-07 | `v11.0` | passed |
| v12.0 | Production Hardening | 57-61 | 2026-07-08 | `v12.0` | passed |
| v13.0 | v10.0 Design Suite Full Rollout & Live Eval | 62-69 | 2026-07-08 | `v13.0` | tech_debt |
| v14.0 | kais-movie-pipeline 4-Track Upgrade (FORM / DUB / IMG / TRANSITION) | 70-76 | 2026-07-10 | `v14.0` | tech_debt (24 satisfied + 2 operator-handoff) |
| v15.0 | Operator-Action Closure Tooling | 77-83 | 2026-07-10 | `v15.0` | tech_debt |

See [MILESTONES.md](./MILESTONES.md) for full milestone history with key accomplishments per milestone, and `milestones/v{N}.0-ROADMAP.md` for archived phase artifacts.

---

## Milestone v15.0 — Operator-Action Closure Tooling (SHIPPED 2026-07-10, tag `v15.0`, verdict `tech_debt`) — [Archive](milestones/v15.0-ROADMAP.md)

**Stats:** 7 phases (77-83) · 13 plans · 15/15 reqs structurally satisfied · 6 operator-action handoffs preserved (closure tooling delivered, operator-action pending — v16+ runtime) · Cross-repo final pins: hermes-agent `48cb57d7`, kais-hermes-skills `009773f`.

**One sentence:** 把 v14.0 留的 6 项 operator-action handoffs 工具化,让每个 handoff 变成 5-minute operator task 而非 research project (DUB-05 benchmark runner + VERSION.json lock / TRANS-07 LTX-FLF validation runner + verdict update / IMG-09 vision-verify calibration + per-stratum threshold apply / DUB-03 voice sample protocol + batch validator / XCUT-04b cloud engine bootstrap doc + opt-in / XCUT-04c GLM-4.6V cost instrumentation + CLI + XCUT-05 automated lineage bump)。

See `milestones/v15.0-ROADMAP.md` for the full phase archive, `milestones/v15.0-REQUIREMENTS.md` for requirement outcomes, and `milestones/v15.0-MILESTONE-AUDIT.md` for the audit report (10 sections, verdict tech_debt).

---

## Backlog

Candidate directions for v16+ (not yet committed — pending milestone planning):

- **TRANS-11 production rollout** (gated by TRANS-07 v15.0 validation verdict): LTX-2.3 FLF + ICLoRA combined workflow — if validation passes, v16+ rolls it into production transition routing.
- **DUB-05-AUTO-LOCK**: full automation of VERSION.json lock based on benchmark scores (v15.0 deferred — operator-in-loop required for audio quality judgment).
- **IMG-09-AUTO-TUNE**: closed-loop auto-threshold adjustment based on rolling production data (v15.0 deferred — operator review still required for threshold changes).
- **v15-LIVE-EVAL**: v13.0 Phase 64 live-eval secrets integration (operator-secret-dependent).
- **feishu-* skills migration** (v7.0 carryforward): largest v7.0 deferred item, not yet planned.
- **FORM-06 / FORM-07 / DUB-06 / DUB-07 / IMG-07 / IMG-08 / TRANS-08 / TRANS-09 / TRANS-10** (v14.0 Future Requirements, all explicitly acknowledged as deferred).

---

*Last updated: 2026-07-10 — **v15.0 SHIPPED** (tag v15.0, verdict tech_debt). Phase 83 VALIDATE complete. 13/13 plans done (100%). All 15 reqs structurally satisfied. 6 operator-action handoffs preserved (closure tooling delivered, operator-action pending — v16+ runtime). Ready for v16.0 milestone planning. Run `/gsd:new-milestone` to start.*
