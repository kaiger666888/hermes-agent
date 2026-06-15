# Hurkman Color Correction Pipeline — Lift/Gamma/Gain Ranges + ACES Pipeline + LUT Formats + Shot-Matching

**Source:** *Color Correction Look Book: Creative Grading Techniques for Film and Video* (Alexis Van Hurkman, 2011, Peachpit Press, ISBN 978-0-321-71311-7) + ACES documentation (Academy Color Encoding System, public spec).
**Copyright:** © 2011 Alexis Van Hurkman / Peachpit Press. Fair Use — paraphrased lift/gamma/gain ranges + ACES transforms + LUT format comparison + 4-step shot-matching protocol only; ≤ 5 specific LUT values per chapter quoted; no reproduction of Hurkman's before/after frame walkthroughs (see [LICENSE.md](./LICENSE.md)).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 colorist 专家在 CxSxZ combination 选择后的 **technical-side 视角** —— 如何把选定的颜色物理地印到画面上。Hurkman 的 *Color Correction Look Book* 是数字电影调色工艺的现代经典:它把"创意调色"工程化为一套可执行、可量化的步骤 —— lift/gamma/gain 窗口、ACES pipeline transforms、LUT format 选择、shot-matching 协议。

本 ref 是 colorist SKILL.md `## Key Parameters > LUT Parameters` 与 `## Workflow` step 5 "Cross-Shot Verification" 的**技术侧权威源**(technical-side authoritative source);它与 [`bellantoni-color-psychology.md`](./bellantoni-color-psychology.md)(creative-side:选什么色)和 [`digital-color-science.md`](./digital-color-science.md)(instrumented-side:如何测量色是否对)互补,共同构成 colorist 决策的三层 grounding。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)([男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [钩子](../../_shared/glossary.md#钩子-hook) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [爆款](../../_shared/glossary.md#爆款-viral-formula-explosive-hit) / [完播率](../../_shared/glossary.md#完播率-completion-rate))。

---

## Lift/Gamma/Gain Ranges

Hurkman 的 lift/gamma/gain 模型是数字调色的基础(对应 Resolve / Baselight / Flame 等所有主流 grading 工具的 primary 工具栏)。三通道分别控制画面亮度区域的颜色偏移:

### Lift/Gamma/Gain 窗口表

| 通道 | 影响亮度区域 | Hurkman 推荐窗口(SDR,Rec.709) | HDR 扩展窗口(Rec.2020 / PQ 1000-nit) | tolerance |
|------|------------|--------------------------------|---------------------------------------|-----------|
| Lift | Shadows(Z < 0.2) | ±0.05(per channel) | ±0.04(per channel,HDR 不易察觉 lift 变化) | 5% |
| Gamma | Midtones(0.2 ≤ Z ≤ 0.7) | 0.8-1.2(整体),per-channel 偏移 ≤ ±0.05 | 0.85-1.15(HDR gamma 不易察觉) | 3% |
| Gain | Highlights(Z > 0.7) | 0.8-1.2(per channel) | 0.75-1.25(HDR highlights headroom 更多) | 5% |

### Lift/Gamma/Gain 使用规则

- **单通道偏移超过 ±0.05 → color cast 风险**;若必须超出,需在 SKILL.md `## Quality Thresholds` 显式声明 `operator_convention_override=true` 并解释。
- **三通道同时同向偏移 = brightness/contrast 调整(中性)**,不产生 color cast;这是合法的 contrast 调整,不是 creative 调色。
- **gamma 0.8-1.2 是 SDR 安全窗口**;HDR 时收紧到 0.85-1.15 因 HDR displays 对 midtone 变化更敏感(详见 [`digital-color-science.md`](./digital-color-science.md) §HDR PQ EOTF)。
- **短剧/竖屏 移动端部署需考虑平台二次编码压缩**(见 [`cn-audience-color.md`](./cn-audience-color.md) §Douyin Saturation Ceiling),LUT 应预先补偿 -0.05 lift(避免阴影被压成黑块);具体补偿量见 §Platform-Specific Compensations。

### Lift/Gamma/Gain 的物理意义与实操

Hurkman 详细解释了三通道的物理意义:

- **Lift 影响画面暗部**(Z < 0.2):lift +0.05 让阴影变浅,lift -0.05 让阴影更深。lift 的 per-channel 偏移(如 R +0.05 / G +0.00 / B +0.00)会让阴影偏红(color cast);中性 lift(三通道同向)只改 brightness 不改 hue。
- **Gamma 影响画面中间调**(0.2 ≤ Z ≤ 0.7):gamma < 1.0 让画面变暗且 contrast 增加;gamma > 1.0 让画面变亮且 contrast 降低。gamma 的 per-channel 偏移通常用于 white balance 修正(R 偏多 → gamma_B 略提升)。
- **Gain 影响画面亮部**(Z > 0.7):gain +0.10 让 highlights 更亮;gain 的 per-channel 偏移通常用于 highlight tint 修正(如日落场景 gain_R 略增加)。

实操示例:男频 revenge 短剧 爽点 climax,Sunset Glow signature:
- 起点:ACEScg working space,AI 生成 frame 已 IDT 转换
- step 1:lift +0.04 warm(per-channel: R +0.05 / G +0.04 / B +0.03)—— 让阴影带温暖感
- step 2:gamma 0.95(整体)—— 提升 midtone contrast
- step 3:gain +0.08 warm(per-channel: R +0.10 / G +0.08 / B +0.05)—— highlights 落日金色
- step 4:saturation +0.15(整体)
- step 5:验证 cross-shot ΔE ≤ 2.0;若失败,selective 调整

### Hurkman 推荐的 5 个 LUT signature shapes

下列 5 个 LUT signature 是从 Hurkman 全书数十个案例中蒸馏出的代表性 shape(每章 ≤ 5 个 LUT 值的 Fair Use 引用);完整 recipe 见原书。colorist 在 SKILL.md `## 28 Core Color Combinations` 表中选定的 combination,可通过这 5 个 signature 之一作为起点。

#### Signature 1: Bleach Bypass

- **LUT values**:lift +0.02 / gain +0.05 / saturation -0.20
- **视觉效果**:高对比 + 低饱和
- **适用场景**:action / thriller / 男频 复仇(冷硬、克制情绪)
- **CN 短剧 部署**:男频 都市修仙 / 重生复仇 爽点 climax 段可考虑,搭配 high contrast 的低 saturation 提供叙事克制感

#### Signature 2: Warm Vintage

- **LUT values**:lift +0.03 warm / gamma 0.95 / saturation +0.10
- **视觉效果**:怀旧橙 + 整体偏暖
- **适用场景**:romance / drama / 怀旧题材
- **CN 短剧 部署**:女频 豪门虐恋 / 闺蜜背叛 的回忆段(见 [`cn-audience-color.md`](./cn-audience-color.md) §"Lit from Within" Trend)

#### Signature 3: Cool Tech

- **LUT values**:lift +0.02 cool / gamma 1.05 / saturation -0.05
- **视觉效果**:蓝绿冷调 + 略 midtone 提升
- **适用场景**:sci-fi / corporate / 都市修仙的现代都市段
- **CN 短剧 部署**:都市修仙 主角在都市写字楼场景,可用 Cool Tech 表达"主角不属于此地的疏离感"

#### Signature 4: Sunset Glow

- **LUT values**:lift +0.04 warm / gain +0.08 warm / saturation +0.15
- **视觉效果**:落日金色 + 高 saturation warm
- **适用场景**:男频 爽点 climax / 黄昏场景
- **CN 短剧 部署**:**男频 爽点 climax 的默认 signature** —— 配合 [`cn-audience-color.md`](./cn-audience-color.md) §"Lit from Within" Trend 的男频 warm radiance 策略;注意 saturation +0.15 超过 Douyin 0.75 ceiling(需 trigger 平台预补偿)

#### Signature 5: Noir Contrast

- **LUT values**:lift -0.03 / gain +0.10 / saturation -0.30
- **视觉效果**:黑白对比 + 极低 saturation
- **适用场景**:noir / 复仇 蓝调 / 黑色电影
- **CN 短剧 部署**:男频 复仇 短剧 的冷开场段或反派回忆段;`noir_contrast` 提供压抑感,与 爽点 climax 的 `sunset_glow` 形成对比

### Platform-Specific Compensations

CN 短剧 在 抖音 / 快手 / 视频号 部署时,平台二次编码会主动降低 saturation(详见 [`cn-audience-color.md`](./cn-audience-color.md) §Douyin Saturation Ceiling)。Hurkman 的 5 个 signature 在 CN 部署时需预补偿:

| Signature | baseline saturation | Douyin 预补偿 | 快手 预补偿 | 视频号 预补偿 | 小程序剧 预补偿 |
|-----------|---------------------|--------------|------------|--------------|----------------|
| Bleach Bypass | -0.20 | +0(已 < 0.75 ceiling)| +0 | +0 | +0 |
| Warm Vintage | +0.10 | +0(假设 baseline S = 0.70)| +0 | +0 | +0 |
| Cool Tech | -0.05 | +0 | +0 | +0 | +0 |
| Sunset Glow | +0.15 | **-0.05 to -0.10** | **-0.05 to -0.10** | +0 | +0 |
| Noir Contrast | -0.30 | +0 | +0 | +0 | +0 |

colorist 在 `## Output Format` 的 `lut_reference` 字段输出时,应为每个平台输出独立的 LUT 文件:`lut_douyin.cube` / `lut_kuaishou.cube` / `lut_video_account.cube` / `lut_miniprogram.cube`。预补偿数值是 production 阶段的 baseline,不依赖具体 episode 内容。

---

## ACES Pipeline

ACES(Academy Color Encoding System)是电影艺术与科学学院推出的 working space + 转换协议。Hurkman 推荐 ACES 作为 multi-deliverable 工作流的 working space(单一 source → 多目标 output),因 ACES 宽色域可无损承载从 SDR Rec.709 到 HDR Rec.2020 / PQ 的所有目标。

### ACES pipeline 关键 transforms

| Transform | 工作空间 / 颜色空间 | EOTF(Electro-Optical Transfer Function) | Target peak luminance | 适用 deliverable |
|-----------|-------------------|----------------------------------------|-----------------------|-----------------|
| ACEScg(working) | Linear ACEScg | Linear(scene-referred) | n/a(working space) | 调色阶段使用 |
| IDT(Input Device Transform) | Camera RAW → ACES2065-1 | Camera-specific(Alexa LogC / Sony S-Log / RED Log3G10) | n/a | 拍摄素材 ingest |
| ODT Rec.709(Output) | ACES2065-1 → Rec.709 | Rec.709 gamma(≈ 2.4) | 100 cd/m²(nit) | SDR 视频 / 抖音/快手 默认 |
| ODT Rec.2020 SDR(Output) | ACES2065-1 → Rec.2020 | Rec.709 gamma | 100 cd/m² | 高质量 SDR / B站 高码率 |
| ODT Rec.2020 HLG(Output) | ACES2065-1 → Rec.2020 | HLG(Hybrid Log-Gamma,BT.2100) | 1000 cd/m²(peak) | 抖音 HDR / Apple devices |
| ODT Rec.2020 PQ(Output) | ACES2065-1 → Rec.2020 | SMPTE ST 2084 PQ | 10000 cd/m²(theoretical)/ 1000-4000 cd/m²(实际 master) | HDR 影院 / 高端 HDR 流媒体 |
| ODT P3 D65(Output) | ACES2065-1 → DCI-P3 D65 | Gamma 2.6 | 48 cd/m² | 影院 DCP / 苹果设备 |

### ACES pipeline 使用规则

- **AI 短剧/微电影的多 deliverable(抖音 SDR + Apple HDR + 影院 DCP)应统一在 ACEScg working space 调色**,通过不同 ODT 输出 —— 避免为每平台独立调色(减少成本与一致性 bug)。
- **若素材来自 AI 生成模型**(`<image_gen_primary>` / `<video_gen_primary>`),其"camera"是模型隐式的 EOTF —— 需用 image-stats 测量后选择最接近的 IDT(通常 Rec.709 camera IDT 适用于大多数 AI 生成图)。
- **ACES pipeline 是 [`SKILL.md`](../SKILL.md) §Color Transitions transition_duration ≥ 2.0s 的工程化基础** —— 在 ACES 中 transition 是 scene-referred linear 计算,不被 ODT 压缩;若在 SDR Rec.709 直接 transition,会因 gamma 压缩导致 transition 不平滑。

### ACES pipeline 在 AI 短剧 部署的具体应用

AI 生成 frame 的 IDT 选择是 AI 短剧 工作流的关键决策点:

| AI 生成模型 | 推荐 IDT | 理由 |
|------------|---------|------|
| FLUX 2 / Z-Image / Imagen 类(单图)| Rec.709 camera IDT | 这类模型训练数据以 Rec.709 sRGB 为主,输出色彩空间隐式为 Rec.709 |
| Veo 3 / Kling 3.4 / Sora(视频)| Rec.709 camera IDT(video)| 视频生成模型同样以 Rec.709 训练 |
| Stable Diffusion 类(基于 VAE)| Rec.709 camera IDT | 同上,但需注意 SD 模型常因 VAE 解码引入 magenta cast,需在 IDT 后额外 neutralize |

**推荐工作流:**
1. AI 模型生成 frame,默认 Rec.709 sRGB JPEG/PNG
2. IDT:Rec.709 → ACES2065-1(转换为 ACES working space)
3. Working:ACEScg(creative 调色,见 §Lift/Gamma/Gain Ranges + 5 signature shapes)
4. ODT:根据平台输出(抖音 → Rec.709;Apple HDR → Rec.2020 HLG;B站 → Rec.2020 SDR)
5. QC:ΔE ≤ 2.0 cross-shot 验证(见 [`digital-color-science.md`](./digital-color-science.md) §CIELAB ΔE Tolerance)

### ACES pipeline 的常见误区

**误区 1:认为 AI 生成图是 "linear",可直接用于 ACEScg。** 错。AI 模型(尤其 FLUX / SD 类)默认输出 sRGB gamma-encoded 图像,不是 linear。直接当 ACEScg 使用会导致 midtone 偏暗。正确做法:IDT = sRGB → ACES2065-1(显式转换)。

**误区 2:在 Rec.709 ODT 后再调色。** 错。ODT 是最终 output transform,不应在 ODT 后再调 lift/gamma/gain;否则下游平台若重新映射 color space 时,你的调色会被"double-applied"。正确做法:所有 creative 调色在 ACEScg working space,ODT 是确定性的 output 转换,不被 creative 修改。

**误区 3:忽略 IDT 对 AI 生成 frame 的统计偏差。** AI 模型即使在相同 prompt 下,输出 frame 的 color stats 仍有 ±5-15% 波动(white balance ±200K、saturation ±0.1)。这意味着即使 IDT 正确,cross-shot consistency 仍可能失败(ΔE > 2.0)。colorist 需在 step 4 (creative grade) 后额外 trigger cross-shot normalization。

**误区 4:HDR deliverable 时直接套用 SDR LUT。** 错。HDR 的 lift/gamma/gain 窗口比 SDR 紧(详见 §Lift/Gamma/Gain Ranges),HDR 与 SDR 的 perceptual effects 不同;直接套用 SDR LUT 到 HDR master 会导致 over-saturation 或 highlight clipping。正确做法:为 HDR 独立调色(或用 tone-mapping 算法转换)。

---

## LUT Formats Compared

LUT(Look-Up Table)是调色结果的载体,可分发 / 加载到下游工具(drawer / animator / playback)。Hurkman 系统比较了 3 种主流 LUT 格式:

### LUT 格式对比表

| 格式 | 起源 | Bit depth | Grid size | 插值方法 | 文件大小 | 适用场景 |
|------|------|-----------|-----------|---------|---------|----------|
| `.cube`(Iridas / Resolve) | Iridas(2007),被 Resolve 继承 | 32-bit float(典型)/ 16-bit | 17³ / 33³ / 65³(默认 33³) | Trilinear(默认)/ Tetrahedral(Resolve 16+) | ~ 1-30 MB(随 grid size) | Resolve / Premiere / FCPX / 大多数 NLE |
| `.3dl`(Lustre / Autodesk) | Autodesk Lustre | 12-bit / 16-bit integer | 17³ / 33³ | Trilinear | ~ 1-10 MB | Lustre / Flame / 工业级 DI |
| `.ccc`(ASC-CDL)| ASC(American Society of Cinematographers) | 10-bit(典型)| n/a(仅 slope/offset/power,9 个值) | n/a(数学函数,不需 LUT) | < 1 KB | on-set look dev / 跨工具基础调色 |

### LUT Format 选择规则

- **AI 短剧工作流推荐 `.cube`(33³,32-bit float,tetrahedral 插值)** —— Resolve / Premiere / FCPX / drawer / playback 全链路支持,tetrahedral 插值精度高,trilinear 在高 contrast 边界会出现 color banding。
- `.3dl` 仅用于工业级 DI(Lustre / Flame);AI 工作流不需要。
- `.ccc` 是 metadata 不是完整 LUT,适用于 on-set 拍摄(或 AI 模型 prompt)记录基础 look,不能承载完整 creative grade —— colorist 在 SKILL.md `## Output Format` 的 `lut_reference` 字段必须输出 `.cube` 格式 LUT。
- **grid size 经验法则:33³ 是 quality/file-size 平衡点**;17³ 在高 contrast 区域精度不足(可能 banding);65³ 精度过剩(文件 ~30 MB,移动端加载延迟)。

### LUT 插值方法的视觉差异

Hurkman 详细比较了 trilinear vs tetrahedral 插值:

- **Trilinear**:简单 + 快,但在高 contrast 边界(如 hair 边缘 / shadow 边缘)可能出现 color banding(色阶断层)
- **Tetrahedral**:Resolve 16+ 引入,精度高 4 倍,避免 banding;但文件大小 + ~ 30%,加载延迟略增加

**推荐:短剧 部署用 tetrahedral**(因移动端 playback bandwidth 已非瓶颈,精度优先);AI 生成 frame 已有 generation artifacts,LUT 精度低会放大瑕疵。

### LUT 文件命名约定

colorist 在 `## Output Format` 的 `lut_reference` 字段输出 LUT 时,需遵守以下命名约定,便于下游工具(drawer / animator / playback)自动 dispatch:

- **`lut_baseline_<combination_id>.cube`** —— baseline LUT,如 `lut_baseline_C21.cube`(C21 Action climax)
- **`lut_douyin_<combination_id>.cube`** —— 抖音 预补偿版
- **`lut_kuaishou_<combination_id>.cube`** —— 快手 预补偿版
- **`lut_video_account_<combination_id>.cube`** —— 视频号 预补偿版
- **`lut_miniprogram_<combination_id>.cube`** —— 小程序剧 版(无预补偿)
- **`lut_hdr_<combination_id>.cube`** —— HDR master(Rec.2020 PQ)
- **`lut_sdr_<combination_id>.cube`** —— SDR master(Rec.709)

每个 episode 输出 1 个 baseline + N 个平台变体(N = 部署平台数);典型 短剧 部署 4-5 个平台变体。

---

## Shot-Matching Protocol

Hurkman 4-step shot-matching 协议是 cross-shot color consistency 的工程化方法。在 colorist `## Workflow` step 5 "Cross-Shot Verification" 中执行。

### 4-Step Shot-Matching 表

| Step | 检查项 | 工具 | 容差 | 失败处理 |
|------|-------|------|------|---------|
| 1. Exposure match | 调整 lift/gamma/gain 使两 shot 的 waveform monitor 一致 | Resolve Waveform / Parade | Y midpoint 差 ≤ 5 IRE(SDR) / ≤ 50 nits(HDR) | 调 lift/gain;失败则 mark 为 re-shoot 候选(或 AI re-gen) |
| 2. White balance match | 调整 RGB gain 使两 shot 的灰点(neutral patch)位于 RGB 重合 | Vectorscope / RGB Parade | color temperature 差 ≤ ±150K(production,per [`cn-audience-color.md`](./cn-audience-color.md) §CN Warmth Preference)| 调 RGB gain;若 scene 内 color temp shift > 200K 需 narrative motivation |
| 3. Contrast match | 调整 gamma 使两 shot 的 contrast ratio(white-black)一致 | Waveform Monitor | contrast ratio 差 ≤ 10% | 调 gamma;失败则 selective curve(曲线)调整 |
| 4. Creative grade match | 应用 creative LUT 后,验证两 shot 的 color intent 一致 | 视觉 + ΔE 测量(见 [`digital-color-science.md`](./digital-color-science.md) §CIELAB ΔE Tolerance)| adjacent shots ΔE ≤ 2.0;whole-scene ΔE ≤ 3.0 | 若 ΔE > 2.0, selective HSL qualifier 调整;若失败, trigger continuity report(见 [`SKILL.md`](../SKILL.md) Collaboration `-> continuity`) |

### Shot-Matching 使用规则

- **4 步必须按顺序执行**(Exposure → White balance → Contrast → Creative);跳步会导致后续调色掩盖原始问题。
- **若 AI 生成 frame 的 exposure / white balance 极不稳定**(常见于 FLUX / Imagen 类模型),step 1+2 失败率 > 30% 时,需 trigger drawer re-gen 而非试图 LUT 修复。
- **creative step 4 的 ΔE ≤ 2.0 阈值是 [`SKILL.md`](../SKILL.md) §Quality Thresholds `color_cross_shot_consistency` 的实际测量方法**(原 SKILL.md 该 metric 是 ≥ 0.80 的抽象值,refactor 后改为 ΔE ≤ 2.0 的物理值,见 [`digital-color-science.md`](./digital-color-science.md) §CIELAB ΔE Tolerance)。
- **男频 短剧 因 cut density 高**(40-60 cuts/90s-ep,见 [`../editor/references/cn-cutting-rhythm.md`](../editor/references/cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre),shot-matching 失败率容忍度低 —— 每 shot 平均 screen time ~1.5-2s,ΔE > 2.0 会被观众察觉为"色彩跳"。

### Shot-Matching 在 AI 短剧 工作流的特殊考量

AI 生成 frame 的 shot-matching 比 photographed frame 更复杂:

- **AI frame 间一致性差**:FLUX / Veo / Kling 等模型在不同 generation call 之间,即使相同 prompt,输出 frame 的 color stats 仍有 ±5-15% 波动(white balance ±200K、saturation ±0.1)。这超出 Hurkman step 1-2 的容差。
- **推荐 workflow**:在 drawer 阶段(生成 frame 时)使用 `color_reference_image` field,强制 frame generation 参考 anchor frame 的色彩;这比 colorist 阶段 LUT 修复更经济。
- **若 drawer 阶段 color reference 不可用**:colorist 必须在 step 1 (Exposure match) 前增加一个 "AI frame normalization" 预处理步骤,使用 AI frame → photographed-style 转换(如 NIQE / BRISQUE-based correction)。

### Shot-Matching 失败的 trigger 报告

colorist 在 shot-matching 失败时,输出 `shot_match_failure_report`:

```json
{
  "failed_shots": [
    {
      "shot_id": "shot_012",
      "ref_shot_id": "shot_011",
      "delta_e": 3.4,
      "failure_step": "step_4_creative_grade_match",
      "cause": "AI generation color drift",
      "remediation_options": ["drawer_regen_with_reference", "lut_correction", "continuity_override"]
    }
  ],
  "scene_worst_delta_e": 3.4,
  "scene_avg_delta_e": 1.6,
  "scene_pass": false
}
```

continuity expert 消费此报告,根据 scene 重要性决定 remediation 策略(关键场景 trigger drawer re-gen;过场镜头 accept continuity-override)。

### Shot-Matching 失败的分级处理

Hurkman 推荐的失败分级:

| ΔE 范围 | 失败等级 | 推荐处理 | 短剧 部署考量 |
|---------|---------|---------|--------------|
| 2.0 < ΔE ≤ 3.0 | 轻度失败(acceptable mismatch)| selective HSL qualifier 调整;无需 re-gen | 过场镜头可接受;关键场景(对话)需 fix |
| 3.0 < ΔE ≤ 6.0 | 中度失败(visible mismatch)| creative LUT 局部调整 + 剪辑掩盖(如 cut on action)| 关键场景 trigger drawer re-gen |
| ΔE > 6.0 | 重度失败(unacceptable)| 必须 trigger drawer re-gen 或 re-grade | 任何场景不可接受 |

男频 短剧 因 cut density 高(40-60 cuts/90s-ep),每 shot 平均 screen time ~1.5-2s;轻度失败(2.0 < ΔE ≤ 3.0)在快切中不易察觉,可降低 remediation 优先级。女频 短剧 因 cut density 低(30-45 cuts/90s-ep)且观众审美更敏感,轻度失败也需 fix。

### Shot-Matching 的经济性权衡

Hurkman 强调 shot-matching 不是"无止境追求 ΔE = 0",而是"达到 production minimum 后即停止"。具体经济性:

- **每 shot 调色时间**:baseline 1-2 分钟;中度失败需 5-10 分钟;重度失败需 30+ 分钟(trigger re-gen)
- **每集 90s 短剧 总调色预算**:男频 40-60 shots × 1-2 min = 40-120 min/episode
- **AI 生成 frame 的 re-gen 成本**:每 frame re-gen ~ $0.05-0.50 USD(取决于模型);每集 re-gen 5-10 frames = $0.25-5 USD/episode
- **推荐 trigger 阈值**:ΔE > 3.0 即 trigger drawer re-gen,因 re-gen 成本($0.25-5)< 手动 fix 成本(30+ min × 时薪)

colorist 在 SKILL.md §Workflow step 5 输出 `shot_match_failure_report` 后,需附上 `cost_benefit_analysis` 字段帮助 continuity / drawer 决策。

---

## Cross-References

- [`bellantoni-color-psychology.md`](./bellantoni-color-psychology.md) — Bellantoni 定义"选什么色"(creative),Hurkman 定义"如何调"(technical);两 ref 共同构成 colorist 决策的两端。
- [`digital-color-science.md`](./digital-color-science.md) — Hurkman 的 shot-matching ΔE ≤ 2.0 与 color temp ±150K 由本 ref 给出 grounding;Hurkman 是 workflow 层,digital-color-science.md 是 instrumented 测量层。
- [`cn-audience-color.md`](./cn-audience-color.md) — Hurkman 的 saturation ceiling 由 cn-audience-color.md §Douyin Saturation Ceiling 给出 CN 平台特定值;本 ref §Platform-Specific Compensations 的具体数值由 cn-audience-color.md 提供。
- [`color-cross-cultural.md`](./color-cross-cultural.md) — Hurkman 的 white balance ±150K 在跨文化部署时需考虑 cross-cultural 颜色接受度差异。
- [`../editor/references/cn-cutting-rhythm.md`](../editor/references/cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre — shot-matching 容忍度受 cut density 影响(高 cut density = 低容忍度);男频 40-60 cuts/90s-ep 与 女频 30-45 cuts/90s-ep 的 shot-matching 失败率 baseline 不同。
- [`../../_shared/glossary.md`](../../_shared/glossary.md) — [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) / [钩子](../../_shared/glossary.md#钩子-hook) / [卡点](../../_shared/glossary.md#卡点-paywall-cliffhanger-paywall-moment) / [爆款](../../_shared/glossary.md#爆款-viral-formula-explosive-hit) / [完播率](../../_shared/glossary.md#完播率-completion-rate) 术语首次出现处超链接。

---

## Refresh Cadence

- **每 12 个月刷新一次**:ACES spec 版本演进(当前 ACES 1.3 / 2.0 在 2024-2026 演进中)、LUT 格式标准(尤其是 HDR 相关 .cube 扩展)。
- **每季度**:检查 Resolve / Premiere / FCPX 工具链版本对 LUT 格式的支持变化(tetrahedral 插值是否已普及到所有 NLE)。
- **触发即修**:见下节 drift signals。

## Drift Signals

- **新 LUT 格式标准出现**:若 ACES Central 或 SMPTE 推出新 HDR LUT 标准(如 ACES 2.0 引入新的 working space),需更新 LUT Formats Compared 表。
- **AI 生成模型的 IDT 变化**:若 `<image_gen_primary>` / `<video_gen_primary>` 模型更新其默认 EOTF(如从 Rec.709 转向 ACEScg-native),需更新 ACES pipeline §IDT 推荐。
- **平台 HDR 标准分裂**:若 抖音 / 快手 / 视频号 推出不同 HDR 标准(如 抖音 采用 HLG,快手 采用 PQ),需扩展 ODT 表。
- **shot-matching 容忍度新数据**:若 CN 短剧 爆款 语料分析发现观众对 ΔE > 2.0 的容忍度高于 Hurkman 的北美经验,需修订 step 4 阈值。

任何 drift signal 触发,需在本 ref 顶部 `**Last-verified:**` 字段更新日期,并在修订章节标注 "revised YYYY-MM due to [drift signal]"。
