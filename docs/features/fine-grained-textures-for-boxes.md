# Feature: fine-grained-textures-for-boxes

**Status:** Complete  
**Priority:** Medium  
**Estimated Effort:** 2 days

## Overview

Box-like elements (classes whose 3D geometry comes from `RectangularGeometry3D`) get per-face control over their look in the glTF export. Each of the six faces (`front`, `back`, `left`, `right`, `top`, `bottom`) can have its own:

- texture (or explicitly none),
- texture scale, either relative to the face size or in metres,
- diffuse colour (`Kd`),
- specular colour (`Ks`) and shininess (`Ns`),
- opacity (`d`).

The settings come from a new structured YAML parameter `textures`. A `default` entry applies to all faces, and a `sides` entry applies to the four vertical faces. An `extras` entry holds faces with arbitrary names for elements whose geometry has more than six faces; walls use it for the reveals of openings (`inside_left`, `inside_right`, `inside_top`, `inside_bottom`). Anything not set falls back to the element class's built-in defaults and then to the element type's `.mtl` file. With no `textures` block, an element looks exactly as it does today.

For box elements the new parameter replaces `texture_scale`.

## Motivation

Today the look is fixed per element *type*. One `.mtl` per type (`models/procedural/<type>/<type>.mtl`) gives every face of every instance the same texture and lighting, and `texture_scale` is a single number for the whole element. Real objects are not like that. A wall has brick on the outside and plaster inside, a cabinet has a wooden top and painted sides, and glass can be partly transparent. This feature is also the first step towards selecting textures per object.

## Decisions (from review)

| # | Topic | Decision |
|---|-------|----------|
| 1 | Default scale | No scale set → **stretched**, as today (one texture per face). Two ways to set a scale: `scale_relative` (repeats relative to the face size, so the look survives resizing) and `scale_meters` (tile size in metres). |
| 2 | Parameter name | `textures` |
| 3 | `texture_scale` on box classes | **Removed** from the box classes (YAML parameter and fixed values in code). Where a class uses a fixed scale today (`window`, `ground`, `deck`, `surface`, `garden_path`), the same effect moves into a class-level default `textures` spec. |
| 4a | Opacity | Supported; `opacity` 0.0–1.0, default 1.0 (100 %) |
| 4b | `sides` group | Supported: face → `sides` → `default` |
| 4c | `texture: null` | Supported: colour only, no texture, even if the `.mtl` has `map_Kd` |
| 4d | Composites | Decided one by one. `composite_glass_door` passes `textures` to its `solid_glass_door` leaf. |
| 5 | `scale_relative` meaning | Confirmed: `2.0` = 2 repeats along *each* face axis (2 × 2 = 4 tiles), on every face regardless of its size. |
| 6 | `opacity` fallback | Confirmed: falls back to the `.mtl`'s `d` before the built-in 1.0, like every other property. |
| 7 | Special faces | New `extras` entry: any number of faces with arbitrary names, same entry format. `wall` / `wallnd` read `inside_left`, `inside_right`, `inside_top`, `inside_bottom` for the reveals of their openings. Other elements may read other names later; names an element does not read are ignored. |

## Current State (what the code does now)

| Topic | Today | Where |
|-------|-------|-------|
| Box geometry | 8 vertices, 12 triangles; `face_groups` = `bottom` [0,1], `top` [2,3], `front` [4,5], `back` [6,7], `right` [8,9], `left` [10,11] (+ `sides`, `all`) | `RectangularGeometry3D.generate_vertices_and_indices()` in [geometry_3d.py](../../floor_planner/geometry_3d.py) |
| Box UVs | expanded to 24 vertices (4 per face, order bottom, top, front, back, right, left); `u,v = size / texture_scale`, or 0–1 per face (stretched) when `texture_scale` is `None` | `_generate_box_geometry_with_uvs()` in [gltf_exporter.py](../../floor_planner/gltf_exporter.py) |
| Walls with openings | different mesh from `generate_wall_with_openings()`, same face names + `opening_edges`; UVs = local position / face size, clamped to 0–1 (stretched), `texture_scale` ignored | `_generate_wall_opening_uvs()` |
| Material | **one primitive, one material per element**; material built from the type's `.mtl` and cached **per element type** | `_add_procedural_element()`, `_get_default_material()` |
| `texture_scale` on boxes | YAML parameter on `wall`, `wallnd`, `door`, `floor`, `ceiling`; fixed in code for `window` 0.2, `ground` 0.5, `deck` 0.6, `surface` 1.0, `garden_path` 1.5 | element constructors |

Elements affected: the 44 registered types that use the plain `RectangularGeometry3D` box. Their classes inherit `RectangularElement` or `SurfaceElement`:

`basin bathtub ceiling chair deck desk dining_table dishwasher door double_bed double_sink dryer fence fish_tank floor freezer fridge garden_house garden_path generic_storage ground hedge lawn oval_pool pergola raised_bed rect_pool retaining_wall shower single_bed single_sink sofa solid_glass_door storage40 storage60 stovetop surface tabletop toilet tv wall wallnd washing_machine window`

Not affected:
- `greenhouse` inherits `RectangularGeometry3D` but overrides the geometry (not a box).
- Roofs, gable ends, circular elements and external models keep `texture_scale` / their `.mtl` as today.

## Design

### Face names

Faces are named for the box in its own local frame, i.e. as it is with `orientation_angle = 0` and before placement. Local X runs along `length`, local Z along `thickness`, Y is up. These names already exist as `face_groups` keys.

| Face | Local position | Outward normal (angle 0) | In the 2D plan (angle 0) |
|------|----------------|--------------------------|--------------------------|
| `front` | z = 0 (the anchor side of the thickness) | −Z | lower edge |
| `back` | z = thickness | +Z | upper edge |
| `left` | x = 0 (the anchor end of the length) | −X | left edge |
| `right` | x = length | +X | right edge |
| `top` | y = v_anchor + height | +Y | — |
| `bottom` | y = v_anchor | −Y | — |

Groups:
- `sides` = `front`, `back`, `left`, `right`;
- `default` = all six faces and every face named in `extras`.

#### Extra faces of walls with openings

A wall with embedded doors or windows gets four reveal strips per opening (generated by `generate_wall_with_openings()`). They are named in the wall's local frame, like the box faces:

| Extra face | Strip | Faces towards | Size (u × v) |
|------------|-------|---------------|--------------|
| `inside_left` | jamb at the opening's start (the side nearer the wall's `left` end, x = `start_x`) | +X, into the opening | thickness × opening height |
| `inside_right` | jamb at the opening's end (x = `end_x`) | −X, into the opening | thickness × opening height |
| `inside_top` | head (underside of the lintel) | down | opening width × thickness |
| `inside_bottom` | sill (for doors: the strip at floor level) | up | opening width × thickness |

All openings of one wall share these four entries.

The faces rotate with the element. Animated doors generate their geometry in local space, so the names hold for them too.

### YAML

```yaml
- type: generic_storage
  anchor_point: [1.0, 2.0]
  length: 2.0
  thickness: 0.6
  textures:
    default:                        # all faces
      texture: generic_storage_oak.jpg
      scale_relative: 2.0           # 2 x 2 repeats on every face, whatever its size
      specular: [0.2, 0.2, 0.2]
    sides:                          # front, back, left, right
      diffuse: [0.9, 0.85, 0.8]
    top:
      texture: plain_named/brown-wood-table.jpg
      scale_meters: 0.3             # one tile per 0.3 m
      shininess: 80
    bottom:
      texture: null                 # colour only
      diffuse: [0.3, 0.3, 0.3]
```

Keys of `textures`: `default`, `sides`, the six face names and `extras`.

`extras` is a mapping from free face names to entries:

```yaml
  textures:
    default:
      texture: surface/white-grayish-plain.jpg
    extras:
      inside_left:   {texture: plaster.jpg}
      inside_right:  {texture: plaster.jpg}
      inside_top:    {texture: plaster.jpg}
      inside_bottom: {texture: window_sill.jpg, scale_meters: 0.3}
```

Keys of each entry (in `default`, `sides`, a face, or `extras`), all optional:

| Key | Type | Meaning | `.mtl` equivalent |
|-----|------|---------|-------------------|
| `texture` | str or `null` | texture file name, searched like any `map_Kd` reference (next to the element type's `.mtl`, then in `textures/`); `null` = no texture | `map_Kd` |
| `scale_relative` | float > 0 | number of texture repeats along each axis of the face; `1.0` = stretched once over the face, `2.0` = 2 × 2 = 4 tiles | — |
| `scale_meters` | float > 0 | size of one texture tile in metres; repeats = face size / value | — |
| `diffuse` | [r, g, b], 0–1 | base colour, multiplies the texture | `Kd` |
| `specular` | [r, g, b], ≥ 0 | specular colour | `Ks` |
| `shininess` | float ≥ 0 | specular exponent | `Ns` |
| `opacity` | float 0–1 | 1.0 = opaque (100 %); < 0.99 enables blending | `d` (`Tr` = 1 − d) |

Validation, done when the element is created, raises `ValueError` for:
- unknown keys or face names (outside `extras`);
- wrong types or out-of-range values;
- `scale_relative` and `scale_meters` set in the same entry;
- an `extras` name that is empty or clashes with `default`, `sides` or a box face name.

Names inside `extras` are otherwise free. Each entry is validated like any other, and names the element does not read are ignored without error.

Numeric values accept variables and arithmetic like other numeric parameters (`scale_meters: tile * 2`), and `texture` accepts `{var}` substitution.

### Resolution rules (per face, per property)

The levels, from most to least specific:

```
box face:    face entry    →  sides (vertical faces only)  →  default  →  class default  →  .mtl  →  built-in
extra face:  extras.<name>                                 →  default  →  class default  →  .mtl  →  built-in
```

Extra faces skip `sides`, because `sides` means the four outer vertical faces of the box. The class default may also contain `extras`.

| Property | Built-in (nothing set anywhere) |
|----------|---------------------------------|
| `texture` | none (colour only) |
| scale | stretched (`scale_relative: 1.0`) |
| `diffuse` | built-in colour (0.8 grey; wall 0.95, door brown, window light blue) |
| `specular` | none |
| `shininess` | roughness 0.8 |
| `opacity` | 1.0 |

Details:
- **Explicit `null` stops the search.** A key that is present with value `null` counts as set. This is how `texture: null` overrides a `map_Kd` from the `.mtl`. For the other keys `null` is not allowed, so validation rejects it.
- **The scale is one property** with two forms. The most specific level that sets either `scale_relative` or `scale_meters` wins. A face with `scale_meters` therefore overrides a `default` with `scale_relative`.
- **Class default** is a class attribute (e.g. `_default_textures`) in the same format as the YAML. It replaces the fixed `texture_scale` values:

  | Class | `_default_textures` | Same effect as today |
  |-------|--------------------|----------------------|
  | `Window` | `{'default': {'scale_meters': 0.2}}` | `texture_scale=0.2` |
  | `Ground` | `{'default': {'scale_meters': 0.5}}` | `texture_scale=0.5` |
  | `Deck` | `{'default': {'scale_meters': 0.6}}` | `texture_scale=0.6` |
  | `GenericSurface` | `{'default': {'scale_meters': 1.0}}` | `texture_scale=1.0` |
  | `GardenPath` | `{'default': {'scale_meters': 1.5}}` | `texture_scale=1.5` |

- **The `.mtl` has no scale.** Opacity comes from `d`, or `1 − Tr`.
- **`alphaMode: BLEND`** is set when the resolved opacity is < 0.99, or when the element has `alpha_mode = "BLEND"` (window, shower, fish tank), as today. Because materials are per face, one face can be transparent and the others opaque.

### UV formulas (per face)

For a face of size `w × h` (in metres, along the face's u and v axes):

| Scale | u range | v range |
|-------|---------|---------|
| none (stretched) / `scale_relative: r` | 0 … r | 0 … r |
| `scale_meters: m` | 0 … w / m | 0 … h / m |

For extra faces, `w × h` is the strip size from the table above. With openings, the front and back faces are the full wall face with holes. Their UVs are the local position divided by the full face size (stretched), multiplied by `r`, or divided by `m`.

Stretched is `r = 1`, which is today's `texture_scale = None` behaviour. `scale_meters` is today's `texture_scale` behaviour.

### Technical changes

**New module `floor_planner/face_textures.py`**
- `BOX_FACES = ('front', 'back', 'left', 'right', 'top', 'bottom')`, `SIDE_FACES = ('front', 'back', 'left', 'right')`.
- `FaceSpec` (dataclass): one entry. An `UNSET` sentinel tells "not given" apart from an explicit `null`.
- `FaceTextures`: `from_yaml(data: dict | None)` with validation; keeps the `default`, `sides`, per-face entries and `extras: dict[str, FaceSpec]`.
- One resolver for both kinds of face: `resolve_face(name, ...)`. `name` is a box face or an extra name, and the chain (with or without `sides`) is chosen from it. A plain dict for `extras` keeps the API simple, so no `**kwargs` are needed, although they were allowed for this.
- `ResolvedFace` (frozen, hashable): `texture_path | None`, `scale_mode` ('relative' | 'meters'), `scale_value`, `diffuse`, `specular`, `shininess`, `opacity`. The material part (everything except the scale) doubles as the material cache key.
- `resolve_face(name, yaml_spec, class_spec, mtl_props, mtl_dir) -> ResolvedFace`.

**`RectangularGeometry3D` ([geometry_3d.py](../../floor_planner/geometry_3d.py))**
- `_init_face_textures(textures: dict | None)` validates and stores `self.face_textures`. The mixin has no `__init__`, so `RectangularElement.__init__` and `SurfaceElement.__init__` call it.
- `_default_textures: dict | None = None` class attribute (the class default level).

**Element constructors**
- `RectangularElement` / `SurfaceElement` ([element.py](../../floor_planner/elements/element.py)):
  - add `textures: dict | None = None`;
  - **remove `texture_scale`**, and call `Element.__init__` without it, so it stays `None` on boxes.
- **`texture_scale` removed from box classes:**
  - `WallND` (and `Wall`), `Door` (and `SolidGlassDoor`), `Floor`, `Ceiling`: drop the parameter and its docstring;
  - `Window`, `Ground`, `Deck`, `GenericSurface`, `GardenPath`: drop the fixed value and set `_default_textures` (table above).
- **Every box leaf class** (44 types, plus intermediate bases such as `WallND`, `MultiBed`, `GenericStorage`, `CircularVegetation` where relevant) gets `textures: dict | None = None` and passes it on. There are no `**kwargs`, so this is mechanical and can be scripted like the earlier `id` change. Docstrings get a `:param textures:` entry.
- `Element.texture_scale` stays for non-box elements (roofs, gable ends, circular elements).

**Composites**
- `Composite_GlassDoor` gets `textures: dict | None = None` and passes it to its `SolidGlassDoor` leaf. Its `AluFrame` is an external model.
- `Composite_WindowDouble` and `Composite_WindowDoorDouble` build only external models, so they get no `textures` parameter.
- `Room` passes `floor`/`ceiling` definitions through unchanged, so `textures` works there without extra code.

**Variable resolution ([variables.py](../../floor_planner/variables.py))**
- Remove the dead `'textures'` entry from the string-field list.
- Add resolution for the new field:
  - `scale_relative`, `scale_meters`, `shininess`, `opacity` and colour components through `resolve_constants`;
  - `texture` through `resolve_string_param`.

**glTF export ([gltf_exporter.py](../../floor_planner/gltf_exporter.py))**
- Split `_get_default_material(element)`:
  - `_read_procedural_mtl(element_type)` → parsed best material plus the `.mtl` folder, cached per type;
  - `_get_procedural_material(element_type, resolved, alpha_mode)` → glTF material, cached by `(element_type, material part of resolved, alpha_mode)`. Elements with identical settings share a material, as today.
- `_generate_box_geometry_with_uvs()`: per-face UV ranges from the resolved scale (formulas above); it no longer reads `element.texture_scale`.
- `_add_procedural_element()`:
  - resolve the six faces;
  - group faces with equal material;
  - emit **one primitive per group**: shared POSITION/NORMAL/TEXCOORD_0 accessors, one index accessor per group. A box without `textures` produces one group and one primitive, as now.
- Walls with openings:
  - group triangles by `face_groups`: the six box faces as for a box, plus the four `inside_*` groups resolved as extra faces;
  - UVs from the resolved scale: stretched = today's local position / face size; `scale_relative` multiplies it; `scale_meters` = local distance / m;
  - remove the clamp to 0–1, which is only correct for the stretched case.

**Wall openings ([wall_openings.py](../../floor_planner/wall_openings.py))**
- `generate_wall_with_openings()` splits the reveal triangles into `face_groups['inside_bottom']`, `['inside_top']`, `['inside_left']` and `['inside_right']`. The strips are emitted per opening in a fixed order (bottom, top, left, right; two triangles each), so the split is by offset.
- `face_groups['opening_edges']` stays as their union, so existing callers keep working.
- Note: the `sides` group of this mesh also contains top, bottom and the reveals, so it is **not** the box `sides`. The exporter resolves faces by their specific names only.
- `WallND` declares the extra faces it reads (e.g. `_extra_faces = ('inside_left', 'inside_right', 'inside_top', 'inside_bottom')`), which is useful for the docs and for future elements that read other `extras` names.

**Docs**
- [element-parameters-reference.md](../element-parameters-reference.md):
  - the `textures` parameter, face names, groups, `extras` and the wall `inside_*` faces, keys, resolution rules;
  - remove `texture_scale` from the box elements (wall, wallnd, door, floor, ceiling);
  - the "Element-specific defaults" table becomes the class-default table.
- [texture-tiling-guide.md](../texture-tiling-guide.md):
  - `scale_relative` / `scale_meters` for boxes; `texture_scale` only for roofs and other non-box geometry;
  - the walls-with-openings limitation removed.
- [texture-material-system.md](../texture-material-system.md): the override levels above the `.mtl`, materials per resolved face, several primitives per mesh.

### Example

```yaml
# Wall: brick outside (front), plaster inside (back), plain edges,
# plastered window reveals with a stone sill
- type: wall
  anchor_point: [0, 0]
  length: 5.0
  thickness: 0.3
  textures:
    default:
      texture: plain_named/light-gray-wall.jpg
    front:
      texture: brick.jpg
      scale_meters: 0.5
      specular: [0.05, 0.05, 0.05]
    back:
      texture: surface/white-grayish-plain.jpg
    extras:
      inside_left:   {texture: surface/white-grayish-plain.jpg}
      inside_right:  {texture: surface/white-grayish-plain.jpg}
      inside_top:    {texture: surface/white-grayish-plain.jpg}
      inside_bottom: {texture: window_sill.jpg, scale_meters: 0.3}

# Glass door with a frosted, half-transparent leaf
- type: composite_glass_door
  anchor_point: [2, 0]
  doorway_width: 1.0
  door_width: 0.9
  thickness: 0.1
  textures:
    default:
      opacity: 0.5
      diffuse: [0.9, 0.95, 1.0]
```

## Implementation Plan

### Phase 1: Data structure
- [x] `floor_planner/face_textures.py`: `FaceSpec` (with `UNSET`), `FaceTextures.from_yaml()` with validation, `ResolvedFace`, `resolve_face()`
- [x] `RectangularGeometry3D._init_face_textures()` and `_default_textures`; `RectangularElement` / `SurfaceElement` accept `textures`, drop `texture_scale`
- [x] Add `textures` to the 44 box leaf classes and their intermediate bases (script, as for `id`); docstrings
- [x] Remove `texture_scale` from `WallND`, `Door`, `Floor`, `Ceiling`; replace the fixed values in `Window`, `Ground`, `Deck`, `GenericSurface`, `GardenPath` with `_default_textures`
- [x] `Composite_GlassDoor` passes `textures` to `SolidGlassDoor`
- [x] Variable resolution for `textures` in `variables.py`; remove the dead `'textures'` string field

### Phase 2: Export of simple boxes
- [x] Split `_get_default_material()` into `.mtl` reading and material building with an override-aware cache key (incl. opacity → alpha/BLEND)
- [x] Per-face UVs from the resolved scale in `_generate_box_geometry_with_uvs()`
- [x] Per-face material groups → several primitives in `_add_procedural_element()`
- [x] Missing `texture` file → error naming the element and face (same behaviour as an unresolved `map_Kd`)

### Phase 3: Walls with openings
- [x] `generate_wall_with_openings()`: split the reveals into `inside_bottom` / `inside_top` / `inside_left` / `inside_right` face groups (keep `opening_edges` as the union)
- [x] `WallND._extra_faces`; resolve the `inside_*` faces through `extras` → `default` → …
- [x] Group triangles by face into primitives, as for boxes
- [x] Scale-aware UVs in `_generate_wall_opening_uvs()` (reveal strip sizes from the table), no clamping

### Phase 4: Integration & docs
- [x] `examples/3d_visualization/face_textures_demo.yml` and a Makefile target in `extras`. Contents:
  - a wall with brick/plaster, with and without openings, with `extras` reveals (incl. a door, whose `inside_bottom` is at floor level);
  - a cabinet with a different top and `texture: null` bottom;
  - a resized pair of boxes using `scale_relative`;
  - a glass door with opacity.
- [x] Add one `textures` use to `tests/all_elements` so `make tests` covers it
- [x] Update the three docs listed above

## Implementation Notes

Details settled during implementation (where the plan left room, or a literal reading would have changed existing output):

- **Reveal UVs keep wall coordinates.** Today the reveals (`opening_edges`) are mapped with wall-normalized coordinates (position / wall length, height or thickness), not per strip. To keep walls without `textures` identical, stretched / `scale_relative` reveals use the same wall-normalized coordinates × `r`. `scale_meters` reveals use position in metres / `m`, so the pattern continues from the wall faces into the reveals. The strip sizes in the table above are therefore informational only.
- **Clamp only in relative mode.** UVs of walls with openings are clamped to `0…r` for stretched / `scale_relative` (identical to today's 0–1 clamp at `r = 1`), and not clamped for `scale_meters`.
- **Opacity from `.mtl` as parsed today.** The shared `.mtl` parser stores `d` and `Tr` in the same field. Changing that would alter third-party models that use `Tr` (e.g. `master_bed`), so the parser is unchanged; no procedural `.mtl` uses `Tr`.
- **Material names.** The first material created for a type is `<type>_material`, further looks `<type>_material_<n>`, in order of creation. With overrides, the plain `.mtl` look can therefore get a suffixed name.
- **The black `Kd` → white rule** (black diffuse with a texture shows the texture) applies only to `Kd` from the `.mtl`; a `diffuse` set in YAML is used as given.
- **Non-box elements** (roofs, circular elements, greenhouse) resolve their single material through the same code with no overrides.
- **Missing texture** named in `textures` stops the export (`WarnMsg`), like an unresolved `map_Kd`: `Texture 'x.jpg' referenced by textures.top of element 'cabinet_1' not found`.

## Testing Strategy

There is no pytest suite; verification uses the Makefile projects run in a scratch copy (outputs land in the repo):

1. **Validation.** A short script builds elements with valid and invalid `textures` specs:
   - unknown face or key;
   - both scale keys in one entry;
   - an `extras` name that clashes with a face name, or an invalid entry inside `extras`;
   - `scale_meters: 0`, `opacity: 1.5`, a colour with 2 values, `diffuse: null`;
   - a missing texture file.

   Each must give the expected error.
2. **No-spec regression (must be identical).** Compare glTF from before and after for all 27 projects. Without `textures`, these must not change:
   - materials (texture file, factors, alpha, extensions);
   - primitive counts;
   - UVs, including the five classes whose fixed `texture_scale` became `_default_textures`.
3. **Spec applied.** In the demo glTF, check:
   - each face group has its own primitive with the expected material values and textures;
   - UV ranges match the formulas;
   - identical specs share one material;
   - a resized box with `scale_relative` keeps the same UV ranges;
   - opacity < 0.99 gives `BLEND` on that face only;
   - a wall with openings has separate primitives for the four `inside_*` faces when they differ, and one shared primitive when they resolve to the same material;
   - an unread `extras` name on a non-wall element is accepted and has no effect.
4. **Visual check** of the demo in the 3D viewer: face orientation (`front`/`back`/`left`/`right` match the table above at several `orientation_angle` values), tiling, specular highlights, opacity, an animated door, and a wall with openings.

## Open Questions

None. All decisions are recorded in the Decisions table.

## References

- [texture-material-system.md](../texture-material-system.md) – current `.mtl` / texture lookup
- [texture-tiling-guide.md](../texture-tiling-guide.md) – current `texture_scale` behaviour and UV formulas
- `RectangularGeometry3D` – [geometry_3d.py](../../floor_planner/geometry_3d.py)
- `_generate_box_geometry_with_uvs`, `_add_procedural_element`, `_get_default_material` – [gltf_exporter.py](../../floor_planner/gltf_exporter.py)
- `generate_wall_with_openings` – [wall_openings.py](../../floor_planner/wall_openings.py)
