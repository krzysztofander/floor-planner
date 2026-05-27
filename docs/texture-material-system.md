# Texture and Material System

## Overview

The Floor Planner's 3D export system uses a registry-based approach for texture and material management. This document explains the architecture and conventions used throughout the system.

## Core Architecture

### Single Source of Truth: The Registry

Element types are defined in [`floor_planner/elements/registry.py`](../floor_planner/elements/registry.py):

```python
def create_elements_registry() -> dict[str, type(Element)]:
    registry = {
        'ceiling_lamp': CeilingLamp,
        'generic_storage': GenericStorage,
        'double_bed': DoubleBed,
        'garden_path': GardenPath,
        # ... etc
    }
    return registry
```

**Registry keys (WITH underscores) determine all naming:**
- Folder names
- Texture filenames
- Material filenames

This eliminates the need for separate texture mapping dictionaries and ensures consistency.

## Directory Structure

```
textures/
├── fallback/                    # System default textures
│   ├── generic_storage/         # Registry key → folder name
│   │   ├── generic_storage.jpg  # Base texture
│   │   └── generic_storage.mtl  # Material properties
│   ├── double_bed/
│   │   ├── double_bed.jpg
│   │   └── double_bed.mtl
│   ├── ceiling_lamp/
│   │   ├── ceiling_lamp.jpg
│   │   └── ceiling_lamp.mtl
│   └── door/
│       ├── door.jpg             # Base texture
│       ├── door_frame.jpg       # Supplemental texture
│       └── door.mtl             # Material references both
└── defaults/                    # User custom textures (overrides)
    └── (same structure)
```

## Naming Convention

### Rule: Registry Key = Folder Name = Base File Name

| Registry Key | Folder | Base Texture | Material |
|--------------|--------|--------------|----------|
| `'generic_storage'` | `generic_storage/` | `generic_storage.jpg` | `generic_storage.mtl` |
| `'double_bed'` | `double_bed/` | `double_bed.jpg` | `double_bed.mtl` |
| `'ceiling_lamp'` | `ceiling_lamp/` | `ceiling_lamp.jpg` | `ceiling_lamp.mtl` |

### Supplemental Textures

Multi-texture elements (doors, desks) use: `<element_type>_<descriptor>.jpg`

Defined in [`floor_planner/supplemental_textures.py`](../floor_planner/supplemental_textures.py):

```python
SUPPLEMENTAL_TEXTURES = {
    'door': ['frame'],      # door.jpg + door_frame.jpg
    'desk': ['sides'],      # desk.jpg + desk_sides.jpg
    'table': ['sides'],     # table.jpg + table_sides.jpg
}
```

## Material Files (.mtl)

Material files define Phong shading properties:

```mtl
# Material for generic_storage
newmtl generic_storage
Ka 0.500000 0.300000 0.200000    # Ambient color (RGB 0-1)
Kd 0.580000 0.380000 0.230000    # Diffuse color (RGB 0-1)
Ks 1.200000 1.200000 1.200000    # Specular color (RGB 0-1)
Ns 250.0                         # Shininess (0-1000)
map_Kd generic_storage.jpg       # Texture reference
```

**Properties:**
- **Ka (Ambient)**: Base color in shadow
- **Kd (Diffuse)**: Color under direct light
- **Ks (Specular)**: Highlight color
- **Ns (Shininess)**: Specular power (higher = sharper highlights)
- **map_Kd**: Texture filename (must match base texture name)

## Key Components

### 1. TextureManager

Located in [`floor_planner/texture_manager.py`](../floor_planner/texture_manager.py).

**Responsibilities:**
- Resolve texture paths from element types
- Handle default/fallback texture lookup
- Copy textures to output directory for 3D export
- Support PNG (with alpha) and JPG formats

**Key Methods:**
- `get_default_textures(element_type)` - Returns texture filenames derived from registry key
- `normalize_texture_spec()` - Converts user texture specs to absolute paths
- `resolve_element_textures()` - Resolves textures for an element
- `copy_texture_to_output()` - Copies textures to visualization directory

**No DEFAULT_TEXTURES Dictionary:**
The old `DEFAULT_TEXTURES` dict has been removed. Texture names now come directly from:
1. Registry keys for base textures
2. `SUPPLEMENTAL_TEXTURES` for multi-texture elements

### 2. MaterialManager

Located in [`floor_planner/material_manager.py`](../floor_planner/material_manager.py).

**Responsibilities:**
- Parse `.mtl` files to extract Ka, Kd, Ks, Ns properties
- Cache loaded materials for performance
- Provide fallback to default material if `.mtl` not found

**Key Methods:**
- `parse_mtl_file(mtl_path)` - Parses MTL file format
- `get_material_for_texture()` - Gets material for a texture file
- `get_default_material()` - Returns neutral gray fallback
- `format_mtl_color()` - Formats RGB tuple for MTL output

### 3. OBJExporter

Located in [`floor_planner/obj_exporter.py`](../floor_planner/obj_exporter.py).

**Responsibilities:**
- Generate OBJ/MTL files for 3D export
- Use `get_element_type_from_instance()` to get registry keys from element instances
- Coordinate TextureManager and MaterialManager
- Write vertex, normal, texture coordinate, and face data

**Key Fix:**
Uses `get_element_type_from_instance(element)` instead of `type(element).__name__.lower()` to get correct registry keys:
- `DoubleBed` class → `'double_bed'` registry key ✓
- ~~`DoubleBed` class → `'doublebed'` (wrong)~~ ✗

### 4. Registry Helper

Located in [`floor_planner/elements/registry.py`](../floor_planner/elements/registry.py).

**New Function:**
```python
def get_element_type_from_instance(element: Element) -> str:
    """
    Get registry key (element type) from an element instance.
    
    This provides the reverse mapping: Class → registry key.
    Essential for texture/material resolution where registry keys
    define folder and file names.
    
    Example:
        bed = DoubleBed(...)
        get_element_type_from_instance(bed)  # Returns: 'double_bed'
    """
```

This function ensures correct mapping from element instances to registry keys, which then determine texture/material paths.

## Texture Resolution Flow

1. **Element instantiation** in YAML config (e.g., `type: double_bed`)
2. **Registry lookup** maps `'double_bed'` → `DoubleBed` class
3. **3D export** calls `get_element_type_from_instance(element)` → `'double_bed'`
4. **TextureManager** looks for:
   - `textures/defaults/double_bed/double_bed.jpg` (user override)
   - `textures/fallback/double_bed/double_bed.jpg` (system default)
5. **MaterialManager** looks for:
   - `textures/defaults/double_bed/double_bed.mtl`
   - `textures/fallback/double_bed/double_bed.mtl`
6. **Texture copying** to `<visualisation_dir>/textures/double_bed.jpg`
7. **MTL file generation** references `textures/double_bed.jpg`

## Custom Textures

Users can override system textures by placing files in `textures/defaults/`:

```bash
# Override generic_storage texture
mkdir -p textures/defaults/generic_storage/
cp my_custom_texture.jpg textures/defaults/generic_storage/generic_storage.jpg
cp my_custom_material.mtl textures/defaults/generic_storage/generic_storage.mtl
```

The system searches defaults first, then falls back to fallback textures.

## Validation

Use the validation script to verify naming compliance:

```bash
python scripts/validate_texture_material_structure.py
```

**Checks:**
- All registered elements have directories (exact match with registry keys)
- All texture files match element names (WITH underscores)
- All textures have corresponding `.mtl` files
- All `.mtl` files reference correct texture filenames (WITH underscores)

## Adding Textures for New Elements

When adding a new element type, **you MUST create textures**:

1. **Add to registry** in `floor_planner/elements/registry.py`:
   ```python
   'new_element': NewElement,
   ```

2. **Create texture directory** (matches registry key exactly):
   ```bash
   mkdir -p textures/fallback/new_element/
   ```

3. **Add texture file**:
   ```bash
   cp source.jpg textures/fallback/new_element/new_element.jpg
   ```

4. **Create MTL file**:
   ```bash
   cat > textures/fallback/new_element/new_element.mtl << 'EOF'
   newmtl new_element
   Ka 0.700000 0.700000 0.700000
   Kd 0.800000 0.800000 0.800000
   Ks 0.200000 0.200000 0.200000
   Ns 30.0
   map_Kd new_element.jpg
   EOF
   ```

5. **For multi-texture elements**, add to `supplemental_textures.py`:
   ```python
   SUPPLEMENTAL_TEXTURES = {
       'new_element': ['frame', 'detail'],
   }
   ```

6. **Validate**:
   ```bash
   python scripts/validate_texture_material_structure.py
   ```

## Common Issues

### Issue: Textures not copied to visualisation_dir

**Cause:** Using class name instead of registry key for texture lookup.

**Solution:** Use `get_element_type_from_instance(element)` to get registry key.

### Issue: MTL file references wrong texture name

**Cause:** MTL file created with old naming convention (no underscores).

**Solution:** Update MTL content to use registry key naming:
```mtl
newmtl double_bed         # Not 'doublebed'
map_Kd double_bed.jpg     # Not 'doublebed.jpg'
```

### Issue: Validation fails with "Missing subdirectory"

**Cause:** Folder name doesn't match registry key exactly.

**Solution:** Rename folder to match registry key (WITH underscores):
```bash
mv textures/fallback/doublebed textures/fallback/double_bed
```

## Benefits of Registry-Based System

1. **Single Source of Truth**: Registry defines everything
2. **No Manual Maintenance**: No DEFAULT_TEXTURES dict to keep in sync
3. **Predictable**: Element name = folder name = file name
4. **Extensible**: Add to registry → create folder → done
5. **Consistent**: Underscores used uniformly across Python code and filesystem
6. **Type-Safe**: Registry provides compile-time validation of element types

## See Also

- [NAMING_CONVENTION.md](./NAMING_CONVENTION.md) - Detailed naming rules and examples
- [supplemental_textures.py](../floor_planner/supplemental_textures.py) - Multi-texture definitions
- [.github/copilot-instructions.md](../.github/copilot-instructions.md) - AI agent instructions
- [element-parameters-reference.md](./element-parameters-reference.md) - Element parameters
