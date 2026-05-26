# Automated Texture Generation Guide

This guide covers different methods to automatically generate realistic textures for 3D floor plan models.

## Methods Overview

| Method | Cost | Setup Difficulty | Quality | Speed |
|--------|------|------------------|---------|-------|
| **DALL-E API** | ~$1.60 | Easy | Excellent | Fast |
| **Stability AI API** | ~$2.00 | Easy | Excellent | Fast |
| **Local Stable Diffusion** | Free | Complex | Excellent | Medium |
| **Manual Web UI** | Free-$20/mo | Very Easy | Excellent | Slow |

## 1. DALL-E API (Recommended) ✅

**Best for:** Quick, automated, high-quality results

### Setup
```bash
# Install dependencies
pip install openai pillow

# Set API key
export OPENAI_API_KEY="sk-..."

# Run script
python scripts/generate_textures_dalle.py
```

### Cost
- **$0.040 per 1024x1024 image** (standard quality)
- **$0.080 per 1024x1024 image** (HD quality)
- **Total: ~$1.60 for all 40 textures** (standard)

### Pros
- ✅ Fully automated - set and forget
- ✅ Excellent quality (DALL-E 3)
- ✅ Fast generation (2-5 seconds per image)
- ✅ No GPU required
- ✅ Script provided: `scripts/generate_textures_dalle.py`

### Cons
- ❌ Requires paid OpenAI API access
- ❌ Internet connection required

## 2. Stability AI API

**Best for:** Alternative to DALL-E with similar features

### Setup
```bash
# Install dependencies
pip install stability-sdk pillow

# Set API key
export STABILITY_API_KEY="sk-..."

# Run script (to be created)
python scripts/generate_textures_stability.py
```

### Cost
- **Varies by model** (~$0.05-0.10 per image)
- **Total: ~$2-4 for all 40 textures**

### Pros
- ✅ Multiple model options (SD 1.5, SDXL, etc.)
- ✅ More control over generation parameters
- ✅ Commercial-friendly licensing

### Cons
- ❌ Requires paid Stability AI API key
- ❌ More complex prompting

## 3. Local Stable Diffusion (Free)

**Best for:** No API costs, full control, offline generation

### Setup

#### Option A: ComfyUI (Recommended)
```bash
# Install ComfyUI
git clone https://github.com/comfyanonymous/ComfyUI
cd ComfyUI
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Download model (SDXL recommended)
# Place in: models/checkpoints/

# Enable API server
python main.py --listen --port 8188
```

#### Option B: Automatic1111
```bash
# Install Automatic1111
git clone https://github.com/AUTOMATIC1111/stable-diffusion-webui
cd stable-diffusion-webui
./webui.sh --api
```

### Requirements
- **GPU:** 4GB+ VRAM (8GB+ recommended for SDXL)
- **Disk:** ~10GB for models
- **RAM:** 16GB+ recommended

### Automation Script
Create `scripts/generate_textures_local.py` that connects to local API:
```python
import requests
import base64
from pathlib import Path

API_URL = "http://127.0.0.1:7860"  # Automatic1111
# Or: "http://127.0.0.1:8188"  # ComfyUI

def generate_texture(prompt, filename):
    payload = {
        "prompt": prompt,
        "steps": 30,
        "width": 1024,
        "height": 1024,
        "sampler_name": "DPM++ 2M Karras",
    }
    
    response = requests.post(f"{API_URL}/sdapi/v1/txt2img", json=payload)
    image_data = response.json()['images'][0]
    
    # Decode and save
    image = Image.open(BytesIO(base64.b64decode(image_data)))
    image.save(f"textures/defaults/{filename}")
```

### Pros
- ✅ **Free** - no API costs
- ✅ Offline generation
- ✅ Full control over models and parameters
- ✅ Can fine-tune models for specific styles

### Cons
- ❌ Complex setup
- ❌ Requires powerful GPU
- ❌ Slower generation (30-60 seconds per image)
- ❌ Requires technical knowledge

## 4. Manual Web UI (Simplest)

**Best for:** One-time generation, no coding

### Free Options
1. **Bing Image Creator** (DALL-E 3)
   - URL: https://www.bing.com/create
   - Limit: ~15 images/day free

2. **Google ImageFX** (Imagen)
   - URL: https://aitestkitchen.withgoogle.com/tools/image-fx
   - Limit: Generous free tier

3. **Leonardo.AI**
   - URL: https://leonardo.ai
   - Limit: 150 images/day free

### Workflow
1. Open web UI
2. Copy-paste prompts from `scripts/generate_textures_dalle.py`
3. Generate and download images
4. Rename and move to `textures/defaults/`

### Pros
- ✅ No setup required
- ✅ Free options available
- ✅ No coding needed
- ✅ High quality

### Cons
- ❌ Manual process (tedious for 40 textures)
- ❌ Rate limits on free tiers
- ❌ Must download and organize files manually

## 5. Batch Processing with AI Services

### Leonardo.AI Batch Generation
Leonardo.AI supports batch generation through their API:

```bash
# Install SDK
pip install leonardo-ai

# Generate in batch
python scripts/generate_textures_leonardo.py
```

Cost: Free tier (150/day) or $10/month for more

## Recommended Workflow

### For Quick Start (Easiest)
1. Use **DALL-E API script** ($1.60 total cost)
2. Run once: `python scripts/generate_textures_dalle.py`
3. Review generated textures
4. Re-generate any unsatisfactory textures

### For Budget (Free but Manual)
1. Use **Bing Image Creator** or **Google ImageFX**
2. Generate 5-10 textures per day (rate limits)
3. Takes 4-8 days to complete all 40 textures

### For Advanced Users (Free but Complex)
1. Set up **Local Stable Diffusion** with ComfyUI
2. Create automation script
3. Generate all textures overnight

## Texture Prompt Tips

### Good Prompts Include:
- **Material description:** "oak wood", "stainless steel", "white porcelain"
- **Surface quality:** "smooth", "brushed", "glossy", "matte"
- **Lighting:** "even lighting", "subtle shadows", "natural light"
- **Scale/view:** "top view", "front view", "close-up"
- **Quality:** "4k quality", "high resolution", "photorealistic"
- **Use case:** "seamless tileable" (for walls/floors), "architectural"

### Avoid:
- ❌ Multiple objects in one texture
- ❌ Complex scenes
- ❌ Text or labels
- ❌ Perspective distortion (for architectural elements)

## Complete Texture Prompts (42 Total)

Copy these prompts directly into Microsoft Copilot, Bing Image Creator, or your preferred AI image generator. After generating, save each with the corresponding filename to `textures/defaults/`.

### 🏗️ Structural Elements (5 textures)

**wall.jpg**
```
Realistic light gray painted wall texture, smooth plaster, subtle grain, even lighting, seamless tileable, architectural, neutral, 4k quality
```

**door.jpg**
```
Realistic oak wood door panel texture, natural wood grain, medium brown, vertical grain pattern, subtle knots, front view, 4k quality
```

**door_frame.jpg**
```
White painted wood trim texture, smooth finish, slight sheen, clean architectural molding, 4k quality
```

**window.jpg**
```
Modern white vinyl window frame texture with glass panes, clean, residential, subtle reflections, 4k quality
```

**floor.jpg**
```
Light oak hardwood floor texture, natural wood grain, horizontal planks, seamless tileable, warm tone, residential, 4k quality
```

### 🗄️ Storage Furniture (4 textures)

**wardrobe.jpg**
```
White painted wood cabinet door texture, smooth finish, modern furniture, clean, residential, 4k quality
```

**bookshelf.jpg**
```
Natural wood bookshelf texture, vertical grain, medium brown, library furniture, 4k quality
```

**dresser.jpg**
```
Cherry wood dresser texture with drawer fronts, natural grain, warm reddish-brown, furniture quality, 4k quality
```

**nightstand.jpg**
```
Light wood nightstand texture, scandinavian style, natural oak, simple clean finish, 4k quality
```

### 🪑 Living & Bedroom Furniture (5 textures)

**desk.jpg**
```
Oak wood desk surface texture, top-down view, natural wood grain, matte finish, warm brown, subtle knots, office furniture, 4k quality
```

**table.jpg**
```
Walnut dining table surface texture, polished finish, rich brown, natural grain patterns, top view, 4k quality
```

**chair.jpg**
```
Upholstered fabric chair texture, dark gray linen weave, subtle texture, furniture grade, neutral, 4k quality
```

**sofa.jpg**
```
Navy blue fabric sofa upholstery texture, soft woven fabric, furniture grade, subtle texture, residential, 4k quality
```

**bed.jpg**
```
White quilted mattress surface texture with subtle stitching pattern, clean bedding, hotel quality, 4k quality
```

### 🍳 Kitchen Appliances (6 textures)

**refrigerator.jpg**
```
Stainless steel refrigerator front panel texture, brushed metal, realistic appliance finish, subtle vertical grain, modern kitchen, 4k quality
```

**stove.jpg**
```
Black ceramic glass cooktop surface texture, glossy smooth finish, modern kitchen appliance, 4k quality
```

**oven.jpg**
```
Stainless steel oven door texture, brushed metal finish, professional kitchen appliance, 4k quality
```

**dishwasher.jpg**
```
Stainless steel dishwasher front panel, brushed metal texture, modern kitchen appliance, 4k quality
```

**microwave.jpg**
```
Stainless steel microwave front panel, brushed metal, modern kitchen, 4k quality
```

**rangehood.jpg**
```
Stainless steel range hood texture, brushed metal finish, professional kitchen, 4k quality
```

### 🧺 Laundry Appliances (2 textures)

**washer.jpg**
```
White enamel washing machine front texture, smooth glossy finish, modern appliance, clean, 4k quality
```

**dryer.jpg**
```
White enamel dryer front texture, smooth glossy finish, modern appliance, matching washer, 4k quality
```

### 🚽 Bathroom Fixtures (5 textures)

**toilet.jpg**
```
White porcelain toilet fixture texture, glossy ceramic finish, clean bathroom fixture, residential, 4k quality
```

**sink.jpg**
```
White porcelain sink basin texture, smooth ceramic glaze, bathroom fixture, clean, 4k quality
```

**bathtub.jpg**
```
White acrylic bathtub texture, smooth glossy finish, modern bathroom fixture, clean, 4k quality
```

**shower.jpg**
```
Chrome shower fixture with glass door texture, metallic shine, modern bathroom, clean, 4k quality
```

**bidet.jpg**
```
White porcelain bidet texture, glossy ceramic finish, bathroom fixture, clean, 4k quality
```

### 💡 Lighting Fixtures (2 textures)

**ceiling_lamp.jpg**
```
Modern white ceiling light fixture texture with frosted glass diffuser, clean minimalist design, 4k quality
```

**wall_lamp.jpg**
```
Brushed nickel wall sconce texture with white glass shade, modern lighting fixture, 4k quality
```

### ⚡ Electrical (2 textures)

**power_outlet.jpg**
```
White plastic electrical outlet cover plate, smooth finish, residential grade, clean, 4k quality
```

**switch.jpg**
```
White plastic light switch cover plate, smooth finish, modern toggle style, residential, 4k quality
```

### 🌳 Landscaping - Vegetation (4 textures)

**tree.jpg**
```
Tree bark texture with green foliage, natural oak bark, realistic outdoor, 4k quality
```

**shrub.jpg**
```
Dense green hedge shrub texture, small leaves, garden landscaping, natural, 4k quality
```

**hedge.jpg**
```
Trimmed boxwood hedge texture, uniform green leaves, formal garden, neat landscaping, 4k quality
```

**lawn.jpg**
```
Fresh cut green grass lawn texture, top view, even coverage, seamless tileable, residential landscaping, 4k quality
```

### 🪨 Landscaping - Hardscape (6 textures)

**path.jpg**
```
Gray concrete paver pathway texture, rectangular stones, slight texture, garden walkway, seamless tileable, 4k quality
```

**deck.jpg**
```
Weathered wood deck planks texture, horizontal boards, natural gray-brown, outdoor, seamless tileable, 4k quality
```

**fence.jpg**
```
Vertical wood fence boards texture, natural cedar color, outdoor fencing, residential, 4k quality
```

**pool.jpg**
```
Light blue pool water surface texture with subtle ripples, swimming pool, crystal clear, 4k quality
```

**fountain.jpg**
```
Smooth gray stone fountain texture, natural stone, wet surface, water feature, 4k quality
```

**pond.jpg**
```
Natural pond water surface texture, dark blue-green, slight ripples, landscaping water feature, 4k quality
```

### 🎨 Fallback (1 texture)

**default.jpg**
```
Light gray neutral surface texture, smooth matte finish, generic material, architectural, 4k quality
```

### 📝 Usage Instructions

**For Microsoft Copilot / Bing Image Creator:**
1. Go to: https://www.bing.com/images/create
2. Sign in with Microsoft account (free)
3. Copy-paste each prompt above
4. Click "Create" and wait 10-30 seconds
5. Download the best image (right-click → Save As)
6. Rename to the filename shown (e.g., "wall.jpg")
7. **Save to: `textures/defaults/` folder** ⬅️ Important!

**For DALL-E API (automated):**
```bash
python scripts/generate_textures_dalle.py
```
All prompts are already included in the script!
Textures are automatically saved to `textures/defaults/`.

**Texture Folder Structure:**
- `textures/defaults/` - Put your custom/realistic textures here (checked first)
- `textures/fallback/` - Dummy solid-color textures (used as backup)

The 3D exporter will use textures from `defaults/` if present, otherwise fall back to `fallback/` dummy textures. This means you can generate textures incrementally - start with the most important ones (walls, doors, windows) and the rest will use fallback textures automatically.

**Priority Order (if doing manually):**
1. **High priority:** wall, door, window, floor (structural - 4 textures)
2. **Medium priority:** desk, chair, sofa, bed, table (common furniture - 5 textures)
3. **Medium priority:** refrigerator, stove, toilet, sink (appliances - 4 textures)
4. **Low priority:** All remaining textures as needed

## Post-Processing

After generation, you may want to:

1. **Resize to 1024x1024** (if not already)
   ```bash
   mogrify -resize 1024x1024 -quality 95 textures/defaults/*.jpg
   ```

2. **Make seamless** (for walls/floors)
   - Use GIMP's "Filters > Distorts > Seamless"
   - Or Photoshop's "Filter > Other > Offset"

3. **Adjust brightness/contrast**
   ```bash
   mogrify -brightness-contrast 5x10 textures/defaults/wall.jpg
   ```

## Next Steps

1. Choose your preferred method
2. Generate textures
3. Test in 3D viewer (Blender, SketchUp)
4. Iterate on any textures that need improvement

## Troubleshooting

### "API key invalid"
- Check environment variable: `echo $OPENAI_API_KEY`
- Verify key at: https://platform.openai.com/api-keys

### "Out of memory" (local Stable Diffusion)
- Reduce image size to 512x512
- Close other applications
- Use `--lowvram` flag

### "Texture doesn't look realistic"
- Regenerate with more detailed prompt
- Try different quality settings (HD vs standard)
- Post-process in image editor

### "Textures don't tile seamlessly"
- Use GIMP/Photoshop to make seamless
- Or regenerate with "seamless tileable pattern" in prompt

## Cost Comparison

| Method | Total Cost | Time |
|--------|-----------|------|
| DALL-E API | $1.60 | 5 min |
| Stability AI | $2-4 | 10 min |
| Local SD | Free (electricity) | 30-60 min |
| Web UI Manual | Free-$20 | 4-8 days |

**Recommendation:** Use DALL-E API for speed and quality. The $1.60 cost is negligible compared to time saved.
