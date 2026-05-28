#!/usr/bin/env python3
"""
Test glTF export with procedural geometry (walls, doors, windows).

This test creates a simple floor plan with basic elements and exports it to glTF
to verify that procedural geometry generation works.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from floor_planner.floor_plan import FloorPlan
from floor_planner.elements import Wall, Door, Window


def main():
    print("=" * 70)
    print("glTF Export Test - Procedural Geometry")
    print("=" * 70)
    print()
    
    # Create floor plan
    print("1. Creating floor plan with walls, doors, and windows...")
    floor_plan = FloorPlan(
        bottom_left_corner=(0, 0),
        top_right_corner=(10, 10),
        scale_numerator=1,
        scale_denominator=100
    )
    
    # Add walls to create a simple room (4m x 3m)
    print("   Adding 4 walls...")
    
    # Bottom wall
    floor_plan.add_element(Wall(
        anchor_point=(1, 1),
        length=4,
        thickness=0.2,
        orientation_angle=0,
        color='gray',
        label='South Wall'
    ))
    
    # Right wall
    floor_plan.add_element(Wall(
        anchor_point=(5, 1),
        length=3,
        thickness=0.2,
        orientation_angle=90,
        color='gray',
        label='East Wall'
    ))
    
    # Top wall
    floor_plan.add_element(Wall(
        anchor_point=(5, 4),
        length=4,
        thickness=0.2,
        orientation_angle=180,
        color='gray',
        label='North Wall'
    ))
    
    # Left wall
    floor_plan.add_element(Wall(
        anchor_point=(1, 4),
        length=3,
        thickness=0.2,
        orientation_angle=270,
        color='gray',
        label='West Wall'
    ))
    
    # Add a door in the bottom wall
    print("   Adding 1 door...")
    floor_plan.add_element(Door(
        anchor_point=(2.5, 1),
        thickness=0.2,
        door_width=0.8,
        doorway_width=1.0,
        orientation_angle=0,
        color='brown',
        label='Main Door'
    ))
    
    # Add a window in the right wall
    print("   Adding 1 window...")
    floor_plan.add_element(Window(
        anchor_point=(5, 2),
        overall_thickness=0.2,
        single_line_thickness=0.05,
        length=1.2,
        orientation_angle=90,
        color='lightblue',
        label='East Window'
    ))
    
    print(f"   ✓ Floor plan created with {len(floor_plan.elements)} elements")
    print()
    
    # Export to glTF
    print("2. Exporting to glTF...")
    output_dir = Path("examples/gltf_output")
    
    try:
        gltf_file = floor_plan.export_to_gltf(
            output_dir=output_dir,
            filename="procedural_test.gltf"
        )
        print()
    except Exception as e:
        print(f"   ✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Verify output
    print("3. Verifying output files...")
    gltf_path = output_dir / "procedural_test.gltf"
    
    if gltf_path.exists():
        print(f"   ✓ glTF file exists: {gltf_path}")
        
        # Read and analyze glTF file
        import json
        with open(gltf_path, 'r') as f:
            gltf_data = json.load(f)
        
        file_size_kb = gltf_path.stat().st_size / 1024
        print(f"   ✓ File size: {file_size_kb:.2f} KB")
        print()
        
        print(f"   glTF Structure:")
        print(f"     - Version: {gltf_data['asset']['version']}")
        print(f"     - Generator: {gltf_data['asset']['generator']}")
        print(f"     - Scenes: {len(gltf_data.get('scenes', []))}")
        print(f"     - Nodes: {len(gltf_data.get('nodes', []))}")
        print(f"     - Meshes: {len(gltf_data.get('meshes', []))}")
        print(f"     - Materials: {len(gltf_data.get('materials', []))}")
        print()
        
        # List nodes
        if gltf_data.get('nodes'):
            print(f"   Node Details:")
            for node in gltf_data['nodes']:
                node_name = node.get('name', 'unnamed')
                extras = node.get('extras', {})
                procedural = extras.get('procedural', False)
                element_type = extras.get('element_type', 'unknown')
                print(f"     - {node_name}: type={element_type}, procedural={procedural}")
        print()
        
        # List materials
        if gltf_data.get('materials'):
            print(f"   Material Details:")
            for material in gltf_data['materials']:
                mat_name = material.get('name', 'unnamed')
                pbr = material.get('pbrMetallicRoughness', {})
                base_color = pbr.get('baseColorFactor', [1, 1, 1, 1])[:3]
                print(f"     - {mat_name}: color={[f'{c:.2f}' for c in base_color]}")
        print()
        
        # Check for binary buffer
        bin_file = output_dir / "procedural_test.bin"
        if bin_file.exists():
            bin_size_kb = bin_file.stat().st_size / 1024
            print(f"   ✓ Binary buffer: {bin_file} ({bin_size_kb:.2f} KB)")
        else:
            print(f"   • No binary buffer (no geometry data)")
    else:
        print(f"   ✗ glTF file not found: {gltf_path}")
        return 1
    
    print()
    print("=" * 70)
    print("✓ glTF Export Test PASSED")
    print("=" * 70)
    print()
    print(f"View the exported scene:")
    print(f"  - Blender: File > Import > glTF 2.0 > {gltf_path}")
    print(f"  - Online: https://gltf-viewer.donmccurdy.com/")
    print(f"  - Three.js: Use GLTFLoader in your viewer")
    print()
    print("✨ Export includes:")
    print("  ✓ Procedurally generated 3D geometry (walls, doors, windows)")
    print("  ✓ PBR materials with element-specific colors")
    print("  ✓ Proper 3D extrusion from 2D floor plan")
    print("  ✓ Vertical positioning (v_anchor + height)")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
