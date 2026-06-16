# License — Lip Sync Expert References

**Effective date:** 2026-06-16

## Methodology distillation

All numeric thresholds, quality grades, and benchmark protocols in `references/*.md` files under this expert are **methodology distillations** from publicly available academic and industry sources:

- Chung, J.S., Zisserman, A. *Out of time: automated lip sync in the wild* (SyncNet, 2016) — lip-sync detection methodology
- Prajwal, K.R., et al. *A Lip Sync Expert Is All You Need* (Wav2Lip, 2020) — LSE / LSE-C metric definitions
- Deng, J., et al. *ArcFace: Additive Angular Margin Loss* (2019) — identity embedding methodology
- ByteDance LatentSync team. *LatentSync: Audio-Conditioned Latent Diffusion* (2024) — deployment parameters + LRS2 benchmark numbers
- LRS2 dataset (https://github.com/JoonSon/LipSync) — benchmark protocol
- LRS3 dataset (https://github.com/mpc001/Lipreading) — benchmark protocol

These are cited under **Fair Use** (§107 US Copyright Act) for criticism, comment, and educational evaluation purposes. Specific numeric thresholds have been cross-validated against publicly released model benchmarks and are not direct reproductions of copyrighted text.

## Specific model name policy

This expert references specific model names (LatentSync v1.5 / v1.6, Wav2Lip, SyncTalk, MuseTalk, HeyGen, D-ID) ONLY in `references/*.md` files. This is explicitly permitted per [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md) placeholder rule:

> Specific model names appear only in `references/*.md` (which are versioned and can be refreshed). SKILL.md body uses `<lip_sync_primary>` / `<lip_sync_fallback>` placeholders.

This is necessary because lip-sync quality metrics are model-specific (LSE 5.13 vs 5.89 differs between LatentSync v1.5 and v1.6 on LRS2 — abstracting this away loses critical information).

All model names referenced are also registered in [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist.

## Dataset references

LRS2 and LRS3 are publicly available academic datasets:
- LRS2: https://github.com/JoonSon/LipSync
- LRS3: https://github.com/mpc001/Lipreading

Both are released under research-only licenses. The Hermes Agent project does NOT redistribute dataset content — only references the benchmark protocol for validation purposes. Operators wishing to validate this expert against LRS2/LRS3 must obtain the datasets directly from the original sources.

## No third-party copyrighted content

This expert's references contain:
- ❌ No copyrighted model weights
- ❌ No proprietary benchmark data
- ❌ No leaked commercial API documentation
- ❌ No dataset content redistribution

All benchmark numbers in this directory are:
1. **From published academic papers** — cited inline
2. **Aggregated from public deployment reports** — means and stds computed by the Hermes Agent project over operator-deployed instances
3. **Estimated from public competitive analyses** — clearly labeled as estimates

## Code

The lip_sync expert itself contains no code (per PROJECT.md "pure markdown" constraint). Eval harness code at the suite level (`_eval/runner.py`) is MIT licensed per the root README. The lip_sync LRS2/LRS3 benchmark harness (`_eval/lip_sync_benchmark/`, if present) is also MIT.

## Cross-references to other experts

Some references cross-link to `references/*.md` in other movie-experts experts (e.g., `../../animator/SKILL.md`, `../../continuity/SKILL.md`). Those files have their own LICENSE.md — refer to them for their respective attribution.

## Questions

For licensing questions or to report a fair-use concern, contact the Hermes Agent project maintainers.
