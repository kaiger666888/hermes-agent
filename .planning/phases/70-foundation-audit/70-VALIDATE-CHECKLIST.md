# Phase 76 VALIDATE Checklist — v14.0 Cross-Cutting Audit

Authored by Phase 70 FOUNDATION-AUDIT. Consumed by Phase 76 VALIDATE. Each row maps a v14.0 requirement to an automated smoke command + expected result. Phase 76 treats this document as its deterministic audit-traceability input — do NOT reverse-engineer assertions from RESEARCH.md (risking the terminology drift flagged in PITFALL 1 below).

**Status glyph convention:** `pending` / `green` / `red` / `flaky` (literal text — no emoji per CLAUDE.md).

---

## XCUT-01 Sub-Claim Verification (Phase 70 self-check + Phase 76 re-verify)

The 6 rows below are the XCUT-01 sub-claims (a-f) split out in RESEARCH.md `## Validation Architecture > Phase Requirements → Test Map`. Phase 70 ran them as smoke assertions via `70-smoke.sh`; Phase 76 re-runs the same commands against post-v14.0 state. Any `red` result at Phase 76 is a BLOCKER.

| Req ID | Behavior | Test Type | Automated Command | Expected Result | Status |
|--------|----------|-----------|-------------------|-----------------|--------|
| XCUT-01a | Lineage Impact Inventory file exists | smoke | `test -f .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md && echo OK` | file present (Phase 70 shipped it; Phase 76 verifies it was not deleted mid-milestone) | pending (Phase 70 green) |
| XCUT-01b | Inventory lists all 6 target SKILL.md files with sha256 | smoke | `[ $(grep -c 'skills/.*SKILL\.md' .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md) -ge 6 ]` | count >= 6 (the 6 targets: cinematographer, editor, audio_pipeline, drawer, kais-movie-pipeline, kais-jimeng-cli) | pending (Phase 70 green) |
| XCUT-01c | Inventory includes cross-repo commit pins for both repos | smoke | `grep -qE 'hermes-agent|kais-hermes-skills' .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md` | both repo names appear; pin SHAs (`8f70fcf7...` hermes-agent, `d9620369...` kais-hermes-skills) are in the embedded JSON block | pending (Phase 70 green) |
| XCUT-01d | Curator is disabled (freeze active during v14.0) | smoke | `grep -A1 "^curator:" ~/.hermes/config.yaml \| grep -q "enabled: false"` (config.yaml grep; CLI `hermes curator status` reports DISABLED) | `curator.enabled: false` for the v14.0 window; Phase 75 flips it back to `true` as its final action (Phase 76 asserts the flip happened) | pending (Phase 70 green; Phase 76 asserts re-enabled) |
| XCUT-01e | STATE.md records the freeze flags | smoke | `grep -q "v14\.0 Freeze Flags" .planning/STATE.md` | `v14.0 Freeze Flags` section present with 4-row flag table (curator.enabled, curator.consolidate, cross_repo_pin.hermes-agent, cross_repo_pin.kais-hermes-skills) | pending (Phase 70 green) |
| XCUT-01f | Phase 76 VALIDATE checklist drafted with all 6 rows | smoke | `[ $(grep -c '^\|' .planning/phases/70-foundation-audit/70-VALIDATE-CHECKLIST.md) -ge 6 ]` | count >= 6 table rows (this file; self-referential row at Phase 76 re-verify time confirms Phase 70 shipped the checklist) | pending (Phase 70 green — this file is the deliverable) |

---

## Phase 76 Hard-Constraint Preservation

The 4 hard constraints below are v14.0 invariants sourced from STATE.md `### Hard Constraints Preserved (v14.0)` (lines 88-93) and `.planning/research/v14-4track-upgrade/PITFALLS.md` (X-2, X-4, X-5). Phase 76 MUST verify each is preserved at milestone close.

### INFRA-04 — serial GLM concurrency (`MAX_CONCURRENT_GL=1`)

**Definition** (per PITFALLS X-5 + MEMORY.md `feedback-glm-overload-reduce-concurrency.md`): the global GLM call budget is pinned at `MAX_CONCURRENT_GL=1`. No `asyncio.gather` / `asyncio.Semaphore` may fan out GLM-coupled routing decisions — including transition engine routing (which is itself LLM-made). The constraint is NOT lifted in v14.0 (deferred to v15+).

**Non-GLM parallelism is allowed** — dreamina_manager `Semaphore(10)` is dreamina CLI fan-out (GPU-bound), Wan-FLF2V local renders are GPU-bound, `MetricsBuffer` ring buffer writes are sync. The rule is narrow: GLM routing decisions stay serialized.

| Req | Automated Command | Expected Result | Status |
|-----|-------------------|-----------------|--------|
| INFRA-04a | `grep -rn "asyncio.gather\|asyncio.Semaphore" skills/ plugins/ scripts/ src/runtime/ 2>/dev/null \| grep -iE "glm\|transition\|img\|dub\|form"` | Zero hits in v14.0-added code paths for GLM-coupled calls. Existing hits in non-GLM code paths (e.g. dreamina_manager.py Semaphore(10)) are acceptable — annotate in audit | pending |
| INFRA-04b | `grep -rn "MAX_CONCURRENT_GL" src/runtime/ plugins/ agent/` | Still pinned at `=1` (or equivalent default). Any v14.0 commit raising this is a BLOCKER | pending |
| INFRA-04c | Manual audit of v14.0 transition engine routing code (TRANS-06 / TRANS-07) | All routing decisions go through the existing `glm_concurrent` semaphore; non-GLM engines share the serialized routing path even if their actual generation fans out | pending |

### EVAL-06 — curator dry-run-first (`--live` frozen for v14.0)

**Definition** (per PITFALLS X-4 + STATE.md Hard Constraints line 91): curator runs dry-run by default; `hermes curator evolve --live` is the explicit opt-in. For v14.0, `curator.enabled: false` (code-enforced freeze) blocks even `--live`. Phase 75 releases the freeze as its final action; Phase 76 asserts the release happened AND verifies the audit log shows zero successful live-ticks during the v14.0 window.

| Req | Automated Command | Expected Result | Status |
|-----|-------------------|-----------------|--------|
| EVAL-06a | `grep -A1 "^curator:" ~/.hermes/config.yaml \| grep -q "enabled: true"` | At Phase 76 time (post-Phase-75 release), `curator.enabled: true` is restored. During v14.0 execution (Phases 70-74), this was `false` (Phase 70 freeze) | pending |
| EVAL-06b | Inspect `~/.hermes/logs/curator_*.log` (or `hermes_cli/curator.py:344-349` `canary_pass=None` audit entries) for any live-tick attempt during v14.0 window (2026-07-09 → Phase 75 completion) | Zero successful live-ticks. Any attempt was blocked at `hermes_cli/curator.py:270-272` (`is_enabled()` check). Attempts are audit-logged — surface in milestone audit | pending |
| EVAL-06c | `python3 -c "from agent import curator; assert curator.is_enabled()"` (post-Phase-75) | Returns True (freeze released). If False at Phase 76 time, Phase 75 release procedure was not completed — BLOCKER | pending |

### FOUND-08 — 15-expert set frozen (TRANS-04 field-level split, no new `expert_id`)

**Definition** (per STATE.md Hard Constraints line 92 + PITFALLS T-2): the 15 movie-expert `expert_id` set is frozen. v14.0 TRANS-04 splits transition ownership as a **field-level** split (creative intent → cinematographer Step 9; post-production execution → editor Step 13), NOT a new `transition_designer` expert. The 6 SKILL.md files touched in v14.0 (`cinematographer`, `editor`, `audio_pipeline`, `drawer`, `kais-movie-pipeline`, `kais-jimeng-cli`) are all existing — zero new expert_id directories under `skills/movie-experts/`.

| Req | Automated Command | Expected Result | Status |
|-----|-------------------|-----------------|--------|
| FOUND-08a | `ls ~/.hermes/agents/*.agent.yaml \| wc -l` | Count unchanged from v13.0 baseline (Phase 70 inventory records 21 files). Any new agent.yaml implies a new expert_id — BLOCKER unless explicitly reconciled | pending |
| FOUND-08b | `grep -rh "^expert_id:" ~/.hermes/agents/*.agent.yaml \| sort -u \| wc -l` | 15 (the frozen movie-expert set). Any new `expert_id` value is a BLOCKER (TRANS-04 must be field-level split, not new expert) | pending |
| FOUND-08c | `ls -d skills/movie-experts/*/ 2>/dev/null` (against kais-hermes-skills repo at v14.0 pin) | No new expert_id directories beyond the v13.0 set. If `transition_designer/` or similar exists — BLOCKER | pending |
| FOUND-08d | `grep -r "transition_designer" skills/ plugins/ src/runtime/ 2>/dev/null` | Zero hits. If any v14.0 code references `transition_designer` expert_id — BLOCKER (TRANS-04 violation) | pending |

### SKILL.md L1-L6 read-only invariant 例外破例 (exception authorized for v14.0)

**Definition** (per STATE.md Hard Constraints line 93 + PROJECT.md): the v10.0 L1-L6 invariant ("kais-hermes-skills SKILL.md read-only") is 例外破例 (exception authorized) for v14.0 ONLY. Lineage regeneration is mandatory per XCUT-03 in Phase 75. The exception covers deliberate SKILL.md edits in v14.0 phase scope (FORM/DUB/IMG/TRANSITION); any drift outside that scope is a violation.

| Req | Automated Command | Expected Result | Status |
|-----|-------------------|-----------------|--------|
| L1-L6a | Compare `git log --oneline kais-hermes-skills/` (post-v14.0 pin `d9620369...` to HEAD) to the list of expected SKILL.md edits (FORM/DUB/IMG/TRANSITION phases) | Every SKILL.md commit maps to a v14.0 phase task. Any commit touching SKILL.md outside phase scope is a violation | pending |
| L1-L6b | `[ $(grep -c "lineage.skill_sha256" ~/.hermes/agents/cinematographer.agent.yaml ~/.hermes/agents/editor.agent.yaml ~/.hermes/agents/audio_pipeline.agent.yaml) -ge 3 ]` (post-Phase-75) | All 3 existing agent.yaml files have refreshed `lineage.skill_sha256` matching the post-v14.0 SKILL.md sha256 (Phase 75 re-transformed them). drawer / kais-movie-pipeline / kais-jimeng-cli remain skill-only (no agent.yaml to bump — per FOUND-08 + research recommendation A1) | pending |
| L1-L6c | `python3 -c "import hashlib; print(hashlib.sha256(open('/data/workspace/kais-hermes-skills/skills/movie-experts/cinematographer/SKILL.md','rb').read().replace(b'\r\n', b'\n')).hexdigest())"` (post-Phase-75) | Matches `cinematographer.agent.yaml` `lineage.skill_sha256` field byte-for-byte. Same check for editor + audio_pipeline | pending |

---

## Cross-Repo Commit Pin Assertion Procedure (Phase 76)

Phase 76 MUST verify that cross-repo coordination was preserved across the v14.0 milestone. The pins recorded in `.planning/STATE.md` `v14.0 Freeze Flags` block (and in `70-LINEAGE-INVENTORY.md` embedded JSON) anchor the baseline.

### Step-by-step procedure

1. **Read the pinned `kais-hermes-skills` SHA from `.planning/STATE.md` `v14.0 Freeze Flags` block.** Expected: `d9620369e48eec51c31ee72ac8827c288eaccf71` (Phase 70 inventory baseline). **Phase 76 reads the LIVE value from STATE.md, NOT hardcoded here** — the pin is the source of truth.

2. **Verify the pin still resolves in the kais-hermes-skills repo:**
   ```bash
   cd /data/workspace/kais-hermes-skills
   git cat-file -t d9620369e48eec51c31ee72ac8827c288eaccf71  # expected: commit
   git merge-base --is-ancestor d9620369e48eec51c31ee72ac8827c288eaccf71 HEAD && echo "descendant" || echo "NOT descendant"
   ```
   The post-v14.0 HEAD MUST be a descendant of the pin (v14.0 commits layered on top, not a force-push rewrite). If `NOT descendant` — BLOCKER.

3. **Re-hash each of the 6 SKILL.md files from the pinned commit using the canonical algorithm** (LF-normalize → UTF-8 → sha256, per `scripts/transform_skill_to_agent.py:232-240`):
   ```bash
   # Use git show to read the file at the pin (no working-tree disruption)
   git show d9620369e48eec51c31ee72ac8827c288eaccf71:skills/movie-experts/cinematographer/SKILL.md \
     | python3 -c "import sys, hashlib; print(hashlib.sha256(sys.stdin.buffer.read().replace(b'\r\n', b'\n')).hexdigest())"
   ```
   **Expected (Phase 70 inventory values, from `70-LINEAGE-INVENTORY.md` embedded JSON block):**
   | skill_id | sha256 (LF-norm UTF-8) |
   |----------|------------------------|
   | cinematographer | `ebe9d3fa8e6b4987d6db2cb6a96bdd407ed526bfe8ce27bb31f8bf41ae5b535b` |
   | editor | `bd5bf4a113eb70485d8774f85ee29e663632a18edcc5540cbe6668691d760f77` |
   | audio_pipeline | `e047010520e3cc4afea5bb0fe96dc1e0ff7826708ae421339305090ce0aeaa9f` |
   | drawer | `2c21f234380ca3fa1f918f733e3cb967d558cdc23b3cca2aedfcb6337682f1eb` |
   | kais-movie-pipeline | `bf8b7f5a48624dea563b8e37e46adb793dba0006090b334583d757ff7879b7ea` |
   | kais-jimeng-cli | `3a9576a66a9567d64074fec278dceae97243f03e2607a902e2a5c4f6b6f4681b` |

   If any re-hash diverges from the inventory — the inventory was tampered with (T-70-06 threat). Investigate via `git log -p -- .planning/phases/70-foundation-audit/70-LINEAGE-INVENTORY.md`.

4. **Compare the re-hashed values (pre-v14.0 baseline) to the post-Phase-75 `agent.yaml.lineage.skill_sha256` values.** CRITICAL: the field name is `lineage.skill_sha256` (NOT `source_sha` — see PITFALL 1 callout below). If Phase 76 greps for `source_sha`, it finds nothing and the assertion silently passes (empty set).
   ```bash
   # Post-Phase-75 (post-bump) check — 3 existing agent.yaml files only
   for agent in cinematographer editor audio_pipeline; do
     pinned_sha=$(grep -A4 "lineage:" ~/.hermes/agents/${agent}.agent.yaml | grep "skill_sha256:" | awk '{print $2}')
     post_v14_skill_sha=$(python3 -c "import hashlib; print(hashlib.sha256(open('/data/workspace/kais-hermes-skills/skills/movie-experts/${agent}/SKILL.md','rb').read().replace(b'\r\n', b'\n')).hexdigest())")
     [ "$pinned_sha" = "$post_v14_skill_sha" ] && echo "OK: $agent" || echo "MISMATCH: $agent pinned=$pinned_sha actual=$post_v14_skill_sha"
   done
   ```
   **Expected:** all 3 existing agent.yaml files (`cinematographer`, `editor`, `audio_pipeline`) have post-bump `lineage.skill_sha256` matching the re-hashed post-v14.0 SKILL.md. The 3 skill-only files (`drawer`, `kais-movie-pipeline`, `kais-jimeng-cli`) have no agent.yaml — Phase 75 decides whether to create them (research recommendation A1: do NOT create, per FOUND-08 frozen 15-expert set + TRANS-04 field-level split).

5. **Verify the hermes-agent pin** (`8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1` per STATE.md): `git -C /data/workspace/hermes-agent merge-base --is-ancestor 8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1 HEAD && echo descendant`. Expected: descendant (Phase 70 Plan 01 commit layered on top).

---

## META-RULE X-2 Audit (XCUT-02 — Phase 76 primary deliverable)

**Definition** (per PITFALLS X-2 + ROADMAP.md Phase 76 success criterion #1): for every MUST / MUST NOT added to SKILL.md across Phases 71-74, a corresponding `_INSTRUCTION` module-level constant exists in the relevant phase `.py` file, injected into the phase `goal` f-string (via `GoalBuilder` `[CONSTRAINTS]` segment, MUST-prefixed for `count_constraints()` detection). This is the #1 documented bug pattern — subagents see only the `goal` string passed to `delegate_task`, never SKILL.md at runtime.

**Phase 76 CI gate:**
```bash
# Per SKILL.md touched in v14.0
diff_count=$(grep -cE "MUST|MUST NOT" /data/workspace/kais-hermes-skills/skills/<path>/SKILL.md)
goal_count=$(grep -cE "MUST" <phase_module.py>::GoalBuilder.goal)
[ "$diff_count" -le "$goal_count" ] || echo "BLOCKER: META-RULE X-2 violation — SKILL.md has $diff_count MUSTs, goal has $goal_count"
```

| Req | Automated Command | Expected Result | Status |
|-----|-------------------|-----------------|--------|
| XCUT-02a | For each SKILL.md touched in Phases 71-74: `grep -cE "MUST \|MUST NOT " <SKILL.md>` vs `grep -cE "_INSTRUCTION = .*MUST" <phase_module.py>` | Every SKILL.md MUST/MUST NOT has a matching `_INSTRUCTION` constant in the phase module that invokes it | pending |
| XCUT-02b | For each `_INSTRUCTION` constant: `grep -E "<keyword>" <phase_module.py>::GoalBuilder.goal` (or test asserting the keyword appears in `captured["goal"]`) | The keyword is actually injected into the goal f-string (not just defined as a constant) | pending |
| XCUT-02c | `pytest tests/test_<phase>.py::test_goal_includes_<keyword>` for each MUST rule | Test exists and passes. Missing test = WARNING (rule not enforced) | pending |

---

## Canonical Field-Name Discipline (load-bearing)

> **PITFALL 1 warning:** The roadmap / REQUIREMENTS prose uses `source_sha` / `transform_rule_id` /
> `transform_timestamp` as shorthand. The ACTUAL agent.yaml schema (verified against 5 live files
> at `~/.hermes/agents/*.agent.yaml` on 2026-07-09, plus `scripts/transform_skill_to_agent.py:191-197`)
> uses the canonical names below. This checklist uses canonical names everywhere; Phase 75 LINEAGE-BUMP
> + Phase 76 VALIDATE assertions MUST do the same or they will grep for nonexistent fields and silently
> pass on empty sets.
>
> | Roadmap shorthand | Canonical field (use this) |
> |-------------------|----------------------------|
> | `source_sha` | `lineage.skill_sha256` |
> | `transform_rule_id` | `lineage.transform_notes` (free text, carries `Rule IDs:` substring) |
> | `transform_timestamp` | `lineage.transform_date` (ISO date `YYYY-MM-DD`, not full timestamp) |
>
> Phase 76 assertions MUST grep for the canonical names. Grepping `source_sha` finds nothing —
> the assertion silently passes on an empty set (false-green). This is the exact bug the v14.0
> Phase 76 audit exists to catch.

The 70-LINEAGE-INVENTORY.md file documents the same mapping in its `## Canonical field-name note (Pitfall 1)` section. The two artifacts are deliberately consistent.

---

## Related Artifacts

- `70-LINEAGE-INVENTORY.md` — Phase 70 Plan 01 deliverable. The primary baseline capture (6 SKILL.md hashes + 3 agent.yaml lineage values + cross-repo pins). Phase 76 cross-references this file via the XCUT-01a/b/c smoke rows.
- `70-smoke.sh` — Phase 70 Plan 03 deliverable. Bash runner executing all 6 XCUT-01 smoke assertions. Phase 70 self-verifies with it; Phase 76 re-runs it as a sanity check.
- `.planning/STATE.md` `### v14.0 Freeze Flags` section — Phase 70 Plan 02 deliverable. 4-row flag table + Phase 75 release procedure. Phase 76 reads the pins + verifies the freeze release (EVAL-06 row).
- `.planning/research/v14-4track-upgrade/PITFALLS.md` — X-1, X-2, X-4, X-5 definitions for the hard-constraint preservation rows above.

---

## Phase 76 Audit Summary Template

Phase 76 fills this in at milestone close:

```
Lineage coverage:           <count>/6 agent.yaml.lineage.skill_sha256 refreshed (expected 3/3 existing + 0/3 skill-only)
Cross-repo pin (hermes):    <descendant/NOT descendant> of 8f70fcf7f0604db21158f86f8495f3d9ce3c9ab1
Cross-repo pin (kais):      <descendant/NOT descendant> of d9620369e48eec51c31ee72ac8827c288eaccf71
Curator freeze released:    <true/false> (EVAL-06 post-Phase-75 restoration)
Curator live-tick attempts: <count> (zero successful during v14.0 window)
INFRA-04 preserved:         <true/false> (MAX_CONCURRENT_GL=1, no asyncio.gather on GLM paths)
FOUND-08 preserved:         <true/false> (15 expert_id unchanged, zero new transition_designer)
META-RULE X-2 compliance:   <count>/<total> MUSTs have matching _INSTRUCTION + test
SKILL.md L1-L6 exception:   <reconciled/unreconciled> (all edits in v14.0 phase scope)
```

---

*Authored: 2026-07-09 — Phase 70 FOUNDATION-AUDIT Plan 03 Task 1. Consumed by Phase 76 VALIDATE.*
