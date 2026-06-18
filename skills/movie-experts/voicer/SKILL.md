---
name: voicer
description: "DEPRECATED — merged into audio_pipeline (Phase 15 MERGE-02). See ../audio_pipeline/SKILL.md"
version: 1.2.0
metadata:
  hermes:
    expert_id: voicer
    aliases: [audio_pipeline]
    status: merged_into
    merged_into: audio_pipeline
---

# Voicer Expert (配音专家) — MERGED INTO audio_pipeline

This expert has been merged into `audio_pipeline` as the `voicer` sub-step (per Phase 7 §4.9 + PITFALLS §2.6: 5-task compression; consistency context unified).
See [`../audio_pipeline/SKILL.md`](../audio_pipeline/SKILL.md).
Backward-compat alias `voicer` preserved in `metadata.hermes.aliases` of audio_pipeline per FOUND-08.

**V8.6 Pipeline Sync (Phase 25 v5.0):** voicer sub-step participates in V8.6 **Step 7B 声音骨架**(TTS skeleton)+ **Step 11 BGM+音效+口型统一**(final dialogue TTS). See [`../audio_pipeline/SKILL.md §V8.6 Pipeline Sync`](../audio_pipeline/SKILL.md) for full Step mapping + dreamina CLI `@Audio N` binding syntax.
