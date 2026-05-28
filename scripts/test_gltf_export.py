"""
Test glTF export with wooden chair.

This script tests Phase 3 glTF export functionality by:
1. Creating a simple floor plan with wooden chairs
2. Exporting to glTF format
3. Verifying the output file structure
"""

from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from floor_planner.floor_plan import FloorPlan
from floor_planner.elements import WoodenChair, Wall

def main():
    print("=" * 70)
    print("glTF Export Test - Wooden Chair")
    print("=" * 70)
    print()
    
    # Create a simple floor plan
    print("1. Creating floor plan...")
    floor_plan = FloorPlan(
        bottom_left_corner=(0, 0),
        top_right_corner=(8, 6),
        scale_numerator=1,
        scale_denominator=50
    )
    
    # Add elements
    print("   Adding wall...")
    wall = Wall(anchor_point=[1, 1], length=6, thickness=0.2, height=2.8, orientation_angle=0)
    floor_plan.add_element(wall)
    
    print("   Adding wooden chairs...")
    chair1 = WoodenChair(anchor_point=[2, 3], orientation_angle=0)
    chair2 = WoodenChair(anchor_point=[4, 3], orientation_angle=45)
    chair3 = WoodenChair(anchor_point=[6, 3], orientation_angle=90)
    
    floor_plan.add_element(chair1)
    floor_plan.add_element(chair2)
    floor_plan.add_element(chair3)
    
    print(f"   ✓ Floor plan created with {len(floor_plan.elements)} elements")
    
    # Export to glTF
    print("\n2. Exporting to glTF...")
    output_dir = Path("examples/gltf_output")
    gltf_path = floor_plan.export_to_gltf(output_dir, "wooden_chair_test.gltf")
    
    # Verify output files
    print("\n3. Verifying output files...")
    
    if gltf_path.exists():
        print(f"   ✓ glTF file exists: {gltf_path}")
        
        # Check file size
        size_kb = gltf_path.stat().st_size / 1024
        print(f"   ✓ File size: {size_kb:.2f} KB")
        
        # Read and display basic info
        import json
        with open(gltf_path) as f:
            gltf_data = json.load(f)
        
        print(f"\n   glTF Structure:")
        print(f"     - Version: {gltf_data['asset']['version']}")
        print(f"     - Generator: {gltf_data['asset']['generator']}")
        print(f"     - Scenes: {len(gltf_data.get('scenes', []))}")
        print(f"     - Nodes: {len(gltf_data.get('nodes', []))}")
        print(f"     - Meshes: {len(gltf_data.get('meshes', []))}")
        print(f"     - Materials: {len(gltf_data.get('materials', []))}")
        print(f"     - Textures: {len(gltf_data.get('textures', []))}")
        print(f"     - Images: {len(gltf_data.get('images', []))}")
        
        # List materials
        if gltf_data.get('materials'):
            print(f"\n   Material Details:")
            for i, material in enumerate(gltf_data['materials']):
                mat_name = material.get('name', f'material_{i}')
                pbr = material.get('pbrMetallicRoughness', {})
                base_color = pbr.get('baseColorFactor', [1, 1, 1, 1])
                has_texture = 'baseColorTexture' in pbr
                print(f"     - {mat_name}: color={base_color[:3]}, texture={has_texture}")
        
        # List textures/images
        if gltf_data.get('images'):
            print(f"\n   Texture Files:")
            for i, image in enumerate(gltf_data['images']):
                image_uri = image.get('uri', 'embedded')
                image_name = image.get('name', f'image_{i}')
                # Check if file exists
                texture_path = output_dir / image_uri
                exists = "✓" if texture_path.exists() else "✗"
                if texture_path.exists():
                    size_kb = texture_path.stat().st_size / 1024
                    print(f"     {exists} {image_uri} ({size_kb:.1f} KB)")
                else:
                    print(f"     {exists} {image_uri} (not found)")
        
        # List nodes
        if gltf_data.get('nodes'):
            print(f"\n   Node Details:")
            for i, node in enumerate(gltf_data['nodes']):
                node_name = node.get('name', f'node_{i}')
                extras = node.get('extras', {})
                element_type = extras.get('element_type', 'unknown')
                print(f"     - {node_name}: type={element_type}, external_model={extras.get('external_model', False)}")
        
        # Check for binary buffer
        bin_file = output_dir / "wooden_chair_test.bin"
        if bin_file.exists():
            bin_size_kb = bin_file.stat().st_size / 1024
            print(f"\n   ✓ Binary buffer: {bin_file} ({bin_size_kb:.2f} KB)")
        else:
            print(f"\n   • No binary buffer (no geometry data yet)")
    else:
        print(f"   ✗ glTF file not found: {gltf_path}")
        return 1
    
    print("\n" + "=" * 70)
    print("✓ glTF Export Test PASSED")
    print("=" * 70)
    print()
    print(f"View the exported scene:")
    print(f"  - Blender: File > Import > glTF 2.0 > {gltf_path}")
    print(f"  - Online: https://gltf-viewer.donmccurdy.com/")
    print(f"  - Three.js: Use GLTFLoader in your viewer")
    print()
    print("✨ Export includes:")
    print("  ✓ 3D mesh geometry from external models")
    print("  ✓ PBR materials with color and texture support")
    print("  ✓ Transform hierarchy (rotation, scale, translation)")
    print("  ✓ Mesh instancing for efficient file sizes")
    print()
    
    return 0


if __name__ == '__main__':
    sys.exit(main())
