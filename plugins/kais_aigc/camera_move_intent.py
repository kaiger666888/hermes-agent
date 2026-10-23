"""camera_move_intent.py — 中文 camera_move 意图 → KAP auto_attach trigger 映射 (批次2, 2026-09-28).

KAP :10588 /api/production/minimax-h3/generate 于批次1 (commit 8c794fcf,
2026-09-28 上午) 上线意图驱动 auto_attach: 请求带 ``camera_move: <trigger>``
字段 → registry 查表 ``auto_attach.trigger === "camera_move:<trigger>"`` →
自动挂载 production LoRA (首例 crash-zoom@0.8)。本模块是 KMC 消费端的意图
映射层: P09 中文运镜枚举 → KAP trigger 语义, 供 video_engine._build_multipart
在无显式 h3_lora 配置时透传 (优先级: 显式 lora > auto_attach > 无, Kai 0927
设计律)。

设计律「宁缺毋滥」的落点: 映射表只收 crash_zoom 增益域内的确定语义项
(r6 定谳: crash-zoom 的增益域是「冲击感推近」族)。固定/手持/跟随/缓慢推进
等日常运镜一律不入表 —— prompt 本来就能执行, 挂 LoRA 反而引入风格漂移,
正是决策律要防的事。registry 将来新增 trigger 时按同一标准扩表 (逐项补
映射理由注释, 拿不准的不收)。

纯函数模块: 无 I/O、无日志、不改入参 —— 无 raise 路径 (isinstance 守卫 +
dict.get), 未命中一律 None, 降级语义由 video_engine 装配侧 (不发字段照常
渲染) 与 KAP 侧 (装配失败 prompt-only) 共同保证。
"""
from __future__ import annotations

# 中文枚举值 → KAP trigger 语义。键集受控: 必须是 564 镜实况词表的子集
# (词表快照见 tests/test_camera_move_intent.py VOCABULARY_564), 值域 =
# registry 在册 trigger (当前仅 crash-zoom 一条带 auto_attach;
# fos-motion-speed-slider 是 overlay 串链语义, 设计上不参与 auto_attach,
# 勿往这里加)。每项注释给出映射理由 —— 扩表时逐项补注。
CAMERA_MOVE_TRIGGERS: dict[str, str] = {
    # 变焦推 (564 镜 ×31): 「冲向镜头」的字面对应 —— crash_zoom 名义主项。
    "变焦推": "crash_zoom",
    # 快速推进 (×18): 推近 + 快速 = 冲击感推近族正成员。「缓慢推进」(×99)
    # 速度语义相反, 不入表 —— 一字之差两个世界, 正是只做精确匹配的理由。
    "快速推进": "crash_zoom",
    # 快速拉远 (×1): 反向冲击 (whip-out) —— crash-zoom LoRA 的增益是冲击感
    # 运镜本身, 推/拉两向同享。「缓慢拉远」(×36) 同理不入表。
    "快速拉远": "crash_zoom",
    # 甩镜 (×2): whip-pan 高速甩动, 冲击感运镜族的横移近亲。
    "甩镜": "crash_zoom",
}


def resolve_camera_move_trigger(shot: dict) -> str | None:
    """读 shot 运镜意图 → KAP auto_attach trigger 语义 | None。

    - 字段口径: ``camera_move`` (P09 L2 产出口径) 优先, ``camera_movement``
      旧拼写 or-兜底 (同形先例 p09_shot_breakdown.py:946)。
    - 精确匹配 CAMERA_MOVE_TRIGGERS; 空值/非 str/非 dict/未命中一律返回
      None —— 不猜、不模糊匹配: 中文枚举是受控词表, 模糊匹配会把
      「缓慢推进」误升级成 crash_zoom, 正好违反「宁缺毋滥」决策律。
    - 纯函数: 不改 shot dict, 不读盘, 不打日志 (装配日志归
      video_engine._build_multipart)。
    """
    if not isinstance(shot, dict):
        return None
    move = shot.get("camera_move") or shot.get("camera_movement")
    if not isinstance(move, str) or not move:
        return None
    return CAMERA_MOVE_TRIGGERS.get(move)
