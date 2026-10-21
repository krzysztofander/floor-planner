# Texture and Material System

## Overview

How the 3D export finds `.mtl` material files and the textures they reference, and turns them into materials. File and folder naming rules are in [NAMING_CONVENTION.md](./NAMING_CONVENTION.md); this document does not repeat them.

The 3D export is **glTF 2.0** (`GLTFExporter` in [`floor_planner/gltf_exporter.py`](../floor_planner/gltf_exporter.py)).

Procedural elements and external models use the same rule: a `.mtl` file describes the material and references its texture with `map_Kd`. Only the place of the `.mtl` differs:

| Element kind | Material (`.mtl`) |
|--------------|-------------------|
| Procedural (has `generate_vertices_and_indices()`: walls, furniture boxes, roofs, gable ends, greenhouse, `solid_glass_door`, ...) | `models/procedural/<key>/<key>.mtl` |
| External model (`ExternalModelElement` with a model file: `model_*`, `glass_door`, `glass_panel`, `glass_slope`, `alu_frame`) | the model's own `model.mtl` (or embedded materials) in `models/.../<_registry_key>/` |

`<key>` is the registry key from `get_element_type_from_instance(element)`.

All texture images live in one common folder, **`textures/`**, so any `.mtl` (procedural or model) can reference any texture by file name.

## Texture Lookup

A texture referenced by `map_Kd <file>` in a `.mtl` is searched in this order (`find_texture()` in [`texture_manager.py`](../floor_planner/texture_manager.py)):

1. the folder that contains the `.mtl` file;
2. the common texture folder `textures/`.

The first rule keeps models that ship their own textures working unchanged (e.g. `models/models_3rd_party/<model>/`). The second one is used by everything in this repository: `models/procedural/*/` and `models/<model>/` contain only `.mtl` (and model) files, and their textures are in `textures/`.

The reference is used as written, so `map_Kd wall.jpg` finds `textures/wall.jpg`, and a relative path such as `map_Kd ../other_model/x.png` is resolved from the `.mtl` folder first and then from `textures/`.

A `map_Kd` that cannot be found stops the export with an error. A procedural `.mtl` without `map_Kd` gives an untextured (colour only) material.

## Key Components

### TextureManager ([`texture_manager.py`](../floor_planner/texture_manager.py))

- `find_texture(texture_ref, mtl_dir)` → absolute path of a texture referenced from a `.mtl` in `mtl_dir` (lookup above), or `None`
- `get_procedural_mtl(element_type)` → `models/procedural/<key>/<key>.mtl`, or `None` if it does not exist

### GLTFExporter material code ([`gltf_exporter.py`](../floor_planner/gltf_exporter.py))

- `_get_default_material(element)` → material for procedural elements (one per element type, cached)
- `_parse_mtl_file(path)` → reads `newmtl`, `Ka`, `Kd`, `Ks`, `Ns`, `map_Kd`, `d`/`Tr`
- `_select_best_mtl_material()` → picks one material if the file has several (prefers one with `map_Kd`, then non-black `Kd`)
- `_create_gltf_material()` / `_copy_texture()` → materials and textures for external models
- `_add_specular_extension()` → `Ks` → `KHR_materials_specular`

## MTL → glTF Material (procedural elements)

`_get_default_material()` reads `models/procedural/<key>/<key>.mtl` and builds a material named `<key>_material`:

| MTL | glTF |
|-----|------|
| `map_Kd` | `baseColorTexture` (file found with the lookup above) |
| `Kd` | `baseColorFactor` RGB (multiplies the texture; black `Kd` with a texture → white) |
| `d` (or `Tr`) < 0.99 | `alphaMode: BLEND`, value used as `baseColorFactor` alpha |
| `Ns` | `roughnessFactor = 1 - min(Ns/100, 1)` (no `Ns` → 0.8) |
| `Ks` | `KHR_materials_specular`: factor = mean(Ks) clamped to 3, colour = Ks / mean |
| `Ka` | ignored |
| — | `metallicFactor = 0` |

Without a `.mtl` the material has no texture and uses a fallback colour (`0.95` grey for `wall`, `[0.7, 0.4, 0.2]` for `door`, `[0.8, 0.9, 1.0]` for `window`, otherwise `0.8` grey).

Procedural elements that set `alpha_mode = "BLEND"` (`Window`, `Shower`, `FishTank`) always get `alphaMode: BLEND`, but their alpha stays 1.0 unless the `.mtl` has `d` — the visible transparency then comes from the PNG alpha channel. For glass use a PNG texture plus `d` (see `solid_glass_door`, `gable_end_glass_*`, `greenhouse` in `models/procedural/`).

The texture is copied to `<output>/textures/<filename>` and referenced as `textures/<filename>`. Tiling is controlled by the element's `texture_scale`, see [texture-tiling-guide.md](./texture-tiling-guide.md).

## External Models

For OBJ models, `_load_obj_as_mesh()` reads `model.mtl` next to `model.obj` and creates one primitive per `usemtl` group (unknown names → best material from the file). Each `map_Kd` is found with the lookup above and copied to `<output>/textures/`. `d` < 0.99 → `BLEND`. GLB models keep their embedded materials; 3DS and DAE models are converted by their own loaders (their textures are also searched next to the model file, then in `textures/`). Folder layout: [NAMING_CONVENTION.md](./NAMING_CONVENTION.md#external-models).

## Custom Textures

Put the image in `textures/` and point the `.mtl` at it:

```bash
cp my_oak.jpg textures/generic_storage_oak.jpg
sed -i 's/^map_Kd .*/map_Kd generic_storage_oak.jpg/' models/procedural/generic_storage/generic_storage.mtl
```

Texture names in `textures/` must be unique. Where two sources had a file with the same name, the copy that is not used by default got a suffix naming its origin (e.g. `wall_fallback.jpg`, `deck_fallback.jpg`).

## Common Issues

- **Texture not applied** — the `map_Kd` name does not match a file next to the `.mtl` or in `textures/`, or the `.mtl` folder/file name differs from the registry key.
- **Export stops with "Texture ... not found"** — a `map_Kd` reference cannot be resolved; fix the file name in the `.mtl` or add the texture to `textures/`.
- **Glass is opaque** — no `d` line in the `.mtl` and no alpha in the PNG.
- **`ValueError: Element class ... not found in registry`** — the element class (not its parent) must be a value in the registry, or be an `ExternalModelElement` with `_registry_key`.

## See Also

- [NAMING_CONVENTION.md](./NAMING_CONVENTION.md) - naming rules
- [texture-tiling-guide.md](./texture-tiling-guide.md) - `texture_scale` and UV tiling
- [element-parameters-reference.md](./element-parameters-reference.md) - element parameters
