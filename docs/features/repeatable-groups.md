# Feature: Repeatable Groups

**Status:** In Progress (Phase 1 done)
**Priority:** Medium
**Estimated Effort:** 1–2 days (about 0.5 day of it is the anchor-resolution refactor in Phase 1)

## Overview

A `group` can repeat itself: its elements are created `repeat_count` times, and the
`repeat_next` section changes the group's variables between one iteration and the next.
`vars` already gives the starting values, so there is no `repeat_begin`.

## Motivation

Plans often contain an element, or a set of elements, laid out at regular steps: lamp
posts along a path, stair treads, trees in an orchard, fence posts, parking bays. Today
each copy is a separate entry in the YAML, so changing the spacing or the number of copies
means editing every one of them. With repetition you define the element once and give the
rule for the next copy.

## Feasibility (summary)

**Feasible, small and local.** The whole feature lives in `Group.create_from_params`
([group.py](../../floor_planner/elements/foundation/group.py)). Nesting works without
extra code: an inner group is created by the outer group's `_create_children`, so it is
created again on every outer iteration, with that iteration's variables.

The analysis turned up one existing limitation that should be fixed first (Phase 1).
A **nested** container's `anchor_point` is resolved in the *parent's* scope. The parent
resolves it before the nested container reads its own `vars`. A top-level container
resolves its anchor in its own scope, so the two behave differently:

```python
# Group._create_children, nested container branch
rel_x, rel_y = resolve_constants(element_def['anchor_point'], merged_vars)  # parent vars only
element_def['anchor_point'] = (rel_x + anchor_point[0], rel_y + anchor_point[1])
```

Checked against the current code:

| Case | Result |
|------|--------|
| top-level group, `vars: {ax: 2}`, `anchor_point: [ax, 0]` | works, anchor `[2.0, 0.0]` |
| the same group nested in another group | `TypeError: can only concatenate str (not "int") to str` |
| nested group redefines a name that also exists outside (`X: 100`, outer `X: 1`) and uses it in `anchor_point` | **silently uses the outer value**: anchor `1.0` (top level: `100.0`) |

The most natural way to write a repeated group is to move the group's own anchor (see
"Pattern A" below). Without the fix, that pattern works at the top level but, once the
group is nested, it either crashes or silently uses the outer value. Nesting is exactly
the case this feature is meant to support.

**Decided:** a container's `anchor_point` is resolved in the container's **own** scope,
for top-level and nested containers alike.

## Design

### Variable scoping (decided)

Repetition relies on the scoping rules below. They are the **current behaviour**, except
for the anchor fix (Phase 1). It was checked against the code, and against the real plans
in `../../rzuty` (`/home/krzys/priv_projects/rzuty`) (37 files, 58 scopes, 77 references to an earlier entry of the same `vars`,
no redefinition of a global name).

1. **Scopes:** global `vars` (project file) → `group`/`room` `vars` → `vars` of nested
   groups/rooms, as deep as the nesting goes. There is no floor-plan-level `vars`.
2. **Inner definitions cover outer ones.** A name defined in a scope covers the same name
   from every outer scope, for everything inside that container (elements, nested
   containers, the container's own `anchor_point`, `repeat_count`, `repeat_next`).
3. **A `vars` section is evaluated in order** (order-dependent, the current behaviour).
   Each entry sees the outer scopes plus the entries above it in the same section:
   * `X: X + 1`: the right-hand `X` is the outer one, because the inner `X` does not
     exist yet;
   * after it, `Y: X` sees the **new**, inner `X`;
   * a name must be defined above the entry that uses it.
4. **Template and instance `vars` are one scope.** The template entries come first, in
   their order, and instance values replace them in place; then come the instance's new
   names. So an instance's `X: X + 1` refers to the `X` **outside the group**, not to the
   template's default `X`, and the template's later entries see the instance's override.
5. **`repeat_next`** (details below) can only change variables of the group's own `vars`
   and is evaluated in order, like `vars`.

Out of scope, separate feature: global `vars` are never evaluated (`b: a + 1` at the
top level stays a string). Variables are substituted as text, so `X ** 2` with `X = -3`
gives `-9`. Typos in expressions are not reported (`X + ofset` becomes a string). See
[Out of scope](#out-of-scope).

### User-facing changes

Two new optional keys on `group`:

| Key | Value | Meaning |
|-----|-------|---------|
| `repeat_count` | non-negative integer, a variable name or an expression (e.g. `5`, `total_elements`, `n - 1`) | how many times the group's elements are created. Evaluated **once**, after `vars`, in the group's scope (global → outer groups → own `vars`). Must evaluate to an integer ≥ 0; `5.0` is accepted, `-1`, `5.5` and `"abc"` raise `ValueError`. **`0` is allowed**: the group creates no elements (see below). Default: 1 (no repetition) |
| `repeat_next` | mapping `var: expression` | applied after each iteration except the last, to compute the next iteration's values. Each expression sees the values of the previous iteration (the first iteration uses the values from `vars`) together with the outer scopes. Entries are applied in order, the same way `vars` entries are, so a later entry sees the new value of an earlier one. Left-hand names must be defined in **this group's own `vars`** |

Iteration by iteration:

```yaml
vars:
  anchor_x: 100
repeat_next:
  anchor_x: anchor_x + 10
repeat_count: 10
```

| Iteration | 1 | 2 | 3 | … | 10 |
|---|---|---|---|---|---|
| `anchor_x` | 100 (from `vars`) | 110 | 120 | … | 190 |

Every iteration creates the group's elements once, with its own value of `anchor_x`.

**`repeat_count: 0` as a condition.** With a count of 0 the group creates no elements and
`repeat_next` is never applied, so a group with `repeat_count: show_lamps` (a variable that
is `0` or `1`) works like an `if`, e.g. for what-if variants of a plan. This is a side
effect of allowing 0, accepted on purpose. With `1`, labels and IDs inside stay exactly
as written: the `_i<N>` suffix is added only when the count is above 1.

`repeat_next` without a `repeat_count` key (or the reverse, a count above 1 and no
`repeat_next`) is allowed, and both print a warning. A `repeat_count` that evaluates to 0
or 1 together with `repeat_next` prints no warning, so the "condition" use above stays
quiet. In the first case `repeat_next` is never applied. In the second case nothing
changes between iterations (there is no loop index), so the N copies lie exactly on top
of each other; only their `_i<N>` suffixes differ. Warnings are printed in the existing
style (`print(f"WARNING: ...")`, as in `runner._warn_unused_layers`) and name the group
(its label or ID).

### Semantics

```
# global_vars = everything visible from outside (global + outer containers), as today
params         = _apply_template(params)                      # once, before anything else
container_vars = resolve(vars)                                # existing behaviour (in order; alias `constants`)
validate repeat_next: a mapping; every key in container_vars  # else ValueError
count          = resolve_repeat_count(repeat_count, {**global_vars, **container_vars})   # once; may be 0; default 1
group_anchor   = resolve(anchor_point, {**global_vars, **container_vars}) + parent_offset # Group's own anchor (also when count is 0)
for i in range(count):
    anchor = resolve(anchor_point, {**global_vars, **container_vars}) + parent_offset   # per iteration
    suffix = iter_suffix + f"_i{i + 1}" if count > 1 else iter_suffix
    children += _create_children(elements, ..., global_vars, container_vars, anchor, ..., iter_suffix=suffix)
    if i < count - 1:
        for name, expr in repeat_next.items():                # in order
            container_vars[name] = resolve(expr, {**global_vars, **container_vars})
            # ValueError if container_vars[name] was a number and the result is not
return Group(child_elements=children, anchor_point=group_anchor, ...)   # ONE Group holding every iteration's children
```

A group without `repeat_count` and `repeat_next` takes exactly one pass through the loop
with an empty suffix, so it behaves as today. No existing config uses the new keys, so
the golden files must not change in Phase 2 either.

Decisions:

1. **One Group object, not N.** The repeated group is one element on the floor plan whose
   `child_elements` holds the children of every iteration. The runner, the floor plan,
   layers and the report keep seeing one container. The group's own `id` and `label`
   stay unique.
2. **`repeat_next` can only change variables defined in this group's own `vars`** (after
   the template is merged). A name that exists only in an outer scope (outer group, room
   or global) or nowhere raises `ValueError`, naming the variable and the group. An inner
   group never changes an outer variable. To step a value that comes from outside, cover
   it locally first: `vars: {x: x}` creates a local `x` that starts with the outer value,
   and `repeat_next` may then step it. The right-hand side may use any visible variable
   (local, outer or global).
3. **Variables that depend on a changed variable are not recomputed.** With
   `vars: {x: 0, x2: x + 1}` and `repeat_next: {x: x + 1}`, `x2` stays `1`.
   Variables are resolved to numbers right away; nothing keeps the expressions. If a value
   must follow `x`, write the expression in the element (`anchor_point: [x + 1, 0]`), or
   recompute it in `repeat_next` after `x`: `repeat_next: {x: x + 1, x2: x + 1}`. The
   entries are applied in order, so `x2` sees the new `x`. Document this (decided: no
   automatic recomputation).
4. **Type check in `repeat_next`.** When a variable that was a number gets a non-numeric
   result, raise `ValueError` naming the variable and the expression. Today a typo such as
   `anchor_x + ofset` quietly resolves to the string `"0.4 + ofset"` and fails much later
   with an unclear error. This check covers only `repeat_next`; the general fix for typos
   in all expressions is the separate feature (see [Out of scope](#out-of-scope)).
5. **Sanity limit.** `repeat_count` above a constant (`MAX_REPEAT_COUNT = 10_000` in
   `constants.py`) raises `ValueError`, to catch a misplaced variable before it runs for
   minutes.

### Two ways to write a repetition

**Pattern A: move the group's anchor** (needs the Phase 1 fix when the group is nested).
The children stay at fixed positions relative to the group, and the group itself moves.

```yaml
- type: group
  label: lamps
  vars:
    lamp_x: 0
    spacing: 4
  repeat_count: 6
  repeat_next:
    lamp_x: lamp_x + spacing
  anchor_point: [lamp_x, 1.5]         # resolved again on every iteration
  elements:
    - type: wall_lamp                 # any element type
      anchor_point: [0, 0]
      label: lamp
```

**Pattern B: move the children** (the form in the request; works today at any depth).
The group's anchor stays fixed and the children use the stepped variable.

```yaml
- type: group
  anchor_point: [2, 0]
  vars:
    anchor_x: start_pos               # start_pos: a global (or outer) variable
    offset: 0.4
    total_elements: 5.0
  repeat_next:
    anchor_x: anchor_x + offset
  repeat_count: total_elements
  elements:
    - type: wall
      anchor_point: [anchor_x, 0]
      ...
```

### Nesting

Nesting needs no special code. The outer loop calls `_create_children` once per iteration,
and that call runs the inner group's `create_from_params` with the outer iteration's
variables as `global_vars`. As a result:

* the inner `vars` (and so the inner starting values) are evaluated again on each outer
  iteration, so the inner counter goes back to its start value for every outer row;
* the inner `repeat_count` can depend on an outer variable, which allows shapes such as a
  triangle;
* the inner group can shadow an outer variable but never changes it (decision 2).

Example: an orchard of 4 rows × 6 trees, with the rows offset in a staggered pattern.

```yaml
- type: group
  label: orchard
  anchor_point: [10, 2]
  vars:
    row_y: 0
    row_shift: 0
  repeat_count: 4
  repeat_next:
    row_y: row_y + 3
    row_shift: 1.5 - row_shift        # alternates 0 / 1.5
  elements:
    - type: group
      label: row
      anchor_point: [row_shift, row_y]   # parent vars: works today
      vars:
        tree_x: 0
      repeat_count: 6
      repeat_next:
        tree_x: tree_x + 3
      elements:
        - type: tree
          anchor_point: [tree_x, 0]
          label: apple
```

Result: one `orchard` group, holding 4 `row` groups (labels `row_i1` … `row_i4`),
each holding 6 trees (labels `apple_i1_i1` … `apple_i4_i6`: row first,
then position in the row; see [IDs and labels](#ids-and-labels-iteration-suffix-decided)).

### Group templates

`_apply_template` runs once, before the loop, so a template and an instance merge into
**one** group with **one** repetition level. Merge rules for the new keys:

| Key | Rule | Reason |
|-----|------|--------|
| `repeat_count` | instance wins (like other scalar keys); without a value in the instance, the template's is used | a template can be "a row of 5 trees" by default |
| `repeat_next` | **merged per variable, like `vars`**: template entries first, instance entries override or are added | an instance changes only the step (`spacing`) or adds a variable, without restating the whole mapping. The current generic "instance replaces the key" rule would drop the template's entries |

Since `repeat_count` and the `repeat_next` expressions are evaluated after the merge,
an instance can change a repetition just by overriding `vars`:

```yaml
group_templates:
  tree_row:
    vars: {tree_x: 0, spacing: 2.0, trees: 5}
    repeat_count: trees
    repeat_next: {tree_x: tree_x + spacing}
    elements:
      - {type: tree, anchor_point: [tree_x, 0]}

floor_plans:
  - elements:
      - {type: group, from_template: tree_row, anchor_point: [0, 0]}                          # 5 trees every 2 m
      - {type: group, from_template: tree_row, anchor_point: [0, 5], vars: {trees: 9, spacing: 1.2}}
```

Two things to document:

* **Elements added by the instance are repeated too.** They are appended to the
  template's elements, and the loop runs over the merged list. This follows from "one
  group", and should be stated explicitly.
* **Two levels of repetition from a template** (for example, repeating a group that
  already repeats) need nesting: an outer repeating group whose element is
  `{type: group, from_template: ...}`. A template cannot repeat itself twice. This
  matches the existing rule that templates do not compose.

The order of `repeat_next` entries matters (sequential evaluation). After a merge the
template's keys come first, in their original order, then the new keys from the instance.
Python dict merge keeps that order, so it is predictable.

### Room

**Decided: no repetition inside `room`. A room that contains `repeat_count` or
`repeat_next` raises `ValueError`, and the message says to wrap the room in a repeating
group.**

Supporting it in Room is *not* simpler. A Room needs exactly 4 `room_edge` walls, so
"repeat the room" has to mean N separate Room objects (each validated, each with its own
area in the report). It cannot mean one Room with 4·N walls. `create_from_params` returns
one element, and the runner and `_create_children` both expect exactly one. A repeating
group around the room already does the job, with no extra code, because the group creates
the room again on every iteration:

```yaml
- type: group
  vars: {box_x: 0}
  repeat_count: 3
  repeat_next: {box_x: box_x + 3.2}
  elements:
    - type: room
      anchor_point: [box_x, 0]   # parent var: works today
      elements: [...]
```

Today `Room.create_from_params` ignores unknown keys. Without the explicit error, a user
who writes `repeat_count` on a room would get one room and no message. (Separately: Room
also ignores `from_template`, because it never calls `_apply_template`. That is out of
scope here.)

## Impact analysis

| Area | Impact | Notes |
|------|--------|-------|
| [group.py](../../floor_planner/elements/foundation/group.py) `create_from_params` | **Main change** | iteration loop, evaluation of `repeat_count` and `repeat_next`, per-iteration anchor |
| [group.py](../../floor_planner/elements/foundation/group.py) `_apply_template` | Small | merge `repeat_next` per variable |
| [group.py](../../floor_planner/elements/foundation/group.py) `_create_children` and `_resolve_params` | **Refactor (Phase 1)** | a nested container resolves its own `anchor_point` in its own scope and adds the parent offset, instead of having the parent resolve it |
| [room.py](../../floor_planner/elements/foundation/room.py) | Small | follows the Phase 1 refactor (same anchor path); rejects `repeat_*`; passes the iteration suffix on to its children and floor/ceiling |
| [group.py](../../floor_planner/elements/foundation/group.py) `_create_children` | Small | appends the iteration suffix to `label` / `id` and passes it to nested containers (see [IDs and labels](#ids-and-labels-iteration-suffix-decided)) |
| [variables.py](../../floor_planner/variables.py) | Small | helper `resolve_repeat_count(value, vars) -> int` that validates |
| [runner.py](../../floor_planner/runner.py) | **None** | a top-level repeated group is still a single `create_from_params` call; `reusable_elements` / `inherited_elements` and templates loaded from files work unchanged |
| [floor_plan.py](../../floor_planner/floor_plan.py), [layers.py](../../floor_planner/layers.py) | None | every child is added with `floor_plan.add_element` as today, each with its own layer; containers stay layerless |
| `embedded_dimensions` | None | the flag is passed down on every iteration; dimension arrows are repeated with the other elements (or skipped everywhere) |
| [markdown_report.py](../../floor_planner/markdown_report.py) | None | lists every created element; repeated rooms (wrapped in a group) appear as separate rooms with their own areas |
| 3D export / wall openings | None | openings are matched by geometry, not by ID; repeated walls and doors are exported like hand-written ones |
| Element counter / z-order | None | each created element increments `Element._element_counter`, so z-order stays unique |
| Performance | Negligible | one `deepcopy` per element definition per iteration; protected by `MAX_REPEAT_COUNT` |

### IDs and labels: iteration suffix (decided)

Without changes, an explicit `id:` inside a repeated group gives N elements with the same
ID (`elements_by_id` silently keeps the last one; the report and the drawn IDs show
duplicates), and every copy shows the same label.

**Rule:** every explicit `id` and every `label` of an element created inside a repetition
whose `repeat_count` is **above 1** gets `_i<N>` appended. `N` is the iteration number of the repeating group, counted
from **1**, written as a whole decimal number (`1`, `2`, … `10`, never `1.0`).

| Definition inside the repetition | Iteration 1 | Iteration 2 |
|---|---|---|
| `label: lamp` | label `lamp_i1` | label `lamp_i2` |
| `id: post` | id `post_i1` | id `post_i2` |
| `label: lamp` without `id` | id generated from the suffixed label: `lamp_i1_1` | `lamp_i2_1` |
| no `label`, no `id` | no label; generated id `<type>_<n>` as today (already unique) | same |

In `lamp_i1_1`, the trailing `_1` is the existing ID counter, not another iteration.
This is accepted as is, so ID generation does not change.

Details:

* **Scope:** the suffix applies to everything created during an iteration, at any depth:
  elements, nested groups and rooms (their own `label`/`id`), elements from the template,
  and room floors/ceilings. It is applied after `{var}` substitution in the label.
* **The repeating group itself** is created once and is not part of its own iterations,
  so its own `label`/`id` get no suffix (unless an outer repetition contains it).
* **Nested repetitions** append one suffix per repeating ancestor, outer first: a tree in
  row 2, position 3 of the orchard is `apple_i2_i3`. Groups between them without
  `repeat_count`, or with a count of 1, add nothing.
* **When it applies:** only when the group's `repeat_count` evaluates to more than 1.
  With a count of 1 (or no `repeat_count`) labels and IDs stay exactly as written, so a
  `0`/`1` count used as an `if` does not change them. A variable count that changes from
  1 to 2 adds the suffix to the labels: accepted.
* **Separator:** `_` between the original text and `i<N>` (`lamp` → `lamp_i1`).
* **Visible effect:** labels drawn on the plan, room labels in the area report and the
  Markdown report show the suffix. For a `line` element the label is the text drawn along
  the line, so that text gets the suffix too.
* With unique suffixes, explicit IDs inside a repetition cannot collide across
  iterations, so no duplicate-ID check is needed. Duplicates written twice in the *same*
  iteration (or anywhere outside repetitions) stay as today: out of scope.

**Implementation:** `create_from_params` and `_create_children` get one more keyword,
`iter_suffix: str = ""` (like `parent_offset`). A repeating group passes
`iter_suffix + f"_i{i + 1}"` to the children of iteration `i` when its count is above 1,
and `iter_suffix` unchanged otherwise.

Who adds the suffix, so that it is never added twice:

* **`_create_children` adds it to every element definition it creates**, regular elements
  and nested containers alike. It is appended to `label` and `id` only when the key is
  present and not `None`. For regular elements this happens after
  `resolve_element_params` (so after `{var}` substitution). For a nested container it is
  appended to `label` / `id` in the definition before `create_from_params` is called.
* **A container never adds the suffix to its own `label` / `id`.** It only passes the
  suffix it received (plus its own `_i<N>`, if it repeats) on to its children.
* `Room.create_from_params` passes the suffix it received to `_create_children` and to
  `_create_surface_elements` (floor/ceiling `label` / `id`). A room has no own iterations.
* The top-level call from `runner._add_element` uses the default `""`.

### Phase 1 refactor: per-container anchor resolution (details)

Current flow: the parent resolves the nested anchor with its own variables, adds its
anchor, and passes absolute numbers to the child's `create_from_params`.

Proposed flow: the parent passes the raw `anchor_point` plus `parent_offset=anchor_point`
(a new keyword argument of `create_from_params`, default `(0, 0)`). The child resolves the
anchor in **its own** scope (`global + parent + own vars`) and adds `parent_offset`.

* Top-level containers already behave this way (offset `(0, 0)`), so after the change
  nested and top-level containers behave the same.
* Repetition needs it anyway: the anchor must be resolved again on every iteration, after
  `repeat_next`, so it has to happen inside the container.
* **Behaviour change (intended):** a nested container that redefines a parent variable
  *and* uses it in its own `anchor_point` now gets its own value instead of the parent's.
  A scan of `../../rzuty` (`/home/krzys/priv_projects/rzuty`) found no redefinition of a global name, so no real plan should
  change. The golden PNG tests (`make check`) and a run of the `../../rzuty` (`/home/krzys/priv_projects/rzuty`) plans confirm it.
* `Room.create_from_params` takes the same keyword argument and goes through the same
  `_resolve_params` path.

## Implementation Plan

### Phase 1: Anchor-resolution refactor (no new feature yet)
- [x] Add a `parent_offset: tuple = (0, 0)` keyword to `Group.create_from_params` and `Room.create_from_params`
- [x] `_resolve_params` resolves `anchor_point` in the container's scope and adds `parent_offset`
- [x] `_create_children`: stop resolving and translating the nested anchor; pass `parent_offset=anchor_point`
- [x] Unit tests: a nested group/room whose `anchor_point` uses its own `vars` (raises `TypeError` today); a nested group that redefines an outer name and uses it in `anchor_point` (uses the outer value today) — in `tests/unit/test_container_anchor_scope.py`
- [x] Unit tests that pin the existing scoping rules (rule 3 in [Variable scoping](#variable-scoping-decided)): `X: X + 1` uses the outer `X`, a later `Y: X` uses the inner one, inner names cover outer names in elements and nested containers
- [x] `make check`: golden images must not change
- [x] Real-plan regression (see [Real-plan regression check](#real-plan-regression-check)): PNGs of the `../../rzuty` plans identical before and after
- [x] Also fixed: a nested container **without** `anchor_point` was placed at `(0, 0)`, ignoring the parent's anchor. It now assumes `anchor_point: [0, 0]` relative to the parent: an element at `[1, 0]` in such a container, inside a parent at `[5, 0]`, is placed at `(6, 0)`. No config in the repo or in `../../rzuty` has such a container, so no output changes
- [x] An `anchor_point` that cannot be resolved now raises `ValueError` naming the container (was `TypeError` for nested containers)

### Phase 2: Repetition core
- [ ] `variables.resolve_repeat_count()`: evaluate, check that the value is a whole number, ≥ 0 and ≤ `MAX_REPEAT_COUNT`; clear error messages
- [ ] `Group.create_from_params`: loop over iterations; anchor resolved per iteration; `repeat_next` applied in order after every iteration except the last
- [ ] `MAX_REPEAT_COUNT = 10_000` in `constants.py` (limit per group, not per total)
- [ ] Check that `repeat_next` is a mapping and that its keys are defined in the group's own `vars` (or `constants`) (an outer-only or undefined name raises `ValueError`); check that numeric variables stay numeric
- [ ] Warnings: `repeat_next` without a `repeat_count` key; `repeat_count` > 1 without `repeat_next` (copies on top of each other); no warning for a count of 0 or 1
- [ ] `_apply_template`: merge `repeat_next` per variable; `repeat_count` instance-wins (existing generic rule)
- [ ] `Room.create_from_params`: reject `repeat_count` / `repeat_next` with a message pointing to a wrapping group
- [ ] `make check` and the real-plan regression check: nothing changes (no existing config uses the new keys)
- [ ] Iteration suffix: `iter_suffix` keyword on `create_from_params` / `_create_children` (Group and Room); `_i<N>` (N from 1, whole number) appended to `label` and explicit `id` only when the count is above 1; nested repetitions append outer first; Room floor/ceiling included

### Phase 3: Tests, example, docs
- [ ] Unit tests in `tests/unit/test_repeatable_groups.py` (in the style of `test_embedded_dimensions.py`, with a collecting floor plan stand-in)
- [ ] Example `examples/templates/groups/repeat_demo/project_main.yml`: lamp row (pattern A), stairs (pattern B), staggered orchard (nested), tree-row template with two instances, rooms repeated through a wrapping group
- [ ] Add the example to `SCENES` in `tests/conftest.py`, generate its golden PNG with `--update-golden`, review it
- [ ] Update the `Group` docstring, the README (feature list), `docs/element-parameters-reference.md` (group keys)
- [ ] Set this document's status to Complete; update the list in [README.md](README.md)

## Testing Strategy

Unit tests (no rendering):
- `repeat_count: 3` with one element → 3 children; anchors stepped by `repeat_next`
- `repeat_count` as a variable, as an expression, as the float `5.0`; errors for `-1`, `2.5`, a string, above the limit
- `repeat_count: 0` → no children, `repeat_next` not evaluated (a `repeat_next` that would fail is not reached), the Group itself still created with its anchor; `repeat_count` from a variable `0`/`1` works as a condition, without warnings
- recomputing a dependent variable in `repeat_next` (`{x: x + 1, x2: x + 1}`) → `x2` follows `x`
- `repeat_next` applied in order (a later entry sees the new value of an earlier one); not applied after the last iteration
- the `anchor_x: 100`, `+ 10`, `repeat_count: 10` example → values 100, 110, …, 190
- `repeat_next` on an outer-only variable → `ValueError`; on an undefined name → `ValueError`; after `vars: {x: x}` stepping it works and the outer `x` is unchanged
- a typo in a `repeat_next` expression → `ValueError` naming the variable
- the dependent variable (`x2: x + 1`) is not recomputed (documents the decision)
- pattern A: the group's own `anchor_point` moves per iteration, at the top level **and nested**
- nesting: 3 × 4 grid → 12 leaves, correct coordinates; inner start values reset on every outer iteration; inner `repeat_count` depending on an outer variable; inner shadowing does not change the outer variable
- templates: template repetition used as is; instance overrides `vars` → count and step change; instance `repeat_next` merged per variable; instance-added elements are repeated
- room: `repeat_count` on a room → `ValueError`; a room inside a repeating group → N rooms, each validated
- `embedded_dimensions: false` with repetition → no arrows in any iteration
- iteration suffix: `label: lamp` → `lamp_i1` … `lamp_iN`; `id: post` → `post_i1` …; N is `1`, not `1.0`; no label and no id → no label, generated id unchanged; the repeating group's own label has no suffix; nested repetitions → `apple_i2_i3` (outer first); a non-repeating group in between adds nothing; `repeat_count: 1` adds no suffix (also as a nested level: `repeat_count: 1` outside a repetition of 3 gives `apple_i1` … `apple_i3`); a room inside a repetition → room label and its walls/floor labels suffixed; all IDs in `elements_by_id` unique

Regression: `make check` after every phase. Phases 1 and 2 must not change any golden
file; only Phase 3 adds a new one (the new example).

### Real-plan regression check

The real plans live outside the repository, in `../../rzuty`
(`/home/krzys/priv_projects/rzuty`). The plans to run are the files with a
`floor_plans:` section: `dom_projekt/dom_projekt3.yml`, `dom_i_dzialka/dom_i_dzialka.yml`,
`dzialka/dzialka_proj.yml`, `tests/tests.yml`, `tests/room_tests.yml`,
`tests/labels.yml`.

**Never write into that folder:** running a plan writes its outputs next to it. Instead:

1. Copy `/home/krzys/priv_projects/rzuty` into the scratchpad (baseline copy) and run
   each plan there with the code **before** the change
   (`.venv/bin/python -m floor_planner -c <copy>/<plan>.yml`).
2. Make a second copy and run the plans there with the code **after** the change.
3. Compare the PNGs of the two copies pixel by pixel (e.g. with Pillow,
   `ImageChops.difference(...).getbbox() is None`). Any difference is reported to the
   user, not accepted silently.

If a plan already fails on the baseline, report it and leave it out of the comparison.

Manual: open the new example PNG and glTF and check the row, the stairs, the orchard and
the tree rows.

## Open Questions

None at the moment.

### Decided

- Scoping: the current, order-dependent behaviour stays (see [Variable scoping](#variable-scoping-decided)).
- A nested container's `anchor_point` is resolved in its own scope (Phase 1).
- `repeat_next` is evaluated in order; it sees the previous iteration's values and can
  only change the group's own `vars`.
- Labels and explicit IDs inside a repetition get `_i<N>` appended (N from 1, whole
  number; outer repetition first when nested), only when the count is above 1. See [IDs and labels](#ids-and-labels-iteration-suffix-decided).
- No implicit loop index: no built-in variable such as `repeat_index` that can be used
  in expressions. A counter, if needed, is an ordinary variable: `vars: {i: 1}`,
  `repeat_next: {i: i + 1}`. The iteration number appears only in the `_i<N>` suffix.
- `repeat_count: 0` is allowed: the group creates no elements. A count from a `0`/`1`
  variable works as an `if` (an accepted side effect).
- `{var}` substitution in strings is unchanged: a number still prints as `1.0`. Only the
  `_i<N>` suffix prints whole numbers.
- No per-iteration exclusions (e.g. "only on the first copy", "skip iteration 3").
- `vars` that depend on a variable changed by `repeat_next` are not recomputed
  automatically; the user recomputes them in `repeat_next` if needed.
- No repetition inside `room`: `repeat_count` or `repeat_next` on a room raises
  `ValueError`. Rooms are repeated by wrapping them in a repeating group.
- Whether the iterations are stored as one Group object or one per iteration is an
  internal detail and does not matter to the user. The plan uses one Group (decision 1),
  the simpler option.

## Out of scope

Problems with variable resolution found during the analysis. They are to be handled as a
separate feature, which does not block this one:

1. **Global `vars` are never evaluated.** `b: a + 1` in the project file stays the string
   `"a + 1"` and fails later with "Issue with combining variables". The top-level scope
   should follow the same in-order rules as group and room `vars`.
2. **Text substitution without parentheses.** `resolve_constants` replaces names with
   their values as text, so `X ** 2` with `X = -3` evaluates `-3.0 ** 2 = -9`. Evaluating
   with a dictionary of names fixes this.
3. **Typos are not reported.** An expression that cannot be evaluated is returned as a
   string (`X + ofset` → `"X + ofset"`) and fails much later, far from its cause.
4. **Only some parameters accept variables.** `resolve_element_params` resolves a fixed
   list of numeric fields; others (e.g. `hinges_point`) cannot use variables.

## References

- [group.py](../../floor_planner/elements/foundation/group.py): `create_from_params`, `_create_children`, `_apply_template`, `_resolve_params`
- [room.py](../../floor_planner/elements/foundation/room.py): `create_from_params`
- [variables.py](../../floor_planner/variables.py): `resolve_constants`, `resolve_element_params`
- [runner.py](../../floor_planner/runner.py): `_add_element`, template registration
- [examples/templates/groups/group_template_demo/project_main.yml](../../examples/templates/groups/group_template_demo/project_main.yml): existing template usage
- [tests/unit/test_embedded_dimensions.py](../../tests/unit/test_embedded_dimensions.py): pattern for container unit tests
