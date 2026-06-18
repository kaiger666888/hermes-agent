# V8.6 Pipeline Mapping — kais-movie-agent V8.6 13-Step → hermes-agent expert_id Canonical Reference

**Source:** kais-movie-agent V8.6 SKILL.md (commit `e41fa68`, 2026-06-18 22:56:46 +0800) §"hermes-agent 专家 → 管线 Step 速查" + §"V8.6 更新" + §"V8.5 更新" + §"V8.4 更新" + §"强制审核门 (Review Gate)". Located at `/data/workspace/kais-movie-agent/SKILL.md`.
**Copyright:** Fair Use — (1) V8.6 Step-to-expert mapping is factual integration architecture of the open-source kais-movie-agent project, not copyrightable expression; (2) the 8-gate structure classification + atomic-operation annotations are original Hermes Agent analytical encoding layer; (3) brief verbatim quotations from kais-movie-agent V8.6 update notes are explicitly attributed and within fair-use citation context (≤ 50 words per quotation).
**Last-verified:** 2026-06-19
**verified_date:** 2026-06

---

## Summary

本 ref 是 hermes-agent 16 个 active movie-experts 与 kais-movie-agent V8.6 13 步管线之间的**canonical mapping**(权威映射表)。所有 movie-expert 的 V8.6 Pipeline Sync sections(critical for v5.0 milestone)都引用此映射作为单一事实源。

**V8.6 vs V8.4-before 关键差异:**
- 管线精简 25→13 步(6 组合并)
- 审核门 12→8 个(用户等待轮次减半)
- Expert 调用 15→10 次(省去冗余 ACP 调用)
- dreamina CLI 取代 jimeng-client.js(V8.5)
- L1-L4 角色资产库完整化(V8.5)

---

## V-Version Provenance

| 版本 | commit | 日期 | 关键变化 |
|------|--------|------|---------|
| V8.4 | `4fb57b4` | 2026-06-18 21:36 | 专家映射全面更新(确认 hermes-agent v3.0 N:1 merges / renames / NEW prompt_injector) |
| V8.5 | `c22867d` | 2026-06-18 22:17 | dreamina CLI 取代 jimeng-client.js + Step 7 角色资产库完整化(L1-L4) |
| V8.6 | `e41fa68` | 2026-06-18 22:56 | 管线精简 25→13 步,审核门 12→8 个,Expert 调用 15→10 次 |

---

## The 13-Step V8.6 Pipeline → expert_id Mapping

> 来源:kais-movie-agent V8.6 SKILL.md §"hermes-agent 专家 → 管线 Step 速查" + §"V8.6 更新" §1-§6 atomic merges

| V8.6 Step | 用途 | 主调用 expert_id | 协同 expert_id | 原始 Step (V8.4 前) | V8.6 §x 合并 |
|-----------|------|-----------------|---------------|---------------------|-------------|
| **Step 1** | 爆款选题雷达 + 主题生成(atomic) | `hook_retention` | — | Step 1 + Step 2 | §1 |
| **Step 2** | 故事框架 + 大纲(atomic) | `creative_source` + `screenplay` | — | Step 2.5 + Step 3 | §2 |
| **Step 3** | 剧本 + 审计(atomic) | `screenplay` + `script_auditor` | — | Step 5 + Step 5B + Step 6 | §3 |
| **Step 4** | 主角设计 + 资产库 | `character_designer` + `visual_executor`(drawer) | — | Step 4 + Step 6 | (no merge,保留) |
| **Step 5** | 场景设计 | `cinematographer` + `style_genome` + `visual_executor`(drawer) | — | Step 8 + Step 9 | (no merge,保留) |
| **Step 6** | 运镜 + 终审(atomic) | `screenplay` + `cinematographer` + `script_auditor` | — | Step 11 + Step 12 | (V8.4 §5 前置的延伸) |
| **Step 7** | 视觉种子 + 风格化(atomic) | `visual_executor` + `prompt_injector` + `style_genome` + `colorist` | — | Step 13A + Step 15 | §4 |
| **Step 7B** | 声音骨架 | `audio_pipeline`(voicer + composer + foley sub-steps) | — | Step 13B(V8.4 §5 引入) | (no merge) |
| **Step 8** | 运镜 + 节奏 | `cinematographer` + `editor` | — | Step 14(V8.4 §6 前置) | (no merge) |
| **Step 9** | 一致性检查 | `continuity_auditor` | — | Step 16 | (no merge) |
| **Step 10** | 视频生成 | (dreamina CLI 执行,无 expert_id 调用) | `visual_executor`(animator 监督) | Step 17 | (no merge) |
| **Step 11** | BGM + 音效 + 口型统一(atomic) | `audio_pipeline`(全 6 sub-steps) | — | Step 17B + Step 18 | §6 |
| **Step 12-13** | (未在 V8.6 mapping table 明确,预留扩展) | TBD | — | — | — |

**Step 2.5 style_genome 前置**(per V8.4 §3):style_genome 在 Step 2 故事框架确认后立即调用(Step 2.5 位置),输出 5D 向量贯穿全管线下游。Step 2.5 不是独立 Step,而是 Step 2 与 Step 4 之间的插入位。

### 按需补充调用专家(非主线 Step)

per kais-movie-agent V8.6 SKILL.md §"其他可用专家",以下专家按需调用(非每项目必需):

- `editor`(主线 Step 8 已调用,成片阶段可再次调用做最终剪辑)
- `production`(制作管理 — hermes-agent v3.0 FUTURE-09 deferred)
- `compliance_marketing` → `compliance_gate`(Phase 13 已 rename,V8.6 仍用 compliance_gate)
- `creative_source`(主线 Step 2 已调用,Step 7 视觉种子时可再次调用做创意深化)
- `theory_critic`(consultative,任意 Step 可调用,典型 Step 2/6/9 后)
- `documentary_maker`(纪录片向项目调用)
- `animation_studio`(动画向项目调用)

---

## V8.6 8-Gate Review Structure

> 来源:kais-movie-agent V8.6 SKILL.md §"V8.6 更新" §2 + §"强制审核门 (Review Gate)"

V8.6 把审核门从 12 个减为 8 个,用户等待轮次减半:

| # | V8.6 审核门 | 触发 Step 后 | 涉及专家 | 用户决策内容 |
|---|------------|------------|---------|------------|
| 1 | 选题 + 主题 + hook 候选 | Step 1 后 | hook_retention + compliance_gate(red-line check) | Topic Kernel + hook 候选确认 |
| 2 | 故事框架 + 大纲 | Step 2 后 | creative_source + screenplay + style_genome(5D 向量) | 故事框架 + Snyder 15-beat 确认 |
| 3 | 剧本 + 审计结果 | Step 3 后 | screenplay + script_auditor + compliance_gate | scene-level 剧本 + 5 维审计报告确认 |
| 4 | 角色资产库 | Step 4 后 | character_designer + visual_executor | L1-L4 资产库确认 |
| 5 | 时空剧本 + 运镜 + 终审 | Step 6 后 | screenplay + cinematographer + script_auditor + compliance_gate | 时空化剧本 + 运镜 + 终审报告确认 |
| 6 | 视觉种子 + 风格化 + 声音骨架 | Step 7(含 7B)后 | visual_executor + prompt_injector + style_genome + colorist + audio_pipeline + compliance_gate(可选红线复查) | 视觉种子 + 风格化 + 声音骨架确认 |
| 7 | 一致性检查 | Step 9 后 | continuity_auditor | 4 维跨镜头一致性审计报告确认 |
| 8 | 最终成片 + BGM + 音效 + 口型 | Step 11 后 | audio_pipeline + 全专家终审 + compliance_gate(distribution compliance) | 最终成片 + 分发合规确认 |

**Hard vs Soft gates:**
- **Hard gates**(fail 阻止推进):compliance_gate(红线 / 备案 / AIGC 标识)+ script_auditor(predicted completion < 65%)+ continuity_auditor(4 维 fail)
- **Soft gates**(用户可越过):theory_critic(artistic critique,advisory only)

---

## Atomic Operations(V8.6 §1-§6 6 组合并)

V8.6 通过 6 组 atomic operation 把原 25 步精简为 13 步。每个 atomic operation 在**单次 ACP 调用**中完成多专家协同:

| V8.6 § | Atomic Step | 原 Step 合并 | 协同专家 | Atomic 的意义 |
|--------|------------|-------------|---------|--------------|
| §1 | Step 1 共鸣+主题 | Step 1 + Step 2 | hook_retention | 选题与主题一步到位,避免 hook 与主题脱节 |
| §2 | Step 2 框架+大纲 | Step 2.5 + Step 3 | creative_source + screenplay | 故事框架与大纲并行,避免 Snowflake 与 Snyder 不匹配 |
| §3 | Step 3 剧本+审计 | Step 5 + 5B + 6 | screenplay + script_auditor | 剧本与审计原子循环,审计驱动剧本选择 |
| §4 | Step 7 视觉+风格化 | Step 13A + 15 | visual_executor + prompt_injector + style_genome + colorist | 4 专家一次协同,避免 style 与 visual 脱节 |
| §5 | (Step 6 运镜+终审 已在 V8.4 §5 前置) | Step 11 + 12 | screenplay + cinematographer + script_auditor | 运镜 + 终审双门一次确认 |
| §6 | Step 11 声音+口型 | Step 17B + 18 | audio_pipeline(6 sub-steps) | audio master 6 sub-steps 一次原子操作,lip_sync 与 mix 完全对齐 |

---

## dreamina CLI as Canonical Image/Video Tool

per `_shared/dreamina-cli-baseline.md`(Phase 22 v5.0)+ kais-movie-agent V8.5 SKILL.md:

- **dreamina CLI 是所有图片/视频生成的唯一规范工具**(6 sub-commands: text2image / image2image / multimodal2video / multiframe2video / frames2video / image_upscale)
- **gold-team 职责收口**:仅服务 video/TTS/3D;图片生成不走 gold-team(`image_draw` 仅 DEGRADE 路径)
- **jimeng-client.js 废弃**(V8.5 标记 `@deprecated`,lib/ 保留仅兼容参考)
- **L1/L2/L3/L4 角色资产库**(V8.5 §"角色一致性策略"):角色参考(L1)只传脸,智能参考(L2/L3/L4)传衣服/姿势/表情,**不要混放**

详见 [`dreamina-cli-baseline.md`](./dreamina-cli-baseline.md)。

---

## Per-Expert V8.6 Section Cross-Reference

每个 movie-expert 的 SKILL.md 都有 `## V8.6 Pipeline Sync (Phase XX v5.0)` section,详细记录该专家在 V8.6 13 步管线中的位置:

| Expert | Phase | V8.6 Step(s) | Section Link |
|--------|-------|--------------|--------------|
| visual_executor | P23 | Step 4 / 5 / 7 | [`../visual_executor/SKILL.md §V8.6 Pipeline Sync`](../visual_executor/SKILL.md) |
| prompt_injector | P23 | Step 7 pre-node | [`../prompt_injector/SKILL.md §V8.6 Pipeline Sync`](../prompt_injector/SKILL.md) |
| character_designer | P23 | Step 4 | [`../character_designer/SKILL.md §V8.6 Pipeline Sync`](../character_designer/SKILL.md) |
| cinematographer | P23 | Step 5 / 6 / 8 | [`../cinematographer/SKILL.md §V8.6 Pipeline Sync`](../cinematographer/SKILL.md) |
| colorist | P23 | Step 7 | [`../colorist/SKILL.md §V8.6 Pipeline Sync`](../colorist/SKILL.md) |
| style_genome | P23 | Step 2.5 / 5 / 7 | [`../style_genome/SKILL.md §V8.6 Pipeline Sync`](../style_genome/SKILL.md) |
| hook_retention | P24 | Step 1 | [`../hook_retention/SKILL.md §V8.6 Pipeline Sync`](../hook_retention/SKILL.md) |
| creative_source | P24 | Step 2 | [`../creative_source/SKILL.md §V8.6 Pipeline Sync`](../creative_source/SKILL.md) |
| screenplay | P24 | Step 2 / 3 / 6 | [`../screenplay/SKILL.md §V8.6 Pipeline Sync`](../screenplay/SKILL.md) |
| script_auditor | P24 | Step 3 / 6 | [`../script_auditor/SKILL.md §V8.6 Pipeline Sync`](../script_auditor/SKILL.md) |
| audio_pipeline | P25 | Step 7B / 11 | [`../audio_pipeline/SKILL.md §V8.6 Pipeline Sync`](../audio_pipeline/SKILL.md) |
| continuity_auditor | P26 | Step 9 | [`../continuity_auditor/SKILL.md §V8.6 Pipeline Sync`](../continuity_auditor/SKILL.md) |
| compliance_gate | P26 | Step 1/3/6/11 后(4 gates) | [`../compliance_gate/SKILL.md §V8.6 Pipeline Sync`](../compliance_gate/SKILL.md) |
| editor | P26 | Step 8 | [`../editor/SKILL.md §V8.6 Pipeline Sync`](../editor/SKILL.md) |
| theory_critic | P26 | consultative(任意 Step) | [`../theory_critic/SKILL.md §V8.6 Pipeline Sync`](../theory_critic/SKILL.md) |

**未在 V8.6 主线映射但保留的 expert:**
- `production`(FUTURE-09 deferred,不在 V8.6 主线)
- `documentary_maker`(按需调用,纪录片向项目)
- `animation_studio`(按需调用,动画向项目)
- `quality_gate`(VALIDATE-D1 gap,canonical 16th DAG node 但无 SKILL.md 目录)

---

## Refresh Cadence

本 ref **每季度复核一次**(per `_shared/` convention)。Drift triggers:

1. **kais-movie-agent V-number 升级**(V8.6 → V8.7+)—— Step 编号 / atomic 合并可能调整
2. **审核门数量变化**(V8.6 8-gate → 后续可能再精简或扩展)
3. **dreamina CLI 子命令新增**(可能新增第 7+ sub-command,影响 Step 10 视频生成)
4. **新增 expert_id 接入 V8.6 主线**(如 production 从 FUTURE-09 deferred 转为 active)

复核动作:
- 重读 kais-movie-agent/SKILL.md 最新版本
- 对比 13-Step mapping table 是否变化
- 更新本 ref 的 `Last-verified:` 与 `verified_date:` 时间戳
- 触发对应 expert SKILL.md 的 V8.6 Pipeline Sync section 同步更新

---

## See Also

- [`dreamina-cli-baseline.md`](./dreamina-cli-baseline.md) — V8.5 dreamina CLI 6 sub-commands + L1-L4 + async poll + gold-team fallback + jimeng-client 废弃(Phase 22 v5.0)
- [`glossary.md`](./glossary.md) — V8.6 术语 EN↔CN 词典(Phase 27 v5.0 新增 Atomic Step / Review Gate / L1 Identity Anchor 等 H3 词条)
- [`RAG-INVOCATION-PATTERN.md`](./RAG-INVOCATION-PATTERN.md) — 专家如何调用共享 ref 的通用模式
- [`SKILL-LAYOUT.md`](./SKILL-LAYOUT.md) — `_shared/` ref 标准文件结构与头块规范

---

## Source Citation

- **Primary:** kais-movie-agent V8.6 SKILL.md @ commit `e41fa68` (2026-06-18 22:56:46 +0800) §"hermes-agent 专家 → 管线 Step 速查" + §"V8.6 更新" + §"强制审核门"
- **Secondary:** kais-movie-agent V8.5 SKILL.md @ commit `c22867d` (2026-06-18 22:17:46 +0800) §"V8.5 更新" + §"L1/L2 双参考角色一致性系统"
- **Tertiary:** kais-movie-agent V8.4 SKILL.md @ commit `4fb57b4` (2026-06-18 21:36:04 +0800) §"V8.4 更新"

---

*Owned by Phase 27 plan 27-01 (集成 close-out). Canonical V8.6 mapping reference for all 16 active movie-experts. No parallel plan touches this file. Cross-references Phase 22 dreamina-cli-baseline.md + Phase 23/24/25/26 expert SKILL.md V8.6 Pipeline Sync sections.*
