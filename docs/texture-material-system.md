# Texture and Material System

## Overview

How the 3D export finds textures and `.mtl` material files and turns them into materials. File and folder naming rules are in [NAMING_CONVENTION.md](./NAMING_CONVENTION.md); this document does not repeat them.

The active export is **glTF 2.0** (`GLTFExporter` in [`floor_planner/gltf_exporter.py`](../floor_planner/gltf_exporter.py)). The OBJ/MTL export ([`obj_exporter.py`](../floor_planner/obj_exporter.py)) still exists but is commented out in [`__main__.py`](../floor_planner/__main__.py).

Two kinds of elements are textured differently:

| Element kind | Texture/material source |
|--------------|-------------------------|
| Procedural (has `generate_vertices_and_indices()`: walls, furniture boxes, roofs, gable ends, greenhouse, `solid_glass_door`, ...) | `textures/defaults/<key>/` or `textures/fallback/<key>/` |
| External model (`ExternalModelElement` with a model file: `model_*`, `glass_door`, `glass_panel`, `glass_slope`, `alu_frame`) | the model's own `model.mtl` / embedded materials in `models/.../<_registry_key>/` |

`<key>` is the registry key from `get_element_type_from_instance(element)`.

## Key Components

### TextureManager ([`texture_manager.py`](../floor_planner/texture_manager.py))

Used by both exporters to find the texture file for an element type.

- `get_default_textures(element_type)` → `{'all': '<key>.jpg'}` (one texture per element)
- `normalize_texture_spec(element_type)` → `{'all': <absolute path>}` using the lookup order below
- `resolve_element_textures(element_type, config_dir)` → `{'all': Path}`; repeats the lookup if the path does not exist
- `copy_texture_to_output()`, `get_relative_texture_path()` → used by the OBJ exporter only

### GLTFExporter material code ([`gltf_exporter.py`](../floor_planner/gltf_exporter.py))

- `_get_default_material(element)` → material for procedural elements (one per element type, cached)
- `_parse_mtl_file(path)` → reads `newmtl`, `Ka`, `Kd`, `Ks`, `Ns`, `map_Kd`, `d`/`Tr`
- `_select_best_mtl_material()` → picks one material if the file has several (prefers one with `map_Kd`, then non-black `Kd`)
- `_create_gltf_material()` → materials for external OBJ models
- `_add_specular_extension()` → `Ks` → `KHR_materials_specular`

### MaterialManager ([`material_manager.py`](../floor_planner/material_manager.py))

Used **only by the OBJ exporter**. Parses `Ka`, `Kd`, `Ks`, `Ns` (no `d`), caches by `.mtl` path, falls back to `get_default_material()` (Ka 0.7, Kd 0.8, Ks 0.2, Ns 30). The glTF export does not use it.

## Lookup Order

For a procedural element with key `<key>` (`TextureManager.normalize_texture_spec`):

1. `textures/defaults/<key>/<key>.png`
2. `textures/defaults/<key>/<key>.jpg`
3. `textures/fallback/<key>/<key>.png`
4. `textures/fallback/<key>/<key>.jpg`
5. `textures/fallback/default/default.jpg` (this file does not exist in the repo; there is a loose `textures/fallback/default.jpg`, which is not used)

The `.mtl` is then read **only from the folder where the texture was found** (`<texture dir>/<key>.mtl`). Consequences:

- An override in `textures/defaults/<key>/` must contain the texture; a `defaults/` folder with only `<key>.mtl` is ignored by glTF export (the texture and `.mtl` come from `fallback/`). Many current `defaults/` folders are like this (copies of the fallback `.mtl`).
- If you override the texture, also put a `.mtl` next to it.

The `map_Kd` line of these `.mtl` files is not used by the glTF export (the texture is the file found above); keep it correct for consistency and for the OBJ exporter.

Roofs (`gable_roof`, `hipped_roof`, `single_slope_roof`, octants), gable ends (`gable_end_wall_*`, `gable_end_glass_*`), `greenhouse` and `solid_glass_door` are procedural and follow this order like any other element.

## MTL → glTF Material (procedural elements)

`_get_default_material()` builds a material named `<key>_material`:

| MTL | glTF |
|-----|------|
| `Kd` | `baseColorFactor` RGB (multiplies the texture; black `Kd` with a texture → white) |
| `d` (or `Tr`) < 0.99 | `alphaMode: BLEND`, value used as `baseColorFactor` alpha |
| `Ns` | `roughnessFactor = 1 - min(Ns/100, 1)` (no `Ns` → 0.8) |
| `Ks` | `KHR_materials_specular`: factor = mean(Ks) clamped to 3, colour = Ks / mean |
| `Ka` | ignored |
| — | `metallicFactor = 0` |

The code has fallback colours for a missing `.mtl` (`0.95` grey for `wall`, `[0.7, 0.4, 0.2]` for `door`, `[0.8, 0.9, 1.0]` for `window`, otherwise `0.8` grey), but currently a missing `.mtl` makes the export fail (see Common Issues). Always ship a `.mtl` with each texture.

Procedural elements that set `alpha_mode = "BLEND"` (`Window`, `Shower`, `FishTank`) always get `alphaMode: BLEND`, but their alpha stays 1.0 unless the `.mtl` has `d` — the visible transparency then comes from the PNG alpha channel. For glass use a PNG texture plus `d` (see `solid_glass_door`, `gable_end_glass_*`, `greenhouse` in `textures/fallback/`).

The texture is copied to `<output>/textures/<filename>` and referenced as `textures/<filename>`. Tiling is controlled by the element's `texture_scale`, see [texture-tiling-guide.md](./texture-tiling-guide.md).

## External Models

For OBJ models, `_load_obj_as_mesh()` reads `model.mtl` next to `model.obj` and creates one primitive per `usemtl` group (unknown names → best material from the file). `map_Kd` is resolved relative to the model folder (e.g. `../balcony_door/balcony_door__glass.png` in `models/glass_panel/model.mtl`) and copied to `<output>/textures/`. `d` < 0.99 → `BLEND`. GLB models keep their embedded materials; 3DS and DAE models are converted by their own loaders. `textures/` is not used. Folder layout: [NAMING_CONVENTION.md](./NAMING_CONVENTION.md#external-models).

## Custom Textures

```bash
mkdir -p textures/defaults/generic_storage/
cp my_texture.jpg  textures/defaults/generic_storage/generic_storage.jpg
cp textures/fallback/generic_storage/generic_storage.mtl textures/defaults/generic_storage/
```

Use `.png` for transparency; it takes priority over `.jpg` in the same folder.

## Common Issues

- **Override has no effect** — the texture is missing from the `defaults/<key>/` folder (an `.mtl` alone is not enough), or the folder/file name differs from the registry key.
- **`TypeError` (`'NoneType'`) raised from `_get_default_material`** — no `<key>.mtl` next to the resolved texture, or no texture folder at all for a procedural element type.
- **Glass is opaque** — no `d` line in the `.mtl` and no alpha in the PNG.
- **`ValueError: Element class ... not found in registry`** — the element class (not its parent) must be a value in the registry, or be an `ExternalModelElement` with `_registry_key`.

## See Also

- [NAMING_CONVENTION.md](./NAMING_CONVENTION.md) - naming rules
- [texture-tiling-guide.md](./texture-tiling-guide.md) - `texture_scale` and UV tiling
- [element-parameters-reference.md](./element-parameters-reference.md) - element parameters
