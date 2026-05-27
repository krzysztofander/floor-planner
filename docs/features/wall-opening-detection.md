# Wall Opening Detection Feature

## Overview
The wall opening detection feature automatically generates realistic 3D wall geometry with cutouts for embedded doors and windows. When a door or window is positioned within a wall, the wall mesh is automatically subdivided to create a proper opening, making the 3D visualization more realistic.

## How It Works

### Detection Algorithm
The system automatically detects when a door or window is embedded in a wall by checking:

1. **Orientation alignment**: The opening must be parallel to the wall (within 5° tolerance) or 180° opposite
2. **Position overlap**: The opening must be positioned along the wall's length
3. **Face alignment**: The opening must be at or near one of the wall's faces (front or back)
4. **Tolerance**: Position checking uses a 0.1m (10cm) tolerance to handle floating-point precision

### Geometry Generation
When an opening is detected:

1. **Grid Subdivision**: The wall face is subdivided into a grid based on opening boundaries
   - Horizontal divisions: wall edges + opening top/bottom positions
   - Vertical divisions: wall edges + opening left/right positions

2. **Cell-based Triangulation**: Each grid cell is checked:
   - If the cell center is inside an opening → skip (create hole)
   - If the cell is outside all openings → generate two triangles

3. **Complete Mesh**: The system generates:
   - Front face with holes (subdivided, cutout areas removed)
   - Back face with holes (similarly processed)
   - Side faces (top, bottom, left, right edges)
   - Inner edges around openings (for structural detail)

## Usage

No special configuration needed! Just position doors and windows in your walls as usual:

```yaml
elements:
  # Wall
  - type: wall
    id: front_wall
    anchor_point: [0, 0]
    orientation_angle: 0
    length: 5
    thickness: 0.2
    color: gray  # Must be visible (not 'invisible')
  
  # Door positioned in the wall
  - type: door
    id: main_door
    anchor_point: [1.5, 0]  # 1.5m along the wall
    orientation_angle: 0     # Same orientation as wall
    doorway_width: 1.0
    door_width: 0.9
    thickness: 0.2           # Match wall thickness
    to_the_right: false
  
  # Window positioned in the wall
  - type: window
    id: main_window
    anchor_point: [3.0, 0]  # 3.0m along the wall
    orientation_angle: 0     # Same orientation as wall
    length: 1.5
    overall_thickness: 0.2   # Match wall thickness
```

## Requirements

For proper opening detection:

1. **Wall visibility**: Wall must not have `color: invisible` (invisible walls are excluded from 3D export)
2. **Matching orientation**: Door/window orientation should match wall orientation (±5°)
3. **Matching thickness**: Door/window thickness should match wall thickness for best results
4. **Proper positioning**: Opening anchor point should be on the wall's face

**Note**: Doors and windows with `color: invisible` will still create holes in walls! They won't be rendered in 2D or exported in 3D, but their geometry is used to cut openings in adjacent walls. This is useful when you want the opening effect without the door/window visual element.

## Export Messages

During 3D export, you'll see messages like:
```
Exporting floor plan to 3D: visualisation_3d/floor_plan.obj
  Wall front_wall has 1 embedded opening(s)
  Wall back_wall has 2 embedded opening(s)
```

This confirms that openings were detected and wall geometry was modified.

## Technical Details

### Files Modified
- `floor_planner/wall_openings.py` - Opening detection and geometry generation
- `floor_planner/obj_exporter.py` - Integration with OBJ export
- `floor_planner/elements/basic.py` - Wall element support
- `floor_planner/elements/door.py` - Door element support

### Coordinate System
The system uses a local coordinate system for each wall:
- **X-axis**: Along wall length (from anchor point)
- **Y-axis**: Along wall thickness (perpendicular to wall)
- **Z-axis**: Vertical (height)

Openings are transformed into this local space for geometric calculations.

### Tolerance Parameters
- **Position tolerance**: 0.1m (10cm) - for checking if opening is at wall face
- **Angle tolerance**: 5° - for checking orientation alignment
- **Grid subdivision**: Automatic based on opening positions

### Performance
- Wall without openings: 8 vertices, 12 triangles (simple box)
- Wall with 1 opening: ~36 vertices, ~50+ triangles (subdivided mesh)
- Wall with 2 openings: ~60+ vertices, ~80+ triangles

## Examples

See `examples/3d_visualization/wall_opening_test.yml` for a complete example demonstrating:
- Front wall with door
- Back wall with window
- Side walls without openings

See `examples/test_invisible_openings/` for a test demonstrating:
- Walls with invisible doors and windows
- Invisible openings still create holes in walls
- Only walls are exported to 3D (no door/window objects)

## Limitations

1. **Single-face openings**: Currently supports openings on front or back face only
2. **Rectangular openings**: Only rectangular cutouts (doors and windows)
3. **Non-overlapping**: Overlapping openings may produce unexpected results
4. **Parallel alignment**: Openings must be parallel to wall (perpendicular not supported)

## Future Enhancements

Potential improvements:
- Support for partially embedded openings (openings extending beyond wall edges)
- Support for circular/arched openings
- Support for multiple overlapping openings
- Texture coordinate preservation across subdivided mesh
- Inner wall edge geometry (reveal depth) for more realistic openings
