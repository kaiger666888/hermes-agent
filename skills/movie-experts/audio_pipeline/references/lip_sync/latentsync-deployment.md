# LatentSync Deployment Reference

**Source:** LatentSync v1.5 / v1.6 official documentation (https://github.com/bytedance/LatentSync) + Hermes Agent project deployment records.
**Copyright:** Fair Use — methodology distillation; specific model name appears here because this file is `references/*.md` (allowed per `_shared/RAG-INVOCATION-PATTERN.md`).
**Last-verified:** 2026-06-16

## Summary

Authoritative deployment guide for the primary lip-sync engine. Documents 5 deployment paths (Linux CLI / Windows / ComfyUI / Replicate / Docker) and the parameter trade-offs that affect LSE quality. This file is the ONLY place in the lip_sync expert where specific model names appear — SKILL.md body uses `<lip_sync_primary>` placeholder.

## Heuristics

### Version selection (v1.5 vs v1.6)

| Feature | v1.5 | v1.6 |
|---|---|---|
| Resolution | 256×256 | 512×512 |
| Min VRAM (inference) | 8 GB | 18 GB |
| Recommended VRAM | 10 GB | 24 GB |
| Temporal consistency | Basic | Improved |
| Chinese support | Optimized | Optimized |
| Blur issue | Present | Significantly mitigated |
| HuggingFace repo | ByteDance/LatentSync-1.5 | ByteDance/LatentSync-1.6 |
| LRS2 LSE (paper) | 5.89 | 5.13 |

**Selection logic:**
- VRAM ≥ 18 GB → v1.6 (recommended for final delivery)
- VRAM 8-18 GB → v1.5 (acceptable for short-form content)
- VRAM < 8 GB → switch to `<lip_sync_fallback>` (GAN-based, see known-external-models.yaml)

### Inference parameters (quality vs speed trade-off)

| Parameter | Range | Default | Effect |
|---|---|---|---|
| `inference_steps` | 20-50 | 20 | ↑ improves quality, ↓ improves speed |
| `guidance_scale` | 1.0-3.0 | 1.5 | ↑ improves lip accuracy, too high → jitter |
| `deepcache` | flag | off | enables DeepCache acceleration (30-40% faster, ~1% LSE increase) |
| `mask_dilation` | 0-10 px | 4 | higher = diffusion edits further from mouth |
| `unet_config_path` | - | stage2 (v1.5) / stage2_512 (v1.6) | do not change unless rebuilding |

**Best-practice presets:**

```yaml
# Daily preview (fast, ~20s on RTX 3090)
inference_steps: 20
guidance_scale: 1.5
deepcache: true

# High-quality final delivery
inference_steps: 35
guidance_scale: 2.0
deepcache: false  # quality > speed

# Quick preview
inference_steps: 20
guidance_scale: 1.0
deepcache: true
```

### Deployment path 1: Linux native

**Prerequisites:** Ubuntu 22.04+, CUDA 12.1+, conda/mamba.

**Steps:**
1. Clone repo
2. Create conda env (Python 3.10)
3. Install requirements + add `torchaudio==2.5.1` to requirements.txt
4. Verify CUDA available
5. Download model weights to `checkpoints/`
6. Run via `python -m scripts.inference ...`

**Common pitfalls:**
- Missing torchaudio → "ImportError: torchaudio"
- CUDA mismatch → silent fallback to CPU (10× slower)
- Whisper tiny.pt missing → "KeyError: 'whisper'"

### Deployment path 2: Windows

**Prerequisites:** Windows 10/11, CUDA 12.1, Anaconda.

**Additional steps vs Linux:**
- Use GitHub Desktop for cloning (avoids line-ending issues)
- Install Visual Studio Build Tools 2019 (for compilation)
- Path: use raw strings (`r"C:\path"`) in Python
- GPU passthrough in WSL2 is supported but ~15% slower than native

### Deployment path 3: ComfyUI integration

**Prerequisites:** ComfyUI installed with custom_nodes support.

**Steps:**
1. `git clone https://github.com/ShmuelRonen/ComfyUI-LatentSyncWrapper.git` into `custom_nodes/`
2. Install wrapper requirements
3. Restart ComfyUI; refresh browser
4. Add "LatentSync" node to workflow

**Workflow benefits:**
- Drag-and-drop UI
- Compatible with other ComfyUI nodes (face enhancement, color grading)
- Persisted workflow as `.json` for reproducibility

### Deployment path 4: Replicate cloud API

**Prerequisites:** Replicate account, API token.

**Use case:** no local GPU, willing to pay per inference.

**Cost reference (2024-2026 average):**
- ~$0.02 per 10s clip on Nvidia A100
- ~$0.05 per 10s clip on H100 (faster, higher quality)

**Limitations:**
- Requires uploading video to Replicate
- Network latency adds 5-15s per call
- Rate limits: 10 concurrent requests per standard account

### Deployment path 5: Docker

**Prerequisites:** Docker 24+, nvidia-docker runtime.

**Dockerfile pattern (simplified):**
```dockerfile
FROM nvidia/cuda:12.1.1-cudnn8-runtime-ubuntu22.04
RUN apt-get update && apt-get install -y python3.10 python3-pip git
RUN git clone https://github.com/bytedance/LatentSync.git /latentsync
WORKDIR /latentsync
RUN pip install -r requirements.txt && pip install torchaudio==2.5.1
# Pre-download weights to image
COPY checkpoints/ /latentsync/checkpoints/
ENTRYPOINT ["python", "-m", "scripts.inference"]
```

**Image size:** ~8 GB (weights dominate).

### Hardware reference

| GPU | VRAM | v1.5 fps | v1.6 fps | Recommended use |
|---|---|---|---|---|
| RTX 3060 Ti | 8 GB | 0.3 fps | OOM | v1.5 preview only |
| RTX 3090 | 24 GB | 1.2 fps | 0.6 fps | Production |
| RTX 4090 | 24 GB | 1.8 fps | 0.9 fps | Production + fine-tuning |
| A100 40GB | 40 GB | 2.5 fps | 1.4 fps | Cloud production |
| A100 80GB | 80 GB | 3.0 fps | 1.8 fps | Cloud production + research |
| H100 | 80 GB | 4.5 fps | 2.5 fps | Cloud SOTA |

**Throughput estimate:** for a 25-episode 短剧 with avg 30s dialogue per episode = 750s of footage. On RTX 4090 v1.6, processing time ≈ 750s × (1/0.9) ≈ 835s ≈ 14 minutes.

### Comparison with alternative engines

| Engine | Method | Quality | Temporal consistency | VRAM | Open-source |
|---|---|---|---|---|---|
| LatentSync | Latent diffusion | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | 8-18 GB | ✅ |
| Wav2Lip | GAN | ⭐⭐⭐ | ⭐⭐⭐ | ~2 GB | ✅ |
| SyncTalk | Diffusion | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ~8 GB | ✅ |
| MuseTalk | Diffusion + Motion | ⭐⭐⭐⭐ | ⭐⭐⭐ | ~8 GB | ✅ |
| HeyGen | Commercial | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | Cloud | ❌ |
| D-ID | Commercial | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | Cloud | ❌ |

**LatentSync advantages:** best open-source quality, Chinese-optimized, end-to-end (no intermediate motion representation).

**LatentSync weaknesses:** requires 8 GB VRAM minimum (vs 2 GB for Wav2Lip); not real-time (0.6-2 fps).

### Troubleshooting reference

| Symptom | Likely cause | Fix |
|---|---|---|
| OOM during inference | VRAM < required | Switch to v1.5; enable deepcache; reduce inference_steps |
| Chinese lip-sync quality poor | Sample rate wrong | Re-encode audio to 16000Hz mono WAV |
| Jitter in output | guidance_scale too high | Lower to 1.0-1.5; switch to v1.6 for better temporal consistency |
| Blur in output | Resolution too low | Switch to v1.6 (512×512) |
| Face detection fails | Input quality issue | See [`./audio-video-input-spec.md`](./audio-video-input-spec.md) §failure modes |

---

## Cross-references

- [`./sync-quality-metrics.md`](./sync-quality-metrics.md) — how deployment parameters affect LSE
- [`./audio-video-input-spec.md`](./audio-video-input-spec.md) — input requirements for successful inference
- [`../../_shared/known-external-models.yaml`](../../_shared/known-external-models.yaml) — model allowlist (this file's content must match the allowlist)
