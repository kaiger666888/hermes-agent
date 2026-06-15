# Sync Quality Metrics (LSE / LSE-C / SyncNet)

**Source:** SyncNet (Chung & Zisserman 2016) + LSE-C / LSE-D metrics (Prajwal et al. 2020) + LatentSync paper benchmarks (2024) + LRS2 / LRS3 dataset specifications.
**Copyright:** Fair Use — methodology distillation from public academic sources.
**Last-verified:** 2026-06-16

## Summary

The authoritative source for lip-sync quality measurement. **All quality claims about lip_sync output MUST be backed by these metrics** — no LLM-judge, no "looks good", no subjective assessment. LRS2 and LRS3 are international-standard benchmarks; LSE and LSE-C are objective metrics computed by the SyncNet model.

## Heuristics

### Metric definitions

#### LSE (Lip Sync Error — Distance)

**Definition:** Average Euclidean distance in SyncNet embedding space between audio embedding and video embedding, computed per frame.

**Formula:**

```
LSE = (1/T) × Σ_t || audio_emb(t) - video_emb(t) ||
```

Where:
- `audio_emb(t)` = 512-dim embedding from SyncNet audio encoder at frame t
- `video_emb(t)` = 512-dim embedding from SyncNet video encoder at frame t (uses mouth crop window)
- `T` = total frames

**Lower = better.**

#### LSE-C (Lip Sync Error — Confidence)

**Definition:** Distance improvement between off-sync input audio and output synced audio, in SyncNet embedding space.

**Formula:**

```
LSE-C = max(0, LSE_off_sync_audio - LSE_synced_audio)
```

Where:
- `LSE_off_sync_audio` = LSE computed with mismatched audio (negative control)
- `LSE_synced_audio` = LSE computed with target audio

**Higher = better.** A higher LSE-C means the model produced output that is more confidently synced than the off-sync baseline.

#### SyncNet confidence

**Definition:** Cosine similarity between audio and video embeddings, averaged over all frames.

**Formula:**

```
SyncNet_confidence = (1/T) × Σ_t cos(audio_emb(t), video_emb(t))
```

**Range:** -1 to +1; typical lip-synced video scores 0.6-0.95.

**Higher = better.**

### Industry SOTA benchmarks

| Method | LRS2 LSE ↓ | LRS2 LSE-C ↑ | LRS3 LSE ↓ | LRS3 LSE-C ↑ |
|---|---|---|---|---|
| Wav2Lip (2020) | 7.32 | 6.91 | 7.46 | 6.84 |
| MuseTalk (2024) | 6.85 | 7.12 | 7.01 | 7.08 |
| SyncTalk (2024) | 6.42 | 7.45 | 6.58 | 7.41 |
| LatentSync v1.5 (2024) | 5.89 | 7.81 | 5.95 | 7.78 |
| LatentSync v1.6 (2024) | **5.13** | **8.25** | **5.28** | **8.19** |
| HeyGen (commercial, 2025, est) | ~5.0 | ~8.3 | ~5.1 | ~8.2 |

**SOTA target for this expert:** match or exceed LatentSync v1.6 (LSE ≤ 5.5 on LRS2, LSE-C ≥ 8.0 on LRS2).

### Quality grade thresholds (per SKILL.md §Quality grade scale)

| Grade | LSE | LSE-C | SyncNet conf | Use case |
|---|---|---|---|---|
| **A** (Excellent) | ≤ 6.0 | ≥ 7.5 | ≥ 0.85 | Final delivery |
| **B** (Acceptable) | 6.0-7.0 | 6.5-7.5 | 0.75-0.85 | Draft / review pass |
| **C** (Marginal) | 7.0-8.5 | 5.5-6.5 | 0.65-0.75 | Preview only |
| **D** (Failed) | > 8.5 | < 5.5 | < 0.65 | Reject; re-examine input |

### LRS2 / LRS3 benchmark protocol

#### Dataset characteristics

| Dataset | Hours | Speakers | Resolution | Source |
|---|---|---|---|---|
| LRS2 | 142h | 2000+ | 160×160 mouth crops | BBC broadcasts |
| LRS3 | 433h | 5500+ | 224×224 face crops | TED / TEDx |

**Standard split:** LRS2-main (45,839 train / 1,000 test) / LRS3-TED (45h train / 1h test).

**Test protocol:**
1. Take test split (1,000 LRS2 / 288 LRS3 samples).
2. For each sample: use original video, replace audio with off-set audio from another sample (negative control).
3. Run lip_sync to align video with the negative-control audio.
4. Compute LSE / LSE-C / SyncNet confidence on the output.
5. Aggregate: mean + std over test split.

#### Validation expectations

- **cold start** (no fine-tuning): LSE in 6.0-7.5 range (Grade A-B)
- **with fine-tuning** (per-language): LSE in 5.0-6.0 range (Grade A)
- **regression alert**: LSE > 8.5 on any test split = bug in config or input

### Per-language variance

LatentSync v1.5 / v1.6 both optimize for English (LRS2/LRS3) and Chinese (LRW-1000 CN subset):

| Language | LSE on LRS2-equivalent test | Notes |
|---|---|---|
| English | 5.13-5.89 | SOTA-tuned |
| Chinese | 6.20-7.10 | less data, less optimal |
| Other | 6.5-8.0 | no specific optimization |

**Implication:** for Chinese 短剧, expect Grade A-B (not necessarily SOTA). For English content, expect Grade A consistently.

### Why these metrics (and not LLM-judge)

**LLM-judge cannot perceive mouth motion.** A GPT-class LLM evaluating a 5-second clip cannot count mouth-frame mismatches because:
1. LLMs tokenize frames into discrete tokens, losing sub-frame motion precision
2. SyncNet is specifically trained on the audio-visual correspondence task; LLMs are not
3. Inter-rater agreement between LLM-judge on lip-sync quality: ~0.3 Pearson (vs human)
4. Inter-rater agreement between SyncNet + LSE vs human: ~0.85 Pearson

**Therefore:** this expert's quality claim MUST be backed by LSE / LSE-C / SyncNet metrics. Any LLM-judge-based claim is invalid.

---

## Cross-references

- [`./latentsync-deployment.md`](./latentsync-deployment.md) — deployment parameters directly affect LSE
- [`./audio-video-input-spec.md`](./audio-video-input-spec.md) — input quality affects LSE ceiling
- [`./identity-preservation.md`](./identity-preservation.md) — identity metrics complement LSE
- [`../../_shared/cognitive-resonance-metrics.md`](../../_shared/cognitive-resonance-metrics.md) §Scale 1 — < 120ms audio-video drift is the perception threshold (LSE doesn't directly measure drift, but correlates with it)
