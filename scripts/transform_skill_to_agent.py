#!/usr/bin/env python3
"""MIGR-01 — transform 9 sample movie-expert SKILL.md → agent YAMLs.

One-shot CLI invoked by the operator (per CONTEXT.md "Claude's Discretion"
point 2 + RESEARCH anti-pattern "Auto-re-transform on SHA-256 drift").

Reads (read-only — Phase 48 + Phase 49 lineage invariants L1-L6):
  /data/workspace/kais-hermes-skills/skills/movie-experts/<name>/SKILL.md

Writes (operator-owned production path):
  ~/.hermes/agents/<name>.agent.yaml

Validation:
  Each emitted YAML is round-tripped through
  ``agent.registry_loader.load_one_agent_yaml`` to verify the schema +
  filename-stem invariant. If any YAML fails, the script exits non-zero
  and emits a diagnostic (does NOT silently emit invalid YAMLs).

Field-mapping rules: Phase 49 §2 75-cell table (5 fields × 15 experts;
subset of 9 applies per CONTEXT.md decision #1). Per-expert edge cases
live in ``_transform_notes`` + ``_build_persona_*`` + ``_tools_for``.

HOOK-09 invariant (Phase 49 §2.4 + 05-POC-PLAN.md §3.2):
  ``screenplay.agent.yaml`` ``lineage.transform_notes`` MUST contain the
  literal substring ``HOOK-09 emotion_curve marker arrays remain
  contract-load-bearing``. Downstream storyboard Step 6.5 + visual_executor
  Step 7 cannot consume screenplay output otherwise.

CLAUDE.md compliance
--------------------
- ``from __future__ import annotations`` at top
- ``encoding="utf-8"`` on every ``open()`` (Ruff PLW1514)
- ``get_hermes_home()`` from ``hermes_constants`` (NEVER ``Path.home()``)
- Lazy %-formatting in log calls
- ``except X as exc:`` with bound name; preserve chains via ``raise ... from exc``
"""

from __future__ import annotations

import hashlib
import json
import logging
import sys
from datetime import date
from pathlib import Path
from typing import Any

import yaml

# Make the agent.* imports resolvable when this script is invoked directly
# via ``python scripts/transform_skill_to_agent.py`` (no installed package).
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from agent.registry_loader import (  # noqa: E402  (after sys.path insert)
    RegistryValidationError,
    load_one_agent_yaml,
)
from agent.skill_utils import parse_frontmatter  # noqa: E402
from hermes_constants import get_hermes_home  # noqa: E402

logger = logging.getLogger("transform_skill_to_agent")

# --------------------------------------------------------------------------- #
# Constants — Phase 49 §2 75-cell table subset for the 9-agent PoC
# --------------------------------------------------------------------------- #

#: The 9-agent subset per CONTEXT.md decision #1. Maps to v3.0+ canonical
#: names (avoids FOUND-08 risk of resurrecting deprecated scene_builder /
#: continuity / performer / composer).
EXPERTS_9: list[str] = [
    "screenplay",
    "cinematographer",
    "hook_retention",
    "theory_critic",
    "editor",
    "character_designer",
    "continuity_auditor",
    "audio_pipeline",
    "style_genome",
]

#: Set form of EXPERTS_9 for fast membership tests in _filter_related_agents.
PANEL_9: frozenset[str] = frozenset(EXPERTS_9)

#: Legacy-name → v3.0+ canonical name mapping (Phase 49 §2.18 + §2.19,
#: RESEARCH Pattern 1b). Used to canonicalize ``related_skills`` arrays
#: that still reference pre-v3.0 names in source SKILLs.
LEGACY_NAME_MAP: dict[str, str] = {
    "scene_builder": "cinematographer",  # absorbed in Phase 17
    "continuity": "continuity_auditor",  # renamed in v3.0+
    "performer": "character_designer",  # CONTEXT.md decision #1 rename
    "composer": "audio_pipeline",  # CONTEXT.md decision #1 rename
}

#: Read-only source path (operator-owned repo, see A1 in 53-RESEARCH.md).
KIAS_SKILLS_ROOT = Path("/data/workspace/kais-hermes-skills/skills/movie-experts")

#: Default platforms list (mirrors source SKILL.md default; OS gate is
#: enforced identically to skill_utils.skill_matches_platform).
_DEFAULT_PLATFORMS = ["linux", "macos", "windows"]

#: Regex matching the agents-schema.yaml §2.9 ``tags`` item pattern
#: ``^[a-z0-9-]+$``. Source SKILL.md ``metadata.hermes.tags`` arrays
#: sometimes include non-ASCII tags (e.g. cinematographer lists `镜头语言`);
#: the schema rejects these, so the transform MUST filter them out.
#: We import the compiled regex lazily to keep the module top-level clean.
import re as _re
_TAG_PATTERN = _re.compile(r"^[a-z0-9-]+$")
del _re

#: Per Phase 49 §2.x default tools whitelist. Screenplay carries
#: ``write_file`` + ``patch`` so it can emit Step 3 JSON artifacts
#: (HOOK-09 contract); character_designer + audio_pipeline add write/file
#: tools for actual asset writing; the remaining 6 are analysis-only.
_TOOLS_TABLE: dict[str, list[str]] = {
    "screenplay": ["hermes_llm", "read_file", "search_files", "write_file", "patch"],
    "cinematographer": ["hermes_llm", "read_file", "search_files"],
    "hook_retention": ["hermes_llm", "read_file", "search_files"],
    "theory_critic": ["hermes_llm", "read_file", "search_files"],
    "editor": ["hermes_llm", "read_file", "search_files"],
    "character_designer": ["hermes_llm", "read_file", "write_file"],
    "continuity_auditor": ["hermes_llm", "read_file", "search_files"],
    "audio_pipeline": ["hermes_llm", "dreamina_cli", "read_file", "write_file"],
    "style_genome": ["hermes_llm", "read_file", "search_files"],
}


# --------------------------------------------------------------------------- #
# Public API
# --------------------------------------------------------------------------- #


def transform_one(expert_name: str, skill_md_path: Path) -> dict[str, Any]:
    """Transform one SKILL.md into the agent YAML dict (in-memory).

    Pure function — does NOT write to disk. The CLI ``__main__`` block
    handles the write step (and the post-write validation).

    Args:
        expert_name: One of ``EXPERTS_9``.
        skill_md_path: Absolute path to the source ``SKILL.md`` file.

    Returns:
        Dict matching agents-schema.yaml's 18-field shape. The ``name``
        field equals ``expert_name`` so the filename-stem invariant
        (T-52-03) holds when the caller writes it as
        ``{expert_name}.agent.yaml``.

    Raises:
        FileNotFoundError: if ``skill_md_path`` does not exist.
        KeyError: if the SKILL frontmatter is malformed (missing
            ``metadata.hermes`` block).
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

    related_agents = _filter_related_agents(_get_list(meta, "related_skills"))
    persona = _build_persona(expert_name, body)
    transform_notes = _transform_notes(expert_name)
    # Filter tags to agents-schema.yaml §2.9 pattern (lowercase-hyphenated).
    # Source SKILLs occasionally include non-ASCII tags (e.g. cinematographer
    # lists `镜头语言`); schema rejects these, so filter rather than fail.
    # CR-03: use _get_list to coerce ``tags:`` (empty value) → [] rather
    # than the None that ``meta.get('tags', [])`` would return (the default
    # is only used when the key is ABSENT, not when it's present-with-None).
    raw_tags = _get_list(meta, "tags")
    filtered_tags = [t for t in raw_tags if isinstance(t, str) and _TAG_PATTERN.fullmatch(t)]

    data: dict[str, Any] = {
        # §2.1 — Identity
        "name": expert_name,
        "description": frontmatter.get("description", ""),
        "version": "1.0.0",  # agent YAML schema version, NOT SKILL version
        # §2.4 — Persona (NEW — must rewrite from SKILL body)
        "persona": persona,
        # §2.5 — Tools (runtime whitelist, per Phase 49 §2.x)
        "tools": _tools_for(expert_name),
        # §2.6 — Memory scope (uniform per_agent per §2.17)
        "memory_scope": "per_agent",
        # §2.7 — Lineage (operator-owned provenance)
        "lineage": {
            "derived_from_skill_id": meta.get("expert_id", expert_name),
            "derived_from_repo": "kais-hermes-skills",
            "transform_date": date.today().isoformat(),  # WR-04: not hardcoded
            "transform_notes": transform_notes,
            "skill_sha256": skill_sha,
        },
        # §2.8 — RAG refs (empty array default; SKILL body has these but
        # Phase 53 PoC leaves RAG wiring to a later phase)
        "refs": [],
        # §2.9 — Tags (filtered to schema pattern; source SKILLs may carry
        # non-ASCII tags like `镜头语言` which the schema rejects)
        "tags": filtered_tags,
        # §2.10 — expert_id (FOUND-08 verbatim copy)
        "expert_id": meta.get("expert_id", expert_name),
        # §2.11 — Metrics (carried verbatim for eval gate continuity)
        # CR-03: use _get_list to handle ``metrics:`` present-with-None.
        "metrics": _get_list(meta, "metrics"),
        # §2.12 — Prerequisites (activation conditions, NOT runtime tools)
        "prerequisites": frontmatter.get("prerequisites", {}),
        # §2.13 — Related agents (collaboration DAG, legacy names canonicalized)
        "related_agents": related_agents,
        # §2.14 — Evolution log (curator-managed; empty at transform time)
        "evolution_log": [],
        # §2.15 — Fitness score (null cold-start per OQ-4)
        "fitness_score": None,
        # §2.16 — Platforms (OS gate)
        "platforms": frontmatter.get("platforms", _DEFAULT_PLATFORMS),
        # §2.17 — Round table eligible (default true)
        "round_table_eligible": True,
        # §2.18 — Default invocation mode (mcp_tool for v11.0 PoC)
        "default_invocation": "mcp_tool",
    }
    return data


# --------------------------------------------------------------------------- #
# Internal helpers
# --------------------------------------------------------------------------- #


def _compute_skill_sha256(content: str) -> str:
    """SHA-256 of LF-normalized SKILL.md content (Phase 49 §2.1 edge case).

    Per RESEARCH Pitfall 7: CRLF checkouts on Windows would produce a
    different hash than CI's LF hash, triggering phantom drift in
    curator's later detection pass. Normalize before hashing.
    """
    lf_content = content.replace("\r\n", "\n")
    return hashlib.sha256(lf_content.encode("utf-8")).hexdigest()


def _get_list(d: dict[str, Any], key: str) -> list[Any]:
    """Read ``key`` from ``d`` as a list, handling missing AND None values.

    CR-03 fix: ``dict.get(key, default)`` returns ``None`` when the key is
    present with an empty value (e.g. frontmatter ``related_skills:``
    with nothing after the colon — ``yaml.safe_load`` parses this as
    ``None``). The list-comprehension consumers downstream then raise
    ``TypeError: 'NoneType' object is not iterable``. The ``or []``
    idiom handles both the missing-key case and the present-with-None
    case uniformly.
    """
    v = d.get(key)
    return v if isinstance(v, list) else []


def _filter_related_agents(related_skills: list[Any]) -> list[str]:
    """Canonicalize legacy names + filter to the 9-agent panel subset.

    Per RESEARCH Pattern 1b: ``related_skills`` in source SKILLs may list
    pre-v3.0 names (``scene_builder``, ``continuity``, ``performer``,
    ``composer``). Map to v3.0+ canonical via ``LEGACY_NAME_MAP``, then
    filter to ``PANEL_9`` so non-panel peers (animation_studio,
    documentary_maker, visual_executor, colorist, compliance_gate,
    production, prompt_injector) don't leak in. Deduplicate while
    preserving source ordering.

    WR-08 fix: defensively skip non-string entries (a malformed
    ``related_skills: [{name: foo}]`` frontmatter would otherwise raise
    ``TypeError: unhashable type: 'dict'`` inside ``LEGACY_NAME_MAP.get``).
    """
    if not isinstance(related_skills, list):
        logger.warning(
            "_filter_related_agents: expected list, got %s",
            type(related_skills).__name__,
        )
        return []
    canonicalized: list[str] = []
    for name in related_skills:
        if not isinstance(name, str):
            logger.warning(
                "_filter_related_agents: skipping non-string entry %r", name,
            )
            continue
        canonicalized.append(LEGACY_NAME_MAP.get(name, name))
    seen: set[str] = set()
    result: list[str] = []
    for name in canonicalized:
        if name in PANEL_9 and name not in seen:
            seen.add(name)
            result.append(name)
    return result


def _tools_for(expert_name: str) -> list[str]:
    """Per Phase 49 §2.x default tools whitelist (runtime grants)."""
    if expert_name not in _TOOLS_TABLE:
        raise KeyError(
            f"no tools table entry for {expert_name!r} — EXPERTS_9 drift?"
        )
    return list(_TOOLS_TABLE[expert_name])


def _build_persona(expert_name: str, body: str) -> str:
    """Build first-person persona fragment for the agent YAML.

    Per agents-schema.yaml §2.4 + ARCHITECTURE §8.1 anti-pattern: persona
    is a SYSTEM-prompt fragment in first-person expert identity ("I am X.
    I do Y."), distinct from SKILL body's USER-message second-person
    register ("You are X. Do Y."). The transform MUST rewrite, not copy.

    Each persona cites the SKILL body's foundational frameworks so the
    agent system-prompt carries the same load-bearing expertise anchors.
    Per CONTEXT.md + 04-MIGRATION-PATH.md §2.x per-expert rules.
    """
    builder = _PERSONA_BUILDERS.get(expert_name)
    if builder is None:
        # Fallback: generic first-person identity for any future expert.
        return (
            f"I am the {expert_name.replace('_', ' ')} expert. "
            f"I operate as a Hermes-native agent with per-agent memory scope, "
            f"consulting my SKILL lineage as fallback when needed. "
            f"My runtime tool whitelist is fixed by my agent YAML."
        )
    return builder(body)


# --------------------------------------------------------------------------- #
# Per-expert persona fragments
# --------------------------------------------------------------------------- #
# Each builder returns a first-person SYSTEM-prompt fragment citing the
# load-bearing frameworks from the source SKILL body. Per CONTEXT.md
# decision #1 + 04-MIGRATION-PATH.md §2.x per-expert rules.
# --------------------------------------------------------------------------- #


def _persona_screenplay(_body: str) -> str:
    """Screenplay persona — HOOK-09 emotion_curve + Snyder + McKee + Tan + cn-shortdrama.

    Per 04-MIGRATION-PATH.md §2.4 + HOOK-09 invariant: persona surfaces
    the emotion_curve marker contract so downstream storyboard + visual
    executor can consume Step 3 output. (The verbatim invariant substring
    lives in transform_notes, not here — but persona references the
    same contract so model-generated output stays marker-compliant.)
    """
    return (
        "I am the Screenplay Expert (剧本专家). I write scene-level scripts "
        "with scene-by-scene emotion_curve marker arrays — hooks, payoffs, "
        "and cliffhangers are first-class JSON fields in my output, not "
        "afterthoughts. My structural backbone is Blake Snyder's 15-beat "
        "Save-the-Cat beat sheet, Robert McKee's scene-level value-shift "
        "framework, and Ed Tan's interest-formula psychology (curiosity + "
        "uncertainty + anticipation). For 短剧 / 竖屏短剧 I apply the "
        "cn-shortdrama-structure reference (3-second cold-open hook, "
        "付费卡点 at beat 8, climax-then-cliffhanger per episode). My "
        "emotion_curve arrays follow the academic arousal (0.0-1.0) + "
        "valence (-1.0..1.0) parameterization so hook_retention and "
        "script_auditor can verify marker coverage downstream.\n"
        "HOOK-09 emotion_curve marker arrays remain contract-load-bearing: "
        "every scene_breakdown entry MUST carry its own per-scene "
        "emotion_curve, and the top-level emotion_curve array MUST be "
        "non-empty — downstream storyboard Step 6.5 + visual_executor "
        "Step 7 cross-reference these arrays for pacing decisions."
    )


def _persona_cinematographer(_body: str) -> str:
    """Cinematographer persona — shot intent + axis + 9:16 vertical framing.

    Per 04-MIGRATION-PATH.md §2.7: cinematographer absorbed the scene_builder
    visual-DNA role in Phase 17. Persona surfaces shot intent layering +
    180° axis + vertical 9:16 framing constraints.
    """
    return (
        "I am the Cinematographer Expert (运镜/摄影指导). I produce the "
        "shot intent layer — shot scale (ECU / CU / MCU / MS / WS / EWS), "
        "composition (rule of thirds, leading lines, headroom), camera "
        "movement (static / pan / tilt / dolly / handheld / crane), and "
        "180° axis continuity — for AI 短剧 / 微电影 with vertical 9:16 "
        "framing. I absorbed the visual-DNA role from the legacy "
        "scene_builder skill (Phase 17 absorption) so shot intent and "
        "visual DNA live in one expert, not two. My output is "
        "shot-intent JSON consumed by visual_executor (Step 7) for "
        "prompt-token mapping to 2026 video gen models (Sora 2, Veo 4, "
        "Kling 2, Dreamina). I refuse shots that violate axis or vertical-"
        "safe framing — even when screenplay's intent suggests otherwise."
    )


def _persona_hook_retention(_body: str) -> str:
    """Hook & Retention persona — 5 hook types + 5 爆款公式 + marker schema.

    Per 04-MIGRATION-PATH.md §2.2: 5 hook categories (cold_open, curiosity,
    shock, cliffhanger, paywall) + per-platform 爆款公式 branching.
    """
    return (
        "I am the Hook & Retention Expert (钩子与留存专家). I design the "
        "3-second cold-open hook, place 付费卡点 (paywall cliffhangers) at "
        "the beat-8 boundary per cn-shortdrama-structure, and branch per "
        "platform 爆款公式 (Douyin 抖音 / Kuaishou 快手 / WeChat Video / "
        "Bilibili / YouTube Shorts each have distinct pacing + paywall "
        "conventions). My HOOK-09 marker schema emits 5 hook types "
        "(cold_open / curiosity / shock / cliffhanger / paywall) as JSON "
        "arrays with timestamp_seconds + type + payload — downstream "
        "editors and analytics use these markers for retention-curve "
        "regression. My 完播率_proxy metric (play-through rate proxy) is "
        "computed from marker density + paywall placement quality."
    )


def _persona_theory_critic(_body: str) -> str:
    """Theory & Criticism persona — soft-gate-only framing.

    Per 04-MIGRATION-PATH.md §2.16: theory_critic is a soft gate, NOT a
    hard gate — advisory-only feedback to screenplay / cinematographer /
    editor. Cites formalism / realism / psychoanalytic / auteur frameworks.
    """
    return (
        "I am the Theory & Criticism Expert (影视理论与批评专家). I "
        "apply film theory frameworks as an advisory soft gate — "
        "formalism (Bordwell), realism (Bazin), psychoanalytic (Mulvey's "
        "male gaze, Metz's apparatus theory), auteur theory (Sarris), "
        "and philosophy (Tarkovsky on time, Žižek on ideology, 戴锦华 "
        "Dai Jinhua on gender + Chinese cinema). I do NOT block production "
        "(I am a soft gate, not a hard gate per Phase 49 §2.16) — I "
        "surface theoretical concerns to screenplay, cinematographer, "
        "and editor as annotated critique. My metrics are theoretical "
        "rigor, citation accuracy, critical depth, and framework fit."
    )


def _persona_editor(_body: str) -> str:
    """Editor persona — FxRxT 3D + cut_density + cut-follows-intent.

    Per 04-MIGRATION-PATH.md §2.13: FxRxT 3D editing matrix (F=fx library,
    R=rhythm, T=tempo) + cut_density metric + cut-follows-intent principle.
    """
    return (
        "I am the Editor Expert (剪辑专家). I orchestrate the FxRxT 3D "
        "editing matrix — F (fx library cross-reference), R (rhythm: "
        "beat, cadence, breath), T (tempo: scene pace) — across Y / L / "
        "C / S cross-library source pools. My cut_density metric (cuts "
        "per minute, normalized by scene type) governs rhythm accuracy; "
        "my cut-follows-intent principle means every cut answers a "
        "narrative question from screenplay (no unmotivated cuts). I "
        "consume screenplay's emotion_curve + cinematographer's shot "
        "intent to produce an edit decision list (EDL) that hook_retention "
        "can verify against the HOOK-09 marker schema."
    )


def _persona_character_designer(_body: str) -> str:
    """Character Designer persona — 4D-Anchor + L1-L4 asset specs.

    Per 04-MIGRATION-PATH.md §2.6: L1-L4 layered asset specifications +
    4D-Anchor multi-view + STYLE_PREFIX layered identity contract.
    """
    return (
        "I am the Character Designer Expert (角色设计师). I define "
        "character identity via the 4D-Anchor multi-view protocol (front "
        "/ side / back / 3-quarter) and a layered STYLE_PREFIX identity "
        "contract that visual_executor must satisfy. My L1-L4 layered "
        "asset specs produce a CharacterBible 2.0 JSON: L1 (identity "
        "anchor — name, age, archetype, negative traits), L2 (visual "
        "style — silhouette, color palette, materials), L3 (voice + "
        "mannerism specs for audio_pipeline TTS), L4 (turnaround sheet "
        "for visual_executor image generation). I am DECOUPLED from "
        "visual_executor (I define identity; visual_executor renders it). "
        "My stress_test_pass_rate metric catches cross-angle consistency "
        "regressions before they reach the editor."
    )


def _persona_continuity_auditor(_body: str) -> str:
    """Continuity Auditor persona — 4-dim hard-gate (face/wardrobe/color/object).

    Per 04-MIGRATION-PATH.md §2.11: continuity_auditor is a HARD gate
    across 4 dimensions + eyeline match + 180° axis + screen direction.
    """
    return (
        "I am the Continuity Auditor Expert (连续性审查专家). I am a "
        "HARD gate, not advisory — every shot pair must pass my 4-"
        "dimension cross-shot audit before reaching the editor: (1) face "
        "similarity (cosine on identity embeddings), (2) wardrobe match "
        "(character_designer's L1 + L2 specs), (3) color consistency "
        "(delta-E on palette anchors from style_genome), (4) object "
        "continuity (prop-tracking across shots). I also enforce eyeline "
        "match, 180° axis continuity, and screen direction. My metrics "
        "(face_similarity, color_consistency, style_uniformity) gate "
        "production: any violation blocks the cut."
    )


def _persona_audio_pipeline(_body: str) -> str:
    """Audio Pipeline persona — 6 sub-step atomicity + Chion audio-vision.

    Per 04-MIGRATION-PATH.md §2.12: 6 sub-steps (voicer / lip_sync /
    composer / foley / mixer / spatial_audio) must be orchestrated
    atomically; cites Chion's audio-vision theory for material credibility.
    """
    return (
        "I am the Audio Pipeline Expert (音频管线专家). I orchestrate the "
        "6-sub-step audio production chain atomically: voicer (TTS — "
        "character voice from character_designer's L3 specs), lip_sync "
        "(audio-driven video-gen sync for talking-head benchmarks), "
        "composer (music score — emotion_curve-driven MusicGen prompt "
        "tokens), foley (sound effects — physical-audio impact-sync), "
        "mixer (mastering — LUFS compliance, dialogue intelligibility, "
        "frequency masking score, ducking), spatial_audio (3D encoding — "
        "Dolby Atmos + binaural HRTF + ambience reverb for immersive "
        "reality anchor). My sub-steps are ATOMIC — partial output is "
        "rejected (CONTEXT D-7 one-directional contract with hook_retention: "
        "I receive BGM sync markers; I do not push back). My theoretical "
        "backbone is Michel Chion's audio-vision (material credibility + "
        "forced sound + reality anchor stability)."
    )


def _persona_style_genome(_body: str) -> str:
    """Style Genome persona — 5D style vector + Cross-Module Alignment.

    Per 04-MIGRATION-PATH.md §2.8: 5D director/genre parametric encoding
    + Cross-Module Alignment metric (gene_extraction_accuracy +
    blend_coherence + cross_module_alignment).
    """
    return (
        "I am the Style Genome Expert (风格基因组专家). I produce the 5D "
        "director/genre parametric encoding — D1 (color palette "
        "temperature/saturation), D2 (composition geometry), D3 (motion "
        "cadence), D4 (texture + grain), D5 (sound signature) — for "
        "AI film style consistency. My Cross-Module Alignment metric "
        "verifies that every downstream module (cinematographer shot "
        "intent, editor EDL, colorist LUT, audio_pipeline mix) carries "
        "the same style vector. Style blending is non-commutative "
        "(A-blend-with-B ≠ B-blend-with-A) — I encode precedence "
        "explicitly. My metrics are style_consistency, "
        "gene_extraction_accuracy, blend_coherence, and "
        "cross_module_alignment."
    )


_PERSONA_BUILDERS: dict[str, Any] = {
    "screenplay": _persona_screenplay,
    "cinematographer": _persona_cinematographer,
    "hook_retention": _persona_hook_retention,
    "theory_critic": _persona_theory_critic,
    "editor": _persona_editor,
    "character_designer": _persona_character_designer,
    "continuity_auditor": _persona_continuity_auditor,
    "audio_pipeline": _persona_audio_pipeline,
    "style_genome": _persona_style_genome,
}


# --------------------------------------------------------------------------- #
# Per-expert transform notes
# --------------------------------------------------------------------------- #


def _transform_notes(expert_name: str) -> str:
    """Per-expert transform notes verbatim from Phase 49 §2.x.

    HOOK-09 invariant: the screenplay entry MUST contain the literal
    substring ``HOOK-09 emotion_curve marker arrays remain
    contract-load-bearing`` (53-01-PLAN.md SC#1 acceptance).
    """
    table: dict[str, str] = {
        "screenplay": (
            "Persona rewritten from SKILL body; SKILL preserved as fallback. "
            "HOOK-09 emotion_curve marker arrays remain contract-load-bearing "
            "— do NOT lose in transform. Snyder 15-beat + McKee value-shift + "
            "Tan interest formula + cn-shortdrama-structure + emotion-curve-"
            "academic anchors all surfaced in persona. Tools whitelist includes "
            "write_file + patch so screenplay can emit Step 3 JSON artifacts."
        ),
        "cinematographer": (
            "Persona rewritten from SKILL body; visual-DNA role absorbed from "
            "legacy scene_builder (Phase 17 absorption per 04-MIGRATION-PATH "
            "§2.7). Shot intent + axis + 9:16 vertical framing are the "
            "load-bearing anchors. Analysis-only tools (no write) — output is "
            "shot-intent JSON consumed by visual_executor."
        ),
        "hook_retention": (
            "Persona rewritten from SKILL body; 5 hook categories + per-platform "
            "爆款公式 branching surfaced (Phase 49 §2.2). HOOK-09 marker schema "
            "is downstream contract, not transform-time concern. Analysis-only "
            "tools — output is hooks/payoffs/cliffhangers marker arrays."
        ),
        "theory_critic": (
            "Persona rewritten from SKILL body; soft-gate-only framing per "
            "Phase 49 §2.16 (theory_critic is advisory, NOT a hard gate). "
            "Cites Bordwell / Bazin / Mulvey / Metz / Tarkovsky / Žižek / "
            "戴锦华. Analysis-only tools — output is annotated critique."
        ),
        "editor": (
            "Persona rewritten from SKILL body; FxRxT 3D editing matrix + "
            "cut_density metric + cut-follows-intent principle surfaced "
            "(Phase 49 §2.13). Analysis-only tools — output is an edit "
            "decision list (EDL) consumed by the rendering pipeline."
        ),
        "character_designer": (
            "Persona rewritten from SKILL body; L1-L4 layered asset specs + "
            "4D-Anchor multi-view surfaced (Phase 49 §2.6). Renamed from "
            "legacy 'performer' (CONTEXT.md decision #1) — LEGACY_NAME_MAP "
            "canonicalizes old references. Tools whitelist includes "
            "write_file for L4 turnaround sheet emission."
        ),
        "continuity_auditor": (
            "Persona rewritten from SKILL body; 4-dimension hard gate "
            "(face/wardrobe/color/object) + eyeline + 180° axis + screen "
            "direction surfaced (Phase 49 §2.11). Renamed from legacy "
            "'continuity' — LEGACY_NAME_MAP canonicalizes old references. "
            "Analysis-only tools — output is a pass/fail audit report."
        ),
        "audio_pipeline": (
            "Persona rewritten from SKILL body; 6-sub-step atomicity "
            "(voicer/lip_sync/composer/foley/mixer/spatial_audio) surfaced "
            "(Phase 49 §2.12). Renamed from legacy 'composer' (CONTEXT.md "
            "decision #1) — the composer sub-step is now ONE of 6, not the "
            "whole expert. Tools whitelist includes dreamina_cli + write_file "
            "for actual asset rendering. Chion audio-vision is the theoretical "
            "backbone."
        ),
        "style_genome": (
            "Persona rewritten from SKILL body; 5D director/genre parametric "
            "encoding + Cross-Module Alignment metric surfaced (Phase 49 §2.8). "
            "Style blending precedence is non-commutative — encoded explicitly. "
            "Analysis-only tools — output is the 5D style vector consumed by "
            "every downstream module."
        ),
    }
    return table[expert_name]


# --------------------------------------------------------------------------- #
# CLI __main__ block — operator-invoked batch transform
# --------------------------------------------------------------------------- #


def _emit_yaml(target_path: Path, data: dict[str, Any]) -> None:
    """Write the agent YAML dict to ``target_path`` with utf-8 encoding."""
    target_path.parent.mkdir(parents=True, exist_ok=True)
    target_path.write_text(
        yaml.safe_dump(data, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _build_audit_log_entry(
    expert_name: str, skill_md_path: Path, data: dict[str, Any]
) -> dict[str, Any]:
    """Build a per-expert audit log entry documenting frontmatter→YAML field mappings.

    SC#1 acceptance (transform audit trail): for each of the 9 experts,
    record which SKILL frontmatter field mapped to which agent YAML field.
    """
    content = skill_md_path.read_text(encoding="utf-8")
    frontmatter, _body = parse_frontmatter(content)
    meta = frontmatter.get("metadata", {}).get("hermes", {})

    return {
        "expert": expert_name,
        "source_path": str(skill_md_path),
        "source_sha256": data["lineage"]["skill_sha256"],
        "frontmatter_mappings": {
            "description": "from frontmatter.description (verbatim)",
            "tags": (
                "from metadata.hermes.tags — filtered to schema pattern "
                "^[a-z0-9-]+$ (non-ASCII tags like `镜头语言` dropped)"
            ),
            "expert_id": "from metadata.hermes.expert_id (verbatim, FOUND-08)",
            "metrics": "from metadata.hermes.metrics (verbatim)",
            "related_agents": (
                "from metadata.hermes.related_skills — canonicalized via "
                "LEGACY_NAME_MAP, filtered to PANEL_9"
            ),
            "prerequisites": "from frontmatter.prerequisites (verbatim)",
            "platforms": "from frontmatter.platforms (verbatim or default)",
            "tools": f"from Phase 49 §2.{_section_x(expert_name)} default",
            "persona": (
                "rewritten first-person from SKILL body — see _persona_* builder"
            ),
            "lineage.skill_sha256": (
                "computed: SHA-256 of LF-normalized source SKILL.md bytes"
            ),
            "lineage.transform_notes": (
                "verbatim from _transform_notes() per Phase 49 §2.x"
            ),
        },
        "frontmatter_related_skills": _get_list(meta, "related_skills"),
        "emitted_related_agents": data["related_agents"],
        "emitted_tools": data["tools"],
        "transform_notes_excerpt": data["lineage"]["transform_notes"][:120],
    }


def _section_x(expert_name: str) -> str:
    """Phase 49 §2.x section number for the audit log (cosmetic)."""
    return {
        "screenplay": "4",
        "cinematographer": "7",
        "hook_retention": "2",
        "theory_critic": "16",
        "editor": "13",
        "character_designer": "6",
        "continuity_auditor": "11",
        "audio_pipeline": "12",
        "style_genome": "8",
    }.get(expert_name, "?")


def main() -> int:
    """CLI entrypoint — transform all 9 SKILLs, validate, write audit log.

    Returns:
        0 on success; non-zero on any validation failure (does NOT silently
        emit invalid YAMLs).
    """
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )

    agents_dir = get_hermes_home() / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    logger.info("target agents dir: %s", agents_dir)

    audit_entries: dict[str, Any] = {}
    emitted_count = 0

    for expert_name in EXPERTS_9:
        skill_path = KIAS_SKILLS_ROOT / expert_name / "SKILL.md"
        if not skill_path.exists():
            logger.warning("SKIP %s: source missing at %s", expert_name, skill_path)
            continue

        try:
            data = transform_one(expert_name, skill_path)
        except (KeyError, ValueError) as exc:
            logger.error("FAIL transform %s: %s", expert_name, exc)
            return 1

        target = agents_dir / f"{expert_name}.agent.yaml"
        _emit_yaml(target, data)

        # Post-write validation (T-53-02 spoofing + T-53-03 undeclared fields).
        try:
            load_one_agent_yaml(target)
        except RegistryValidationError as exc:
            logger.error("FAIL validate %s: %s", target, exc)
            return 2

        audit_entries[expert_name] = _build_audit_log_entry(expert_name, skill_path, data)
        emitted_count += 1
        logger.info("OK %s -> %s", expert_name, target.name)

    # Write the audit log to the test fixture location (operator's repo).
    # This is a test fixture, NOT production state — it documents the
    # field-mapping audit trail per SC#1.
    audit_path = _ROOT / "tests" / "fixtures" / "transform-audit-log.json"
    audit_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path.write_text(
        json.dumps(audit_entries, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    logger.info(
        "emitted %d agent YAMLs to %s; audit log at %s",
        emitted_count,
        agents_dir,
        audit_path,
    )

    if emitted_count != len(EXPERTS_9):
        logger.error(
            "expected %d YAMLs, emitted %d — missing source SKILLs?",
            len(EXPERTS_9),
            emitted_count,
        )
        return 3

    return 0


if __name__ == "__main__":
    sys.exit(main())
