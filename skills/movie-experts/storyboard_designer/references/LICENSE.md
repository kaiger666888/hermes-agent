# License — Storyboard Designer Expert References

**Effective date:** 2026-06-16

## Methodology distillation

All numeric thresholds, schema definitions, and protocols in `references/*.md` files under this expert are **methodology distillations** from publicly available sources:

- Bordwell, D., Thompson, K. *Film Art: An Introduction* (11th ed., 2016) — shot composition + editing rules
- McKee, R. *Story* (1997) — scene decomposition doctrine
- Zhang, L. et al. *Adding Conditional Control to Text-to-Image Diffusion Models* (ControlNet, 2023)
- Ye, H. et al. *IP-Adapter: Text Compatible Image Prompt Adapter for Text-to-Image Diffusion Models* (2023)
- IC-Light (Lvmin Zhang, 2024) — lighting conditioning methodology
- AnimateDiff (Hu, J. et al. 2023) — temporal coherence methodology

These are cited under **Fair Use** (§107 US Copyright Act) for criticism, comment, and educational evaluation purposes.

## Schema originality

The `Storyboard` JSON schema defined in [`./storyboard-schema.md`](./storyboard-schema.md) is an original Hermes Agent project specification, derived from but not directly reproducing:
- OpenClaw kais-storyboard-designer's Storyboard format (methodology only)
- Generic film production storyboard conventions
- Downstream consumer requirements specific to the movie-experts suite (4D anchoring, extension-chain, dual-pointer)

## Specific model name policy

This expert references specific model names (ControlNet, IP-Adapter, IC-Light, AnimateDiff) ONLY in `references/*.md` files. SKILL.md body uses `<controlnet_depth>` / `<ip_adapter>` / `<ic_light>` / `<animatediff>` placeholders. Per [`../_shared/RAG-INVOCATION-PATTERN.md`](../_shared/RAG-INVOCATION-PATTERN.md) placeholder rule, this is permitted.

All model names referenced are also registered in [`../_shared/known-external-models.yaml`](../_shared/known-external-models.yaml) allowlist.

## No third-party copyrighted content

This expert's references contain:
- ❌ No copyrighted storyboard samples from commercial films
- ❌ No proprietary film-school curriculum material
- ❌ No leaked production documents
- ❌ No celebrity footage references

All examples in references are:
1. **Synthetic** — fictional scenes constructed for illustration
2. **Schema specifications** — abstract structural definitions
3. **Industry-standard methodology** — properly attributed inline

## Cross-references to other experts

Some references cross-link to `references/*.md` in other movie-experts experts (e.g., `../../cinematographer/SKILL.md`, `../../character_designer/references/character-bible-schema.md`). Those files have their own LICENSE.md — refer to them for their respective attribution.

## Code

The storyboard_designer expert itself contains no code (per PROJECT.md "pure markdown" constraint). Eval harness code at the suite level (`_eval/runner.py`) is MIT licensed per the root README.

## Questions

For licensing questions or to report a fair-use concern, contact the Hermes Agent project maintainers.
