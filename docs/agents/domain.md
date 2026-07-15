# Domain Docs

This is a single-context repository. Engineering skills consume the domain model from
root `CONTEXT.md` and architectural decisions from `docs/adr/`.

## Before exploring

- Read root `CONTEXT.md` when it exists.
- Read ADRs in `docs/adr/` that affect the area being changed.
- Proceed silently when a referenced domain file does not yet exist.

## Vocabulary

Use the canonical terms defined in `CONTEXT.md` in specs, tickets, implementation, and
tests. Do not substitute terms listed under `_Avoid_`. A missing term may indicate
either vocabulary drift or a domain-modeling gap.

## ADR conflicts

Surface any proposed change that contradicts an existing ADR rather than silently
overriding the recorded decision.
