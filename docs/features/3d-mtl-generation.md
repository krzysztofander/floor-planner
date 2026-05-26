# Feature: 3D Model Generation in OBJ/MTL Format

**Status:** In Progress (Phases 1-6 Complete ✅, Phase 8 In Progress)  
**Priority:** High  
**Estimated Effort:** 3-4 Weeks (8 phases, realistic textures in Phase 7)

## Overview
Generate 3D models in OBJ format with MTL (material) files from 2D floor plan elements. This feature leverages the existing vertical positioning system (v_anchor, height) to extrude 2D floor plan elements into 3D objects with textures.

**Current Status:** Phases 1-6 completed (May 26, 2026). Core 3D export functionality is working with texture validation, z-fighting prevention, and configurable circular element segments. Phase 7 (AI textures) deferred. Working on Phase 8 (documentation).

## Motivation
- Enable 3D visualization of floor plans for better spatial understanding
- Allow rendering in 3D modeling software (Blender, SketchUp, etc.)
- Provide foundation for future VR/AR walkthrough features
- Leverage already-implemented v_anchor and height properties
- Create realistic textured models for presentations

## Design

### User-Facing Changes

**YAML Configuration:**
```yaml
project:
  dpi: 200
  png_dir: "output"
  visualisation_dir: "3d_models"  # Triggers 3D generation

# Optional: global texture settings
textures:
  default_folder: "textures/defaults"  # AI-generated default textures
  
floor_plans:
  - title:
      text: "Living Room"
    elements:
      - type: wall
        anchor_point: [0, 0]
        length: 5.0
        thickness: 0.15
        # Optional: custom texture override (single texture)
        texture: "textures/brick_wall.jpg"
      
      - type: door
        anchor_point: [2, 0]
        doorway_width: 1.0
        door_width: 0.9
        thickness: 0.2
        # Multiple textures for different faces
        textures:
          front: "textures/door_oak_front.jpg"
          back: "textures/door_oak_back.jpg"
          frame: "textures/door_frame.jpg"
      
      - type: desk
        anchor_point: [2.0, 1.5]
        length: 1.2
        width: 0.6
        # Single string: uses default texture from textures/defaults/desk.jpg
        # Can also use dict for multiple textures:
        textures:
          top: "textures/desk_oak_top.jpg"
          sides: "textures/desk_oak_sides.jpg"
```

**Output Files:**
- `3d_models/floor_plan_name.obj` - 3D geometry
- `3d_models/floor_plan_name.mtl` - Material definitions
- `3d_models/textures/` - Texture image files. Copy of defaults or copy of specified manually.
  

### Technical Changes

#### New Files

**1. `floor_planner/obj_exporter.py`**
- Core OBJ/MTL generation logic
- Functions:
  - `export_floor_plan_to_obj(floor_plan, output_path, mtl_path)`
  - `generate_obj_header()`
  - `generate_mtl_file(materials, textures)`
  
**2. `floor_planner/elements/geometry_3d.py`**
- Mixin classes for 3D geometry generation
- `Generate3DMixin` - base class with abstract methods
- `RectangularGeometry3D` - for rectangular elements
- `CircularGeometry3D` - for circular elements
- `SurfaceGeometry3D` - for surfaces that use width instead of thickness (e.g., lawns, paths)
  - Note: These still have height > 0 for 3D generation
  - Implementation is same as RectangularGeometry3D

**3. `floor_planner/material_properties.py`**
- Material property definitions for MTL export
- Default Ka, Kd, Ks, Ns values per element type
- Functions:
  - `get_material_properties(element_type)` - Returns material dict for element
  - `format_mtl_color(rgb_tuple)` - Formats RGB as MTL string
- Organized by category (structural, furniture, appliances, bathroom, landscaping)
- Easy to modify all material properties in one place

**4. `floor_planner/texture_manager.py`**
- Texture file management with multi-texture support
- Functions:
  - `get_default_textures(element_type)` - Returns dict of default textures per face
  - `resolve_element_textures(element, config_dir)` - Resolves single or multiple textures
  - `copy_texture_to_output(texture_path, output_dir)`
  - `normalize_texture_spec(texture_spec)` - Converts string or dict to dict format
- Design:
  - Elements can specify single texture (string) or multiple textures (dict)
  - Dict keys are face names: 'front', 'back', 'top', 'bottom', 'sides', 'all'
  - Single string uses 'all' key internally
  - Default textures defined per element type with face mappings

#### Element Eligibility

**Generate 3D models for:**
- ✅ Walls (WallND, Wall)
- ✅ Windows
- ✅ Doors
- ✅ Furniture (all types)
- ✅ Appliances
- ✅ Bathroom fixtures
- ✅ Landscaping elements
- ✅ Lighting fixtures
- ✅ Electrical elements

**Exclude from 3D generation:**
- ❌ Info elements (DimensionArrow, TextBox) - height = 0, non-physical
- ❌ Room containers - just coordinate systems, children are generated

**Eligibility check:**
```python
def is_3d_eligible(element: Element) -> bool:
    from .info import DimensionArrow, TextBox
    from .room import Room
    
    if isinstance(element, (DimensionArrow, TextBox, Room)):
        return False
    
    if element.height == 0.0:
        return False
    
    return True
```

#### 3D Geometry Generation

**Rectangular Elements:**
```python
class RectangularGeometry3D:
    def generate_vertices_and_indices(self) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
        """
        Generate 3D vertices and triangle indices for rectangular element.
        
        Uses:
        - anchor_point (x, z) - bottom-left corner in 2D
        - length, width - dimensions
        - orientation_angle - rotation around vertical axis
        - v_anchor - Y coordinate of bottom
        - height - Y extent (top = v_anchor + height)
        
        Returns 8 vertices (bottom 4, top 4) and 12 triangles (2 per face)
        """
        # Bottom rectangle (Y = v_anchor)
        bottom_corners = self._get_rotated_corners(self.anchor_point, 
                                                     self.length, 
                                                     self.width,
                                                     self.orientation_angle)
        
        vertices = []
        # Bottom 4 vertices
        for x, z in bottom_corners:
            vertices.append((x, self.v_anchor, z))
        
        # Top 4 vertices
        for x, z in bottom_corners:
            vertices.append((x, self.v_anchor + self.height, z))
        
        # Generate triangle indices for 6 faces (12 triangles)
        indices = self._generate_box_indices()
        
        return vertices, indices
```

**Circular Elements:**
```python
class CircularGeometry3D:
    CIRCLE_SEGMENTS = 16  # Number of vertices around circle
    
    def generate_vertices_and_indices(self) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]]]:
        """
        Generate 3D vertices for circular element.
        
        Returns:
        - 32 vertices (16 bottom circle + 16 top circle)
        - N triangles for sides + triangulated top/bottom
        """
        center_x, center_z = self.anchor_point
        radius = self.diameter / 2
        
        vertices = []
        
        # Bottom circle (Y = v_anchor)
        for i in range(self.CIRCLE_SEGMENTS):
            angle = 2 * math.pi * i / self.CIRCLE_SEGMENTS
            x = center_x + radius * math.cos(angle)
            z = center_z + radius * math.sin(angle)
            vertices.append((x, self.v_anchor, z))
        
        # Top circle (Y = v_anchor + height)
        for i in range(self.CIRCLE_SEGMENTS):
            angle = 2 * math.pi * i / self.CIRCLE_SEGMENTS
            x = center_x + radius * math.cos(angle)
            z = center_z + radius * math.sin(angle)
            vertices.append((x, self.v_anchor + self.height, z))
        
        # Generate indices for cylinder sides and caps
        indices = self._generate_cylinder_indices()
        
        return vertices, indices
```

**Surface Elements:**
```python
class SurfaceGeometry3D:
    def generate_vertices_and_indices(self):
        """
        Generate 3D geometry for surface elements (lawns, paths, decks).
        
        Note: SurfaceElement uses 'width' instead of 'thickness' for semantic clarity,
        but the 3D geometry generation is identical to RectangularGeometry3D.
        
        Surface elements still have height > 0 to be generated (e.g., lawn height = 0.05m,
        path height = 0.02m, deck height = 0.3m).
        
        Uses:
        - anchor_point (x, z) - bottom-left corner
        - length, width - horizontal dimensions
        - orientation_angle - rotation
        - v_anchor - Y coordinate of bottom (typically 0.0 for ground level)
        - height - Y extent (even if small)
        
        Returns same structure as RectangularGeometry3D: 8 vertices, 12 triangles
        """
        # Implementation is identical to RectangularGeometry3D
        # (width is already mapped to thickness in parent class)
        pass
```

#### OBJ File Format

```
# floor_plan.obj
mtllib floor_plan.mtl

# Vertices (v x y z)
v 0.0 0.0 0.0
v 5.0 0.0 0.0
v 5.0 2.7 0.0
v 0.0 2.7 0.0
...

# Texture coordinates (vt u v)
vt 0.0 0.0
vt 1.0 0.0
vt 1.0 1.0
vt 0.0 1.0
...

# Normals (vn x y z)
vn 0.0 1.0 0.0
vn 0.0 -1.0 0.0
vn 1.0 0.0 0.0
...

# Object: wall_1
o wall_1
usemtl wall_material
f 1/1/1 2/2/1 3/3/1
f 1/1/1 3/3/1 4/4/1
...

# Object: door_2 with multiple materials (front/back faces)
o door_2
usemtl door_front_material
f 5/5/3 6/6/3 7/7/3  # Front face
f 5/5/3 7/7/3 8/8/3
usemtl door_back_material
f 9/9/4 10/10/4 11/11/4  # Back face
f 9/9/4 11/11/4 12/12/4
usemtl door_frame_material
f 13/13/5 14/14/5 15/15/5  # Frame
...

# Object: desk_5
o desk_5
usemtl desk_top_material
f 20/16/6 21/17/6 22/18/6  # Top surface
usemtl desk_sides_material
f 23/19/7 24/20/7 25/21/7  # Sides
...
```

#### MTL File Format

```
# floor_plan.mtl

# Material: wall_material
newmtl wall_material
Ka 0.8 0.8 0.8          # Ambient color (from material_properties.py)
Kd 0.9 0.9 0.9          # Diffuse color
Ks 0.1 0.1 0.1          # Specular color
Ns 10.0                 # Shininess
map_Kd textures/defaults/wall.jpg  # Diffuse texture

# Door with multiple materials (front, back, frame)
newmtl door_front_material
Ka 0.5 0.3 0.2          # Brown wood ambient
Kd 0.6 0.4 0.25         # Wood diffuse (from material_properties.py)
Ks 0.2 0.2 0.2          # Low specular
Ns 25.0                 # Low-medium shininess
map_Kd textures/door_oak_front.jpg

newmtl door_back_material
Ka 0.5 0.3 0.2
Kd 0.6 0.4 0.25
Ks 0.2 0.2 0.2
Ns 25.0
map_Kd textures/door_oak_back.jpg

newmtl door_frame_material
Ka 0.6 0.6 0.6
Kd 0.8 0.8 0.8
Ks 0.1 0.1 0.1
Ns 15.0
map_Kd textures/door_frame.jpg

# Desk with multiple materials (top, sides)
newmtl desk_top_material
Ka 0.5 0.3 0.2          # Brown wood ambient
Kd 0.6 0.4 0.25         # Wood diffuse (from material_properties.py)
Ks 0.2 0.2 0.2          # Low specular
Ns 25.0                 # Low-medium shininess
map_Kd textures/desk_oak_top.jpg

newmtl desk_sides_material
Ka 0.5 0.3 0.2
Kd 0.6 0.4 0.25
Ks 0.2 0.2 0.2
Ns 25.0
map_Kd textures/desk_oak_sides.jpg

newmtl refrigerator_material
Ka 0.85 0.85 0.85       # Metallic white ambient
Kd 0.9 0.9 0.9          # Stainless/white diffuse (from material_properties.py)
Ks 0.6 0.6 0.6          # High specular (metal)
Ns 150.0                # High shininess
map_Kd textures/custom/fridge_front.jpg
```

**Material Properties Source:**
All Ka, Kd, Ks, Ns values come from `floor_planner/material_properties.py`, which provides
default material definitions for each element type. This keeps all material properties
organized in one place and makes them easy to modify.

### Texture System

**Directory Structure:**
```
3d_models/
  ├── floor_plan.obj
  ├── floor_plan.mtl
  └── textures/
      ├── defaults/           # AI-generated default textures (copy)
      │   ├── wall.jpg
      │   ├── door.jpg
      │   ├── window.jpg
      │   ├── desk.jpg
      │   ├── refrigerator.jpg
      │   ├── stove.jpg
      │   ├── toilet.jpg
      │   ├── bathtub.jpg
      │   └── ... (one per element type)
      └── custom/             # User-provided textures (copy)
          ├── brick_wall.jpg
          └── wood_floor.jpg
```

**Dummy Texture Generation (Phase 1-5):**
- Create simple placeholder textures for testing
- Solid colors or very simple patterns
- Generation methods:
  - Copy same solid color image for all types
  - Use Python PIL/Pillow to generate 512x512 solid color images
  - Use free/public domain textures from texture libraries
  - Manual creation in GIMP/Photoshop (very quick)
- Priority: Functionality over appearance
- Simple color coding:
  - wall.jpg: light gray (#DDDDDD)
  - door.jpg: brown (#8B6F47)
  - window.jpg: light blue (#B0E0E6)
  - "White porcelain toilet, front view, bathroom fixture"
- Generated once, committed to repo
- 1024x1024 or 512x512 resolution

**Texture Coordinate Generation:**
- Simple box mapping for rectangular elements
- Cylindrical mapping for circular elements
- UVs normalized 0.0 - 1.0

## Implementation Plan

### Phase 1: Foundation (4-5 days) ✅ COMPLETED

**Setup and Core Structure:**
- [x] Add `visualisation_dir` option to YAML (COMPLETED)
- [x] Create `floor_planner/obj_exporter.py` module
- [x] Create `floor_planner/geometry_3d.py` with mixin classes
- [x] Create `floor_planner/material_properties.py` (COMPLETED)
- [x] Create `floor_planner/texture_manager.py` with multi-texture support
  - [x] Design texture specification format (string or dict)
  - [x] Implement `normalize_texture_spec()` for flexible input
  - [x] Support face-specific textures ('front', 'back', 'top', 'sides', etc.)
  - [x] Default texture mappings per element type
- [x] Add `Generate3DMixin` abstract base class
- [x] Implement `is_3d_eligible()` function

**Basic Geometry Generation:**
- [x] Implement `RectangularGeometry3D` mixin
  - [x] `generate_vertices_and_indices()` method
  - [x] Rotation handling
  - [x] Box face generation (6 faces, 12 triangles)
- [x] Implement `CircularGeometry3D` mixin
  - [x] 16-segment circle generation
  - [x] Cylinder side faces
  - [x] Top/bottom cap triangulation
- [x] Implement `SurfaceGeometry3D` mixin
  - [x] Same as RectangularGeometry3D (width maps to thickness)
  - [x] Verify height > 0 for all surface elements

### Phase 2: Element Integration (5-6 days) ✅ COMPLETED

**Update Base Classes:**
- [x] Add geometry mixin to `RectangularElement`
  - Should inherit both `RectangularElement` and `RectangularGeometry3D`
- [x] Add geometry mixin to `CircularElement`
- [x] Add geometry mixin to `SurfaceElement`
- [x] Add `textures` parameter to Element base class (replaces old `texture`)
  - Type: `str | dict[str, str] | None`
  - String: single texture for all faces
  - Dict: face-specific textures (e.g., {'front': 'door_front.jpg', 'back': 'door_back.jpg'})
  - None: use default textures from texture manager
  - Normalized internally to dict format for consistent processing

**Test with Core Elements:**
- [x] Update `WallND` to generate 3D geometry
- [x] Update `Window` to generate 3D geometry
- [x] Update `Door` to generate 3D geometry
- [x] Test vertex/index generation for these elements

**Dummy Texture System:**
- [x] Implement `TextureManager` class with multi-texture support
- [x] Add `get_default_textures(element_type)` function returning dict
- [x] Add `resolve_element_textures()` for single/multi texture resolution
- [x] Add texture path resolution logic
- [x] Define default face mappings per element type
  - Doors: front, back, frame
  - Desks/Tables: top, sides
  - Walls: all (single texture)
- [x] Create simple dummy textures (solid colors or basic patterns)
  - [x] Generate with PIL: 512x512 solid color images
  - [x] Store in `textures/defaults/` directory (45 textures generated)
  - [ ] Commit to repo (small file sizes with solid colors)
  - Example colors:
    - wall.jpg: #DDDDDD (light gray)
    - door.jpg: #8B6F47 (brown)
    - window.jpg: #B0E0E6 (light blue)
    - desk.jpg: #8B6F47 (wood brown)
    - refrigerator.jpg: #F0F0F0 (white)
- [x] Test that textures load and apply correctly in OBJ/MTL

### Phase 3: OBJ/MTL Export (4-5 days) ✅ COMPLETED

**File Generation:**
- [x] Implement OBJ file header generation
- [x] Implement vertex writing (v x y z)
- [x] Implement texture coordinate writing (vt u v)
- [x] Implement normal writing (vn x y z)
- [x] Implement face writing (f v1/vt1/vn1 v2/vt2/vn2 ...)
- [x] Add object grouping (o object_name)
- [x] Implement MTL file generation
  - [x] Material definitions using material_properties.py
  - [x] Import Ka, Kd, Ks, Ns from get_material_properties()
  - [x] Texture references (map_Kd)

**Integration:**
- [x] Add `export_to_obj()` method to `Project` class
- [x] Call from `__main__.py` when `visualisation_dir` is set
- [x] Handle coordinate system mapping (Floor Planner → OBJ)
  - X → X (same)
  - Y (vertical in FP) → Y (vertical in OBJ)
  - Z (north in FP) → Z (north in OBJ)

### Phase 4: Expand Element Coverage (3-4 days) ✅ COMPLETED

**Furniture:**
- [x] Update all furniture classes (21 classes)
  - Already have VertInfoLvl03 and height
  - Inherited geometry generation from base classes automatically

**Landscaping:**
- [x] Update landscaping classes (13 classes)
  - Trees, shrubs (circular)
  - Paths, lawns (surface)
  - Pools, fountains (rectangular/circular)
  - All inherited from base classes

**Fixtures:**
- [x] Update electrical elements
- [x] Update lighting elements

### Phase 5: Testing & Refinement (2-3 days) ✅ COMPLETED

**Verify Core Functionality:**
- [x] Test OBJ/MTL generation with all element types
- [x] Verify geometry correctness (dimensions, rotation)
- [x] Test material properties application
- [x] Verify dummy textures work correctly
- [x] Import generated models into 3D software (manual testing):
  - **Blender** (free, powerful) - best for detailed inspection, proper material preview
  - **SketchUp Free** (web-based) - quick verification without installation
  - **Online OBJ viewers** (e.g., 3dviewer.net, clara.io) - fastest for smoke testing
  - Verify: geometry dimensions, element positioning, texture application, no missing/inverted faces
  - Test file available: visualisation_3d/test_3d_export.obj
- [x] Fix any geometry or export issues

**Texture List (Priority Order):**
1. Structural (5 textures)
   - wall.jpg
   - door.jpg
   - window.jpg
   - floor.jpg
   - ceiling.jpg

2. Furniture (10 textures)
   - desk.jpg
   - chair.jpg
   - sofa.jpg
   - bed.jpg
   - table.jpg
   - wardrobe.jpg
   - bookshelf.jpg
   - dresser.jpg
   - nightstand.jpg
   - tvstand.jpg

3. Appliances (8 textures)
   - refrigerator.jpg
   - stove.jpg
   - oven.jpg
   - dishwasher.jpg
   - washer.jpg
   - dryer.jpg
   - microwave.jpg
   - rangehood.jpg

4. Bathroom (5 textures)
   - toilet.jpg
   - sink.jpg
   - bathtub.jpg
   - shower.jpg
   - bidet.jpg

5. Landscaping (8 textures)
   - tree.jpg
   - shrub.jpg
   - hedge.jpg
   - lawn.jpg
   - path.jpg
   - deck.jpg
   - fence.jpg
   - pool.jpg

**Total: ~36 default textures**

### Phase 6: Advanced Features (4-5 days) ✅ PARTIALLY COMPLETE

**Custom Geometry Overrides:** (Deferred - not critical for initial release)
- [ ] Allow elements to override `generate_vertices_and_indices()`
- [ ] Implement complex shapes:
  - [ ] Door with frame and handle
  - [ ] Window with panes
  - [ ] Toilet with curved surfaces
  - [ ] Bathtub with curved edges

**Texture Validation:** ✅ COMPLETE
- [x] Validate texture file paths exist
- [x] Validate texture dict keys match element's face definitions  
- [x] Generate warnings for missing textures (fall back to defaults)

**Optimization:** ✅ PARTIALLY COMPLETE
- [ ] Merge adjacent walls into single mesh (deferred - complex)
- [ ] Generate LOD (Level of Detail) versions (deferred - overkill for floor plans)
- [x] Optimize vertex count for circular elements (configurable segments)

**Additional Improvements:**
- [x] Elements with `color == 'invisible'` excluded from 3D generation
- [x] Elements with zero dimensions (length/thickness/diameter) excluded
- [x] Configurable `circle_segments` parameter for circular elements (3-64 range)
- [x] Created example configurations in `examples/3d_visualization/`

### Phase 7: Realistic Texture Generation with AI (2-3 days) - DEFERRED ⏸️

**Status:** Deferred - automated scripts provided, can be executed when needed

**Multiple Automation Options Available:**

See detailed guide: [docs/TEXTURE_GENERATION.md](../TEXTURE_GENERATION.md)

**Recommended: DALL-E API Automation** (Easiest & Fastest)
- [ ] Install dependencies: `pip install openai pillow`
- [ ] Set API key: `export OPENAI_API_KEY="sk-..."`
- [ ] Run script: `python scripts/generate_textures_dalle.py`
- [ ] Cost: ~$1.60 for all 40 textures (1024x1024)
- [ ] Time: ~5 minutes total

**Alternative Options:**
- **Free Manual:** Use Bing Image Creator / Google ImageFX (4-8 days, tedious)
- **Local Stable Diffusion:** ComfyUI/Automatic1111 (free, requires GPU, complex setup)
- **Stability AI API:** Similar to DALL-E (~$2-4)

**Texture Requirements:**
- [ ] Photorealistic appearance
- [ ] Resolution: 1024x1024 (good quality, manageable file size)
- [ ] Seamless/tileable where appropriate (walls, floors, paths)
- [ ] Correct perspective for each element type
- [ ] Consistent lighting across all textures
- [ ] File format: JPEG (quality 95)

**Implementation Notes:**
- ✅ Automation script ready: `scripts/generate_textures_dalle.py`
- ✅ 40 texture prompts pre-written and optimized
- ✅ Automatic download, resize, and organize
- ✅ Skip already-generated textures (incremental)
- ⚠️ Requires OpenAI API key ($1.60 one-time cost)

**Why Deferred:**
- Not blocking for core 3D functionality
- Dummy textures sufficient for testing
- Can be executed anytime with one command
- Cost is minimal but requires API setup

### Phase 8: Final Documentation & Polish (2-3 days)

### Phase 8: Final Documentation & Polish (2-3 days) - IN PROGRESS

- [x] Create example configuration with 3D output
  - [x] `examples/3d_visualization/simple_room.yml`
  - [ ] `examples/3d_visualization/full_house.yml` (optional - can be added later)
- [ ] Test in 3D software:
  - [ ] Blender import and render
  - [ ] SketchUp import
  - [ ] Online OBJ viewers
- [ ] Update documentation:
  - [ ] Add 3D generation section to README
  - [ ] Document texture system in docs/ (single and multi-texture support)
  - [ ] Add OBJ/MTL reference guide
- [ ] Update element-parameters-reference.md with `textures` parameter (string or dict)
- [x] Update element-parameters-reference.md with `circle_segments` parameter (3-64 range)
- [ ] Add troubleshooting guide for common issues

## Testing Strategy

### Unit Tests
```python
# tests/test_geometry_3d.py
def test_rectangular_geometry_vertices():
    wall = WallND(anchor_point=(0, 0), length=5.0, thickness=0.15)
    vertices, indices = wall.generate_vertices_and_indices()
    assert len(vertices) == 8  # 4 bottom + 4 top
    assert len(indices) == 12  # 6 faces × 2 triangles

def test_circular_geometry_vertices():
    lamp = CeilingLamp(anchor_point=(2, 3), diameter=0.3)
    vertices, indices = lamp.generate_vertices_and_indices()
    assert len(vertices) == 32  # 16 bottom + 16 top
    
def test_element_eligibility():
    arrow = DimensionArrow(...)
    assert not is_3d_eligible(arrow)
    
    wall = Wall(...)
    assert is_3d_eligible(wall)
```

### Integration Tests
- [ ] Generate OBJ file from simple floor plan
- [ ] Verify OBJ syntax is valid
- [ ] Verify MTL references are correct
- [ ] Validate texture paths exist

### Manual Testing
1. **Simple Room Test:**
   - 4 walls, 1 door, 1 window
   - Generate OBJ/MTL
   - Import to Blender
   - Verify geometry and textures

2. **Complex Floor Plan Test:**
   - Multiple rooms with furniture
   - Various element types
   - Custom textures
   - Verify no vertex/index errors

3. **Circular Elements Test:**
   - Ceiling lamps
   - Circular tables
   - Toilet
   - Verify smooth circles

### Example Configurations

**`examples/3d_visualization/simple_room.yml`:**
```yaml
project:
  dpi: 200
  png_dir: "output"
  visualisation_dir: "3d_output"  # Enables 3D generation

default_layout:
  bottom_left_corner: [0, 0]
  top_right_corner: [6, 5]
  scale_numerator: 1
  scale_denominator: 50

floor_plans:
  - title:
      text: "Simple Room 3D"
    elements:
      - type: wall
        anchor_point: [0, 0]
        length: 6.0
        thickness: 0.2
      
      - type: wall
        anchor_point: [0, 0]
        length: 5.0
        thickness: 0.2
        orientation_angle: 90
      
      - type: door
        anchor_point: [2, 0]
        doorway_width: 1.0
        door_width: 0.9
        thickness: 0.2
        # Multi-texture example: different textures for front/back
        textures:
          front: "textures/custom/oak_door_front.jpg"
          back: "textures/custom/oak_door_back.jpg"
        
      - type: desk
        anchor_point: [1, 1]
        length: 1.2
        width: 0.6
        # Multi-texture example: different textures for top/sides
        textures:
          top: "textures/custom/oak_desk_top.jpg"
          sides: "textures/custom/oak_desk_sides.jpg"
      
      - type: chair
        anchor_point: [1.5, 2]
        length: 0.5
        width: 0.5
        # Single texture (string) - applies to all faces
        texture: "textures/custom/leather_chair.jpg"
```

## Open Questions

### Technical Decisions

1. **Coordinate System:**
   - Should Y be up (standard in 3D) or maintain Floor Planner's 2D convention?
   - **Decision:** Use Y-up (standard), map FP's anchor_point → (X, Z) and v_anchor → Y

2. **Texture Coordinates:**
   - Simple box mapping or smart UV unwrapping?
   - **Decision:** Start with simple box mapping, add smart UV in Phase 6

3. **File Organization:**
   - One OBJ per floor plan or one master OBJ for entire project?
   - **Decision:** One OBJ per floor plan (easier to manage, smaller files)

4. **Vertex Precision:**
   - How many decimal places for vertex coordinates?
   - **Decision:** 6 decimal places (millimeter precision)

5. **Normal Generation:**
   - Flat shading or smooth normals?
   - **Decision:** Flat normals for architectural elements (walls, furniture), smooth for decorative elements

### Implementation Questions

6. **Room Handling:**
   - Should rooms generate bounding box geometry?
   - **Decision:** No, rooms are just containers. Generate child elements only.

7. **Overlapping Elements:**
   - Handle Z-fighting (overlapping faces)?
   - **Decision:** Use v_anchor offsets (already implemented) to prevent exact overlap

8. **Texture Resolution:**
   - 512x512, 1024x1024, or 2048x2048?
   - **Decision:** 1024x1024 as default (good quality, manageable size)

9. **Multi-material Elements:**
   - Elements with multiple textures (e.g., desk with different wood for top/sides)?
   - **Decision:** Supported from Phase 1. Design texture system to handle dict of textures from start.
   - Element can specify `texture: "file.jpg"` (single) or `textures: {front: "a.jpg", back: "b.jpg"}` (multi)
   - Internally normalized to dict format for consistent handling

10. **Performance:**
    - Max number of elements before performance issues?
    - **Decision:** Test with 100-200 elements, optimize if needed

### AI Texture Generation

11. **AI Service:**
    - DALL-E 3 (paid, high quality) or Stable Diffusion (free, good quality)?
    - **Decision:** Start with Stable Diffusion (local or HuggingFace API), upgrade to DALL-E if needed

12. **Texture Style:**
    - Photorealistic or stylized/artistic?
    - **Decision:** Photorealistic for structural/furniture, may add stylized option later

13. **Seamless Textures:**
    - Should all textures be seamless/tileable?
    - **Decision:** Yes for surfaces (walls, floors), not critical for furniture (single use)

14. **Texture Licensing:**
    - AI-generated textures okay for open source project?
    - **Decision:** Check AI service terms, likely okay if properly attributed

## Future Enhancements (Post-Implementation)

### Phase 8+: Advanced Features
- [x] Multiple texture support per element (MOVED TO PHASE 1-2, implemented from start)
- [ ] PBR (Physically Based Rendering) materials
  - Normal maps
  - Roughness maps
  - Metallic maps
- [ ] glTF export (more modern format, better for web)
- [ ] FBX export (for Unity/Unreal Engine)
- [ ] Automatic LOD generation
- [ ] Baked lighting/shadows
- [ ] Animation support (opening doors, etc.)

### Integration with 3D Software
- [ ] Blender Python script for automatic import + setup
- [ ] SketchUp plugin
- [ ] Three.js web viewer
- [ ] Unity/Unreal Engine import pipeline

### Procedural Generation
- [ ] Procedural window panes
- [ ] Procedural door panels
- [ ] Procedural furniture details (drawers, handles)
- [ ] Procedural architectural elements (moldings, baseboards)

## References

### OBJ/MTL Format Specifications
- [Wavefront OBJ Format](http://www.martinreddy.net/gfx/3d/OBJ.spec)
- [MTL Material Format](http://paulbourke.net/dataformats/mtl/)

### Similar Implementations
- [Sweet Home 3D](http://www.sweethome3d.com/) - Java-based floor planner with 3D export
- [RoomSketcher](https://www.roomsketcher.com/) - Commercial tool with OBJ export
- [Blender Architecture](https://www.blenderarchitecture.com/) - Architectural modeling techniques

### AI Texture Generation
- [Stable Diffusion](https://github.com/Stability-AI/stablediffusion)
- [DALL-E 3 API](https://platform.openai.com/docs/guides/images)
- [Texture Generation Best Practices](https://80.lv/articles/procedural-textures-best-practices/)

### Python Libraries
- No external dependencies needed (use built-in file I/O)
- Consider `numpy` for matrix operations (already in dependencies)
- Consider `Pillow` for texture validation (already likely in dependencies)

## Success Criteria

1. **Core Functionality:**
   - ✅ Generate valid OBJ/MTL files from floor plans
   - ✅ All eligible elements export correctly
   - ✅ Textures apply correctly in 3D software

2. **Quality:**
   - ✅ Geometry is accurate (matches 2D floor plan dimensions)
   - ✅ Textures are high-quality and appropriate
   - ✅ Files import cleanly into Blender/SketchUp

3. **Usability:**
   - ✅ Simple YAML configuration (just set `visualisation_dir`)
   - ✅ Reasonable default textures for all elements
   - ✅ Easy to override with custom textures

4. **Performance:**
   - ✅ Generate 100-element floor plan in < 5 seconds
   - ✅ OBJ files < 10MB for typical floor plans
   - ✅ Texture set < 50MB total

5. **Compatibility:**
   - ✅ Works with existing YAML configs (backward compatible)
   - ✅ OBJ files open in Blender, SketchUp, and online viewers
   - ✅ All example configs generate successfully


## Implementation Summary

### Phase Overview (3-4 weeks total)

**Phases 1-5: Core 3D Functionality (2-3 weeks)**
- Foundation and geometry generation
- Element integration across all types
- OBJ/MTL export with dummy textures
- Material properties from central configuration
- Testing and refinement

**Phase 6: Advanced Features (4-5 days)**
- Custom geometry overrides for complex shapes
- Texture customization in YAML
- Performance optimization

**Phase 7: Realistic AI Textures (2-3 days)**
- Generate 36 high-quality photorealistic textures
- Replace dummy textures with AI-generated assets
- Use Stable Diffusion or DALL-E for generation
- Final visual polish

**Phase 8: Documentation (2-3 days)**
- Example configurations
- 3D software import guides
- Comprehensive documentation
- Troubleshooting guide

### Key Design Decisions

**1. Multiple Textures Supported from Start (Phase 1-2)**
Elements can specify textures in two ways:
- **Single texture (string):** `texture: "wall.jpg"` - applies to all faces
- **Multiple textures (dict):** `textures: {front: "door_front.jpg", back: "door_back.jpg", frame: "frame.jpg"}`

This design is implemented from Phase 1 to avoid refactoring later. Benefits:
- More realistic rendering (e.g., different wood grain on desk top vs sides)
- Architectural detail (door front/back can differ)
- Internally normalized to dict format for consistent processing
- Backward compatible: single string automatically converted to `{'all': 'texture.jpg'}`

Common face names: `front`, `back`, `top`, `bottom`, `sides`, `left`, `right`, `frame`, `all`

**2. Material Properties in Separate File**
All Ka (ambient), Kd (diffuse), Ks (specular), and Ns (shininess) values are defined in `floor_planner/material_properties.py`. This provides:
- Single source of truth for all material definitions
- Easy modification grouped by element category
- Consistent material appearance across all elements
- Helper functions for element-to-material lookup

**3. Phased Texture Approach**
- **Phases 1-5:** Use very simple dummy textures (solid colors via PIL or copied placeholder.jpg)
  - Priority: Get 3D geometry working correctly
  - Textures are just 512x512 solid color JPEGs
  - Quick to generate, small file size, easy to commit
  - Example: wall.jpg = #DDDDDD, door.jpg = #8B6F47
  
- **Phase 7:** Replace with photorealistic AI-generated textures
  - Use Stable Diffusion or DALL-E 3
  - High quality 1024x1024 resolution
  - ~36 textures covering all element types
  - Proper lighting, seamless tiling where appropriate

This approach unblocks early testing while reserving time for high-quality texture generation at the end.

**4. SurfaceElement Geometry**
SurfaceElement (lawn, path, deck) uses same 3D geometry as RectangularElement:
- `width` parameter maps to `thickness` in parent class
- Still generates 8 vertices (4 bottom + 4 top) and 12 triangles
- Height > 0 even for "flat" surfaces (lawn = 0.05m, path = 0.02m)
- Ensures all elements render as proper 3D objects

### Files Created

**Python Modules:**
1. `floor_planner/material_properties.py` - ✅ COMPLETED
2. `floor_planner/geometry_3d.py` - mixin classes for geometry generation
3. `floor_planner/obj_exporter.py` - OBJ/MTL file writing
4. `floor_planner/texture_manager.py` - texture path resolution

**Textures:**
- `textures/defaults/` - Initially dummy textures, replaced with AI in Phase 7
- `textures/custom/` - User-provided custom textures (optional)

**Documentation:**
- Example configs in `examples/3d_visualization/`
- Updated `docs/element-parameters-reference.md`
- New OBJ/MTL format reference guide

### Next Steps

1. Begin Phase 1: Create geometry_3d.py, obj_exporter.py, texture_manager.py
   - **IMPORTANT:** Design texture_manager.py to handle both single and multi-texture specs from start
   - Implement `normalize_texture_spec()` to convert string → dict format
   - Define standard face names (front, back, top, bottom, sides, etc.)
2. Implement basic geometry generation (RectangularGeometry3D)
   - Track which faces correspond to which texture keys
   - Pass face identifier when applying materials in OBJ export
3. Generate simple dummy textures with PIL (one per face type if needed)
4. Test OBJ export with wall/door/window
   - Test both single texture (wall) and multi-texture (door front/back) elements
5. Continue through phases systematically
6. Save AI texture generation for Phase 7 (near end)
