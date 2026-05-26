#!/usr/bin/env python3
"""
Automated texture generation using OpenAI DALL-E API.

Generates realistic textures for all floor plan elements and saves them to
textures/defaults/ folder. These will be used by the 3D exporter with fallback
to textures/fallback/ dummy textures for any missing textures.

Requirements:
    pip install openai pillow

Setup:
    export OPENAI_API_KEY="your-api-key-here"
    
Usage:
    python scripts/generate_textures_dalle.py
    
Cost: ~$1.60 for 40 textures at 1024x1024 ($0.040 per image)

Output: textures/defaults/ (custom textures, checked first by 3D exporter)
Fallback: textures/fallback/ (dummy textures, used if defaults not found)
"""

import os
from pathlib import Path
from openai import OpenAI
import requests
from PIL import Image
from io import BytesIO
import time

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Output directory
OUTPUT_DIR = Path("textures/defaults")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Texture prompts for each element type
TEXTURE_PROMPTS = {
    # Structural elements
    "wall.jpg": "Realistic light gray painted wall texture, smooth plaster, subtle grain, even lighting, seamless tileable, architectural, neutral, 4k quality",
    "door.jpg": "Realistic oak wood door panel texture, natural wood grain, medium brown, vertical grain pattern, subtle knots, front view, 4k quality",
    "door_frame.jpg": "White painted wood trim texture, smooth finish, slight sheen, clean architectural molding, 4k quality",
    "window.jpg": "Modern white vinyl window frame texture with glass panes, clean, residential, subtle reflections, 4k quality",
    "floor.jpg": "Light oak hardwood floor texture, natural wood grain, horizontal planks, seamless tileable, warm tone, residential, 4k quality",
    
    # Furniture - Wood
    "desk.jpg": "Oak wood desk surface texture, top-down view, natural wood grain, matte finish, warm brown, subtle knots, office furniture, 4k quality",
    "table.jpg": "Walnut dining table surface texture, polished finish, rich brown, natural grain patterns, top view, 4k quality",
    "chair.jpg": "Upholstered fabric chair texture, dark gray linen weave, subtle texture, furniture grade, neutral, 4k quality",
    "sofa.jpg": "Navy blue fabric sofa upholstery texture, soft woven fabric, furniture grade, subtle texture, residential, 4k quality",
    "bed.jpg": "White quilted mattress surface texture with subtle stitching pattern, clean bedding, hotel quality, 4k quality",
    "wardrobe.jpg": "White painted wood cabinet door texture, smooth finish, modern furniture, clean, residential, 4k quality",
    "bookshelf.jpg": "Natural wood bookshelf texture, vertical grain, medium brown, library furniture, 4k quality",
    "dresser.jpg": "Cherry wood dresser texture with drawer fronts, natural grain, warm reddish-brown, furniture quality, 4k quality",
    "nightstand.jpg": "Light wood nightstand texture, scandinavian style, natural oak, simple clean finish, 4k quality",
    
    # Kitchen appliances
    "refrigerator.jpg": "Stainless steel refrigerator front panel texture, brushed metal, realistic appliance finish, subtle vertical grain, modern kitchen, 4k quality",
    "stove.jpg": "Black ceramic glass cooktop surface texture, glossy smooth finish, modern kitchen appliance, 4k quality",
    "oven.jpg": "Stainless steel oven door texture, brushed metal finish, professional kitchen appliance, 4k quality",
    "dishwasher.jpg": "Stainless steel dishwasher front panel, brushed metal texture, modern kitchen appliance, 4k quality",
    "washer.jpg": "White enamel washing machine front texture, smooth glossy finish, modern appliance, clean, 4k quality",
    "dryer.jpg": "White enamel dryer front texture, smooth glossy finish, modern appliance, matching washer, 4k quality",
    "microwave.jpg": "Stainless steel microwave front panel, brushed metal, modern kitchen, 4k quality",
    "rangehood.jpg": "Stainless steel range hood texture, brushed metal finish, professional kitchen, 4k quality",
    
    # Bathroom fixtures
    "toilet.jpg": "White porcelain toilet fixture texture, glossy ceramic finish, clean bathroom fixture, residential, 4k quality",
    "sink.jpg": "White porcelain sink basin texture, smooth ceramic glaze, bathroom fixture, clean, 4k quality",
    "bathtub.jpg": "White acrylic bathtub texture, smooth glossy finish, modern bathroom fixture, clean, 4k quality",
    "shower.jpg": "Chrome shower fixture with glass door texture, metallic shine, modern bathroom, clean, 4k quality",
    "bidet.jpg": "White porcelain bidet texture, glossy ceramic finish, bathroom fixture, clean, 4k quality",
    
    # Lighting
    "ceiling_lamp.jpg": "Modern white ceiling light fixture texture with frosted glass diffuser, clean minimalist design, 4k quality",
    "wall_lamp.jpg": "Brushed nickel wall sconce texture with white glass shade, modern lighting fixture, 4k quality",
    
    # Electrical
    "power_outlet.jpg": "White plastic electrical outlet cover plate, smooth finish, residential grade, clean, 4k quality",
    "switch.jpg": "White plastic light switch cover plate, smooth finish, modern toggle style, residential, 4k quality",
    
    # Landscaping - Vegetation
    "tree.jpg": "Tree bark texture with green foliage, natural oak bark, realistic outdoor, 4k quality",
    "shrub.jpg": "Dense green hedge shrub texture, small leaves, garden landscaping, natural, 4k quality",
    "hedge.jpg": "Trimmed boxwood hedge texture, uniform green leaves, formal garden, neat landscaping, 4k quality",
    "lawn.jpg": "Fresh cut green grass lawn texture, top view, even coverage, seamless tileable, residential landscaping, 4k quality",
    
    # Landscaping - Hardscape
    "path.jpg": "Gray concrete paver pathway texture, rectangular stones, slight texture, garden walkway, seamless tileable, 4k quality",
    "deck.jpg": "Weathered wood deck planks texture, horizontal boards, natural gray-brown, outdoor, seamless tileable, 4k quality",
    "fence.jpg": "Vertical wood fence boards texture, natural cedar color, outdoor fencing, residential, 4k quality",
    "pool.jpg": "Light blue pool water surface texture with subtle ripples, swimming pool, crystal clear, 4k quality",
    "fountain.jpg": "Smooth gray stone fountain texture, natural stone, wet surface, water feature, 4k quality",
    "pond.jpg": "Natural pond water surface texture, dark blue-green, slight ripples, landscaping water feature, 4k quality",
    
    # Fallback
    "default.jpg": "Light gray neutral surface texture, smooth matte finish, generic material, architectural, 4k quality",
}


def generate_texture(filename: str, prompt: str, size: str = "1024x1024") -> bool:
    """
    Generate a single texture using DALL-E API.
    
    Args:
        filename: Output filename (e.g., 'wall.jpg')
        prompt: DALL-E prompt
        size: Image size (1024x1024, 1792x1024, or 1024x1792)
        
    Returns:
        True if successful, False otherwise
    """
    output_path = OUTPUT_DIR / filename
    
    # Skip if already exists
    if output_path.exists():
        print(f"⏭️  Skipping {filename} (already exists)")
        return True
    
    print(f"🎨 Generating {filename}...")
    print(f"   Prompt: {prompt[:80]}...")
    
    try:
        # Generate image with DALL-E
        response = client.images.generate(
            model="dall-e-3",
            prompt=prompt,
            size=size,
            quality="standard",  # or "hd" for higher quality (2x cost)
            n=1,
        )
        
        # Download image
        image_url = response.data[0].url
        image_response = requests.get(image_url)
        image = Image.open(BytesIO(image_response.content))
        
        # Convert to RGB if needed (remove alpha channel)
        if image.mode in ('RGBA', 'LA'):
            background = Image.new('RGB', image.size, (255, 255, 255))
            if image.mode == 'RGBA':
                background.paste(image, mask=image.split()[3])
            else:
                background.paste(image, mask=image.split()[1])
            image = background
        
        # Save as JPEG
        image.save(output_path, 'JPEG', quality=95)
        print(f"✅ Saved {filename}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to generate {filename}: {e}")
        return False


def main():
    """Generate all textures."""
    print("=" * 80)
    print("Automated Texture Generation with DALL-E")
    print("=" * 80)
    print(f"Output directory: {OUTPUT_DIR.resolve()}")
    print(f"Total textures: {len(TEXTURE_PROMPTS)}")
    print(f"Estimated cost: ${len(TEXTURE_PROMPTS) * 0.040:.2f} (standard quality)")
    print("=" * 80)
    print()
    
    # Check API key
    if not os.getenv("OPENAI_API_KEY"):
        print("❌ Error: OPENAI_API_KEY environment variable not set")
        print("   Please run: export OPENAI_API_KEY='your-key-here'")
        return
    
    # Generate textures
    success_count = 0
    fail_count = 0
    
    for i, (filename, prompt) in enumerate(TEXTURE_PROMPTS.items(), 1):
        print(f"\n[{i}/{len(TEXTURE_PROMPTS)}]")
        
        if generate_texture(filename, prompt):
            success_count += 1
        else:
            fail_count += 1
        
        # Rate limiting: wait between requests (DALL-E has generous limits)
        if i < len(TEXTURE_PROMPTS):
            time.sleep(1)
    
    # Summary
    print()
    print("=" * 80)
    print("Generation Complete")
    print("=" * 80)
    print(f"✅ Success: {success_count}/{len(TEXTURE_PROMPTS)}")
    if fail_count > 0:
        print(f"❌ Failed: {fail_count}/{len(TEXTURE_PROMPTS)}")
    print(f"💰 Approximate cost: ${success_count * 0.040:.2f}")
    print()


if __name__ == "__main__":
    main()
