# Texture Tiling Guide

## Overview

Tiling makes a texture repeat in the 3D (glTF) export instead of stretching once over a whole surface, which gives realistic brick walls, tiled floors and wood grain. It has no effect on 2D rendering.

- **Box elements** (walls, doors, windows, floors, furniture boxes, decks, ...) set the scale per face in the [`textures`](element-parameters-reference.md#textures-per-face-textures-box-elements) structure, with `scale_relative` or `scale_meters`.
- **Non-box geometry** (roofs, gable ends, sloped meshes) uses `texture_scale`.

## Box Elements

### Two ways to set the scale

| Key | Meaning | Use when |
|-----|---------|----------|
| none | stretched: one texture per face (UV 0…1) | doors, solid colours, non-repeating images |
| `scale_relative: r` | `r` repeats along each face axis (UV 0…r), whatever the face size | the element should look the same when resized |
| `scale_meters: m` | one texture tile is `m` × `m` metres (UV 0…size/m) | real-world sized patterns: bricks, tiles, planks |

Example: a 1.8 m × 1.5 m face
- `scale_relative: 2` → 2 × 2 tiles (UV 0…2 × 0…2)
- `scale_meters: 0.2` → 9 × 7.5 tiles (UV 0…9 × 0…7.5)

The scale can differ per face. It is resolved like the other per-face properties: face entry → `sides` (vertical faces) → `default` → class default → stretched. The most specific level that sets either key wins, and one entry may not set both.

### Class defaults

Some elements tile by default (same effect as their former fixed `texture_scale`):

| Element (YAML type) | Class default |
|---------------------|---------------|
| `window` | `scale_meters: 0.2` |
| `ground` | `scale_meters: 0.5` |
| `deck` | `scale_meters: 0.6` |
| `surface` | `scale_meters: 1.0` |
| `garden_path` | `scale_meters: 1.5` |
| all other box elements | stretched |

A `textures` entry in YAML overrides the class default.

### Walls with openings

Walls with embedded doors/windows are tiled too. Their front/back faces and the reveals of the openings (`inside_left`, `inside_right`, `inside_top`, `inside_bottom` in `textures.extras`) use wall coordinates:
- stretched / `scale_relative: r` → position / wall size × `r`;
- `scale_meters: m` → position in metres / `m`, so the pattern continues from the wall into its reveals.

### YAML

```yaml
elements:
  # Brick wall: 0.5 m tiles outside, stretched plaster inside
  - type: wall
    anchor_point: [0, 0]
    length: 5.0
    thickness: 0.3
    textures:
      front: {texture: patio.jpg, scale_meters: 0.5}
      back:  {texture: wall.jpg}

  # Cabinet that keeps its look when resized: 2 x 2 tiles on every face
  - type: storage60
    anchor_point: [2.2, 2.6]
    length: 0.8
    textures:
      default: {texture: drawer.jpg, scale_relative: 2}

  # Window: 0.2 m tiles from the class default, no YAML needed
  - type: window
    anchor_point: [2.5, 0]
    length: 1.5
    overall_thickness: 0.3
```

### Choosing values

| `scale_meters` | Typical use |
|----------------|-------------|
| 0.1 | small tiles, detailed patterns |
| 0.2 | window panes (window default), small bricks, floor tiles |
| 0.3 | standard bricks, wood planks |
| 0.5 | large tiles, stone blocks |
| 1.0 | big panels, large format tiles |

## Non-Box Geometry (`texture_scale`)

Roofs, gable ends and other sloped meshes (`_generate_slope_uvs_expanded`) give each triangle its own UV space, with U along its first edge and V perpendicular in the face plane. Distances in metres are divided by `texture_scale` (1.0 if unset). Roofs use a fixed 3.0.

External `model_*` elements accept `texture_scale`, but a loaded model keeps its own UVs, so the value has no effect on them.

## UV Calculation (box)

`_generate_box_geometry_with_uvs` in [`gltf_exporter.py`](../floor_planner/gltf_exporter.py) expands the box to 24 vertices (4 per face) and gives each face its own UV range:

```
face size (w × h):  front/back = length × height
                    left/right = thickness × height
                    top/bottom = length × thickness

stretched / scale_relative r :  u_max = r,      v_max = r
scale_meters m               :  u_max = w / m,  v_max = h / m
```

Tiled UVs are stored in each primitive's `TEXCOORD_0`. Textures are written without an explicit sampler, so viewers use the glTF default wrap mode (`REPEAT`), which makes UVs above 1.0 tile.

## Texture Requirements

1. **Seamless textures**: edges must match when tiled
2. **Square textures**: 1:1 aspect ratio (e.g. 512×512, 1024×1024)
3. **Power-of-two sizes**: preferred by 3D viewers (256, 512, 1024, 2048)
4. **PNG with alpha** for glass/transparent materials

Which texture is used is set by `textures` or, by default, by the `map_Kd` of `models/procedural/<element_type>/<element_type>.mtl` (see [texture-material-system.md](texture-material-system.md#texture-lookup)).

## Viewing

```bash
python -m floor_planner -c my_floor_plan.yml
```

Each floor plan is written to `<visualisation_dir>/<Title_With_Underscores>.gltf` (plus `.bin`), with textures copied to `<visualisation_dir>/textures/`. Open it in Blender (File → Import → glTF 2.0) or an online viewer such as [https://gltf-viewer.donmccurdy.com](https://gltf-viewer.donmccurdy.com).

## Troubleshooting

- **Texture stretched** — no scale is set (stretched is the default for most boxes); add `scale_meters` or `scale_relative`.
- **Seams between tiles** — the image is not seamless.
- **Too many / too few repeats** — `scale_meters`: increase for larger tiles; `scale_relative`: decrease for fewer repeats.
- **Distorted texture** — the image is not square, or the element's dimensions differ from what you intended.

## Examples

- `examples/3d_visualization/face_textures_demo.yml` - per-face textures, both scale forms, walls with openings
- `examples/3d_visualization/furnished_room.yml` - furnished room with default textures

## Related Documentation

- [Element Parameters Reference](element-parameters-reference.md#textures-per-face-textures-box-elements) - the `textures` parameter
- [Texture and Material System](texture-material-system.md) - texture lookup and materials
- [Textures README](../textures/README.md) - texture file requirements
