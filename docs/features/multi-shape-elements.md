# Multi-Shape Elements Feature

**Status**: On Hold  
**Priority**: Medium  
**Complexity**: High  
**Target**: v3.0  
**Note**: Superseded by external-model-integration feature for initial implementation. May revisit for procedural generation of complex shapes.  

## Overview

Implement a compositional architecture where floor plan elements can be built from multiple distinct geometric shapes. Each shape has independent dimensions, textures, and materials, enabling more realistic and detailed 3D representations.

## Motivation

### Current Limitations
- Elements generate single unified meshes
- All faces share the same base texture (supplemental textures exist but limited)
- No way to model complex objects with distinct parts (e.g., door frame vs door wing)
- Fixed geometry patterns don't support compositional designs

### Use Cases
1. **Doors**: Frame + wing + handle (each with different materials)
2. **Windows**: Frame + glass pane + sill (glass transparent, frame opaque)
3. **Furniture**: Desk with separate top, legs, drawers (different wood finishes)
4. **Kitchen**: Cabinets with body + doors + handles
5. **Lighting**: Lamp with base + shade + bulb (different textures/materials)

## Requirements

### Functional Requirements

**FR1**: Elements shall support multiple named sub-shapes  
**FR2**: Each sub-shape shall have independent geometry generation  
**FR3**: Sub-shapes shall support variable dimensions based on element parameters  
**FR4**: Sub-shapes shall support fixed dimensions regardless of element parameters  
**FR5**: Each sub-shape shall have its own texture and material  
**FR6**: Sub-shapes shall be positioned relative to element anchor point  
**FR7**: Sub-shapes shall respect element orientation/rotation  
**FR8**: Sub-shapes shall export as distinct object groups in OBJ format  

### Non-Functional Requirements

 
**NFR2**: Memory - Vertex deduplication to minimize memory overhead  
**NFR3**: Backward Compatibility - Existing single-shape elements must continue to work  
**NFR4**: Extensibility - New shape types easily added without modifying core  

## Architecture Design

### Component Hierarchy

```
Element (e.g., Door)
├── MultiShapeMixin (new)
│   └── define_shapes() → List[ShapeDefinition]
├── RectangularElement (existing)
└── Generate3DMixin (existing, modified)
    └── generate_vertices_and_indices()
        ├── generate_composite_geometry() (new)
        └── generate_single_geometry() (existing)
```

### Core Classes

#### 1. ShapeDefinition

Defines a single geometric shape within a multi-shape element.

```python
@dataclass
class ShapeDefinition:
    """Definition of a sub-shape within a multi-shape element."""
    
    name: str                                    # e.g., 'frame', 'wing', 'knob'
    geometry_type: str                           # 'rectangular', 'circular', 'custom'
    
    # Dimensions (can be callable for dynamic sizing)
    dimensions: dict[str, float | Callable]      # e.g., {'length': 2.0, 'thickness': lambda el: el.thickness}
    
    # Positioning relative to element anchor
    offset: tuple[float, float, float]           # (x, y, z) offset from element anchor
    rotation: float = 0.0                        # Additional rotation in degrees
    
    # Appearance
    texture_name: str | None = None              # Texture key (e.g., 'door_frame')
    material_override: dict | None = None        # Ka, Kd, Ks, Ns overrides
    
    # Geometry generation
    geometry_generator: Callable | None = None   # Custom geometry function
```

#### 2. MultiShapeMixin

Mixin that enables elements to define multiple sub-shapes.

```python
class MultiShapeMixin(ABC):
    """Mixin for elements composed of multiple distinct shapes."""
    
    @abstractmethod
    def define_shapes(self) -> list[ShapeDefinition]:
        """
        Define the sub-shapes that compose this element.
        
        Returns:
            List of ShapeDefinition instances describing each sub-shape.
            
        Example:
            [
                ShapeDefinition(
                    name='frame',
                    geometry_type='rectangular',
                    dimensions={
                        'length': lambda el: el.length,
                        'thickness': lambda el: el.thickness,
                        'height': lambda el: el.height
                    },
                    offset=(0, 0, 0),
                    texture_name='door_frame'
                ),
                ShapeDefinition(
                    name='wing',
                    geometry_type='rectangular',
                    dimensions={
                        'length': lambda el: el.length - 0.1,
                        'thickness': 0.04,  # Fixed 4cm
                        'height': lambda el: el.height - 0.1
                    },
                    offset=(0.05, 0.05, 0.05),
                    texture_name='door_wing'
                ),
            ]
        """
        pass
    
    def is_multi_shape(self) -> bool:
        """Check if element has multiple shapes."""
        return True
```

#### 3. CompositeGeometry3D

New geometry mixin for multi-shape elements.

```python
class CompositeGeometry3D(Generate3DMixin):
    """3D geometry generation for multi-shape elements."""
    
    def generate_vertices_and_indices(self) -> tuple[
        list[tuple[float, float, float]],      # vertices
        list[tuple[int, int, int]],            # indices
        dict[str, list[int]],                  # face_groups
        dict[str, dict]                        # shape_metadata (NEW)
    ]:
        """
        Generate geometry for multi-shape element.
        
        Returns extended tuple with shape_metadata:
            shape_metadata: {
                'frame': {
                    'vertex_range': (0, 8),
                    'face_range': (0, 12),
                    'texture': 'door_frame',
                    'material': {...}
                },
                'wing': {
                    'vertex_range': (8, 16),
                    'face_range': (12, 24),
                    'texture': 'door_wing',
                    'material': {...}
                },
                ...
            }
        """
        # Get shape definitions
        shapes = self.define_shapes()
        
        all_vertices = []
        all_indices = []
        all_face_groups = {}
        shape_metadata = {}
        
        vertex_offset = 0
        face_offset = 0
        
        for shape_def in shapes:
            # Generate geometry for this shape
            shape_vertices, shape_indices, shape_face_groups = \
                self._generate_shape_geometry(shape_def)
            
            # Offset indices
            shape_indices_offset = [
                (i1 + vertex_offset, i2 + vertex_offset, i3 + vertex_offset)
                for i1, i2, i3 in shape_indices
            ]
            
            # Track metadata
            shape_metadata[shape_def.name] = {
                'vertex_range': (vertex_offset, vertex_offset + len(shape_vertices)),
                'face_range': (face_offset, face_offset + len(shape_indices)),
                'texture': shape_def.texture_name,
                'material': shape_def.material_override,
                'face_groups': {
                    group_name: [idx + face_offset for idx in indices]
                    for group_name, indices in shape_face_groups.items()
                }
            }
            
            # Accumulate
            all_vertices.extend(shape_vertices)
            all_indices.extend(shape_indices_offset)
            
            vertex_offset += len(shape_vertices)
            face_offset += len(shape_indices)
        
        # Combine face groups
        for shape_name, meta in shape_metadata.items():
            for group_name, indices in meta['face_groups'].items():
                group_key = f"{shape_name}_{group_name}"
                all_face_groups[group_key] = indices
        
        return all_vertices, all_indices, all_face_groups, shape_metadata
    
    def _generate_shape_geometry(self, shape_def: ShapeDefinition) -> tuple:
        """Generate geometry for a single shape definition."""
        # Resolve dimensions (evaluate callables)
        resolved_dims = {}
        for key, value in shape_def.dimensions.items():
            if callable(value):
                resolved_dims[key] = value(self)
            else:
                resolved_dims[key] = value
        
        # Generate based on geometry type
        if shape_def.geometry_type == 'rectangular':
            return self._generate_rectangular_shape(shape_def, resolved_dims)
        elif shape_def.geometry_type == 'circular':
            return self._generate_circular_shape(shape_def, resolved_dims)
        elif shape_def.geometry_generator:
            return shape_def.geometry_generator(self, shape_def, resolved_dims)
        else:
            raise ValueError(f"Unknown geometry type: {shape_def.geometry_type}")
```

### OBJExporter Integration

Modify `obj_exporter.py` to handle multi-shape elements:

```python
def _write_element_geometry(self, element, element_type):
    """Write element geometry, handling both single and multi-shape."""
    
    if hasattr(element, 'is_multi_shape') and element.is_multi_shape():
        # Multi-shape element
        result = element.generate_vertices_and_indices()
        
        if len(result) == 4:  # New format with metadata
            vertices, indices, face_groups, shape_metadata = result
            
            # Write each shape as separate object group
            for shape_name, meta in shape_metadata.items():
                # Write object group
                self.obj_file.write(f"o {element.id}_{shape_name}\n")
                
                # Get material for this shape
                texture = meta['texture']
                material_name = self._get_or_create_material(
                    texture, element_type, meta['material']
                )
                self.obj_file.write(f"usemtl {material_name}\n")
                
                # Write faces for this shape only
                start_face, end_face = meta['face_range']
                for face_idx in range(start_face, end_face):
                    self._write_face(indices[face_idx])
        else:
            # Backward compatibility: old 3-tuple format
            vertices, indices, face_groups = result
            self._write_single_shape(element, vertices, indices, face_groups)
    else:
        # Single-shape element (existing code path)
        vertices, indices, face_groups = element.generate_vertices_and_indices()
        self._write_single_shape(element, vertices, indices, face_groups)
```

## Proof of Concept: Door with Frame, Wing, and Knob

### Implementation Steps

#### Step 1: Create Door Shape Definitions

```python
# floor_planner/elements/basic.py

class Door(RectangularElement, MultiShapeMixin, CompositeGeometry3D):
    """Door element with frame, wing, and handle."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Door-specific parameters
        self.frame_thickness = kwargs.get('frame_thickness', 0.1)  # 10cm frame
        self.wing_thickness = kwargs.get('wing_thickness', 0.04)   # 4cm wing
        self.handle_height = kwargs.get('handle_height', 1.0)      # 1m from floor
        self.handle_offset = kwargs.get('handle_offset', 0.15)     # 15cm from edge
    
    def define_shapes(self) -> list[ShapeDefinition]:
        """Define door components."""
        return [
            # Door frame (outer rectangle)
            ShapeDefinition(
                name='frame',
                geometry_type='rectangular',
                dimensions={
                    'length': lambda el: el.length,
                    'thickness': lambda el: el.frame_thickness,
                    'height': lambda el: el.height,
                },
                offset=(0, 0, 0),  # Aligned with element anchor
                texture_name='door_frame',
                material_override={
                    'Ka': (0.5, 0.3, 0.2),   # Darker wood
                    'Kd': (0.6, 0.4, 0.25),
                    'Ks': (0.3, 0.3, 0.3),
                    'Ns': 50.0
                }
            ),
            
            # Door wing (inner rectangle, slightly inset)
            ShapeDefinition(
                name='wing',
                geometry_type='rectangular',
                dimensions={
                    'length': lambda el: el.length - 2 * el.frame_thickness,
                    'thickness': lambda el: el.wing_thickness,
                    'height': lambda el: el.height - 2 * el.frame_thickness,
                },
                offset=(
                    lambda el: el.frame_thickness,           # x offset
                    lambda el: el.frame_thickness,           # y offset (bottom)
                    lambda el: el.frame_thickness / 2        # z offset (centered)
                ),
                texture_name='door_wing',
                material_override={
                    'Ka': (0.7, 0.5, 0.3),   # Lighter wood
                    'Kd': (0.8, 0.6, 0.4),
                    'Ks': (0.5, 0.5, 0.5),
                    'Ns': 100.0
                }
            ),
            
            # Door handle (small cylinder)
            ShapeDefinition(
                name='handle',
                geometry_type='circular',
                dimensions={
                    'diameter': 0.05,        # Fixed 5cm diameter
                    'height': 0.12,          # Fixed 12cm length
                },
                offset=(
                    lambda el: el.length - el.handle_offset,  # Near edge
                    lambda el: el.handle_height,               # 1m from floor
                    lambda el: el.thickness / 2                # Centered in depth
                ),
                rotation=90.0,  # Rotate to stick out from door
                texture_name='door_handle',
                material_override={
                    'Ka': (0.7, 0.7, 0.7),   # Metallic gray
                    'Kd': (0.8, 0.8, 0.8),
                    'Ks': (1.0, 1.0, 1.0),   # High specular
                    'Ns': 500.0               # Very shiny
                }
            ),
        ]
```

#### Step 2: Create Textures

```bash
# Frame texture (darker wood)
textures/fallback/door_frame/door_frame.jpg

# Wing texture (lighter wood with panels)
textures/fallback/door_wing/door_wing.jpg

# Handle texture (brushed metal)
textures/fallback/door_handle/door_handle.jpg
```

#### Step 3: Update SUPPLEMENTAL_TEXTURES

```python
# floor_planner/supplemental_textures.py

SUPPLEMENTAL_TEXTURES = {
    'door': ['frame', 'wing', 'handle'],  # Add wing and handle
    'desk': ['sides'],
    'table': ['sides'],
}
```

#### Step 4: Test Configuration

```yaml
# examples/multi_shape/door_demo.yml

project:
  dpi: 300
  file: examples/multi_shape/door_demo.pdf
  visualisation_dir: examples/multi_shape/door_3d

default_layout:
  width: 5
  length: 5
  scale: 50

floor_plans:
  - title: Multi-Shape Door Test
    elements:
      - type: door
        id: door_001
        anchor_point: [2, 2]
        length: 0.9          # 90cm wide
        thickness: 0.2       # 20cm thick (including frame)
        height: 2.1          # 2.1m tall
        orientation_angle: 0
        frame_thickness: 0.1  # 10cm frame
        wing_thickness: 0.04  # 4cm wing
        handle_height: 1.0    # Handle at 1m
        handle_offset: 0.15   # 15cm from edge
```

## Implementation Phases

### Phase 1: Core Infrastructure (Week 1-2)
- [ ] Create `ShapeDefinition` dataclass
- [ ] Implement `MultiShapeMixin` base class
- [ ] Implement `CompositeGeometry3D` mixin
- [ ] Add shape metadata to geometry return signature

### Phase 2: OBJ Export Support (Week 2-3)
- [ ] Modify `OBJExporter` to handle multi-shape elements
- [ ] Implement separate object groups per shape
- [ ] Support per-shape materials
- [ ] Test with simple 2-shape element

### Phase 3: Door Proof of Concept (Week 3-4)
- [ ] Implement `Door` with frame, wing, handle shapes
- [ ] Create door textures (frame, wing, handle)
- [ ] Add door-specific parameters (frame_thickness, etc.)
- [ ] Create test YAML configurations
- [ ] Generate and validate 3D output

### Phase 4: Backward Compatibility (Week 4)
- [ ] Ensure existing single-shape elements work
- [ ] Test all example configurations
- [ ] Performance benchmarking (single vs multi-shape)
- [ ] Update documentation

### Phase 5: Additional Elements (Week 5-6)
- [ ] Convert Window to multi-shape (frame + glass)
- [ ] Convert Desk to multi-shape (top + legs + drawers)
- [ ] Convert Cabinet to multi-shape (body + doors)
- [ ] Add furniture examples

## Testing Strategy

### Unit Tests
- `test_shape_definition.py` - ShapeDefinition creation and validation
- `test_multi_shape_mixin.py` - Shape definition resolution
- `test_composite_geometry.py` - Multi-shape geometry generation
- `test_obj_export_multi_shape.py` - OBJ/MTL export with shapes

### Integration Tests
- Door with all three shapes renders correctly
- Textures applied to correct shapes
- Materials differ between shapes
- OBJ file has proper object groups

### Visual Tests
- Load door OBJ in Blender/MeshLab
- Verify frame, wing, handle are distinct objects
- Verify textures map correctly
- Verify materials look appropriate

### Performance Tests
- Compare single-shape vs 3-shape door rendering time
- Memory usage with 10 multi-shape doors vs 10 single doors
- Ensure < 2x overhead

## Migration Path

### For Existing Elements

**Option 1: Gradual Migration**
- Keep existing single-shape elements working
- Add multi-shape versions as new classes (e.g., `DetailedDoor`)
- Users opt-in by changing element type in YAML

**Option 2: In-Place Enhancement**
- Add `use_detailed_geometry: true` parameter
- Elements check parameter and use multi-shape if enabled
- Default to single-shape for backward compatibility

**Recommended**: Option 2 - allows gradual adoption without breaking changes.

## Configuration Schema

### Element Parameters

New parameters for multi-shape elements:

```yaml
- type: door
  # Standard parameters
  anchor_point: [2, 2]
  length: 0.9
  thickness: 0.2
  height: 2.1
  
  # Multi-shape control
  use_detailed_geometry: true    # Enable multi-shape rendering
  
  # Shape-specific parameters
  frame_thickness: 0.1
  wing_thickness: 0.04
  handle_height: 1.0
  handle_offset: 0.15
  handle_type: 'lever'           # Could support different handle styles
  
  # Per-shape texture overrides (optional)
  textures:
    frame: 'custom_oak_frame.jpg'
    wing: 'custom_oak_panel.jpg'
    handle: 'brushed_nickel.jpg'
```

## Open Questions

1. **Shape Overlapping**: How to handle z-fighting between overlapping shapes?
   - **Proposed**: Use `z_offset` in ShapeDefinition for slight separation
   - **Alternative**: Rely on material/texture differences

2. **Performance at Scale**: What's acceptable performance for complex scenes?
   - **Target**: < 2x slowdown for multi-shape elements
   - **Strategy**: Profile and optimize vertex generation

3. **Material Blending**: Should we support material blending at shape boundaries?
   - **Phase 1**: No blending, distinct shapes
   - **Phase 2**: Consider smooth transitions

4. **Custom Shapes**: How to support truly custom geometry (not rectangular/circular)?
   - **Proposed**: `geometry_generator` callback in ShapeDefinition
   - **Example**: Custom bezier curves for decorative elements

5. **Animation/LOD**: Should multi-shape support level-of-detail?
   - **Not Phase 1**: Keep simple initially
   - **Future**: Could simplify to single shape at distance

## Success Criteria

- [ ] Door renders with 3 distinct shapes in OBJ viewer
- [ ] Each shape has correct texture applied
- [ ] Frame is darker wood, wing is lighter, handle is metallic
- [ ] All existing examples still render correctly
- [ ] Performance overhead < 2x for multi-shape elements
- [ ] Documentation complete for adding new multi-shape elements
- [ ] At least 3 different multi-shape elements implemented

## Dependencies

### New Dependencies
- None (uses existing Python standard library)

### Modified Files
- `floor_planner/elements/geometry_3d.py` - Add CompositeGeometry3D
- `floor_planner/obj_exporter.py` - Handle multi-shape export
- `floor_planner/elements/basic.py` - Update Door class
- `floor_planner/supplemental_textures.py` - Add new texture mappings

### New Files
- `floor_planner/elements/multi_shape.py` - MultiShapeMixin, ShapeDefinition
- `examples/multi_shape/door_demo.yml` - Example configuration
- `docs/multi-shape-guide.md` - User documentation
- `tests/test_multi_shape.py` - Test suite

## References

- Current geometry system: `floor_planner/elements/geometry_3d.py`
- Texture system: `docs/texture-material-system.md`
- OBJ format spec: Wavefront OBJ (v/vt/vn/f/o/g/usemtl)
- Similar systems: Blender's object hierarchy, Unity's GameObject composition

## Future Enhancements

### Phase 2 Features
- Shape templates (reusable shape definitions)
- Shape groups (hierarchical nesting)
- Procedural shape generation (parametric curves)
- Animation support (doors opening, drawers sliding)

### Phase 3 Features
- Material blending at boundaries
- Level-of-detail (LOD) for performance
- Physics properties per shape (for simulation)
- Interactive elements (clickable handles)

---

**Document History**:
- 2026-05-27: Initial planning document created
- Author: AI Assistant (GitHub Copilot)
- Status: Awaiting review and approval for implementation
