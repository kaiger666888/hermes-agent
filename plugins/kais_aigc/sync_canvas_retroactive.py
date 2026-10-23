#!/usr/bin/env python3
"""sync_canvas_retroactive.py — 补同步：把已跑完的管线 phase 重新灌入无限画布。

背景
----
KMC 管线 ``ep-chongchong-ppt-01`` 已跑完 P01–P10c + 部分 P11b，但画布几乎是
空的（canvas_nodes 只有 4 个 P11 节点；P01–P10 的 zone/phase 节点完全缺失，
``a-*`` artifact 子节点一个都没有）。

根因（详见 canvas_sync.py 注释）：
  1. 早期 v2 运行时 ``CanvasSyncSubscriber.on_phase_complete`` 对 P01–P10 要么没
     被注册、要么抛错被 degrade-tolerant 兜底静默吞掉；
  2. 后续 v8–v19 从 checkpoint 恢复时，``runner._compute_start_index`` 直接跳过
     已完成 phase（``for idx in range(start_idx, ...)``），被跳过的 phase 永远
     不会再触发 ``on_phase_complete`` → 画布节点永久缺失。

本脚本就是那条「补同步」路径：绕过 runner 的 skip 逻辑，按 PHASE_REGISTRY 顺序
逐个 phase 重新调用同一个 ``CanvasSyncSubscriber.on_phase_complete``，把缺失的
zone / phase / artifact / candidate / link 节点全部补回去。

关键设计
--------
* **单一持久 subscriber**：全程复用同一个 ``CanvasSyncSubscriber`` 实例，按
  registry 顺序处理，保证 ``_prev_phase_id`` 链式 ``n-{prev}→n-{cur}`` 连边正确
  （每个 phase 独立建一个 fresh subscriber 会让链断掉）。
* **结果重建**：
    - 完整 phase（P01–P10 等）：直接用 ``.pipeline-state.json`` 里
      ``phases[p]["result"]["result"]``（含 ``outputs``）。
    - 子步骤 phase（p09c / p11a / p11b）：checkpoint 只存
      ``{phase,status,rollback_to}``，没有 outputs → 从
      ``.pipeline-assets/*.json``（SSOT wrapper，``value`` 字段）重建
      ``outputs``。
* **不静默吞错**：每个 phase 的 on_phase_complete 结果都显式上报（OK / 软失败 /
  硬失败），并在结束时打印汇总表 + 非零退出码。这是对「问题2：on_phase_complete
  被静默吞」的直接补丁——live 运行保留 degrade-tolerant（不阻塞管线），但补同步
  场景必须让操作者看到每个 phase 到底成没成。
* **所有 DB 写入走 save-v2 HTTP API**：本脚本只调用 ``on_phase_complete``（内部
  load_canvas→build→save_canvas 走 ``/api/canvas/v2/save-v2``），不直接写 sqlite。
  o_assets/o_image 的写入沿用 subscriber 既有路径（canvas_sync.py 既设计如此）。
* **幂等**：可重复运行；on_phase_complete 内部 upsert + retry-cleanup，重跑只会
  刷新节点。P11b 还在跑（6/20）时也可以跑——未渲染的 shot 会生成指向尚不存在
  文件的 video 节点（pending），等 P11b 跑完再跑一次即更新。

用法
----
可作为直接脚本运行，也可用 ``python -m`` 从仓库根目录运行（推荐，路径更稳）::

    # 默认：同步 ep-chongchong-ppt-01 全部已完成 phase
    python3 -m plugins.kais_aigc.sync_canvas_retroactive
    # 等价于：
    python3 plugins/kais_aigc/sync_canvas_retroactive.py

    # 指定 episode 目录 / project_id / episodes_id（--episode 可选，仅覆盖 id）
    python3 -m plugins.kais_aigc.sync_canvas_retroactive \\
        --episode ep-chongchong-ppt-01 \\
        --workdir /data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/episodes/ep-chongchong-ppt-01 \\
        --project-id 1786428475193 --episodes-id 1

    # 只看会同步哪些 phase，不真正写画布
    python3 -m plugins.kais_aigc.sync_canvas_retroactive --dry-run

    # 只补某几个 phase
    python3 -m plugins.kais_aigc.sync_canvas_retroactive --only p04_character_design,p11b_final_render

    # 即便 phase 在 state 里不是 completed，只要有重建文件就同步（默认即如此，
    # 用于把 in-progress 的 p11b 视频也灌进去）
    python3 -m plugins.kais_aigc.sync_canvas_retroactive --include-in-progress

约束
----
* 不修改 runner.py 的核心执行逻辑（本脚本完全不碰 runner）。
* 保持 degrade-tolerant：单 phase 失败不影响其它 phase，只上报不中断。
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
import traceback
from typing import Any

# ── 让 plugins.* 与 tools.* 可被导入 ───────────────────────────────────
# canvas_sync.py 属于 kais-hermes-skills（提供 `plugins` 包），但其 __init__
# 依赖 hermes-agent 的 `tools` 包（tools.registry）。两个仓库根都要上 sys.path。
_KAIS_ROOT = "/data/workspace/kais-hermes-skills"      # → plugins.kais_aigc
_HERMES_ROOT = "/data/workspace/hermes-agent"           # → tools.registry
for _root in (_KAIS_ROOT, _HERMES_ROOT):
    if os.path.isdir(_root) and _root not in sys.path:
        sys.path.insert(0, _root)

# canvas_sync 在 import 时不会触发 I/O，可安全 import。
from plugins.kais_aigc.canvas import CanvasClient, CanvasClientError  # noqa: E402
from plugins.kais_aigc.canvas_sync import (  # noqa: E402
    CanvasSyncSubscriber,
    CanvasSyncValidationError,
    _ensure_project_exists,
)

logger = logging.getLogger("sync_canvas_retroactive")

# ── PHASE_REGISTRY 顺序（与 pipeline/phases/__init__.py 保持一致）────────
# 顺序至关重要：subscriber 的 _prev_phase_id 链式连边依赖这个顺序。这里硬编码是
# 为了避免 import pipeline 包（会拖入大量依赖 / 副作用）。registry 若新增 phase，
# 这里同步追加即可。
#
# B-5（2026-08-16）僵尸清理：p05_pain_points（2026-07-28 DIALOGUE-REFORM
# 注销）与 p10b_rapid_preview（board 职责迁往 p11a 后注销）已从
# PHASE_REGISTRY 移除——保留在这里只会让 retroactive 白查一个永不存在的
# checkpoint（旧 episode 若真有 p10b 状态，其产物槽 storyboard-board 由
# p09c 条目重建、rapid-preview-clips.jsonl 由 p11a 条目重建，不丢数据）。
# 一致性由 test_phase_registry_canvas_map_consistency.py 锁定
# （PHASE_REGISTRY_ORDER ⊆ 现役 registry）。
PHASE_REGISTRY_ORDER: list[str] = [
    "p01_hook_topic",
    "p02_outline",
    "p03_script_audit",
    "p035_dramatic_polish",     # P03.5 86ke 戏剧事件打磨（micro-phase, 2026-08-15）
    "p036_hook_reconcile",      # ICA M2 2026-08-25: C4b 钩子再实例化
    "p04_character_design",
    "p06_spatio_temporal_script",
    "p07_scene_generation",
    "p08_scene_selection",
    "p09_shot_breakdown",
    "p09b_shot_audit",
    "p09c_storyboard_board",
    "p10_voice",
    "p10c_voice_audit",
    "p11a0_iframe_qc",          # P11a0 条件帧自动审核（qwen-eye, 2026-08-16）
    "p11a_preview_clips",       # p10b_rapid_preview 的后继（preview 职责; board 职责 2026-09-28 退役）
    "p11a5_preview_audio",      # P11a.5 预演音频+成片（2026-08-24 落地; PRG-02 补登记）
    "p11b_final_render",
    "p11c_video_qc",             # P11c 视频智能质检 (qwen-eye, 2026-08-15)
    "p12a_timeline_composition",
    "p12b_audio_composition",
    "p13_delivery",
    "p14_quality_audit",
    "p15_feedback",
]

# state 里视为「已完成」的 status（与 PipelineStateStore.DONE_STATUSES 对齐）。
_DONE_STATUSES = frozenset({"completed", "approved", "awaiting_review"})

# 子步骤 phase → (SSOT 文件名, 重建到 outputs 的 key)。
# 这些 phase 的 checkpoint 不存 result.result（只有 {phase,status,rollback_to}），
# 必须从 .pipeline-assets/<file> 重建 outputs。JSON 文件读 ``value`` 字段
# （SSOT wrapper），JSONL 文件逐行读取返回 list（见 _load_substep_value）。
#   - p09c: storyboard-board.json → storyboard_board（分镜故事板 dict）
#   - p11a: rapid-preview-clips.jsonl → rapid_preview_clips（B-5 修复
#     2026-08-16：此前错映到 storyboard-board.json，纯 retroactive 补同步
#     时 31 个预览视频节点全部缺席、timeline 页缺视频。主槽就是
#     rapid_preview_clips——p11a live result.outputs 也带它
#     (p11a_preview_clips.py:1211)。文件是 jsonl 裸行（无 wrapper，实测
#     ep-demo-pixar 31 行 {shot_id,variant_id,clip_path,...}）。storyboard_board
#     覆写仍走 p09c 的重建条目（p11a 的 board 组装已随 2026-09-28 分镜板退役
#     批摘除，不再覆写本槽；p09c 白模链是唯一 writer）。）
#   - p11b: video-clips.json → video_clips（20 个 shot 成片，时间轴所需）
SUBSTEP_RECONSTRUCT: dict[str, tuple[str, str]] = {
    "p09c_storyboard_board": ("storyboard-board.json", "storyboard_board"),
    "p11a_preview_clips": ("rapid-preview-clips.jsonl", "rapid_preview_clips"),
    "p11b_final_render": ("video-clips.json", "video_clips"),
    # P11c 视频质检: video-qc.json → video_qc（per_shot 判定 dict）。
    "p11c_video_qc": ("video-qc.json", "video_qc"),
    # P02 兜底（2026-08-18，ep-ccport-test01）：p02 的 checkpoint 只存
    # {phase,status,rollback_to}（无 result.result），live sync 之后重放
    # 会跳过 p02 → comedy_premise / story_kernel / reversal_blueprint /
    # creative_constraints 等 dict 子节点永久缺失。story-framework.json
    # 是 p02 的 SSOT 槽。⚠️ 不能只灌单键——on_phase_complete 的 retry-cleanup
    # 会删掉该 phase 既有 artifact 节点，单键重建删多补少（ep-ccport-test01
    # 第一次跑丢过 outline_beats×5 + emotion_curve）。走 _rebuild_p02_outputs
    # 按 live 输出键位全形状重组（见其 docstring）。state 有完整 result 的
    # 旧 episode 不受影响（优先级已调整）。
    "p02_outline": ("story-framework.json", "story_framework"),
    # qwen-eye advisory QC expansion (2026-08-16) — storyboard-qc /
    # preview-qc / master-qc land on disk too, but their writer phases
    # (p09c/p11a/p13) all keep full results in pipeline-state (or already
    # own a SUBSTEP entry for their PRIMARY slot). A second entry here is
    # keyed by phase id and would REPLACE that primary reconstruction, so
    # the QC slots rebuild via the live-sync path / state result instead.
    # Retroactive fallback: the phase-overview node still renders, only
    # the per-QC child node is absent on a pure retroactive rebuild.
}


# ── 辅助 ───────────────────────────────────────────────────────────────


def _load_pipeline_state(workdir: str) -> dict[str, Any]:
    """读取 ``<workdir>/.pipeline-state.json``。"""
    path = os.path.join(workdir, ".pipeline-state.json")
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def _load_wrapped_value(workdir: str, fname: str) -> Any:
    """读取 ``.pipeline-assets/<fname>``，返回其 ``value`` 字段（SSOT wrapper）。

    这些文件统一是 ``{value, derived_from, content_hash, schema_version}``；
    真正的 phase 产出在 ``value`` 里。文件不存在/损坏时抛异常由调用方处理。
    """
    path = os.path.join(workdir, ".pipeline-assets", fname)
    with open(path, "r", encoding="utf-8") as f:
        wrapper = json.load(f)
    if isinstance(wrapper, dict) and "value" in wrapper:
        return wrapper["value"]
    return wrapper


def _rebuild_p02_outputs(value: Any) -> dict[str, Any]:
    """把 story-framework 槽 value 重组回 p02 live 输出键位（全形状重建）。

    p02 live ``result.outputs`` 的形状（canvas_sync._PHASE_OUTPUT_MAP["p02"]）：
      * ``story_framework``: {premise, central_conflict, thematic_question,
        character_anchors, …}   ← 槽 value.story_kernel 同形（实测
        ep-ccport-test01 逐键一致）
      * ``outline_beats``: list[beat] ← 槽 value.reversal_chain_blueprint
        同形（beat_name/duration_pct/content/trait_used/hook_strength）
      * ``emotion_curve_summary``: 槽内无对应物，无法重建（保留缺失，
        不造假数据）
      * ``snowflake_artifacts``: 槽内无对应物（live 也未产出节点）

    槽 value 顶层其余字段（comedy_premise / creative_constraints /
    reversal_blueprint / social_resonance_disabled / provenance）并入
    ``story_framework``——它们本就是故事框架的组成字段，dict 子节点展开
    （canvas_sync 2026-08-18）会为它们生成子节点。

    为什么不全量信任槽→live 的映射：on_phase_complete 的 retry-cleanup
    会删除 phase 既有 artifact 节点。若重建输出缺 live 曾有的键
    （outline_beats），cleanup 会把对应节点删掉且新输出补不回——删多补少。
    本函数按 live 键位重组，保证 cleanup 删掉的都能被重建覆盖。
    """
    if not isinstance(value, dict):
        return {"story_framework": value}
    outputs: dict[str, Any] = {}
    sk = value.get("story_kernel")
    framework: dict[str, Any] = dict(sk) if isinstance(sk, dict) else {}
    for k, v in value.items():
        if k in ("story_kernel", "reversal_chain_blueprint", "provenance"):
            continue
        framework.setdefault(k, v)
    outputs["story_framework"] = framework
    rcb = value.get("reversal_chain_blueprint")
    if isinstance(rcb, list) and rcb:
        outputs["outline_beats"] = rcb
    return outputs


def _load_substep_value(workdir: str, fname: str) -> Any:
    """按扩展名分派：``.jsonl`` 逐行读成 list，其余走 SSOT wrapper。

    B-5（2026-08-16）：``rapid-preview-clips.jsonl`` 是 jsonl 裸行格式
    （每行一个 variant dict，无 ``value`` wrapper —— 实测 ep-demo-pixar
    31 行 ``{shot_id, variant_id, clip_path, ...}``）。直接套
    ``_load_wrapped_value`` 会把整段文本当 JSON parse 失败。这里补 JSONL
    读取分支：非空行逐行 ``json.loads``，坏行抛异常由调用方上报
    （reconstruct-failed），不静默跳过。
    """
    if fname.endswith(".jsonl"):
        path = os.path.join(workdir, ".pipeline-assets", fname)
        with open(path, "r", encoding="utf-8") as f:
            lines = [ln for ln in f.read().split("\n") if ln.strip()]
        return [json.loads(ln) for ln in lines]
    return _load_wrapped_value(workdir, fname)


def _reconstruct_result(
    phase_id: str,
    entry: dict[str, Any] | None,
    workdir: str,
) -> tuple[dict[str, Any], str]:
    """重建传给 ``on_phase_complete`` 的 ``result`` dict。

    Returns:
        ``(result, source)`` —— source 描述数据来源（用于日志）。
    """
    # 优先级（2026-08-18 调整）：state 完整 result > 槽文件重建。
    # 此前 SUBSTEP_RECONSTRUCT 先于 state 检查——对 p09c/p11a/p11b/p11c
    # 无影响（它们的 checkpoint 按设计只存 {phase,status,rollback_to}，
    # state 永远无 result.result），但 p02_outline 这类「完整 phase +
    # 槽文件兜底」的新映射会让存有完整 result 的旧 episode 降级成只灌
    # 单槽数据（丢 outline_beats / emotion_curve_summary 等其余 outputs）。
    # state 有的永远用 state；state 没有再看槽文件。
    if entry is not None:
        payload = entry.get("result") or {}
        inner = payload.get("result") if isinstance(payload, dict) else None
        if isinstance(inner, dict):
            # on_phase_complete 期望 {phase, outputs, gate, ...}；inner 正是此形。
            return inner, "state.result.result"

    spec = SUBSTEP_RECONSTRUCT.get(phase_id)
    if spec:
        fname, out_key = spec
        value = _load_substep_value(workdir, fname)
        # p02 走全形状重建（按 live 输出键位重组，防 cleanup 删多补少）。
        if phase_id == "p02_outline":
            outputs = _rebuild_p02_outputs(value)
        else:
            outputs = {out_key: value}
        return (
            {"phase": phase_id, "outputs": outputs, "gate": None},
            f"sub-step file {fname}",
        )

    if entry is not None:
        # 有 entry 但没有嵌套 result（异常 checkpoint）→ 至少建 zone+phase 节点。
        return (
            {"phase": phase_id, "outputs": {}, "gate": None},
            "state (no outputs — zone/phase node only)",
        )

    return {"phase": phase_id, "outputs": {}, "gate": None}, "minimal (no entry)"


# ── 主流程 ─────────────────────────────────────────────────────────────


def run(
    *,
    workdir: str,
    project_id: int,
    episodes_id: int,
    base_url: str,
    only: set[str] | None,
    include_in_progress: bool,
    dry_run: bool,
    episode_override: str | None = None,
) -> int:
    """执行补同步。返回进程退出码（0=全成功，1=有硬失败，2=有软失败）。"""
    os.environ["KAIS_RUN_WORKDIR"] = workdir  # subscriber 据此解析媒体路径

    state = _load_pipeline_state(workdir)
    episode_id = (
        episode_override
        or state.get("episode")
        or os.path.basename(workdir.rstrip("/"))
    )
    phases_state: dict[str, Any] = state.get("phases") or {}
    logger.info("episode=%s  workdir=%s", episode_id, workdir)

    # 决定要同步哪些 phase（保留 registry 顺序）。
    todo: list[str] = []
    skip_report: list[tuple[str, str]] = []
    for phase_id in PHASE_REGISTRY_ORDER:
        if only and phase_id not in only:
            continue
        entry = phases_state.get(phase_id)
        spec = SUBSTEP_RECONSTRUCT.get(phase_id)
        status = (entry or {}).get("status")
        if spec:
            # 子步骤：有重建文件就同步（覆盖 in-progress 的 p11b）。
            fname = spec[0]
            if not os.path.isfile(os.path.join(workdir, ".pipeline-assets", fname)):
                skip_report.append((phase_id, f"sub-step but {fname} missing"))
                continue
            if status not in _DONE_STATUSES and not include_in_progress and not dry_run:
                # 默认仍允许子步骤（p11b in-progress 正是本脚本要补的），
                # 这里仅记录状态供日志可见。
                pass
            todo.append(phase_id)
        elif entry is not None and status in _DONE_STATUSES:
            todo.append(phase_id)
        else:
            skip_report.append(
                (phase_id, f"status={status or 'absent'} (not completed)")
            )

    logger.info("phases to sync: %s", ", ".join(todo) or "(none)")
    for phase_id, why in skip_report:
        logger.info("  skip %s — %s", phase_id, why)

    if dry_run:
        print("\n=== DRY RUN — would sync these phases (in order) ===")
        for phase_id in todo:
            entry = phases_state.get(phase_id)
            try:
                _result, source = _reconstruct_result(phase_id, entry, workdir)
                outs = _result.get("outputs") or {}
                keys = list(outs.keys()) if isinstance(outs, dict) else []
                counts = {
                    k: len(v) for k, v in outs.items()
                    if isinstance(v, (list, dict))
                }
                print(f"  {phase_id:32s} [{source}]  outputs={keys}  sizes={counts}")
            except Exception as exc:  # noqa: BLE001
                print(f"  {phase_id:32s} [RECONSTRUCT FAILED] {exc}")
        print(f"\n({len(todo)} phase(s) would be synced; {len(skip_report)} skipped)")
        return 0

    # ── 构造单一持久 subscriber（保证 _prev_phase_id 链式连边）──────────
    _ensure_project_exists(base_url, project_id)
    client = CanvasClient(
        base_url=base_url,
        project_id=project_id,
        episodes_id=episodes_id,
    )
    sub = CanvasSyncSubscriber(client)

    results: list[dict[str, Any]] = []

    for phase_id in todo:
        entry = phases_state.get(phase_id)
        try:
            result, source = _reconstruct_result(phase_id, entry, workdir)
        except Exception as exc:  # noqa: BLE001 — 重建失败不应中断其它 phase
            logger.error("RECONSTRUCT FAILED %s: %s", phase_id, exc, exc_info=True)
            results.append({
                "phase": phase_id, "outcome": "reconstruct-failed",
                "detail": f"{type(exc).__name__}: {exc}",
            })
            continue

        logger.info(">>> syncing %s (source=%s)", phase_id, source)
        try:
            sub.on_phase_complete(episode_id, phase_id, result)
            results.append({"phase": phase_id, "outcome": "ok", "detail": source})
            logger.info("    OK  %s", phase_id)
        except (CanvasClientError, CanvasSyncValidationError) as exc:
            # live 运行里这俩会停管线；补同步场景只上报、继续。
            logger.error(
                "HARD-FAIL %s: %s", phase_id, exc, exc_info=True,
            )
            results.append({
                "phase": phase_id, "outcome": "hard-fail",
                "detail": f"{type(exc).__name__}: {exc}",
            })
        except Exception as exc:  # noqa: BLE001 — 其余异常：上报但不中断
            logger.error(
                "soft-fail %s: %s", phase_id, exc, exc_info=True,
            )
            results.append({
                "phase": phase_id, "outcome": "soft-fail",
                "detail": f"{type(exc).__name__}: {exc}",
            })

    # ── 汇总 ───────────────────────────────────────────────────────────
    print("\n" + "=" * 72)
    print(f" RETROACTIVE CANVAS SYNC — {episode_id} (project={project_id} ep={episodes_id})")
    print("=" * 72)
    by_outcome: dict[str, int] = {}
    for r in results:
        by_outcome[r["outcome"]] = by_outcome.get(r["outcome"], 0) + 1
    for r in results:
        flag = {
            "ok": "OK ",
            "soft-fail": "WARN",
            "hard-fail": "ERR ",
            "reconstruct-failed": "ERR ",
        }.get(r["outcome"], "?? ")
        print(f"  [{flag}] {r['phase']:32s} {r['outcome']:18s} {r['detail'][:60]}")
    print("-" * 72)
    print(f"  synced={by_outcome.get('ok', 0)}  "
          f"soft-fail={by_outcome.get('soft-fail', 0)}  "
          f"hard-fail={by_outcome.get('hard-fail', 0)}  "
          f"reconstruct-failed={by_outcome.get('reconstruct-failed', 0)}  "
          f"skipped={len(skip_report)}")
    print("=" * 72)

    # 退出码：硬失败/重建失败 → 1；仅有软失败 → 2；全 OK → 0。
    if by_outcome.get("hard-fail", 0) or by_outcome.get("reconstruct-failed", 0):
        return 1
    if by_outcome.get("soft-fail", 0):
        return 2
    return 0


def _parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="补同步：把已完成管线 phase 重新灌入无限画布（走 save-v2）。",
    )
    p.add_argument(
        "--workdir",
        default="/data/workspace/kais-hermes-skills/skills/kais-movie-pipeline/"
                "episodes/ep-chongchong-ppt-01",
        help="episode 工作目录（含 .pipeline-state.json 与 assets/）",
    )
    p.add_argument(
        "--episode",
        default=None,
        help="episode id 覆盖（默认从 .pipeline-state.json 的 episode 字段或 "
             "workdir 目录名推导）。多数情况无需指定。",
    )
    p.add_argument("--project-id", type=int, default=1786428475193)
    p.add_argument("--episodes-id", type=int, default=1)
    p.add_argument(
        "--base-url",
        default=os.environ.get("KAIS_CANVAS_URL", "http://127.0.0.1:10588"),
        help="canvas 平台地址（默认读 KAIS_CANVAS_URL）",
    )
    p.add_argument(
        "--only",
        default="",
        help="只同步这些 phase（逗号分隔，如 p04_character_design,p11b_final_render）",
    )
    p.add_argument(
        "--include-in-progress",
        action="store_true",
        help="对子步骤 phase，即便 state 非完成也同步（默认即允许，用于 p11b）",
    )
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="只打印会同步哪些 phase + 重建出的 outputs，不写画布",
    )
    p.add_argument(
        "-v", "--verbose", action="store_true", help="DEBUG 级别日志",
    )
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = _parse_args(argv if argv is not None else sys.argv[1:])
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s %(levelname)-7s %(name)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    only = {s.strip() for s in args.only.split(",") if s.strip()} or None

    # 基本前置检查
    if not os.path.isfile(os.path.join(args.workdir, ".pipeline-state.json")):
        print(f"ERROR: 找不到 {args.workdir}/.pipeline-state.json", file=sys.stderr)
        return 3
    if not args.base_url:
        print("ERROR: 缺少 canvas base_url（用 --base-url 或设 KAIS_CANVAS_URL）", file=sys.stderr)
        return 3

    try:
        return run(
            workdir=args.workdir,
            project_id=args.project_id,
            episodes_id=args.episodes_id,
            base_url=args.base_url,
            only=only,
            include_in_progress=args.include_in_progress,
            dry_run=args.dry_run,
            episode_override=args.episode,
        )
    except FileNotFoundError as exc:
        print(f"ERROR: 文件缺失 — {exc}", file=sys.stderr)
        traceback.print_exc()
        return 3
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        traceback.print_exc()
        return 3


if __name__ == "__main__":
    sys.exit(main())
