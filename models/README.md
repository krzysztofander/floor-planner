# External Model Library

This directory contains external 3D models for floor plan elements that use pre-made assets instead of procedural geometry. The 2D drawing of these elements is still procedural; the model is used only in the 3D (glTF) export.

## Where Models Are Looked Up

For each element, the first of these directories that contains a `<registry_key>/` folder is used:

1. `models/` - models kept in this repository (mostly windows and doors)
2. `models/local/` - private models, not versioned
3. `models/models_3rd_party/` - third-party models kept in a separate repository (git-ignored)
4. `models/stubs/` - 1x1x1 m cube placeholders, used when the real model is not available

A different base directory can be passed with the element's `models_dir` parameter; the same subdirectories are searched relative to it.

## Directory Layout

Each model has its own folder, named after the element's `_registry_key` (set in its class in `floor_planner/elements/external/`). Note that this is not always the YAML `type`, e.g. YAML type `model_window_90x120` uses folder `window_90x120/`.

```
models/
├── window_90x120/
│   ├── model.obj              # 3D model
│   ├── model.mtl              # OBJ materials (map_Kd window_90x120__frame.jpg, ...)
│   └── model.transform.json   # metadata (always required)
├── procedural/                # materials of procedural elements (not models)
│   └── wall/wall.mtl
├── models_3rd_party/
│   └── leafy_tree/            # may keep its textures next to model.mtl
└── stubs/
    └── leafy_tree/ ...
```

Textures referenced by `model.mtl` (`map_Kd`) are searched in the model folder first, then in the common [`textures/`](../textures/README.md) folder. Models in this repository keep their textures in `textures/`, so models and procedural elements can share them; third-party models can keep theirs next to `model.mtl`.

`procedural/` is not a model folder: it holds `<element_type>/<element_type>.mtl` for procedurally generated elements (walls, furniture boxes, roofs, ...). See [docs/texture-material-system.md](../docs/texture-material-system.md).

## Model Formats

The model file is detected in this order: `model.glb`, `model.gltf`, `model.obj` (+ `model.mtl`), `model.dae`, `model.3ds`. OBJ is the format used by the current models; glTF is preferred for models with animations.

## Missing Models

- Elements with `_requires_external_model = True` (e.g. Blender furniture, trees, master bed) stop the script with a `FileNotFoundError` that lists all searched locations.
- Other elements fall back to default dimensions and procedural geometry.

## Metadata (`model.transform.json`)

Example (see any folder in `models/` for a complete file):

```json
{
  "model_file": "model.obj",
  "model_format": "obj",
  "format_version": "1.0",
  "element_type": "window_90x120",
  "registry_key": "window_90x120",
  "units": "meters",
  "up_axis": "Y",
  "normalization": {
    "description": "Model at 1:1 metre scale. Origin at bottom-left corner of frame.",
    "scale": [1.0, 1.0, 1.0],
    "rotation": [0, 0, 0],
    "translation": [0, 0, 0]
  },
  "anchor_point": "bottom_left",
  "anchor_offset": [0, 0, 0],
  "bounding_box": {"min": [0, 0, 0], "max": [0.9, 1.2, 0.12]},
  "dimensions": {"width": 0.9, "length": 0.9, "height": 1.2}
}
```

Fields:

- **model_file**, **model_format**, **format_version** - model file name, format (`obj` / `gltf`) and metadata version (`1.0`). `model_file`, `format_version` and `element_type` are required.
- **element_type**, **registry_key** - element name; `registry_key` must match the folder name.
- **normalization** - transform from the model's native space to the standard space: `scale`, `rotation` (Euler angles in degrees, applied X → Y → Z) and `translation`, applied in the order scale → rotate → translate. An explicit 4x4 `matrix` is still accepted for backward compatibility.
- **anchor_point**, **anchor_offset** - semantic anchor name and an extra offset.
- **bounding_box** - extents in the normalized space.
- **dimensions** - fixed `width`, `length`, `height` in meters (some elements, e.g. trees, also use `diameter`). Users cannot override dimensions in YAML.
- Optional: **visual_properties** (`color`, `material_type`, `texture`, `thumbnail`), **interactions** (animation metadata), **metadata** (`author`, `license`, `source`, `created`, `tags`).

## Standard Coordinate System

- **Y-axis**: vertical (up)
- **X-axis**: width
- **Z-axis**: length/depth
- **Units**: 1 unit = 1 meter
- **Origin**: on the floor; most models use the bottom-left-front corner

## Adding a New Model

1. Put the model files in `models/<registry_key>/` (or `local/` / `models_3rd_party/` for models that must not be versioned here).
2. Write `model.transform.json` with the normalization, bounding box and dimensions.
3. If the model is not committed to this repository, add a cube placeholder in `models/stubs/<registry_key>/` so the project still builds without it.
4. Add an element class with `_registry_key` in `floor_planner/elements/external/` and register it in `floor_planner/elements/registry.py`.
5. Validate with `python scripts/validate_models.py` and check the result in a 3D example.

Blender models can be converted with `scripts/blend_to_obj.py` and `scripts/blend_to_gltf.py`. See `scripts/README.md`.
