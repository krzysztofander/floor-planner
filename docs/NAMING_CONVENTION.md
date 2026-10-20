# Texture/Material Naming Convention

Short naming rules for textures and materials. For how textures are resolved and turned into glTF materials, see [texture-material-system.md](./texture-material-system.md).

## Core Principle

**The registry is the single source of truth.** Keys of `create_elements_registry()` in [`floor_planner/elements/registry.py`](../floor_planner/elements/registry.py) determine all names, exactly as written (snake_case, WITH underscores):

```python
registry = {
    'ceiling_lamp': CeilingLamp,
    'generic_storage': GenericStorage,
    'double_bed': DoubleBed,
    'garden_path': GardenPath,
    # ... etc
}
```

At export time the key is obtained from an instance with `get_element_type_from_instance(element)` (never from the class name: `DoubleBed` → `'double_bed'`, not `'doublebed'`). For external-model elements it returns the class's `_registry_key` instead (see below).

## Rules

For a registry key `<key>`:

| Item | Name | Example (`double_bed`) |
|------|------|------------------------|
| Directory | `textures/fallback/<key>/` and/or `textures/defaults/<key>/` | `double_bed/` |
| Base texture | `<key>.png` or `<key>.jpg` (PNG wins if both exist) | `double_bed.jpg` |
| Material file | `<key>.mtl`, in the same directory as the texture | `double_bed.mtl` |
| `newmtl` | `<key>` | `newmtl double_bed` |
| `map_Kd` | texture filename | `map_Kd double_bed.jpg` |

Only one texture per element type is used (face key `'all'`). Extra files such as `door/door_frame.jpg` or `desk/desk_sides.jpg` are not read by the code.

Example (`textures/fallback/generic_storage/generic_storage.mtl`):

```mtl
# Auto-generated material for generic_storage
newmtl generic_storage
Ka 0.500000 0.300000 0.200000
Kd 0.580000 0.380000 0.230000
Ks 1.200000 1.200000 1.200000
Ns 250.0
map_Kd generic_storage.jpg
```

Transparent (glass) elements use a `.png` texture and a `d` (opacity) line, e.g. `textures/fallback/solid_glass_door/solid_glass_door.mtl`:

```mtl
newmtl solid_glass_door
Ka 0.85 0.90 1.00
Kd 0.85 0.90 1.00
Ks 0.90 0.90 0.95
Ns 150.0
d 0.20
map_Kd solid_glass_door.png
```

## Directory Structure

```
textures/
├── fallback/                    # System defaults (always searched second)
│   ├── generic_storage/
│   │   ├── generic_storage.jpg
│   │   └── generic_storage.mtl
│   ├── gable_end_glass_left/
│   │   ├── gable_end_glass_left.png   # PNG for transparency
│   │   └── gable_end_glass_left.mtl
│   ├── future/                  # Spare textures, not referenced by the registry
│   └── ...
└── defaults/                    # User overrides (searched first, same layout)
    ├── wall/
    │   ├── wall.jpg
    │   └── wall.mtl
    └── ...
```

## External Models

Elements with external 3D models (e.g. `model_wooden_chair`, `glass_panel`, `glass_door`, `glass_slope`, `alu_frame`) do not use `textures/`. Their folder is `models/<_registry_key>/` (searched in `models/`, then `models/local/`, `models/models_3rd_party/`, `models/stubs/`), with `model.obj` + `model.mtl` (or `model.glb`) and `model.transform.json`. `_registry_key` may drop the `model_` YAML prefix (e.g. `model_wooden_chair` → `models/models_3rd_party/wooden_chair/`). Material names inside `model.mtl` are free; `map_Kd` paths are relative to the model folder. Validate with `python scripts/validate_models.py`.

## Adding a New Procedural Element

1. Add `'new_element': NewElement` to the registry.
2. Create `textures/fallback/new_element/` with `new_element.jpg` (or `.png`) and `new_element.mtl` following the rules above.
3. Optionally put an override in `textures/defaults/new_element/` (texture **and** `.mtl` — see [texture-material-system.md](./texture-material-system.md#lookup-order)).

There is no automated texture-structure validator; check names by hand.
