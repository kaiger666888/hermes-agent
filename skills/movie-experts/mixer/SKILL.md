---
name: mixer
description: "DEPRECATED — merged into audio_pipeline (Phase 15 MERGE-02). See ../audio_pipeline/SKILL.md"
version: 1.2.0
metadata:
  hermes:
    expert_id: mixer
    aliases: [audio_pipeline]
    status: merged_into
    merged_into: audio_pipeline
---

# Mixer Expert (混音专家) — MERGED INTO audio_pipeline

This expert has been merged into `audio_pipeline` as the `mixer` sub-step (per Phase 7 §4.9 + PITFALLS §2.6: 5-task compression; consistency context unified).
See [`../audio_pipeline/SKILL.md`](../audio_pipeline/SKILL.md).
Backward-compat alias `mixer` preserved in `metadata.hermes.aliases` of audio_pipeline per FOUND-08.
