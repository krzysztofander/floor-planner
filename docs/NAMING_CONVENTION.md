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
| Material directory | `models/procedural/<key>/` | `models/procedural/double_bed/` |
| Material file | `<key>.mtl` | `double_bed.mtl` |
| `newmtl` | `<key>` | `newmtl double_bed` |
| `map_Kd` | name of a file in `textures/` (any name; by convention `<key>.jpg` or `.png`) | `map_Kd double_bed.jpg` |
| Texture file | `textures/<file>`, unique within `textures/` | `textures/double_bed.jpg` |

Only one texture per element type is used: the `map_Kd` of the best material in the `.mtl` (face key `'all'`). Textures that no `.mtl` references (e.g. `textures/door_frame.jpg`, `textures/desk_sides.jpg`, spare textures such as `textures/bench.jpg`) are kept for future use and are not read by the code.

When two textures would have the same name, the one that is not the default gets a suffix naming its origin, e.g. `wall.jpg` (default) and `wall_fallback.jpg`.

Example (`models/procedural/generic_storage/generic_storage.mtl`):

```mtl
# Auto-generated material for generic_storage
newmtl generic_storage
Ka 0.500000 0.300000 0.200000
Kd 0.580000 0.380000 0.230000
Ks 1.200000 1.200000 1.200000
Ns 250.0
map_Kd generic_storage.jpg
```

Transparent (glass) elements use a `.png` texture and a `d` (opacity) line, e.g. `models/procedural/solid_glass_door/solid_glass_door.mtl`:

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
models/
├── procedural/                  # Materials of procedural element types
│   ├── generic_storage/
│   │   └── generic_storage.mtl  # map_Kd generic_storage.jpg
│   ├── gable_end_glass_left/
│   │   └── gable_end_glass_left.mtl   # map_Kd gable_end_glass_left.png
│   └── ...
└── balcony_door/                # External model: model files + model.mtl
    ├── model.obj
    └── model.mtl                # map_Kd balcony_door__frame.jpg
textures/                        # All texture images, flat
├── generic_storage.jpg
├── gable_end_glass_left.png     # PNG for transparency
├── balcony_door__frame.jpg
└── ...
```

A `map_Kd` reference is searched next to the `.mtl` file first, then in `textures/` (see [texture-material-system.md](./texture-material-system.md#texture-lookup)).

## External Models

Elements with external 3D models (e.g. `model_wooden_chair`, `glass_panel`, `glass_door`, `glass_slope`, `alu_frame`) have their own `model.mtl`. Their folder is `models/<_registry_key>/` (searched in `models/`, then `models/local/`, `models/models_3rd_party/`, `models/stubs/`), with `model.obj` + `model.mtl` (or `model.glb`) and `model.transform.json`. `_registry_key` may drop the `model_` YAML prefix (e.g. `model_wooden_chair` → `models/models_3rd_party/wooden_chair/`). Material names inside `model.mtl` are free; a `map_Kd` texture is searched in the model folder first, then in `textures/`. Models in this repository keep their textures in `textures/`; third-party models in `models/models_3rd_party/` keep them next to their `model.mtl`. Validate with `python scripts/validate_models.py`.

## Adding a New Procedural Element

1. Add `'new_element': NewElement` to the registry.
2. Add the texture to `textures/` (e.g. `textures/new_element.jpg`, or reuse an existing one).
3. Create `models/procedural/new_element/new_element.mtl` following the rules above, with `map_Kd` naming the texture.

There is no automated texture-structure validator; check names by hand.
