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
| `map_Kd` | name of a file in `textures/` (any name, may be shared with other types) | `map_Kd plain_named/white-cream-bed.jpg` |
| Texture file | `textures/<file>`, unique within `textures/` | `textures/double_bed.jpg` |

Only one texture per element type is used: the `map_Kd` of the best material in the `.mtl` (face key `'all'`). Textures that no `.mtl` references (e.g. `textures/armchair.jpg`, `textures/driveway.jpg`, `textures/floor_lamp.jpg`) are kept for future use and are not read by the code.

Textures are organized in subfolders by kind (`wood/`, `tiles/`, `paving/`, `transparent/`, `plain_named/` for plain colours named after what they depict, ...), and `.mtl` files refer to them with the folder, e.g. `map_Kd wood/pear_wood.jpg`. Each image exists once; several element types may share it (e.g. `generic_storage`, `storage40` and `storage60` use `wood/pear_wood.jpg`). The `.mtl` decides which image an element uses. File names must be unique across all folders (the glTF export copies textures into one flat folder).

Example (`models/procedural/generic_storage/generic_storage.mtl`):

```mtl
# Auto-generated material for generic_storage
newmtl generic_storage
Ka 0.500000 0.300000 0.200000
Kd 0.580000 0.380000 0.230000
Ks 1.200000 1.200000 1.200000
Ns 250.0
map_Kd wood/pear_wood.jpg
```

Transparent (glass) elements use a `.png` texture and a `d` (opacity) line, e.g. `models/procedural/solid_glass_door/solid_glass_door.mtl`:

```mtl
newmtl solid_glass_door
Ka 0.85 0.90 1.00
Kd 0.85 0.90 1.00
Ks 0.90 0.90 0.95
Ns 150.0
d 0.20
map_Kd transparent/shower-plain.png
```

## Directory Structure

```
models/
├── procedural/                  # Materials of procedural element types
│   ├── generic_storage/
│   │   └── generic_storage.mtl  # map_Kd wood/pear_wood.jpg
│   ├── gable_end_glass_left/
│   │   └── gable_end_glass_left.mtl   # map_Kd transparent/shower-plain.png
│   └── ...
└── balcony_door/                # External model: model files + model.mtl
    ├── model.obj
    └── model.mtl                # map_Kd wood/exotic_wood_1.jpg
textures/                        # All texture images, in subfolders (unique file names)
├── wood/pear_wood.jpg                 # used by generic_storage, storage40, storage60
├── transparent/shower-plain.png                   # PNG for transparency (shared glass texture)
├── wood/exotic_wood_1.jpg
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
