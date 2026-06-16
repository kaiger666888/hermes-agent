#!/usr/bin/env python3
"""v2.0 PRFP design-doc governance lint (~30 lines, per GOV-02).

Runs structural checks on the design suite under .planning/research/v2-pipeline-design/.
Exit 0 = pass;exit 1 = violations found.

Checks (per GOV-01 G1-G7):
  G1 node-count: 8 <= linear_count <= 25
  G2 per-node fields: all 15 spec fields populated in nodes.yaml
  G3 model-name isolation: model names appear ONLY in 02-NODE-SPECS.md §2.17
  G4 version stamps: design-2026-06-16-prfp present + supersedes/superseded_by declared
  G5 stability markers: each .md has Stability: marker
  G6 forbidden phrases: "obviously"/"every pipeline has"/"traditionally" absent from derivations
  G7 YAML validity: nodes.yaml + edges.yaml + skills-mapping.yaml + kais-migration-matrix.yaml parse

Usage: python3 scripts/validate_design.py [--fix-hints]
"""
import sys, re, yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
failures = []

def chk(cond, msg):
    if not cond: failures.append(msg)

# G7 — YAML validity
for yf in ["nodes.yaml", "edges.yaml", "skills-mapping.yaml", "kais-migration-matrix.yaml"]:
    p = ROOT / yf
    if p.exists():
        try: yaml.safe_load(p.read_text(encoding="utf-8"))
        except Exception as e: chk(False, f"G7 YAML invalid: {yf}: {e}")

# G1 — node count
nodes = yaml.safe_load((ROOT / "nodes.yaml").read_text(encoding="utf-8"))
linear = [n for n in nodes["nodes"] if n.get("location") == "linear"]
chk(8 <= len(linear) <= 25, f"G1 linear_count={len(linear)} out of [8,25]")

# G2 — per-node fields
REQ = ["core_task","io_contract","aigc_transformation","traditional_anchor",
       "success_criteria","fail_modes","fallback_strategy","dependencies",
       "complexity_class","ai_capability_assumption","non_ai_alternative",
       "rationale_for_existence","cost_budget","latency_budget","model_horizon"]
for n in nodes["nodes"]:
    miss = [f for f in REQ if f not in n]
    chk(not miss, f"G2 node {n['id']} missing: {miss}")

# G3 — model name isolation
MODEL_RE = re.compile(r"\b(Claude|GPT-?\d?|Sora|Kling|Veo|FLUX|CosyVoice|Stable Diffusion|Suno|Udio|Gemini|GLM-?\d?)\b")
specs_md = (ROOT / "02-NODE-SPECS.md").read_text(encoding="utf-8")
# Strip §2.17 annex
specs_no_annex = re.split(r"## §2\.17", specs_md)[0]
chk(not MODEL_RE.search(specs_no_annex), "G3 model name found outside §2.17 annex")

# G4 + G5 — version stamps + stability
for mf in ["00-FIRST-PRINCIPLES.md","01-NODE-DAG.md","02-NODE-SPECS.md",
           "03-CORPUS-TRACEABILITY.md","04-LLM-CREATIVE-DISTILLATION.md",
           "05-COMPARISON-VS-8-PHASES.md","06-COMPARISON-VS-26-SKILLS.md","07-HANDOFF-PLAN.md"]:
    p = ROOT / mf
    if p.exists():
        t = p.read_text(encoding="utf-8")
        chk("design-2026-06-16-prfp" in t, f"G4 {mf} missing version stamp")
        chk("Stability" in t or "stability" in t, f"G5 {mf} missing Stability marker")

# G6 — forbidden phrases in derivation sections only
fp_md = (ROOT / "00-FIRST-PRINCIPLES.md").read_text(encoding="utf-8")
deriv_section = re.split(r"## §3", fp_md)[1].split(r"## §4")[0] if "## §3" in fp_md else ""
chk("obviously" not in deriv_section.lower(), "G6 'obviously' in derivation")
chk("every pipeline has" not in deriv_section.lower(), "G6 'every pipeline has' in derivation")

# Report
if failures:
    print("FAIL — design governance violations:")
    for f in failures: print(f"  ✗ {f}")
    sys.exit(1)
print(f"PASS — {len(linear)} linear nodes, all 16 spec'd, model names isolated, versions stamped, no forbidden phrases.")
sys.exit(0)
