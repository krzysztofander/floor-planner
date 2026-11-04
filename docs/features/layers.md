# Layers

Elements of all kinds (walls, furniture, installations) are usually defined once, in one YAML file. Some drawings should show only part of them, e.g. only the walls, or the walls in a light shade under the electrical installation. Layers filter and restyle elements per floor plan; the 2D drawing and the 3D export are filtered separately.

## Usage

Every element belongs to one layer. A floor plan's `layers` has a `2d` section (layers drawn, with their 2D modifiers) and/or a `3d` section (layers exported to the glTF):

```yaml
reusable_elements:
  house: "house.yml"

floor_plans:
  - title: {text: "All elements", font_size: 14}
    inherited_elements: [house]                     # no layers: everything, in 2D and 3D

  - title: {text: "Electric", font_size: 14}
    inherited_elements: [house]
    layers:
      2d:                                           # layer name -> 2D modifiers (or nothing)
        construction: {force_color: grey, alpha: 0.3}
        electric: {z_order: 1, force_color: red}
      3d: [construction, electric]                  # layers exported to 3D

  - title: {text: "Walls", font_size: 14}
    inherited_elements: [house]
    export_3d: false                                # no glTF for this floor plan
    layers:
      2d:
        construction:
```

| `layers` | 2D drawing | 3D export |
|----------|------------|-----------|
| not given | everything | everything |
| `2d` only | the `2d` layers | everything |
| `3d` only | everything (not restyled) | the `3d` layers |
| `2d` and `3d` | the `2d` layers | the `3d` layers |

`layers` must contain `2d` and/or `3d`; an empty `layers`, `2d` or `3d`, any other key and the former list form (`- name: ...`) raise `ValueError`. Only the `2d` layers are restyled: to restyle every layer, list them all under `2d`.

`export_3d: false` on a floor plan skips its 3D export (default `true`), e.g. for 2D-only sheets that would otherwise write another copy of the same model.

Floor plans that show the same elements with different layers share them through `reusable_elements` / `inherited_elements`. Example: [tests/layers/project_main.yml](../../tests/layers/project_main.yml).

### 2D modifiers

Each entry of `2d` is a layer name (built-in or any name used by an element's `layer`) with optional modifiers:

| Key | Type | Default | Meaning |
|-----|------|---------|---------|
| `z_order` | int 0–8 | 0 | layers with a higher value are drawn on top; within one value elements keep their own order (`v_anchor`). Several layers may share a value |
| `force_color` | colour | none | colour of all lines, edges, fills and texts of the layer (any matplotlib colour, e.g. `grey`, `'#336699'`, `[0.2, 0.2, 0.6]`) |
| `alpha` | number 0–1 | 1 | multiplies the opacity of the layer's lines, edges, fills and texts |

White and fully transparent colours are never changed by `force_color` or `alpha`: white fills cover what is under them (the hole a door cuts in its wall, the white area of furniture). Texts of all layers (labels, IDs, dimensions) are drawn above everything, at level 9.

A name in `2d` or `3d` that is not built-in and that no element of the floor plan uses prints a warning (probably a typo). Invalid entries raise `ValueError`. Each `3d` entry is just a name, with no modifiers.

### Element layer

Each element type has a default layer:

| Layer | Element types |
|-------|---------------|
| `construction` | walls, windows, doors (procedural and `model_*`, including `glass_door`, `solid_glass_door`, composite doors and windows), `floor`, `ceiling` |
| `furniture` | furniture, appliances, beds, storage (`generic_storage`, `storage40/60`, `tabletop`), kitchen and bathroom fixtures, `tv`, `fish_tank`, external furniture models |
| `vegetation` | `tree`, `shrub`, `hedge`, `lawn`, `model_leafy_tree`, `model_leafy_shrub_1` |
| `electric` | `power_outlet`, `electrical_cable`, `ground_cable`, `switch`, lamps, `led_strip` |
| `water` | `generic_tank` |
| `roof` | roofs, roof octants, gable ends |
| `default` | everything else: landscaping (paths, fences, decks, ground, structures, glass panels, greenhouse), annotations (`dimension_arrow`, `text_box`), `line`, `polygon`, `circle` , other elements |

Any element takes an optional `layer` parameter that puts it on another layer, built-in or custom:

```yaml
- type: generic_storage        # a chimney drawn with the walls
  layer: construction
- type: glass_door             # a shower door drawn with the furniture
  layer: furniture
- type: line
  layer: measurements          # custom layer
```

`group` and `room` are containers and have no layer (a `layer` key on them is ignored); their children have their own layers. A container is always drawn (e.g. the room label, its texts at level 9) and exported. A composite element (`composite_*`) puts all its parts on its own layer (`addToList()` sets it), whatever their own default.

### 3D export

Each floor plan is exported to its own folder:

```
<visualisation_dir>/<name>/<name>.gltf   (+ .bin)
<visualisation_dir>/<name>/textures/
<visualisation_dir>/<name>/camera.json
```

`<name>` is the floor plan's title with spaces and `/` replaced by `_` (`floor_plan_<index>` without a title). Floor plan names must be unique; two floor plans with the same name raise `ValueError`.

A floor plan with a `3d` section exports only the elements of those layers; floor plans with `export_3d: false` are not exported.

A wall gets an opening from every door and window that is exported with it, whatever its layer. With a door on a layer `doors` and the walls on `construction`, `3d: [construction, doors]` cuts the openings and `3d: [construction]` exports solid walls.

## Design

- **Filter at draw / export time.** Elements are still all created and added to the floor plan, so rooms, IDs and the Markdown report do not change. `parse_layers()` returns a `FloorPlanLayers` (`layers_2d`: specs by name, `layers_3d`: names; None = no filtering), stored as `FloorPlan.layers`. `FloorPlan.get_drawn_elements()` (used by `draw_elements()`) and `get_exported_elements()` (used by `export_to_gltf()`) return containers and the elements of the listed layers.
- **Restyle the drawn artists.** Many elements set no zorder on some of their artists, or use fixed colours (sofa models, pools, trees, labels). So `draw_elements()` collects the artists each element adds to the axes and `apply_layer()` (`floor_planner/layers.py`) changes them: zorder `level × 1000 + own zorder` (level = `z_order`, or 9 for texts), and colours with `force_color` / `alpha`. No element's `draw()` knows about layers.
- **Default layer** is the class attribute `default_layer` (on `ElementBase`, overridden on base classes such as `WallND`, `Door`, `BalconyDoor`, `_RoofBase`); the YAML `layer` sets `element.layer` (`ElementBase.set_layer()`, which also sets the parts of a composite). `get_layer()` returns the one in use. The runner, `Group` and `Room` remove `layer` from the parameters before creating the element, so element constructors do not take it.
- **Openings follow the export.** The exporter only receives the exported elements, so `find_embedded_openings()` sees exactly the doors and windows that are in the glTF.
