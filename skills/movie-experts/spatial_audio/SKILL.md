---
name: spatial_audio
description: "DEPRECATED — folded into audio_pipeline (Phase 15 MERGE-02, disposition D-1: fold). See ../audio_pipeline/SKILL.md"
version: 1.2.0
metadata:
  hermes:
    expert_id: spatial_audio
    aliases: [audio_pipeline]
    status: folded_into
    folded_into: audio_pipeline
---

# Spatial Audio Expert (空间音效专家) — FOLDED INTO audio_pipeline

This expert has been folded into `audio_pipeline` as the `spatial_audio` sub-step (per Phase 15 disposition D-1: spatial audio rendering is fundamentally a mixer/mastering concern; unified consistency context).
See [`../audio_pipeline/SKILL.md`](../audio_pipeline/SKILL.md).
Backward-compat alias `spatial_audio` preserved in `metadata.hermes.aliases` of audio_pipeline per FOUND-08.
