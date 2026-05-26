# Texture Tiling Guide

## Overview

The `texture_scale` parameter enables realistic texture repeating/tiling in 3D exports instead of stretching a single texture across entire surfaces. This creates more realistic materials like brick walls, tiled floors, and wood grain patterns.

## How It Works

### Without Tiling (Default for Most Elements)
By default, textures stretch to fit the entire surface:
- A 5m wall gets one stretched texture
- UV coordinates range from 0.0 to 1.0

### With Tiling (texture_scale Set)
When `texture_scale` is set, textures repeat based on physical dimensions:
- `texture_scale: 0.2` means one texture tile is 0.2m × 0.2m
- A 1.8m window with 0.2m tiles repeats 9 times (1.8 ÷ 0.2 = 9)
- UV coordinates scale accordingly (0.0 to 9.0 for 9 repeats)

**Note**: Windows use tiled textures by default (`texture_scale: 0.2`) since glass panes typically have visible grids. To override this for a specific window, explicitly set `texture_scale: null` or a different value.

## Usage

### YAML Configuration

Add `texture_scale` to any element definition:

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
| None   | Stretch fit | Doors, solid colors, non-repeating textures (walls default to this) |

## UV Coordinate Calculation

The system calculates UV repeats automatically:

```
For each face:
  repeat_u = face_width / texture_scale
  repeat_v = face_height / texture_scale

Example: 1.8m window × 1.5m high with texture_scale: 0.2
  repeat_u = 1.8 / 0.2 = 9.0 (texture repeats 9 times horizontally)
  repeat_v = 1.5 / 0.2 = 7.5 (texture repeats 7.5 times vertically)
```

## Texture Requirements

For best results with tiling:

1. **Seamless Textures**: Use textures designed to tile seamlessly (edges match perfectly)
2. **Square Textures**: Use 1:1 aspect ratio textures (e.g., 512×512, 1024×1024)
3. **Power-of-Two Sizes**: Preferred by 3D viewers (256, 512, 1024, 2048)
4. **PNG with Alpha**: Use PNG format for glass/transparent materials

## Example Workflow

### 1. Create Floor Plan with Tiling

```yaml
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
      - type: window
        anchor_point: [2.0, 0]
        length: 2.4
        overall_thickness: 0.3
        texture_scale: 0.2  # 20cm glass panes
```

### 2. Generate 3D Export

```bash
python -m floor_planner -c my_floor_plan.yml
```

### 3. View in 3D Software

Open the generated `.obj` file in:
- **Blender**: File → Import → Wavefront (.obj)
- **SketchUp**: File → Import → OBJ
- **Online Viewers**: [https://3dviewer.net](https://3dviewer.net)

## Technical Details

### OBJ File Format

Tiled UVs appear in the OBJ file like this:

```obj
# Window with texture_scale: 0.2 (1.8m wide, 1.5m high)
vt 0.000000 0.000000  # Bottom-left
vt 9.000000 0.000000  # Bottom-right (repeats 9 times horizontally)
vt 0.400000 0.000000  # For side face
vt 0.000000 0.000000
vt 0.000000 7.500000  # Top-left (repeats 7.5 times vertically)
vt 9.000000 7.500000  # Top-right
vt 0.400000 7.500000
vt 0.000000 7.500000
```

### Per-Face Calculation

Different faces use appropriate dimensions:
- **Front/Back faces**: Use length × height
- **Left/Right faces**: Use thickness × height  
- **Top/Bottom faces**: Use length × thickness

### Backwards Compatibility

Elements without `texture_scale` work exactly as before (stretch to fit).

## Troubleshooting

### Problem: Texture appears blurry/stretched

**Solution**: Use a tileable texture and set appropriate `texture_scale` value.

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
- `/examples/3d_visualization/tiling_demo.yml` - Side-by-side comparison
- `/examples/3d_visualization/furnished_room.yml` - Real-world usage

## Related Documentation

- [Element Parameters Reference](element-parameters-reference.md) - Full texture_scale parameter documentation
- [Textures README](../textures/README.md) - Texture file requirements
- [Landscaping Guide](landscaping-guide.md) - Landscaping element textures
