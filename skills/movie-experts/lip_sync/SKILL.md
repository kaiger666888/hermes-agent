---
name: lip_sync
description: "DEPRECATED — merged into audio_pipeline (Phase 15 MERGE-02). See ../audio_pipeline/SKILL.md"
version: 1.1.0
metadata:
  hermes:
    expert_id: lip_sync
    aliases: [audio_pipeline]
    status: merged_into
    merged_into: audio_pipeline
---

# Lip Sync Expert (唇形同步专家) — MERGED INTO audio_pipeline

This expert has been merged into `audio_pipeline` as the `lip_sync` sub-step (per Phase 7 §4.9 + PITFALLS §2.6: 5-task compression; consistency context unified).
See [`../audio_pipeline/SKILL.md`](../audio_pipeline/SKILL.md).
Backward-compat alias `lip_sync` preserved in `metadata.hermes.aliases` of audio_pipeline per FOUND-08.

**V8.6 Pipeline Sync (Phase 25 v5.0):** lip_sync sub-step participates in V8.6 **Step 11 BGM+音效+口型统一**(atomic — was Step 17B in V8.4 before V8.6 §6 merge). Lip sync operates on final mix rather than intermediate dialogue (per V8.6 atomic rationale). See [`../audio_pipeline/SKILL.md §V8.6 Pipeline Sync`](../audio_pipeline/SKILL.md).
