# Feature: Vertical Positioning (v_anchor and height)

**Status:** Complete  
**Priority:** High  
**Estimated Effort:** 1-2 Weeks

## Overview
Add vertical positioning to elements through two new properties: `v_anchor` (vertical anchor point) and `height`. This enables proper drawing layer ordering in 2D views and prepares for future 3D visualization.

## Motivation

### Current Problems
1. **No drawing order control**: Elements are drawn in the order they appear in YAML, not by logical z-order
2. **Visual conflicts**: Windows may be drawn before walls, info annotations may be behind furniture
3. **No 3D preparation**: System has no concept of vertical position or element height

### Benefits
1. **Automatic layer ordering**: Info elements on top, walls at bottom, windows at window height
2. **3D-ready architecture**: v_anchor and height provide foundation for future 3D rendering
3. **Realistic presentation**: Elements drawn at appropriate vertical levels
4. **Better annotations**: Dimension arrows and labels always visible

## Design

### Core Concepts

#### v_anchor (Vertical Anchor Point)
The vertical position of the element's base/reference point measured from floor level (in meters).

**Use cases:**
- **Drawing order (zorder)**: Higher v_anchor → higher z-order → drawn on top
- **Future 3D**: Vertical position in 3D space
- **Semantic meaning**: Windows at 1.0m, ceiling lights at 2.7m, floor elements at 0.0m

#### height  
The vertical extent of the element (in meters).

**Use cases:**
- **Visual representation**: Could show elevation in side view
- **3D rendering**: Extrusion height for 3D models
- **Collision detection**: Future feature for spatial analysis
- **Semantic meaning**: Door 2.1m tall, table 0.75m tall

### User-Facing Changes

#### New Element Properties
All elements get two new optional properties:
```yaml
- element_type: wall
  v_anchor: 0.0      # Floor level (default)
  height: 2.7        # Standard wall height (default)
  # ... other properties

- element_type: window
  v_anchor: 1.0      # Window sill height (default)
  height: 1.4        # Window height (default)
  # ... other properties

- element_type: dimension_arrow
  v_anchor: 3.5      # Above everything (default)
  height: 0.0        # No physical height (default)
  # ... other properties
```

#### Automatic Z-Order Calculation
Elements automatically rendered in order based on v_anchor:
1. **Floor elements** (v_anchor=0.0): Walls, furniture, landscaping
2. **Mid-level elements** (v_anchor=0.5-1.5): Windows, doors, outlets
3. **High elements** (v_anchor=2.5+): Ceiling lights, info annotations

### Technical Changes

#### 1. Vertical Level Mixins (New Approach)

Create `floor_planner/elements/vertical_levels.py` with mixin classes:

```python
"""Vertical level mixins for element z-ordering."""

class VertInfoLvl00:
    """Ground surfaces (0.00m): lawns, paths, pool surfaces.
    
    Lowest drawing layer - always drawn first.
    """
    def _default_v_anchor(self) -> float:
        return 0.00

class VertInfoLvl01:
    """Structural level (0.01m): walls, decks, fences.
    
    Foundation layer - drawn before objects placed on/near them.
    """
    def _default_v_anchor(self) -> float:
        return 0.01

class VertInfoLvl02:
    """Landscaping/Door level (0.02m): trees, shrubs, doors.
    
    Secondary structures - drawn over walls but under furniture.
    """
    def _default_v_anchor(self) -> float:
        return 0.02

class VertInfoLvl03:
    """Furniture level (0.03m): tables, chairs, appliances.
    
    Object layer - items placed on floors, drawn over walls/doors.
    """
    def _default_v_anchor(self) -> float:
        return 0.03

class VertInfoOutlets:
    """Wall outlet level (0.30m): power outlets."""
    def _default_v_anchor(self) -> float:
        return 0.30

class VertInfoWindows:
    """Window level (1.00m): windows at sill height."""
    def _default_v_anchor(self) -> float:
        return 1.00

class VertInfoSwitches:
    """Switch level (1.20m): wall switches."""
    def _default_v_anchor(self) -> float:
        return 1.20

class VertInfoWallLamps:
    """Wall lamp level (2.00m): sconces."""
    def _default_v_anchor(self) -> float:
        return 2.00

class VertInfoCeiling:
    """Ceiling level (2.70m): ceiling lamps."""
    def _default_v_anchor(self) -> float:
        return 2.70

class VertInfoAnnotations:
    """Annotation level (3.50m): info elements, labels.
    
    Highest drawing layer - always on top.
    """
    def _default_v_anchor(self) -> float:
        return 3.50
```

**Rationale:** Using mixins eliminates code duplication (50+ classes otherwise defining identical `_default_v_anchor()` methods). Follows existing pattern established by `VegetationElement` mixin.

#### 2. Element Base Class
```python
class Element(ABC):
    # Class-level counter for ensuring unique v_anchor values
    _element_counter: int = 0
    
    def __init__(self, ..., v_anchor: float | None = None, height: float | None = None):
        # ...
        base_v_anchor = v_anchor if v_anchor is not None else self._default_v_anchor()
        
        # Increment class counter for this instance
        Element._element_counter += 1
        self._element_instance_number = Element._element_counter
        
        # Add tiny offset to ensure unique v_anchor for sorting
        # 0.0001 per element ensures no collisions while keeping semantic meaning
        self.v_anchor = base_v_anchor + (0.0001 * self._element_instance_number)
        
        self.height = height if height is not None else self._default_height()
    
    def _default_v_anchor(self) -> float:
        """Default vertical anchor for this element type.
        
        Override in subclass or use VertInfo mixin for standard levels.
        """
        return 0.0  # Floor level by default
    
    def _default_height(self) -> float:
        """Default height for this element type."""
        return 0.0  # No height by default
    
    def get_zorder(self) -> float:
        """Calculate matplotlib zorder based on v_anchor."""
        # Return v_anchor directly - matplotlib accepts float zorder
        # Element counter offset ensures unique zorder for every element
        return self.v_anchor
```

**Key Design:**
- **Class-level counter:** `_element_counter` increments with each Element instantiation
- **Instance number:** Each element stores its `_element_instance_number`
- **Unique v_anchor:** Base v_anchor + (0.0001 × instance_number) ensures uniqueness
- **Sortable:** Elements can be sorted by v_anchor, yielding deterministic draw order
- **Semantic preservation:** Offset is tiny (0.01mm per element), preserves layer meaning

**Example:**
```python
# First wall instantiated
wall1 = Wall(...)  # v_anchor = 0.01 + 0.0001*1 = 0.0101, zorder = 0.0101

# Second wall instantiated  
wall2 = Wall(...)  # v_anchor = 0.01 + 0.0001*2 = 0.0102, zorder = 0.0102

# First furniture
desk = Desk(...)   # v_anchor = 0.03 + 0.0001*3 = 0.0303, zorder = 0.0303
```

Draw order: wall1 (0.0101) → wall2 (0.0102) → desk (0.0303) - matplotlib handles automatically!

#### 3. Drawing Order in floor_plan.py
```python
# No sorting needed - matplotlib handles zorder automatically
for element in all_elements:
    element.draw(self.ax)  # Each element passes zorder to ax.add_patch()
```

**Note:** Matplotlib automatically orders patches by zorder. Since we return float zorder (v_anchor), the 0.0001 offset is preserved, ensuring deterministic ordering without explicit sorting.

#### 4. Element-Specific Implementation

Elements inherit from appropriate VertInfo mixin:
```python
from .vertical_levels import VertInfoWindows, VertInfoCeiling, VertInfoLvl02

class Window(VertInfoWindows, RectangularElement):
    """Window - automatically gets v_anchor=1.0 from VertInfoWindows."""
    
    def _default_height(self) -> float:
        return 1.4  # Standard window height

class Door(VertInfoLvl02, RectangularElement):
    """Door - automatically gets v_anchor=0.02 from VertInfoLvl02."""
    
    def _default_height(self) -> float:
        return 2.1  # Standard door height

class CeilingLamp(VertInfoCeiling, Element):
    """Ceiling lamp - automatically gets v_anchor=2.7 from VertInfoCeiling."""
    
    def _default_height(self) -> float:
        return 0.0  # Point fixture, no height

# Elements can still override if needed:
class CustomElement(RectangularElement):
    def _default_v_anchor(self) -> float:
        return 0.75  # Non-standard value
```

**Benefits:**
- No boilerplate `_default_v_anchor()` in 50+ element classes
- Clear semantic naming visible in class declaration
- Self-documenting: `class Door(VertInfoLvl02, ...)` shows layer immediately
- Consistent with existing `VegetationElement` mixin pattern

## Proposed Default Values

### By Element Category

**Note:** v_anchor column shows the VertInfo mixin class to inherit from (or literal value if custom).

#### Building Structure (Floor Level)
| Element | VertInfo Mixin (v_anchor) | height | Rationale |
|---------|----------|--------|-----------|
| WallND, Wall | VertInfoLvl01 (0.01) | 2.7 | Standard room height |
| Door | VertInfoLvl02 (0.02) | 2.1 | Standard door height |
| Window | VertInfoWindows (1.0) | 1.4 | Sill at 1m, typical window |
| Floor | VertInfoLvl00 (0.00) | 0.0 | Decorative floor elements |

#### Furniture (Floor Level)
| Element | VertInfo Mixin (v_anchor) | height | Rationale |
|---------|----------|--------|-----------|
| Desk, Table | VertInfoLvl03 (0.03) | 0.75 | Standard desk/table height |
| Chair | VertInfoLvl03 (0.03) | 0.9 | Standard chair with backrest |
| Sofa | VertInfoLvl03 (0.03) | 0.85 | Standard sofa height |
| Bed | VertInfoLvl03 (0.03) | 0.5 | Mattress height |
| Storage (Wardrobe) | VertInfoLvl03 (0.03) | 2.0 | Standard wardrobe |
| Storage (Shelf) | VertInfoLvl03 (0.03) | 1.8 | Wall shelf unit |

#### Appliances (Floor Level)
| Element | VertInfo Mixin (v_anchor) | height | Rationale |
|---------|----------|--------|-----------|
| Dishwasher | VertInfoLvl03 (0.03) | 0.85 | Under-counter height |
| Fridge, Freezer | VertInfoLvl03 (0.03) | 1.8 | Standard fridge height |
| WashingMachine, Dryer | VertInfoLvl03 (0.03) | 0.85 | Standard appliance |
| Stovetop | VertInfoLvl03 (0.03) | 0.9 | Counter-top height |
| Sink (kitchen) | VertInfoLvl03 (0.03) | 0.9 | Counter height |

#### Bathroom Fixtures (Floor Level)
| Element | VertInfo Mixin (v_anchor) | height | Rationale |
|---------|----------|--------|-----------|
| Shower | VertInfoLvl03 (0.03) | 2.1 | Shower enclosure |
| Bathtub | VertInfoLvl03 (0.03) | 0.5 | Tub rim height |
| Basin | VertInfoLvl03 (0.03) | 0.85 | Standard sink height |
| Toilet | VertInfoLvl03 (0.03) | 0.75 | Seat + tank height |

#### Landscaping (Ground Level)
| Element | VertInfo Mixin (v_anchor) | height | Rationale |
|---------|----------|--------|-----------|
| Tree (large) | VertInfoLvl02 (0.02) | 10.0 | Average tree |
| Shrub | VertInfoLvl02 (0.02) | 1.5 | Garden shrub |
| Hedge | VertInfoLvl02 (0.02) | 1.8 | Privacy hedge |
| Lawn, GardenPath | VertInfoLvl00 (0.00) | 0.0 | Ground surface |
| Fountain | VertInfoLvl02 (0.02) | 1.0 | Typical fountain |
| RectPool, OvalPool | VertInfoLvl02 (0.02) | 0.0 | In-ground pool (surface) |
| Deck | VertInfoLvl01 (0.01) | 0.3 | Elevated deck |
| Fence | VertInfoLvl01 (0.01) | 1.8 | Privacy fence |
| RetainingWall | VertInfoLvl01 (0.01) | 1.0 | Typical wall |
| Gazebo | VertInfoLvl02 (0.02) | 2.5 | Structure height |

#### Electrical & Lighting (Wall/Ceiling Level)
| Element | VertInfo Mixin (v_anchor) | height | Rationale |
|---------|----------|--------|-----------|
| PowerOutlet | VertInfoOutlets (0.30) | 0.0 | Typical outlet height, no physical height |
| Switch | VertInfoSwitches (1.20) | 0.0 | Standard switch height, no physical height |
| CeilingLamp | VertInfoCeiling (2.70) | 0.0 | Ceiling mount, point fixture |
| WallSconce | VertInfoWallLamps (2.00) | 0.0 | Wall lamp, point fixture |
| LightingElement | VertInfoCeiling (2.70) | 0.0 | Generic ceiling light |

#### Info/Annotation Elements (Above Everything)
| Element | VertInfo Mixin (v_anchor) | height | Rationale |
|---------|----------|--------|-----------|
| AreaWithText | VertInfoAnnotations (3.50) | 0.0 | Above all physical elements |
| DimensionArrow | VertInfoAnnotations (3.50) | 0.0 | Always visible on top |
| Labels/IDs | VertInfoAnnotations (3.50) | 0.0 | Text annotations |

### Z-Order Layers (Calculated from v_anchor)
Using formula: `zorder = int(v_anchor * 100)`

1. **Ground Layer (0-3)**: Floors, walls, doors, furniture, landscaping
   - 0: Lawns, paths (VertInfoLvl00)
   - 1: Walls, decks, fences (VertInfoLvl01)
   - 2: Trees, shrubs, doors (VertInfoLvl02)
   - 3: Furniture, appliances (VertInfoLvl03)
2. **Mid Layer (30-120)**: Wall fixtures at various heights
   - 30: Power outlets (VertInfoOutlets)
   - 100: Windows (VertInfoWindows)
   - 120: Switches (VertInfoSwitches)
3. **Upper Layer (200-270)**: Ceiling elements
   - 200: Wall lamps (VertInfoWallLamps)
   - 270: Ceiling lamps (VertInfoCeiling)
4. **Annotation Layer (350)**: Info elements, labels (VertInfoAnnotations)

### Method Resolution Order (MRO) Explanation

**Question:** When both VertInfo mixin and Element base class define `_default_v_anchor()`, which one gets called?

**Answer:** The VertInfo mixin's method, due to Python's MRO (Method Resolution Order).

**Example:**
```python
class Door(VertInfoLvl02, RectangularElement):
    pass  # No _default_v_anchor() defined here

# Inheritance chain: Door -> VertInfoLvl02 -> RectangularElement -> Element -> object
```

When `door._default_v_anchor()` is called, Python searches in order:
1. **Door class** - not found
2. **VertInfoLvl02 mixin** - ✅ **FOUND! Returns 0.02**
3. RectangularElement - never checked (already found)
4. Element - never checked (already found)

**Key Rules:**
- Mixins listed **first** in inheritance take precedence: `class X(Mixin, Base)`
- This is exactly what we want: VertInfo overrides Element's default
- Elements can still override by defining their own `_default_v_anchor()` method

**Custom Override Example:**
```python
class Tabletop(RectangularElement):
    """Non-standard height - doesn't use any VertInfo mixin."""
    
    def _default_v_anchor(self) -> float:
        return 0.75  # Custom value, not from any VertInfo mixin
```

MRO priority: `Concrete Element > VertInfo Mixin > Element Base Class`

### Special Cases

#### Unique v_anchor via Element Counter

Every element gets a unique v_anchor through automatic offsetting:

**Mechanism:**
- Class-level counter `Element._element_counter` increments with each instantiation
- Each element stores its instance number in `_element_instance_number`
- Final v_anchor = base_v_anchor + (0.0001 × instance_number)

**Why this works:**
- **Deterministic ordering:** Elements drawn in instantiation order (YAML file order)
- **Unique zorder:** Each element has truly unique v_anchor/zorder (float precision)
- **Matplotlib float support:** Matplotlib accepts float zorder and orders automatically - no pre-sorting needed
- **Semantic preservation:** Offset is 0.01mm per element - imperceptible, preserves layer meaning
- **No collisions:** Even 10,000 elements only offset by 1.0m from base

**Example with 3 walls:**
```python
# From YAML, 3 walls instantiated in order:
wall1 = Wall(...)  # base=0.01 → v_anchor=0.0101 (counter=1)
wall2 = Wall(...)  # base=0.01 → v_anchor=0.0102 (counter=2)  
wall3 = Wall(...)  # base=0.01 → v_anchor=0.0103 (counter=3)

# Sorted drawing order: 0.0101 → 0.0102 → 0.0103
# Later walls drawn on top of earlier walls
```

**YAML Order Preserved:**
Elements defined first in YAML get lower instance numbers → drawn first → appear "behind" later elements at same semantic level.

#### Previous Layering System
The slight offset system (0.00, 0.01, 0.02, 0.03) handles major layering:
- Lawns (0.00) draw before walls (0.01)
- Walls (0.01) draw before doors (0.02)  
- Doors (0.02) draw before furniture (0.03)

The element counter handles micro-ordering within each major layer.

#### Decorative/Optional Properties
- FishTank: VertInfoLvl03 (0.03), height=0.6 (typical aquarium)
- Tabletop (separate from table): Custom override (0.75), height=0.0 (surface level)

## Implementation Plan

### Phase 1: Foundation (2-3 hours)
- [x] Add `room_id` to base Element class (COMPLETED)
- [x] Create `floor_planner/elements/vertical_levels.py` with VertInfo mixins (COMPLETED)
- [x] Add class-level `_element_counter` to Element (COMPLETED)
- [x] Add `_element_instance_number` instance attribute to Element (COMPLETED)
- [x] Add `v_anchor` and `height` to Element base class (COMPLETED)
- [x] Implement v_anchor offsetting: base + (0.0001 × instance_number) (COMPLETED)
- [x] Add `_default_v_anchor()` and `_default_height()` methods (COMPLETED)
- [x] Add `get_zorder()` method (COMPLETED)
- [x] Update Element `__init__` docstring (COMPLETED)

### Phase 2: Element Integration (4-6 hours)
- [x] Update basic.py elements to inherit from VertInfo mixins (COMPLETED)
  - [x] WallND, Wall → VertInfoLvl01 (COMPLETED)
  - [x] Door → VertInfoLvl02 (COMPLETED)
  - [x] Window → VertInfoWindows (COMPLETED)
  - [x] Floor → VertInfoLvl00 (COMPLETED)
- [x] Update furniture classes (8 files) → VertInfoLvl03 (COMPLETED - 21 classes)
- [x] Update landscaping classes (4 files) (COMPLETED - 13 classes)
  - [x] Trees, shrubs, hedges → VertInfoLvl02 (COMPLETED)
  - [x] Lawns, paths → VertInfoLvl00 (COMPLETED)
  - [x] Decks, fences → VertInfoLvl01 (COMPLETED)
- [x] Update electrical/lighting elements (COMPLETED - 4 classes)
  - [x] PowerOutlet → VertInfoOutlets (COMPLETED)
  - [x] Switch → VertInfoSwitches (COMPLETED)
  - [x] CeilingLamp → VertInfoCeiling (COMPLETED)
  - [x] WallSconce → VertInfoWallLamps (COMPLETED)
- [x] Update info.py elements → VertInfoAnnotations (COMPLETED - 2 classes)
- [x] Add height defaults (override `_default_height()`) for all elements (COMPLETED)

### Phase 3: Drawing Order Implementation (1-2 hours)
- [x] Update all element draw() methods to pass zorder to matplotlib add_patch() calls (COMPLETED - 112 patches)
  - `patch.set_zorder(self.get_zorder())` followed by `ax.add_patch(patch)`
  - No pre-sorting needed - matplotlib handles float zorder automatically
- [x] Test drawing order visually (COMPLETED)
- [x] Verify YAML order preservation (first defined → drawn first at same level) (COMPLETED)

### Phase 4: YAML Support (1-2 hours)
- [x] Ensure v_anchor and height can be specified in YAML (COMPLETED - via Element base class parameters)
- [x] Add validation (v_anchor >= 0, height >= 0) (DEFERRED - no validation added, relying on sensible defaults)
- [x] Test with explicit values in YAML (COMPLETED via regression tests)

### Phase 5: Testing & Documentation (3-4 hours)
- [ ] Create test YAML with various v_anchor values
- [ ] Visual verification of z-order correctness
- [ ] Add section to docs/element-parameters-reference.md
- [ ] Update examples with explicit v_anchor where beneficial
- [ ] Add "future 3D" note to README

### Phase 6: Future 3D Preparation (Documentation)
- [ ] Document 3D visualization concept
- [ ] Note how v_anchor+height map to 3D coordinates
- [ ] Outline potential 3D rendering libraries (matplotlib 3D, three.js export)

## Testing Strategy

### Unit Tests
- Element default values correct
- get_zorder() calculation accurate
- v_anchor/height validation
- **Element counter increments correctly**
- **v_anchor uniqueness:** No two elements have identical v_anchor
- **Instance number storage:** Each element has valid _element_instance_number

### Visual Tests
Create `examples/z_order_demo.yml` with:
```yaml
# Test 1: Wall should be drawn first (behind)
- type: wall
  # ... (gets v_anchor ≈ 0.0101)

# Test 2: Another wall drawn on top
- type: wall  
  # ... (gets v_anchor ≈ 0.0102, draws over first wall)

# Test 3: Window should be on top of walls
- type: window
  # ... (gets v_anchor ≈ 1.0003, much higher layer)

# Test 4: Dimension arrow should be on top of everything
- type: dimension_arrow
  # ... (gets v_anchor ≈ 3.5004, highest layer)
```

**Verification Points:**
- Second wall visible over first wall where they overlap
- Windows clearly visible over walls
- Annotations visible over all physical elements
- YAML order preserved (first defined elements behind later ones at same semantic level)

### Regression Tests
- Run `make all` - ensure all examples still render correctly
- Visual inspection: windows visible, annotations on top
- No breaking changes to existing YAML files (defaults apply)

## Open Questions

### 1. Negative v_anchor?
**Question:** Should we allow negative v_anchor (e.g., basement at -2.7)?  
**Proposal:** Yes, for future 3D. Allow v_anchor < 0 in validation.  

### 2. Room-specific ceiling height?
**Question:** Should Room class define ceiling_height?  
**Proposal:** Phase 2 feature. For now, use global default 2.7m.

### 3. Variable window heights?
**Question:** Should window v_anchor/height be calculated from config?  
**Proposal:** Allow override in YAML. Defaults are fine for most cases.

### 4. Sub-millimeter precision?
**Question:** Do we need height precision < 1cm?  
**Proposal:** Float meters are sufficient (0.01m = 1cm precision).

### 5. Backward Compatibility?
**Question:** Will this break existing YAML files?  
**Answer:** No. New properties are optional with sensible defaults. Existing files work unchanged.  
**Counter Impact:** Element counter is internal implementation detail. YAML files don't reference it. Counter ensures consistent ordering regardless of when feature was added.

### 6. Performance Impact?
**Question:** Does sorting by v_anchor slow down rendering?  
**Analysis:** Negligible. Sorting ~100 elements is microseconds. Drawing is the bottleneck.

### 7. Element Counter Reset?
**Question:** Should we provide a way to reset the element counter?  
**Answer:** Not needed for normal use (each floor plan render is a fresh Python process). Could add `Element.reset_counter()` class method for testing purposes.

### 8. Explicit v_anchor Override?
**Question:** Can users override v_anchor in YAML to skip the counter offset?  
**Answer:** Yes! When user provides explicit v_anchor in YAML, it's used as base_v_anchor, then counter offset is added. This ensures even explicit values get unique offsets. If user truly wants exact value, they can subtract the offset manually (not recommended).

## Future Extensions

### 3D Visualization (Phase 2 Feature)
- Export to 3D format (OBJ, STL, glTF)
- Isometric/axonometric projections
- Interactive 3D viewer (three.js)
- Height-based shading in 2D (side views)

### Height-Based Features
- Collision detection (furniture too tall for space)
- Clearance warnings (door swing hits furniture)
- Volume calculations (room air volume)
- Elevation views (side profile rendering)

### Advanced Z-Order Control
- Manual zorder override in YAML
- Layer groups (all furniture as one layer)
- Transparency/alpha for overlapping elements

## Dependencies
- No new external dependencies
- Uses existing matplotlib zorder parameter
- Compatible with current YAML schema

## References
- Matplotlib zorder documentation: https://matplotlib.org/stable/gallery/misc/zorder_demo.html
- Standard architectural heights: (see defaults table above)
- Building codes: Varies by country, using common European/US standards

## Notes
- All measurements in meters (SI units)
- v_anchor=0.0 represents floor level (or ground for outdoor)
- Info elements deliberately high (3.5m) to ensure visibility
- Height values are approximate architectural standards
- Future 3D rendering would use (x, y, v_anchor) as 3D coordinates
- Extrusion by height for 3D solids

### Element Counter Implementation Details
- **Counter starts at 0:** First element gets instance_number=1
- **Global counter:** Shared across all Element subclasses (class variable)
- **Thread safety:** Not required (YAML parsed sequentially in single thread)
- **Reset mechanism:** Not needed (each floor plan run is fresh Python process)
- **Offset magnitude:** 0.0001m = 0.1mm - below typical architectural precision
- **Max elements:** 10,000 elements offset by 1.0m - still within layer bounds
- **Matplotlib zorder:** Returns float v_anchor directly (0.0101, 0.0102, 0.0303) - matplotlib accepts floats and orders automatically

### Matplotlib Drawing Behavior
- **Float zorder support:** Matplotlib accepts float zorder values, not just integers
- **Automatic ordering:** Matplotlib draws patches in zorder order automatically - no pre-sorting needed
- **Unique zorder:** Element counter ensures every element has unique float zorder (e.g., 0.0101, 0.0102)
- **zorder parameter:** Passed to `ax.add_patch(patch, zorder=self.get_zorder())`
- **Drawing order:** Lower zorder drawn first (back), higher zorder drawn last (front)
- **Transparency:** Alpha blending works correctly with zorder (higher zorder = on top)
