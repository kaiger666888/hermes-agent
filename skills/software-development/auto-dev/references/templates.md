# MVP Document Templates

## REQUIREMENTS.md Template

```markdown
# Requirements: [Project Name]

## Overview
[1-2 sentence project description]

## Target Users
- [Primary user type]

## User Stories
1. As a [user], I want to [action] so that [benefit]
2. ...

## Functional Requirements
### Must Have (MVP)
- [FR-001] [Requirement description]
- [FR-002] ...

### Nice to Have (Post-MVP)
- [FR-101] ...

## Non-Functional Requirements
- Performance: [target]
- Tech stack: [chosen stack with reasoning]

## Acceptance Criteria
- [ ] [AC-1] ...
- [ ] [AC-2] ...

## Out of Scope
- [Explicitly excluded features]
```

## ARCHITECTURE.md Template

```markdown
# Architecture: [Project Name]

## Tech Stack
| Layer | Technology | Reason |
|-------|-----------|--------|
| Frontend | ... | ... |
| Backend | ... | ... |
| Database | ... | ... |
| Deploy | ... | ... |

## System Overview
[Component diagram description]

## Data Flow
[Step-by-step data flow]

## Key Design Decisions
1. [Decision] → [Reason]

## Directory Structure
\`\`\`
project/
├── src/
├── tests/
├── docs/
└── ...
\`\`\`

## API Design (if applicable)
| Endpoint | Method | Description |
|----------|--------|-------------|
| /api/... | GET | ... |
```

## MVP-PLAN.md Template

```markdown
# MVP Implementation Plan: [Project Name]

## Milestones

### M1: Foundation [Est: Xh]
- [ ] Project scaffolding
- [ ] Core data models
- [ ] Basic CRUD
- **Deliverable**: Working local dev environment

### M2: Core Feature [Est: Xh]
- [ ] Main user flow
- [ ] UI components
- **Deliverable**: Core feature working end-to-end

### M3: Polish [Est: Xh]
- [ ] Error handling
- [ ] Basic styling
- [ ] Deploy setup
- **Deliverable**: Deployed MVP ready for review

## Risk Mitigation
| Risk | Probability | Mitigation |
|------|------------|------------|
| ... | ... | ... |
```
