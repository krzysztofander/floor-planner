#!/usr/bin/env python3
"""
Export a Blender .blend file to model.obj + model.mtl for use as an external model.

Usage:
    python scripts/blend_to_obj.py <input.blend> <output_dir> [options]

Examples:
    # Export to a new model directory (creates models/my_chair/model.obj + model.mtl)
    python scripts/blend_to_obj.py ~/models/chair.blend models/my_chair

    # Export with custom Blender executable
    python scripts/blend_to_obj.py chair.blend models/my_chair --blender /opt/blender/blender

    # Export only selected objects
    python scripts/blend_to_obj.py chair.blend models/my_chair --selected-only

The output directory will be created if it does not exist.
model.obj and model.mtl are placed in <output_dir>.
Textures referenced by the MTL are copied alongside them.
A template model.transform.json is also generated — edit it to set correct
dimensions, anchor_point, normalization, etc.
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path


# Blender Python script executed inside Blender's embedded interpreter.
BLENDER_EXPORT_SCRIPT = '''
import bpy
import sys
import os

args = sys.argv[sys.argv.index("--") + 1:]
output_path = args[0]
selected_only_flag = "--selected-only" in args

# Apply all modifiers so geometry is fully baked
for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        bpy.context.view_layer.objects.active = obj
        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass

bpy.ops.wm.obj_export(
    filepath=output_path,
    export_selected_objects=selected_only_flag,
    apply_modifiers=True,
    export_triangulated_mesh=True,
    export_normals=True,
    export_uv=True,
    export_materials=True,
    path_mode="COPY",           # embed textures next to the OBJ
    export_pbr_extensions=False,
    export_object_groups=True,
    export_material_groups=False,
    global_scale=1.0,
    forward_axis="NEGATIVE_Z",
    up_axis="Y",
)
print("OBJ_EXPORT_OK:" + output_path)
'''

# Fallback script for older Blender (<3.3) that uses the legacy exporter
BLENDER_EXPORT_SCRIPT_LEGACY = '''
import bpy
import sys
import os

args = sys.argv[sys.argv.index("--") + 1:]
output_path = args[0]
selected_only_flag = "--selected-only" in args

for obj in bpy.context.scene.objects:
    if obj.type == "MESH":
        bpy.context.view_layer.objects.active = obj
        for mod in list(obj.modifiers):
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass

bpy.ops.export_scene.obj(
    filepath=output_path,
    use_selection=selected_only_flag,
    use_mesh_modifiers=True,
    use_triangles=True,
    use_normals=True,
    use_uvs=True,
    use_materials=True,
    path_mode="COPY",
    global_scale=1.0,
    axis_forward="-Z",
    axis_up="Y",
)
print("OBJ_EXPORT_OK:" + output_path)
'''


def find_blender() -> str:
    """Find the Blender executable on the system PATH."""
    candidates = ["blender", "blender-4.2", "blender-4.1", "blender-4.0", "blender-3.6"]
    for candidate in candidates:
        path = subprocess.run(
            ["which", candidate], capture_output=True, text=True
        ).stdout.strip()
        if path:
            return path
    raise FileNotFoundError(
        "Blender not found on PATH. Install Blender or pass --blender /path/to/blender"
    )


def get_blender_version(blender_exe: str) -> tuple[int, int]:
    """Return (major, minor) version tuple."""
    result = subprocess.run(
        [blender_exe, "--version"], capture_output=True, text=True, timeout=15
    )
    for line in result.stdout.splitlines():
        if line.startswith("Blender"):
            parts = line.split()
            if len(parts) >= 2:
                try:
                    major, minor = parts[1].split(".")[:2]
                    return int(major), int(minor)
                except (ValueError, IndexError):
                    pass
    return (0, 0)


def export_blend(
    blend_file: Path,
    output_obj: Path,
    blender_exe: str,
    selected_only: bool,
    blender_version: tuple[int, int],
) -> None:
    """Run Blender headlessly to export blend_file → output_obj + output_obj.mtl."""
    # Choose script: wm.obj_export added in 3.3
    script_src = (
        BLENDER_EXPORT_SCRIPT
        if blender_version >= (3, 3)
        else BLENDER_EXPORT_SCRIPT_LEGACY
    )

    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(script_src)
        script_path = f.name

    try:
        cmd = [
            blender_exe,
            "--background",
            str(blend_file),
            "--python", script_path,
            "--",
            str(output_obj),
        ]
        if selected_only:
            cmd.append("--selected-only")

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, timeout=120)

        if result.returncode != 0:
            print(f"ERROR: Blender exited with code {result.returncode}", file=sys.stderr)
            sys.exit(1)

        if not output_obj.exists():
            print(f"ERROR: Expected output file not created: {output_obj}", file=sys.stderr)
            sys.exit(1)

    finally:
        os.unlink(script_path)


def rename_mtl(output_obj: Path) -> None:
    """
    Blender names the MTL after the blend file; rename it to model.mtl
    and patch the reference inside model.obj.
    """
    obj_dir = output_obj.parent

    # Find any .mtl that isn't already model.mtl
    mtl_files = [p for p in obj_dir.glob("*.mtl") if p.name != "model.mtl"]
    if not mtl_files:
        return  # already named correctly or no MTL

    src_mtl = mtl_files[0]
    dst_mtl = obj_dir / "model.mtl"
    src_mtl.rename(dst_mtl)

    # Patch the mtllib line inside the OBJ
    obj_text = output_obj.read_text(encoding="utf-8", errors="replace")
    patched = obj_text.replace(f"mtllib {src_mtl.name}", f"mtllib model.mtl")
    if patched != obj_text:
        output_obj.write_text(patched, encoding="utf-8")


def make_transform_json(output_dir: Path, registry_key: str) -> None:
    """Generate a template model.transform.json in output_dir."""
    transform = {
        "model_file": "model.obj",
        "model_format": "obj",
        "format_version": "1.0",
        "element_type": registry_key,
        "registry_key": registry_key,
        "units": "meters",
        "up_axis": "Y",
        "normalization": {
            "description": "TODO: adjust scale/rotation/translation to fit standard space",
            "scale": [1.0, 1.0, 1.0],
            "rotation": [0, 0, 0],
            "translation": [0, 0, 0]
        },
        "anchor_point": "bottom_center",
        "anchor_offset": [0, 0, 0],
        "bounding_box": {
            "min": [-0.5, 0.0, -0.5],
            "max": [0.5, 1.0, 0.5]
        },
        "dimensions": {
            "width": 1.0,
            "length": 1.0,
            "height": 1.0
        },
        "visual_properties": {
            "color": [0.7, 0.7, 0.7],
            "material_type": "generic"
        },
        "metadata": {
            "author": "",
            "license": "",
            "source": "",
            "creation_date": str(date.today()),
            "tags": []
        }
    }

    out_path = output_dir / "model.transform.json"
    if out_path.exists():
        print(f"  Skipping model.transform.json (already exists)")
        return

    with open(out_path, "w") as f:
        json.dump(transform, f, indent=2)
    print(f"  Created template: {out_path}")
    print("  → Edit model.transform.json to set correct dimensions, normalization, and anchor_point.")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export a .blend file to model.obj + model.mtl for use as a floor_planner external model.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("blend_file", help="Input .blend file")
    parser.add_argument(
        "output_dir",
        help="Output directory (e.g. models/my_chair). Created if it does not exist.",
    )
    parser.add_argument(
        "--blender",
        default=None,
        metavar="PATH",
        help="Path to Blender executable (default: auto-detected from PATH)",
    )
    parser.add_argument(
        "--selected-only",
        action="store_true",
        help="Export only selected objects in the .blend file",
    )
    parser.add_argument(
        "--no-transform-json",
        action="store_true",
        help="Skip generating the template model.transform.json",
    )
    args = parser.parse_args()

    blend_file = Path(args.blend_file).resolve()
    if not blend_file.exists():
        print(f"ERROR: .blend file not found: {blend_file}", file=sys.stderr)
        sys.exit(1)
    if blend_file.suffix.lower() != ".blend":
        print(f"ERROR: Input file must have .blend extension: {blend_file}", file=sys.stderr)
        sys.exit(1)

    output_dir = Path(args.output_dir).resolve()
    output_dir.mkdir(parents=True, exist_ok=True)
    output_obj = output_dir / "model.obj"

    registry_key = output_dir.name

    blender_exe = args.blender or find_blender()
    version = get_blender_version(blender_exe)
    version_str = f"{version[0]}.{version[1]}" if version != (0, 0) else "unknown"
    exporter_api = "wm.obj_export" if version >= (3, 3) else "export_scene.obj (legacy)"
    print(f"Blender: {blender_exe}  (v{version_str}, using {exporter_api})")
    print(f"Input:   {blend_file}")
    print(f"Output:  {output_obj}")
    print()

    export_blend(blend_file, output_obj, blender_exe, args.selected_only, version)
    rename_mtl(output_obj)

    obj_size_kb = output_obj.stat().st_size / 1024
    mtl_path = output_dir / "model.mtl"
    mtl_size_kb = mtl_path.stat().st_size / 1024 if mtl_path.exists() else 0

    print(f"\nExported:")
    print(f"  {output_obj}  ({obj_size_kb:.1f} KB)")
    if mtl_path.exists():
        print(f"  {mtl_path}  ({mtl_size_kb:.1f} KB)")

    textures = [p for p in output_dir.iterdir() if p.suffix.lower() in ('.png', '.jpg', '.jpeg', '.tga', '.bmp')]
    if textures:
        print(f"  Textures: {', '.join(t.name for t in textures)}")

    if not args.no_transform_json:
        make_transform_json(output_dir, registry_key)

    print(f"\nDone. Add '{registry_key}' to your element registry and YAML configs.")
    print(f"Remember to adjust model.transform.json (dimensions, normalization, anchor_point).")


if __name__ == "__main__":
    main()
