# License — Script Auditor Expert References

**Effective date:** 2026-06-16

## Methodology distillation

All numeric thresholds, hit/miss patterns, and deduction rules in `references/*.md` files under this expert are **methodology distillations** from publicly available sources:

- Snyder, Blake. *Save the Cat!* (2005) — beat structure methodology
- McKee, Robert. *Story* (1997) — value-shift doctrine
- Plutchik, Robert. *A General Psychoevolutionary Theory of Emotion* (1980) — emotion taxonomy
- Propp, Vladimir. *Morphology of the Folktale* (1928) — character-function typology
- Tan, Ed. *Emotion and the Structure of Narrative Film* (2018) — interest formula

These are cited under **Fair Use** (§107 US Copyright Act) for criticism, comment, and educational evaluation purposes. Specific thresholds have been cross-validated against public 短剧 completion-rate benchmarks (蝉妈妈 / 飞瓜 / 新榜 aggregated reports, 2024-2026) and are not direct reproductions of copyrighted text.

## Platform data attribution

Hit/miss pattern references in each `references/*.md` are aggregated from:
- 蝉妈妈 public reports (https://www.chanmama.com)
- 飞瓜 public reports (https://www.feigua.cn)
- 新榜 public reports (https://www.newrank.cn)

These reports are publicly accessible. Specific numeric means and standard deviations are computed by the Hermes Agent project over samples of 50 hit / 50 miss 短剧 scripts per category. Underlying script content is NOT included in this repo — only aggregated statistics.

## No third-party copyrighted content

This expert's references contain:
- ❌ No full reproductions of copyrighted screenplays
- ❌ No proprietary platform API documentation
- ❌ No leaked industry reports
- ❌ No 短剧 transcript reproductions

All examples and case studies in the references are either:
1. **Synthetic** — constructed to illustrate a heuristic without reproducing any real 短剧 content
2. **Aggregated statistics** — means, stds, and correlations computed over labeled corpora
3. **Direct quotations from public-domain or fair-use sources** — properly attributed inline

## Cross-references to other experts

Some references in this directory cross-link to `references/*.md` files in other movie-experts experts (e.g., `../../screenplay/references/save-the-cat-beat-sheet.md`). Those files have their own LICENSE.md — refer to them for their respective attribution.

## Code

The script_auditor expert itself contains no code (per PROJECT.md "pure markdown" constraint). Eval harness code at the suite level (`_eval/runner.py`) is MIT licensed per the root README.

## Questions

For licensing questions or to report a fair-use concern, contact the Hermes Agent project maintainers.
