---
name: foley
description: "DEPRECATED — merged into audio_pipeline (Phase 15 MERGE-02). See ../audio_pipeline/SKILL.md"
version: 1.1.0
metadata:
  hermes:
    expert_id: foley
    aliases: [audio_pipeline]
    status: merged_into
    merged_into: audio_pipeline
---

# Foley Expert (物理音效专家) — MERGED INTO audio_pipeline

This expert has been merged into `audio_pipeline` as the `foley` sub-step (per Phase 7 §4.9 + PITFALLS §2.6: 5-task compression; consistency context unified).
See [`../audio_pipeline/SKILL.md`](../audio_pipeline/SKILL.md).
Backward-compat alias `foley` preserved in `metadata.hermes.aliases` of audio_pipeline per FOUND-08.

**V8.6 Pipeline Sync (Phase 25 v5.0):** foley sub-step participates in V8.6 **Step 7B 声音骨架**(key SFX placeholders)+ **Step 11 BGM+音效+口型统一**(full SFX library expansion). See [`../audio_pipeline/SKILL.md §V8.6 Pipeline Sync`](../audio_pipeline/SKILL.md).
