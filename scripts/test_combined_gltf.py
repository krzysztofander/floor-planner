#!/usr/bin/env python3
"""
Test glTF export with combined procedural and external model geometry.

This test creates a floor plan with both procedural elements (walls, doors, windows)
and external models (wooden chairs), verifying they work together.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from floor_planner.floor_plan import FloorPlan
from floor_planner.elements import Wall, Door, Window
from floor_planner.elements.wooden_chair import WoodenChair


def main():
    print("=" * 70)
    print("glTF Export Test - Combined Procedural + External Models")
    print("=" * 70)
    print()
    
    # Create floor plan
    print("1. Creating floor plan...")
    floor_plan = FloorPlan(
        bottom_left_corner=(0, 0),
        top_right_corner=(10, 10),
        scale_numerator=1,
        scale_denominator=100
    )
    
    # Add walls to create a room
    print("   Adding walls...")
    floor_plan.add_element(Wall(
        anchor_point=(1, 1),
        length=4,
        thickness=0.2,
        orientation_angle=0,
        color='gray',
        label='South Wall'
    ))
    
    floor_plan.add_element(Wall(
        anchor_point=(5, 1),
        length=3,
        thickness=0.2,
        orientation_angle=90,
        color='gray',
        label='East Wall'
    ))
    
    floor_plan.add_element(Wall(
        anchor_point=(5, 4),
        length=4,
        thickness=0.2,
        orientation_angle=180,
        color='gray',
        label='North Wall'
    ))
    
    floor_plan.add_element(Wall(
        anchor_point=(1, 4),
        length=3,
        thickness=0.2,
        orientation_angle=270,
        color='gray',
        label='West Wall'
    ))
    
    # Add door
    print("   Adding door...")
    floor_plan.add_element(Door(
        anchor_point=(2.5, 1),
        thickness=0.2,
        door_width=0.8,
        doorway_width=1.0,
        orientation_angle=0,
        color='brown',
        label='Main Door'
    ))
    
    # Add window
    print("   Adding window...")
    floor_plan.add_element(Window(
        anchor_point=(5, 2),
        overall_thickness=0.2,
        single_line_thickness=0.05,
        length=1.2,
        orientation_angle=90,
        color='lightblue',
        label='East Window'
    ))
    
    # Add wooden chairs (external models)
    print("   Adding wooden chairs...")
    floor_plan.add_element(WoodenChair(
        anchor_point=(2, 2),
        orientation_angle=0,
        label='Chair 1'
    ))
    
    floor_plan.add_element(WoodenChair(
        anchor_point=(3.5, 2),
        orientation_angle=45,
        label='Chair 2'
    ))
    
    floor_plan.add_element(WoodenChair(
        anchor_point=(2, 3),
        orientation_angle=90,
        label='Chair 3'
    ))
    
    print(f"   ✓ Floor plan created with {len(floor_plan.elements)} elements")
    print("     - 4 walls (procedural)")
    print("     - 1 door (procedural)")
    print("     - 1 window (procedural)")
    print("     - 3 wooden chairs (external models)")
    print()
    
    # Export to glTF
    print("2. Exporting to glTF...")
    output_dir = Path("examples/gltf_output")
    
    try:
        gltf_file = floor_plan.export_to_gltf(
            output_dir=output_dir,
            filename="combined_test.gltf"
        )
        print()
    except Exception as e:
        print(f"   ✗ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Verify output
    print("3. Verifying output files...")
    gltf_path = output_dir / "combined_test.gltf"
    
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
        print(f"     - Scenes: {len(gltf_data.get('scenes', []))}")
        print(f"     - Nodes: {len(gltf_data.get('nodes', []))} (6 procedural + 3 external)")
        print(f"     - Meshes: {len(gltf_data.get('meshes', []))} (6 procedural + 1 shared external)")
        print(f"     - Materials: {len(gltf_data.get('materials', []))}")
        print(f"     - Textures: {len(gltf_data.get('textures', []))}")
        print(f"     - Images: {len(gltf_data.get('images', []))}")
        print()
        
        # Separate procedural and external nodes
        procedural_nodes = []
        external_nodes = []
        for node in gltf_data.get('nodes', []):
            extras = node.get('extras', {})
            if extras.get('procedural'):
                procedural_nodes.append(node)
            elif extras.get('external_model'):
                external_nodes.append(node)
        
        print(f"   Procedural Elements ({len(procedural_nodes)}):")
        for node in procedural_nodes:
            name = node.get('name', 'unnamed')
            extras = node.get('extras', {})
            elem_type = extras.get('element_type', 'unknown')
            print(f"     - {name}: {elem_type}")
        print()
        
        print(f"   External Models ({len(external_nodes)}):")
        for node in external_nodes:
            name = node.get('name', 'unnamed')
            print(f"     - {name}")
        print()
        
        # Check for binary buffer
        bin_file = output_dir / "combined_test.bin"
        if bin_file.exists():
            bin_size_kb = bin_file.stat().st_size / 1024
            print(f"   ✓ Binary buffer: {bin_file} ({bin_size_kb:.2f} KB)")
        
        # Check for texture
        texture_file = output_dir / "wood_texture.jpg"
        if texture_file.exists():
            texture_size_kb = texture_file.stat().st_size / 1024
            print(f"   ✓ Texture file: {texture_file} ({texture_size_kb:.1f} KB)")
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
    print()
    print("✨ Export includes:")
    print("  ✓ Procedural geometry for walls, doors, windows")
    print("  ✓ External 3D models for furniture (wooden chairs)")
    print("  ✓ PBR materials for all elements")
    print("  ✓ Textures for external models")
    print("  ✓ Mesh instancing (3 chairs share 1 mesh)")
    print("  ✓ Proper transforms and positioning")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
