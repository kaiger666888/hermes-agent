---
name: empty_list_skill
description: |
  Test fixture for CR-03: frontmatter with `related_skills:` and `tags:`
  present but with empty (None) values. `yaml.safe_load` returns `None`
  for these keys; `dict.get(key, default)` then returns `None`, NOT the
  default, which would crash `_filter_related_agents` + tag/metric list
  comprehensions with `TypeError: 'NoneType' object is not iterable`.
expert_id: empty_list_skill
metadata:
  hermes:
    related_skills:
    tags:
    metrics:
prerequisites: {}
---

# Empty List Values Skill

Body content does not matter for this test — the frontmatter above is
the load-bearing part.
