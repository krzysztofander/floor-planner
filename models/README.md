# External Model Library

This directory contains external 3D models for floor plan elements that use pre-made assets instead of procedural geometry generation.

## Supported Model Formats

### OBJ Format (Wavefront .obj + .mtl)
- **Best for**: Static furniture, simple objects
- **Pros**: Simple, universal, text-based, easy to create/edit
- **Cons**: No animations, separate material files
- **Files**: `model.obj` + `model.mtl` + `model.transform.json`

### glTF Format (Binary .glb)
- **Best for**: Animated elements (doors, drawers), complex models
- **Pros**: Industry standard, animations, PBR materials, single file
- **Cons**: More complex, binary format
- **Files**: `model.glb` + `model.transform.json`

**Detection Priority**: System checks for `model.glb` first, then `model.obj`, then falls back to procedural generation.

## Directory Structure

Each element type has its own folder, named after the registry key from `create_elements_registry()`:

```
models/
├── external_model_test/      # Test element (validation) - OBJ format
│   ├── model.obj              # 3D model file (OBJ format)
│   ├── model.mtl              # OBJ material file
│   └── model.transform.json   # Metadata and normalization transform
├── chair/                     # Future: Chair element - OBJ or glTF
│   ├── model.obj (or model.glb)
│   ├── model.mtl (if OBJ)
│   └── model.transform.json
├── desk/                      # Future: Desk element
│   ├── model.glb (or model.obj + model.mtl)
│   └── model.transform.json
└── ...                        # Additional element types
```

## File Naming Convention

- **Folder name**: Must match registry key exactly (WITH underscores, e.g., `external_model_test`, `dining_table`)
- **Model files** (choose one format per element):
  - **OBJ format**: `model.obj` + `model.mtl`
  - **glTF format**: `model.glb`
- **Metadata file**: Always named `model.transform.json` (required for all formats)

## Metadata Format

Each `model.transform.json` file contains:"model.glb" or "model.obj")
- **model_format**: Format type ("gltf" or "obj

- **model_file**: Filename of the 3D model (always "model.glb")
- **format_version**: Metadata format version ("1.0")
- **element_type**: Element type name
- **registry_key**: Registry key (determines folder name)
- **units**: Model units ("meters", "centimeters", "inches")
- **up_axis**: Vertical axis ("Y" or "Z")
- **normalization**: 4x4 transformation matrix (column-major) to convert model to standard space
- **anchor_point**: Semantic anchor point name ("bottom_center", "center", etc.)
- **bounding_box**: Axis-aligned bounding box (min/max corners)
- **dimensions**: Fixed width, length, height in meters
- **visual_properties**: Color, material type, thumbnail
- **metadata**: Author, license, source, creation date, tags

See `external_model_test/model.transform.json` for a complete example.

## Standard Coordinate System

All models must be normalized to this standard coordinate system:

- **Y-axis**: Vertical (up direction)
- **X-axis**: Horizontal (width dimension)
- **Z-axis**: Horizontal (length/depth dimension)
- **Units**: 1 unit = 1 meter
- **Origin**: Floor center of the element
- **Anchor point**: Bottom center (on the floor, centered in X-Z plane)

The `normalization.matrix` field in metadata defines the transformation from the model's native coordinate system to this standard space.

## Adding New Models

To add a new external model:

1. **Choose format**: OBJ (simple, static) or glTF (animations, complex)
3. **Add model file(s)**:
   - **OBJ**: Place `model.obj` and `model.mtl` in the folder
   - **glTF**`model_format` field ("gltf" or "obj")
   - Correct : Place `model.glb` in the folder
4. **Add model file**: Place `model.glb` in the folder
3. **Create metadata**: Generate `model.transform.json` with:
   - Correct normalization matrix (convert model to standard space)
   - Accurate bounding box (measure min/max extents)
   - Fixed dimensions (width, length, height)
4. **Test**: Use test element YAML to verify loading and placement
5. **Validate**: Run `python scripts/validate_model_metadata.py` (when available)

## Model Requirements
### OBJ Format
- **Format**: Wavefront OBJ (.obj) with material file (.mtl)
- **Coordinate system**: Must be normalized via metadata matrix
- **Scale**: Fixed dimensions, no user scaling
- **Materials**: Basic Phong materials (Ka, Kd, Ks, Ns)
- **Polygons**: Reasonable poly count (< 10k triangles for furniture)
- **Limitations**: No animations (static only)

### glTF Format
- **Format**: glTF 2.0 binary (.glb) onlyfiles exist:
- **glTF**: `models/{registry_key}/model.glb` (checked first)
- **OBJ**: `models/{registry_key}/model.obj` + `model.mtl` (checked second)
- **Metadata**: `models/{registry_key}/model.transform.json` (always required)
- **Textures**: Embedded in .glb or referenced relatively
- **Polygons**: Reasonable poly count (< 10k triangles for furniture)
- **Materials**: PBR materials recommended (Physically Based Rendering)
- **Animations**: Supported (for future interactive elements
- **Materials**: PBR materials recommended (Physically Based Rendering)

## Using External Models

External models are automatically detected when both files exist:
- `models/{registry_key}/model.glb`
- `models/{registry_key}/model.transform.json`

When files exist:
- Element renders in 2D (procedural drawing)
- ElFormat**: OBJ (simple test cube)
- **2D Drawing**: Simple brown rectangle
- **3D Model**: Simple OBJ cube with wood material
When files missing:
- Element renders in 2D only (procedural generation)
- Warning logged: "External model not found for '{registry_key}'"

## Test Element

The `external_model_test` element serves as validation and example:
- **Purpose**: Test 2D+3D hybrid rendering pipeline
- **Dimensions**: 1.0m × 0.5m × 0.3m (W×L×H)
- **2D Drawing**: Simple brown rectangle
- **3D Model**: Placeholder cube (when model.glb present)
- **Usage**: Test external model loading before adding production models

YAML example:
```yaml
- type: external_model_test
  id: test_001
  anchor_point: [2, 3]
  orientation_angle: 45
  v_anchor: 0.0
```

## Future Enhancements

- Model validator tool (`scripts/validate_model_metadata.py`)
- Model converter tool (OBJ → glTF with metadata generation)
- Model library browser (web UI for previewing models)
- Animation support (doors opening, drawers sliding)
- LOD (Level of Detail) support for performance
- Model thumbnails for UI
