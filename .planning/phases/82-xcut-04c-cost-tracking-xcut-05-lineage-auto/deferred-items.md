# Deferred Items — Phase 82

## Pre-existing test failure (out of scope)

**Discovered during:** Plan 82-01 verification (full kais_aigc test suite run)

**Item:** `plugins/kais_aigc/tests/test_canvas_sync_integration.py::TestFullPipelineEpisodeSubscriber::test_save_v2_bodies_carry_phase_node_ids` fails.

**Root cause:** Pre-existing failure unrelated to Phase 82 changes. Verified by `git stash` — failure reproduces without any Phase 82 modifications. The test exercises the canvas sync pipeline (episode subscriber + phase node IDs), not dreamina_stats / vision_verify / dreamina_manager.

**Scope:** OUT of Phase 82 scope. Canvas sync integration is a separate subsystem. Logging per scope-boundary rule — do NOT fix.

**Reproduction:** `cd /data/workspace/kais-hermes-skills && python -m pytest plugins/kais_aigc/tests/test_canvas_sync_integration.py::TestFullPipelineEpisodeSubscriber::test_save_v2_bodies_carry_phase_node_ids -x -q` → 1 failed.
