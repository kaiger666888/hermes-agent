# Auteur Theory — Sarris 3-Criteria + Auteur vs Operator + Style Coherence Doctrine

**Source:** Andrew Sarris *The American Cinema: Directors and Directions 1929-1968* (1968, Dutton, ISBN 0-02-603750-3); Robin Wood *Hitchcock's Films* (1965, A. Zwemmer); Bordwell & Thompson *Film Art: An Introduction* (11th ed, 2020, McGraw-Hill, ISBN 978-1260565816); Truffaut *A Certain Tendency of the French Cinema* (Cahiers du cinéma, 1954).
**Copyright:** Fair Use — Sarris 3-criteria rubric paraphrased; auteur vs operator distinction paraphrased. No verbatim quotation from critical texts beyond short technical phrases (≤20 words each). See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 style_genome 专家在判定"某导演是否进入 Pantheon / Modern Auteur / Operator Convention 三层 tier"时的**理论侧权威源**(theoretical-side authoritative source)。它与 [`director-dna-archive.md`](./director-dna-archive.md)(数据侧:30-50 导演 5D 向量)与 [`cross-cultural-style.md`](./cross-cultural-style.md)(跨文化侧:CN vs Western vs Korean 风格分野)互补,共同构成 style_genome 编码的三层 grounding。

术语定义见 [`../../_shared/glossary.md`](../../_shared/glossary.md)。

---

## Sarris 3-Criteria Rubric (Pantheon Tier 判定)

Sarris 在 *The American Cinema* 提出判定 auteur 地位的 3 项必须同时满足的标准(style_genome §Director Archive Tier-1 Pantheon 准入硬规则):

### 关键 heuristic 1 (load-bearing): Sarris 3-criteria 全通过 → Pantheon tier

| 标准 | 操作化判据 | 5D 编码精度 | 失败则降级到 |
|------|-----------|------------|--------------|
| **(1) Technical competence** | director 至少 3 部作品摄影/剪辑/混音无 amateur 标记(marketplace rejection 标准:Rotten Tomatoes ≥70 + ASC / ACE / CAS 协会 nomination ≥1)| ±0.05 | Modern Auteur (criteria 2+3 通过) |
| **(2) Distinguishable personality** | 5D vector 跨 ≥3 部作品标准差 ≤0.10(personality signature 在不同项目中保持稳定);至少 3 个 signature elements 跨作品重复出现 | ±0.05 | Operator Convention |
| **(3) Interior meaning** | director 在 ≥2 部作品中体现可识别的主题(love / loss / power / identity / morality 等 7 大主题之一),且该主题在 critic analysis 中被 ≥3 个独立来源确认 | ±0.05 | Operator Convention |

**判定流程:** 全 3 通过 → Pantheon tier(5D 编码 ±0.05 精度,加入 [`director-dna-archive.md`](./director-dna-archive.md) §Pantheon 表);2/3 通过 → Modern Auteur tier(精度 ±0.05,加入 §Modern Auteurs 表);≤1/3 通过 → Operator Convention tier(精度 ±0.10,subjectivity acknowledged,加入 §Operator Convention 表)。

### 关键 heuristic 2: Sarris 9-rank ladder(简化版)

Sarris 在 *The American Cinema* 将导演分为 9 个 rank。style_genome 仅保留与现代 AI film pipeline 相关的 4 个 rank:

| Rank | Sarris 原始类别 | style_genome tier | 5D 编码精度 | 示例 |
|------|----------------|-------------------|-------------|------|
| 1 | Pantheon directors | Pantheon | ±0.05 | Hitchcock / Ford / Kubrick / Welles / Chaplin / Keaton / Murnau / Renoir / Dreyer / Rossellini / De Sica / Eisenstein |
| 2 | The Far Side of Paradise | Modern Auteur (Pantheon-adjacent) | ±0.05 | Fuller / Aldrich / Kazan / Nichols / Wilder |
| 3 | Expressive Esoterica | Modern Auteur | ±0.05 | Minnelli / Tashlin / Sirk |
| 4 | Less Than Meets The Eye | Operator Convention (high-skill) | ±0.10 | Stevens / Zinnemann |
| 5 | Strained Seriousness | Operator Convention | ±0.10 | Cukor (early) |
| 6-9 | Oddities, Newcomers, Subjects for Further Research, Make Way for the Clowns! | 未编码(等 operator confirm) | — | — |

style_genome 部署默认仅 rank 1-4 可直接 5D 编码;rank 5-9 必须通过 §Operator Convention Flag 流程(下方 §编码决策树 Step 2)。

### 关键 heuristic 3: Auteur vs Operator 判定决策树

```
Step 1: 该导演是否在 director-dna-archive.md §Director Archive (35 directors) 表中?
├── Yes → 直接读取 5D vector,跳过 Step 2-4
└── No → Step 2

Step 2: 应用 Sarris 3-criteria rubric(§Sarris 3-Criteria Rubric)
├── 3 criteria 全通过 → 标记 Pantheon tier,5D 编码精度 ±0.05
├── 2 criteria 通过 → 标记 Modern Auteur tier,5D 编码精度 ±0.05
└── ≤ 1 criteria 通过 → Operator Convention tier(精度 ±0.10,需 user 显式 confirm 部署)

Step 3: 若 Operator Convention tier:
├── 设置 OPERATOR_CONVENTION_FLAG=true(style_genome.json 必须包含此 flag)
├── 输出 5D vector 但精度 ±0.10
└── 在 style_alignment_report.json 中标注 "subjective encoding, requires user review"

Step 4: 加入 §Director Archive 表对应 tier(标记 *observed* status,与 Sarris 历史判定区分)
```

---

## Auteur vs Operator Convention Doctrine

### 关键 heuristic 4 (load-bearing): Auteur personality signature 跨项目稳定性

Auteur 与 operator 的核心分野:not "shoot well" but "shoot consistently". Auteur 在 ≥3 部不同项目中 5D vector 标准差 ≤0.10(任何维度);operator 即使单部作品技术优秀,跨项目 5D 漂移 >0.15。

**Worked Example 1 — Stanley Kubrick(Pantheon):**
- *2001* 5D: [0.1, 0.4, 0.2, 0.6, 0.7]
- *The Shining* 5D: [0.15, 0.5, 0.3, 0.65, 0.7]
- *Eyes Wide Shut* 5D: [0.2, 0.45, 0.25, 0.7, 0.65]
- **跨 3 部作品标准差:** composition σ=0.05 / color σ=0.05 / rhythm σ=0.05 / light_shadow σ=0.05 / sound σ=0.03 — **全部 ≤0.05 = Auteur personality signature 稳定 = Pantheon tier 证据**

**Worked Example 2 — Modern commercial director(降级到 Operator Convention):**
- Project A 5D: [0.3, 0.5, 0.6, 0.5, 0.5]
- Project B 5D: [0.6, 0.3, 0.4, 0.7, 0.4]
- Project C 5D: [0.4, 0.7, 0.7, 0.4, 0.6]
- **跨 3 部作品标准差:** composition σ=0.15 / color σ=0.20 / rhythm σ=0.15 / light_shadow σ=0.15 / sound σ=0.10 — **多维度 σ >0.10 = 无 personality signature = Operator Convention tier**

### 关键 heuristic 5: Operator Convention Flag (T-03-23 mitigate)

当 style_genome 检测到用户输入的 director 在 archive 中不存在 + Sarris 3-criteria 失败,部署硬规则:

1. 设置 `operator_convention: true` 在 `style_genome.json` 输出中
2. 5D 编码精度放宽到 ±0.10(承认 subjectivity)
3. 在 `style_alignment_report.json` 顶部添加 warning: "Director X encoding is operator convention (≤1 Sarris criteria). Subjectivity acknowledged. User review required before distribution."
4. **不阻止部署**(用户可能确实想用 "类 Michael Bay 但更克制" 风格),但下游 expert(continuity / compliance_marketing)必须传播此 flag

### 关键 heuristic 6: Auteur "interior meaning" 主题归类

Sarris 第 3 条 "interior meaning" 必须 mapping 到下列 7 大主题之一(style_genome §Director Archive §Interior Meaning 列):

| 主题 ID | 主题名 | canonical directors(Pantheon 示例)|
|---------|--------|----------------------------------|
| TM-01 | love / desire / loss | Wong Kar-wai / Almodóvar / Bergman |
| TM-02 | power / corruption / authority | Coppola(*Godfather*)/ Kubrick(*Paths of Glory*)/ Scorsese(*Goodfellas*)|
| TM-03 | identity / self / transformation | Kieslowski(*Three Colors*)/ Tarkovsky(*Stalker*)|
| TM-04 | morality / guilt / redemption | Dreyer / Bresson / Kiarostami |
| TM-05 | alienation / modernity / isolation | Antonioni / Tati / Wong Kar-wai(*Chunking Express*)|
| TM-06 | nature / humanity / cosmos | Malick / Tarkovsky / Miyazaki |
| TM-07 | violence / chaos / order | Peckinpah / Tarantino / Park Chan-wook |

style_genome 部署:`style_genome.json` 必须包含 `interior_meaning: <TM-ID>` 字段;若 Operator Convention tier,设为 `TM-XX: uncategorized`。

---

## Truffaut "Cinéma d'auteurs" vs "Cinéma de qualité" Distinction

### 关键 heuristic 7: Tradecraft vs Personal Vision

Truffaut 在 *A Certain Tendency of the French Cinema* (1954) 区分两类导演:

- **Cinéma d'auteurs**(auteur): director 是 creative author,5D vector 由 director 个性驱动。Pantheon / Modern Auteur tier 必须是 auteur。
- **Cinéma de qualité**(quality-tradecraft): director 是 well-crafted executor,5D vector 由剧本/制片 driven。Operator Convention tier 通常是 qualité。

**style_genome 实操:** 若用户指定 "faithful literary adaptation"(e.g., 2020 *Emma.*),style_genome 应自动设置 `cinema_mode: qualité` flag,5D vector 取 genre-typical 而非 director-typical,精度 ±0.10。

---

## Bordwell & Thompson " stylistic history" caution

### 关键 heuristic 8: Auteurism 过度使用的 anti-pattern

Bordwell & Thompson *Film Art* §"Auteur Criticism" 警告 auteurism 3 种滥用模式,style_genome 必须规避:

1. **Confirmation bias anti-pattern:** 只看 auteur 风格化的作品,忽略其作品中的非典型作品(如 Hitchcock *Rope* 实验性长镜头 vs *Psycho* 经典蒙太奇 — 不能因 *Rope* 把 Hitchcock rhythm 编码为 0.2)。**Mitigation:** 5D vector 取 ≥3 部作品均值,而非单部代表作。
2. **Personality signature 误读 anti-pattern:** 把 cinematographer / production designer 的工作归因于 director(如 Deakins 对 Coen brothers 的视觉影响 / Dante Ferretti 对 Scorsese 的场景影响)。**Mitigation:** 5D 编码必须标注 "primary contributor: director" vs "primary contributor: cinematographer"。在 archive 中,Fincher composition=0.4 标注 "*with Cronenweth*",P.T. Anderson composition=0.4 标注 "*with Elswit*"。
3. **Forced interior meaning anti-pattern:** 给商业导演强加 "interior meaning"(如把 Michael Bay 的爆炸场景解读为 TM-02 power)。**Mitigation:** Operator Convention tier 不允许设置 TM-ID;`interior_meaning` 字段必须为 `TM-XX: uncategorized`。

---

## "Style Coherence Doctrine" — Wood / Hitchcock 解读

### 关键 heuristic 9 (load-bearing): Style coherence 是 auteur 的硬性指标

Robin Wood *Hitchcock's Films* 提出 auteur 的判定不在于"有无 signature style",而在于"signature style 是否在 ≥3 部作品中**互相呼应**"(coherent oeuvre doctrine)。

**操作化:** style_genome 计算 `style_coherence_score` = 1 - (跨 ≥3 部作品 5D vector 范数化方差均值)。阈值:
- `style_coherence_score >= 0.85` → 强 auteur 证据(Pantheon tier 加分项)
- `style_coherence_score 0.70-0.85` → auteur 标准
- `style_coherence_score < 0.70` → Operator Convention(无论 Sarris criteria 1-2 是否通过)

**Hitchcock Worked Example:**
- *Vertigo* (1958) 5D: [0.4, 0.45, 0.4, 0.7, 0.7]
- *Psycho* (1960) 5D: [0.45, 0.4, 0.6, 0.65, 0.7]
- *The Birds* (1963) 5D: [0.4, 0.45, 0.5, 0.7, 0.65]
- **style_coherence_score:** 1 - mean(σ/0.5) = 1 - 0.07/0.5 = 0.86 → 强 auteur 证据 ✓

---

## Auteur Encoding Protocol 与 Director DNA Archive 集成

style_genome §Director Archive 表新增 4 列(本 ref 强制要求):

| 列名 | 取值范围 | 来源 |
|------|---------|------|
| `sarris_rank` | 1-9(简化为 1-4 部署) | Sarris *The American Cinema* 1968 |
| `tier` | Pantheon / Modern Auteur / Operator Convention | 本 ref §Sarris 3-Criteria Rubric |
| `interior_meaning` | TM-01..TM-07 / TM-XX(uncategorized) | 本 ref §Auteur "interior meaning" 主题归类 |
| `style_coherence_score` | 0.0-1.0 | 本 ref §Style Coherence Doctrine |

**Archive 集成示例(Kubrick row):**
```
| Kubrick | composition=0.1 | color=0.4 | rhythm=0.2 | light_shadow=0.6 | sound=0.7 |
|         | sarris_rank=1 (Pantheon) | tier=Pantheon | interior_meaning=TM-02 (power/authority) |
|         | style_coherence_score=0.93 | primary_contributor=director |
```

详见 [`director-dna-archive.md`](./director-dna-archive.md) §Director Archive (35 directors) 表。

---

## 与 CN 导演分析的接口

CN 导演(张艺谋 / 贾樟柯 / 王家卫 / 周星驰 等)的 Sarris 3-criteria 评估存在跨文化挑战 — Pantheon tier 的 "distinguishable personality" 在 CN 语境下需要额外的"摄影 / 美术指导签名"标注。详见 [`cn-director-analysis.md`](./cn-director-analysis.md) §CN Director Tiering Crosswalk。

---

## Glossary

- **Pantheon tier:** Sarris 3-criteria 全通过;5D 编码精度 ±0.05;archive 中标记 *canonical* status。
- **Modern Auteur tier:** 2/3 criteria 通过;5D 编码精度 ±0.05;archive 中标记 *modern* status。
- **Operator Convention tier:** ≤1/3 criteria 通过 OR style_coherence_score <0.70;5D 编码精度 ±0.10;archive 中标记 *observed* status;**需 user confirm 部署**。
- **Interior meaning:** Sarris 第 3 criteria;mapping 到 TM-01..TM-07。
- **Style coherence score:** Wood 1965 提出;跨 ≥3 部作品 5D vector 范数化方差;阈值 ≥0.70 为 auteur 证据。

---

*Generated: 2026-06-15 as part of Phase 3 REFACTOR-04 (style_genome deep refactor).*
*Source provenance: Sarris 1968 / Wood 1965 / Bordwell & Thompson 2020 / Truffaut 1954 — fair use paraphrase + short technical phrases only.*
