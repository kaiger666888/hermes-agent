# Platform Comparison Matrix (2026-Q2)

**Source:** Cross-platform synthesis — derived from the 3 platform-spec reference files (抖音 / 快手 / 微信小程序剧)
**Copyright:** Public Platform Documentation — Fair Use (synthesis)
**Last-verified:** 2026-06-15
verified_date: 2026-06

> 本矩阵是 compliance_marketing 专家与下游消费者(Phase 2 HOOK 专家)的「速查表」,提供三大短剧分发平台的 at-a-glance 差异。每个单元格的具体阈值与公式请参阅对应的 platform-spec ref —— 本矩阵不重复深度内容,只做结构化对比。

## Summary

三大平台(抖音 / 快手 / 微信小程序剧)在分发机制、内容红线、付费模式、备案要求上有显著差异。抖音以算法漏斗为主,完播率权重最高,男频 / 女频 二元明显;快手以老铁文化 + 私域流量为主,草根共鸣 + 家庭伦理主导,男频 / 女频 二元弱化;小程序剧以微信生态裂变 + 长剧集模式为主,需双重备案,情感共鸣超越男频 / 女频 二元。本矩阵是 Phase 2 HOOK 专家消费 付费门槛 + 爆款公式 的稳定契约。

## Matrix

| 平台 | 付费门槛 | 红线差异 | 备案触发 | 推荐时长 |
|------|----------|----------|----------|----------|
| **抖音** | 前 3-5 集免费;单集 ¥1-3;整季 ¥19-99;平台抽成 30%<br>→ see [platform-specs-douyin.md](../compliance_marketing/references/platform-specs-douyin.md) | 平台专属:引流外部 / 医疗虚假 / 金融诱导 / 标题党;男频擦边镜头高风险<br>→ see [platform-specs-douyin.md](../compliance_marketing/references/platform-specs-douyin.md) | 任一集 ≥ 1 分钟 + 商业分发 → 网络微短剧 / 网络剧 备案;AIGC 任一帧 → AI 漫剧 备案<br>→ see [platform-specs-douyin.md](../compliance_marketing/references/platform-specs-douyin.md) | 单集 1-3 分钟(竖屏);完播率门槛 30-40%<br>→ see [platform-specs-douyin.md](../compliance_marketing/references/platform-specs-douyin.md) |
| **快手** | 前 3-5 集免费;单集 ¥1-3(略低 ¥0.2-0.5);整季 ¥15-79;平台抽成 25-30% + 创作者激励<br>→ see [platform-specs-kuaishou.md](../compliance_marketing/references/platform-specs-kuaishou.md) | 平台专属:直播带货虚假宣传 / 老铁 PK 不当 / 土味擦边 / 草根炫富;审核略宽于抖音<br>→ see [platform-specs-kuaishou.md](../compliance_marketing/references/platform-specs-kuaishou.md) | 同抖音(广电总局统一规则);备案号展示字段位置略异<br>→ see [platform-specs-kuaishou.md](../compliance_marketing/references/platform-specs-kuaishou.md) | 单集 1-3 分钟(竖屏),长内容 3-5 分钟;完播率门槛 25-35%<br>→ see [platform-specs-kuaishou.md](../compliance_marketing/references/platform-specs-kuaishou.md) |
| **微信小程序剧** | 前 5-10 集免费(长剧集);单集 ¥3-10(高于抖音/快手);整季 ¥39-199;无平台分账(仅 0.6% 微信支付通道费)<br>→ see [platform-specs-miniprogram.md](../compliance_marketing/references/platform-specs-miniprogram.md) | 平台专属:诱导分享 / 多级分销 / 涉政更严 / 色情低俗判定最严(接吻 > 3 秒即风险)<br>→ see [platform-specs-miniprogram.md](../compliance_marketing/references/platform-specs-miniprogram.md) | **双重备案**:广电总局(短剧)+ 微信 ICP(小程序)+ 增值电信业务许可证(付费分发)<br>→ see [platform-specs-miniprogram.md](../compliance_marketing/references/platform-specs-miniprogram.md) | 单集 1-3 分钟(短集)或 5-10 分钟(长集);典型 10-30 集(长篇 50-80 集);完播率门槛 35-50%<br>→ see [platform-specs-miniprogram.md](../compliance_marketing/references/platform-specs-miniprogram.md) |

## Platform Selection Decision Tree

根据内容类型选择主投放平台(主)与次投放平台(次):

1. **男频 短剧(战神 / 赘婿 / 修仙)** —— 主:**抖音**;次:快手(增加草根背景元素)。小程序剧仅适合长篇改编(10+ 集)。
2. **女频 短剧(豪门 / 闺蜜 / 替身)** —— 主:**抖音**;次:小程序剧(扩展为长篇情感线);快手需增加家庭线。
3. **草根共鸣 短剧(农村 / 打工人 / 老铁)** —— 主:**快手**;次:抖音(调整节奏更密)。小程序剧转化率低。
4. **家庭伦理 短剧(婆媳 / 父子 / 兄弟)** —— 主:**快手**;次:小程序剧(扩展为长篇);抖音需缩短为短集。
5. **长剧集(10+ 集,多线叙事)** —— 主:**小程序剧**;次:无(抖音 / 快手不支持长剧集变现)。视频号 可作引流入口。
6. **互动剧 / 多结局剧** —— 主:**小程序剧**(微信生态支持交互);次:无(抖音 / 快手无原生互动机制)。
7. **AIGC 漫剧(全 AI 生成)** —— 三平台均可,但需完成 AI 漫剧 备案(2026-04-01 新规);推荐主:**抖音**(算法对 AIGC 内容权重未显著降权);次:小程序剧(需在「关于」页补充 AI 说明)。

## Stable Contract for Phase 2 HOOK

本矩阵的 `付费门槛` + `爆款公式`(platform-specs-*.md 中)列是 Phase 2 HOOK 专家(hook_retention)的稳定消费契约。HOOK 将基于这两列数据:

- **付费门槛 → 卡点 设计**:HOOK 根据 付费门槛 集数阈值(抖音 ep.3-5 / 快手 ep.3-5 / 小程序剧 ep.5-10)与单集价格区间(¥1-10),设计符合平台变现节奏的 卡点。
- **爆款公式 → 钩子元素选择**:HOOK 根据 爆款公式 中的题材(男频 战神 / 女频 豪门 / 草根逆袭 / 长篇情感)与 完播率 目标,选择对应的钩子类型(冲突钩 / 情感钩 / 反差钩)。

**契约稳定性承诺(COMPLI → HOOK)**:

- 矩阵 4 列(付费门槛 / 红线差异 / 备案触发 / 推荐时长)结构在 v1 内冻结;新增列(例如「AIGC 标识要求」「算法陷阱」)采用 **additive-only** 政策,不重命名 / 不删除现有列。
- 列重命名 / 列删除需在 Phase 2 与 HOOK 团队同步后方可进行(威胁模型 T-01-09 缓解)。
- 数值更新(例如 抖音 分账比例从 30% 调整为 35%)在季度 Refresh Cadence 中统一更新,会同步通知 HOOK。

## Refresh Cadence

每 90 天(季度)re-verification,与 3 个 platform-spec refs 同步更新。Owner: compliance_marketing 专家。Next check: 2026-09-15。

具体校验动作:
1. 重新访问 3 个平台官方文档,更新 platform-specs-{douyin,kuaishou,miniprogram}.md。
2. 基于更新后的 spec,刷新本矩阵的 4 列内容。
3. 若数值变化超过 ±20%(例如分账比例从 30% 调整为 40%),在 HOOK 团队的同步通道中通知。
4. 更新本文件头部 Last-verified 与 verified_date,并 bump 矩阵版本(在 H1 标题后添加版本号,例如 `(2026-Q3 Verified)`)。

## Drift Signals

出现以下任一信号时,触发 off-cycle re-verification(不等季度窗口):

- 任一平台发布新的短剧运营公告或政策更新。
- 广电总局 / 网信办 发布新的 备案 / AIGC 相关通知(三平台同步影响)。
- 任一平台 付费机制 大改(例如抖音新增订阅模式、快手分账比例调整、微信支付通道费率调整)。
- 任一平台 爆款公式 趋势显著转变(观察 5+ 顶流账号集体转向新题材)。
- 新平台入局(例如 B 站竖屏短剧、小红书短剧),需新增矩阵行。
- 矩阵列结构调整需求(需在 Phase 2 HOOK 团队同步后进行)。
- Stable Contract for Phase 2 HOOK 节的契约边界受到挑战(例如 HOOK 反馈 4 列不足以覆盖其需求)。

## Cross-References

- [platform-specs-douyin.md](../compliance_marketing/references/platform-specs-douyin.md) —— 抖音 深度规则
- [platform-specs-kuaishou.md](../compliance_marketing/references/platform-specs-kuaishou.md) —— 快手 深度规则
- [platform-specs-miniprogram.md](../compliance_marketing/references/platform-specs-miniprogram.md) —— 微信小程序剧 深度规则
- [cn-content-rules.md](../compliance_marketing/references/cn-content-rules.md) —— 8 类通用红线(Plan 01-01 交付)
- [viral-element-catalog.md](../compliance_marketing/references/viral-element-catalog.md) —— 爆款元素目录(Plan 01-01 交付)
- [glossary.md](./glossary.md) —— 术语对照表
