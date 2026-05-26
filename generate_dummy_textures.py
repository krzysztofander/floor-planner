#!/usr/bin/env python3
"""
Generate dummy textures for 3D floor plan visualization.

Creates solid-color 512x512 JPEG files for all element types.
This is Phase 2 of the 3D OBJ/MTL generation feature.
Run this script once to populate the textures/defaults/ directory.
"""

from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# Output directory
OUTPUT_DIR = Path(__file__).parent / 'textures' / 'defaults'

# Texture definitions: {filename: (R, G, B, description)}
TEXTURES = {
    # Structural elements
    'wall.jpg': ((221, 221, 221), 'Light gray wall'),
    'door.jpg': ((139, 111, 71), 'Wood brown door'),
    'door_frame.jpg': ((240, 240, 240), 'White painted door frame'),
    'sliding_door.jpg': ((160, 130, 90), 'Lighter wood sliding door'),
    'window.jpg': ((176, 224, 230), 'Light blue window glass'),
    'stairs.jpg': ((180, 180, 180), 'Gray concrete stairs'),
    'floor.jpg': ((200, 170, 130), 'Light wood floor'),
    
    # Furniture - General
    'table.jpg': ((160, 130, 90), 'Wood table'),
    'chair.jpg': ((140, 120, 80), 'Wood chair'),
    'sofa.jpg': ((100, 100, 120), 'Gray-blue sofa'),
    'armchair.jpg': ((110, 110, 130), 'Gray-blue armchair'),
    'bed.jpg': ((230, 230, 240), 'White/cream bed'),
    'wardrobe.jpg': ((180, 150, 110), 'Wood wardrobe'),
    'cabinet.jpg': ((170, 140, 100), 'Wood cabinet'),
    'shelves.jpg': ((190, 160, 120), 'Light wood shelves'),
    'desk.jpg': ((150, 120, 80), 'Dark wood desk'),
    'nightstand.jpg': ((165, 135, 95), 'Wood nightstand'),
    'bookcase.jpg': ((175, 145, 105), 'Wood bookcase'),
    'bookshelf.jpg': ((175, 145, 105), 'Wood bookshelf'),
    'dresser.jpg': ((160, 130, 90), 'Wood dresser'),
    'drawer.jpg': ((155, 125, 85), 'Wood drawer'),
    'bench.jpg': ((145, 115, 75), 'Wood bench'),
    'tvstand.jpg': ((150, 120, 80), 'Dark wood TV stand'),
    
    # Kitchen & Bathroom
    'countertop.jpg': ((200, 200, 205), 'Light gray countertop'),
    'sink.jpg': ((220, 220, 225), 'White ceramic sink'),
    'stove.jpg': ((50, 50, 60), 'Dark gray/black stove'),
    'oven.jpg': ((55, 55, 65), 'Dark gray oven'),
    'refrigerator.jpg': ((240, 240, 245), 'White refrigerator'),
    'microwave.jpg': ((210, 210, 215), 'Light gray microwave'),
    'rangehood.jpg': ((200, 200, 205), 'Stainless steel range hood'),
    'bathtub.jpg': ((230, 230, 235), 'White bathtub'),
    'shower.jpg': ((225, 225, 230), 'White shower'),
    'toilet.jpg': ((235, 235, 240), 'White toilet'),
    'bidet.jpg': ((230, 230, 235), 'White bidet'),
    'washer.jpg': ((215, 215, 220), 'Light gray washer'),
    'dryer.jpg': ((215, 215, 220), 'Light gray dryer'),
    'dishwasher.jpg': ((210, 210, 215), 'Light gray dishwasher'),
    
    # Landscaping - Vegetation
    'tree.jpg': ((34, 139, 34), 'Forest green tree'),
    'bush.jpg': ((50, 155, 50), 'Medium green bush'),
    'shrub.jpg': ((50, 155, 50), 'Medium green shrub'),
    'hedge.jpg': ((60, 170, 60), 'Bright green hedge'),
    'lawn.jpg': ((85, 180, 85), 'Grass green lawn'),
    'flower_bed.jpg': ((255, 192, 203), 'Pink flower bed'),
    
    # Landscaping - Hardscape
    'deck.jpg': ((150, 120, 80), 'Wood deck'),
    'fence.jpg': ((160, 130, 90), 'Wood fence'),
    'path.jpg': ((180, 170, 150), 'Beige stone path'),
    'patio.jpg': ((170, 160, 140), 'Gray patio'),
    'driveway.jpg': ((130, 130, 130), 'Dark gray driveway'),
    
    # Landscaping - Water
    'pool.jpg': ((70, 130, 180), 'Blue pool water'),
    'pond.jpg': ((80, 140, 190), 'Light blue pond water'),
    'fountain.jpg': ((90, 150, 200), 'Cyan fountain water'),
    
    # Electrical & Lighting
    'outlet.jpg': ((240, 240, 240), 'White outlet plate'),
    'power_outlet.jpg': ((240, 240, 240), 'White power outlet plate'),
    'switch.jpg': ((245, 245, 245), 'White switch plate'),
    'ceiling_lamp.jpg': ((255, 250, 200), 'Warm white ceiling lamp'),
    'wall_lamp.jpg': ((255, 245, 190), 'Warm white wall lamp'),
    'floor_lamp.jpg': ((255, 240, 180), 'Warm white floor lamp'),
    
    # Default fallback
    'default.jpg': ((200, 200, 200), 'Light gray default'),
}


def generate_texture(filename: str, color: tuple[int, int, int], description: str):
    """
    Generate a solid color texture with text label.
    
    Args:
        filename: Output filename
        color: RGB color tuple
        description: Text description to render on texture
    """
    # Create 512x512 image
    img = Image.new('RGB', (512, 512), color)
    draw = ImageDraw.Draw(img)
    
    # Try to use a nice font, fall back to default if not available
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 24)
        small_font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 16)
    except:
        font = ImageFont.load_default()
        small_font = ImageFont.load_default()
    
    # Calculate text color (black for light backgrounds, white for dark)
    brightness = (color[0] * 299 + color[1] * 587 + color[2] * 114) / 1000
    text_color = (0, 0, 0) if brightness > 128 else (255, 255, 255)
    
    # Draw description text in center
    bbox = draw.textbbox((0, 0), description, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = (512 - text_width) // 2
    text_y = (512 - text_height) // 2
    draw.text((text_x, text_y), description, fill=text_color, font=font)
    
    # Draw RGB values in corner
    rgb_text = f"RGB: {color[0]}, {color[1]}, {color[2]}"
    draw.text((10, 480), rgb_text, fill=text_color, font=small_font)
    
    # Save as JPEG
    output_path = OUTPUT_DIR / filename
    img.save(output_path, 'JPEG', quality=90)
    print(f"  Generated: {filename} - {description}")


def main():
    """Generate all dummy textures."""
    print("Generating dummy textures for floor_planner...")
    print(f"Output directory: {OUTPUT_DIR}")
    print()
    
    # Create output directory
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    
    # Generate each texture
    for filename, (color, description) in TEXTURES.items():
        generate_texture(filename, color, description)
    
    print()
    print(f"Successfully generated {len(TEXTURES)} textures in {OUTPUT_DIR}")
    print()
    print("These are dummy textures for Phase 2 development.")
    print("They will be replaced with realistic textures in Phase 7.")


if __name__ == '__main__':
    main()
