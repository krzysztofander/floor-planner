# Texture/Material Naming Convention

## Overview

This document defines the **registry-based naming convention** for textures and materials in the floor_planner system.

## Core Principle

**Registry is the single source of truth**. Element types from `floor_planner/elements/registry.py` determine ALL naming.

- Registry keys (WITH underscores) → folder names and file names
- Example: Registry key `'generic_storage'` → folder `generic_storage/`, file `generic_storage.jpg`
- No need for DEFAULT_TEXTURES dict - names come directly from registry

## Naming Rules

### Registry as Source of Truth

The `create_elements_registry()` function in [`registry.py`](cci:1://file:///home/krzysztof/work/excercises/preprojektant/floor_planner/floor_planner/elements/registry.py:0:0-0:0) defines all valid element types:

```python
registry = {
    'ceiling_lamp': CeilingLamp,
    'generic_storage': GenericStorage,
    'double_bed': DoubleBed,
    'garden_path': GardenPath,
    # ... etc
}
```

These keys (WITH underscores) become the naming standard.

### Directory Names
- Directory name = Registry key exactly
- Examples:
  - Registry: `'generic_storage'` → Directory: `generic_storage/`
  - Registry: `'double_bed'` → Directory: `double_bed/`
  - Registry: `'ceiling_lamp'` → Directory: `ceiling_lamp/`

### Base Texture Names
- Base texture = `<element_type>.jpg` or `<element_type>.png`
- Examples:
  - Element: `generic_storage` → File: `generic_storage.jpg`
  - Element: `double_bed` → File: `double_bed.jpg`
  - Element: `ceiling_lamp` → File: `ceiling_lamp.jpg`

### Supplemental Texture Names
- For multi-texture elements (doors, desks): `<element_type>_<descriptor>.jpg`
- Defined in `SUPPLEMENTAL_TEXTURES` registry
- Examples:
  - Door frame: `door_frame.jpg`
  - Desk sides: `desk_sides.jpg`
  - Table sides: `table_sides.jpg`

### Material File Names
- Material file = `<element_type>.mtl`
- Same base name as texture
- Examples:
  - Element: `generic_storage` → File: `generic_storage.mtl`
  - Element: `double_bed` → File: `double_bed.mtl`

### MTL File Content
- `newmtl` declaration: Use element type (WITH underscores)
- `map_Kd` reference: Use texture filename (WITH underscores)

Example MTL file for `generic_storage`:
```mtl
# Auto-generated material for generic_storage
newmtl generic_storage
Ka 0.500000 0.300000 0.200000
Kd 0.580000 0.380000 0.230000
Ks 1.200000 1.200000 1.200000
Ns 250.0
map_Kd generic_storage.jpg
```

## Directory Structure

```
textures/
├── fallback/                    # System defaults
│   ├── generic_storage/
│   │   ├── generic_storage.jpg  # WITH underscores
│   │   └── generic_storage.mtl
│   ├── double_bed/
│   │   ├── double_bed.jpg
│   │   └── double_bed.mtl
│   ├── ceiling_lamp/
│   │   ├── ceiling_lamp.jpg
│   │   └── ceiling_lamp.mtl
│   ├── door/
│   │   ├── door.jpg
│   │   ├── door_frame.jpg       # Supplemental texture
│   │   └── door.mtl
│   └── ...
└── defaults/                    # User overrides
    ├── generic_storage/
    │   └── generic_storage.mtl
    └── ...
```

## Supplemental Textures

Defined in [`supplemental_textures.py`](cci:1://file:///home/krzysztof/work/excercises/preprojektant/floor_planner/floor_planner/supplemental_textures.py:0:0-0:0):

```python
SUPPLEMENTAL_TEXTURES = {
    'door': ['frame'],      # door.jpg + door_frame.jpg
    'desk': ['sides'],      # desk.jpg + desk_sides.jpg
    'table': ['sides'],     # table.jpg + table_sides.jpg
}
```

## No More DEFAULT_TEXTURES Dict

The old `DEFAULT_TEXTURES` dictionary has been **removed**. Texture names now come directly from:
1. Registry keys for base textures
2. `SUPPLEMENTAL_TEXTURES` for additional textures

This simplifies the system - one source of truth instead of two.

## Validation

Use the validation script to verify naming compliance:
```bash
python scripts/validate_texture_material_structure.py
```

This checks:
- All registered elements have directories (exact match with registry keys)
- All texture files match element names (WITH underscores)
- All textures have corresponding `.mtl` files
- All `.mtl` files reference correct texture filenames

## Migration

If you have textures that don't follow this convention, use:
```bash
python scripts/rename_to_registry_keys.py
```

This will:
- Rename directories to match registry keys exactly
- Rename files to match registry keys
- Update MTL file content to reference new filenames

## Examples

| Registry Key | Directory | Texture | Material | MTL newmtl | MTL map_Kd |
|--------------|-----------|---------|----------|------------|------------|
| `generic_storage` | `generic_storage/` | `generic_storage.jpg` | `generic_storage.mtl` | `generic_storage` | `generic_storage.jpg` |
| `double_bed` | `double_bed/` | `double_bed.jpg` | `double_bed.mtl` | `double_bed` | `double_bed.jpg` |
| `ceiling_lamp` | `ceiling_lamp/` | `ceiling_lamp.jpg` | `ceiling_lamp.mtl` | `ceiling_lamp` | `ceiling_lamp.jpg` |
| `wall_lamp` | `wall_lamp/` | `wall_lamp.jpg` | `wall_lamp.mtl` | `wall_lamp` | `wall_lamp.jpg` |
| `single_sink` | `single_sink/` | `single_sink.jpg` | `single_sink.mtl` | `single_sink` | `single_sink.jpg` |
| `garden_path` | `garden_path/` | `garden_path.jpg` | `garden_path.mtl` | `garden_path` | `garden_path.jpg` |
| `door` | `door/` | `door.jpg` + `door_frame.jpg` | `door.mtl` | `door` | `door.jpg` |

## Adding New Elements

When adding a new element with texture support:

1. **Add to registry** in [`registry.py`](cci:1://file:///home/krzysztof/work/excercises/preprojektant/floor_planner/floor_planner/elements/registry.py:0:0-0:0):
   ```python
   registry = {
       'new_element': NewElement,
   }
   ```

2. **Create directory** (matches registry key exactly):
   ```bash
   mkdir -p textures/fallback/new_element
   ```

3. **Add texture file** (matches registry key):
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

5. **Add supplemental textures** (if needed) in [`supplemental_textures.py`](cci:1://file:///home/krzysztof/work/excercises/preprojektant/floor_planner/floor_planner/supplemental_textures.py:0:0-0:0):
   ```python
   SUPPLEMENTAL_TEXTURES = {
       'new_element': ['detail'],  # Creates new_element_detail.jpg
   }
   ```

6. **Validate**:
   ```bash
   python scripts/validate_texture_material_structure.py
   ```

## Key Advantages

1. **Single Source of Truth**: Registry defines everything
2. **Simpler Code**: No DEFAULT_TEXTURES dict to maintain
3. **Predictable**: Element name = folder name = file name
4. **Maintainable**: Add element to registry, create folder, done
5. **Consistent**: Underscores used uniformly across Python code and filesystem
