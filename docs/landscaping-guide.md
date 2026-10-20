# Landscaping Elements Documentation

Parameter reference for the landscaping elements: vegetation, hardscape, water features and garden structures. Other element types (including the external-model plants `model_leafy_tree` / `model_leafy_shrub_1` and the glass structures / `greenhouse`) are described in [element-parameters-reference.md](element-parameters-reference.md).

Examples: [examples/landscaping/](../examples/landscaping/) (`vegetation_demo.yml`, `hardscape_demo.yml`, `water_features_demo.yml`, `structures_demo.yml`, `site_plan_complete.yml`).

## Common Notes

- Positions are given with `anchor_point: [x, y]` in meters. Rectangular elements use the bottom-left corner (rotation via `orientation_angle`, degrees, counterclockwise around the anchor); circular elements and `pond` use the center.
- Rectangular *surface* elements (`lawn`, `garden_path`, `ground`, `pergola`, `raised_bed`, `deck`, `surface`, `garden_house`) take `size: [x_size, z_size]`. Linear elements (`hedge`, `fence`, `retaining_wall`, `rect_pool`, `oval_pool`) take `length` and `thickness`.
- `color: 'invisible'` hides an element (drawn red when `Wall: show_invisible: true` is set).
- Only `deck` and `surface` accept `v_anchor` and `height` overrides (see [Vertical Positioning](element-parameters-reference.md#vertical-positioning-v_anchor-and-height)). None of the landscaping elements accepts `id` or `texture_scale` in YAML. Some have a fixed `texture_scale` for 3D export: `garden_path` 1.5, `ground` 0.5, `deck` 0.6, `surface` 1.0.
- Drawing order: every element, including its patterns (grass, gravel, planks, ripples, bloom overlays), is drawn at its own zorder = `v_anchor`, plus a tiny per-element offset. Default `v_anchor`: `ground` -0.10; `lawn`, `garden_path` -0.01; `pond`, `pergola`, `raised_bed`, `garden_house` 0.0; all others 0.01.

---

## Vegetation

### Tree
**YAML type:** `tree`

Circular canopy with a trunk circle. Unset values come from `species` first (see [Species Database](#species-database)), then from the fallback.
- `anchor_point`: tuple[float, float] - center of the canopy
- `diameter`: float | None = None - canopy diameter; fallback 4.0
- `height`: float | None = None - tree height (shown in label); fallback 10.0
- `trunk_diameter`: float | None = None - fallback 0.3
- `color`: str | None = None - canopy color; fallback '#228B22'
- `trunk_color`: str | None = None - fallback '#654321'
- `species`: str | None = None - species name; fills unset values from the database
- `bloom_season_start` / `bloom_season_end`: str | None = None - bloom period, 'dd.mm'
- `bloom_color`: str | None = None - color of the dashed bloom ring
- `label`: str | None = None

### Shrub
**YAML type:** `shrub`

Circular bush without a trunk; blooms are drawn as 5 small colored circles.
- `anchor_point`: tuple[float, float] - center of the shrub
- `diameter`: float | None = None - fallback 1.0
- `height`: float | None = None - fallback 1.5
- `color`: str | None = None - fallback '#90EE90'
- `species`, `bloom_season_start`, `bloom_season_end`, `bloom_color`, `label` - as for Tree

### Hedge
**YAML type:** `hedge`

Rectangle; blooms are drawn as a dashed outline.
- `anchor_point`: tuple[float, float] - bottom-left corner
- `length`: float - hedge length
- `thickness`: float - hedge depth
- `height`: float | None = None - from `species`; otherwise stays unset (not shown)
- `color`: str | None = None - fallback '#556B2F'
- `orientation_angle`: float = 0
- `species`, `bloom_season_start`, `bloom_season_end`, `bloom_color`, `label` - as for Tree (species fills `height`, `color` and bloom values)

### Lawn
**YAML type:** `lawn`

Filled rectangle with a grass texture; the label shows `size` (e.g. `8.0m×5.0m`).
- `anchor_point`: tuple[float, float] - bottom-left corner
- `size`: tuple[float, float] - (x_size, z_size)
- `color`: str = '#7CFC00'
- `orientation_angle`: float = 0
- `label`: str | None = None

### External-model plants
`model_leafy_tree` and `model_leafy_shrub_1` take the same parameters as Tree/Shrub (also resolved from `species`), plus 3D-model options. See [External Models - Vegetation](element-parameters-reference.md#external-models---vegetation).

---

## Species Database

Defined in `floor_planner/elements/landscaping/species_db.py` (`SPECIES_DB`). When `species` matches a key (case-insensitive), the entry gives default values. Priority: explicit YAML value > species value > class fallback. Unknown names are ignored silently (the name is still shown as text).

Parameters a species entry can fill: `height`, `diameter`, `color`, `trunk_diameter`, `trunk_color` (trees only), `bloom_season_start`, `bloom_season_end`, `bloom_color`. Tree and the external-model plants use all of them, Shrub all except the trunk values, Hedge only `height`, `color` and the bloom values.

Available keys:
- Trees: `Lipa`, `Glediczja`, `Katalpa`, `Dąb`, `Klon`, `Brzoza`, `Świerk`, `Sosna`, `Jabłoń`, `Wiśnia`
- Shrubs: `Heptakodium`, `Jagoda Kamczacka`, `Biała Forsycja`, `Kalina Waka`, `Guzikowiec`, `Krzewuszka`, `Ligustr`, `Lilak`, `Jaśminowiec`, `Forsycja`, `Hortensja`, `Tawuła`, `Pęcherznica`, `Kalina Pompon`
- Berries: `Porz. czerwona`, `Porz. biała`, `Porz. czarna`, `Borówka`

To add a species, add an entry to `SPECIES_DB` with only the keys you need.

```yaml
- type: tree
  anchor_point: [5, 5]
  species: 'Lipa'      # height 20, diameter 12, bloom 15.06-15.07 ...
  diameter: 8.0        # explicit value wins
```

---

## Vegetation Options

Options are set per element class in `default_options` and can be overridden for one floor plan in its `options` section:

- `show_species`: bool = false - draw the species name in the center (Tree, Shrub, Hedge)
- `show_bloom`: bool = false - draw the bloom period text, and the bloom overlay when `bloom_color` and both bloom dates are set (Tree, Shrub, Hedge)
- `label_color` / `id_color` - color of the label / ID text. A label is drawn only when `label_color` is set for its class.

Keys: `Tree`, `Shrub`, `Hedge`, `Lawn`, or `Vegetation`. `Vegetation` is used for any of these that has no setting of its own. `model_leafy_tree` / `model_leafy_shrub_1` are drawn in 2D as a Tree / Shrub and use those keys. The other landscaping keys are `Fence`, `GardenPath`, `RetainingWall`, `Fountain`, `Pond`, `Pool` (both `rect_pool` and `oval_pool`), `Pergola`, `RaisedBed`, `Gazebo`, `Deck`, `GenericSurface` (`surface`) and `GardenHouse`. `ground` never draws a label or ID.

```yaml
default_options:
  Vegetation:
    show_species: true
    show_bloom: true
    label_color: 'black'
  Pool:
    label_color: 'navy'
floor_plans:
  - options:
      Tree:
        show_bloom: false   # this floor plan only
```

Note: options must be nested under a class key. A bare `label_color` placed directly under `default_options` is ignored.

---

## Hardscaping

### Fence
**YAML type:** `fence`
- `anchor_point`: tuple[float, float] - start point (bottom-left)
- `length`: float
- `style`: str = 'solid' - 'solid', 'picket', 'chain-link', 'rail'
- `height`: float = 1.8 - shown in label
- `thickness`: float = 0.1
- `color`: str = '#8B4513'
- `orientation_angle`: float = 0
- `label`: str | None = None

### GardenPath
**YAML type:** `garden_path`
- `anchor_point`: tuple[float, float] - bottom-left corner
- `size`: tuple[float, float] - (x_size, z_size)
- `material`: str = 'gravel' - 'gravel', 'stone', 'paving', 'wood', 'mulch'
- `color`: str = '#D3D3D3'
- `orientation_angle`: float = 0
- `label`: str | None = None

### Ground
**YAML type:** `ground`

Earth/soil area below ground level, drawn as a thin outline only. Default height 0.09 m.
- `anchor_point`: tuple[float, float] - bottom-left corner
- `size`: tuple[float, float] - (x_size, z_size)
- `color`: str = '#D2691E' - outline color
- `orientation_angle`: float = 0
- `label`: str | None = None - not drawn

### RetainingWall
**YAML type:** `retaining_wall`
- `anchor_point`: tuple[float, float] - start point (bottom-left)
- `length`: float
- `height`: float - wall height; sets the number of stone courses drawn (one per 0.3 m). Required in practice: the code has no working fallback.
- `thickness`: float = 0.3
- `color`: str = '#696969'
- `orientation_angle`: float = 0
- `label`: str | None = None

---

## Water Features

### Fountain
**YAML type:** `fountain`
- `anchor_point`: tuple[float, float] - center
- `diameter`: float - basin diameter
- `height`: float = 0.5
- `style`: str = 'tiered' - 'tiered', 'spray', 'simple'
- `color`: str = '#87CEEB' - water
- `basin_color`: str = '#A9A9A9'
- `label`: str | None = None

### Pond
**YAML type:** `pond`
- `anchor_point`: tuple[float, float] - center
- `length`: float
- `width`: float
- `shape`: str = 'oval' - 'oval', 'kidney', 'rectangular', 'irregular'
- `color`: str = '#4682B4' - water
- `border_color`: str = '#2F4F4F'
- `label`: str | None = None

### RectPool
**YAML type:** `rect_pool`

Water rectangle with a 0.15 m border; the label shows `length×thickness`. Default height 1.4 m.
- `anchor_point`: tuple[float, float] - bottom-left corner of the water
- `length`: float - pool length (along X before rotation)
- `thickness`: float - pool width
- `pool_color`: str = '#00BFFF'
- `border_color`: str = '#B0C4DE'
- `show_lanes`: bool = False - lane lines
- `show_steps`: bool = True - entry steps in the bottom-left corner
- `orientation_angle`: float = 0
- `label`: str | None = None

### OvalPool
**YAML type:** `oval_pool`

Like RectPool, but oval and without `show_lanes`. `show_steps` draws semicircular steps.
- `anchor_point`, `length`, `thickness`, `pool_color`, `border_color`, `show_steps`, `orientation_angle`, `label` - as for RectPool

---

## Garden Structures

Glass structures and `greenhouse` are described in [Glass Structures](element-parameters-reference.md#glass-structures).

### Pergola
**YAML type:** `pergola`
- `anchor_point`: tuple[float, float] - bottom-left corner
- `size`: tuple[float, float] - (x_size, z_size)
- `post_size`: float = 0.2
- `orientation_angle`: float = 0
- `color`: str = '#8B4513'
- `label`: str | None = None

### RaisedBed
**YAML type:** `raised_bed`
- `anchor_point`: tuple[float, float] - bottom-left corner
- `size`: tuple[float, float] - (x_size, z_size)
- `height`: float = 0.4
- `border_thickness`: float = 0.15
- `fill_color`: str = '#654321' - soil
- `border_color`: str = '#8B4513'
- `orientation_angle`: float = 0
- `label`: str | None = None

### Gazebo
**YAML type:** `gazebo`

Octagonal structure with a roof. Default height 2.5 m.
- `anchor_point`: tuple[float, float] - center
- `diameter`: float
- `color`: str = '#DEB887'
- `roof_color`: str = '#8B4513'
- `label`: str | None = None

### Deck
**YAML type:** `deck`
- `anchor_point`: tuple[float, float] - bottom-left corner
- `size`: tuple[float, float] - (x_size, z_size)
- `color`: str = '#D2691E'
- `orientation_angle`: float = 0
- `label`: str | None = None
- `v_anchor`: float | None = None - default 0.01
- `height`: float | None = None - default 0.015

### Surface
**YAML type:** `surface`

Generic flat surface (e.g. concrete), drawn as a faint rectangle with a black outline.
- `anchor_point`: tuple[float, float] - bottom-left corner
- `size`: tuple[float, float] - (x_size, z_size)
- `color`: str = '#6D645E'
- `orientation_angle`: float = 0
- `label`: str | None = None
- `v_anchor`: float | None = None - default 0.01
- `height`: float | None = None - default 0.30

### GardenHouse
**YAML type:** `garden_house`
- `anchor_point`: tuple[float, float] - bottom-left corner
- `size`: tuple[float, float] - (x_size, z_size)
- `height`: float = 2.5
- `color`: str = '#DEB887' - walls
- `roof_color`: str = '#8B4513'
- `orientation_angle`: float = 0
- `label`: str | None = None

---

## Color Palette Suggestions

- **Vegetation:** `#228B22` forest green (tree default), `#90EE90` light green (shrub default), `#556B2F` dark olive (hedge default), `#3CB371`, `#32CD32`
- **Wood / earth:** `#8B4513` saddle brown, `#D2B48C` tan, `#DEB887` burlywood, `#654321` dark brown
- **Stone / gravel:** `#696969` dim gray, `#A9A9A9` dark gray, `#D3D3D3` light gray
- **Water:** `#4682B4` pond, `#87CEEB` fountain, `#00BFFF` pool, `#2F4F4F` pond edge
- **Bloom:** `#FFB6C1` light pink, `#FF69B4` hot pink, `#E6E6FA` lavender, `#ADD8E6` light blue, `#FFD700` gold, `white`

## Best Practices

1. **Layout:** draw perimeter elements first (fences, hedges, retaining walls), then large trees and structures, then paths, beds and shrubs.
2. **Scale:** use the same `scale_denominator` across site plans (1:50 for detailed gardens, 1:100 for larger sites). For alignment, set `grid_major_step` / `grid_minor_step` in the layout.
3. **Species:** use the database keys to get consistent sizes, colors and bloom periods; override single values explicitly.
4. **Bloom planning:** give bloom dates as 'dd.mm' (e.g. '15.04'). Use `show_bloom` on separate floor plans to compare seasons (see `vegetation_demo.yml`).
5. **Labels:** set `label_color` (and `id_color: 'gray'` for subtle IDs) per class or via `Vegetation`, otherwise labels are not drawn.
6. **Reuse:** keep shared elements in `reusable_elements` and pull them in with `inherited_elements`. Use groups or group templates for repeated arrangements (see [Groups](element-parameters-reference.md#groups)).
7. **Output:** `project.dpi: 300` gives print quality. The generated Markdown report lists the vegetation with species, height, bloom period and bloom color, and the counts of the other elements.
