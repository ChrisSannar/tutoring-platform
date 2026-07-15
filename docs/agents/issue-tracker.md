# Issue tracker: Local Markdown

Issues and specs for this repository live as Markdown files in `.scratch/`.

## Conventions

- One feature per directory: `.scratch/<feature-slug>/`.
- The spec is `.scratch/<feature-slug>/spec.md`.
- Implementation issues are one file per ticket at
  `.scratch/<feature-slug>/issues/<NN>-<slug>.md`, numbered from `01`.
- Triage state is recorded as a `Status:` line near the top of each issue file.
- Comments and conversation history append under a `## Comments` heading.

## Skill operations

When a skill says to publish to the issue tracker, create the appropriate file beneath
`.scratch/<feature-slug>/`. When a skill says to fetch a ticket, read the referenced
file or issue number directly.

## Wayfinding operations

- Map: `.scratch/<effort>/map.md`, containing Notes, Decisions-so-far, and Fog.
- Child ticket: `.scratch/<effort>/issues/NN-<slug>.md`.
- Child metadata includes `Type:` (`research`, `prototype`, `grilling`, or `task`) and
  `Status:` (`claimed` or `resolved`).
- Blocking is recorded as `Blocked by: NN, NN`; a ticket becomes unblocked when every
  listed ticket is resolved.
- The frontier is the first numbered open, unblocked, and unclaimed ticket.
- Claim by setting `Status: claimed` before work.
- Resolve by appending an `## Answer`, setting `Status: resolved`, and adding a context
  pointer to the map's Decisions-so-far.
