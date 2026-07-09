# v14.0 Lineage Impact Inventory — Phase 70 Baseline

**Captured:** 2026-07-09 (before any v14.0 SKILL.md edit)
**Algorithm:** SHA-256 of LF-normalized UTF-8 working-tree bytes (canonical per `scripts/transform_skill_to_agent.py:232-240`).
**Cross-repo pins:**
- `hermes-agent` HEAD = `8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1`
- `kais-hermes-skills` HEAD = `d9620369e48eec51c31ee72ac8827c288eaccf71` (remote `https://github.com/kaiger666888/kais-hermes-skills.git`)

> **Working-tree vs committed-blob (Pitfall 5):** the `sha256` column hashes the on-disk working-tree bytes of each `SKILL.md` at `/data/workspace/kais-hermes-skills/...`, NOT the git-committed blob. Phase 71–74 will edit working-tree bytes, so this baseline must match what those phases touch. The cross-repo commit pins above anchor "which commit was checked out when Phase 70 ran" for Phase 76's coordination check, but the lineage hash itself is against working-tree bytes. kais-hermes-skills has uncommitted changes at HEAD `d9620369...` (operator pre-v14.0 work in pipeline scripts, NOT in the 6 target SKILL.md files — see Assumption A4 in `70-RESEARCH.md`).

## Canonical field-name note (Pitfall 1)

The roadmap/REQUIREMENTS prose uses shorthand `source_sha` / `transform_rule_id` / `transform_timestamp`. The actual agent YAML schema (verified against 5 live `~/.hermes/agents/*.agent.yaml` files on 2026-07-09, plus `scripts/transform_skill_to_agent.py:191-197`) uses the canonical names below. This inventory uses canonical names everywhere; Phase 75 LINEAGE-BUMP + Phase 76 VALIDATE assertions MUST do the same or they will grep for nonexistent fields and silently pass on empty sets.

| Roadmap shorthand | Canonical field (use this) |
|-------------------|----------------------------|
| `source_sha` | `lineage.skill_sha256` |
| `transform_rule_id` | `lineage.transform_notes` (free text, carries `Rule IDs:` substring) |
| `transform_timestamp` | `lineage.transform_date` (ISO date, not full timestamp) |

## SKILL.md baseline (6 files)

| skill_id | SKILL.md path | sha256 (LF-norm UTF-8) | bytes | agent.yaml exists? | agent.yaml `lineage.skill_sha256` | agent.yaml `lineage.transform_date` | lineage_match |
|----------|---------------|------------------------|-------|--------------------|-----------------------------------|------------------------------------|---------------|
| cinematographer | `skills/movie-experts/cinematographer/SKILL.md` | `ebe9d3fa8e6b4987d6db2cb6a96bdd407ed526bfe8ce27bb31f8bf41ae5b535b` | 40780 | YES (`cinematographer.agent.yaml`) | `b4bcc9c69163899d2a3d069c54d8a2a6a8d651a4fe76c256a397ec0cdc875244` | 2026-07-07 | **MISMATCH** |
| editor | `skills/movie-experts/editor/SKILL.md` | `bd5bf4a113eb70485d8774f85ee29e663632a18edcc5540cbe6668691d760f77` | 30364 | YES (`editor.agent.yaml`) | `bd5bf4a113eb70485d8774f85ee29e663632a18edcc5540cbe6668691d760f77` | 2026-07-07 | OK |
| audio_pipeline | `skills/movie-experts/audio_pipeline/SKILL.md` | `e047010520e3cc4afea5bb0fe96dc1e0ff7826708ae421339305090ce0aeaa9f` | 72251 | YES (`audio_pipeline.agent.yaml`) | `fe59f7fa9684086ef5116472d38fb56a5c85b8dc2b3f7936e11630708bea3da9` | 2026-07-07 | **MISMATCH** |
| drawer | `skills/movie-experts/drawer/SKILL.md` | `2c21f234380ca3fa1f918f733e3cb967d558cdc23b3cca2aedfcb6337682f1eb` | 654 | NO (DEPRECATED stub; merged into `visual_executor` Phase 14) | n/a | n/a | N/A (skill-only) |
| kais-movie-pipeline | `skills/kais-movie-pipeline/SKILL.md` | `bf8b7f5a48624dea563b8e37e46adb793dba0006090b334583d757ff7879b7ea` | 111743 | NO (skill-only, orchestration skill — not a native expert agent) | n/a | n/a | N/A (skill-only) |
| kais-jimeng-cli | `skills/kais-creative/kais-jimeng-cli/SKILL.md` | `3a9576a66a9567d64074fec278dceae97243f03e2607a902e2a5c4f6b6f4681b` | 17098 | NO (skill-only, tool skill — not a native expert agent) | n/a | n/a | N/A (skill-only) |

**Lineage bump scope reminder (Pitfall 2):** only 3 of the 6 names above have `~/.hermes/agents/*.agent.yaml` files today (`cinematographer`, `editor`, `audio_pipeline`). The roadmap's "6 affected agents" is best read as "6 SKILL.md files" — NOT "6 agent.yaml bumps". Phase 75 LINEAGE-BUMP re-transforms the 3 existing agent.yaml files; the other 3 remain skill-only (per FOUND-08 frozen 15-expert set; `drawer` is DEPRECATED and merged into `visual_executor`, whose agent.yaml is touched separately IF its source SKILL.md is edited in v14.0).

## Pre-existing drift callout (Pitfall 3)

> **Pre-existing drift (captured, NOT fixed in Phase 70):** `cinematographer` and `audio_pipeline` agent.yaml `lineage.skill_sha256` values mismatch their current SKILL.md hashes. The drift was introduced between the v13.0 P62 transform (2026-07-07) and today (2026-07-09) — someone edited the kais-hermes-skills SKILL.md files after P62 without re-running `scripts/transform_skill_to_agent.py`. Phase 70 captures it here as `MISMATCH`; Phase 75 LINEAGE-BUMP closes it as a side effect of re-transforming. **DO NOT re-bump mid-Phase-70** — that would be a SKILL.md/agent.yaml write and would violate the read-only enumeration scope of this phase.

Delta decomposition for Phase 75 (so it can tell v14.0-introduced drift from pre-existing drift):

| skill_id | working-tree sha (this inventory) | agent.yaml `lineage.skill_sha256` | total_drift (Phase 75 closes) | pre-v14.0 portion |
|----------|-----------------------------------|-----------------------------------|-------------------------------|-------------------|
| cinematographer | `ebe9d3fa...` | `b4bcc9c6...` | `ebe9d3fa...` − `b4bcc9c6...` | `ebe9d3fa...` − (v13.0 P62 baseline) = unknown until Phase 75 re-measures; but the `b4bcc9c6... → ebe9d3fa...` delta is PRE-v14.0 (captured here) |
| audio_pipeline | `e0470105...` | `fe59f7fa...` | `e0470105...` − `fe59f7fa...` | `e0470105...` − (v13.0 P62 baseline) = pre-v14.0 drift |
| editor | `bd5bf4a1...` | `bd5bf4a1...` | none | none |

Phase 75's job: capture the `pre_v14_SKILL_sha = sha256(working-tree at Phase 70 pin)` from this inventory, then `post_v14_SKILL_sha = sha256(working-tree after Phase 74)` — the v14.0-introduced drift is the delta between those two; the total drift (what the bump actually closes) is `post_v14_SKILL_sha − agent_yaml.lineage.skill_sha256`.

## Agent.yaml lineage detail (3 files, read from `~/.hermes/agents/`)

Full lineage blocks captured for Phase 75/76 provenance audit. Values are read verbatim from the live YAML files on 2026-07-09.

### `cinematographer.agent.yaml`

| field | value |
|-------|-------|
| `lineage.derived_from_skill_id` | `cinematographer` |
| `lineage.derived_from_repo` | `kais-hermes-skills` |
| `lineage.transform_date` | `2026-07-07` |
| `lineage.skill_sha256` | `b4bcc9c69163899d2a3d069c54d8a2a6a8d651a4fe76c256a397ec0cdc875244` |
| `lineage.transform_notes` | Persona rewritten from SKILL body; visual-DNA role absorbed from legacy scene_builder (Phase 17 absorption per 04-MIGRATION-PATH §2.7). Shot intent + axis + 9:16 vertical framing are the load-bearing anchors. Analysis-only tools (no write) — output is shot-intent JSON consumed by visual_executor. |

### `editor.agent.yaml`

| field | value |
|-------|-------|
| `lineage.derived_from_skill_id` | `editor` |
| `lineage.derived_from_repo` | `kais-hermes-skills` |
| `lineage.transform_date` | `2026-07-07` |
| `lineage.skill_sha256` | `bd5bf4a113eb70485d8774f85ee29e663632a18edcc5540cbe6668691d760f77` |
| `lineage.transform_notes` | Persona rewritten from SKILL body; FxRxT 3D editing matrix + cut_density metric + cut-follows-intent principle surfaced (Phase 49 §2.13). Analysis-only tools — output is an edit decision list (EDL) consumed by the rendering pipeline. |

### `audio_pipeline.agent.yaml`

| field | value |
|-------|-------|
| `lineage.derived_from_skill_id` | `audio_pipeline` |
| `lineage.derived_from_repo` | `kais-hermes-skills` |
| `lineage.transform_date` | `2026-07-07` |
| `lineage.skill_sha256` | `fe59f7fa9684086ef5116472d38fb56a5c85b8dc2b3f7936e11630708bea3da9` |
| `lineage.transform_notes` | Persona rewritten from SKILL body; 6-sub-step atomicity (voicer/lip_sync/composer/foley/mixer/spatial_audio) surfaced (Phase 49 §2.12). Renamed from legacy 'composer' (CONTEXT.md decision #1) — the composer sub-step is now ONE of 6, not the whole expert. Tools whitelist includes dreamina_cli + write_file for actual asset rendering. Chion audio-vision is the theoretical backbone. |

## Trust-boundary notes (threat model T-70-01 / T-70-03)

- This inventory is committed to the `hermes-agent` repo. Any post-Phase-70 tampering with the human-readable table is detectable via `git diff` against this commit, AND via the machine-readable JSON block below — Phase 76 re-hashes from the pinned `kais-hermes-skills` commit `d9620369...` and compares against the JSON block's `sha256` field. Manual table edits that diverge from the JSON block are flagged as tampering.
- The `cross_repo_pins` below are documentation anchors; Phase 76 asserts the `kais-hermes-skills` pin still resolves and that the post-v14.0 commits are descendants of `d9620369...`.

<!-- MACHINE-READABLE BLOCK (Phase 76 parses this — do NOT hand-edit; regenerate via the canonical algorithm at scripts/transform_skill_to_agent.py:232-240). -->
```json
{
  "captured_at": "2026-07-09T06:36:30Z",
  "algorithm": "sha256(LF-normalized UTF-8 working-tree bytes)",
  "algorithm_source": "scripts/transform_skill_to_agent.py:232-240",
  "field_name_canonicalization": {
    "source_sha": "lineage.skill_sha256",
    "transform_rule_id": "lineage.transform_notes",
    "transform_timestamp": "lineage.transform_date"
  },
  "cross_repo_pins": {
    "hermes-agent": "8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1",
    "kais-hermes-skills": "d9620369e48eec51c31ee72ac8827c288eaccf71"
  },
  "skills": [
    {
      "skill_id": "cinematographer",
      "skill_path": "skills/movie-experts/cinematographer/SKILL.md",
      "sha256": "ebe9d3fa8e6b4987d6db2cb6a96bdd407ed526bfe8ce27bb31f8bf41ae5b535b",
      "bytes": 40780,
      "agent_yaml": "cinematographer.agent.yaml",
      "agent_lineage_skill_sha256": "b4bcc9c69163899d2a3d069c54d8a2a6a8d651a4fe76c256a397ec0cdc875244",
      "agent_lineage_transform_date": "2026-07-07",
      "agent_lineage_derived_from_skill_id": "cinematographer",
      "lineage_match": "MISMATCH"
    },
    {
      "skill_id": "editor",
      "skill_path": "skills/movie-experts/editor/SKILL.md",
      "sha256": "bd5bf4a113eb70485d8774f85ee29e663632a18edcc5540cbe6668691d760f77",
      "bytes": 30364,
      "agent_yaml": "editor.agent.yaml",
      "agent_lineage_skill_sha256": "bd5bf4a113eb70485d8774f85ee29e663632a18edcc5540cbe6668691d760f77",
      "agent_lineage_transform_date": "2026-07-07",
      "agent_lineage_derived_from_skill_id": "editor",
      "lineage_match": "OK"
    },
    {
      "skill_id": "audio_pipeline",
      "skill_path": "skills/movie-experts/audio_pipeline/SKILL.md",
      "sha256": "e047010520e3cc4afea5bb0fe96dc1e0ff7826708ae421339305090ce0aeaa9f",
      "bytes": 72251,
      "agent_yaml": "audio_pipeline.agent.yaml",
      "agent_lineage_skill_sha256": "fe59f7fa9684086ef5116472d38fb56a5c85b8dc2b3f7936e11630708bea3da9",
      "agent_lineage_transform_date": "2026-07-07",
      "agent_lineage_derived_from_skill_id": "audio_pipeline",
      "lineage_match": "MISMATCH"
    },
    {
      "skill_id": "drawer",
      "skill_path": "skills/movie-experts/drawer/SKILL.md",
      "sha256": "2c21f234380ca3fa1f918f733e3cb967d558cdc23b3cca2aedfcb6337682f1eb",
      "bytes": 654,
      "agent_yaml": null,
      "agent_lineage_skill_sha256": null,
      "agent_lineage_transform_date": null,
      "agent_lineage_derived_from_skill_id": null,
      "lineage_match": "N/A (skill-only)"
    },
    {
      "skill_id": "kais-movie-pipeline",
      "skill_path": "skills/kais-movie-pipeline/SKILL.md",
      "sha256": "bf8b7f5a48624dea563b8e37e46adb793dba0006090b334583d757ff7879b7ea",
      "bytes": 111743,
      "agent_yaml": null,
      "agent_lineage_skill_sha256": null,
      "agent_lineage_transform_date": null,
      "agent_lineage_derived_from_skill_id": null,
      "lineage_match": "N/A (skill-only)"
    },
    {
      "skill_id": "kais-jimeng-cli",
      "skill_path": "skills/kais-creative/kais-jimeng-cli/SKILL.md",
      "sha256": "3a9576a66a9567d64074fec278dceae97243f03e2607a902e2a5c4f6b6f4681b",
      "bytes": 17098,
      "agent_yaml": null,
      "agent_lineage_skill_sha256": null,
      "agent_lineage_transform_date": null,
      "agent_lineage_derived_from_skill_id": null,
      "lineage_match": "N/A (skill-only)"
    }
  ]
}
```
