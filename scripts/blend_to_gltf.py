#!/usr/bin/env python3
"""
Export a Blender .blend file to glTF (model.glb) for use as an external model.

Usage:
    python scripts/blend_to_gltf.py <input.blend> <output_dir> [options]

Examples:
    # Export to a new model directory (creates models/my_chair/model.glb)
    python scripts/blend_to_gltf.py ~/models/chair.blend models/my_chair

    # Export with custom Blender executable
    python scripts/blend_to_gltf.py chair.blend models/my_chair --blender /opt/blender/blender

    # Export only selected objects
    python scripts/blend_to_gltf.py chair.blend models/my_chair --selected-only

The output directory will be created if it does not exist.
A model.glb file is placed in <output_dir>.
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
# This is passed to `blender --python-expr`.
BLENDER_EXPORT_SCRIPT = '''
import bpy
import sys
import os

output_path = sys.argv[sys.argv.index("--") + 1]
selected_only_flag = "--selected-only" in sys.argv

# Apply all modifiers so geometry is baked
for obj in bpy.data.objects:
    if obj.type == "MESH":
        bpy.context.view_layer.objects.active = obj
        for mod in obj.modifiers:
            try:
                bpy.ops.object.modifier_apply(modifier=mod.name)
            except Exception:
                pass  # Some modifiers may not be applicable in this context

bpy.ops.export_scene.gltf(
    filepath=output_path,
    export_format="GLB",
    use_selection=selected_only_flag,
    export_apply=True,            # Apply modifiers
    export_yup=True,              # Y-up (standard for glTF)
    export_texcoords=True,
    export_normals=True,
    export_materials="EXPORT",
    #export_colors=True,
    export_animations=False,
    export_skins=False,
    export_morph=False,
    export_lights=False,
    export_cameras=False,
)
print("GLTF_EXPORT_OK:" + output_path)
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


def get_blender_version(blender_exe: str) -> str:
    """Return Blender version string."""
    result = subprocess.run(
        [blender_exe, "--version"], capture_output=True, text=True, timeout=15
    )
    for line in result.stdout.splitlines():
        if line.startswith("Blender"):
            return line.strip()
    return "unknown"


def export_blend(blend_file: Path, output_glb: Path, blender_exe: str, selected_only: bool) -> None:
    """Run Blender headlessly to export blend_file → output_glb."""
    # Write the export script to a temp file so we can pass --selected-only as an arg
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(BLENDER_EXPORT_SCRIPT)
        script_path = f.name

    try:
        cmd = [
            blender_exe,
            "--background",
            str(blend_file),
            "--python", script_path,
            "--",                     # separator: everything after is available to the script
            str(output_glb),
        ]
        if selected_only:
            cmd.append("--selected-only")

        print(f"Running: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=False, text=True, timeout=120)

        if result.returncode != 0:
            print(f"ERROR: Blender exited with code {result.returncode}", file=sys.stderr)
            sys.exit(1)

        if not output_glb.exists():
            print(f"ERROR: Expected output file not created: {output_glb}", file=sys.stderr)
            sys.exit(1)

    finally:
        os.unlink(script_path)


def make_transform_json(output_dir: Path, registry_key: str) -> None:
    """Generate a template model.transform.json in output_dir."""
    transform = {
        "model_file": "model.glb",
        "model_format": "gltf",
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
        description="Export a .blend file to model.glb for use as a floor_planner external model.",
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
    output_glb = output_dir / "model.glb"

    # Registry key = folder name (user is expected to name the folder correctly)
    registry_key = output_dir.name

    # Resolve Blender
    blender_exe = args.blender or find_blender()
    print(f"Blender: {blender_exe} ({get_blender_version(blender_exe)})")
    print(f"Input:   {blend_file}")
    print(f"Output:  {output_glb}")
    print()

    export_blend(blend_file, output_glb, blender_exe, args.selected_only)

    size_kb = output_glb.stat().st_size / 1024
    print(f"\nExported: {output_glb}  ({size_kb:.1f} KB)")

    if not args.no_transform_json:
        make_transform_json(output_dir, registry_key)

    print(f"\nDone. Add '{registry_key}' to your element registry and YAML configs.")
    print(f"Remember to adjust model.transform.json (dimensions, normalization, anchor_point).")


if __name__ == "__main__":
    main()
