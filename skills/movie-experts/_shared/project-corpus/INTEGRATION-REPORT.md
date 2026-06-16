# Project Corpus Integration Report — Phase 8

**Date:** 2026-06-16
**Source Project:** `/home/kai/Downloads/100+本影视剪辑书/`
**Target:** `/data/workspace/hermes-agent/skills/movie-experts/`
**Status:** ✅ Complete

---

## 📊 Integration Stats

| Metric | Before Phase 8 | After Phase 8 |
|---|---|---|
| **Total experts** | 23 | **26** (+3 new) |
| **Total references** | ~80 | **98** (+13 new project-corpus + 5 cross-refs to existing experts) |
| **Total corpus coverage** | Industry-standard only | **Industry + 102 Chinese film books** |
| **Theoretical depth** | Pragmatic | **Now has formalism/realism/psychoanalytic/history frameworks** |
| **Documentary support** | None | **Now has 4-school + 6-type + ethnographic** |
| **Animation support** | None (just animator execution) | **Now has Disney 4-stage + 12-pipeline + cross-cultural adaptation** |

---

## 🆕 What Was Added

### 3 New Experts

```
skills/movie-experts/
├── theory_critic/                    # NEW (Phase 8)
│   ├── SKILL.md
│   └── references/
│       └── narrative-revolution-and-modernism.md
├── documentary_maker/                # NEW (Phase 8)
│   ├── SKILL.md
│   └── references/                   # (uses _shared/project-corpus)
└── animation_studio/                 # NEW (Phase 8)
    ├── SKILL.md
    └── references/                   # (uses _shared/project-corpus)
```

### Shared Project Corpus

```
skills/movie-experts/_shared/project-corpus/
├── README.md                                       # 102-book master index
├── INTEGRATION-REPORT.md                           # THIS FILE
├── theory-formalism-vs-realism.md                  # Andrew / Agel / Balázs
├── film-philosophy-baz-tarkovsky.md                # Bazin / Tarkovsky / 七部半
├── psychoanalytic-film-theory.md                   # Mulvey / Žižek / Metz
├── auteur-director-biographies.md                  # 7 director bios
├── film-criticism-methodology.md                   # Dai Hua / Writing / Foreign
├── film-history-methods.md                         # Allen / Oxford / Sadoul
├── narrative-revolution-and-modernism.md (in theory_critic/references/)
├── screenwriting-chinese-and-supplementary.md      # 芦苇 / Viki King / etc.
├── cinematography-masterclass-and-grammar.md       # Arijon / 100 techniques
├── lighting-equipment-and-design.md                # Equipment + Color narrative
├── editing-sound-post.md                           # Murch / Sound Bible / Documentary
├── production-chinese-and-low-budget.md            # Filmmaking handbooks
└── animation-disney-system.md                      # Disney 4-stage + Mulan
```

### Existing Experts Enhanced (cross-refs added)

| Expert | Cross-ref added |
|---|---|
| `style_genome` | `auteur-director-biographies.md` |
| `screenplay` | `screenwriting-chinese-and-supplementary.md` |
| `cinematographer` | `cinematography-masterclass-and-grammar.md` + `lighting-equipment-and-design.md` |
| `editor` | `editing-sound-post.md` |
| `colorist` | `lighting-equipment-and-design.md` §Part 2 |
| `production` | `production-chinese-and-low-budget.md` |

---

## 🔗 Integration Pattern

### How existing experts integrate

```yaml
# Example: screenplay/SKILL.md (excerpt)
references:
  # ... existing 5 refs ...
  - ../_shared/project-corpus/screenwriting-chinese-and-supplementary.md
    # Adds: Lu Wei (芦苇) epic adaptation + Viki King 21-day + Liu Tianci theme
    #       "cleverness" + Hook design 4 sources + O'Bannon dynamic structure +
    #       Winston film grammar
```

### How new experts consume project corpus

```yaml
# Example: theory_critic/SKILL.md (excerpt)
references:
  - ../_shared/project-corpus/theory-formalism-vs-realism.md
  - ../_shared/project-corpus/film-philosophy-bazin-tarkovsky.md
  - ../_shared/project-corpus/psychoanalytic-film-theory.md
  - ../_shared/project-corpus/auteur-director-biographies.md
  - ../_shared/project-corpus/film-criticism-methodology.md
  - ../_shared/project-corpus/film-history-methods.md
  - ./references/narrative-revolution-and-modernism.md
  - ../_shared/project-corpus/README.md  # corpus navigation
```

---

## 📚 Project Corpus Coverage Matrix

| Category | Books | Mapped to Refs |
|---|---|---|
| **剧本 (Screenwriting)** | 15 | `screenwriting-chinese-and-supplementary.md` |
| **分镜/导演 (Pre-Viz)** | 12 | `cinematography-masterclass-and-grammar.md` |
| **拍摄/摄影/美术 (Production)** | 18 | `cinematography-masterclass-and-grammar.md` + `lighting-equipment-and-design.md` + `animation-disney-system.md` |
| **后期/剪辑/声音 (Post)** | 12 | `editing-sound-post.md` |
| **制片 (Producing)** | 8 | `production-chinese-and-low-budget.md` |
| **理论批评 (Theory)** | 25 | 6 theory refs (formalism/bazin-tark/psycho/auteur/criticism/history) |
| **史类 (History)** | 5 | `film-history-methods.md` |
| **单片研究 (Single-Film)** | 7 | Distributed across refs as case studies |
| **TOTAL** | **102** | **100% covered** |

---

## 🎯 RAG Retrieval Pattern

### For theory / criticism / research tasks
```python
# Pseudo-code
agent.invoke("theory_critic", {
    "task": "analyze",
    "target": "<film or 短剧 IP>",
    "framework": "auto"  # or "formalism" / "psychoanalytic" / "auteur" / etc.
})

# Internally retrieves from:
# tags="expert:theory_critic,domain:formalism-vs-realism"
# tags="expert:theory_critic,domain:bazin-tarkovsky"
# tags="expert:theory_critic,domain:psychoanalytic-theory"
# tags="expert:theory_critic,domain:auteur-research"
# tags="expert:theory_critic,domain:criticism-methodology"
# tags="expert:theory_critic,domain:film-history-methods"
# tags="expert:theory_critic,domain:modernism-benjamin-adorno"
# tags="domain:project-corpus,category:理论批评"
```

### For documentary tasks
```python
agent.invoke("documentary_maker", {
    "task": "plan",
    "subject": "<topic>",
    "type": "auto"  # or "observational" / "participatory" / "reflexive" / etc.
})

# Internally retrieves from editing-sound-post.md §Part 5 (Wang Jing 6-lecture)
```

### For animation tasks
```python
agent.invoke("animation_studio", {
    "task": "plan",
    "type": "3d_feature",  # or "2d_short" / "stop_motion" / "animation_style_短剧"
    "source": "<folk tale or original>"
})

# Internally retrieves from animation-disney-system.md
```

### For existing experts with corpus enrichment
```python
# screenplay can now also leverage 芦苇/Viki King/O'Bannon methods
agent.invoke("screenplay", {
    "task": "write_short_drama",
    "chinese_adaptation": true,
    "epic_source": true  # triggers Lu Wei method
})

# cinematographer can now leverage Arijon grammar + 21 masters
agent.invoke("cinematographer", {
    "task": "design_shot_intent",
    "reference_master": "deakins"  # triggers master-class retrieval
})
```

---

## ✅ Validation Checklist

- [x] All 3 new experts have `SKILL.md` with proper frontmatter
- [x] All 3 new experts follow `_shared/SKILL-LAYOUT.md` conventions
- [x] All 3 new experts declare `related_skills` to existing experts
- [x] All 13 project-corpus refs have proper source attribution + Fair Use notice
- [x] All 13 project-corpus refs have `verified_date: 2026-06`
- [x] Existing experts updated with cross-refs to project corpus
- [x] Existing experts' `related_skills` updated to include new experts
- [x] `README.md` updated to reflect 26-expert suite
- [x] DAG diagram shows Phase 8 cross-cutting layer
- [x] 102-book index in `_shared/project-corpus/README.md`
- [x] Integration report (this file) created

---

## 🔄 Maintenance

### When source project adds new books
1. Re-run `python /home/kai/Downloads/100+本影视剪辑书/scripts/build-index.py`
2. Update `_shared/project-corpus/README.md` with new book entries
3. Identify which existing ref needs update (or create new ref)
4. Bump `verified_date` in affected ref
5. If significant: create new expert or split existing

### When Hermes runtime changes
- All Phase 8 experts follow provider-agnostic RAG pattern (per `_shared/RAG-INVOCATION-PATTERN.md`)
- Static refs are authoritative; memory plugin is optimization
- No vendor-specific tool names hard-coded

---

## 🎬 Summary

The 102-book Chinese film production library has been **deeply integrated** into Hermes Agent's movie-experts suite:

- **3 new consultative experts** (theory_critic / documentary_maker / animation_studio) wrap the corpus into actionable skills
- **6 existing experts** (style_genome / screenplay / cinematographer / editor / colorist / production) now have enriched cross-references
- **13 corpus ref files** serve as the unified RAG layer
- **100% of 102 books** are mapped to at least one ref
- All integration follows existing Hermes conventions (SKILL-LAYOUT / RAG-INVOCATION-PATTERN / glossary)

The movie-experts suite can now handle:
- ✅ AI 短剧 production (existing 23 experts)
- ✅ **Academic film criticism / theory** (theory_critic)
- ✅ **Documentary production** including ethnographic (documentary_maker)
- ✅ **Animation production** including cross-cultural adaptation (animation_studio)
- ✅ **Chinese-source adaptation** (Lu Wei / 21-day / etc.)
- ✅ **Master-class reference** (21 cinematographers, 7 director bios)
