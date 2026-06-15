# License — Character Designer Expert References

**Effective date:** 2026-06-16

## Methodology distillation

All numeric thresholds, schemas, and protocols in `references/*.md` files under this expert are **methodology distillations** from publicly available sources:

- CLIP (Radford et al. 2021) — image embedding methodology
- DINO / DINOv2 (Caron et al. 2021, 2023) — self-supervised image embedding methodology
- ArcFace (Deng et al. 2019) — face identity embedding
- Animation industry character turnaround conventions
- OpenClaw kais-character-designer reference framework (methodology only, no code)

These are cited under **Fair Use** (§107 US Copyright Act) for criticism, comment, and educational evaluation purposes.

## Schema originality

The `CharacterBible 2.0` schema defined in [`./character-bible-schema.md`](./character-bible-schema.md) is an original Hermes Agent project specification, derived from but not directly reproducing:
- OpenClaw kais-character-designer's CharacterBible format
- Generic animation production character-bible conventions
- Downstream consumer requirements specific to the movie-experts suite

## No third-party copyrighted content

This expert's references contain:
- ❌ No copyrighted character designs
- ❌ No proprietary turnaround sheets from animation studios
- ❌ No leaked model prompts or system prompts from commercial character-creation tools
- ❌ No celebrity likeness references

All character examples in references are:
1. **Synthetic** — fictional characters constructed for illustration (e.g., the cyberpunk "char_wuji" example)
2. **Schema specifications** — abstract structural definitions, not specific character content

## Cross-references to other experts

Some references cross-link to `references/*.md` files in other movie-experts experts (e.g., `../../drawer/references/character-consistency-lora.md`, `../../lip_sync/references/identity-preservation.md`). Those files have their own LICENSE.md — refer to them for their respective attribution.

## Code

The character_designer expert itself contains no code (per PROJECT.md "pure markdown" constraint). Eval harness code at the suite level (`_eval/runner.py`) is MIT licensed per the root README.

## Questions

For licensing questions or to report a fair-use concern, contact the Hermes Agent project maintainers.
