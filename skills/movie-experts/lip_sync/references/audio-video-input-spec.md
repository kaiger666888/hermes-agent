# Audio-Video Input Specification

**Source:** LatentSync official input requirements + face-detection best practices + Hermes Agent project input-corpus analysis.
**Copyright:** Fair Use — methodology distillation.
**Last-verified:** 2026-06-16

## Summary

Authoritative specification for the input video + audio pair that lip_sync consumes. Defines the 4-tier input quality rating system that determines whether inference will succeed, the failure modes per tier, and the preprocessing recommendations to upgrade low-tier inputs.

## Heuristics

### Video input requirements

| Spec | Required | Recommended |
|---|---|---|
| Container | MP4 | MP4 |
| Codec | H.264 | H.264 (CRF 18-23) |
| Frame rate | 25 fps | 25 fps (do not change mid-pipeline) |
| Resolution | ≥ 360×360 (face crop) | 720p+ original |
| Face position | frontal (yaw ≤ 30°, pitch ≤ 20°) | full frontal |
| Face size | ≥ 80×80 px mouth region | ≥ 200×200 px |
| Lighting | uniform, no harsh shadows | soft 3-point lighting |
| Single face | exactly 1 face per frame | 1 face |
| Occlusion | mouth unobstructed | mouth clear |
| Duration | ≤ audio duration | = audio duration |

### Audio input requirements

| Spec | Required | Recommended |
|---|---|---|
| Container | WAV | WAV (lossless) |
| Sample rate | 16000 Hz | 16000 Hz (resample if different) |
| Channels | mono | mono |
| Bit depth | 16-bit PCM | 16-bit PCM |
| Duration | ≤ video duration | = video duration |
| SNR | ≥ 20 dB | ≥ 30 dB |
| Silence padding | 0-100ms at start | 50ms at start |

### 4-tier input quality rating

#### Tier A (excellent) — ship directly

- Frontal face, ≤ 15° yaw
- Single person, no other faces in frame
- Mouth clear, no occlusion (no hand / hair / mask / mic)
- Uniform lighting, no harsh shadows
- Face ROI ≥ 200×200 px
- Studio-quality audio, SNR ≥ 30 dB

**Expected output:** Grade A sync quality.

#### Tier B (acceptable) — ship with monitoring

- Yaw 15-30°
- Distant secondary face in background (clearly not speaking)
- Hair partially across mouth corner (< 20% mouth area)
- Slight shadow on one side
- Face ROI 100-200 px
- Audio SNR 20-30 dB

**Expected output:** Grade B sync quality. May have minor artifacts on shadow side.

#### Tier C (marginal) — preprocess or retry

- Yaw 30-45°
- Background person similar size to speaker (could confuse face detector)
- Occlusion 20-40% of mouth
- Harsh shadow or strong backlight
- Face ROI 80-100 px
- Audio SNR 10-20 dB

**Expected output:** Grade C-D sync quality. **Required preprocessing:**
- For yaw > 30°: trim video to moments when face is more frontal
- For background face: pre-crop video to speaker region only
- For occlusion: request reshoot OR switch to [`animator`](../../animator/SKILL.md) for synthetic footage
- For audio: denoise + speech enhancement

#### Tier D (reject) — do not attempt

- Profile shot (yaw > 45°)
- Multiple speakers, indistinguishable
- Heavy occlusion (> 40% mouth)
- Face ROI < 80 px
- Audio SNR < 10 dB
- Multi-person overlapping dialogue

**Action:** Reject input. Route to [`animator`](../../animator/SKILL.md) for synthetic footage generation, OR request reshoot.

### Failure mode catalog

| Symptom | Cause | Detection signal | Recommended action |
|---|---|---|---|
| No face detected | Multi-person / extreme angle / face < 80px | Face detector returns 0 results | Pre-crop; or reject |
| Wrong face synced | Background person similar size | Face detector picks largest face, not speaker | Pre-crop to speaker ROI |
| Mouth deforms | Heavy occlusion | Mouth detector returns < 50% confidence | Reject; reshoot |
| Blurry output | Low input resolution | Face ROI < 100px | Upscale input or switch to v1.6 (512×512) |
| Jitter on shadow side | Harsh lighting | One side of face has std < 5 in pixel values | Color-grade for even exposure |
| Audio drift | Sample rate mismatch | Audio duration ≠ video duration × 1.0 | Re-encode audio to 16000Hz |
| Output too short | Audio > video duration | Audio duration > video duration | Trim audio OR extend video |

### Preprocessing recommendations

#### For Tier B inputs

```python
# Auto-tier-B enhancement (conceptual; not in this file as code)
def enhance_tier_b(video, audio):
    # 1. Crop video to speaker ROI using face tracker
    # 2. Color-grade for even exposure
    # 3. Resample audio to 16000Hz if needed
    # 4. Add 50ms silence padding at start
    return enhanced_video, enhanced_audio
```

#### For Tier C inputs

Tier C requires human-in-the-loop preprocessing:
1. Manual trim of profile sections
2. Manual speaker ROI crop
3. Optional: speech enhancement (RNNoise / Demucs)
4. **Recommendation:** if preprocessing > 5 minutes of work, switch to [`animator`](../../animator/SKILL.md)

#### For Tier D inputs

Do NOT preprocess. The information loss is too severe. Route to:
- [`animator`](../../animator/SKILL.md) for synthetic footage
- [`voicer`](../../voicer/SKILL.md) for audio re-generation
- User reshoot

### Audio duration vs video duration rules

| Relationship | Action |
|---|---|
| Audio duration ≈ video duration (±100ms) | Ideal; process directly |
| Audio shorter | Process; output video matches audio duration (truncate trailing video) |
| Audio longer by < 1s | Pad video with last frame freeze; warning emitted |
| Audio longer by ≥ 1s | Reject; ask user to either trim audio or extend video |
| Audio silence > 500ms in middle | Process; sync quality may dip during silence |

### Special case: multi-shot footage

If footage contains cuts (e.g., character walking between rooms):
- **Strong recommendation:** split into per-shot clips; run lip_sync on each independently; re-stitch in [`editor`](../../editor/SKILL.md)
- **Why:** lip_sync assumes continuous temporal context; cross-cut footage confuses the model

### Special case: character avatar footage

For AI-generated character avatars (from [`drawer`](../../drawer/SKILL.md) or [`animator`](../../animator/SKILL.md)):
- Treat as Tier A if drawer/animator output meets frontal-face requirement
- Common pitfall: drawer outputs side-view character → downgrades to Tier C
- Fix: explicitly request "frontal portrait, ≤ 15° yaw" from drawer

---

## Cross-references

- [`./sync-quality-metrics.md`](./sync-quality-metrics.md) — how input tier affects achievable output grade
- [`./latentsync-deployment.md`](./latentsync-deployment.md) — deployment parameters can partially compensate for Tier B-C inputs
- [`../../animator/SKILL.md`](../../animator/SKILL.md) — fallback for Tier D inputs (synthetic footage)
- [`../../voicer/SKILL.md`](../../voicer/SKILL.md) — audio source; must produce 16000Hz mono WAV
