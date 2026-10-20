# Texture Tiling Guide

## Overview

The `texture_scale` parameter enables realistic texture repeating/tiling in the 3D (glTF) export instead of stretching a single texture across entire surfaces. This creates more realistic materials like brick walls, tiled floors, and wood grain patterns. It has no effect on 2D rendering.

## How It Works

### Without Tiling (texture_scale Not Set)
For box-shaped elements (walls, doors, storage, floors, ...) textures stretch to fit each face:
- A 5m wall gets one stretched texture per face
- UV coordinates range from 0.0 to 1.0

**Note**: Non-box geometry (roofs, gable ends, sloped/complex meshes) does not stretch; it uses per-face planar UVs with an implicit `texture_scale` of 1.0 (one tile per meter).

### With Tiling (texture_scale Set)
When `texture_scale` is set, textures repeat based on physical dimensions:
- `texture_scale: 0.2` means one texture tile is 0.2m × 0.2m
- A 1.8m window with 0.2m tiles repeats 9 times (1.8 ÷ 0.2 = 9)
- UV coordinates scale accordingly (0.0 to 9.0 for 9 repeats)

**Note**: Windows use tiled textures by default (`texture_scale: 0.2`). To override this for a specific window, explicitly set `texture_scale: null` (stretch) or a different value.

### Element Defaults

| Element (YAML type) | Default texture_scale | Settable in YAML |
|---------------------|-----------------------|------------------|
| `window` | 0.2 | yes |
| `wall`, `wallnd`, `door`, `floor`, `ceiling`, `generic_storage`, `storage40`, `storage60` | None (stretch) | yes |
| `ground` | 0.5 | no (fixed) |
| `deck` | 0.6 | no (fixed) |
| `surface` | 1.0 | no (fixed) |
| `garden_path` | 1.5 | no (fixed) |
| roofs (`gable_roof`, `hipped_roof`, `single_slope_roof`, octant roofs) | 3.0 | no (fixed) |

External `model_*` elements accept `texture_scale`, but a loaded model file keeps its own UVs, so the value has no effect on them.

**Limitation**: walls containing embedded doors/windows (openings) always get stretched 0–1 UVs; `texture_scale` is ignored for them.

## Usage

### YAML Configuration

Add `texture_scale` to an element that accepts it (see table above):

```yaml
elements:
  # Window with default tiling (0.2m tiles - automatic for windows)
  - type: window
    anchor_point: [2.0, 3.5]
    length: 1.8
    overall_thickness: 0.15
    orientation_angle: 0
    color: lightblue
    # No texture_scale needed - windows default to 0.2m tiles

  # Window with custom tiling (larger tiles)
  - type: window
    anchor_point: [5.0, 3.5]
    length: 2.4
    overall_thickness: 0.15
    orientation_angle: 0
    color: lightblue
    texture_scale: 0.5  # Override default: 0.5m tiles instead of 0.2m

  # Wall with brick texture (0.5m bricks)
  - type: wall
    anchor_point: [0, 0]
    length: 5.0
    thickness: 0.2
    orientation_angle: 0
    color: gray
    texture_scale: 0.5  # Each brick ~0.5m

  # Door without tiling (default - stretches to fit)
  - type: door
    anchor_point: [3.0, 0]
    doorway_width: 1.0
    door_width: 0.9
    thickness: 0.2
    # No texture_scale: texture stretches to fit
```

### Choosing texture_scale Values

| Value  | Description | Typical Use Cases |
|--------|-------------|-------------------|
| 0.1    | Fine detail | Small tiles, detailed patterns |
| 0.2    | Medium-fine | **Window panes (default for windows)**, small bricks, floor tiles |
| 0.3    | Medium      | Standard bricks, wood planks |
| 0.5    | Large       | Large tiles, stone blocks |
| 1.0    | Very large  | Big panels, large format tiles |
| None   | Stretch fit | Doors, solid colors, non-repeating textures (default for most box elements) |

## UV Coordinate Calculation

The glTF exporter (`floor_planner/gltf_exporter.py`) calculates UV repeats automatically.

Box geometry (`_generate_box_geometry_with_uvs`):

```
For each face:
  repeat_u = face_width / texture_scale
  repeat_v = face_height / texture_scale
  (texture_scale None or <= 0 → repeat_u = repeat_v = 1.0)

Example: 1.8m window × 1.5m high with texture_scale: 0.2
  repeat_u = 1.8 / 0.2 = 9.0 (texture repeats 9 times horizontally)
  repeat_v = 1.5 / 0.2 = 7.5 (texture repeats 7.5 times vertically)
```

Non-box geometry (`_generate_slope_uvs_expanded`): each triangle gets its own UV space, with U along its first edge and V perpendicular in the face plane; distances in meters are divided by `texture_scale` (1.0 if unset).

## Texture Requirements

For best results with tiling:

1. **Seamless Textures**: Use textures designed to tile seamlessly (edges match perfectly)
2. **Square Textures**: Use 1:1 aspect ratio textures (e.g., 512×512, 1024×1024)
3. **Power-of-Two Sizes**: Preferred by 3D viewers (256, 512, 1024, 2048)
4. **PNG with Alpha**: Use PNG format for glass/transparent materials

Default textures are looked up per element type in `textures/defaults/<element_type>/<element_type>.png` (then `.jpg`), with fallbacks in `textures/fallback/`.

## Example Workflow

### 1. Create Floor Plan with Tiling

```yaml
project:
  visualisation_dir: "visualisation_3d"  # required for 3D export

floor_plans:
  - title:
      text: "Living Room with Textured Walls"
    
    elements:
      # Brick wall exterior (large bricks)
      - type: wall
        anchor_point: [0, 0]
        length: 8.0
        thickness: 0.3
        color: red
        texture_scale: 0.5  # 50cm bricks
      
      # Interior wall with smaller tiles
      - type: wall
        anchor_point: [0, 5.0]
        length: 8.0
        thickness: 0.15
        color: white
        texture_scale: 0.3  # 30cm tiles
      
      # Window with glass grid pattern
      # (embedding it in the wall above would make that wall ignore texture_scale)
      - type: window
        anchor_point: [2.0, 2.5]
        length: 2.4
        overall_thickness: 0.3
        texture_scale: 0.2  # 20cm glass panes
```

### 2. Generate 3D Export

```bash
python -m floor_planner -c my_floor_plan.yml
```

Each floor plan is written to `<visualisation_dir>/<Title_With_Underscores>.gltf` (plus `.bin`), with textures copied to `<visualisation_dir>/textures/`.

### 3. View in 3D Software

Open the generated `.gltf` file in:
- **Blender**: File → Import → glTF 2.0 (.glb/.gltf)
- **Online Viewers**: [https://3dviewer.net](https://3dviewer.net), [https://gltf-viewer.donmccurdy.com](https://gltf-viewer.donmccurdy.com)

## Technical Details

### glTF Output

Tiled UVs are stored in each mesh primitive's `TEXCOORD_0` accessor. Textures are written without an explicit sampler, so viewers use the glTF default wrap mode (`REPEAT`), which makes UVs above 1.0 tile.

### Per-Face Calculation

Different box faces use appropriate dimensions:
- **Front/Back faces**: Use length × height
- **Left/Right faces**: Use thickness × height  
- **Top/Bottom faces**: Use length × thickness

## Troubleshooting

### Problem: Texture appears blurry/stretched

**Solution**: Use a tileable texture and set appropriate `texture_scale` value. For walls, check that no door/window is embedded in the wall (openings disable tiling).

### Problem: Seams visible between tiles

**Solution**: Ensure texture image is truly seamless. Many "seamless" textures still show seams.

### Problem: Texture repeats too many/few times

**Solution**: Adjust `texture_scale` value:
- Increase to get fewer repeats (larger tiles)
- Decrease to get more repeats (smaller tiles)

### Problem: Texture looks distorted

**Solution**:
1. Check texture aspect ratio (should be 1:1 for square tiling)
2. Verify physical dimensions of element match intended design
3. Try different `texture_scale` values

## Examples

See the example configurations:
- `examples/3d_visualization/tiling_demo.yml` - Side-by-side comparison
- `examples/3d_visualization/furnished_room.yml` - Furnished room with default textures

## Related Documentation

- [Element Parameters Reference](element-parameters-reference.md#texture_scale-texture-tiling) - Full texture_scale parameter documentation
- [Textures README](../textures/README.md) - Texture file requirements
- [Landscaping Guide](landscaping-guide.md) - Landscaping element textures
