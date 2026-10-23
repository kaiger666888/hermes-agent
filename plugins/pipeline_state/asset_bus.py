"""asset_bus.py — AssetBus V3 port (reference: kais-movie-agent/lib/asset-bus.js).

Port of the Node.js AssetBus V3 (332 lines). Pure stdlib, sync API, atomic
writes via ``tempfile.mkstemp`` + ``os.replace``.

Scope (Phase 33, per CONTEXT CF-05 / SC#2):
  - 3 v3.0 typed slots: ``creative-history`` / ``failed-shots`` / ``finetune-dataset``
  - ``review-outcomes`` routed as generic JSON (D-33-03; Phase 34 tightens schema)
  - V3 envelope ``{value, derived_from, content_hash, schema_version}`` with v2.0
    backward compat on unwrap
  - Atomic write (write-tmp-then-rename) for JSON slots; JSONL append via
    ``open(..., "a")`` for the finetune-dataset slot (no fsync — matches Node.js)
  - mtime-based cache keyed on ``st_mtime_ns`` (writes invalidate by slot prefix)

Differences from Node.js (documented in PATTERNS.md):
  - Sync API (no ``async def``); D-07 applies
  - ``json.dumps(sort_keys=True)`` for cross-run hash determinism
  - ``st_mtime_ns`` (ns precision) rather than ``mtimeMs``
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)

SCHEMA_VERSION = "3.0"
ASSETS_DIR = ".pipeline-assets"

# ASSET_SCHEMA — Phase 33 scope (3 v3.0 typed slots + review-outcomes).
# V2/V4.1 slots (art-bible, character-assets, visual-soul, etc.) are out of
# scope — they belong to other phases per CONTEXT CF-05.
ASSET_SCHEMA: dict[str, dict] = {
    "creative-history": {
        "file": "creative-history.json",
        "format": "json",
        "schema": {
            "shots": "Array<{shot_id, source_hash, derived_from: string[], content_hash, timestamp}>",
            "version": "number",
        },
    },
    "failed-shots": {
        "file": "failed-shots.json",
        "format": "json",
        "schema": {
            "failures": "Array<{shot_id, error, timestamp, run_id, prompt, fingerprints?: {dino?: number[], phash?: string}}>",
            "version": "number",
        },
    },
    "finetune-dataset": {
        "file": "finetune-dataset.jsonl",
        "format": "jsonl",  # append-only — use append_line / read_lines
    },
    # D-33-03: Phase 33 routes this slot as generic JSON; Phase 34 defines the
    # full schema + Gate resolution semantics.
    "review-outcomes": {
        "file": "review-outcomes.json",
        "format": "json",
    },

    # ── Phase 35 additions — phase-output slots (D-35-05) ──────────────
    # Phase 35-02 task 1 registers these 6 slots so phase modules
    # (p01_hook_topic, p02_outline, p03_script_audit — implemented in 35-03)
    # can write their outputs via AssetBus.write(). All are JSON format
    # (envelope-wrapped, atomic write). None are append-only history slots.
    #
    # Slot names mirror the V8.6 Node.js asset-bus slot names where they
    # exist, in kebab-case, so cross-port tracing is easier in Phase 36.
    # Phase 36 will extend this list with the remaining slots
    # (character-bible, scene-design, shot-list, voice-timeline, video-clips,
    # audio-stems, master-mp4, etc.).
    "requirement": {
        "file": "requirement.json",
        "format": "json",
        "description": "Operator requirement / creative constraints",
        "writer_phase": None,
        "reader_phases": ["p01_hook_topic", "p03_script_audit", "p09b_shot_audit"],
    },
    "requirement-feasibility": {
        "file": "requirement-feasibility.json",
        "format": "json",
        "description": "P01 pre-delegate feasibility audit (P0-A1+A2 2026-07-14): reversal_count vs duration, pacing interval checks",
        "writer_phase": "p01_hook_topic",
        "reader_phases": ["p14_quality_audit"],
    },
    "topic-kernel": {
        "file": "topic-kernel.json",
        "format": "json",
        "description": "Topic kernel (爆款选题核)",
        "writer_phase": "p01_hook_topic",
        "reader_phases": ["p02_outline"],
    },
    "hook-design": {
        "file": "hook-design.json",
        "format": "json",
        "description": "Hook design (钩子设计)",
        "writer_phase": "p01_hook_topic",
        "reader_phases": ["p02_outline", "p09b_shot_audit"],
    },
    # ── Phase 4 (v1.3) addition — creative hook candidates ──────────────
    "hook-candidates": {
        "file": "hook-candidates.json",
        "format": "json",
        "description": "K framing-divergent hook candidates (variant-tagged array, creative-hook mode only)",
        "writer_phase": None,  # conditionally written by p01_hook_topic when enable_creative_hook=True;
                                # None here so default-off path skips Layer-3 validation (Phase 4 design)
        "reader_phases": [],  # Phase 5 SELECT reads this; downstream p02+ reads hook-design
    },
    # ── ICA M2 (2026-08-25): hook intent / spec split (C4b 派生失效协议) ──
    # hook-intent: 稳定钩子承诺（P01 从 hook-design 确定性提取，不再生）
    # hook-spec:   从锁定剧本再实例化的开场规格（p036 产，承诺型资产
    #              必须从最终交付物派生）。两个 slot 都用 writer_phase=None
    #              占位（flag-gated 防 Layer 3 假 incomplete；M4 翻默认时
    #              按四步原子启用补齐）。
    "hook-intent": {
        "file": "hook-intent.json",
        "format": "json",
        "description": "ICA C4b: 稳定钩子承诺（P01 从自身 hook-design 确定性提取，不再生）",
        "writer_phase": None,      # 由 runner v2 分支义务强制，理由同 creative-contracts（flag-gated 防 Layer 3 假 incomplete）
        "reader_phases": ["p036_hook_reconcile"],
    },
    "hook-spec": {
        "file": "hook-spec.json",
        "format": "json",
        "description": "ICA C4b: 从锁定剧本再实例化的开场规格（承诺型资产必须从最终交付物派生）",
        "writer_phase": None,      # 同上；M4 翻默认时按四步原子启用补齐
        "reader_phases": ["p09b_shot_audit", "p14_quality_audit"],
    },
    "story-framework": {
        "file": "story-framework.json",
        "format": "json",
        "description": "Story framework (故事框架)",
        "writer_phase": "p02_outline",
        "reader_phases": ["p03_script_audit"],
    },
    # ── ICA M4 T5: craft-budget（节拍预算） ──
    # P02 子步（v2 flag-gated）从 emotion_curve 确定性推导 per-scene 预算。
    # writer_phase=None（占位注册，防 Layer 3 假 incomplete）；v2 下 P02
    # 实际写入。P09 分镜读取预算，超预算必须走 deviation-ledger 申报。
    "craft-budget": {
        "file": "craft-budget.json",
        "format": "json",
        "description": "ICA C8: per-scene pacing budget (beats/density/end_scale/protected_frames)",
        "writer_phase": None,    # 占位注册；v2 下 P02 实际写入
        "reader_phases": ["p09_shot_breakdown", "p09b_shot_audit"],
    },
    "script-draft": {
        "file": "script-draft.json",
        "format": "json",
        "description": "Script draft (剧本初稿)",
        "writer_phase": "p03_script_audit",
        # MV-VAR (2026-10-15): mv02_visual_script 是本槽在 MV 链内的写入者
        # （DESIGN §5.6 bookkeeping / §9-1 跨变体写槽 —— writer_phase 保持
        # drama 属主单值，mv 侧写入者记录于此；reader_phases 无运行期强制）。
        "reader_phases": ["p04_character_design", "p05_pain_discovery",
                          "mv02_visual_script"],
    },
    "audit-report": {
        "file": "audit-report.json",
        "format": "json",
        "description": "Script audit report (剧本审计报告)",
        "writer_phase": "p03_script_audit",
        "reader_phases": ["p04_character_design"],
    },
    # ── P03.5 (86ke dramatic-event polish) additions ─────────────────
    # 86ke 方法论落地收尾（2026-08-15）：P03→P04 之间的轻量 LLM 打磨 pass。
    # 写侧用两个 NEW slot 而非回写 script-draft —— writer_phase 是单值字段，
    # 追加 p035 会破坏 Layer-3 验证语义（脚本真源 §层1 决策规则：最小侵入）。
    # P04 读序：script-draft-polished 存在→用之，否则→script-draft（旧
    # checkpoint 兼容，p035 degrade 时也写 polished=原文，读序永远单调）。
    "script-draft-polished": {
        "file": "script-draft-polished.json",
        "format": "json",
        "description": "Polished script (86ke dramatic-event polish; degraded path = verbatim script-draft)",
        "writer_phase": "p035_dramatic_polish",
        "reader_phases": ["p04_character_design"],
    },
    "dramatic-polish-report": {
        "file": "dramatic-polish-report.json",
        "format": "json",
        "description": "P03.5 dramatic-event polish report (86ke): which scenes polished, change summary, gap_score before/after",
        "writer_phase": "p035_dramatic_polish",
        "reader_phases": ["p14_quality_audit"],
    },
    # Quality-gate rollback feedback: the runner writes the rejection
    # payload here so the producing phase can read fix instructions on
    # retry. Used by run_episode's QualityGateRejection handler.
    "fix-required": {
        "file": "fix-required.json",
        "format": "json",
        "description": "Quality-gate rejection + fix instructions (质量门驳回反馈)",
        "writer_phase": None,  # written by runner rollback logic
        "reader_phases": [],   # read by whichever phase is rolling back
    },
    # ── ICA M4 T3: stigma registry（降级/瑕疵登记册） ──
    # 创意打磨类 phase 失败降级时，登记一条 stigma（polish_skipped 等）。
    # stigma 沿 derived_from 逻辑传播：下游 phase 可读到上游所有 stigma。
    # writer_phase=None（由 runner 的 v2 分支统一写入，侵入最小）。
    "stigmas": {
        "file": "stigmas.json",
        "format": "json",
        "description": "ICA T3: stigma registry — 全管线降级/瑕疵条目汇总（polish_skipped 等）",
        "writer_phase": None,   # runner v2 分支统一写（T3）
        "reader_phases": ["p14_quality_audit"],
    },

    # ── Phase 36-01 additions — p04/p05/p06 output slots (D-36-04) ──────
    # Wave 1 plan 36-01 registers these 6 slots so p04_character_design,
    # p05_pain_discovery, p06_spatio_temporal_script can write their outputs
    # via AssetBus.write(). All JSON format (envelope-wrapped, atomic write).
    # Per-plan asset-bus extension (D-36-05): PRESERVES existing slots
    # byte-equivalent — only appends.
    "character-bible": {
        "file": "character-bible.json",
        "format": "json",
        "description": "Character Bible 2.0 (4D-Anchor + style_prefix)",
        "writer_phase": "p04_character_design",
        "reader_phases": ["p05_pain_discovery", "p06_spatio_temporal_script",
                          "p07_scene_generation", "p09_shot_breakdown"],
    },
    "character-assets": {
        "file": "character-assets.json",
        "format": "json",
        "description": "L1-L4 character asset manifest (identity anchors + costume cards)",
        "writer_phase": "p04_character_design",
        "reader_phases": ["p07_scene_generation", "p11_video_render"],
    },
    "pain-points": {
        "file": "pain-points.json",
        "format": "json",
        "description": "L1-L6 pain point strata",
        "writer_phase": "p05_pain_discovery",
        "reader_phases": ["p06_spatio_temporal_script"],
    },
    "escalation-ladder": {
        "file": "escalation-ladder.json",
        "format": "json",
        "description": "Pain escalation ladder (step-by-step intensity)",
        "writer_phase": "p05_pain_discovery",
        "reader_phases": ["p06_spatio_temporal_script"],
    },
    "spatio-temporal-script": {
        "file": "spatio-temporal-script.json",
        "format": "json",
        "description": "Spatio-temporal script (shot intent + axis + composition_lock)",
        "writer_phase": "p06_spatio_temporal_script",
        # MV-VAR (2026-10-15): mv02_visual_script 是本槽在 MV 链内的写入者
        # （DESIGN §5.6 bookkeeping / §9-1 —— writer_phase 保持 drama 属主，
        # mv 侧写入者记录于此；reader_phases 无运行期强制）。
        "reader_phases": ["p07_scene_generation", "p08_scene_selection",
                          "p09_shot_breakdown", "mv02_visual_script"],
    },
    "final-audit": {
        "file": "final-audit.json",
        "format": "json",
        "description": "Final script audit report (5-dim post spatio-temporal)",
        "writer_phase": "p06_spatio_temporal_script",
        "reader_phases": [],
    },
    "visual-direction": {
        "file": "visual-direction.json",
        "format": "json",
        "description": "Unified visual motif decisions (color temp + contrast + lighting + visual leitmotif)",
        "writer_phase": "p06_blackboard",
        "reader_phases": ["p07_scene_generation", "p11_video_render"],
    },
    "production-design": {
        "file": "production-design.json",
        "format": "json",
        "description": "Prop placement + scene geometry + environment constraints",
        "writer_phase": "p06_blackboard",
        "reader_phases": ["p07_scene_generation", "p09_shot_breakdown"],
    },
    "physics-precheck-report": {
        "file": "physics-precheck-report.json",
        "format": "json",
        "description": "Physics feasibility precheck (camera move + character action + AI video capability)",
        "writer_phase": "p06_blackboard",
        "reader_phases": ["p09_shot_breakdown", "p11_video_render"],
    },

    # ── Phase 36-02 additions — p07/p08/p09 visual design slots (D-36-04) ─
    # Wave 1 plan 36-02 registers these 7 slots for p07_scene_generation,
    # p08_scene_selection, p09_shot_breakdown. All JSON format (envelope-
    # wrapped, atomic write). Per-plan asset-bus extension (D-36-05):
    # PRESERVES existing slots byte-equivalent — only appends.
    "scene-images": {
        "file": "scene-images.json",
        "format": "json",
        "description": "Scene image set (5-view per scene) produced by p07",
        "writer_phase": "p07_scene_generation",
        "reader_phases": ["p08_scene_selection", "p11_video_render"],
    },
    "style-vector": {
        "file": "style-vector.json",
        "format": "json",
        "description": "5D style genome vector (genre/mood/aesthetic/pace/color)",
        "writer_phase": "p07_scene_generation",
        "reader_phases": ["p11_video_render", "p12a_timeline_composition", "p12b_audio_composition"],
    },
    "color-intent": {
        "file": "color-intent.json",
        "format": "json",
        "description": "CxSxZ 28-combination color intent + LUT design",
        "writer_phase": "p07_scene_generation",
        "reader_phases": ["p13_delivery"],
    },
    "scene-selection": {
        "file": "scene-selection.json",
        "format": "json",
        "description": "Selected scenes (operator-approved subset)",
        "writer_phase": "p08_scene_selection",
        "reader_phases": ["p09_shot_breakdown"],
    },
    "geometry-bed": {
        "file": "geometry-bed.json",
        "format": "json",
        "description": "Cross-shot geometry consistency bed",
        "writer_phase": "p08_scene_selection",
        "reader_phases": ["p09_shot_breakdown", "p11_video_render"],
    },
    "shot-list": {
        "file": "shot-list.json",
        "format": "json",
        "description": "Shot list (one entry per shot with intent + duration)",
        "writer_phase": "p09_shot_breakdown",
        # MV-VAR (2026-10-15): mv03_music_shot_breakdown 是本槽在 MV 链内的
        # 写入者（DESIGN §5.6 bookkeeping / §9-1 —— writer_phase 保持 drama
        # 属主，mv 侧写入者记录于此；reader_phases 无运行期强制）。
        "reader_phases": ["p10_voice", "p11_video_render",
                          "mv03_music_shot_breakdown"],
    },
    "e-konte-sheets": {
        "file": "e-konte-sheets.json",
        "format": "json",
        "description": "E-Konte 5-layer shot decomposition sheets (DEPRECATED — merged into shot-list; P09 no longer writes this slot)",
        "writer_phase": None,
        "reader_phases": ["p11_video_render"],
    },

    # ── Phase 74 additions — transition design slot (TRANS-03) ──────────
    # Phase 74 registers this slot so p09_shot_breakdown (cinematographer
    # Step 9) can write transition design creative intent, and p13_delivery
    # (editor Step 13) can read it for post-production execution. JSON
    # format (envelope-wrapped, atomic write). Per-plan asset-bus extension
    # (D-36-05): PRESERVES existing slots byte-equivalent — only appends.
    # TRANS-04 ownership split encoded in writer_phase / reader_phases.
    "transition-design": {
        "file": "transition-design.json",
        "format": "json",
        "description": "Transition design (creative intent from cinematographer "
                       "Step 9; drives SFX behavior in p12b + the EDL transition "
                       "field in p12a + per-shot render hints in p11a). Per-shot "
                       "transition_method (12-enum) + visual_hook + camera_continuity.",
        "writer_phase": "p09_shot_breakdown",
        # MV-VAR (2026-10-15): mv03_music_shot_breakdown 是本槽在 MV 链内的
        # 写入者（DESIGN §5.6 bookkeeping / §9-1 —— writer_phase 保持 drama
        # 属主，mv 侧写入者记录于此；reader_phases 无运行期强制）。
        "reader_phases": ["p11a_preview_clips", "p12a_timeline_composition", "p12b_audio_composition",
                          "mv03_music_shot_breakdown"],
    },

    # ── Phase 36-03 additions — p10/p11 voice + video render slots (D-36-04) ─
    # Wave 1 plan 36-03 registers these 4 slots for p10_voice (voice-clips,
    # voice-timeline) and p11_video_render (video-clips, lip-sync-reports).
    # All JSON format (envelope-wrapped, atomic write). Per-plan asset-bus
    # extension (D-36-05): PRESERVES existing slots byte-equivalent — only
    # appends. p11 video-clips + lip-sync-reports are aggregated SINGLE
    # writes (the phase fans out shot-level delegate_task calls internally
    # via ThreadPoolExecutor per D-36-08, then writes one consolidated slot).
    "voice-clips": {
        "file": "voice-clips.json",
        "format": "json",
        "description": "TTS voice clips per shot (narration + dialogue)",
        "writer_phase": "p10_voice",
        # p12a_timeline_composition is NOT a reader: it assembles the EDL from
        # video clips alone (their durations already encode the dialog length).
        # voice-clips stay a p12b input — mix-only (muxing TTS dialog into the
        # master), never a BGM-composition reference.
        # MV-VAR (2026-10-15): mv04_vocal_track 是本槽在 MV 链内的写入者
        # （DESIGN §5.6 bookkeeping / §9-1 —— MV 把该槽当纯时钟通道，切片
        # 内容不进任何混音；writer_phase 保持 drama 属主，mv 侧写入者记录
        # 于此；reader_phases 无运行期强制）。
        "reader_phases": ["p11_video_render", "p12b_audio_composition",
                          "mv04_vocal_track"],
    },
    "voice-timeline": {
        "file": "voice-timeline.json",
        "format": "json",
        "description": "Voice timeline alignment (per-shot start/end + lip-sync cues)",
        "writer_phase": None,  # Phase 36 planned but not implemented
        "reader_phases": ["p11_video_render"],
    },
    "video-clips": {
        "file": "video-clips.json",
        "format": "json",  # NOT jsonl — aggregated single write per D-36-08
        "description": "Rendered video clips (one entry per shot, parallel-generated)",
        "writer_phase": "p11_video_render",
        "reader_phases": ["p12a_timeline_composition", "p12b_audio_composition"],
    },
    "lip-sync-reports": {
        "file": "lip-sync-reports.json",
        "format": "json",
        "description": "Lip-sync alignment reports per shot",
        "writer_phase": "p11_video_render",
        "reader_phases": [],
    },

    # ── Phase 36-04 additions — p12/p13 final ship slots (D-36-04) ──────
    # Wave 1 plan 36-04 registers these 4 slots so p12*/p13 can write their
    # outputs via AssetBus.write(). P12 split (2026-08-09): master-timeline is
    # now written by p12a_timeline_composition; audio-stems by
    # p12b_audio_composition. All JSON format (envelope-wrapped, atomic write).
    # master-mp4 slot preserves the v4.0 PIPE-COMPOSE-01 contract (master.mp4
    # as the canonical pipeline output artifact).
    "master-timeline": {
        "file": "master-timeline.json",
        "format": "json",
        "description": "FxRxT master timeline (assembled edit decision list)",
        "writer_phase": "p12a_timeline_composition",
        "reader_phases": ["p13_delivery"],
    },
    "audio-stems": {
        "file": "audio-stems.json",
        "format": "json",
        "description": "Audio stems (BGM + SFX + voice + mixdown)",
        "writer_phase": "p12b_audio_composition",
        # MV-VAR (2026-10-15): mv05_vocal_mixdown 是本槽在 MV 链内的写入者
        # （DESIGN §5.6 bookkeeping / §9-1 —— MV 链内唯一写者，p12b 不在链
        # 故无 manifest 哈希互踩；writer_phase 保持 drama 属主，mv 侧写入者
        # 记录于此；reader_phases 无运行期强制）。
        "reader_phases": ["p13_delivery", "mv05_vocal_mixdown"],
    },
    # p11a5 preview-audio slots (added 2026-08-26: phase wrote them but they
    # were never registered — AssetBusError: Unknown asset: ambient-stems
    # killed the runner mid-p11a5; registered in both repo copies in sync).
    "ambient-stems": {
        "file": "ambient-stems.json",
        "format": "json",
        "description": "Per-scene ambient audio stems (p11a5 preview chain)",
        "writer_phase": "p11a5_preview_audio",
        "reader_phases": [],
    },
    "preview-mix": {
        "file": "preview-mix.json",
        "format": "json",
        "description": "Preview roughcut audio mixdown (p11a5 preview chain)",
        "writer_phase": "p11a5_preview_audio",
        "reader_phases": [],
    },
    "preview-verdicts": {
        "file": "preview-verdicts.json",
        "format": "json",
        "description": "Per-shot preview watch verdicts (p11a5 roughcut gate)",
        "writer_phase": "p11a5_preview_audio",
        "reader_phases": [],
    },
    "roughcut-mp4": {
        "file": "roughcut-mp4.json",
        "format": "json",
        "description": "Roughcut preview mp4 metadata (p11a5 preview chain)",
        "writer_phase": "p11a5_preview_audio",
        "reader_phases": [],
    },
    "master-mp4": {
        "file": "master-mp4.json",
        "format": "json",
        "description": "Final master.mp4 metadata (path, duration, resolution, codec)",
        "writer_phase": "p13_delivery",
        "reader_phases": [],
    },
    "delivery-package": {
        "file": "delivery-package.json",
        "format": "json",
        "description": "Delivery package manifest (master + captions + compliance report + metadata)",
        "writer_phase": "p13_delivery",
        "reader_phases": [],
    },

    # ── Phase 40-01 additions — p10b rapid preview slots (BLOCKER #1 + #5) ──
    # Wave 1 plan 40-01 registers these 2 slots so p10b_rapid_preview (the
    # rapid preview tier between p10_voice and p11_video_render) can persist
    # its outputs. Per CONTEXT.md LOCKED decisions:
    #   - "rapid-preview-clips" (NOT "preview-clips") — the latter is
    #     documented in v3.0-era SKILL.md for a future p06.5 phase with JSON
    #     semantics; renaming avoids namespace collision (BLOCKER #5).
    #   - "episode-meta" (NOT "pipeline-state") — pipeline-state.json is a
    #     separate file managed by PipelineStateStore, NOT an AssetBus slot.
    #     Use the new episode-meta AssetBus slot for the preview_skipped flag
    #     (BLOCKER #1).
    # Per-plan asset-bus extension (D-36-05): PRESERVES existing slots
    # byte-equivalent — only appends.
    "rapid-preview-clips": {
        "file": "rapid-preview-clips.jsonl",
        "format": "jsonl",  # append-only — use append_line() / read_lines()
        "description": "Rapid preview variants per shot (p10b output; one line "
                       "per variant). Renamed from v3.0-era 'preview-clips' to "
                       "avoid collision with SKILL.md p06.5 documented future slot.",
        "writer_phase": "p10b_rapid_preview",
        "reader_phases": [],  # consumed operator-side per blueprint Out of Scope
    },
    "episode-meta": {
        "file": "episode-meta.json",
        "format": "json",
        "description": "Episode-level metadata flags written by p10b "
                       "(preview_skipped on full-degrade). NOT the same as "
                       "pipeline-state.json (which is managed by PipelineStateStore).",
        "writer_phase": "p10b_rapid_preview",
        "reader_phases": [],  # consumed operator-side / by monitoring
    },
    "storyboard-board": {
        "file": "storyboard-board.json",
        "format": "json",
        # 2026-09-28 分镜板退役批: p11a 的 preview-clip 板组装链已摘除,
        # p10b 早已注销 — 唯一在册 writer = p09c 白模链 (engine 缺省 off →
        # 早退写空槽占位)。落库者 (canvas_sync._persist_storyboard_board) 与
        # 消费者 (KAP StoryboardBoard 视图 + /api/v1/storyboard) 同批退役。
        "description": "White-model storyboard slot written by p09c "
                       "(degrade-tolerant empty placeholder by default; the "
                       "p11a preview-clip board assembly was removed "
                       "2026-09-28).",
        "writer_phase": "p09c_storyboard_board",
        "reader_phases": [],
    },

    # ── 2026-08-26 fix: p11a preview-candidates slot（对比管线候选墙数据源）──
    # p11a_preview_clips.py 的 WBI-02/F35 落盘点（"preview-candidates"）此前
    # 从未注册进 ASSET_SCHEMA —— bus.write() 每次都 raise AssetBusError:
    # Unknown asset（ep-zhongkui-v2-ep01 03:03 与 08:50 两次 traceback 实锤），
    # 候选台账从未落盘 → canvas_sync._CANDIDATE_FILES["p11a"] 永远读不到
    # preview-candidates.json → 画布候选变体墙/对比管线 p11a 段一直为空。
    # 形状对齐 hook-candidates：{"value": {variants: [...], k, chosen_variant_id,
    # selector_state}}（envelope 写入）。Per-plan asset-bus extension (D-36-05):
    # append-only，不改既有槽位。
    "preview-candidates": {
        "file": "preview-candidates.json",
        "format": "json",
        "description": "p11a preview candidate variants (post-selection wall data "
                       "source). Written by p11a_preview_clips after per-shot 选优; "
                       "rank=1 marks the chosen variant. Read by canvas_sync "
                       "_CANDIDATE_FILES for the canvas candidate wall / 对比管线.",
        "writer_phase": "p11a_preview_clips",
        "reader_phases": [],  # consumed by canvas_sync (operator-side mirror)
    },

    # ── Phase 41-01 additions — Emotion Recipe Library slot ─────────────
    # Wave 1 plan 41-01 registers this slot so RecipeLibrary (recipe_library.py)
    # can persist structured emotion recipes. Append-only (jsonl format); one
    # line per recipe version (update_validation appends version=N+1).
    # Per-plan asset-bus extension (D-36-05): PRESERVES existing slots
    # byte-equivalent — only appends.
    # NOTE: NOT added to AssetBus.JSONL_SLOTS frozenset (line 422) — dispatch
    # consults ASSET_SCHEMA[slot]["format"] directly, not JSONL_SLOTS. Keeping
    # JSONL_SLOTS unchanged preserves test_asset_bus_phase35_slots.py::
    # test_jsonl_slots_unchanged. The emotion-recipe slot's jsonl format in
    # ASSET_SCHEMA is what the dispatch path actually checks.
    "emotion-recipe": {
        "file": "emotion-recipe.jsonl",
        "format": "jsonl",  # append-only — use append_line() / read_lines()
        "description": "Structured emotion recipes extracted from creative-history "
                       "5-dim script_auditor scores. One line per recipe version "
                       "(update_validation appends version=N+1). Reader: operator-side "
                       "+ Phase 42 feedback_ingest (calls update_validation).",
        "writer_phase": "recipe_library",
        "reader_phases": [],  # Phase 42 feedback_ingest reads via RecipeLibrary methods
    },

    # ── Phase 42-01 additions — Feedback Ingestion slots ──────────────
    # Wave 1 plan 42-01 registers these 2 slots so FeedbackIngestClient
    # (plugins/kais_aigc/feedback_ingest.py) can persist raw feedback
    # records (feedback-data) and rejection audit trail (feedback-rejected).
    # Append-only JSONL (one line per feedback / rejection). Per-plan
    # asset-bus extension (D-36-05): PRESERVES existing slots
    # byte-equivalent — only appends.
    # NOTE: NOT added to AssetBus.JSONL_SLOTS frozenset (line ~444) —
    # dispatch consults ASSET_SCHEMA[slot]["format"] directly, not
    # JSONL_SLOTS. Keeping JSONL_SLOTS unchanged preserves the V5.0
    # invariant asserted by test_asset_bus_phase35_slots.py::
    # test_jsonl_slots_unchanged. The new slots' jsonl format in
    # ASSET_SCHEMA is what the dispatch path actually checks.
    "feedback-data": {
        "file": "feedback-data.jsonl",
        "format": "jsonl",  # append-only — use append_line() / read_lines()
        "description": "Raw platform feedback records (POST /api/v1/feedback payload + "
                       "received_at + signature_valid). One line per feedback "
                       "submission. Reader: operator-side + RecipeLibrary.update_validation "
                       "(Phase 42).",
        "writer_phase": "feedback_ingest",
        "reader_phases": [],
    },
    "feedback-rejected": {
        "file": "feedback-rejected.jsonl",
        "format": "jsonl",  # append-only — use append_line() / read_lines()
        "description": "Rejected feedback submissions (signature/schema/semantic/episode "
                       "existence failures). One line per rejection. Each line contains "
                       "{feedback_id, reason, payload_snippet, timestamp}. Used for audit "
                       "trail — never feeds RecipeLibrary.update_validation.",
        "writer_phase": "feedback_ingest",
        "reader_phases": [],
    },

    # ── Phase 43 additions — Asset Management V2 (full lifecycle provenance) ──
    # Three new slots that transform AssetBus from a write-tool into an
    # asset management system:
    #   1. prompt-log: complete delegate_task prompt provenance (layer 1)
    #   2. asset-manifest: global media file index (layer 2)
    #   3. phase-execution-log: per-phase execution metadata (layer 3)
    # All three are append-only JSONL, auto-written by the runner via
    # _log_prompt() / _scan_new_assets() / _log_phase_execution().
    "prompt-log": {
        "file": "prompt-log.jsonl",
        "format": "jsonl",  # append-only — use append_line() / read_lines()
        "description": "Complete prompt provenance — one line per delegate_task call. "
                       "Auto-logged by runner's _make_logged_delegate wrapper. Contains "
                       "the full 6-segment GoalBuilder goal, phase_id, episode_id, "
                       "context_hash, and timestamp. Enables full reproducibility.",
        "writer_phase": "runner",
        "reader_phases": [],
    },
    "asset-manifest": {
        "file": "asset-manifest.jsonl",
        "format": "jsonl",  # append-only — use append_line() / read_lines()
        "description": "Global asset index — one line per media file created. "
                       "Auto-scanned by runner's _scan_new_assets() after each phase. "
                       "Contains phase_id, relative_path, category, size, mtime. "
                       "Provides a complete inventory without manual ls.",
        "writer_phase": "runner",
        "reader_phases": [],
    },
    "phase-execution-log": {
        "file": "phase-execution-log.jsonl",
        "format": "jsonl",  # append-only — use append_line() / read_lines()
        "description": "Per-phase execution metadata — one line per phase run. "
                       "Auto-logged by runner after each phase completes. Contains "
                       "phase_id, episode_id, status, duration_sec, output_slots_written, "
                       "validation_passed, timestamp.",
        "writer_phase": "runner",
        "reader_phases": [],
    },
    # M7 — GLM advisory audit log (Tier-3 second opinion). Append-only JSONL:
    # one record per advisory dispatch (p03 quantitative, p13/p14 compliance).
    # Advisory (non-blocking); written by pipeline.glm_advisory via the runner's
    # post-phase hook. reader_phases empty — advisory is operator-facing only,
    # never consumed by a downstream phase.
    "glm-audit-report": {
        "file": "glm-audit-report.jsonl",
        "format": "jsonl",  # append-only — use append_line() / read_lines()
        "description": "GLM (GLM-5.2) advisory audit reports — one line per GLM "
                       "advisory dispatch. p03 = quantitative (beat density, "
                       "emotional arc, completion-rate prediction); p13/p14 = CN "
                       "compliance (sensitive words, content rules, marketing/AIGC "
                       "labeling). Advisory only — never blocks the pipeline.",
        "writer_phase": "glm_advisory",
        "reader_phases": [],
    },

    # ── Micro-gate audit slots — p09b/p10c/p14 quality gate outputs ──
    # These audit phases write their structured findings/reports to AssetBus
    # so downstream phases and operator review can access them. All JSON
    # format (envelope-wrapped, atomic write).
    "shot-audit": {
        "file": "shot-audit.json",
        "format": "json",
        "description": "Shot audit report (4D continuity + axis adherence)",
        "writer_phase": "p09b_shot_audit",
        "reader_phases": ["p10_voice", "p11_video_render"],
    },
    "voice-audit": {
        "file": "voice-audit.json",
        "format": "json",
        "description": "Voice/audio audit report (TTS quality + alignment)",
        "writer_phase": "p10c_voice_audit",
        "reader_phases": ["p11_video_render"],
    },
    "quality-audit": {
        "file": "quality-audit.json",
        "format": "json",
        "description": "Post-delivery quality audit report (P14)",
        "writer_phase": "p14_quality_audit",
        "reader_phases": [],
    },
    "take-log": {
        "file": "take-log.json",
        "format": "json",
        "description": "Per-shot take tracking (retake info: take_n, changed_variable, seed, verdict)",
        "writer_phase": "p11_video_render",
        "reader_phases": ["p14_quality_audit"],
    },
    # P11c 视频智能质检眼 (qwen-eye, 2026-08-15): local Qwen3.8-27B VL 两段式
    # 判定结果。advisory — fail 汇总由 P14 聚合进 quality report；P12 永不读它
    # (P11c 任何失败都 degrade-tolerant, 不得阻塞时间线合成)。
    "video-qc": {
        "file": "video-qc.json",
        "format": "json",
        "description": "Per-shot video QC verdicts (qwen-eye: observation + "
                       "spec-vs-observation judgement; verdict/dims/reasons/obs "
                       "per shot + pass/fail summary)",
        "writer_phase": "p11c_video_qc",
        "reader_phases": ["p14_quality_audit"],
    },
    # ── qwen-eye advisory QC expansion (2026-08-16) ────────────────────
    # Three more advisory slots, same contract as video-qc: writer = the
    # producing phase, sole reader = P14 aggregation. Fail/skip paths write
    # a status-marked slot and NEVER block the producing phase.
    "storyboard-qc": {
        "file": "storyboard-qc.json",
        "format": "json",
        "description": "Storyboard board sheet QC verdicts (qwen-eye: panels "
                       "non-blank / pose legible / scene-match; per-sheet "
                       "pass/issues/reasons + summary)",
        "writer_phase": "p09c_storyboard_board",
        "reader_phases": ["p14_quality_audit"],
    },
    "preview-qc": {
        "file": "preview-qc.json",
        "format": "json",
        "description": "Preview variant QC verdicts (qwen-eye over the first "
                       "frame of each rapid-preview clip vs shot intent; "
                       "per-variant pass/reasons + summary)",
        "writer_phase": "p11a_preview_clips",
        "reader_phases": ["p14_quality_audit"],
    },
    # P11a0 条件帧自动审核 (qwen-eye, 2026-08-16): iframe slot × variant 两段式
    # 判定 + per-slot 选优回写 iframe-manifest.json。advisory — 选优失败回退 v1,
    # P11a/P11b 永不因它阻塞; fail 汇总由 P14 聚合 (docs/iframe-qc-design.md)。
    "iframe-qc": {
        "file": "iframe-qc.json",
        "format": "json",
        "description": "Per-slot iframe variant QC verdicts (qwen-eye: "
                       "observation + frame-SPEC judgement; per-variant "
                       "verdict/score/reasons + per-slot selection summary)",
        "writer_phase": "p11a0_iframe_qc",
        "reader_phases": ["p14_quality_audit"],
    },
    "master-qc": {
        "file": "master-qc.json",
        "format": "json",
        "description": "Master.mp4 final review verdict (qwen-eye over 8 "
                       "uniform frames: color continuity / subtitle / "
                       "watermark / black frames / defects). ADVISORY — "
                       "never changes P13 delivery semantics",
        "writer_phase": "p13_delivery",
        "reader_phases": ["p14_quality_audit"],
    },
    "feedback-log": {
        "file": "feedback-log.json",
        "format": "json",
        "description": "Cross-episode reflection summary (P15 — knowledge feedback loop WRITE side)",
        "writer_phase": "p15_feedback",
        "reader_phases": [],
    },

    # ── Notion《首尾帧设计》新资产类型占位 slot ──────────────────────
    # 这些是纯占位 slot：管线尚未实装生成逻辑，phase 模块不写入。writer_phase
    # 故意设为 None —— 若设为产出 phase（如 p07_scene_generation），_validate_phase_outputs
    # （runner.py Layer 3）会强制要求该 phase 写入此 slot，未写入即 raise
    # AssetBusError → 整集 run 失败、无法产出 master.mp4（违反「主线必须跑通」）。
    # 与现有 requirement / hook-candidates / fix-disabled 等 None-writer 占位 slot 同构。
    # 待后续 phase 实装生成时，再把 writer_phase + _PHASE_EXPECTED_COUNTS + phase
    # 写入三者一并补上。canvas_sync 的节点映射（_PHASE_OUTPUT_MAP）已就位，
    # 一旦 phase 在 result.outputs emit 对应 key，画布节点自动出现。
    "scene-blueprint": {
        "file": "scene-blueprint.json",
        "format": "json",
        "description": "Scene blueprint (空间结构+灭点+地标坐标) — Notion §1.2a",
        "writer_phase": None,
        "reader_phases": ["p09_shot_breakdown", "p11_video_render"],
    },
    "scene-temporal-variants": {
        "file": "scene-temporal-variants.json",
        "format": "json",
        "description": "Scene temporal variants (时段/天气变体矩阵) — Notion §1.2b",
        "writer_phase": None,
        "reader_phases": ["p09_shot_breakdown"],
    },
    "midframes": {
        "file": "midframes.json",
        "format": "json",
        "description": "Mid-frame keyframes for long shots (>8s) — Notion §2d",
        "writer_phase": None,
        "reader_phases": [],
    },
    "foley-stems": {
        "file": "foley-stems.json",
        "format": "json",
        "description": "Foley independent stems — Notion §5c",
        "writer_phase": None,
        "reader_phases": ["p13_delivery"],
    },
    "bgm-tracks": {
        "file": "bgm-tracks.json",
        "format": "json",
        "description": "BGM tracks — Notion §5d",
        "writer_phase": None,
        "reader_phases": ["p13_delivery"],
    },
    "sfx-tracks": {
        "file": "sfx-tracks.json",
        "format": "json",
        "description": "SFX design tracks (transitions/impacts/atmosphere) — Notion §5e",
        "writer_phase": None,
        "reader_phases": ["p13_delivery"],
    },

    # ── ICA (Intent Contract Architecture) M1 additions — 2026-08-25 ──
    # 设计文档: /home/kai/.hermes/plans/2026-08-25-kmc-intent-contract-architecture.md
    # M1 契约内核三 slot。creative-contracts 是 flag-gated 条件写入
    # （generation_config.consistency.layer == "v2" 才产，默认 off）——
    # writer_phase 故意 None（同 hook-candidates Phase 4 先例）：若设为
    # "p02_outline"，runner Layer 3 (_validate_phase_outputs) 会无条件强制
    # P02 写入该 slot，flag=off 的旧行为零变化（M1 回归锁）与提取失败的
    # 宽松降级（M1 不 fail phase）都无法成立。待 consistency.layer 默认翻
    # v2 后，再按 pipeline-asset-bus-slot-management §3 四步原子启用补齐
    # writer_phase + _PHASE_EXPECTED_COUNTS（当前加 expected_count 会让
    # flag=off 时 P02 恒判 incomplete → resume 无限重跑）。
    "creative-contracts": {
        "file": "creative-contracts.json",
        "format": "json",
        "description": "ICA C1: 结构化创作契约清单（P02 从 requirement+story-framework 提取，Gate 2 operator 确认）",
        "writer_phase": None,  # flag-gated: p02_outline 在 consistency.layer=v2 时写（见上）
        "reader_phases": ["p03_script_audit", "p09_shot_breakdown", "p09b_shot_audit", "p14_quality_audit"],
    },
    # C2 偏离台账：append-only JSONL（read_lines 读，防假 incomplete）。
    # 多 phase 可写（任何 owner phase 申报 deviated 时落一条）→ 无单一
    # writer_phase，与 runner/fix-required 的 None-writer 语义一致。
    "deviation-ledger": {
        "file": "deviation-ledger.jsonl",
        "format": "jsonl",  # append-only — use append_line() / read_lines()
        "description": "ICA C2: 偏离台账（append-only，多 phase 可写 → writer_phase=None）",
        "writer_phase": None,
        "reader_phases": ["p14_quality_audit"],
    },
    # 占位：M3 才启用（世界规则登记簿），现在只占位防下游引用炸。
    "world-canon": {
        "file": "world-canon.json",
        "format": "json",
        "description": "Placeholder (M3) — 世界规则登记簿",
        "writer_phase": None,
        "reader_phases": [],
    },

    # ── M-intent 音乐意图契约 (M1) — 2026-09-18 ─────────────────────
    # 设计文档: docs/music-intent-design.md (f039acfc)。music-intent 是
    # flag-gated 条件写入（generation_config.music_intent.enabled 才产，
    # 默认 off）——writer_phase 故意 None（同 creative-contracts 先例）：
    # 若设为 "p03_script"，runner Layer 3 (_validate_phase_outputs) 会无条件
    # 强制 P03 写入该 slot，flag=off 的旧行为零变化（M1 回归锁）与提取
    # 失败的宽松降级（M1 不 fail phase）都无法成立。待 music_intent.enabled
    # 默认翻 true 后，再按 pipeline-asset-bus-slot-management §3 四步原子
    # 启用补齐 writer_phase + _PHASE_EXPECTED_COUNTS。
    "music-intent": {
        "file": "music-intent.json",
        "format": "json",
        "description": "M-intent: 音乐意图契约（P03 提取情感弧线→音乐决策，P12b 消费）",
        "writer_phase": None,  # flag-gated: p03_form_c 在 music_intent.enabled 时写（见上）
        "reader_phases": ["p12b_audio_composition"],
    },

    # ── NC-VAR-01 (2026-08-26 B2) — narration_comic 文字链槽位 ──────────
    # 解说漫变体 (docs/narration-comic-pipeline-design.md §5) 的前两个产物
    # 槽。注册后 gates.yaml 已锁的 narration 槽条目（nc01-gate 的
    # asset_bus_slots_to_lock）自动生效 —— 锁机制按 ASSET_SCHEMA + yaml
    # 求交，无需额外接线。
    "narration": {
        "file": "narration.json",
        "format": "json",
        "description": "解说词 + 句级切分(narration_comic NC-VAR-01)",
        "writer_phase": "nc01_narration",
        "reader_phases": ["nc02_panel_storyboard", "nc05_tts"],
    },
    "panel-list": {
        "file": "panel-list.json",
        "format": "json",
        "description": "画格分镜序列",
        "writer_phase": "nc02_panel_storyboard",
        "reader_phases": ["nc03_char_sheet", "nc04_panel_gen"],
    },

    # ── NC-VAR-01 (2026-08-27 B3) — 图音链产物槽位 ──────────────────────
    # 与上方 narration/panel-list 同一变体（docs/narration-comic-pipeline-
    # design.md §3 行 3~5）。char-sheets 是 png + 文字描述卡混合载体
    # （sheet 条目带 image_path，配角是纯 desc 卡）；panels/tts-clips 的
    # 物理 png/wav 落 workdir/assets/N0X/，槽 JSON 只携带路径与门结果。
    # drama 变体永不写这三槽（writer_phase 是 nc* id），零交叉。
    "char-sheets": {
        "file": "char-sheets.json",
        "format": "json",
        "description": "角色参考表(turnaround sheet + desc 卡混合)(narration_comic NC-VAR-01)",
        "writer_phase": "nc03_char_sheet",
        "reader_phases": ["nc04_panel_gen"],
    },
    "panels": {
        "file": "panels.json",
        "format": "json",
        "description": "画格图产物清单(per-panel gate_results/seed/degraded)",
        "writer_phase": "nc04_panel_gen",
        "reader_phases": ["nc06_motion"],
    },
    "tts-clips": {
        "file": "tts-clips.json",
        "format": "json",
        "description": "旁白 TTS clip 清单(实测时长回填 timings)",
        "writer_phase": "nc05_tts",
        "reader_phases": ["nc06_motion", "nc07_compose"],
    },

    # ── MV-VAR (2026-10-15) — MV 变体歌曲包槽位 ──────────────────────
    # mv01_song_intake 的结构化产物：渲外定稿歌曲包的契约化 payload
    # （beat_grid/sections/lyric_lines/tracks/license，见
    # mv-variant-dag/DESIGN.md §2.1/§4）。MV 链四个 mv* 相的公共上游；
    # drama/nc 变体永不写本槽（writer_phase 是 mv* id）。注册后 gates.yaml
    # 已锁的 song-package 槽条目（mv01-gate 的 asset_bus_slots_to_lock）
    # 自动生效 —— 锁机制按 ASSET_SCHEMA + yaml 求交，无需额外接线。
    "song-package": {
        "file": "song-package.json",
        "format": "json",
        "description": "渲外歌曲包结构化契约(节拍网格/段落轴/歌词行时间轴/双轨路径)(MV-VAR)",
        "writer_phase": "mv01_song_intake",
        "reader_phases": ["mv02_visual_script", "mv03_music_shot_breakdown",
                          "mv04_vocal_track", "mv05_vocal_mixdown"],
    },
}


class AssetBusError(Exception):
    """Programmer-error exception (unknown slot, format mismatch, missing required)."""


# ─── Module-level helpers (mirror Node.js exports) ───────────────────


def _compute_content_hash(value: Any) -> str:
    """SHA-256 hex of canonical JSON.

    Uses ``sort_keys=True`` for cross-run determinism (differs from Node.js
    insertion-order JSON.stringify, but removes a class of dict-ordering bugs —
    see PATTERNS.md "Differences From Node.js Reference").
    """
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, ensure_ascii=False).encode("utf-8")
    ).hexdigest()


def wrap_envelope(value: Any, derived_from: list[str] | None = None) -> dict:
    """Wrap raw payload in a v3.0 envelope.

    Mirrors ``asset-bus.js:122-129``. Returns a dict with:
      - ``value``: the raw payload
      - ``derived_from``: list of upstream content_hashes (defaults to [])
      - ``content_hash``: SHA-256 hex of ``value``
      - ``schema_version``: ``"3.0"``
    """
    derived_list = list(derived_from) if derived_from else []
    return {
        "value": value,
        "derived_from": derived_list,
        "content_hash": _compute_content_hash(value),
        "schema_version": SCHEMA_VERSION,
    }


def unwrap_envelope(raw: Any) -> Any:
    """Return ``raw["value"]`` if ``raw`` is a v3.0 envelope, else return ``raw`` unchanged.

    Backward-compatible with v2.0 raw JSON: a plain dict without
    ``schema_version == "3.0"`` and a ``value`` key passes through untouched.
    Arrays are never envelopes. Mirrors ``asset-bus.js:136-143``.
    """
    if (
        isinstance(raw, dict)
        and not isinstance(raw, list)
        and raw.get("schema_version") == SCHEMA_VERSION
        and "value" in raw
    ):
        return raw["value"]
    return raw


def _atomic_write_text(path: Path, data: str) -> None:
    """Atomic write: tmp file + ``os.replace`` (POSIX rename atomicity).

    Mirrors Node.js ``asset-bus.js:160-165`` (``writeFile`` + ``rename``).
    The tmp filename embeds pid + ms timestamp + urandom hex for uniqueness
    across concurrent producers within one process.

    On any exception during write, best-effort clean up the tmp file.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_name = (
        f"{path.name}.tmp.{os.getpid()}.{int(time.time() * 1000)}.{os.urandom(3).hex()}"
    )
    tmp_path = path.parent / tmp_name
    try:
        with open(tmp_path, "w", encoding="utf-8") as f:
            f.write(data)
        os.replace(str(tmp_path), str(path))
    except Exception:
        # Best-effort cleanup of tmp residue on failure
        try:
            if tmp_path.exists():
                tmp_path.unlink()
        except OSError:
            pass
        raise


# ─── AssetBus ────────────────────────────────────────────────────────


class AssetBus:
    """Filesystem-backed asset bus over ``.pipeline-assets/``.

    JSON slots round-trip through the v3.0 envelope (``write`` / ``read``).
    JSONL slots (``finetune-dataset``) use ``append_line`` / ``read_lines``.
    All JSON writes are atomic (tmp + ``os.replace``). mtime-based cache
    invalidates on every write for the affected slot.
    """

    # Slots that use append_line/read_lines (Plan 33-04 dispatches on this set).
    # INFORMATIONAL ONLY — the actual dispatch in append_line()/write()/read()/
    # read_lines() consults ASSET_SCHEMA[slot]["format"] directly, NOT this
    # frozenset (verified Phase 40-01). Kept UNCHANGED (rapid-preview-clips
    # NOT added) to preserve the V5.0 invariant asserted by
    # test_asset_bus_phase35_slots.py::test_jsonl_slots_unchanged — the new
    # rapid-preview-clips slot is jsonl-format in ASSET_SCHEMA, which is what
    # the dispatch path actually checks. External tooling that introspects
    # JSONL slots by ASSET_SCHEMA format gets the correct answer; callers that
    # (incorrectly) consult JSONL_SLOTS would miss rapid-preview-clips, but
    # no production code path does so.
    JSONL_SLOTS = frozenset({"finetune-dataset"})

    def __init__(self, workdir: str | Path):
        self._dir = Path(workdir) / ASSETS_DIR
        self._cache: dict[str, Any] = {}

    # ── Cache helpers ──────────────────────────────────────────────

    def _cache_key(self, slot: str) -> str | None:
        """Return ``f"{slot}:{mtime_ns}"`` or None if file missing / slot unknown."""
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            return None
        path = self._dir / schema["file"]
        try:
            st = path.stat()
        except FileNotFoundError:
            return None
        return f"{slot}:{st.st_mtime_ns}"

    def _invalidate_cache(self, slot: str) -> None:
        """Delete all cache entries for ``slot`` (mtime change → next read misses)."""
        prefix = f"{slot}:"
        keys_to_delete = [k for k in self._cache if k.startswith(prefix) or k == slot]
        for k in keys_to_delete:
            del self._cache[k]

    # ── JSON slot API ──────────────────────────────────────────────

    def write(
        self,
        slot: str,
        data: Any,
        *,
        envelope: bool = True,
        derived_from: list[str] | None = None,
    ) -> str:
        """Atomically write a JSON slot, wrapping in the v3.0 envelope by default.

        ``derived_from`` non-empty forces envelope even when ``envelope=False``
        (mirrors ``asset-bus.js:206-213`` — Phase 23 change so that
        ``content_hash`` linkage required by CreativeHistoryTracker is always
        recorded). Returns the absolute path written.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") == "jsonl":
            raise AssetBusError(
                f"Slot {slot} is JSONL — use append_line() instead of write()"
            )

        derived_list = list(derived_from) if derived_from else []
        # derived_from non-empty forces envelope (asset-bus.js:210)
        use_envelope = (len(derived_list) > 0) or envelope
        payload = wrap_envelope(data, derived_list) if use_envelope else data

        path = self._dir / schema["file"]
        _atomic_write_text(path, json.dumps(payload, indent=2, ensure_ascii=False))

        # Invalidate stale entries for this slot (mtime changed → new key)
        self._invalidate_cache(slot)
        # Prime cache with the current mtime key
        key = self._cache_key(slot)
        if key is not None:
            self._cache[key] = payload
        return str(path)

    def read(self, slot: str) -> Any | None:
        """Read a JSON slot, auto-unwrapping the v3.0 envelope.

        Returns None if the file is missing or unparseable. Raises
        ``AssetBusError`` for unknown slots and JSONL slots.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") == "jsonl":
            raise AssetBusError(
                f"Slot {slot} is JSONL — use read_lines() instead of read()"
            )

        key = self._cache_key(slot)
        if key is not None and key in self._cache:
            return unwrap_envelope(self._cache[key])

        try:
            raw = (self._dir / schema["file"]).read_text(encoding="utf-8")
            parsed = json.loads(raw)
        except (FileNotFoundError, json.JSONDecodeError):
            return None
        if key is not None:
            self._cache[key] = parsed
        return unwrap_envelope(parsed)

    def read_envelope(self, slot: str) -> dict | None:
        """Read raw parsed content (no unwrap) — useful for inspecting metadata.

        Returns None on missing/unparseable file. Raises AssetBusError for
        unknown or JSONL slots.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") == "jsonl":
            raise AssetBusError(
                f"Slot {slot} is JSONL — use read_lines() instead of read_envelope()"
            )
        try:
            raw = (self._dir / schema["file"]).read_text(encoding="utf-8")
            return json.loads(raw)
        except (FileNotFoundError, json.JSONDecodeError):
            return None

    def require(self, slot: str) -> Any:
        """Read a slot, raising ``AssetBusError`` if the file is missing."""
        data = self.read(slot)
        if data is None:
            raise AssetBusError(f"Required asset '{slot}' not found in {self._dir}")
        return data

    # ── JSONL slot API ─────────────────────────────────────────────

    def append_line(self, slot: str, line_obj: dict) -> str:
        """Append one JSONL line to a jsonl-format slot.

        Uses ``open(..., "a")`` (O_APPEND) — mirrors Node.js ``fs.appendFile``
        without ``fsync``. Returns the absolute path written.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") != "jsonl":
            raise AssetBusError(
                f"Slot {slot} is not JSONL — use write() instead of append_line()"
            )
        path = self._dir / schema["file"]
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "a", encoding="utf-8") as f:
            f.write(json.dumps(line_obj, ensure_ascii=False) + "\n")
        self._invalidate_cache(slot)
        return str(path)

    def read_lines(self, slot: str) -> list[dict]:
        """Read all non-blank lines of a jsonl slot as parsed dicts.

        Returns [] on missing file. Raises AssetBusError for unknown or
        non-JSONL slots.
        """
        schema = ASSET_SCHEMA.get(slot)
        if not schema:
            raise AssetBusError(f"Unknown asset: {slot}")
        if schema.get("format") != "jsonl":
            raise AssetBusError(
                f"Slot {slot} is not JSONL — use read() instead of read_lines()"
            )
        try:
            raw = (self._dir / schema["file"]).read_text(encoding="utf-8")
        except FileNotFoundError:
            return []
        return [json.loads(line) for line in raw.split("\n") if line.strip()]

    # ── Introspection ──────────────────────────────────────────────

    def list_asset_names(self) -> list[str]:
        """Return all registered slot names (copy of ASSET_SCHEMA keys)."""
        return list(ASSET_SCHEMA.keys())
