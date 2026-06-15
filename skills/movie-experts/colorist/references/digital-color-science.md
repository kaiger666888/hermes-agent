# Digital Color Science: ΔE, Rec.709/2020, CCT, HDR PQ

**Source:** ITU-R BT.709-6 (2015) / BT.2020-2 (2015) / BT.2100-2 (2018) standards + SMPTE ST 2084:2014 (PQ EOTF) + CIE 15:2004(Colorimetry, 3rd edition)+ BT.2408-4 (2021, HDR operational practices)。
**Copyright:** Public standards — ITU-R / SMPTE / CIE standards documents are public international standards, freely re-distributable with attribution. Quoted values are factual technical specifications, not copyrighted creative content.
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

数字色彩科学是 colorist 防止"凭感觉调色"的工程化基础。本 ref 蒸馏 4 个核心数字色彩概念:CIELAB ΔE(Delta E)容差(感知-物理色彩差异度量)、Rec.709 vs Rec.2020 gamut(SDR/HDR 色域覆盖)、Color temperature 与相关色温(CCT)计算、HDR PQ EOTF(SMPTE ST 2084)。这些是 [`SKILL.md`](../SKILL.md) `## Quality Thresholds` 中 `color_cross_shot_consistency` metric 的物理化测量方法 —— 从抽象的"≥ 0.80"改为具体的"ΔE ≤ 2.0"。本 ref 与 [`hurkman-color-pipeline.md`](./hurkman-color-pipeline.md) 紧密耦合 —— Hurkman 提供"如何调",本 ref 提供"如何测量调得对不对"。

## CIELAB ΔE Tolerance

CIE 1976 LAB 是 perceptually-uniform 颜色空间(尽管不完美,但仍是工业标准),ΔE(Delta E)是其颜色差异度量。ΔE 公式(CIE 1976,简化版):

```
ΔE*ab = sqrt( (L*_1 - L*_2)^2 + (a*_1 - a*_2)^2 + (b*_1 - b*_2)^2 )
```

更精确的 ΔE2000 公式(CIE 2000,引入 perceptual weighting):

```
ΔE_00 = sqrt( (ΔL' / (kL*SL))^2 + (ΔC' / (kC*SC))^2 + (ΔH' / (kH*SH))^2 + RT * (ΔC' / (kC*SC)) * (ΔH' / (kH*SH)) )
```

(其中 SL / SC / SH / RT 是 weighting functions;kL = kC = kH = 1 为 reference conditions;完整公式见 CIE 158:2004 technical report。)

**ΔE 容差分级(工业标准):**

| ΔE 范围(CIE 1976) | 人类感知 | colorist 应用 | 短剧/微电影 部署场景 |
|------------------|---------|--------------|--------------------|
| **ΔE ≤ 1.0** | 几乎不可察觉(imperceptible) | 同 shot 内 master-grade 一致性 | 同 shot 内 AI frame 间一致性(`<video_gen_primary>` / `<image_gen_primary>` 输出) |
| **1.0 < ΔE ≤ 2.0** | 可察觉但可接受(acceptable match) | **adjacent shots cross-shot consistency** | 邻接 shots 一致性(production minimum,见 [`SKILL.md`](../SKILL.md) §Quality Thresholds)|
| **2.0 < ΔE ≤ 3.0** | 明显可见差异(visible mismatch) | whole-scene 容忍上限 | 同场景内 shots 间一致性(whole-scene ceiling)|
| **3.0 < ΔE ≤ 6.0** | 显著不同 | 不可接受(除非 narrative motivation) | scene-to-scene color shift(若 value-shift 驱动)|
| **ΔE > 6.0** | 完全不同颜色 | 完全 unacceptable | trigger continuity report 与 re-grade |

**ΔE Tolerance 使用规则:**
- **adjacent shots ΔE ≤ 2.0** —— 这是 SKILL.md `color_cross_shot_consistency` metric 的物理化定义(替代原抽象的 ≥ 0.80);CIE 1976 ΔE = 2.0 是 cross-shot consistency 的 production minimum
- **whole-scene ΔE ≤ 3.0** —— 整个场景内所有 shots 的 pairwise ΔE 不应超过 3.0(允许更松的容差,因 scene 内可能有 narrative-driven color shift)
- **CIE 2000 ΔE 公式优先** —— 若工具(Resolve / Baselight)支持 ΔE2000,使用它;否则降级到 CIE 1976(注意 1976 比 2000 偏保守,ΔE1976 = 2.0 ≈ ΔE2000 = 1.4)
- AI 生成 frame 的 ΔE 测量需用 patch-based(reference neutral patch + reference color patches),不能直接对整 frame 测平均(避免构图差异干扰)
- 短剧 男频 revenge 高 cut density(40-60 cuts/90s-ep,见 [`../editor/references/cn-cutting-rhythm.md`](../editor/references/cn-cutting-rhythm.md) §Cut-Density Windows by Platform/Genre),每 shot screen time ~ 1.5-2s,ΔE > 2.0 会被观众察觉;容忍度低于 horizontal 长片

**ΔE measurement 实施建议:**
- Resolve / Baselight 内置 ΔE scope(vectorscope with ΔE reference);若用 LLM-as-judge,需用 CLIP-color embedding cosine distance ≈ proxy(相关但不等于 ΔE)
- 工具链:Resolve Color Page → right-click → "Match Frame" → 显示与 reference 的 ΔE;或用 OpenColorIO + Python 脚本批量测量
- 输出 JSON 格式:`{shot_id, ref_shot_id, delta_e_lab76, delta_e_lab00, status}` —— status = "pass" / "fail" / "operator_override"

## Rec.709 vs Rec.2020 Gamut

Rec.709(SDR)与 Rec.2020(HDR)是数字视频的两大色域标准,定义了 R/G/B primaries 的 CIE 1931 xy 坐标。

| 标准 | Red primary (x, y) | Green primary (x, y) | Blue primary (x, y) | White point(D65)| CIE 1931 覆盖率 | CIE 1976 u'v' 覆盖率 |
|------|-------------------|---------------------|---------------------|----------------|----------------|----------------------|
| **Rec.709**(SDR,1990)| (0.640, 0.330) | (0.300, 0.600) | (0.150, 0.060) | (0.3127, 0.3290)| ~ 35.9% | ~ 38.0% |
| **Rec.2020**(HDR,2012)| (0.708, 0.292) | (0.170, 0.797) | (0.131, 0.046) | (0.3127, 0.3290)| ~ 75.8% | ~ 75.0% |
| **DCI-P3**(影院,2007)| (0.680, 0.320) | (0.265, 0.690) | (0.150, 0.060) | (0.314, 0.351)(DCI)/ (0.3127, 0.3290)(D65)| ~ 45.5% | ~ 49.0% |
| **ACES AP0**(working)| (0.7347, 0.2653) | (0.1424, 0.8576) | (0.0991, -0.0308)| (0.32168, 0.33767)| ~ 100%(过度宽)| ~ 100% |

**Rec.709 vs Rec.2020 关键观察:**
- **Rec.709 覆盖 CIE 1931 的 ~ 36%** —— 老旧 SDR 标准,无法表达高 saturation 的 cyan / magenta / 深绿
- **Rec.2020 覆盖 CIE 1931 的 ~ 76%** —— 比 Rec.709 大 2.1 倍,可表达更广 saturation;但实际显示设备覆盖率有限(典型 OLED ~ 70% Rec.2020,LED LCD ~ 50-60%)
- **Rec.709 是 抖音 / 快手 / 视频号 / 小程序剧 的默认目标** —— 移动端播放器 + 主流 mobile display 仍以 Rec.709 为基础(2026 年现状)
- **Rec.2020 仅用于 HDR deliverable** —— 抖音 HDR(iOS 端)/ Apple devices HDR-default / 高端影院;但短剧/微电影主流仍是 SDR Rec.709

**Rec.709/2020 使用规则:**
- SKILL.md `## Key Parameters > Color Intent Encoding` 的 `color_space` 字段:`CIELAB`(computation)/ `HSL`(creative output)/ `Rec.709 RGB`(SDR deliverable)/ `Rec.2020 RGB`(HDR deliverable)
- AI 短剧/微电影默认 deliverable 是 SDR Rec.709;若 multi-platform 含 HDR(抖音 HDR / Apple HDR),输出 Rec.2020 HDR master(经 ACES ODT,见 [`hurkman-color-pipeline.md`](./hurkman-color-pipeline.md) §ACES Pipeline)
- colorist 在选 CxSxZ combination 时,S(饱和度)值的物理范围取决于目标 gamut:Rec.709 的 S = 1.0 对应 Rec.709 gamut 边界;Rec.2020 的 S = 1.0 对应 Rec.2020 gamut 边界(更大);不能跨 gamut 直接对比 S 值
- CIELAB computation 空间是 gamut-independent(可表达任何可见色);creative LUT 必须声明目标 gamut,避免 out-of-gamut artifacts

**Rec.709/2020 gamut 测量工具:**
- Resolve Color Page → Color Space Transform → 显示 out-of-gamut warning
- OpenColorIO + Python:`image_rgb -> gamut_compression` 工具链
- 短剧 部署前必须验证 production CxSxZ 在目标 gamut 内;若 out-of-gamut,需 trigger LUT clamp 或 re-grade

## Color Temperature & CCT

Color temperature(色温)是黑体辐射体(blackbody radiator)的色,以 Kelvin(K)为单位。相关色温(Correlated Color Temperature, CCT)用于描述非黑体光源(如 LED / 荧光灯)的色温等效值。

**标准 color temperature:**

| Color temperature | 光源类型 | 视觉效果 | 短剧 部署场景 |
|------------------|---------|---------|--------------|
| 2700-3200K | Tungsten(钨丝灯 / 实用光)| warm yellow-orange | 情感亲密场景"lit from within"(见 [`cn-audience-color.md`](./cn-audience-color.md) §"Lit from Within" Trend)|
| 3200K | Tungsten cinema standard | warm | 男频 爽点 climax 主角 warm radiance |
| 4500-5500K | Cool daylight | neutral-cool | 女频 豪门虐恋 baseline |
| 5500K | Daylight(D55)| neutral | 标准中性 baseline |
| 6500K | D65(standard daylight)| neutral-cool | **Reference white**(Rec.709 / Rec.2020 / sRGB 都以 D65 为 reference white)|
| 7000-8500K | Cool overcast | cool blue | 悬疑 / 恐惧场景 |
| 9300K | Asian CRT legacy white point | very cool blue | 历史遗留 —— 旧 CRT 显示器参考点;现代设备不使用 |

**McCamy formula(CCT from xy chromaticity):**

```
CCT ≈ 449 * n^3 + 3525 * n^2 + 6823.3 * n + 5520.33
其中 n = (x - 0.3320) / (0.1858 - y)
x, y 为 CIE 1931 chromaticity coordinates
```

McCamy formula 适用于 3000-9000K 范围(误差 ± 50K);超出范围需用更精确的算法(如 Robertson 1968)。

**CCT 使用规则:**
- SKILL.md `## Key Parameters > LUT Parameters` 的 `temperature_shift` 范围 -150K to +150K(production minimum,见 [`cn-audience-color.md`](./cn-audience-color.md) §CN Warmth Preference Data);CIE-based 测量(非 LLM-as-judge)
- colorist 在 cross-shot consistency 检查时,white balance(CCT)是首要维度(per [`hurkman-color-pipeline.md`](./hurkman-color-pipeline.md) §Shot-Matching Protocol step 2)
- 短剧 部署 CCT 范围:2700K(tungsten warm)到 6500K(D65);超过 7500K 或低于 2500K 视为 operator override
- 男频 warm preference:CCT 5500-6500K 是 baseline(见 [`cn-audience-color.md`](./cn-audience-color.md));女频 cool preference:4500-5500K baseline

**CCT measurement 工具:**
- Resolve Color Page → white balance picker(点击 frame 中 neutral patch 自动计算 CCT)
- color checker passport + 光谱仪(production on-set 测量)
- LLM-as-judge 不适合 CCT 测量(因 LLM 无光谱分析能力);必须用 instrumented 工具

## HDR PQ EOTF

PQ(Perceptual Quantizer)EOTF 是 SMPTE ST 2084 标准定义的 HDR transfer function,由 Dolby 开发,被 Rec.2100 HDR 标准(2016)采纳。与 SDR Rec.709 gamma 不同,PQ 是 perceptually-linear(对人类视觉的 response linear)。

**PQ EOTF 关键参数:**

| 参数 | 数值 | 物理含义 |
|------|------|---------|
| Peak luminance(L_max) | **10000 cd/m²(nit)** | PQ 设计的理论上限(实际显示设备远未达到)|
| Reference white | **203 cd/m²** | BT.2408-4 定义的 reference white(SDR equivalent ~ 100 nits 的 HDR 等效值)|
| 50% signal luminance | ~ 92 cd/m² | PQ 设计:50% signal ≈ 92 nits(perceptually midpoint)|
| Reference black | 0.001 cd/m²(典型) | BT.2408-4 minimum;OLED 可达 0.0001 |
| Scene-cut threshold | 1000 cd/m² | 高于此值,人眼不适;cinema master 通常 capping 在 1000-4000 nits |
| Master typical peak | 1000-4000 cd/m² | Dolby Vision master / HDR10 master |

**PQ EOTF 公式(SMPTE ST 2084,简化版):**

```
L = 10000 * ( (c1 + c2 * V^m) / (1 + c3 * V^m) )^(1/n)
其中:
V = input signal value (0-1)
c1 = 0.8359375
c2 = 18.8515625
c3 = 18.6875
m = 0.1593017578125
n = 0.8359375
```

**PQ EOTF 使用规则:**
- AI 短剧/微电影 HDR 部署(抖音 HDR / Apple HDR-default)必须用 PQ EOTF master(SDR master 在 HDR 显示器上会显得 flat / dim)
- colorist 在 ACES pipeline 调色时,working space(ACEScg)与 HDR output(PQ)是分离的 —— 不要在 PQ 空间直接 creative grade(会因 perceptual-linear 失真);creative grade 在 ACEScg,经 ODT 转 PQ(见 [`hurkman-color-pipeline.md`](./hurkman-color-pipeline.md) §ACES Pipeline)
- Reference white 203 cd/m² 是 skin tone / 面部亮度 的目标;超过 1000 cd/m² 仅用于 specular highlights(灯光反射 / 太阳直射 / 火焰)
- PQ EOTF 与 HLG(Hybrid Log-Gamma,BT.2100 另一 HDR 标准)不兼容;抖音 HDR 当前主要用 HLG(更兼容 SDR 显示器);colorist 需根据平台选择 PQ 或 HLG master

**HDR vs SDR 调色 strategy:**
- SDR Rec.709 baseline:lift ±0.05 / gamma 0.8-1.2 / gain 0.8-1.2(见 [`hurkman-color-pipeline.md`](./hurkman-color-pipeline.md) §Lift/Gamma/Gain Ranges)
- HDR PQ:lift ±0.04 / gamma 0.85-1.15 / gain 0.75-1.25(HDR 更敏感,窗口收紧);perceptual effects 与 SDR 不同
- HDR 不等于"更 saturation" —— HDR 的优势是 wider dynamic range(更深的黑 + 更亮的白),不是更鲜艳的色;colorist 不应在 HDR master 中自动 +0.1 saturation

## Cross-References

- [`bellantoni-color-psychology.md`](./bellantoni-color-psychology.md) — Bellantoni 定义"选什么色"(creative 层);本 ref 定义"如何测量色对不对"(technical 层)
- [`hurkman-color-pipeline.md`](./hurkman-color-pipeline.md) — Hurkman 定义"如何调"(workflow 层);本 ref 定义"如何测量调得对不对"(verification 层);Hurkman §Shot-Matching Protocol step 4 的 ΔE ≤ 2.0 由本 ref 给出
- [`color-cross-cultural.md`](./color-cross-cultural.md) — Cross-cultural color perception 是 perceptual 层;本 ref 是 instrumented 层
- [`cn-audience-color.md`](./cn-audience-color.md) — CN audience warmth preference 是 perceptual-industry 层;本 ref 是物理化测量层
- [`../../_shared/glossary.md`](../../_shared/glossary.md) — [男频](../../_shared/glossary.md#男频-male-oriented-channel) / [女频](../../_shared/glossary.md#女频-female-oriented-channel) 术语首次出现处超链接

## Refresh Cadence

- **每 12 个月刷新一次**:ITU-R / SMPTE / CIE standards 每 3-5 年有 minor revision;ITU-R BT.2408 HDR operational practices 更频繁(2021 至 2026 已 4 版)
- **每 3 年**:验证 Rec.709 / Rec.2020 是否被新 standard 取代(目前 2026 年仍主导;Rec.2100 HDR 在 2024-2026 加速普及,但 Rec.709 SDR 仍是 mobile 短剧 主流)
- **触发即修**:见下节 drift signals

## Drift Signals

- **新 color space 标准**:若 ITU-R 或 SMPTE 推出 Rec.2030 / Rec.2100+ 等新色域标准(目前 2026 年无迹象),需更新 Rec.709/2020 表
- **新 ΔE 公式**:若有 CIE 2030+ 推出新 ΔE 公式(目前 CIE 2000 是最新),需更新 ΔE Tolerance 表
- **HDR 标准分裂**:若 HDR10+ / Dolby Vision / HLG / HDR Vivid(中国移动 5G 推的标准)出现分裂,需扩展 HDR PQ EOTF 表
- **AI 生成 frame ΔE 异常**:若 AI 生成 frame 的 inter-frame ΔE 显著高于 photographed frame(常见现象),需在 SKILL.md §Quality Thresholds 标注 "AI frame ΔE tolerance may need relaxation"
- **新 ΔE2000 工具普及**:若主流 grading 工具(Resolve / Baselight)默认从 ΔE1976 切到 ΔE2000,需更新 tolerance 表的数值映射

任何 drift signal 触发,需在本 ref 顶部 `**Last-verified:**` 字段更新日期,并在修订章节标注 "revised YYYY-MM due to [drift signal]"。
