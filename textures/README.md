# Textures

Common folder for all texture images used by the 3D export, organized in subfolders by kind (e.g. `wood/`, `tiles/`, `transparent/`, `plain_named/`). File names are unique across all subfolders.

Textures are never picked by name alone. A material (`.mtl`) references them with `map_Kd`:

- procedural elements: `models/procedural/<element_type>/<element_type>.mtl`
- external models: `models/<model>/model.mtl`

A `map_Kd` reference is searched in the folder of the `.mtl` file first, then here. Models that ship their own textures (e.g. `models/models_3rd_party/<model>/`) therefore keep working, and any `.mtl` can reuse any texture from this folder.

## Adding or changing a texture

```bash
# add the image
cp my_oak.jpg textures/generic_storage_oak.jpg
# point the material at it
sed -i 's/^map_Kd .*/map_Kd generic_storage_oak.jpg/' models/procedural/generic_storage/generic_storage.mtl
```

## Naming

- Textures are organized in subfolders by kind (`wood/`, `tiles/`, `paving/`, `transparent/`, `plain_named/` for plain colours named after what they depict, ...), and `.mtl` files refer to them with the folder, e.g. `map_Kd wood/pear_wood.jpg`. Each image exists once; several element types may share it (e.g. `generic_storage`, `storage40` and `storage60` use `wood/pear_wood.jpg`). The `.mtl` decides which image an element uses.
- The reference includes the subfolder (`map_Kd wood/pear_wood.jpg` → `textures/wood/pear_wood.jpg`). File names must be unique across all folders, because the glTF export copies textures into one flat output folder.
- Each image exists once: identical files were merged.
- Files that no `.mtl` references (e.g. `plain_named/gray-armchair.jpg`, `plain_named/gray-dark-gray-driveway.jpg`, `plain_named/yellow-warm-white-floor-lamp.jpg`) are kept for future elements.

## Requirements

- **Format**: PNG for transparency (alpha channel: glass, cutouts), JPEG for opaque textures
- **Size**: 1024x1024 recommended (512x512 minimum)
- **Seamless**: textures that tile (walls, floors, roofs) should be seamless, see `scale_meters` / `scale_relative` in [docs/texture-tiling-guide.md](../docs/texture-tiling-guide.md)

See [docs/texture-material-system.md](../docs/texture-material-system.md) for the full lookup and material rules.
