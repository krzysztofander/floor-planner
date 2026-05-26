# Feature: Common Properties Refactoring

**Status:** Planning  
**Priority:** High  
**Estimated Effort:** 2.5-3.5 Days (includes SurfaceElement creation and Pool parameter migration)

## Overview
Refactor the Element class hierarchy to move commonly-used properties (`color`, `length`, `thickness`, `width`, `diameter`) from individual subclasses into appropriate base classes. This introduces a new `SurfaceElement` class to distinguish 2D surface area elements from line-like/3D rectangular elements, eliminating code duplication and creating a clearer type system.

**Note:** `anchor_point` and `orientation_angle` have already been refactored in previous work and are properly defined in base classes.

## Motivation

### Current Problems

1. **Architectural Inconsistency**: `RectangularElement` has methods that reference properties not declared in the class:
   - `get_draw_color()` references `self.color` (line 79 in element.py)
   - `get_corners()` references `self.length` and `self.thickness` (line 104)
   - These properties are only defined in subclasses, violating proper OOP design

2. **Massive Code Duplication**: 
   - `self.color = color` appears in 50+ classes
   - `self.length = length` appears in 40+ classes
   - `self.thickness = thickness` appears in 26+ classes
   - `self.width = width` appears in 12+ classes
   - `self.diameter = diameter` appears in 6+ classes

3. **Semantic Ambiguity**:
   - `thickness` and `width` serve different semantic purposes but both appear in RectangularElement subclasses
   - No type-level distinction between line-like elements (walls, fences) and surface area elements (decks, paths)
   - Confusion between perpendicular depth vs. second face dimension

4. **Unclear Type Semantics**:
   - No explicit `CircularElement` type for circular shapes
   - Circular elements inherit from generic `Element` and manually set `diameter`

## Design

### Property Analysis

| Property      | Classes | Semantic Meaning            | Proposed Location                |
|---------------|---------|-----------------------------|----------------------------------|
| `color`       | 50+     | All visual elements         | ✅ Move to `Element`             |
| `length`      | 40+     | All rectangular elements    | ✅ Move to `RectangularElement`  |
| `thickness`   | 26      | Line-like/3D elements       | ✅ Move to `RectangularElement`  |
| `width`       | 12      | 2D surface area elements    | ✅ Move to `SurfaceElement` (NEW)|
| `diameter`    | 6       | Circular elements           | ✅ Move to `CircularElement`     |

**Class Distribution:**
- **26 classes** extend `RectangularElement`: use `length` + `thickness` (walls, doors, windows, fence, most furniture)
- **12 classes** extend `SurfaceElement` (NEW): use `length` + `width` (paths, decks, lawns, hedges, pools)
- **6 classes** extend `CircularElement`: use `diameter` (trees, shrubs, fountain, gazebo)

**Architectural Decision:** Create separate `SurfaceElement` class to enforce semantic distinction at the class hierarchy level:
- **thickness** = perpendicular/depth dimension (walls: 0.2m thick, fence: 0.1m, furniture depth: 0.6m)
- **width** = second face dimension for 2D areas (deck: 5m × 3m, path: 10m × 2m, lawn: 20m × 15m)

## Proposed Solution

### Class Hierarchy Changes

```
Element (ABC)
├─ color: tuple[int, int, int] | None        ✅ Already refactored: anchor_point, label, id
│
├─ RectangularElement                         ✅ Already refactored: orientation_angle
│  ├─ length: float                           
│  └─ thickness: float                        ← NEW (perpendicular/depth dimension)
│     - Semantics: For line-like/3D elements (walls: 0.2m, fence: 0.1m, furniture depth: 0.6m)
│     - Subclasses: Wall, Door, Window, Fence, most Furniture (~26 classes)
│
├─ SurfaceElement                             ← NEW CLASS (extends RectangularElement)
│  ├─ length: float                           (inherited from RectangularElement)
│  └─ width: float                            ← NEW (second face dimension)
│     - Semantics: For 2D surface areas (deck: 5m×3m, path: 10m×2m, lawn: 20m×15m, pools)
│     - Subclasses: GardenPath, Deck, Lawn, Hedge, RaisedBed, RectPool (~12 classes)
│
└─ CircularElement                            ← NEW CLASS
   └─ diameter: float
      - Subclasses: Tree, Shrub, Fountain, Gazebo (~6 classes)
```

### Element Base Class

**Current:**
```python
class Element(ABC):
    def __init__(
        self,
        anchor_point: tuple[float, float] | None = None,  # ✅ Already refactored
        label: str | None = None
    ):
        self.label = label
        self.id = generate_element_id(self.__class__.__name__, label)
        self.anchor_point = anchor_point  # ✅ Already refactored
        # Subclasses manually assign: color
```

**After:**
```python
class Element(ABC):
    def __init__(
        self,
        anchor_point: tuple[float, float],
        color: tuple[int, int, int] | None = None,  # ← NEW
        label: str | None = None,
        id: str | None = None,
    ):
        self.anchor_point = anchor_point
        self.color = color  # ← NEW
        self.label = label
        self.id = id if id else generate_element_id(self.__class__.__name__, label)
    
    def get_draw_color(self) -> tuple[int, int, int] | None:  # ← MOVED from RectangularElement
        """Get the effective color for drawing."""
        if self.color == 'invisible':
            return None
        return self.color
```

### RectangularElement

**Current:**
```python
class RectangularElement(Element):
    def __init__(
        self,
        anchor_point: tuple[float, float] | None = None,
        orientation_angle: float = 0,  # ✅ Already refactored
        label: str | None = None
    ):
        super().__init__(anchor_point=anchor_point, label=label)
        self.orientation_angle = orientation_angle
        # Subclasses manually assign: length, thickness, color
```

**After:**
```python
class RectangularElement(Element):
    def __init__(
        self,
        anchor_point: tuple[float, float],
        orientation_angle: float,
        length: float,
        thickness: float,                         # ← NEW
        color: tuple[int, int, int] | None = None,
        label: str | None = None,
        id: str | None = None,
    ):
        super().__init__(anchor_point, color, label, id)
        self.orientation_angle = orientation_angle
        self.length = length
        self.thickness = thickness
    
    def get_corners(self) -> ...:  # ✅ Now references declared properties!
        # Uses self.length and self.thickness
        ...
```

**Used by:** Wall, Door, Window, Fence, RetainingWall, Pergola, most Furniture (~26 classes)

### SurfaceElement (NEW)

```python
class SurfaceElement(RectangularElement):
    """Base class for 2D surface area elements (decks, paths, lawns, pools)."""
    
    def __init__(
        self,
        anchor_point: tuple[float, float],
        orientation_angle: float,
        length: float,
        width: float,                             # ← NEW semantic parameter
        color: tuple[int, int, int] | None = None,
        label: str | None = None,
        id: str | None = None,
    ):
        # Pass width as thickness to parent for geometry calculations
        super().__init__(
            anchor_point, orientation_angle, length, width,  # width → thickness internally
            color, label, id
        )
        self.width = width  # Semantic alias for clarity in subclasses
```

**Rationale:**
- Enforces semantic distinction at class level (not just convention)
- Internally reuses `RectangularElement` geometry (width maps to thickness)
- Exposes `width` property for semantic clarity in subclass code
- Makes 2D vs 3D intent explicit in type system

**Used by:** GardenPath, Deck, Lawn, Hedge, RaisedBed, RectPool (~12 classes)

### CircularElement (NEW)

```python
class CircularElement(Element):
    """Base class for circular elements (anchor_point is center)."""
    
    def __init__(
        self,
        anchor_point: tuple[float, float],
        diameter: float,
        color: tuple[int, int, int] | None = None,
        label: str | None = None,
        id: str | None = None,
    ):
        super().__init__(anchor_point, color, label, id)
        self.diameter = diameter
    
    @property
    def radius(self) -> float:
        """Get circle radius."""
        return self.diameter / 2
    
    @abstractmethod
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the element."""
        pass
```

**Used by:** Tree, Shrub, Fountain, Gazebo (~6 classes)

### User-Facing Changes

**Breaking Change:** Pool classes parameter rename (no backward compatibility)
- `RectPool` and `OvalPool` currently use `height` parameter (inconsistent with rest of codebase)
- Will be renamed to `length` to match standard `length × width` pattern
- **Users MUST update YAML configs**
- No backward compatibility code

**YAML Migration Example:**
```yaml
# OLD - will break:
- element_type: rect_pool
  anchor_point: [10, 10]
  width: 4.0
  height: 8.0  # ❌ NO LONGER SUPPORTED

# NEW - required format:
- element_type: rect_pool
  anchor_point: [10, 10]
  length: 8.0  # ✨ Renamed from height
  width: 4.0   # ✅ Unchanged
```

**All other elements:** No YAML changes needed - purely internal refactoring.

## Implementation Plan

### Phase 1: Update Base Classes (3-4 hours)
- [ ] Add `color` parameter to `Element.__init__()`
- [ ] Move `get_draw_color()` from `RectangularElement` to `Element`
- [ ] Add `length`, `thickness` parameters to `RectangularElement.__init__()` (both required)
- [ ] Create new `SurfaceElement` class in `element.py` (extends RectangularElement, adds `width`)
- [ ] Create new `CircularElement` class in `element.py`
- [ ] Export `SurfaceElement` and `CircularElement` from `elements/__init__.py`
- [ ] Update docstrings for all four classes
- [ ] Verify `get_corners()` and `get_draw_color()` now reference declared properties

### Phase 2: Update RectangularElement Subclasses (4-5 hours)

**Elements staying as `RectangularElement` subclasses (~26 classes using `length` + `thickness`):**

- [ ] **basic.py**: WallND, Wall, Window, Door
- [ ] **door.py**: StandardDoor, etc.
- [ ] **multipurpose.py**: Room
- [ ] **furniture/bed.py**: All bed classes
- [ ] **furniture/furniture.py**: Table, Chair, Sofa, etc.
- [ ] **furniture/storage.py**: Wardrobe, Shelf, etc.
- [ ] **furniture/appliances.py**: All appliance classes
- [ ] **furniture/bathroom.py**: All bathroom fixture classes
- [ ] **furniture/decorations.py**: All decoration classes
- [ ] **info.py**: AreaWithText
- [ ] **lighting.py**: LightingElement, CeilingLight, WallSconce
- [ ] **electricity.py**: Outlet, Switch
- [ ] **landscaping/hardscape.py**: Fence, RetainingWall
- [ ] **landscaping/structures.py**: Pergola

**Change Pattern:**
```python
# Before
class Wall(RectangularElement):
    def __init__(self, anchor_point, orientation_angle, length, thickness, color, ...):
        super().__init__(anchor_point, orientation_angle)
        self.length = length
        self.thickness = thickness
        self.color = color

# After
class Wall(RectangularElement):
    def __init__(self, anchor_point, orientation_angle, length, thickness, color, ...):
        super().__init__(
            anchor_point, orientation_angle, length, thickness, color, ...
        )
        # No property assignments needed!
```

### Phase 3: Update SurfaceElement Subclasses (3-4 hours)

**Elements changing parent class from `RectangularElement` → `SurfaceElement` (~12 classes using `length` + `width`):**

- [ ] **landscaping/hardscape.py**: GardenPath
- [ ] **landscaping/structures.py**: Deck, RaisedBed
- [ ] **landscaping/vegetation.py**: Hedge, Lawn
- [ ] **landscaping/water.py**: RectPool (also rename `height` → `length` in Phase 5)

**Change Pattern:**
```python
# Before
class GardenPath(RectangularElement):
    def __init__(self, anchor_point, orientation_angle, length, width, color, ...):
        super().__init__(anchor_point, orientation_angle)
        self.length = length
        self.width = width
        self.color = color

# After
class GardenPath(SurfaceElement):  # ← Changed parent class!
    def __init__(self, anchor_point, orientation_angle, length, width, color, ...):
        super().__init__(
            anchor_point, orientation_angle, length, width, color, ...
        )
        # No property assignments needed!
```

### Phase 4: Update CircularElement Subclasses (2-3 hours)

- [ ] Refactor `CircularVegetation` to extend `CircularElement` in `landscaping/vegetation.py`
- [ ] Update `Tree` and `Shrub` (minimal - parameter passing only)
- [ ] Update `Fountain` in `landscaping/water.py` to extend `CircularElement`
- [ ] Update `Gazebo` in `landscaping/structures.py` to extend `CircularElement`
- [ ] Run landscaping examples to verify
- [ ] Run `make all` for full regression test

**Change Pattern:**
```python
# Before
class CircularVegetation(VegetationElement):
    def __init__(self, anchor_point, diameter, height, color, ...):
        super().__init__(height=height, ...)
        self.anchor_point = anchor_point  # ❌ Redundant
        self.diameter = diameter          # ❌ Should be in CircularElement
        self.color = color                # ❌ Should be in Element

# After
class CircularVegetation(CircularElement):
    def __init__(self, anchor_point, diameter, height, color, ...):
        super().__init__(anchor_point, diameter, color, ...)
        self.height = height  # ✅ Only vegetation-specific property
```

### Phase 5: Pool Parameter Migration (1 hour) - **BREAKING CHANGE**

- [ ] Update `RectPool` in `landscaping/water.py`:
  - Rename `height` parameter to `length` in `__init__`
  - Update all internal references from `self.height` to `self.length`
  - Update docstring
- [ ] Update `OvalPool` in `landscaping/water.py`:
  - Rename `height` parameter to `length` in `__init__`
  - Update all internal references from `self.height` to `self.length`
  - Update docstring
- [ ] Update YAML example files:
  - `examples/landscaping/water_features_demo.yml` - change `height:` to `length:`
  - Search for any other pool usage: `grep -rn "element_type.*pool" examples/`
- [ ] Test pool rendering: `python -m floor_planner -c examples/landscaping/water_features_demo.yml`
- [ ] Verify no backward compatibility code exists

### Phase 6: Cleanup & Documentation (1-2 hours)

- [ ] Search codebase for remaining direct assignments:
  - `grep -rn "self.color = color" floor_planner/elements/`
  - `grep -rn "self.length = length" floor_planner/elements/`
  - `grep -rn "self.thickness = thickness" floor_planner/elements/`
  - `grep -rn "self.width = width" floor_planner/elements/`
  - `grep -rn "self.diameter = diameter" floor_planner/elements/`
- [ ] Update `docs/element-parameters-reference.md` with new architecture
- [ ] Add breaking change notice to README for pool parameter rename
- [ ] Document width vs thickness semantic distinction
- [ ] Final `make all` regression test
- [ ] Commit with detailed message

## Testing Strategy

### Automated Testing
- Run `make all` after each phase to build all examples
- Regression tests via example floor plans:
  - `examples/templates/rooms/` - tests Room, Wall, Door elements
  - `examples/elements/` - tests all element types
  - `examples/furniture/` - tests all furniture
  - `examples/landscaping/` - tests vegetation, hardscape, water, structures
  - `examples/simple_no_rooms/` - tests basic floor plans

### Manual Verification Checklist
After each phase, verify:
- [ ] All example images generate successfully
- [ ] No visual regressions (compare before/after images)
- [ ] All elements render with correct colors
- [ ] All elements render with correct dimensions
- [ ] Rotation works correctly
- [ ] Circular elements maintain proper center positioning
- [ ] Pool elements fail gracefully if old `height` parameter is used (error message should suggest using `length`)

### Edge Cases
- [ ] Elements with `color='invisible'` still work with `get_draw_color()`
- [ ] Circular elements with varying diameters render correctly
- [ ] Surface elements (width-based) render identically to before

## Impact Analysis

### Files Modified (Estimated)
- **1 file:** `floor_planner/elements/element.py` (base classes: Element, RectangularElement, SurfaceElement, CircularElement)
- **1 file:** `floor_planner/elements/__init__.py` (exports SurfaceElement)
- **~26 files:** RectangularElement subclass implementation files
- **~12 files:** SurfaceElement subclass implementation files (parent class change)
- **~6 files:** CircularElement subclass implementation files
- **~3 files:** YAML example configs (pool parameter rename)

### Lines of Code
- **Added:** ~80 lines (new base class methods, SurfaceElement, CircularElement)
- **Removed:** ~150-200 lines (redundant property assignments)
- **Net reduction:** ~70-120 lines
- **Modified:** ~350-450 lines (constructor calls + parent class changes + pool parameter renames)

### Backwards Compatibility
- ⚠️ **Breaking change for Pool elements only:** `height` parameter renamed to `length`
  - Users must update YAML configs for `rect_pool` and `oval_pool`
  - No backward compatibility code - old `height` parameter will cause `TypeError`
  - Error message: "unexpected keyword argument 'height'" (natural Python error)
- ✅ All other elements: 100% backwards compatible (internal refactoring only)
- ✅ All existing floor plans work unchanged (except pool configs)

## Benefits

1. **Reduced Code Duplication:** Eliminate 150-200 lines of repetitive property assignments
2. **Clearer Intent:** Base class constructors document which properties are fundamental
3. **Easier Maintenance:** Property changes happen in one place
4. **Better IDE Support:** IntelliSense shows inherited properties
5. **Type Safety:** Properties typed in base class constructors
6. **Consistent Naming:** Pool `height` → `length` aligns with rest of codebase
7. **Architectural Consistency:** Methods in `RectangularElement` no longer reference undeclared properties
8. **Semantic Clarity:** Separate `SurfaceElement` class makes 2D vs 3D distinction explicit at type level
9. **Compile-Time Enforcement:** Class hierarchy enforces thickness/width distinction (no runtime checks needed)
10. **Extensibility:** New element types inherit common properties automatically

## Open Questions

### 1. Should we provide helpful error message for deprecated `height` parameter?

Since we're removing backward compatibility for pools, should we catch attempts to use `height` and provide guidance?

**Recommendation:** No special handling needed
- Natural Python `TypeError: got unexpected keyword argument 'height'` is clear enough
- Error naturally guides users to check function signature
- Keep implementation simple - no special deprecation handling code
- Document breaking change in README and migration guide

### 2. Parameter ordering in constructors?

What order should parameters follow in base classes?

**Proposed Order:**
```python
def __init__(
    anchor_point,         # 1. Position (required)
    orientation_angle,    # 2. Orientation (for rectangles)
    length,               # 3. Primary dimension
    thickness/width,      # 4. Secondary dimension
    color,                # 5. Appearance
    label,                # 6. Metadata
    id,                   # 7. Metadata (last)
):
```

**Recommendation:** Follow this order consistently for all elements

## References

- Element class design: `floor_planner/elements/element.py`
- Existing element implementations: `floor_planner/elements/**/*.py`
- YAML configuration: examples throughout `examples/` folder
- Previous refactoring work: Session history (Phase 1-3 anchor_point migration)

## Success Criteria

1. ✅ `make all` passes without errors (after updating pool YAML configs)
2. ✅ No visual regressions in example outputs
3. ✅ `get_corners()` and `get_draw_color()` reference declared properties only
4. ✅ Code reduction: net removal of 70+ lines
5. ✅ All 50+ elements inherit common properties from base classes
6. ✅ `CircularElement` exists and is used by 6+ classes
7. ✅ `SurfaceElement` exists and is used by 12+ classes
8. ✅ Pool elements use `length` instead of `height` (breaking change implemented)
9. ✅ Documentation updated with new architecture and breaking change notice
10. ✅ No backward compatibility code for deprecated `height` parameter
