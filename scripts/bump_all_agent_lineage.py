#!/usr/bin/env python3
"""XCUT-05-AUTO — automate the full 15-agent lineage bump.

One-shot CLI that wraps ``transform_skill_to_agent.py`` for Track A (the 9
EXPERTS_9 experts the base script knows how to transform) and handles
Track B (the 6 v13.0 P62 manual cases the base script does NOT know
about) with the same field-mapping rules but per-expert persona / tools /
transform-notes overrides.

Reads (read-only — Phase 48 + Phase 49 lineage invariants L1-L6):
  /data/workspace/kais-hermes-skills/skills/movie-experts/<name>/SKILL.md

Writes (operator-owned production path):
  ~/.hermes/agents/<name>.agent.yaml

Validation:
  Each of the 15 emitted YAMLs is round-tripped through
  ``agent.registry_loader.load_one_agent_yaml`` to verify schema +
  filename-stem invariant. The script exits 0 only when all 15 bump +
  validate; exit 1 on partial success (some experts failed — operator
  reviews the per-expert log lines).

Two-track design
----------------
- **Track A (9 experts):** ``screenplay, cinematographer, hook_retention,
  theory_critic, editor, character_designer, continuity_auditor,
  audio_pipeline, style_genome`` — handled by ``transform_one`` in the
  base script. The bump script delegates to that proven function and only
  adds the write + validate step.
- **Track B (6 experts):** ``animation_studio, colorist,
  documentary_maker, performer, storyboard_designer, visual_executor`` —
  NOT in EXPERTS_9. These were hand-crafted in v13.0 P62. The bump script
  regenerates them using ``transform_track_b_one`` (mirrors transform_one
  but with Track-B-specific persona / tools / transform-notes + a broader
  related-agents filter that preserves the existing collaboration graph).

Track B related-agents preservation
-----------------------------------
The v13.0 P62 Track B YAMLs preserved ``related_skills`` from source
SKILL.md verbatim — they did NOT apply ``LEGACY_NAME_MAP`` canonicalization
(so ``scene_builder`` survives as-is) and they did NOT filter to a narrow
panel (so non-expert agent peers like ``compliance_gate``, ``production``,
``prompt_injector`` survive). ``_filter_related_agents_track_b`` preserves
that behavior: canonicalization is skipped, the filter panel includes
ACTIVE_EXPERTS_15 + the 3 non-expert agent peers, and deduplication
preserves source ordering.

CLAUDE.md compliance
--------------------
- ``from __future__ import annotations`` at top
- ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514)
- ``get_hermes_home()`` from ``hermes_constants`` (NEVER ``Path.home()``)
- Lazy %-formatting in log calls
- ``except X as exc:`` with bound name; preserve chains via ``raise ... from exc``
"""

from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# Make the agent.* + transform_skill_to_agent imports resolvable when this
# script is invoked directly via ``python scripts/bump_all_agent_lineage.py``
# (no installed package — mirrors transform_skill_to_agent.py:52-54).
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
# scripts/ itself must be on sys.path so we can import transform_skill_to_agent.
_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from agent.registry_loader import (  # noqa: E402  (after sys.path insert)
    RegistryValidationError,
    load_one_agent_yaml,
)
from agent.skill_utils import parse_frontmatter  # noqa: E402
from hermes_constants import get_hermes_home  # noqa: E402

# Track A infrastructure — reuse the proven base script (do NOT duplicate).
from transform_skill_to_agent import (  # noqa: E402
    EXPERTS_9,
    KIAS_SKILLS_ROOT,
    _TAG_PATTERN,
    _compute_skill_sha256,
    _emit_yaml,
    _get_list,
    transform_one,
)

logger = logging.getLogger("bump_all_agent_lineage")

# --------------------------------------------------------------------------- #
# Constants — the 15 active experts split into Track A + Track B
# --------------------------------------------------------------------------- #

#: Track A — the 9 experts handled by transform_skill_to_agent.transform_one.
#: Equal to EXPERTS_9 from the base script. Listed explicitly for operator
#: traceability (the two sub-lists are the canonical operator-facing view).
TRACK_A_EXPERTS: list[str] = list(EXPERTS_9)

#: Track B — the 6 experts NOT in EXPERTS_9. These were hand-crafted in
#: v13.0 P62 and have per-expert persona / tools / transform-notes that
#: the base script does not know about. The bump script regenerates them
#: via transform_track_b_one.
TRACK_B_EXPERTS: list[str] = [
    "animation_studio",
    "colorist",
    "documentary_maker",
    "performer",
    "storyboard_designer",
    "visual_executor",
]

#: The full 15-expert active set. Track A (9) + Track B (6). Hardcoded +
#: explicit per CONTEXT.md D-03 (auto-detect is v16+ scope).
ACTIVE_EXPERTS_15: list[str] = TRACK_A_EXPERTS + TRACK_B_EXPERTS

#: Per-expert tools whitelist for Track B. Source: the existing
#: ``~/.hermes/agents/<name>.agent.yaml`` files (v13.0 P62 / v14.0 P75).
#: These differ from the plan's <interfaces> block, which was stale —
#: the existing YAMLs are the ground truth (Rule 1 auto-fix).
TRACK_B_TOOLS: dict[str, list[str]] = {
    "animation_studio": ["hermes_llm", "read_file", "search_files"],
    "colorist": ["hermes_llm", "read_file", "search_files", "write_file"],
    "documentary_maker": ["hermes_llm", "read_file", "search_files"],
    "performer": ["hermes_llm", "read_file", "search_files"],
    "storyboard_designer": ["hermes_llm", "read_file", "search_files"],
    "visual_executor": [
        "hermes_llm",
        "hermes_llm_vision",
        "dreamina_cli",
        "read_file",
        "write_file",
        "patch",
    ],
}

#: Related-agents filter panel for Track B. Broader than ACTIVE_EXPERTS_15:
#: the existing v13.0 P62 Track B YAMLs reference 3 non-expert agent peers
#: (compliance_gate, production, prompt_injector) in their related_agents
#: arrays, and the collaboration graph must be preserved. The panel also
#: includes ACTIVE_EXPERTS_15 itself. Legacy name canonicalization is NOT
#: applied (so ``scene_builder`` survives verbatim — matches existing YAMLs).
TRACK_B_PANEL: frozenset[str] = frozenset(
    ACTIVE_EXPERTS_15
    + ["compliance_gate", "production", "prompt_injector", "scene_builder"]
)

#: Per-expert transform notes for Track B. Each notes string cites 1-2
#: key frameworks from the existing agent.yaml + the v15.0 Phase 82
#: automation provenance. Pattern mirrors transform_skill_to_agent's
#: ``_transform_notes`` table.
TRACK_B_TRANSFORM_NOTES: dict[str, str] = {
    "animation_studio": (
        "Persona rewritten from SKILL body; Disney 4-stage system + "
        "12-stage pipeline + cross-cultural (花木兰 hero-journey case) "
        "surfaced. Analysis-only tools — advisory/expert-knowledge output. "
        "v15.0 Phase 82 bump_all_agent_lineage.py automated transform "
        "(Track B)."
    ),
    "colorist": (
        "Persona rewritten from SKILL body; CxSxZ 3D color intent (Chroma × "
        "Saturation × Brightness, 28 core combinations) + Bellantoni 8-color "
        "vocabulary + Hurkman digital pipeline + cross-cultural CN-audience "
        "divergence surfaced. +write_file load-bearing for LUT plan artifacts. "
        "v15.0 Phase 82 bump_all_agent_lineage.py automated transform "
        "(Track B). | v14.0 P75 lineage bump baseline."
    ),
    "documentary_maker": (
        "Persona rewritten from SKILL body; 6 documentary types (Bill Nichols) "
        "+ 4 schools (Flaherty / Vertov / Grierson / Direct-Vérité) + "
        "ethnographic methods surfaced. Analysis-only tools. v15.0 Phase 82 "
        "bump_all_agent_lineage.py automated transform (Track B)."
    ),
    "performer": (
        "Persona rewritten from SKILL body; Performance-4D matrix (ExBxSxP) + "
        "Stanislavski ExB + Laban Effort + Meisner truth-of-moment surfaced. "
        "CONTEXT.md reactivates performer as an active agent (overriding "
        "source SKILL deprecated:true from Phase 17). Analysis-only tools. "
        "v15.0 Phase 82 bump_all_agent_lineage.py automated transform (Track B)."
    ),
    "storyboard_designer": (
        "Persona rewritten from SKILL body; shot decomposition + 4D anchoring "
        "(depth / identity / lighting / temporal) + decoupling from "
        "cinematographer (rules vs application) surfaced. CONTEXT.md reactivates "
        "storyboard_designer as an independent agent (overriding source SKILL "
        "deprecated:true from Phase 17). Analysis-only tools. v15.0 Phase 82 "
        "bump_all_agent_lineage.py automated transform (Track B)."
    ),
    "visual_executor": (
        "Persona rewritten from SKILL body; 2-sub-step visual production chain "
        "(drawer FLUX 2 Klein 9B + animator 2026 video-gen catalog) + "
        "intra-expert drawer→animator handoff (Phase 14 MERGE-01) + "
        "intent-vs-execution split surfaced. +dreamina_cli + write_file + patch "
        "load-bearing for sub-step iteration. v15.0 Phase 82 "
        "bump_all_agent_lineage.py automated transform (Track B). | v14.0 P75 "
        "lineage bump baseline."
    ),
}


# --------------------------------------------------------------------------- #
# Track B persona builders
# --------------------------------------------------------------------------- #
# Each builder returns a first-person SYSTEM-prompt fragment citing the
# load-bearing frameworks from the source SKILL body. Content adapted from
# the existing v13.0 P62 / v14.0 P75 agent.yaml persona fields so the bump
# script regenerates them faithfully.
# --------------------------------------------------------------------------- #


def _persona_animation_studio(_body: str) -> str:
    return (
        "I am the Animation Studio Expert (动画制片专家). I orchestrate the "
        "Disney 4-stage system (early-animation / feature-animation / "
        "live-action-hybrid / magic-kingdom-3D) and the 12-stage animation "
        "production pipeline (story-pitch → development → treatment → "
        "storyboard → dialogue → pitch-reel → visual-dev → rough-animation → "
        "clean-up → color/composite → final-pix → delivery) for 2D / 3D / "
        "stop-motion workflows. My Story Structure Score metric catches "
        "structural regressions before story-pitch locks. Cross-cultural "
        "adaptation is my specialty — the 花木兰 hero-journey case (folk tale "
        "→ global animation) is the canonical pattern I apply: honor the "
        "source mytheme while reshaping hero-arc beats for a mainstream "
        "audience. I defer to visual_executor on execution (character design "
        "+ concept art + animation rendering), to colorist on the color "
        "script, and to audio_pipeline on musical storytelling (composer "
        "sub-step) and voice casting for animation (voicer sub-step). I am "
        "advisory — I surface structural / methodological concerns to "
        "screenplay and the broader pipeline."
    )


def _persona_colorist(_body: str) -> str:
    return (
        "I am the Colorist Expert (色彩专家). I produce the CxSxZ 3D color "
        "intent (Chroma × Saturation × Brightness) with 28 core high-"
        "frequency combinations ensuring color language serves narrative "
        "emotion across every shot. My output is a color_intent.json + LUT "
        "plan (lift/gamma/gain curves) consumed by visual_executor at Step 7 "
        "of the V8.6 pipeline — I integrate with visual_executor at Step 7 "
        "for the 视觉种子+风格化 atomic operation. Cross-shot ΔE2000 ≤ 3.0 "
        "(production) is my quality gate. My theoretical backbone is the "
        "Bellantoni 8-color vocabulary (the emotional palette), Hurkman "
        "digital color pipeline (node-graph + ACES color space), and cross-"
        "cultural CN-audience color divergence (CN audiences read "
        "red/jade/gold differently than Western emotional mappings). I defer "
        "to style_genome on the 5D vector (D1 color dimension is "
        "style_genome's jurisdiction — I operationalize, I do not redefine "
        "the vector). My color_intent_match + color_cross_shot_consistency + "
        "style_fidelity metrics gate color discipline."
    )


def _persona_documentary_maker(_body: str) -> str:
    return (
        "I am the Documentary Maker Expert (纪录片创作专家). I apply the 6 "
        "documentary types per Bill Nichols (poetic / expository / "
        "observational / participatory / reflexive / performative) and the 4 "
        "documentary schools (Flaherty romantic-tradition / Vertov kino-eye "
        "/ Grierson creative-treatment-of-actuality / Direct-Vérité "
        "observational-trust) as my theoretical backbone. My ethnographic "
        "methods — sustained observation, long-form fieldwork, interview "
        "ethics (informed consent + representation care) — ground "
        "documentary-style 短剧 / 微电影 in observed reality rather than "
        "invented narrative. I am advisory (NOT a hard gate) — I surface "
        "documentary-craft concerns to screenplay (narrative structure), "
        "cinematographer (verité camera work), and editor (documentary "
        "editing rhythm). My metrics — authenticity_score, "
        "ethical_compliance, narrative_arc_quality, observational_rigor — "
        "validate documentary discipline without blocking production."
    )


def _persona_performer(_body: str) -> str:
    return (
        "I am the Performer Expert (表演/动作专家). I define character action "
        "and emotion via the Performance-4D matrix (Emotion × Body × Space × "
        "Pace parametric dispatch) backed by Stanislavski ExB (Emotion×Body "
        "psycho-physical unity), Laban Effort (weight/space/time/flow "
        "movement analysis), and Meisner truth-of-moment technique "
        "(impulse→action without premeditation). My emotion_accuracy metric "
        "validates that character action matches the emotional intent from "
        "screenplay; movement_naturalness + body_consistency metrics gate "
        "cross-shot physical continuity. I defer to character_designer on "
        "identity contracts (L1-L4 layered specs — character_designer owns "
        "who the character IS; I own what the character DOES) and to "
        "screenplay on dialogue subtext (screenplay owns what characters SAY; "
        "I own how they emote through the saying). CONTEXT.md locked decision "
        "reactivates performer as an active agent (overriding source SKILL "
        "deprecated:true status from Phase 17) — my Performance-4D + "
        "Stanislavski + Laban + Meisner content remains distinct from "
        "character_designer's identity-contract layer."
    )


def _persona_storyboard_designer(_body: str) -> str:
    return (
        "I am the Storyboard Designer Expert (分镜设计师). I decompose "
        "screenplay scenes into per-shot Storyboard JSON with camera params, "
        "action, duration, reference image pointers, and 4D anchoring (depth "
        "/ identity / lighting / temporal). I am DECOUPLED from "
        "cinematographer — cinematographer defines the shot-grammar RULES "
        "(axis, framing, camera moves); I APPLY those rules to produce the "
        "executable shot list. My axis_compliance_rate metric validates that "
        "my storyboard obeys cinematographer's axis rules. [CONTEXT.md "
        "reactivates storyboard_designer as an independent agent — source "
        "SKILL deprecated:true status from Phase 17 overridden.]"
    )


def _persona_visual_executor(_body: str) -> str:
    return (
        "I am the Visual Executor Expert (视觉执行专家). I orchestrate the "
        "2-sub-step visual production chain atomically: drawer (FLUX 2 Klein "
        "9B cinematic still image generation + LoRA + IP-Adapter + InstantID "
        "for character consistency + first-frame I-frames), animator (2026 "
        "Hermes-catalog video gen models — veo3.1 / kling-v3-4k / pixverse-v6 "
        "/ ltx-2.3 / seedance-2.0 — for camera motion + temporal consistency, "
        "consuming drawer's first_frame as I-frame input). My sub-steps are "
        "ATOMIC — the drawer→animator handoff is now an INTRA-expert handoff "
        "(same expert_id visual_executor), eliminating the consistency-"
        "context drift of v1's inter-expert edge (Phase 14 MERGE-01). I do "
        "NOT decide intent — cinematographer's job; I EXECUTE given intent "
        "via dreamina CLI (text2image / image2image / multimodal2video). My "
        "aesthetic_score + character_consistency + temporal_consistency "
        "metrics gate visual quality. Intent-vs-execution split is load-"
        "bearing — I refuse to second-guess cinematographer's shot intent."
    )


_TRACK_B_PERSONA_BUILDERS: dict[str, Any] = {
    "animation_studio": _persona_animation_studio,
    "colorist": _persona_colorist,
    "documentary_maker": _persona_documentary_maker,
    "performer": _persona_performer,
    "storyboard_designer": _persona_storyboard_designer,
    "visual_executor": _persona_visual_executor,
}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def transform_track_b_one(expert_name: str, skill_md_path: Path) -> dict[str, Any]:
    """Transform one Track B SKILL.md into the agent YAML dict (in-memory).

    Mirrors ``transform_skill_to_agent.transform_one`` but with Track-B-
    specific persona / tools / transform-notes and a broader related-agents
    filter that preserves the existing v13.0 P62 collaboration graph
    (non-expert agent peers + legacy names like ``scene_builder`` survive).

    Pure function — does NOT write to disk.

    Args:
        expert_name: One of ``TRACK_B_EXPERTS``.
        skill_md_path: Absolute path to the source ``SKILL.md`` file.

    Returns:
        Dict matching agents-schema.yaml's 18-field shape.

    Raises:
        FileNotFoundError: if ``skill_md_path`` does not exist.
        KeyError: if the SKILL frontmatter is malformed (missing
            ``metadata.hermes`` block) or ``expert_name`` is not a
            known Track B expert.
    """
    content = skill_md_path.read_text(encoding="utf-8")
    skill_sha = _compute_skill_sha256(content)
    frontmatter, body = parse_frontmatter(content)

    meta = frontmatter.get("metadata", {}).get("hermes", {})
    if not meta:
        raise KeyError(
            f"{skill_md_path}: frontmatter missing metadata.hermes block — "
            "transform requires tags / related_skills / expert_id / metrics"
        )

    related_agents = _filter_related_agents_track_b(_get_list(meta, "related_skills"))
    persona = _build_track_b_persona(expert_name, body)
    transform_notes = TRACK_B_TRANSFORM_NOTES.get(expert_name, "")
    if not transform_notes:
        raise KeyError(
            f"no Track B transform notes entry for {expert_name!r} — "
            "TRACK_B_TRANSFORM_NOTES drift?"
        )

    # Filter tags to agents-schema.yaml §2.9 pattern (lowercase-hyphenated).
    raw_tags = _get_list(meta, "tags")
    filtered_tags = [
        t for t in raw_tags if isinstance(t, str) and _TAG_PATTERN.fullmatch(t)
    ]

    data: dict[str, Any] = {
        # §2.1 — Identity
        "name": expert_name,
        "description": frontmatter.get("description", ""),
        "version": "1.0.0",
        # §2.4 — Persona (Track-B-specific first-person rewrite)
        "persona": persona,
        # §2.5 — Tools (Track-B-specific whitelist)
        "tools": list(TRACK_B_TOOLS[expert_name]),
        # §2.6 — Memory scope (uniform per_agent per §2.17)
        "memory_scope": "per_agent",
        # §2.7 — Lineage
        "lineage": {
            "derived_from_skill_id": meta.get("expert_id", expert_name),
            "derived_from_repo": "kais-hermes-skills",
            "transform_date": date.today().isoformat(),
            "transform_notes": transform_notes,
            "skill_sha256": skill_sha,
        },
        # §2.8 — RAG refs (empty array default)
        "refs": [],
        # §2.9 — Tags (filtered to schema pattern)
        "tags": filtered_tags,
        # §2.10 — expert_id (FOUND-08 verbatim copy)
        "expert_id": meta.get("expert_id", expert_name),
        # §2.11 — Metrics (carried verbatim)
        "metrics": _get_list(meta, "metrics"),
        # §2.12 — Prerequisites
        "prerequisites": frontmatter.get("prerequisites", {}),
        # §2.13 — Related agents (Track B broader filter)
        "related_agents": related_agents,
        # §2.14 — Evolution log (curator-managed; empty at transform time)
        "evolution_log": [],
        # §2.15 — Fitness score (null cold-start per OQ-4)
        "fitness_score": None,
        # §2.16 — Platforms (OS gate)
        "platforms": frontmatter.get(
            "platforms", ["linux", "macos", "windows"]
        ),
        # §2.17 — Round table eligible (default true)
        "round_table_eligible": True,
        # §2.18 — Default invocation mode
        "default_invocation": "mcp_tool",
    }
    return data


def _filter_related_agents_track_b(related_skills: list[Any]) -> list[str]:
    """Filter related_agents for Track B — preserve existing collaboration graph.

    The v13.0 P62 Track B YAMLs preserved ``related_skills`` from source
    SKILL.md verbatim — they did NOT apply ``LEGACY_NAME_MAP``
    canonicalization (so ``scene_builder`` survives) and they did NOT
    filter to a narrow 9-agent panel (so non-expert agent peers like
    ``compliance_gate``, ``production``, ``prompt_injector`` survive).

    This helper replicates that behavior: no canonicalization, filter to
    ``TRACK_B_PANEL`` (15 active experts + 3 non-expert peers + the legacy
    ``scene_builder`` name), deduplicate while preserving source ordering.

    Args:
        related_skills: the raw ``metadata.hermes.related_skills`` list.

    Returns:
        Deduplicated list of related agent names in source order.
    """
    if not isinstance(related_skills, list):
        logger.warning(
            "_filter_related_agents_track_b: expected list, got %s",
            type(related_skills).__name__,
        )
        return []
    seen: set[str] = set()
    result: list[str] = []
    for name in related_skills:
        if not isinstance(name, str):
            logger.warning(
                "_filter_related_agents_track_b: skipping non-string entry %r",
                name,
            )
            continue
        if name in TRACK_B_PANEL and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def _build_track_b_persona(expert_name: str, body: str) -> str:
    """Build first-person persona fragment for a Track B expert.

    Falls back to a generic first-person identity if no specific builder
    exists (defensive — all 6 Track B experts have builders, but future
    additions may not).
    """
    builder = _TRACK_B_PERSONA_BUILDERS.get(expert_name)
    if builder is None:
        return (
            f"I am the {expert_name.replace('_', ' ')} expert. "
            f"I operate as a Hermes-native agent with per-agent memory scope, "
            f"consulting my SKILL lineage as fallback when needed. "
            f"My runtime tool whitelist is fixed by my agent YAML."
        )
    return builder(body)


# --------------------------------------------------------------------------- #
# Track A / Track B bump orchestration
# --------------------------------------------------------------------------- #


def bump_track_a() -> dict[str, bool]:
    """Bump all Track A (EXPERTS_9) agent YAMLs via the base transform.

    For each expert in ``TRACK_A_EXPERTS``: read the source SKILL.md,
    call ``transform_one``, write via ``_emit_yaml`` to
    ``~/.hermes/agents/<name>.agent.yaml``. Missing SKILL.md files are
    logged and skipped (partial success).

    Returns:
        Dict ``{expert_name: True/False}`` — True if the YAML was
        successfully written, False on any failure.
    """
    agents_dir = get_hermes_home() / "agents"
    results: dict[str, bool] = {}
    for expert in TRACK_A_EXPERTS:
        skill_path = KIAS_SKILLS_ROOT / expert / "SKILL.md"
        if not skill_path.exists():
            logger.warning(
                "Track A SKIP %s: source missing at %s", expert, skill_path
            )
            results[expert] = False
            continue
        try:
            data = transform_one(expert, skill_path)
            target = agents_dir / f"{expert}.agent.yaml"
            _emit_yaml(target, data)
            logger.info("Track A OK %s -> %s", expert, target.name)
            results[expert] = True
        except (KeyError, ValueError, OSError) as exc:
            logger.error("Track A FAIL %s: %s", expert, exc)
            results[expert] = False
    return results


def bump_track_b() -> dict[str, bool]:
    """Bump all Track B (6 manual-case) agent YAMLs.

    For each expert in ``TRACK_B_EXPERTS``: read the source SKILL.md,
    call ``transform_track_b_one``, write via ``_emit_yaml``. Missing
    SKILL.md files or transform failures are logged and the script
    continues to the next expert (partial success).

    Returns:
        Dict ``{expert_name: True/False}`` — True if successfully written.
    """
    agents_dir = get_hermes_home() / "agents"
    results: dict[str, bool] = {}
    for expert in TRACK_B_EXPERTS:
        skill_path = KIAS_SKILLS_ROOT / expert / "SKILL.md"
        if not skill_path.exists():
            logger.warning(
                "Track B SKIP %s: source missing at %s", expert, skill_path
            )
            results[expert] = False
            continue
        try:
            data = transform_track_b_one(expert, skill_path)
            target = agents_dir / f"{expert}.agent.yaml"
            _emit_yaml(target, data)
            logger.info("Track B OK %s -> %s", expert, target.name)
            results[expert] = True
        except (KeyError, ValueError, OSError) as exc:
            logger.error("Track B FAIL %s: %s", expert, exc)
            results[expert] = False
    return results


def validate_all(results: dict[str, bool]) -> tuple[int, int]:
    """Validate every successfully-bumped YAML via ``load_one_agent_yaml``.

    Args:
        results: the merged ``{expert: bumped?}`` dict from bump_track_a +
            bump_track_b. Only experts that were successfully bumped
            (``True``) are validated.

    Returns:
        Tuple ``(success_count, failure_count)``. ``success_count`` is the
        number of YAMLs that passed validation; ``failure_count`` is the
        number that failed. ``success_count + failure_count`` equals the
        number of experts that were successfully bumped.
    """
    agents_dir = get_hermes_home() / "agents"
    success = 0
    failure = 0
    for expert, bumped in results.items():
        if not bumped:
            continue
        target = agents_dir / f"{expert}.agent.yaml"
        try:
            load_one_agent_yaml(target)
            logger.info("VALIDATE OK %s", target.name)
            success += 1
        except RegistryValidationError as exc:
            logger.error("VALIDATE FAIL %s: %s", target, exc)
            failure += 1
    return success, failure


def main() -> int:
    """CLI entrypoint — bump all 15 agent YAMLs + validate.

    Returns:
        0 on full success (all 15 bumped + validated).
        1 on partial success (some experts failed — operator reviews logs).
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    agents_dir = get_hermes_home() / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    logger.info("target agents dir: %s", agents_dir)

    # --- Track A ---
    logger.info("=== Track A (9 EXPERTS_9) ===")
    results_a = bump_track_a()
    bumped_a = sum(1 for v in results_a.values() if v)
    logger.info("Track A: %d/9 bumped", bumped_a)

    # --- Track B ---
    logger.info("=== Track B (6 manual-case experts) ===")
    results_b = bump_track_b()
    bumped_b = sum(1 for v in results_b.values() if v)
    logger.info("Track B: %d/6 bumped", bumped_b)

    # --- Merge + validate ---
    results = {**results_a, **results_b}
    total_bumped = sum(1 for v in results.values() if v)
    logger.info("=== Validation ===")
    valid_count, invalid_count = validate_all(results)

    # --- Summary report ---
    print()
    print("=" * 60)
    print(f"Bump summary: {total_bumped}/15 bumped "
          f"(Track A {bumped_a}/9, Track B {bumped_b}/6)")
    print(f"Validation:   {valid_count} passed, {invalid_count} failed")
    if total_bumped < 15:
        failed = [name for name, ok in results.items() if not ok]
        print(f"Bump failures: {', '.join(sorted(failed))}")
    if invalid_count:
        print(f"Validation failures: {invalid_count} YAML(s) failed schema check")
    print("=" * 60)

    # Exit 0 only on full success.
    if total_bumped == 15 and invalid_count == 0:
        logger.info("FULL SUCCESS — all 15 agents bumped + validated")
        return 0
    logger.error(
        "PARTIAL SUCCESS — %d bumped, %d validated, %d failed",
        total_bumped,
        valid_count,
        15 - total_bumped + invalid_count,
    )
    return 1


if __name__ == "__main__":
    sys.exit(main())
