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

- By convention the default texture of an element type is `<element_type>.jpg` (or `.png`), e.g. `wall.jpg`.
- Model textures use `<model>__<part>.jpg`, e.g. `balcony_door__frame.jpg`.
- When two textures would have the same name, the one that is not used by default gets a suffix naming its origin, e.g. `wall_fallback.jpg`.
- Files that no `.mtl` references (e.g. `bench.jpg`, `stairs.jpg`, `door_frame.jpg`) are kept for future elements.
- `default.jpg` is used by the (legacy) OBJ exporter when an element type has no material.

## Requirements

- **Format**: PNG for transparency (alpha channel: glass, cutouts), JPEG for opaque textures
- **Size**: 1024x1024 recommended (512x512 minimum)
- **Seamless**: textures that tile (walls, floors, roofs) should be seamless, see `texture_scale` in [docs/texture-tiling-guide.md](../docs/texture-tiling-guide.md)

See [docs/texture-material-system.md](../docs/texture-material-system.md) for the full lookup and material rules.
