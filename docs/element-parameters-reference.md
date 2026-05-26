# Floor Planner Element Parameters Reference

Comprehensive parameter documentation for all non-landscaping elements in the floor_planner project.

## Table of Contents
1. [Basic Elements](#basic-elements)
2. [Doors](#doors)
3. [Electricity](#electricity)
4. [Lighting](#lighting)
5. [Info/Annotations](#infoannotations)
6. [Multipurpose/Shapes](#multipurposeshapes)
7. [Rooms](#rooms)
8. [Furniture - Storage](#furniture---storage)
9. [Furniture - Beds](#furniture---beds)
10. [Furniture - Appliances](#furniture---appliances)
11. [Furniture - Bathroom](#furniture---bathroom)
12. [Furniture - General](#furniture---general)
13. [Furniture - Decorations](#furniture---decorations)
14. [Vertical Positioning (v_anchor and height)](#vertical-positioning-v_anchor-and-height)

---

## Basic Elements

### WallND
Straight wall without dimensions. For corners of acute or obtuse angles, consider `Polygon` class.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the wall (in meters)
- `thickness`: float - thickness of the wall (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the wall; measured between X-axis and the wall in positive direction (counterclockwise); initial wall is rotated around anchor point
- `color`: str = 'black' - color to use for drawing the wall
- `label`: str | None = None - optional label for the element
- `room_edge`: bool = False - if True, this wall forms the boundary of a room (used for room validation and calculations)

### Wall
Wall with dimensions. Same as WallND, but includes a dimension arrow from the anchor point to the end of the wall when dimensions option is enabled.

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

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the window (in meters)
- `overall_thickness`: float - total thickness of the window (in meters)
- `single_line_thickness`: float = -1 - thickness of a single outer line forming window (in meters); defaults to `overall_thickness / 10` if ≤ 0
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the window
- `color`: str = 'black' - color to use for drawing the window
- `label`: str | None = None - optional label for the element

---

## Doors

### Door
Single door.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the door frame corner that is on the same side with hinges and is on the side where the door opens (given `to_the_right` is set to `False`, else it is on the opposite side)
- `doorway_width`: float - width of the doorway (in meters), i.e. width of the door itself plus the width of both sides of the door frame
- `door_width`: float - width of the door itself (in meters)
- `thickness`: float - thickness of the door (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the doorway
- `to_the_right`: bool = False - binary indicator whether the door opens to the right if someone looks at it from the hinges point along the doorway
- `color`: str = 'black' - color to use for drawing the window
- `hinges_point`: float = 0.95 - relative position of the hinges along the doorway (0.0 = start, 1.0 = end, 0.5 = middle)
- `opening_outside`: bool = False - if True, door opens outward; if False, door opens inward
- `label`: str | None = None - optional label for the element

---

## Electricity

### PowerOutlet
Power outlet.

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

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the center of the segment shared with a wall is anchor point
- `symbol_length`: float - length of the symbol, not of the real cable
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the electrical cable
- `n_arcs`: int = 4 - number of turns representing a curved cable
- `line_width`: float = 0.5 - width of lines for matplotlib
- `color`: str = 'black' - color to use for drawing the power outlet
- `label`: str | None = None - optional label for the element

---

## Lighting

### CeilingLamp
Ceiling lamp represented by a circle and a cross inside.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; here, it is the center of the symbol
- `symbol_diameter`: float - diameter of the symbol (in meters)
- `line_width`: float = 0.5 - width of lines for matplotlib
- `color`: str = 'black' - color to use for drawing the lamp
- `label`: str | None = None - optional label for the element

### WallLamp
Wall lamp (e.g., sconce).

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

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the leftmost point is anchor point if `orientation_angle == 0`
- `length`: float - length of the wall (in meters); this value is also placed to annotation
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the arrow
- `width`: int = 0.01 - width of lines (in meters before scaling)
- `tip_length`: float = 0.1 - length of single arrow tip (in meters before scaling)
- `font_size`: int = 10 - font size
- `annotate_above`: bool = False - if set to True, annotation is placed above the arrow (prior to its rotation)
- `color`: str = 'black' - color to use for drawing the arrow and its annotation
- `label`: str | None = None - optional label for the element

### TextBox
Text box.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates (in meters) of anchor point; the center of a text box is its anchor point
- `lines`: list[str] - text lines to be printed
- `font_size`: int = 10 - font size
- `color`: str = 'black' - color to use for drawing the text and the bounding box
- `transparency`: float = 0.75 - transparency of the bounding box
- `edgecolor`: str = 'black' - edge color of the bounding box
- `label`: str | None = None - optional label for the element

---

## Multipurpose/Shapes

### Line
Line (solid, dashed, or dotted).

**Parameters:**
- `first_point`: tuple[float, float] - coordinates of the first end (in meters)
- `second_point`: tuple[float, float] - coordinates of the second end (in meters)
- `width`: float = 0.5 - width of the line for matplotlib
- `style`: str = 'solid' - type of line ('solid', 'dashed', 'dotted', or 'dash_dot')
- `color`: str = 'black' - color to use for drawing the line
- `label`: str | None = None - optional label for the element

### Polygon
Polygon. In particular, it can be used for wall corners of acute or obtuse angles.

**Parameters:**
- `vertices`: list[tuple[float, float]] - list of vertices coordinates (in meters)
- `line_width`: float = 0.1 - width of lines for matplotlib
- `color`: str = 'black' - color to use for drawing the line
- `label`: str | None = None - optional label for the element

### Circle
Circle element.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of the center (in meters)
- `radius`: float - radius of the circle (in meters)
- `color`: str = 'black' - color to use for drawing the circle
- `label`: str | None = None - optional label for the element

---

## Rooms

### Room
Room defined by 4 walls forming a rectangle, with optional other elements. A room consists of 2 horizontal walls (rotation 0 or 180) and 2 vertical walls (rotation 90 or 270), plus any number of additional elements.
Room is a higher level container for other remaining elements.
**Parameters:**
- `elements`:  list of element objects (windows, doors, etc.) inside the room. At least 4 walls are needed for a room
- `anchor_point`: tuple[float, float] = (0, 0) - coordinates (x, y) of the room's reference point (bottom-left corner)
- `color`: str = 'black' - default color for room walls if they don't have explicit color
- `label`: str | None = None - optional label for the room

**Note:** Rooms are typically created using `Room.create_from_params()` from YAML configuration rather than direct instantiation.

---

## Furniture - Storage

### GenericStorage
Storage box.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the storage box (in meters)
- `thickness`: float - thickness of the storage box (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the storage box
- `color`: str = 'black' - color to use for drawing the storage box
- `label`: str | None = None - optional label for the element

### Storage60
Storage box with thickness of 60 cm.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the storage box (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the storage box
- `color`: str = 'black' - color to use for drawing the storage box
- `label`: str | None = None - optional label for the element

**Note:** Thickness is fixed at 0.6 meters.

### Storage40
Storage box with thickness of 40 cm.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the storage box (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the storage box
- `color`: str = 'black' - color to use for drawing the storage box
- `label`: str | None = None - optional label for the element

**Note:** Thickness is fixed at 0.4 meters.

### Tabletop
Tabletop element.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the tabletop (in meters)
- `thickness`: float = 0.6 - thickness of the tabletop (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the tabletop
- `color`: str = 'black' - color to use for drawing the tabletop
- `label`: str | None = None - optional label for the element

---

## Furniture - Beds

### DoubleBed
Double bed.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the bed
- `color`: str = 'grey' - color to use for drawing the bed
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=2.15m, thickness=1.7m.

### SingleBed
Single bed.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the bed
- `color`: str = 'grey' - color to use for drawing the bed
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=2.0m, thickness=0.9m.

---

## Furniture - Appliances

### Dishwasher
Dishwasher appliance.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.6m × 0.6m (standard dishwasher size).

### Fridge
Refrigerator appliance.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `length`: float = 0.6 - length of the appliance (in meters)
- `thickness`: float = 0.6 - thickness of the appliance (in meters)
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

### Freezer
Freezer appliance.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `length`: float = 0.6 - length of the appliance (in meters)
- `thickness`: float = 0.6 - thickness of the appliance (in meters)
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

### WashingMachine
Washing machine appliance.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.6m × 0.6m (standard washing machine size).

### Dryer
Dryer appliance.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.6m × 0.6m (standard dryer size).

### Stovetop
Stovetop appliance.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.6m × 0.6m (standard stovetop size).

### SingleSink
Single sink appliance.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=0.9m, thickness=0.6m.

### DoubleSink
Double sink appliance.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the appliance
- `color`: str = 'grey' - color to use for drawing the appliance
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are typically larger than SingleSink to accommodate two basins.

---

## Furniture - Bathroom

### Shower
Shower stall.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fixture
- `color`: str = 'black' - color to use for drawing the fixture
- `label`: str | None = None - optional label for the element
- `length`: float = 0.9 - length of the shower stall (in meters)
- `thickness`: float = 0.9 - thickness of the shower stall (in meters)

### Bathtub
Bathtub.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fixture
- `length`: float = 1.7 - length of the bathtub (in meters)
- `thickness`: float = 0.8 - thickness of the bathtub (in meters)
- `color`: str = 'black' - color to use for drawing the fixture
- `label`: str | None = None - optional label for the element

### Basin
Bathroom basin/sink.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fixture
- `color`: str = 'black' - color to use for drawing the fixture
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=0.6m, thickness=0.5m.

### Toilet
Toilet.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fixture
- `color`: str = 'black' - color to use for drawing the fixture
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at length=0.7m, thickness=0.4m.

---

## Furniture - General

### Desk
Desk with standard dimensions.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the desk
- `length`: float = 1.4 - length of the desk (in meters)
- `thickness`: float = 0.65 - thickness of the desk (in meters)
- `color`: str = 'brown' - color to use for drawing the desk
- `label`: str | None = None - optional label for the element

### DiningTable
Dining table with configurable dimensions.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `length`: float - length of the table (in meters)
- `thickness`: float - width of the table (in meters)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the table
- `color`: str = 'brown' - color to use for drawing the table
- `label`: str | None = None - optional label for the element

### Chair
Chair with standard dimensions.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the chair
- `color`: str = 'darkgray' - color to use for drawing the chair
- `label`: str | None = None - optional label for the element

**Note:** Dimensions are fixed at 0.45m × 0.45m.

### Sofa
N-element sofa with configurable number of seats.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `num_seats`: int - number of seats in the sofa (1, 2, 3, etc.)
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the sofa
- `color`: str = 'darkslateblue' - color to use for drawing the sofa
- `label`: str | None = None - optional label for the element

**Note:** Each seat is 0.8m wide; total length = num_seats × 0.8m; depth is fixed at 0.9m.

---

## Furniture - Decorations

### FishTank
Fish tank / aquarium.

**Parameters:**
- `anchor_point`: tuple[float, float] - coordinates of anchor point (in meters); bottom left point is anchor point if `orientation_angle == 0`
- `orientation_angle`: float = 0 - angle (in degrees) that specifies orientation of the fish tank
- `length`: float = 0.6 - length of the fish tank (in meters)
- `thickness`: float = 0.3 - depth of the fish tank (in meters)
- `color`: str = 'blue' - color to use for drawing the fish tank
- `label`: str | None = None - optional label for the element

---

## Common Parameter Notes

### Coordinate System
- All coordinates are in **meters**
- `anchor_point` is typically the **bottom-left corner** when `orientation_angle == 0`
- The Y-axis points upward, X-axis points right

### Orientation
- `orientation_angle` is measured in **degrees**
- Positive angles rotate **counterclockwise**
- 0° = horizontal (pointing right), 90° = vertical (pointing up)

### Labels and IDs
- Every element has an auto-generated unique `id` property
- `label` is optional and user-defined for identification
- Both can be displayed on the floor plan if configured in options

### Colors
- Colors can be any matplotlib-compatible color string
- Common values: 'black', 'grey', 'brown', 'blue', 'darkgray', 'darkslateblue'
- Also supports hex colors (e.g., '#FF5733') and RGB tuples

### Room Integration
- Many elements have `room_id` property (set automatically when part of a room)
- Elements inside rooms have their `anchor_point` relative to the room's anchor

### Visibility
- Elements inherit visibility settings from global options
- Can be controlled via options like `show_invisible` and element-specific color settings

---

## Vertical Positioning (v_anchor and height)

All elements support vertical positioning through two parameters that control their rendering order and enable future 3D visualization.

### v_anchor (Vertical Anchor)

**Type:** `float | None`  
**Default:** Element-specific (see table below)  
**Range:** 0.0 - 10.0 (higher = rendered on top)

The `v_anchor` parameter determines the vertical position and rendering order (z-order) of elements:

- **Rendering Order**: Elements with higher `v_anchor` values are drawn on top of those with lower values
- **Automatic Offsetting**: Each element instance receives a unique offset of `0.0001 × instance_number` added to its base `v_anchor`, ensuring deterministic rendering order even for elements at the same level
- **YAML Order Preservation**: Elements defined first in YAML are instantiated first, so they render first (behind) within the same level

**Default v_anchor Values by Element Type:**

| Level | v_anchor | Element Types | Description |
|-------|----------|---------------|-------------|
| Ground | 0.00 | Floor surfaces, lawns, paths | Ground-level elements |
| Structural | 0.01 | Walls, decks, fences | Structural elements |
| Mid-Level | 0.02 | Doors, trees, shrubs, pools | Mid-height elements |
| Furniture | 0.03 | Tables, chairs, beds, appliances | Furniture and fixtures |
| Wall Outlets | 0.30 | PowerOutlet | Electrical outlets on walls |
| Windows | 1.00 | Window | Windows in walls |
| Switches | 1.20 | Switch | Light switches |
| Wall Lamps | 2.00 | WallLamp | Wall-mounted lighting |
| Ceiling | 2.70 | CeilingLamp | Ceiling fixtures |
| Annotations | 3.50 | DimensionArrow, TextBox | Info elements (always on top) |

**When to Override:**
- You want a specific element to render above/below its default layer
- Creating custom layering effects
- Debugging rendering order issues

**YAML Example:**
```yaml
elements:
  - element_type: desk
    anchor_point: [2.0, 3.0]
    # Uses default v_anchor: 0.03 (furniture level)
  
  - element_type: desk
    anchor_point: [4.0, 3.0]
    v_anchor: 2.5  # Override: render this desk very high (unusual but possible)
```

### height

**Type:** `float | None`  
**Default:** Element-specific (see table below)  
**Unit:** meters  
**Range:** 0.0+ (physical height in meters)

The `height` parameter represents the physical height of elements:

- **Current Use**: Semantic metadata (not used for 2D rendering)
- **Future Use**: Will enable 3D visualization and elevation views
- **Info Elements**: Annotation elements (DimensionArrow, TextBox) have `height = 0.0` as they're non-physical

**Default Heights by Element Type:**

| Element Type | Default Height (m) | Description |
|--------------|-------------------|-------------|
| **Structural** |
| Wall, WallND | 2.7 | Standard room height |
| Window | 1.4 | Typical window height |
| Door | 2.1 | Standard door height |
| **Furniture** |
| Desk, Table | 0.75 | Standard desk/table height |
| Chair, Sofa | 0.9 | Seating height with backrest |
| Bed | 0.5 | Mattress height |
| Wardrobe, Bookshelf | 2.0 | Tall storage furniture |
| **Appliances** |
| Refrigerator | 1.8 | Standard fridge height |
| Stove, Dishwasher | 0.9 | Counter-height appliances |
| WashingMachine | 0.85 | Standard washer height |
| **Bathroom** |
| Toilet, Bidet | 0.4 | Fixture height |
| Bathtub | 0.6 | Tub height |
| Sink | 0.85 | Sink height |
| **Landscaping** |
| Hedge, Shrub | 1.5 | Small hedge/shrub |
| DecidTree, EverTree | 5.0 - 10.0 | Tree heights |
| Lawn, Path, Deck | 0.0 | Ground-level surfaces |
| **Lighting** |
| CeilingLamp | 0.2 | Fixture depth |
| WallLamp | 0.3 | Sconce depth |
| **Annotations** |
| DimensionArrow, TextBox | 0.0 | Non-physical elements |

**When to Override:**
- Modeling specific furniture dimensions
- Creating elevation views
- Preparing for 3D visualization
- Accurate space planning with vertical constraints

**YAML Example:**
```yaml
elements:
  - element_type: bookshelf
    anchor_point: [1.0, 2.0]
    # Uses default height: 2.0m
  
  - element_type: bookshelf
    anchor_point: [3.0, 2.0]
    height: 2.5  # Override: taller bookshelf
```

### Implementation Details

**Automatic Element Counter:**
- Each Element instantiation increments a class-level counter
- Counter value is stored as `_element_instance_number`
- Final `v_anchor = base_v_anchor + (0.0001 × _element_instance_number)`
- This ensures unique z-order values without collisions

**Method Resolution Order (MRO):**
- Elements inherit from VertInfo mixin classes (e.g., `VertInfoLvl03`)
- Mixin MUST come first in inheritance: `class Desk(VertInfoLvl03, RectangularElement)`
- Mixins provide `_default_v_anchor()` method
- Elements override `_default_height()` method

**Z-Order in Matplotlib:**
- The `get_zorder()` method returns the final `v_anchor` value
- Passed to matplotlib as `patch.set_zorder(self.get_zorder())`
- Matplotlib handles float z-order values automatically (no manual sorting needed)
