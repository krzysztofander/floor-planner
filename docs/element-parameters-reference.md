# Floor Planner Element Parameters Reference

Parameter reference for the YAML element types of floor_planner, except landscaping elements (vegetation, hardscape, water features, garden structures), which are described in [landscaping-guide.md](landscaping-guide.md).

## Table of Contents
1. [Basic Elements](#basic-elements)
2. [Doors](#doors)
3. [Electricity](#electricity)
4. [Lighting](#lighting)
5. [Info/Annotations](#infoannotations)
6. [Multipurpose/Shapes](#multipurposeshapes)
7. [Rooms](#rooms)
8. [Room Surfaces (Floor & Ceiling)](#room-surfaces-floor--ceiling)
9. [Groups](#groups)
10. [Group Templates](#group-templates)
11. [Roofs](#roofs)
12. [Furniture - Storage](#furniture---storage)
13. [Furniture - Beds](#furniture---beds)
14. [Furniture - Appliances](#furniture---appliances)
15. [Furniture - Bathroom](#furniture---bathroom)
16. [Furniture - General](#furniture---general)
17. [Furniture - Decorations](#furniture---decorations)
18. [Devices](#devices)
19. [External Models - Common](#external-models---common)
20. [External Models - Windows and Doors](#external-models---windows-and-doors)
21. [External Models - Furniture](#external-models---furniture)
22. [External Models - Vegetation](#external-models---vegetation)
23. [Composite Elements](#composite-elements)
24. [Glass Structures](#glass-structures)
25. [Common Parameter Notes](#common-parameter-notes)
26. [Vertical Positioning (v_anchor and height)](#vertical-positioning-v_anchor-and-height)
27. [3D Visualization Parameters](#3d-visualization-parameters)
28. [Floor Plan v_anchor (3D Elevation)](#floor-plan-v_anchor-3d-elevation)

---

## Basic Elements

### WallND
Straight wall without dimensions. For corners of acute or obtuse angles, consider `Polygon` class.

**YAML type:** `wallnd`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the wall (in meters)
- `thickness`: float - thickness of the wall (in meters); walls thinner than 0.01 m are drawn 0.01 m thick and semi-transparent in 2D
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the wall; measured between X-axis and the wall in positive direction (counterclockwise); initial wall is rotated around anchor point
- `color`: str = 'black' - color to use for drawing the wall
- `label`: str | None = None - optional label for the element
- `room_edge`: bool = False - if True, this wall forms the boundary of a room (used for room validation and calculations)

### Wall
Wall with dimensions. Same as WallND, but includes a dimension arrow from the anchor point to the end of the wall when dimensions option is enabled.

**YAML type:** `wall`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the wall (in meters)
- `thickness`: float - thickness of the wall (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the wall
- `color`: str = 'black' - color to use for drawing the wall
- `label`: str | None = None - optional label for the element
- `room_edge`: bool = False - if True, this wall forms the boundary of a room

### Window
Window in a wall.

**YAML type:** `window`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the window (in meters)
- `overall_thickness`: float - total thickness of the window (in meters); must be greater than `2 * single_line_thickness`, otherwise a `ValueError` is raised
- `single_line_thickness`: float = -1 - thickness of a single outer line forming window (in meters); defaults to `overall_thickness / 10` if ≤ 0
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the window
- `color`: str = 'black' - color to use for drawing the window
- `label`: str | None = None - optional label for the element

---

## Doors

### Door
Single door, either hinged (swinging) or sliding.

**YAML type:** `door`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the door frame corner that is on the same side with hinges and is on the side where the door opens (given `to_the_right` is set to `False`, else it is on the opposite side)
- `doorway_width`: float - width of the doorway (in meters), i.e. width of the door itself plus the width of both sides of the door frame
- `door_width`: float - width of the door itself (in meters)
- `thickness`: float - thickness of the door (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the doorway
- `to_the_right`: bool = False - binary indicator whether the door opens to the right if someone looks at it from the hinges point along the doorway; for `door_type: sliding` it sets the slide direction (True = towards +X of the doorway, False = towards -X)
- `color`: str = 'black' - color to use for drawing the door
- `hinges_point`: float = 0.95 - relative position of the hinges across the door thickness (0.0 = start, 1.0 = end, 0.5 = middle); for a sliding door it sets the depth of the panel within the thickness
- `opening_outside`: bool = False - if True, door opens outward (hinge/panel depth becomes `1 - hinges_point`); if False, door opens inward
- `label`: str | None = None - optional label for the element
- `door_type`: str = 'hinged' - `'hinged'` (swinging door with opening arc; 3D rotation animation) or `'sliding'` (2D: closed panel, dashed open position and slide-direction arrow; 3D slide animation by `door_width`); any other value raises `ValueError`

---

## Electricity

### PowerOutlet
Power outlet.

**YAML type:** `power_outlet`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the center of the segment shared with a wall is anchor point
- `length`: float - length of the power outlet (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the power outlet
- `waterproof`: bool = False - indicator whether the power outlet is waterproof
- `high_voltage`: bool = False - indicator whether the power outlet has 380-400V instead of regular 220-230V
- `low_current`: bool = False - indicator whether the power outlet is designed for low-current appliances (e.g., Wi-Fi router); also can be used for Ethernet outlets
- `line_width`: float = 0.5 - width of lines for matplotlib
- `color`: str = 'black' - color to use for drawing the power outlet
- `label`: str | None = None - optional label for the element

### ElectricalCable
Electrical cable for direct power supply without any outlets.

**YAML type:** `electrical_cable`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the center of the segment shared with a wall is anchor point
- `symbol_length`: float - length of the symbol, not of the real cable
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the electrical cable
- `n_arcs`: int = 4 - number of turns representing a curved cable
- `line_width`: float = 0.5 - width of lines for matplotlib
- `color`: str = 'black' - color to use for drawing the cable
- `label`: str | None = None - optional label for the element

### GroundCable
Ground (buried) electrical cable drawn as a straight line between two points. Subclass of `Line`.

**YAML type:** `ground_cable`

**Parameters:**
- `first_point`: tuple[float, float] - coordinates of the first end (in meters)
- `second_point`: tuple[float, float] - coordinates of the second end (in meters)
- `width`: float = 1.0 - width of the line for matplotlib
- `style`: str = 'solid' - type of line ('solid', 'dashed', 'dotted', or 'dash_dot')
- `color`: str = 'red' - color to use for drawing the cable
- `label`: str | None = None - optional label for the element
- `print_len`: bool | None = None - if True and `label` is set, the cable length is appended to the label

---

## Lighting

### CeilingLamp
Ceiling lamp represented by a circle and a cross inside.

**YAML type:** `ceiling_lamp`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; here, it is the center of the symbol
- `symbol_diameter`: float - diameter of the symbol (in meters)
- `line_width`: float = 0.5 - width of lines for matplotlib
- `color`: str = 'black' - color to use for drawing the lamp
- `label`: str | None = None - optional label for the element

### WallLamp
Wall lamp (e.g., sconce).

**YAML type:** `wall_lamp`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; here, it is the center of wall connection segment
- `symbol_diameter`: float - diameter of the symbol (in meters)
- `orientation_angle`: float = 0.0 - angle (in degrees) that specifies orientation of the lamp
- `stub_relative_depth`: float = 0.3 - ratio of stub depth to its width
- `line_width`: float = 0.5 - width of lines for matplotlib
- `color`: str = 'black' - color to use for drawing the lamp
- `label`: str | None = None - optional label for the element

### LEDStrip
LED strip.

**YAML type:** `led_strip`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; here, it is the bottom left corner
- `length`: float - length of the strip (in meters)
- `width`: float - width of the strip (in meters)
- `orientation_angle`: float = 0.0 - angle (in degrees) that specifies orientation of the strip
- `line_width`: float = 0.5 - width of lines for matplotlib
- `color`: str = 'black' - color to use for drawing the strip
- `label`: str | None = None - optional label for the element

### Switch
Lighting switch.

**YAML type:** `switch`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the point shared with a wall is the anchor point
- `symbol_length`: float - length of the symbol, not of the real switch
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the switch
- `two_key`: bool = False - binary indicator whether the switch has two keys
- `pass_through`: bool = False - binary indicator whether there are other switches controlling the same lamp (or lamps)
- `line_width`: float = 0.5 - width of lines for matplotlib
- `color`: str = 'black' - color to use for drawing the switch
- `label`: str | None = None - optional label for the element

---

## Info/Annotations

### DimensionArrow
Dimension arrow.

**YAML type:** `dimension_arrow`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the leftmost point is anchor point if `orientation_angle == 0`
- `length`: float - length of the arrow (in meters); this value (rounded to 3 decimals) is also placed in the annotation
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the arrow
- `width`: float = 0.01 - width of lines (in meters before scaling)
- `tip_length`: float = 0.1 - length of single arrow tip (in meters before scaling)
- `font_size`: int = 10 - font size
- `annotate_above`: bool = False - if set to True, annotation is placed above the arrow (prior to its rotation)
- `color`: str = 'black' - color to use for drawing the arrow and its annotation
- `label`: str | None = None - optional label for the element

### TextBox
Text box.

**YAML type:** `text_box`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the center of a text box is its anchor point
- `lines`: list[str] - text lines to be printed
- `font_size`: int = 10 - font size
- `color`: str = 'black' - color to use for drawing the text
- `transparency`: float = 0.75 - transparency (alpha) of the bounding box
- `edgecolor`: str = 'black' - edge color of the bounding box
- `label`: str | None = None - optional label for the element

---

## Multipurpose/Shapes

### Line
Line (solid, dashed, or dotted).

**YAML type:** `line`

**Parameters:**
- `first_point`: tuple[float, float] - coordinates of the first end (in meters)
- `second_point`: tuple[float, float] - coordinates of the second end (in meters)
- `width`: float = 0.5 - width of the line for matplotlib
- `style`: str = 'solid' - type of line ('solid', 'dashed', 'dotted', or 'dash_dot')
- `color`: str = 'black' - color to use for drawing the line
- `label`: str | None = None - optional label, drawn along the line (font size 10) when a label color is configured for `Line`
- `append_len`: bool = False - if True, the line length is added to the rendered label

### Polygon
Polygon. In particular, it can be used for wall corners of acute or obtuse angles.

**YAML type:** `polygon`

**Parameters:**
- `vertices`: list[tuple[float, float]] - list of vertices coordinates (in meters)
- `line_width`: float = 0.1 - width of lines for matplotlib
- `color`: str = 'black' - fill and edge color of the polygon
- `label`: str | None = None - optional label for the element

### Circle
Filled circle.

**YAML type:** `circle`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of the center (in meters)
- `radius`: float - radius of the circle (in meters)
- `color`: str = 'black' - fill and edge color of the circle
- `label`: str | None = None - optional label for the element

---

## Rooms

### Room
Room defined by 4 walls forming a rectangle, with optional other elements. A room is a specialised `Group`: it needs exactly 4 walls (`wall` / `wallnd`) with `room_edge: true` – 2 horizontal (rotation 0 or 180) and 2 vertical (rotation 90 or 270) – whose outer corners form an axis-aligned rectangle. Any number of additional elements (windows, doors, furniture, nested groups, `floor` / `ceiling`) may be added. Inner/outer dimensions, areas and corners are computed from the room-edge walls.

**YAML type:** `room`

**Parameters:**
- `elements`: list - child element definitions (required, must not be empty); child coordinates are relative to `anchor_point`
- `anchor_point`: tuple[float, float] = (0, 0) - room reference point; may use variable expressions
- `color`: str = 'black' - default color for child `wall` / `wallnd` elements that have no explicit `color`
- `label`: str | None = None - optional label; drawn at the inner bottom-left corner when `Room.label_color` is set, and required for the room to be listed in the floor plan `report`
- `purpose`: str | None = None - optional purpose (e.g. living space, outdoor, storage); the `report` area list groups labeled rooms by `purpose` under the heading "`<purpose>` room areas:" (rooms without a purpose go under "Other"), each group with its own total
- `vars`: dict = {} - scoped variables (alias: `constants`), same rules as for [Group](#group)

**Display options** (`default_options.Room` or per-floor-plan `options.Room`):
- `label_color`: str - color of the room label
- `dimensions`: bool = False - draw inner horizontal and vertical dimension arrows
- `inner_area`: bool = False - show inner area (m²) in the room centre
- `inner_corner_label_color`: str - color for inner corner coordinate labels
- `outer_corner_label_color`: str - color for outer corner coordinate labels

**Floor plan report** (`report` key of a floor plan): `anchor_point`, `areas` (list labeled room inner areas), `total_area` (sum per purpose group), `notes` (list of strings), `fontsize` = 11.

**Note:** `from_template` is not supported for `room` (only `group` applies templates).

---

## Room Surfaces (Floor & Ceiling)

Floor and ceiling are special child elements of a `room`. They are **3D-only** — invisible in 2D plans — and their `anchor_point` and `size` are automatically derived from the room's internal corners. Do **not** specify `anchor_point` or `size` in YAML; the room injects these automatically. They are only recognised directly inside a `room`'s `elements` list.

### Floor
Room floor plane. Spans the full interior of the room at floor level.

**YAML type:** `floor`

**Parameters (all optional):**
- `v_anchor`: float | None = None — override vertical anchor; default is `VertInfoFloors` = 0.0 m
- `height`: float | None = None — override slab thickness; default is 0.02 m
- `label`: str | None = None — optional label
- `id`: str | None = None — optional explicit ID
- `texture_scale`: float | None = None — texture tiling scale in meters (3D export)

**Example:**
```yaml
- type: room
  anchor_point: [0, 0]
  color: black
  elements:
    - type: wall
      ...
    - type: floor
    - type: floor          # with overrides
      v_anchor: 0.0
      height: 0.05
```

### Ceiling
Room ceiling plane. Spans the full interior of the room at ceiling level.

**YAML type:** `ceiling`

**Parameters (all optional):**
- `v_anchor`: float | None = None — override vertical anchor; default is `VertInfoCeilingSurface` = 2.69 m
- `height`: float | None = None — override slab thickness; default is 0.01 m
- `label`: str | None = None — optional label
- `id`: str | None = None — optional explicit ID
- `texture_scale`: float | None = None — texture tiling scale in meters (3D export)

**Example:**
```yaml
- type: room
  anchor_point: [0, 0]
  color: black
  elements:
    - type: wall
      ...
    - type: ceiling
    - type: ceiling        # with overrides
      v_anchor: 3.0
      height: 0.02
```

**Note:** A room may contain both a `floor` and a `ceiling` entry simultaneously. Floor color is fixed (`brown`), ceiling color is fixed (`white`).

---

## Groups

### Group

A lightweight container that positions child elements relative to a shared `anchor_point`.  Unlike `Room`, a `Group` has no structural requirements — it does not need walls and imposes no validation on its contents.  Groups can be nested recursively: a child element of type `group` (or `room`) is fully resolved before it is added to the parent.

**YAML type:** `group`

**Parameters:**
- `anchor_point`: tuple[float, float] = (0, 0) — origin for all child coordinates; child `anchor_point`, `first_point` and `second_point` values are expressed relative to this point
- `color`: str = 'black' — default wall color inherited by child `wall` / `wallnd` elements that have no explicit `color`
- `label`: str | None = None — optional informational label
- `vars`: dict = {} — scoped variables (alias: `constants`); evaluated in order after global vars; each can reference global vars, parent-container vars and previously defined vars of this group using arithmetic expressions; nested containers inherit them
- `elements`: list = [] — child element definitions; each must have a `type` key
- `from_template`: str | None = None — name of a registered group template; see [Group Templates](#group-templates)

**Merge rules when `from_template` is used:**
- template `vars` supply defaults; instance `vars` override them
- template `elements` come first; instance `elements` are appended after
- any other instance key (`anchor_point`, `color`, `label`, …) overrides the template value

**Example — standalone group:**
```yaml
- type: group
  label: "bathroom"
  anchor_point: [5, 2]
  vars:
    w: 2.5
    h: 2.0
    t: 0.15
  elements:
    - type: wall
      anchor_point: [0, 0]
      length: w
      thickness: t
      orientation_angle: 0
      color: black
    # ... more elements
```

**Example — nested groups:**
```yaml
- type: group
  label: "apartment"
  anchor_point: [0, 0]
  elements:
    - type: group
      label: "kitchen corner"
      anchor_point: [3, 0]   # relative to parent anchor
      elements:
        - type: text_box
          anchor_point: [0, 0]
          lines: ["kitchen"]
          font_size: 10
          color: gray
          edgecolor: none
```

**Note:** `Group` itself draws nothing — only its children are rendered. A `group` can contain a `room` as a child. String fields of children (e.g. `color`, `label`) can reference string vars with `{var_name}`.

---

## Group Templates

Group templates are reusable group blueprints.  They are **never instantiated directly** — they only exist to be referenced by `group` instances via `from_template`.

### Defining templates

Templates can be defined in two places:
- the top-level `group_templates` key of the main config;
- a `group_templates` key inside an external file referenced from `reusable_elements` (dict format with optional `group_templates` and `elements` keys). On a name collision, a file template overrides the main-config one.

Templates cannot be defined inside element lists.

```yaml
group_templates:

  small_office:
    vars:
      room_w: 3.5
      room_h: 2.8
      wall_t: 0.15
      window_w: 1.2
    elements:
      - type: wall
        anchor_point: [0, 0]
        length: room_w
        thickness: wall_t
        orientation_angle: 0
        color: black
      # ... remaining walls, windows, doors
```

External reusable file (`reusable_elements: {offices: "offices.yml"}`):
```yaml
group_templates:
  small_office: { ... }
elements:            # optional; used via inherited_elements: [offices]
  - type: group
    from_template: small_office
```

Templates support the same keys as a `group` (`vars`, `elements`, `anchor_point`, `color`, `label`).  A template **must not** contain `from_template` itself — template composition is not supported (raises an error). Referencing an unknown template name also raises an error.

### Using a template

Reference a template with `from_template` in a `group` element (`room` does not support it):

```yaml
- type: group
  from_template: small_office      # inherit vars and elements
  anchor_point: [0, 0]             # overrides template anchor_point (if any)
  vars:
    room_w: 5                      # override one template var
    wall_t: 0.2                    # override another
  elements:
    - type: text_box               # APPENDED after template elements
      anchor_point: [0.3, 0.3]
      lines: ["office A"]
      font_size: 9
      color: gray
      edgecolor: none
```

**Merge rules (summary):**

| Key | Result |
|-----|--------|
| `vars` | template values are defaults; instance values override |
| `elements` | template list first, instance list appended |
| any other key (`anchor_point`, `color`, `label`, …) | instance wins if present, else template |

**Multiple instances from the same template:**

```yaml
group_templates:
  bedroom:
    vars: {w: 3, h: 3.5, t: 0.15}
    elements: [ ... ]

floor_plans:
  - elements:
      - type: group
        from_template: bedroom
        anchor_point: [0, 0]
        label: "bedroom 1"

      - type: group
        from_template: bedroom
        anchor_point: [4, 0]
        label: "bedroom 2"
        vars:
          w: 4          # wider variant
```

**Note:** Templates are registered once per config load and are available to all groups (including nested ones) in all floor plans and reusable elements of that config file.

---

## Roofs

Roof elements are drawn in 2D as dashed footprint outlines (dotted lines show eave extensions) and generate proper sloped geometry in 3D. Default vertical level is `VertInfoRoof`: `v_anchor` = 2.70 m (top of walls), `height` = 2.5 m.

**Common roof parameters:**
- `anchor_point`: tuple[float, float] - bottom-left corner of the footprint (for octants: apex / valley point, also the rotation pivot)
- `size`: tuple[float, float] - (x_size, z_size) in meters: x = left/right, z = up/down in plan view
- `height`: float | None = None - ridge height above `v_anchor`; default 2.5 m
- `v_anchor`: float | None = None - 3D height of the roof base; default 2.70 m
- `orientation_angle`: float = 0 - rotation in degrees around `anchor_point` (for `gable_roof` default is None, see below)
- `color`: str = '#8B4513' - outline color in 2D; `'invisible'` hides it
- `label`: str | None = None - optional label, drawn at the footprint centre
- `roof_thickness`: float = 0.4 - thickness (vertical offset) of the roof shell in 3D (not for gable ends)
- `draw_edge_a`: bool = True - draw the footprint edge perpendicular to the ridge at local 0 (rectangular roofs)
- `draw_edge_b`: bool = True - draw the footprint edge perpendicular to the ridge at the far end (rectangular roofs)

Ridge direction for 2D drawing of rectangular roofs: along X when `orientation_angle` is given (any value) or `x_size >= z_size`; otherwise along Z.

### GableRoof
Two sloping planes meeting at a ridge (no gable-end triangles; add `gable_end_*` elements for those).

**YAML type:** `gable_roof`

**Parameters:** common roof parameters, plus:
- `orientation_angle`: float | None = None - when None, the ridge follows the longer side; when set, the ridge always runs along local X
- `extension_a`: float = 0 - horizontal overhang of the "a" slope (z = 0 side if ridge along X, x = 0 side if along Z), slope angle preserved
- `extension_b`: float = 0 - horizontal overhang of the "b" slope (z = z_size side / x = x_size side)
- `draw_ridge`: bool = True - draw the ridge line in 2D

### HippedRoof
All four sides slope toward the centre; square plan gives a pyramid, rectangular plan a short ridge with hip faces at the short ends.

**YAML type:** `hipped_roof`

**Parameters:** common roof parameters.

### SingleSlopeRoof
Mono-pitch (lean-to) roof: low eave along local z = 0 at `v_anchor`, high eave along z = z_size at `v_anchor + height`. No gable end caps.

**YAML type:** `single_slope_roof`

**Parameters:** common roof parameters, plus:
- `extension`: float = 0 - horizontal overhang of the low eave (z < 0 side)
- `draw_ridge`: bool = True - draw the high-eave edge in 2D

### HippedRoofOctantLeft / HippedRoofOctantRight
1/8 of a pyramid: right-angle triangle in plan from the apex (`anchor_point`, high) down to the eave. With `orientation_angle` = 0 it points in +z; the edge midpoint is at (0, z_size) and the base corner at (−x_size, z_size) for left or (+x_size, z_size) for right. For a 2d×2d pyramid use `size: [d, d]`; combine 4 left + 4 right at 0/90/180/270°.

**YAML type:** `hipped_roof_octant_left`, `hipped_roof_octant_right`

**Parameters:** common roof parameters (without `draw_edge_a/b`), plus:
- `extension`: float = 0 - horizontal eave overhang, slope angle preserved
- `draw_long_edge`: bool = True - draw the hypotenuse (apex → corner) in 2D
- `draw_short_edge`: bool = False - draw the leg apex → midpoint in 2D; the eave edge is always drawn

### HippedInternalOctantLeft / HippedInternalOctantRight
Inverted octant for inside corners / valleys: same plan triangle as the external octant, but `anchor_point` is the low valley point (at `v_anchor`) and the eave edge is high (`v_anchor + height`). 8 pieces around one point form a drain-to-centre roof. Drawn with dash-dot lines.

**YAML type:** `hipped_internal_octant_left`, `hipped_internal_octant_right`

**Parameters:** common roof parameters (without `draw_edge_a/b`), plus:
- `extension`: float = 0 - horizontal overhang of the high eave edge
- `draw_long_edge`: bool = True - draw the hypotenuse (valley → corner) in 2D
- `draw_short_edge`: bool = False - draw the leg valley → midpoint in 2D
- `draw_ridge`: bool = True - draw the high edge (midpoint → corner) in 2D

### GableEndWallLeft / GableEndWallRight / GableEndGlassLeft / GableEndGlassRight
Vertical triangular panel filling the gable end of a `gable_roof`, from `v_anchor` up to the ridge at `v_anchor + height`. Wall variants are opaque, glass variants transparent. **3D only** – nothing is drawn in 2D. Use the same `anchor_point`, `size`, `height`, `v_anchor` and `orientation_angle` as the matching `gable_roof`. The end is chosen by size: if `x_size >= z_size`, left is at local x = 0 and right at x = x_size; otherwise left is at z = 0 and right at z = z_size.

**YAML type:** `gable_end_wall_left`, `gable_end_wall_right`, `gable_end_glass_left`, `gable_end_glass_right`

**Parameters:** `anchor_point`, `size`, `height`, `v_anchor`, `orientation_angle` (= 0), `label` as in common roof parameters, plus:
- `color`: str = '#D3D3D3' - panel color (no 2D drawing)

**Example** (adapted from `examples/roofs/roofs_demo.yml`):
```yaml
- type: gable_roof
  anchor_point: [1, 44]
  size: [10, 6]
  height: 3.0
  v_anchor: 2.7
  extension_a: 0.8
  extension_b: 0.8
  label: 'Gable + walls'

- type: gable_end_wall_left
  anchor_point: [1, 44]
  size: [10, 6]
  height: 3.0
  v_anchor: 2.7
  color: '#D0CCC8'

- type: gable_end_glass_right
  anchor_point: [1, 44]
  size: [10, 6]
  height: 3.0
  v_anchor: 2.7

- type: single_slope_roof
  anchor_point: [26, 20]
  size: [8, 6]
  height: 2.5
  extension: 0.8
```

---

## Furniture - Storage

### GenericStorage
Storage box.

**YAML type:** `generic_storage`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the storage box (in meters)
- `thickness`: float - thickness of the storage box (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the storage box
- `color`: str = 'black' - color to use for drawing the storage box
- `label`: str | None = None - optional label for the element
- `height`: float | None = None - height of the storage box (in meters); if None, defaults to 2.0
- `v_anchor`: float | None = None - vertical anchor (in meters above floor); if None, uses the default level (0.04)

### Storage60
Storage box with thickness of 60 cm.

**YAML type:** `storage60`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the storage box (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the storage box
- `color`: str = 'black' - color to use for drawing the storage box
- `label`: str | None = None - optional label for the element
- `height`: float | None = None - height of the storage box (in meters); if None, defaults to 2.0
- `v_anchor`: float | None = None - vertical anchor (in meters above floor); if None, uses the default level (0.04)

**Note:** Thickness is fixed at 0.6 meters.

### Storage40
Storage box with thickness of 40 cm.

**YAML type:** `storage40`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the storage box (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the storage box
- `color`: str = 'black' - color to use for drawing the storage box
- `label`: str | None = None - optional label for the element
- `height`: float | None = None - height of the storage box (in meters); if None, defaults to 2.0
- `v_anchor`: float | None = None - vertical anchor (in meters above floor); if None, uses the default level (0.04)

**Note:** Thickness is fixed at 0.4 meters.

### Tabletop
Tabletop element.

**YAML type:** `tabletop`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the tabletop (in meters)
- `thickness`: float = 0.6 - thickness of the tabletop (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the tabletop
- `color`: str = 'black' - color to use for drawing the tabletop
- `label`: str | None = None - optional label for the element

**Note:** Height is fixed at the default 0.75 m.

---

## Furniture - Beds

### DoubleBed
Double bed.

**YAML type:** `double_bed`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the bed
- `color`: str = 'grey' - color to use for drawing the bed
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=2.15m, thickness=1.7m, height=0.5m.

### SingleBed
Single bed.

**YAML type:** `single_bed`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the bed
- `color`: str = 'grey' - color to use for drawing the bed
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=2.0m, thickness=0.9m, height=0.5m.

---

## Furniture - Appliances

### Dishwasher
Dishwasher appliance.

**YAML type:** `dishwasher`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.6m × 0.6m, height 0.72m.

### Fridge
Refrigerator appliance.

**YAML type:** `fridge`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `length`: float = 0.6 - length of the appliance (in meters)
- `thickness`: float = 0.6 - thickness of the appliance (in meters)
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Height is fixed at 1.8m.

### Freezer
Freezer appliance.

**YAML type:** `freezer`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `length`: float = 0.6 - length of the appliance (in meters)
- `thickness`: float = 0.6 - thickness of the appliance (in meters)
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Height is fixed at 1.8m.

### WashingMachine
Washing machine appliance.

**YAML type:** `washing_machine`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.6m × 0.6m, height 0.85m.

### Dryer
Dryer appliance.

**YAML type:** `dryer`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.6m × 0.6m, height 0.85m.

### Stovetop
Stovetop appliance.

**YAML type:** `stovetop`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.6m × 0.6m, height 0.85m.

### SingleSink
Single sink appliance.

**YAML type:** `single_sink`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=0.9m, thickness=0.6m, height=0.9m.

### DoubleSink
Double sink appliance.

**YAML type:** `double_sink`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=1.2m, thickness=0.6m, height=0.9m.

### TV
Flat TV set with a 16:9 screen; length and height are derived from the screen diagonal.

**YAML type:** `tv`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `diagonal`: float - screen diagonal (in inches); aspect ratio 16:9 is assumed
- `thickness`: float = 0.2 - thickness of the TV (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the TV
- `color`: str = 'black' - color to use for drawing the TV outline (fill is grey `#A2A2A2`)
- `label`: str | None = None - optional label for the element
- `v_anchor`: float = 0.80 - vertical anchor (in meters above floor)

**Note:** length = diagonal × 0.0254 × 16/√(16²+9²), height = diagonal × 0.0254 × 9/√(16²+9²) (e.g. 55" gives ≈1.22m × 0.68m).

---

## Furniture - Bathroom

### Shower
Shower stall.

**YAML type:** `shower`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fixture
- `color`: str = 'black' - color to use for drawing the fixture
- `label`: str | None = None - optional label for the element
- `length`: float = 0.9 - length of the shower stall (in meters)
- `thickness`: float = 0.9 - thickness of the shower stall (in meters)

**Note:** Height is fixed at 2.1m; rendered with alpha blending (glass).

### Bathtub
Bathtub.

**YAML type:** `bathtub`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fixture
- `length`: float = 1.7 - length of the bathtub (in meters)
- `thickness`: float = 0.8 - thickness of the bathtub (in meters)
- `height`: float = 0.6 - height of the bathtub (in meters)
- `color`: str = 'black' - color to use for drawing the fixture
- `label`: str | None = None - optional label for the element

### Basin
Bathroom basin/sink.

**YAML type:** `basin`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fixture
- `height`: float = 0.85 - height of the basin (in meters)
- `color`: str = 'black' - color to use for drawing the fixture
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=0.6m, thickness=0.5m.

### Toilet
Toilet.

**YAML type:** `toilet`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fixture
- `color`: str = 'black' - color to use for drawing the fixture
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=0.7m, thickness=0.4m, height=0.5m.

---

## Furniture - General

### Desk
Desk with standard dimensions.

**YAML type:** `desk`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the desk
- `length`: float = 1.4 - length of the desk (in meters)
- `thickness`: float = 0.65 - thickness of the desk (in meters)
- `color`: str = 'brown' - color to use for drawing the desk
- `label`: str | None = None - optional label for the element

**Note:** Height is fixed at 0.75m.

### DiningTable
Dining table with configurable dimensions.

**YAML type:** `dining_table`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the table (in meters)
- `thickness`: float - width of the table (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the table
- `color`: str = 'brown' - color to use for drawing the table
- `label`: str | None = None - optional label for the element

**Note:** Height is fixed at 0.75m.

### Chair
Chair with standard dimensions.

**YAML type:** `chair`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the chair
- `color`: str = 'darkgray' - color to use for drawing the chair
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.45m × 0.45m, height 0.9m.

### Sofa
N-element sofa with configurable number of seats.

**YAML type:** `sofa`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `num_seats`: int - number of seats in the sofa (1, 2, 3, etc.)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the sofa
- `color`: str = 'darkslateblue' - color to use for drawing the sofa
- `label`: str | None = None - optional label for the element

**Note:** Each seat is 0.8m wide; total length = num_seats × 0.8m; depth is fixed at 0.9m; height 0.85m.

---

## Furniture - Decorations

### FishTank
Fish tank / aquarium.

**YAML type:** `fish_tank`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fish tank
- `length`: float = 0.6 - length of the fish tank (in meters)
- `thickness`: float = 0.3 - depth of the fish tank (in meters)
- `v_anchor`: float = 0.6 - vertical anchor (in meters above floor)
- `color`: str = 'blue' - color to use for drawing the fish tank
- `label`: str | None = None - optional label for the element

**Note:** Height is fixed at 0.5m; rendered with alpha blending (glass).

---

## Devices

### GenericTank
Generic cylindrical water tank, drawn as a circle.

**YAML type:** `generic_tank`

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of the tank center (in meters)
- `diameter`: float = 0.6 - diameter of the tank (in meters)
- `height`: float = 1.32 - height of the tank (in meters); 0.6 × 1.32 gives about 150 liters
- `v_anchor`: float = 0.05 - vertical anchor (in meters above floor)
- `color`: str = '#7B7060' - color to use for drawing the tank
- `label`: str | None = None - optional label for the element

**Note:** When `label` is set, it is rendered at the center, rotated 45°, followed by the dimensions as `Ø<diameter>x<height>cm`.

---

## External Models - Common

These elements use pre-made 3D models (OBJ/glTF) for 3D export; the 2D drawing is still procedural. The model folder is named after the class `_registry_key`, which is the YAML type without the `model_` prefix (e.g. `model_armchair` → `armchair/`). Folders are searched in this order: `models/`, `models/local/`, `models/models_3rd_party/`, `models/stubs/` (1×1×1 m placeholder cubes). See [models/README.md](../models/README.md).

All elements listed here have `_requires_external_model = True`: if no model is found, the script stops with `FileNotFoundError`. Dimensions come from the model's `model.transform.json`. Passing `width`, `length` or `height` raises `TypeError`, unless the element takes that parameter itself (noted per element).

**Common parameters** (from `ExternalModelElement`):
- `anchor_point`: tuple[float, float] - (x, y) position in meters
- `orientation_angle`: float = 0 - rotation in degrees
- `color`: str | None = None - 2D drawing color (furniture ignores it and uses a hardcoded color)
- `label`: str | None = None - optional label for the element
- `id`: str | None = None - explicit ID; generated when omitted
- `v_anchor`: float | None = None - 3D elevation of the base (meters); default depends on the element's vertical level
- `texture_scale`: float | None = None - optional texture tiling scale (meters)
- `models_dir`: str | None = None - base model directory to search instead of the package `models/` (the same subdirectories are searched inside it)

**Note:** Some elements also set `secondary_normalization` (scale/rotation/translation) and `secondary_anchor_offset` internally to resize or flip the model. These are not YAML parameters.

---

## External Models - Windows and Doors

### Fixed-size windows
Windows drawn in 2D like the standard [Window](#window), with a fixed-size external model in 3D. Default `v_anchor` = 1.00 m (sill height).

| YAML type | Class | Size W×L×H (m) |
|---|---|---|
| `model_window_140x120` | Window140x120 | 1.40 × 1.40 × 1.20 |
| `model_window_90x120` | Window90x120 | 0.90 × 0.90 × 1.20 |
| `model_window_double_160x120` | WindowDouble160x120 | 1.60 × 1.60 × 1.20 |
| `model_window_double_160x140` | WindowDouble160x140 | 1.60 × 1.60 × 1.40 |

**Parameters:** the common parameters, plus:
- `overall_thickness`: float - total window/wall depth (meters), used for 2D drawing
- `single_line_thickness`: float = -1 - glazing line thickness in 2D; defaults to `overall_thickness / 10` if ≤ 0
- `color`: str = 'black' - 2D drawing color

### WindowSingleAny
**YAML type:** `model_window_single_any`

Single-pane window that scales its 1.40 × 1.20 m model to any size. Takes the same parameters as the fixed-size windows, plus:
- `length`: float = 1.4 - window width along the wall (meters)
- `height`: float = 1.2 - window height (meters)

### BalconyDoor
**YAML type:** `model_balcony_door`

Drawn in 2D like a [Door](#door). In 3D it uses a fixed 0.9 × 2.1 m model (frame, solid lower panel, glazed upper panel). The model is not resized to `doorway_width`. Its door-swing animation comes from `Door3D`. Default `v_anchor` = 0.02 m.

**Parameters:** the common parameters, plus:
- `doorway_width`: float - doorway width including both frame sides (meters, 2D)
- `door_width`: float - clear door width (meters, 2D)
- `thickness`: float - door/wall thickness (meters)
- `door_orientation_in_doorway`: float = 0.5 - share of the frame width (`doorway_width - door_width`) on the left side
- `to_the_right`: bool = False - door opens to the right
- `color`: str = 'black' - 2D drawing color
- `hinges_point`: float = 0.95 - relative hinge depth along the thickness (0-1)
- `opening_outside`: bool = False - door opens outward
- `door_type`: str = 'hinged' - `'hinged'` or `'sliding'` (2D drawing)

### Door variants
These take the same parameters as BalconyDoor. Only the 3D model is different.

| YAML type | Class | Size W×L×H (m) | Model |
|---|---|---|---|
| `model_window_door` | WindowDoor | 0.90 × 0.90 × 2.10 | single full-height glass wing |
| `model_solid_door_1` | SolidDoor1 | 0.90 × 0.90 × 2.10 | solid full-height panel |
| `model_solid_door_2` | SolidDoor2 | 0.90 × 0.90 × 2.10 | solid panel (second model) |
| `glass_door` | GlassDoor | 0.90 × 0.90 × 2.10 | glass wing with aluminium frame (see [Glass Structures](#glass-structures)) |

### WindowDoorDouble
**YAML type:** `model_window_door_double`

Double glass door: one 1.80 × 2.10 m model with a centre bar. In 2D it draws two hinged wings, each half of `doorway_width`/`door_width`. The left wing is hinged on the left and the right wing on the right. When `opening_outside` is False, the model is rotated 180° and offset by `thickness × 2/3`. Otherwise it is offset by `thickness / 3`.

**Parameters:** same as BalconyDoor. `to_the_right` is accepted but has no effect on the 2D wings, which are always symmetric.

---

## External Models - Furniture

Furniture uses only the common parameters. The `color` parameter is ignored because the 2D outline uses a fixed color. When `orientation_angle == 0`, the anchor is the bottom-left corner of the footprint. The default `v_anchor` is 0. Sizes come from `models/models_3rd_party/<key>/model.transform.json`. Only 1×1×1 stubs are in the repository, so these sizes apply only when the 3rd-party models are installed.

| YAML type | Class | Size W×L×H (m) | Description |
|---|---|---|---|
| `model_wooden_chair` | WoodenChair | 0.50 × 0.50 × 0.85 | wooden chair |
| `model_sofa_model` | SofaModel | 0.49 × 1.368 × 0.489 | loveseat; long axis along Y at 0° |
| `model_master_bed` | MasterBed | 1.749 × 2.257 × 1.19 | king-size bed; anchor at the foot of the bed |
| `model_armchair` | Armchair | 0.776 × 0.825 × 0.747 | bergère / club armchair |
| `model_chair_20` | Chair20 | 0.661 × 0.687 × 1.295 | high-back dining chair |
| `model_chaise_longue_1` | ChaiseLongue1 | 0.783 × 1.649 × 0.808 | chaise longue; long axis along Y at 0° |
| `model_desk_1` | Desk1 | 2.059 × 0.971 × 1.095 | desk with upper hutch |
| `model_sofa_22` | Sofa22 | 2.835 × 0.904 × 0.702 | 3-seat sofa |
| `model_sofa_23` | Sofa23 | 2.003 × 0.903 × 0.702 | 2-seat sofa |
| `model_stool_7` | Stool7 | 0.297 × 0.297 × 0.670 | bar / counter stool |
| `model_table_01` | Table01 | 4.123 × 1.671 × 0.854 | large dining / conference table |
| `model_well` | Well | 1.0 × 1.0 × 1.0 | garden well (2D: square with circle) |

---

## External Models - Vegetation

Trees and shrubs drawn in 2D like circular vegetation (`anchor_point` is the centre). The 3D model is scaled to `diameter`/`height` and rotated randomly around the vertical axis. Values not given are resolved from `species` (see species database), then from the defaults below. Default `v_anchor` = 0.01 m.

### LeafyTree
**YAML type:** `model_leafy_tree` (model: 4.4 × 4.4 × 7.4 m)

**Parameters:**
- `anchor_point`: tuple[float, float] - centre of the crown
- `diameter`: float | None = None - crown diameter; fallback 4.0
- `height`: float | None = None - tree height; fallback 10.0
- `trunk_diameter`: float | None = None - fallback 0.3
- `color`: str | None = None - crown color; fallback '#228B22'
- `trunk_color`: str | None = None - fallback '#654321'
- `species`: str | None = None - species name used to fill the unset values
- `bloom_season_start` / `bloom_season_end`: str | None = None - bloom period
- `bloom_color`: str | None = None - bloom color
- `label`, `id`, `v_anchor`, `models_dir` - as in the common parameters

### LeafyShrub1
**YAML type:** `model_leafy_shrub_1` (model: 2 × 2 × 5 m)

**Parameters:** same as LeafyTree, without `trunk_diameter`/`trunk_color`. The fallbacks are `diameter` 2.0, `height` 2.0 and `color` '#228B22'.

---

## Composite Elements

A composite element creates several child elements and draws each of them. Its ID is the given `id`, or is generated from the class name and `label`. Model-based composites (`composite_model_*`) forward `v_anchor` and `models_dir` to every child.

### Composite_WindowDoorDouble
**YAML type:** `composite_model_window_door_double`

Two `WindowDoor` elements placed side by side. Each child gets half of `doorway_width` and `door_width`. The left wing is hinged on the left (`door_orientation_in_doorway` = 1) and the right wing on the right (`door_orientation_in_doorway` = 0).

**Parameters:**
- `anchor_point`: tuple[float, float] - left frame corner
- `doorway_width`: float - total doorway width (meters)
- `door_width`: float - total clear opening width (meters)
- `thickness`: float - door/wall thickness (meters)
- `orientation_angle`: float = 0 - rotation in degrees
- `to_the_right`: bool = False - accepted but not used
- `color`: str = 'black' - 2D drawing color
- `hinges_point`: float = 0.95 - relative hinge depth (0-1)
- `opening_outside`: bool = False - wings open outward
- `label`: str | None = None - passed to both wings

### Composite_WindowDouble
**YAML type:** `composite_model_window_double`

Two `WindowSingleAny` windows side by side, each `length / 2` wide.

**Parameters:**
- `anchor_point`: tuple[float, float] - bottom-left corner
- `overall_thickness`: float - window/wall depth (meters)
- `single_line_thickness`: float = -1 - see fixed-size windows
- `length`: float = 1.4 - total width (meters)
- `height`: float = 1.2 - window height (meters)
- `orientation_angle`: float = 0
- `color`: str = 'black'
- `label`: str | None = None - passed to both windows

### Composite_GlassDoor
**YAML type:** `composite_glass_door`

An `AluFrame` (static outer frame) with an animated `SolidGlassDoor` leaf inside it. The leaf is trimmed by a 0.005 m margin on every side and sits at depth `hinges_depth × (thickness − 0.01)` in the wall, where `hinges_depth` = `hinges_point`, or `1 − hinges_point` when opening outside. The label is shown only on the frame.

**Parameters:**
- `anchor_point`: tuple[float, float] - bottom-left of the frame
- `doorway_width`: float - total frame width (meters)
- `door_width`: float - glass leaf opening width (meters); side bars are `(doorway_width − door_width) / 2`
- `thickness`: float - frame/wall depth (meters)
- `height`: float = 2.1 - frame height (meters)
- `orientation_angle`: float = 0
- `to_the_right`: bool = False - leaf swings to the right
- `color`: str = 'black' - 2D door-arc color
- `hinges_point`: float = 0.95 - hinge depth fraction (0 = front, 1 = back)
- `opening_outside`: bool = False - leaf opens outward
- `label`: str | None = None
- `v_anchor`: float | None = None - 3D base of the frame; default 0.02

---

## Glass Structures

Elements for winter gardens and conservatories. Example: `examples/glass_structures/glass_demo.yml`.

### GlassDoor
**YAML type:** `glass_door`

A full-height glass door with an aluminium frame. It is identical to `WindowDoor` (same parameters as [BalconyDoor](#balconydoor)) and only uses the `glass_door` model (0.9 × 0.9 × 2.1 m).

### GlassPanel
**YAML type:** `glass_panel`

A static glass wall panel with an aluminium frame, placed like a Wall. The base model (1 × 2.1 × 0.08 m) is scaled to `length` × `height` × `thickness`. In 2D it is drawn as a semi-transparent rectangle. Default `v_anchor` = 0.01 m.

**Parameters:**
- `anchor_point`: tuple[float, float] - bottom-left corner of the panel
- `length`: float - panel width along the wall (meters)
- `thickness`: float - frame depth (meters)
- `height`: float | None = None - panel height; default 2.5
- `orientation_angle`: float = 0
- `color`: str = '#C8E8F4' - 2D fill color
- `label`: str | None = None
- `v_anchor`: float | None = None

**Note:** `id` is accepted; any other parameter (e.g. `texture_scale`, `models_dir`) raises a `TypeError`.

### AluFrame
**YAML type:** `alu_frame`

An aluminium frame without glass (four perimeter bars). It takes the same parameters as GlassPanel (`color` default '#C8E8F4') and uses the `alu_frame` model. In 2D it is drawn as a grey rectangle with a white hollow interior.

### GlassSlope
**YAML type:** `glass_slope`

A tilted glass roof slope with an aluminium frame, configured like `SingleSlopeRoof`. The low eave runs along plan-z = 0 at `v_anchor`, and the high eave along plan-z = `z_size` at `v_anchor + height`. The flat 1 × 1 m model is scaled and tilted. In 2D it is drawn as a dashed footprint, with a dotted line for the extension.

**Parameters:**
- `anchor_point`: tuple[float, float] - bottom-left corner of the footprint
- `size`: tuple[float, float] - (x_size, z_size) in meters
- `height`: float | None = None - rise from low to high eave; default 1.5
- `v_anchor`: float | None = None - 3D height of the low eave; default 2.70
- `orientation_angle`: float = 0
- `extension`: float = 0 - extends the low-eave edge outward (meters)
- `color`: str = '#C8E8F4' - 2D outline color
- `label`: str | None = None - drawn only when set

**Note:** Like GlassPanel, `id` is accepted and any other parameter raises a `TypeError`.

### SolidGlassDoor
**YAML type:** `solid_glass_door`

A frameless glass door (procedural, no external model). It is drawn like [Door](#door) and exported in 3D as a thin glass box.

**Parameters:** same as Door, except:
- `thickness`: float = 0.01 - glass panel depth
- `color`: str = '#C8E8F4'

### Greenhouse
**YAML type:** `greenhouse`

A glass greenhouse (procedural): four glass walls with a gable glass roof. In 2D it is drawn as a translucent rectangle with a ~1 m panel grid and a ridge line along the longer side. Example: `examples/landscaping/structures_demo.yml`.

**Parameters:**
- `anchor_point`: tuple[float, float] - bottom-left corner of the footprint
- `size`: tuple[float, float] - (x_size, z_size) in meters
- `height`: float | None = None - wall height; default 2.0
- `roof_height`: float = 1.2 - extra height from wall top to ridge
- `color`: str = '#D3D3D3' - 2D fill color
- `orientation_angle`: float = 0
- `label`: str | None = None
- `v_anchor`: float | None = None - 3D base; default 0.01 (ground level)

**Note:** Any other parameter raises a `TypeError`.

---

## Common Parameter Notes

### Coordinate System
- All coordinates are in **meters**
- `anchor_point` is the **bottom-left corner** (when `orientation_angle == 0`) for rectangular/surface elements and the **center** for circular elements
- In 2D the Y-axis points upward and the X-axis points right
- In 3D (glTF) plan X → X, plan Y → Z, and `v_anchor`/`height` are along the vertical Y-axis

### Orientation
- `orientation_angle` is measured in **degrees**
- Positive angles rotate **counterclockwise** around the anchor point
- 0° = horizontal (pointing right), 90° = vertical (pointing up)

### Labels and IDs
- Every element accepts an explicit `id`; when omitted, a unique one is generated: `<label>_<number>` if a `label` is given, otherwise `<lowercase_type>_<number>`
- Elements accept only the parameters listed for them; any other parameter raises a `TypeError`
- `label` is optional and user-defined for identification
- Both can be displayed on the floor plan if configured in options

### Colors
- Colors can be any matplotlib-compatible color string
- Common values: 'black', 'grey', 'brown', 'blue', 'darkgray', 'darkslateblue'
- Also supports hex colors (e.g., '#FF5733') and RGB tuples
- `color: invisible` hides the element in 2D; with the `show_invisible` option it is drawn in red instead

### Variables and Expressions
- Top-level `vars:` (legacy name: `constants:`) define variables; `group`/`room` containers may define their own `vars` that override global ones
- Numeric parameters (`anchor_point`, `length`, `thickness`, `width`, `size`, `height`, `v_anchor`, `diameter`, `radius`, `orientation_angle`, `doorway_width`, `door_width`, `overall_thickness`, `first_point`, `second_point`, `extension`, `extension_a`, `extension_b`, `roof_thickness`) accept a variable name or an arithmetic expression, e.g. `length: room_w - 2 * wall_t`
- String parameters (`color`, `label`, `species`, `trunk_color`, `bloom_color`, `bloom_season_start`, `bloom_season_end`, `material`, `textures`) accept `{var}` references, e.g. `color: {wall_clr}` or `label: "shrub ({gat_1})"`; an unknown variable raises an error
- String variables are not substituted inside arithmetic expressions

### Container Integration
- `Room` and `Group` are containers; child `anchor_point` values are relative to the container's own `anchor_point`
- `Room` validates that exactly 4 child walls have `room_edge=True` forming an axis-aligned rectangle; `Group` has no such requirement
- Containers can be nested: a `group` or `room` may contain another `group` or `room` as a child element
- `room_id` is set automatically on walls owned by a `Room`

### Options
- Per-element-type drawing options come from top-level `default_options`; a floor plan's `options` section overrides them for that floor plan only

---

## Vertical Positioning (v_anchor and height)

Every element has a `v_anchor` and a `height` attribute. They control 2D drawing order and the element's vertical placement and size in the 3D (glTF) export.

**Not every element accepts them as YAML parameters.** Many elements (e.g. `desk`, `chair`, `sofa`, `toilet`, `shower`, `fridge`, `lawn`, `garden_path`, `ground`, `switch`, `power_outlet`, lamps, annotations) always use the defaults from their `VertInfo*` mixin / class; passing `v_anchor` or `height` to them raises an "unexpected keyword argument" error.

| Accepts | Element types |
|---------|---------------|
| `v_anchor` and `height` | `wall`, `wallnd`, `window`, `door`, `floor`, `ceiling`, roofs (`gable_roof`, `hipped_roof`, `single_slope_roof`, gable-end and hipped-octant parts), `glass_panel`, `glass_slope`, `alu_frame`, `deck`, `surface`, `greenhouse`, `generic_storage`, `storage40`, `storage60`, `generic_tank` |
| `v_anchor` only | `fish_tank`, `tv`, external `model_*` elements (their height is fixed by the model; passing `height` raises an error) |
| `height` only | `basin`, `bathtub`, `fence`, `fountain`, `hedge`, `retaining_wall`, `shrub`, `tree`, `raised_bed`, `garden_house`, `model_leafy_tree`, `model_leafy_shrub_1`, `model_window_single_any` |

### v_anchor (Vertical Anchor)

**Type:** `float | None`  
**Default:** Element-specific (see table below)  
**Unit:** meters

- **3D placement**: the element's base is placed at Y = `v_anchor` (relative to the floor plan's own `v_anchor`)
- **Rendering order**: in 2D, elements with higher `v_anchor` are drawn on top (it is used directly as the matplotlib z-order)
- **Automatic offsetting**: each element instance gets `0.0001 × instance_number` added to its base `v_anchor` (the counter is global across all elements), giving a deterministic draw order; elements defined first in YAML are drawn first (behind) within the same level. The offset is part of `v_anchor` and therefore also shifts the 3D position slightly.

**Default levels (`VertInfo*` mixins in `elements/vertical_levels.py`):**

| Mixin | v_anchor | Mixin default height | Element types |
|-------|----------|----------------------|---------------|
| `VertInfoLvlGround` | -0.10 | 0.09 | `ground` |
| `VertInfoLvl00` | -0.01 | – | `lawn`, `garden_path` |
| `VertInfoFloors` | 0.00 | 0.02 | `floor` |
| `VertInfoLvl01` | 0.01 | – | walls, `fence`, `retaining_wall`, `hedge`, `shrub`, `tree`, `deck`, `surface`, `greenhouse`, `gazebo`, pools, `fountain`, `glass_panel`, `alu_frame` |
| `VertInfoDoor` | 0.02 | 2.1 | `door`, `glass_door`, `solid_glass_door`, `model_balcony_door`, `model_window_door(_double)`, `model_solid_door_1/2` |
| `VertInfoLvl03` | 0.03 | – | furniture, appliances, bathroom fixtures, beds, `tabletop`, `fish_tank`, `generic_tank` |
| `VertInfoLvl04` | 0.04 | – | `generic_storage`, `storage40`, `storage60`, `tv` |
| `VertInfoOutlets` | 0.30 | 0.08 | `power_outlet` |
| `VertInfoWindows` | 1.00 | 1.4 | `window`, fixed `model_window_*` |
| `VertInfoSwitches` | 1.20 | 0.08 | (defined, currently unused) |
| `VertInfoWallLamps` | 2.00 | 0.3 | `wall_lamp` |
| `VertInfoCeilingSurface` | 2.69 | 0.01 | `ceiling` |
| `VertInfoCeiling` | 2.70 | 0.07 | `ceiling_lamp` |
| `VertInfoRoof` | 2.70 | 2.5 | roofs and roof parts, `glass_slope` |
| `VertInfoAnnotations` | 3.50 | 0.0 | `dimension_arrow`, `text_box` |
| *(none)* | 0.00 | 0.0 | `switch`, `line`, `polygon`, `circle`, cables, `led_strip`, `pond`, `pergola`, `raised_bed`, `garden_house`, containers, external `model_*` furniture/trees |

Each mixin also defines a small 3D size expansion/shrink (`_get_3d_expansion`) used to avoid z-fighting, e.g. furniture shrinks slightly, doors/windows/outlets protrude slightly from walls.

**YAML Example:**
```yaml
elements:
  - type: desk
    anchor_point: [2.0, 3.0]
    # Fixed v_anchor 0.03 (furniture level), height 0.75

  - type: generic_storage
    anchor_point: [4.0, 3.0]
    orientation_angle: 0
    length: 0.8
    thickness: 0.4
    v_anchor: 1.6   # wall-hung cabinet
    height: 0.6
```

### height

**Type:** `float | None`  
**Default:** Element-specific (see table below)  
**Unit:** meters

The physical height of the element. It is not used for 2D drawing; in the 3D export it is the vertical extent of the generated geometry. Class-level defaults override the mixin defaults above.

**Default Heights by Element Type:**

| Element Type | Default Height (m) |
|--------------|-------------------|
| **Structural** | |
| `wall`, `wallnd` | 2.7 |
| `window` | 1.4 |
| `door` and door models | 2.1 |
| `floor` / `ceiling` | 0.02 / 0.01 |
| roofs, roof parts | 2.5 |
| `glass_panel`, `alu_frame` / `glass_slope` | 2.5 / 1.5 |
| **Furniture** | |
| `desk`, `dining_table`, `tabletop` | 0.75 |
| `chair` / `sofa` | 0.9 / 0.85 |
| `single_bed`, `double_bed` | 0.5 |
| `generic_storage`, `storage40`, `storage60` | 2.0 |
| `tv` | derived from its diagonal (16:9) |
| **Appliances** | |
| `fridge`, `freezer` | 1.8 |
| `washing_machine`, `dryer`, `stovetop` | 0.85 |
| `dishwasher` | 0.72 |
| `single_sink`, `double_sink` | 0.9 |
| `generic_tank` | 1.32 |
| **Bathroom** | |
| `toilet` | 0.5 |
| `shower` | 2.1 |
| `bathtub` / `basin` | 0.6 / 0.85 (constructor parameter defaults) |
| **Landscaping** | |
| `ground` | 0.09 |
| `lawn` / `garden_path` / `deck` | 0.0 / 0.02 / 0.015 |
| `surface` | 0.30 |
| `fence`, `hedge` | 1.8 |
| `retaining_wall`, `fountain` | 1.0 |
| `rect_pool` | 1.4 |
| `gazebo` / `greenhouse` | 2.5 / 2.0 |
| **Symbols and lighting** | |
| `power_outlet`, `switch`, `wall_lamp`, `ceiling_lamp` | 0.0 |
| `dimension_arrow`, `text_box` | 0.0 |
| **External models** (`model_*`) | from model metadata, fixed |

---

## 3D Visualization Parameters

The 3D model is exported only when `project.visualisation_dir` is set: one glTF 2.0 file per floor plan (named after the floor-plan title), with textures copied to `<visualisation_dir>/textures/`, plus a `camera.json` viewer file. OBJ/MTL export exists in code but is disabled.

### Textures and Materials

- Textures and materials are resolved **per element type** (registry key), not per element: `textures/defaults/<type>/<type>.png|.jpg` is tried first, then `textures/fallback/<type>/`, then `textures/fallback/default/default.jpg` (`.png` is preferred over `.jpg`)
- An optional `<type>.mtl` next to the texture sets material properties:
  - `Kd` → base color (black `Kd` with a `map_Kd` texture is treated as white)
  - `Ns` → roughness = `1 − min(Ns / 100, 1)` (default roughness 0.8)
  - `Ks` → glTF specular extension
  - `d` / `Tr` < 0.99 → alpha and `alphaMode: BLEND`
- Without an `.mtl` the base color is a built-in default (light grey; `wall` near white, `door` brown, `window` light blue)
- `window`, fixed window models, `shower` and `fish_tank` always use `alphaMode: BLEND`

### texture_scale (Texture Tiling)

**Type:** `float | None`  
**Default:** `None` (stretch texture to fit), with element-specific defaults below  
**Unit:** meters (size of one texture tile)

- **None**: box-shaped geometry gets 0–1 UVs per face (texture stretched over each face)
- **Set to value**: texture repeats every N meters: `u_max = face_length / texture_scale`, computed per face from that face's own dimensions (e.g. a 1.8 m window face with 0.2 → 9 repeats)
- Sloped/roof geometry uses per-face planar UVs divided by `texture_scale` (1.0 if unset)
- Texture must be seamless/tileable for good results

**Element-specific defaults:**

| Element | texture_scale | Overridable |
|---------|---------------|-------------|
| `window` | 0.2 | no |
| `ground` | 0.5 | no |
| `deck` | 0.6 | no |
| `surface` | 1.0 | no |
| `garden_path` | 1.5 | no |
| roofs | 3.0 | no |

`texture_scale` can be set only on elements whose constructor accepts it: `wall`, `wallnd`, `door`, `floor`, `ceiling` and external `model_*` elements (which keep their model's own UVs, so it has no effect there).

**YAML Example:**
```yaml
elements:
  # Window with fixed tiling (0.2m tiles)
  - type: window
    anchor_point: [0, 3.5]
    orientation_angle: 0
    length: 1.8
    overall_thickness: 0.15
    color: lightblue

  # Wall with a repeating brick texture
  - type: wall
    anchor_point: [0, 0]
    orientation_angle: 0
    length: 5.0
    thickness: 0.2
    color: gray
    texture_scale: 0.5
```

---

## Floor Plan v_anchor (3D Elevation)

Each entry in `floor_plans:` accepts an optional top-level `v_anchor` key that sets the
**Y-axis elevation (metres)** of the entire floor plan in the exported 3D model (glTF).
It has no effect on 2D rendering.

**Type:** `float`  
**Default:** `0.0` (ground level)  
**Unit:** metres

### How it works

When `v_anchor` is non-zero the exporter wraps all geometry from that floor plan in a
single glTF node called `"floor_level"` with `translation: [0, v_anchor, 0]`.  All
element nodes become children of this wrapper, so no element coordinates need to change —
only the root transform shifts on Y.

### YAML example — multi-storey building

```yaml
floor_plans:
  - title: parter
    v_anchor: 0.0     # ground floor (default, can be omitted)
    layout: ...
    elements: ...

  - title: pietro
    v_anchor: 3.0     # first floor, 3 m above ground floor
    layout: ...
    elements: ...

  - title: poddasze
    v_anchor: 6.0     # second floor / attic
    layout: ...
    elements: ...
```

### Notes

- `v_anchor: 0.0` (or omitting the key) produces no wrapper node.
- The value is independent of the element-level `v_anchor`: element-level `v_anchor` positions an element within its floor plan (and sets its 2D draw order); this key positions the whole floor plan on the Y axis in 3D.
- Element `v_anchor` values are therefore relative to the floor plan origin. A `ceiling` at `v_anchor: 2.69` in a floor plan with `v_anchor: 3.0` appears at Y = 5.69 m in the merged 3D scene.
