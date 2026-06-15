# Blender 4.x Previz Workflow + Camera Blocking

**Source:** Blender Foundation *Blender 4.x Documentation* (docs.blender.org, 2026);Hermes 3D tool catalog(2026-06);Fernandez *3D for Film Previz* (2019);CGSociety previz case studies(2020-2026)。
**Copyright:** Fair Use — paraphrased workflow; no proprietary project files. See [LICENSE.md](./LICENSE.md).
**Last-verified:** 2026-06-15
verified_date: 2026-06

## Summary

本 ref 定义 scene_builder 专家在 **3D previz + camera blocking** 决策时的**权威源**。它涵盖 Blender 4.x workflow + FxSxA scene matrix + camera blocking patterns + asset 复用。

## Blender 4.x Previz Workflow

### 关键 heuristic 1 (load-bearing): Previz 5-phase workflow

per Fernandez 2019 + Blender 4.x docs:

| Phase | 任务 | 工具 | Output |
|-------|------|------|--------|
| **1. Scene blockout** | 简单几何 blockout 主要 prop + environment | Blender primitives | Rough scene layout |
| **2. Camera blocking** | 主要 camera angle + 180° axis + sight lines | Blender camera + sequencer | Shot list previz |
| **3. Lighting previz** | 主要 light source + 3-point setup | Blender EEVEE render | Lighting reference |
| **4. Animation previz** | Character 简单 stick figure animation | Blender armature + Action | Movement reference |
| **5. Render previz** | Low-resolution preview render | EEVEE 1-2s/frame | Sequence preview |

### 关键 heuristic 2: Camera blocking 4 pattern

per Arijon 1976 + 现代 previz 实践:

| Pattern | 描述 | 用例 |
|---------|------|------|
| **Standard coverage** | MS two-shot + OTS A + OTS B + singles | 对话场景 |
| **Cross-coverage** | 两个 camera 同时 cover 双方 | 对峙 / 张力 |
| **Single-camera + insert** | 主 camera + 关键 insert 切换 | Action / choreography |
| **Multi-camera cinematic** | 多 camera 同步 for 一镜到底 | Long take / oner |

---

## FxSxA Scene Matrix

### 关键 heuristic 3: FxSxA 3-dimension scene encoding

per SKILL.md §FxSxA Scene Matrix:

| 维度 | 全名 | 取值 | 用途 |
|------|------|------|------|
| **F (Function)** | 场景功能 | dialogue / action / revelation / transition | Scene narrative purpose |
| **S (Scale)** | 场景规模 | intimate / small / medium / large / epic | Camera distance + asset count |
| **A (Atmosphere)** | 场景氛围 | bright / neutral / dark / surreal | Lighting + color baseline |

### 关键 heuristic 4: Per-FxSxA 推荐 camera coverage

| F × S × A | 推荐 coverage |
|-----------|---------------|
| dialogue × small × neutral | Standard coverage(MS + OTS) |
| action × large × dark | Multi-camera + low-key lighting |
| revelation × medium × bright | Single-camera + push-in |
| transition × epic × surreal | Drone + crane + stylized lighting |

---

## Asset Reuse in Previz

### 关键 heuristic 5: Previz asset library 复用

per [`../production/references/asset-reuse-plan.md`](../production/references/asset-reuse-plan.md):

```text
asset_library/scene_builder/
├── environments/
│   ├── office_generic.blend       (复用 for 多个 office 场景)
│   ├── street_urban.blend
│   ├── park.blend
│   └── ...
├── cameras/
│   ├── standard_3point.blend      (3-point lighting setup)
│   ├── handheld.blend
│   └── ...
└── characters/
    ├── rig_protagonist.blend      (绑定好的 character rig)
    └── ...
```

**复用率 target:** 70%+ 场景 reuse existing library asset。

---

## Anti-Patterns

### 关键 heuristic 6: Previz 5 大 anti-pattern

1. **Skip previz anti-pattern:** 直接生成 final shot 不做 previz。**Mitigation:** 5-phase workflow mandatory。
2. **Too detailed blockout anti-pattern:** Previz 用高细节 asset。**Mitigation:** primitives + simple rigs。
3. **No camera blocking anti-pattern:** Previz 仅做 scene 不做 camera。**Mitigation:** Phase 2 camera blocking。
4. **No 180° axis plan anti-pattern:** Previz 不规划 axis。**Mitigation:** 显式 axis_line per shot。
5. **No asset reuse anti-pattern:** 每个 previz 从零开始。**Mitigation:** asset_library 复用。

---

## Glossary

- **Previz:** Previsualization,3D scene + camera + animation preview。
- **Blockout:** 简单几何 layout 主要 prop。
- **Camera blocking:** 规划 camera angle + sight line + axis。
- **FxSxA:** Function × Scale × Atmosphere scene matrix。
- **EEVEE:** Blender 实时 render engine。

---

*Generated: 2026-06-15 as part of Phase 5 REFACTOR-rest-08 (scene_builder RAG uplift).*
*Source provenance: Blender Foundation 4.x docs (2026) / Hermes 3D tool catalog / Fernandez 2019 / CGSociety case studies — fair use paraphrase + short technical phrases only.*
