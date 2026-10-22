# Textures

Common folder for all texture images used by the 3D export. It is flat: every file is directly in `textures/`, and file names are unique.

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

- Each image exists once in `textures/`: identical files were merged, keeping the shortest name, so an element type's texture is often named after another type (e.g. `generic_storage`, `storage40` and `storage60` use `wardrobe.jpg`). The `.mtl` decides which image an element uses; the file name says nothing about it.
- Names that differ only by origin keep a suffix, e.g. `door_fallback.jpg`.
- Subfolders work when the reference includes them (`map_Kd wood/oak.jpg` → `textures/wood/oak.jpg`). File names must still be unique across all folders, because the glTF export copies textures into one flat output folder.
- Files that no `.mtl` references (e.g. `armchair.jpg`, `driveway.jpg`, `floor_lamp.jpg`) are kept for future elements.

## Requirements

- **Format**: PNG for transparency (alpha channel: glass, cutouts), JPEG for opaque textures
- **Size**: 1024x1024 recommended (512x512 minimum)
- **Seamless**: textures that tile (walls, floors, roofs) should be seamless, see `scale_meters` / `scale_relative` in [docs/texture-tiling-guide.md](../docs/texture-tiling-guide.md)

See [docs/texture-material-system.md](../docs/texture-material-system.md) for the full lookup and material rules.
