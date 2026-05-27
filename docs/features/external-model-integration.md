# External 3D Model Integration

**Status**: Planning  
**Priority**: High  
**Complexity**: Very High  
**Target**: v2.0  

## Overview

Implement a hybrid rendering system where floor plan elements can reference pre-made external 3D models instead of generating geometry procedurally. This enables high-quality, artist-created assets (chairs, appliances, decorative objects) to be integrated into floor plans while maintaining the flexibility of procedural generation for architectural elements (walls, floors, basic shapes).

## Motivation

### Current Limitations
- All geometry is procedurally generated (boxes, cylinders)
- Limited realism for complex objects (furniture, appliances, decorations)
- No way to use professionally created 3D assets
- Difficult to model intricate details (chair legs, door panels, appliance controls)

### Use Cases
1. **High-quality furniture**: Import detailed chair/table/sofa models from 3D libraries
2. **Kitchen appliances**: Realistic refrigerator, oven, dishwasher models
3. **Decorative objects**: Lamps, plants, artwork with complex geometry
4. **Mixed approach**: Procedural walls/floors + external furniture models
5. **Asset reuse**: Library of models shared across projects
6. **Future animations**: Doors that open, drawers that slide (defined in model)

## Problem Analysis & Solutions

### Problem 1: Scale and Position Normalization

**Issue**: External models come in arbitrary scales, positions, and orientations.
- Model A: 1 unit = 1 meter, origin at base center
- Model B: 1 unit = 1 centimeter, origin at geometric center
- Model C: 1 unit = 1 inch, origin at back-left corner

**Solution**: Model Metadata with Normalization Transform

Each external model has companion `.transform.json` file:
```json
{
  "model_file": "office_chair.obj",
  "units": "meters",
  "normalization": {
    "matrix": [
      [1.0, 0.0, 0.0, 0.0],
      [0.0, 1.0, 0.0, 0.0],
      [0.0, 0.0, 1.0, 0.0],
      [0.0, 0.0, 0.0, 1.0]
    ],
    "description": "4x4 transformation matrix (provided externally with model)"
  },
  "anchor_point": "bottom_center",
  "anchor_point_description": "Semantic reference for YAML config positioning",
  "bounding_box": {
    "min": [-0.3, 0.0, -0.3],
    "max": [0.3, 0.9, 0.3],
    "description": "Axis-aligned bounding box for collision detection and UI display"
  }
}
```

**Normalization process:**
1. Load model in original scale/position
2. Apply normalization transform from `.transform.json` (4x4 matrix provided externally by model creator)
3. Normalization brings model to standard: 1 unit = 1m, Y-up, origin at floor center
4. Model now ready for scene placement (from YAML config)

**Purpose of metadata fields:**
- **`normalization.matrix`**: 4x4 transformation matrix (column-major) provided by model creator. Converts model from arbitrary coordinate system to standard space. GPU-ready format.
- **`anchor_point`**: Semantic label ("bottom_center", "center", "back_left") for documentation. Helps users understand where YAML `anchor_point` positions the model.
- **`bounding_box`**: Axis-aligned bounding box in normalized space. Used for:
  - Collision detection during floor plan layout
  - UI visualization (show model extents before placement)
  - Automatic dimension calculation (`width = max[0] - min[0]`)
  - Spatial queries ("find all elements in this area")

### Problem 2: Non-Scalable Elements

**Issue**: Pre-made models have fixed dimensions (can't stretch a chair from 0.5m to 2m).

**Solution**: Fixed-Size Element Classes

```python
class ExternalModelElement(Element):
    """Element that uses external 3D model."""
    
    # Properties inherited from Element (read from .transform.json)
    # width: float       # Calculated from bounding_box, read-only for external models
    # length: float      # Calculated from bounding_box, read-only for external models  
    # height: float      # Calculated from bounding_box, read-only for external models
    
    # User-configurable properties
    anchor_point: tuple      # Where to place in floor plan
    orientation_angle: float # Rotation around vertical axis
    v_anchor: float         # Vertical position
    
    # Model reference
    model_path: str         # Path to external model file
    
    def __init__(self, model_path: str, *args, **kwargs):
        # Load model metadata
        metadata = self._load_model_metadata(model_path)
        
        # Calculate dimensions from bounding box
        bbox = metadata['bounding_box']
        calculated_width = bbox['max'][0] - bbox['min'][0]
        calculated_length = bbox['max'][2] - bbox['min'][2]
        calculated_height = bbox['max'][1] - bbox['min'][1]
        
        # Reject user attempts to override dimensions
        if 'width' in kwargs or 'length' in kwargs or 'height' in kwargs:
            raise ValueError(
                f"Cannot set dimensions for external model element. "
                f"Dimensions are fixed by model: {calculated_width:.2f}m × "
                f"{calculated_length:.2f}m × {calculated_height:.2f}m (W×L×H)"
            )
        
        # Set dimensions from metadata (parent Element expects these)
        kwargs['width'] = calculated_width
        kwargs['length'] = calculated_length
        kwargs['height'] = calculated_height
        
        super().__init__(*args, **kwargs)
```

**YAML Configuration:**
```yaml
- type: office_chair
  id: chair_001
  anchor_point: [2, 3]
  orientation_angle: 45
  v_anchor: 0.0
  # NO width/length/height - these are read from model metadata
```

### Problem 3: Scene Composition Transform

**Issue**: 3D viewer needs to know where to place each model instance in the scene.

**Solution**: Hierarchical Transform Chain

```
Final Transform = Scene Placement × Model Normalization
                = (User Position/Rotation) × (Standardization)
```

**Example:**
```python
# 1. Normalization transform (from .transform.json - provided externally with model)
# This 4x4 matrix is created by the model author/curator
normalization_matrix = np.array([
    [0.01,  0.0,  0.0, 0.0],  # Scale from cm to m + X-axis
    [0.0,   0.0, 0.01, 0.0],  # Rotate Z-up to Y-up + Y-axis  
    [0.0, -0.01,  0.0, 0.0],  # + Z-axis
    [0.0,  -0.5,  0.0, 1.0]   # Translate origin to base + translation
])  # Column-major 4x4 matrix (GPU-standard)

# 2. Scene placement (from YAML config - user specifies in floor plan)
# Generated as 4x4 matrix from user's anchor_point, orientation_angle, v_anchor
placement_matrix = np.array([
    [cos(45°), 0.0, -sin(45°), 0.0],  # Rotation around Y-axis (orientation_angle)
    [0.0,      1.0,  0.0,      0.0],  # Y-axis (vertical)
    [sin(45°), 0.0,  cos(45°), 0.0],  # Rotation component
    [2.0,      0.0,  3.0,      1.0]   # Translation (anchor_point [2,3] + v_anchor 0.0)
])  # 4x4 matrix

# 3. Combined transform for 3D viewer
# Order: placement × normalization (right-to-left application)
final_transform = placement_matrix @ normalization_matrix
```

**Scene Placement Matrix Generation:**
```python
def create_placement_matrix(anchor_point: tuple[float, float], 
                           orientation_angle: float, 
                           v_anchor: float) -> np.ndarray:
    """
    Generate 4x4 placement matrix from YAML config parameters.
    
    Args:
        anchor_point: (x, z) position in floor plan coordinates
        orientation_angle: Rotation around vertical Y-axis (degrees)
        v_anchor: Vertical position (Y-coordinate)
        
    Returns:
        4x4 column-major transformation matrix
    """
    angle_rad = np.radians(orientation_angle)
    cos_a = np.cos(angle_rad)
    sin_a = np.sin(angle_rad)
    
    # 4x4 matrix: rotation around Y-axis + translation
    # Column-major order (GPU-standard)
    matrix = np.array([
        [cos_a,  0.0,  -sin_a, 0.0],           # X-axis after rotation
        [0.0,    1.0,   0.0,   0.0],           # Y-axis (vertical, unchanged)
        [sin_a,  0.0,   cos_a, 0.0],           # Z-axis after rotation
        [anchor_point[0], v_anchor, anchor_point[1], 1.0]  # Translation
    ])
    
    return matrix
```

**Transform Source Clarification:**
- **Normalization matrix**: Provided externally by model creator in `.transform.json`. Fixed for each model. Converts from model's native coordinate system to standard space (Y-up, 1m units, floor-centered origin).
- **Placement matrix**: Generated at export time from YAML configuration. User specifies `anchor_point`, `orientation_angle`, `v_anchor` in floor plan YAML. Converted to 4x4 matrix using the function above.

### Problem 4: Multi-Model Scene Description Format

**Issue**: Need unified format that 3D viewers can parse to reconstruct the scene.

**Solution**: glTF 2.0 Scene Graph

**Why glTF 2.0?**
- Industry standard (Khronos Group)
- Supports multi-model scenes natively
- Rich transformation system (TRS: Translation, Rotation, Scale)
- Material support (PBR: Physically Based Rendering)
- Animation support (for future door opening, etc.)
- Widely supported (Blender, Three.js, Unity, Unreal Engine, web viewers)
- JSON format (human-readable, easy to parse)
- Excellent C++ parsing support (see C++ Libraries section below)

**Decision**: Use glTF 2.0 JSON format for all multi-model scene exports.

### C++ glTF Libraries

**Question**: Is glTF easily parsable from C++?

**Answer**: Yes, glTF has excellent C++ support with multiple mature libraries:

1. **tinygltf** (Recommended)
   - URL: https://github.com/syoyo/tinygltf
   - License: MIT
   - Header-only library (single `tiny_gltf.h` file)
   - Full glTF 2.0 support (JSON format)
   - Minimal dependencies (C++11 standard library only)

2. **fx-gltf**
   - URL: https://github.com/jessey-git/fx-gltf
   - License: MIT
   - Header-only, modern C++14
   - Type-safe API

3. **cgltf**
   - URL: https://github.com/jkuhlmann/cgltf
   - License: MIT
   - Single-file C library (C++ compatible)
   - Read-only, very lightweight

4. **Assimp**
   - URL: https://github.com/assimp/assimp
   - License: BSD
   - Supports 40+ formats including glTF
   - Large dependency, unified API

### Problem 5: Future Animation Support

**Issue**: Need to prepare for interactive elements (doors opening, drawers sliding).

**Solution**: Animation Metadata in Model Files

**glTF Animation Structure:**
```json
{
  "animations": [
    {
      "name": "door_open",
      "channels": [
        {
          "sampler": 0,
          "target": {
            "node": 3,  // door_wing node
            "path": "rotation"
          }
        }
      ],
      "samplers": [
        {
          "input": 0,   // time keyframes
          "output": 1,  // rotation keyframes
          "interpolation": "LINEAR"
        }
      ]
    }
  ]
}
```

**Element Metadata:**
```json
{
  "model_file": "door_with_frame.glb",
  "interactions": {
    "door_open": {
      "type": "animation",
      "animation_name": "door_open",
      "trigger": "click",
      "duration": 1.0,
      "reversible": true,
      "default_state": "closed"
    },
    "drawer_slide": {
      "type": "animation",
      "animation_name": "drawer_1_open",
      "trigger": "click",
      "duration": 0.5
    }
  }
}
```

**Phase 1**: Export animations to glTF, don't implement triggers  
**Phase 2**: Implement web viewer with animation playback  
**Phase 3**: Add UI triggers (click to open door)  

## Architecture Design

### System Components

```
Floor Planner
├── Element Registry
│   ├── Procedural Elements (existing)
│   │   ├── Wall, Door, Window
│   │   └── Generate geometry at export time
│   └── External Model Elements (new)
│       ├── Chair, Table, Appliance
│       └── Reference external files
│
├── Model Library
│   ├── models/
│   │   ├── chair/                    # Registry key from create_elements_registry()
│   │   │   ├── model.glb             # External 3D model
│   │   │   └── model.transform.json  # Normalization metadata
│   │   ├── desk/
│   │   │   ├── model.glb
│   │   │   └── model.transform.json
│   │   ├── external_model_test/      # Test element
│   │   │   ├── model.glb             # Simple test cube
│   │   │   └── model.transform.json  # Test metadata
│   │   ├── fridge/
│   │   │   ├── model.glb
│   │   │   └── model.transform.json
│   │   └── [element_type]/           # One folder per registry key
│   └── textures/
│
├── Export System
│   ├── OBJ Exporter (existing)
│   │   └── Exports procedural geometry
│   └── glTF Exporter (new)
│       ├── Scene graph builder
│       ├── Model reference linker
│       ├── Transform calculator
│       └── Animation embedder
│
└── 3D Viewer Integration
    ├── Web Viewer (Three.js + glTF)
    ├── Desktop Viewer (Blender, MeshLab)
    └── VR/AR Viewer (future)
```

### Class Hierarchy

```python
# New base class for external models
class ExternalModelElement(Element):
    """Element that references an external 3D model file."""
    
    model_path: str
    model_metadata: dict
    # width, length, height inherited from Element (calculated from bounding_box)
    
    def __init__(self, model_path: str, **kwargs):
        self.model_path = model_path
        self.model_metadata = self._load_metadata()
        self._set_fixed_dimensions()
        super().__init__(**kwargs)
    
    def _load_metadata(self) -> dict:
        """Load .transform.json metadata file."""
        metadata_path = self.model_path.replace('.glb', '.transform.json')
        with open(metadata_path) as f:
            return json.load(f)
    
    def _set_fixed_dimensions(self):
        """Set dimensions from bounding box (read-only for external models)."""
        bbox = self.model_metadata['bounding_box']
        self.width = bbox['max'][0] - bbox['min'][0]
        self.length = bbox['max'][2] - bbox['min'][2]
        self.height = bbox['max'][1] - bbox['min'][1]
    
    def get_normalization_transform(self) -> np.ndarray:
        """Get 4x4 normalization matrix from metadata."""
        matrix = self.model_metadata['normalization']['matrix']
        return np.array(matrix)  # 4x4 matrix (column-major)
    
    def get_placement_transform(self) -> np.ndarray:
        """Get 4x4 placement matrix from element configuration."""
        return create_placement_matrix(
            anchor_point=self.anchor_point,
            orientation_angle=self.orientation_angle,
            v_anchor=self.v_anchor
        )

# Specific element types
# No separate classes needed - existing classes (Chair, Desk, etc.) can use external models
# Element type from YAML 'type' field maps to registry key, which determines model folder
# Example: type='chair' → models/chair/model.glb
#          type='desk' → models/desk/model.glb
#          type='fridge' → models/fridge/model.glb
#          type='external_model_test' → models/external_model_test/model.glb
#
# For test element: ExternalModelTest class implements simple 2D rect drawing
# When model.glb exists, also exports to 3D; otherwise uses procedural 2D rect only
```

### Model Metadata Format

**File: `models/furniture/office_chair.transform.json`**
```json
{
  "model_file": "office_chair.glb",
  "format_version": "1.0",
  "element_type": "chair",
  
  "units": "meters",
  "up_axis": "Y",
  
  "normalization": {
    "description": "4x4 transformation matrix to bring model to standard coordinate system",
    "matrix": [
      [1.0, 0.0, 0.0, 0.0],
      [0.0, 1.0, 0.0, 0.0],
      [0.0, 0.0, 1.0, 0.0],
      [0.0, 0.0, 0.0, 1.0]
    ]
  },
  
  "anchor_point": "bottom_center",
  "anchor_offset": [0, 0, 0],
  
  "bounding_box": {
    "min": [-0.3, 0.0, -0.3],
    "max": [0.3, 0.9, 0.3]
  },
  
  "dimensions": {
    "width": 0.6,
    "length": 0.6,
    "height": 0.9
  },
  
  "visual_properties": {
    "color": [0.6, 0.4, 0.2],
    "material_type": "leather",
    "thumbnail": "office_chair_thumbnail.png"
  },
  
  "interactions": {
    "rotate": {
      "type": "animation",
      "animation_name": "chair_rotate",
      "axis": "Y",
      "range": [0, 360],
      "default": 0
    }
  },
  
  "metadata": {
    "author": "3D Artist Name",
    "license": "CC-BY-4.0",
    "source": "https://example.com/models/chair",
    "created": "2026-01-15",
    "tags": ["furniture", "chair", "office", "swivel"]
  }
}
```

### glTF Scene Export Format

**Generated file: `floor_plan_3d.gltf`**
```json
{
  "asset": {
    "version": "2.0",
    "generator": "Floor Planner v2.0"
  },
  
  "scene": 0,
  "scenes": [
    {
      "name": "Floor Plan Scene",
      "nodes": [0, 1, 2, 3]
    }
  ],
  
  "nodes": [
    {
      "name": "wall_001",
      "mesh": 0,
      "translation": [0, 0, 0]
    },
    {
      "name": "chair_001",
      "mesh": 1,
      "translation": [2.0, 0.0, 3.0],
      "rotation": [0, 0.7071, 0, 0.7071],
      "extras": {
        "element_type": "office_chair",
        "source_model": "models/furniture/office_chair.glb",
        "floor_plan_id": "chair_001"
      }
    },
    {
      "name": "chair_001_base",
      "parent": 1,
      "mesh": 2,
      "translation": [0, -0.5, 0],
      "rotation": [0.7071, 0, 0, 0.7071],
      "scale": [0.01, 0.01, 0.01]
    }
  ],
  
  "meshes": [
    {
      "name": "wall_001_geometry",
      "primitives": [
        {
          "attributes": {
            "POSITION": 0,
            "NORMAL": 1,
            "TEXCOORD_0": 2
          },
          "indices": 3,
          "material": 0
        }
      ]
    },
    {
      "name": "office_chair",
      "extras": {
        "external_model": true,
        "source": "models/furniture/office_chair.glb"
      }
    }
  ],
  
  "materials": [
    {
      "name": "wall_material",
      "pbrMetallicRoughness": {
        "baseColorTexture": {
          "index": 0
        },
        "metallicFactor": 0.0,
        "roughnessFactor": 0.9
      }
    }
  ],
  
  "animations": [
    {
      "name": "chair_001_rotate",
      "channels": [...],
      "samplers": [...]
    }
  ]
}
```

## Implementation Plan

### Phase 1: Foundation (Week 1-2)

#### 1.1 Model Metadata System
- [ ] Define `.transform.json` schema
- [ ] Create `ModelMetadata` dataclass
- [ ] Implement metadata loader/validator
- [ ] Write unit tests for metadata parsing

#### 1.2 ExternalModelElement Base Class
- [ ] Implement `ExternalModelElement` class
- [ ] Fixed dimension enforcement
- [ ] Transform calculation methods
- [ ] Error handling for missing models

#### 1.3 Transform System
- [ ] Create `Matrix4x4` class or use numpy
- [ ] Implement TRS (Translation, Rotation, Scale) composition
- [ ] Quaternion support for rotations
- [ ] Transform chain validation

### Phase 2: Model Library Setup (Week 2-3)

#### 2.1 Directory Structure
```
models/
├── chair/                      # Registry key: 'chair'
│   ├── model.glb               # External 3D model file
│   └── model.transform.json    # Normalization metadata
├── desk/                       # Registry key: 'desk'
│   ├── model.glb
│   └── model.transform.json
├── dining_table/               # Registry key: 'dining_table'
│   ├── model.glb
│   └── model.transform.json
├── external_model_test/        # Registry key: 'external_model_test' (TEST ELEMENT)
│   ├── model.glb               # Simple test cube
│   └── model.transform.json    # Test metadata
├── fridge/                     # Registry key: 'fridge'
│   ├── model.glb
│   └── model.transform.json
├── sofa/                       # Registry key: 'sofa'
│   ├── model.glb
│   └── model.transform.json
└── README.md
```

**Naming Convention:**
- Each element type from `create_elements_registry()` gets its own folder
- Folder name = registry key (e.g., 'chair', 'desk', 'dining_table')
- Fixed filenames: `model.glb` and `model.transform.json` (no per-model naming)
- No model overwriting: Each element type has exactly one external model
- If element type has no external model, use procedural generation (current behavior)

#### 2.2 Test Element Type Creation
- [ ] Create `ExternalModelTest` class in `floor_planner/elements/basic.py` or new file
- [ ] Implement simple 2D drawing (rectangular shape, e.g., 1m × 0.5m × 0.3m)
- [ ] Register in `create_elements_registry()` as `'external_model_test': ExternalModelTest`
- [ ] Create directory: `models/external_model_test/`
- [ ] Generate `models/external_model_test/model.transform.json`:
  ```json
  {
    "model_file": "model.glb",
    "format_version": "1.0",
    "element_type": "external_model_test",
    "registry_key": "external_model_test",
    "units": "meters",
    "up_axis": "Y",
    "normalization": {
      "description": "Identity matrix - model already in standard space",
      "matrix": [
        [1.0, 0.0, 0.0, 0.0],
        [0.0, 1.0, 0.0, 0.0],
        [0.0, 0.0, 1.0, 0.0],
        [0.0, 0.0, 0.0, 1.0]
      ]
    },
    "anchor_point": "bottom_center",
    "bounding_box": {
      "min": [-0.5, 0.0, -0.25],
      "max": [0.5, 0.3, 0.25]
    },
    "dimensions": {
      "width": 1.0,
      "length": 0.5,
      "height": 0.3
    },
    "visual_properties": {
      "color": [0.8, 0.6, 0.4],
      "material_type": "wood"
    },
    "metadata": {
      "author": "Floor Planner Test",
      "license": "MIT",
      "created": "2026-05-27",
      "tags": ["test", "external", "model"]
    }
  }
  ```
- [ ] Create simple `model.glb` placeholder (cube or box, 1m × 0.5m × 0.3m)
- [ ] Test 2D rendering: element draws as rectangle in floor plan
- [ ] Test external model detection: `has_external_model()` returns True
- [ ] Validate fallback: Delete model.glb temporarily, verify procedural generation works

#### 2.3 Sample Models
- [ ] Create/acquire 3-5 test models (chair, desk, fridge)
- [ ] Normalize models to standard coordinate system
- [ ] Create `model.transform.json` for each element type
- [ ] Place in `models/{registry_key}/` folders
- [ ] Validate folder names match registry keys exactly

#### 2.4 Model Validator Tool
- [ ] Script to validate model + metadata
- [ ] Check bounding box correctness
- [ ] Verify transform normalization
- [ ] Generate validation report

### Phase 3: glTF Export System (Week 3-5)

#### 3.1 glTF Writer
- [ ] Implement `GLTFExporter` class
- [ ] Scene graph builder
- [ ] Node hierarchy management
- [ ] Buffer/accessor creation

#### 3.2 Model Integration
- [ ] External model reference system
- [ ] Transform hierarchy (normalization + placement)
- [ ] Material preservation/override
- [ ] Texture path resolution

#### 3.3 Procedural Geometry Export
- [ ] Convert existing OBJ export to glTF buffers
- [ ] Maintain backward compatibility with OBJ export
- [ ] Unified material system (procedural + external)

#### 3.4 Animation Embedding
- [ ] Read animations from external glTF models
- [ ] Preserve animation data in output
- [ ] Map animations to element IDs
- [ ] Animation metadata export

### Phase 4: Element Registration (Week 5-6)

#### 4.1 Element Detection Logic
- [ ] Add `has_external_model()` method to Element base class
- [ ] Check for `models/{registry_key}/model.glb` existence
- [ ] If exists, load external model; otherwise use procedural generation
- [ ] Maintain backward compatibility with all existing elements

#### 4.2 Model Path Resolution
- [ ] Use registry key to determine model folder path
- [ ] Path formula: `models/{registry_key}/model.glb`
- [ ] Automatic fallback to procedural if model missing
- [ ] Warning system: "External model not found for '{registry_key}', using procedural generation"

#### 4.3 YAML Configuration
- [ ] **No changes to YAML format required**
- [ ] Existing `type` field determines element from registry
- [ ] Element automatically detects if external model exists
- [ ] All elements keep 2D drawing capability (backward compatible)
- [ ] Elements with external models render in 3D, still draw in 2D

### Phase 5: 3D Viewer Integration (Week 6-8)

#### 5.1 Web Viewer (Three.js)
- [ ] Basic glTF loader
- [ ] Scene reconstruction
- [ ] Camera controls (orbit, pan, zoom)
- [ ] Lighting setup

#### 5.2 Model Display
- [ ] External model loading
- [ ] Procedural geometry display
- [ ] Material rendering
- [ ] Texture mapping

#### 5.3 User Interface
- [ ] Element selection/highlighting
- [ ] Info panel (element properties)
- [ ] Layer visibility toggles
- [ ] Screenshot/export functionality

#### 5.4 Animation Playback
- [ ] Animation controls
- [ ] Play/pause/reset
- [ ] Timeline scrubbing
- [ ] Multiple animation support

### Phase 6: Testing & Documentation (Week 8-9)

#### 6.1 Test Suite
- [ ] Unit tests for ExternalModelElement
- [ ] Integration tests for glTF export
- [ ] Visual regression tests
- [ ] Performance benchmarks

#### 6.2 Example Floor Plans
- [ ] Test layout with `external_model_test` element (verify 2D + 3D)
- [ ] Office layout with external furniture
- [ ] Kitchen with appliances
- [ ] Living room with mixed models
- [ ] Complete house with furniture

#### 6.3 Documentation
- [ ] Model metadata format specification
- [ ] Creating custom models guide
- [ ] glTF export format documentation
- [ ] Web viewer usage guide
- [ ] Troubleshooting guide

## Configuration Examples

### YAML: Mixed Procedural + External Models

```yaml
project:
  dpi: 300
  file: examples/mixed_models/office.pdf
  visualisation_dir: examples/mixed_models/office_3d
  export_format: gltf  # NEW: glTF export instead of OBJ

model_library:
  path: models/
  fallback_to_procedural: true  # Generate box if model missing

default_layout:
  width: 10
  length: 8
  scale: 50

floor_plans:
  - title: Office Floor Plan
    elements:
      # Procedural elements (generated geometry)
      - type: wall
        id: wall_001
        anchor_point: [0, 0]
        length: 10
        thickness: 0.2
        height: 2.8
        
      # Test element with external model
      - type: external_model_test
        id: test_001
        anchor_point: [1, 1]
        orientation_angle: 0
        v_anchor: 0.0
        # Tests both 2D drawing (rect) and 3D external model loading
        
      # External model elements (if models/chair/model.glb exists)
      # Otherwise falls back to procedural generation
      - type: chair
        id: chair_001
        anchor_point: [2, 3]
        orientation_angle: 45
        v_anchor: 0.0
        # Dimensions are fixed, read from models/chair/model.transform.json
        # Still draws in 2D, exports to 3D if external model exists
        
      - type: chair
        id: chair_002
        anchor_point: [4, 3]
        orientation_angle: -45
        # Same type='chair', references same models/chair/model.glb
        # No per-instance model override (one model per element type)
        
      - type: desk
        id: desk_001
        anchor_point: [3, 2.5]
        orientation_angle: 0
        # Fixed size: 1.6m x 0.8m x 0.75m
        
      - type: desk_lamp
        id: lamp_001
        anchor_point: [3.2, 2.8]  # On the desk
        v_anchor: 0.75  # Desktop height
        orientation_angle: 90
```

### Model Metadata: Office Chair

**File: `models/chair/model.transform.json`**
```json
{
  "model_file": "model.glb",
  "format_version": "1.0",
  "element_type": "chair",
  "registry_key": "chair",
  
  "units": "meters",
  "up_axis": "Y",
  
  "normalization": {
    "description": "Model exported from Blender, Y-up, origin at base center",
    "matrix": [
      [1.0, 0.0, 0.0, 0.0],
      [0.0, 1.0, 0.0, 0.0],
      [0.0, 0.0, 1.0, 0.0],
      [0.0, 0.0, 0.0, 1.0]
    ]
  },
  
  "anchor_point": "bottom_center",
  "bounding_box": {
    "min": [-0.3, 0.0, -0.3],
    "max": [0.3, 0.9, 0.3]
  },
  
  "dimensions": {
    "width": 0.6,
    "length": 0.6,
    "height": 0.9
  },
  
  "interactions": {
    "height_adjust": {
      "type": "animation",
      "animation_name": "seat_height",
      "trigger": "none",
      "range": [0.4, 0.55],
      "default": 0.45
    },
    "rotate": {
      "type": "continuous_rotation",
      "axis": "Y",
      "speed": 180
    }
  },
  
  "visual_properties": {
    "thumbnail": "office_chair_thumb.png",
    "preview_camera": {
      "position": [1.5, 1.2, 1.5],
      "target": [0, 0.45, 0]
    }
  },
  
  "metadata": {
    "author": "Floor Planner Team",
    "license": "MIT",
    "created": "2026-05-27",
    "tags": ["furniture", "chair", "office", "ergonomic"]
  }
}
```

## Technical Challenges & Solutions

### Challenge 1: Large Model Files

**Problem**: glTF files can be large, slow to load.

**Solutions:**
1. **Lazy loading**: Load models on-demand, not all at once
2. **Texture optimization**: Resize textures to appropriate resolution
3. **Geometry simplification**: Reduce polygon count for background elements
4. **Caching**: Cache parsed models in memory
5. **Streaming**: Load large scenes incrementally

**Note**: Binary glTF (.glb) not used in this feature. JSON format is sufficient and easier to debug/inspect.

### Challenge 2: Model Coordinate System Consistency

**Problem**: Different 3D software uses different conventions.
- Blender: Z-up
- 3ds Max: Z-up
- Maya: Y-up
- SketchUp: Z-up, different scale

**Solution**: Mandatory normalization step
1. All models must be normalized to: Y-up, 1 unit = 1 meter, origin at floor center
2. Validation tool checks compliance
3. Clear documentation for model creators
4. Automated conversion scripts where possible

### Challenge 3: Animation Compatibility

**Problem**: Animations may reference nodes that don't exist after transformation.

**Solution**: Node name preservation
1. Keep original node hierarchy
2. Apply transforms at scene root level
3. Preserve node IDs in glTF export
4. Animation channels reference preserved node names

### Challenge 4: Material Consistency

**Problem**: External models may have materials incompatible with procedural ones.

**Solution**: Material normalization
1. Convert all materials to PBR (Physically Based Rendering)
2. Standardize texture channels (baseColor, metallic, roughness, normal)
3. Apply consistent lighting model
4. Allow material overrides in metadata



## Testing Strategy

### Unit Tests

```python
# test_external_model_element.py

def test_external_model_test_element():
    """Test the test element for external model integration."""
    from floor_planner.elements.external_model_test import ExternalModelTest
    
    # Test 2D drawing
    test_elem = ExternalModelTest(anchor_point=[0, 0])
    assert test_elem.width == 1.0
    assert test_elem.length == 0.5
    assert test_elem.height == 0.3
    
    # Test external model detection
    assert test_elem.has_external_model() == True
    
    # Test metadata loading
    metadata = test_elem.model_metadata
    assert metadata['registry_key'] == 'external_model_test'
    assert metadata['bounding_box']['max'][0] == 0.5

def test_fixed_dimensions_enforced():
    """Ensure user cannot override model dimensions."""
    with pytest.raises(ValueError):
        Chair(
            anchor_point=[0, 0],
            width=2.0  # Should fail
        )

def test_metadata_loading():
    """Verify metadata loads correctly."""
    chair = Chair(anchor_point=[0, 0])
    assert chair.width == 0.6
    assert chair.height == 0.9

def test_transform_calculation():
    """Verify transform matrices are correct."""
    chair = Chair(
        anchor_point=[2, 3],
        orientation_angle=45,
        v_anchor=0.0
    )
    transform = chair.get_placement_transform()
    assert transform.translation == [2, 0, 3]
    assert abs(transform.rotation[1] - 45) < 0.01

def test_missing_model_handling():
    """Ensure graceful failure when model missing."""
    with pytest.raises(FileNotFoundError):
        Chair(model_path='nonexistent.glb')
```

### Integration Tests

```python
# test_gltf_export.py

def test_external_model_test_export():
    """Test export of external_model_test element."""
    from floor_planner.elements.external_model_test import ExternalModelTest
    
    test_elem = ExternalModelTest(anchor_point=[1, 1], orientation_angle=0)
    exporter = GLTFExporter()
    scene = exporter.export([test_elem])
    
    assert len(scene.nodes) == 1
    assert scene.nodes[0].mesh.is_external
    # Verify transform applied correctly
    node = scene.nodes[0]
    assert node.translation[0] == 1.0
    assert node.translation[2] == 1.0

def test_mixed_scene_export():
    """Export scene with procedural + external models."""
    floor_plan = FloorPlan([
        Wall(anchor_point=[0, 0], length=5, thickness=0.2, height=2.8),
        Chair(anchor_point=[2, 2], orientation_angle=0)
    ])
    
    exporter = GLTFExporter()
    scene = exporter.export(floor_plan)
    
    assert len(scene.nodes) == 2
    assert scene.nodes[0].mesh.is_procedural
    assert scene.nodes[1].mesh.is_external

def test_animation_preservation():
    """Verify animations are preserved in export."""
    chair = Chair(anchor_point=[0, 0])
    exporter = GLTFExporter()
    scene = exporter.export([chair])
    
    assert len(scene.animations) > 0
    assert any(anim.name == 'height_adjust' for anim in scene.animations)
```

### Visual Tests

1. **Baseline images**: Render reference scenes with known-good output
2. **Regression detection**: Compare new renders to baseline
3. **Manual review**: Web viewer for visual inspection
4. **Automated checks**: Verify model placement, orientation, scale

### Performance Tests

```python
def test_large_scene_performance():
    """Ensure large scenes export in reasonable time."""
    elements = []
    
    # 100 procedural elements
    for i in range(100):
        elements.append(Wall(...))
    
    # 50 external model elements
    for i in range(50):
        elements.append(Chair(...))
    
    start = time.time()
    exporter = GLTFExporter()
    scene = exporter.export(elements)
    duration = time.time() - start
    
    assert duration < 5.0  # 5 seconds max
    assert len(scene.nodes) == 150
```

## Success Criteria

- [ ] Test element (`external_model_test`) successfully created and registered
- [ ] Test element draws correctly in 2D (simple rectangle)
- [ ] Test element loads external model.glb when present
- [ ] Test element falls back to 2D drawing when model.glb missing
- [ ] External models load and display correctly
- [ ] Fixed dimensions enforced (cannot scale models)
- [ ] Transform chain works (normalization + placement)
- [ ] glTF export produces valid files (validated by glTF-Validator)
- [ ] Web viewer displays mixed procedural + external scenes
- [ ] Animations preserved but not yet interactive
- [ ] At least 5 furniture models in library (including test element)
- [ ] Performance: < 5 seconds to export 100-element scene
- [ ] All existing procedural elements still work
- [ ] Documentation complete

## Future Enhancements

### Phase 2 Features
- [ ] **Interactive animations** (click to open door, drag drawer, rotate chair)
  - UI triggers in web viewer
  - Animation state management
  - Keyframe interpolation
  - Reversible animations (open/close)
  - Multiple simultaneous animations

## Open Questions

1. **Custom models**: Should users upload their own models?
   - **Phase 1**: No, use curated library
   - **Phase 2**: Yes, with validation

2. **Hybrid scaling**: Can some dimensions scale while others are fixed?
   - **Example**: Bookshelf width variable, but depth/height fixed
   - **Proposed**: Define in metadata which dimensions are scalable

## Dependencies

### New Dependencies
- **pygltflib**: Python glTF 2.0 library for reading/writing
- **numpy**: Matrix math (if not already included)
- **Pillow**: Texture processing
- **validators**: URL/path validation

### Optional Dependencies
- **trimesh**: Mesh processing and analysis

### Modified Files
- `floor_planner/elements/element.py` - Add ExternalModelElement base
- `floor_planner/elements/registry.py` - Register external model elements
- `floor_planner/project.py` - Add glTF export option
- `floor_planner/obj_exporter.py` - Maintain for backward compatibility

### New Files
- `floor_planner/gltf_exporter.py` - glTF export system
- `floor_planner/model_metadata.py` - Metadata handling
- `floor_planner/transform.py` - Transform matrix math
- `floor_planner/elements/external_models.py` - ExternalModelElement base class
- `floor_planner/elements/external_model_test.py` - Test element for external model integration
- `models/external_model_test/model.glb` - Test cube model
- `models/external_model_test/model.transform.json` - Test metadata
- `models/README.md` - Model library documentation
- `tools/validate_model.py` - Model validation script
- `viewer/index.html` - Web-based 3D viewer
- `viewer/viewer.js` - Three.js viewer implementation

## References

- **glTF 2.0 Specification**: https://registry.khronos.org/glTF/specs/2.0/glTF-2.0.html
- **Three.js GLTFLoader**: https://threejs.org/docs/#examples/en/loaders/GLTFLoader
- **pygltflib**: https://gitlab.com/dodgyville/pygltflib
- **Blender glTF Exporter**: https://docs.blender.org/manual/en/latest/addons/import_export/scene_gltf2.html
- **glTF Sample Models**: https://github.com/KhronosGroup/glTF-Sample-Models
- **PBR Materials**: https://learnopengl.com/PBR/Theory

---

**Document History**:
- 2026-05-27: Initial planning document created
- Author: AI Assistant (GitHub Copilot)
- Status: Awaiting review and approval for implementation
