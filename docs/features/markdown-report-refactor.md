# Feature: Markdown Report Refactor

**Status:** Planning  
**Priority:** Medium  
**Estimated Effort:** Days

## Overview
Rework `floor_planner/markdown_report.py` so the generated `<config>.md` report lists every element a project can contain in the right section, with useful data per section, split per floor plan.

## Motivation
The report is meant to be a bill of elements for a project: what is where, how big it is, how many of each. The project has grown well beyond the element set the report was written for (groups, roofs, glass structures, external models, composites, furniture, devices), and the report has not followed:

- Most element types end up in a generic "Other Elements" list that shows only their IDs.
- Some sections show wrong or empty data.
- Composite elements hide their parts.
- All floor plans are mixed in one list.

The report generator also matches exact class names (`grouped['Door']`). Every new element or subclass is therefore silently left out of its section, so the report needs a structure that new elements fit into without edits to the report code.

## Issues Found in the Current Report

Checked against the code and the generated reports in `tests/all_elements`, `examples/landscaping`, `examples/glass_structures`, `examples/roofs`, `tests/play_with_double_doors` and `examples/templates/groups/group_template_demo`.

### 1. Composite elements are not unwound
`composite_glass_door`, `composite_model_window_door_double` and `composite_model_window_double` appear only as `Composite_*` with an ID. Their parts (e.g. `AluFrame` + `SolidGlassDoor`) are never added to `all_elements`, because `__main__._add_element` appends only the composite. The FIXME is already in the code.

### 2. Sections match exact class names
- **Windows:** only `Window`. Missing: `model_window_*` (4 fixed sizes), `model_window_single_any`, `glass_panel`, `glass_slope`.
- **Doors:** only `Door`. Missing: `SolidGlassDoor` (a `Door` subclass), `BalconyDoor`, `WindowDoor`, `WindowDoorDouble`, `SolidDoor1/2`, `GlassDoor`. This is also a FIXME in the code.
- **Invisible elements:** walls with `color: invisible` are split into their own section, but invisible windows and doors are not.

### 3. Wrong or always-empty columns
- **Width:** Garden Paths, Pergolas, Raised Beds, Decks and Garden Houses read `element.width`, which is always `None`. These are surface elements, and the value is in `thickness` (`z_axis_size`).
- **Species and bloom:** Tree and Shrub keep `species` and bloom data on `element.veg2d` (a `CircularVegetation2D`), not on the element itself. Species and bloom columns are always `-`. For example, "Mature Oak" with `species: 'Oak'` in `site_plan_complete.md` shows `-`. Hedge works because it mixes in `VegetationElement` directly.
- **Falsy values:** values are formatted with `if element.x`, so a real `0.0` is shown as `-`.

### 4. Categories with no section ("Other Elements", IDs only)
| Category | Element types |
|---|---|
| Roofs | all 11 roof types incl. gable end walls and glass gable ends |
| Glass structures | `greenhouse`, `glass_panel`, `glass_slope`, `alu_frame` |
| Landscaping | `lawn`, `ground`, `surface`, `rect_pool`, `oval_pool` |
| External furniture and vegetation | all `model_*` furniture, `model_leafy_tree`, `model_leafy_shrub_1` |
| Furniture, appliances, bathroom | storage, beds, appliances, `tv`, bathroom fixtures, tables, chairs, sofas, `fish_tank` |
| Devices | `generic_tank` |
| Electrical and lighting | `power_outlet`, `electrical_cable`, `ground_cable`, lamps, `led_strip`, `switch` (no cable lengths) |
| Room surfaces | `floor`, `ceiling` |
| Annotations | `text_box`, `dimension_arrow`, `line`, `polygon`, `circle` (counted as if they were building elements) |

### 5. Containers
- **Groups:** a `group` appears only as an ID in "Other Elements". It has no section, and its children don't show which group they belong to.
- **Rooms:** they have a detailed section, but the room's `floor` and `ceiling` are missing from "Other Elements in Room". `Room._create_surface_elements` adds them to `all_elements` but not to `room.other_elements`.

### 6. Floor plans are mixed
One report covers all floor plans, with no split and no indication of the floor. Elements from `inherited_elements` are counted once for each floor that includes them, with no way to tell them apart.

### 7. Code structure
- About 340 lines of near-identical table-writing blocks; the excluded type names are kept in a hard-coded list.
- A new element needs code changes in several places, and nothing reports what was missed.

## Design

### User-Facing Changes
- The report has the same file name and location (`<config>.md`), with a new layout (below).
- No YAML changes are required. One optional floor-plan/project key may be added later (see Open Questions).

### Ideas for the New Layout

```markdown
# Floor Plan Elements Report: <project>

## Summary                       ← per category, all floor plans
| Category | Count |             ← e.g. Walls, Windows, Doors, Roofs, Furniture, ...
| Floor plan | Inner area (m²) | ← room areas per floor (labelled rooms, by purpose)

## Floor plan: <title>           ← one block per floor plan (v_anchor shown)

### Structure
#### Walls                      ← ID, length, thickness, corners, room/group
#### Windows                    ← ID, kind (procedural / model), size W×H, model key, corners
#### Doors                      ← ID, kind (hinged / sliding / model), doorway/door width, opens right, corners
#### Roofs                      ← ID, type, footprint X×Z, height/slope, extensions
#### Invisible openings and walls

### Rooms and Groups
#### <room label>               ← as today + floor/ceiling + child list with categories
#### <group label>              ← anchor, template (from_template), children by category

### Interior
#### Furniture                  ← ID, type, size W×L×H, source (procedural / model + key)
#### Appliances and Bathroom
#### Devices

### Installations
#### Electrical                 ← outlets (count per room), cables (length), switches
#### Lighting

### Outdoor
#### Vegetation                 ← ID, species, height, diameter, bloom (incl. model_leafy_*)
#### Hardscape and Surfaces     ← paths, fences, retaining walls, lawn, ground, deck, surface
#### Water                      ← ponds, fountains, pools
#### Garden and Glass Structures

### Composite Elements          ← composite → list of parts

## Annotations                  ← counts only (text boxes, dimension arrows, lines, ...)

## Unclassified                 ← should stay empty; anything here is a missing category
```

Principles:
- **Categories, not classes:** sections are chosen by category. Within a section, the table has a "Type" column, so related element types share one table.
- **Complete:** each element appears exactly once per floor plan. An element inside a room or group is listed in its category section, with its container shown in a column, and is referenced from the room/group block.
- **Annotations:** they are not building elements, so they are only counted.
- **Visible gaps:** an *Unclassified* section, plus a test, catch new elements without a category.

### Technical Changes

1. **Category on the element classes.** Add a class attribute `REPORT_CATEGORY` (e.g. `'wall'`, `'window'`, `'door'`, `'roof'`, `'furniture'`, `'electrical'`, `'vegetation'`, `'annotation'`, ...) on base classes and mixins, so subclasses inherit it. For example, every `Door` subclass and the external door models become `'door'`. Elements without it fall into *Unclassified*.
2. **Row data from the element.** Add an `Element.report_info() -> dict` that returns the column values (size, kind, model key, species, ...). Each class overrides it where needed. This removes the attribute guessing (`hasattr(element, 'width')`) and fixes the `thickness` and `veg2d` problems where the data actually lives. Formatting goes into a single helper that treats `None` as `-` and keeps `0.0`.
3. **Unwind composites.** Either:
   - make `__main__._add_element` register the parts of every `ElementBase.isList()` element in `all_elements` (with a parent reference), or
   - have the report walk `getList()`. The first also helps other consumers of `all_elements`.
4. **Track floor plans and containers.** Collect the elements per floor plan (e.g. `list[(floor_plan_title, v_anchor, elements)]`) instead of one flat list. Record each element's parent container (room/group) when it is created in `Group._create_children` and `Room._create_surface_elements`, and add the floor/ceiling to `room.other_elements`.
5. **Table-driven writer.** Map each category to its section title, columns and order. A single function writes any section, which replaces the hand-written blocks.
6. **Coverage check.** Add a test that instantiates every registry type (as in `tests/all_elements`) and asserts that each one has a `REPORT_CATEGORY` and a `report_info()`.

### Example
No new YAML. Reports to compare before and after: `tests/all_elements/project_main.md`, `examples/landscaping/site_plan_complete.md`, `examples/glass_structures/glass_demo.md`, `examples/roofs/roofs_demo.md`.

## Implementation Plan

### Phase 1: Foundation
- [ ] Add `REPORT_CATEGORY` to the base classes, mixins and element classes; list all registry types and their categories
- [ ] Add `Element.report_info()` with a default (id, type, label) and overrides per category
- [ ] Fix where the data comes from: surface width (`thickness`), Tree/Shrub species and bloom (`veg2d`)

### Phase 2: Collection
- [ ] Register composite parts in `all_elements` with a parent reference
- [ ] Record each element's container (room/group) and floor plan
- [ ] Add floor/ceiling to `room.other_elements`
- [ ] Pass the per-floor-plan structure to the report

### Phase 3: Report Writer
- [ ] Table-driven section writer (category → title, columns, order)
- [ ] New layout: summary, per-floor blocks, rooms and groups, composites, annotations, unclassified
- [ ] Remove the old per-class blocks and the hard-coded exclusion list

### Phase 4: Integration & Testing
- [ ] Coverage test over all registry types
- [ ] Regenerate the reports with `make all` and `make tests` and compare them with the current ones
- [ ] Update `docs/landscaping-guide.md` (report contents), the README "Floor plan reports" item and this document's status

## Testing Strategy
- **Coverage test:** every registry type has a category, and no example or test config produces *Unclassified* entries.
- **Count check:** for each example, the number of elements per category equals the number of YAML definitions, with composites expanded to their parts.
- **Regression:**
  - `tests/all_elements`: all types present.
  - `play_with_double_doors`: composites unwound.
  - `group_template_demo`: groups.
  - `site_plan_complete`: species and width filled in.
  - A multi-floor example: the floor split.
- **Manual:** read one full report for readability, checking table width and order.

## Open Questions
- Should rooms and groups list their children only as references (IDs), or as full rows?
- Should elements from `inherited_elements` be marked as shared, so totals across floors can avoid counting them twice?
- Should the report be configurable (e.g. `project.report: {annotations: false, corners: false}`), or stay fixed?
- Should corner coordinates stay for walls, windows and doors, or move to an optional detail level?
- Should the elements report also include the room-area report that floor plans draw (`report.areas`, grouped by `purpose`), so both use the same numbers?

## References
- `floor_planner/markdown_report.py`: current generator
- `floor_planner/__main__.py`: `_add_element`, how `all_elements` is collected
- `floor_planner/elements/foundation/group.py` (`_create_children`), `room.py` (`_create_surface_elements`)
- `floor_planner/elements/element.py`: `ElementBase.getList()` for composites
- `docs/element-parameters-reference.md`, `docs/landscaping-guide.md`: element types and categories
