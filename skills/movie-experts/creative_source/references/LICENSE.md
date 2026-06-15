# License — Creative Source Expert References

**Effective date:** 2026-06-16

## Methodology distillation

All strata definitions, theoretical bases, and analysis frameworks in `references/*.md` files under this expert are **methodology distillations** from publicly available academic sources:

- Bourdieu, P. *Distinction: A Social Critique of the Judgement of Taste* (1979) — field theory + cultural capital
- Foucault, M. *Discipline and Punish* (1975) — power/knowledge doctrine
- Giddens, A. *The Constitution of Society* (1984) — structuration theory
- Barthes, R. *S/Z* (1970) — narrative structure analysis
- Lefebvre, H. *The Production of Space* (1974) — spatial production theory
- Harvey, D. *The Urban Experience* (1989) — spatial fix theory
- Braverman, H. *Labor and Monopoly Capital* (1974) — labor process theory
- Acemoglu, D., Restrepo, P. *Robots and Jobs* (2020) — task model of automation
- Fromm, E. *Escape from Freedom* (1941) + *The Sane Society* (1955)
- Han, B.-C. *The Burnout Society* (2010) + *Agony of Eros* (2012)
- Lasch, C. *The Culture of Narcissism* (1979)
- Mannheim, K. *The Problem of Generations* (1928)
- Beck, U. *Risk Society* (1986)
- Demographic Transition Theory (Notestein 1945) + Push-Pull Theory (Lee 1966)

These are cited under **Fair Use** (§107 US Copyright Act) for criticism, comment, and educational evaluation purposes.

## Data source attribution

All data source URLs in `references/*.md` are publicly accessible:
- 中国政府网 (gov.cn) — public policy archive
- 国家统计局 (stats.gov.cn) — public census data
- WEF / McKinsey / ILO — public reports
- 贝壳研究院 — public housing market reports
- 知乎 / 小红书 / 微博 — public social platforms

The Hermes Agent project does NOT redistribute third-party data — only references public URLs for retrieval.

## Schema originality

The `StoryKernel` JSON schema defined in [`./story-kernel-schema.md`](./story-kernel-schema.md) is an original Hermes Agent project specification, derived from but not directly reproducing:
- OpenClaw kais-soul-radar's Story Kernel format (methodology only)
- Generic story-bible conventions
- Downstream consumer requirements specific to the movie-experts suite

## Unspeakability protocol source

The unspeakability scoring protocol in [`./unspeakability-protocol.md`](./unspeakability-protocol.md) is calibrated against:
- 网信办 publicly announced content guidelines
- 广电总局 publicly announced备案 regulations
- Each CN platform's publicly posted community guidelines

The Hermes Agent project does NOT include proprietary internal moderation policies. Scoring is based on publicly observable content takedowns + creator-community shared experiences.

## No third-party copyrighted content

This expert's references contain:
- ❌ No copyrighted academic text reproductions
- ❌ No proprietary moderation policy documents
- ❌ No leaked platform internal guidelines
- ❌ No specific individual personal stories

All examples in references are:
1. **Synthetic** — constructed for illustration (e.g., the "灵活就业者" example is a generalized composite)
2. **Public-domain data references** — URLs to public sources
3. **Industry-standard methodology** — properly attributed inline

## Cross-references to other experts

Some references cross-link to `references/*.md` in other movie-experts experts (e.g., `../../compliance_marketing/SKILL.md`, `../../_shared/quality-rubric.md`). Those files have their own LICENSE.md — refer to them for their respective attribution.

## Code

The creative_source expert itself contains no code (per PROJECT.md "pure markdown" constraint). Eval harness code at the suite level (`_eval/runner.py`) is MIT licensed per the root README.

## Questions

For licensing questions or to report a fair-use concern, contact the Hermes Agent project maintainers.
