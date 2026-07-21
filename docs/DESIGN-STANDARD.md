# Constellation Design Standard

Status: Approved for future application-wide adoption  
Reference implementation: authenticated `/tutor` workspace  
Prototype reference: `/style-prototype/10`

## Scope

Constellation is the visual standard for future work across the application. This
document defines the approved language; it does not authorize or include changes to
the Landing, Student, Invitation, authentication, or checkout surfaces.

When adoption begins, preserve each surface's behavior, semantics, and information
hierarchy. Apply the standard through shared theme tokens and scoped component rules,
not by copying prototype markup or introducing a component framework.

## Principles

- Operational and calm: dark navy neutrals carry the interface; blue signals focus,
  state, and identity rather than filling large controls.
- Square and structured: sections, cards, dialogs, inputs, selects, textareas, and
  buttons use square corners and thin borders.
- Layered without ornament: background, surface, raised, border, and text colors
  establish hierarchy. Shadows are restrained and never replace borders.
- Theme parity: light and dark modes keep the same geometry, hierarchy, states, and
  interaction behavior.
- Accessible by default: keyboard focus remains visible, status is not conveyed by
  color alone, and controls retain semantic labels and usable target sizes.

## Theme tokens

Use semantic tokens instead of raw colors in component rules. These values are the
approved baseline.

| Token | Light | Dark | Purpose |
| --- | --- | --- | --- |
| `background` | `#eef3f9` | `#07111f` | Page and workspace canvas |
| `surface` | `rgb(250 252 255 / 94%)` | `rgb(11 25 43 / 94%)` | Primary sections |
| `raised` | `#ffffff` | `#102741` | Inputs and nested cards |
| `ink` | `#122239` | `#edf5ff` | Primary text |
| `muted` | `#607086` | `#8fa6bf` | Secondary text |
| `line` | `#b7c6d8` | `#1e3d5d` | Standard borders and minor dots |
| `line-strong` | `#91a7c0` | `#315779` | Input borders and major dots |
| `accent` | `#146cff` | `#9cbcff` | Focus, identity, and active state |
| `control` | `#122239` | `#171e2b` | Action-control fill |
| `control-ink` | `#ffffff` | `#ffffff` | Action-control text |
| `control-border` | Same as `control` | Same as `control-ink` | Action-control border |

Derived hover, focus, and shadow colors should use `color-mix()` with these tokens so
they remain theme-aware.

## Canvas

Full workspace surfaces use a subtle dotted field:

- Minor dots repeat every `28px` using `line` at approximately 45% strength.
- Major dots repeat every `140px` using `line-strong` at approximately 55% strength.
- Dots remain visible behind surfaces without competing with text or controls.
- Content pages that do not use a full workspace may omit the dotted field, but keep
  the same background and surface hierarchy.

## Typography

- Use Georgia or the existing serif stack for page-level weekday headings, times, and
  prominent metrics.
- Use the system sans-serif stack for navigation, labels, controls, operational copy,
  and data.
- Use weight, size, and spacing for hierarchy; avoid decorative subtitles and excess
  uppercase copy.

## Surfaces and geometry

- Sections use `surface`, a `1px line` border, and square corners.
- Nested cards and editable fields use `raised` with the same square geometry.
- Inputs, selects, textareas, dialogs, buttons, and articles use `border-radius: 0`.
- Circular geometry is reserved for compact status markers and count badges.
- Connected information, such as metric strips, shares borders instead of appearing
  as unrelated floating cards.

## Buttons

Action buttons use a secondary-style treatment rather than a bright blue fill.

- Light mode: `control` fill, matching `control` border, and `control-ink` text.
- Dark mode: `control` fill with `control-ink` for both border and text.
- Hover: mix approximately 12% `accent` into `control`; do not add elevation.
- Focus: use a clearly visible `accent` outline outside the control.
- Disabled: use `background`, `line`, and `muted`; do not present disabled actions as
  active.
- Navigation controls may remain transparent. The current item uses a surface fill and
  an accent edge, with `aria-current` exposing the same state semantically.

## Inputs

- Use `raised` fill, `line-strong` border, and `ink` text.
- Hover changes the border to `accent`.
- Keyboard focus uses an `accent` border and a translucent accent ring.
- Read-only fields use `background`, `line`, and `muted` to distinguish them from
  editable fields without reducing legibility.
- Labels remain visible and are not replaced by placeholders.

## Count badges

Count badges follow the action-control palette instead of using a bright accent fill:

- `1.5rem` square with a circular shape.
- `control` fill.
- `control-ink` border and text.
- Grid or flex centering in both axes; do not position the number with padding or
  floats.
- Include an accessible label that explains the count, such as “3 open requests.”

## Responsive behavior

- Preserve every work area at narrow widths; reorganize rather than hide content.
- Controls and fields must not cause horizontal page overflow at `390px`.
- Navigation may change orientation while retaining every destination, visible focus,
  keyboard operation, and current-state indication.
- Keep information order intentional when grids collapse; do not rely on visual CSS
  placement to change reading order.

## Adoption checks

Future implementation work is complete only when it verifies:

- Light and dark theme parity.
- Visible keyboard focus and semantic current/status states.
- Button, input, badge, and surface colors from shared tokens.
- No horizontal overflow at desktop, tablet, and `390px` widths.
- Existing workflows and nonvisual behavior remain unchanged.

