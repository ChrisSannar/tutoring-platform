# Agent Instructions

## Agent skills

### Issue tracker

Issues and specs use local Markdown under `.scratch/`. See
`docs/agents/issue-tracker.md`.

### Triage labels

Use the default five-role label vocabulary. See `docs/agents/triage-labels.md`.

### Domain docs

This is a single-context repository using root `CONTEXT.md` and `docs/adr/`. See
`docs/agents/domain.md`.

## Module size

Modules should strive to stay small and cohesive — around 100 lines is a good
guideline. It is a principle, not a rule: when a cohesive module genuinely
needs more lines, keep it together rather than splitting it into fragments.
