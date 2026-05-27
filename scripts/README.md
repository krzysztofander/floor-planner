# Floor Planner Utility Scripts

Automated scripts for texture generation and 3D visualization.

## Quick Start

### Texture Generation (Recommended)

```bash
# Install dependencies
pip install openai pillow

# Set your OpenAI API key
export OPENAI_API_KEY="sk-your-key-here"

# Generate all textures (~5 minutes, $1.60 cost)
python scripts/generate_textures_dalle.py
```

### 3D Visualization

```bash
# Set your 3D viewer executable
export WALKER_3D="/path/to/your/3d/viewer"

# Copy script to your 3D export directory
cp scripts/run_3d_walker.sh examples/3d_visualization/visualisation_3d/

# Run the viewer
cd examples/3d_visualization/visualisation_3d/
./run_3d_walker.sh
```

## Available Scripts

### `run_3d_walker.sh` 🎨 3D VIEWER
**Purpose:** Launch 3D visualization tools on exported OBJ files  
**Requirements:** 3D viewer executable (e.g., MeshLab, Blender)

Automated launcher for 3D visualization:
- Validates WALKER_3D environment variable
- Finds .obj files and textures automatically
- Passes full paths to your 3D viewer
- Comprehensive error messages and help

**Usage:**
```bash
# 1. Set your 3D viewer path
export WALKER_3D="/usr/local/bin/meshlab"

# 2. Copy script to visualisation_3d folder
cp scripts/run_3d_walker.sh path/to/visualisation_3d/

# 3. Run from that directory
cd path/to/visualisation_3d/
./run_3d_walker.sh
```

The script expects this directory structure:
```
visualisation_3d/
├── run_3d_walker.sh      # This script
├── your_floor_plan.obj   # OBJ file
├── your_floor_plan.mtl   # Material file
└── textures/             # Texture folder
    ├── texture1.png
    └── texture2.jpg
```

### `generate_textures_dalle.py` ✅ READY
**Status:** Production-ready  
**Cost:** ~$1.60 (40 textures × $0.040 each)  
**Time:** ~5 minutes  
**Quality:** Excellent (DALL-E 3)

Fully automated texture generation using OpenAI DALL-E API:
- 40 pre-written optimized prompts
- Automatic download and organization
- Skips existing textures (incremental generation)
- Converts to JPEG with optimal compression

## Documentation

See [../docs/TEXTURE_GENERATION.md](../docs/TEXTURE_GENERATION.md) for:
- Comparison of all generation methods
- Alternative APIs (Stability AI, Leonardo.AI)
- Local Stable Diffusion setup
- Manual web UI workflow
- Post-processing tips
- Troubleshooting guide

## Cost Comparison

| Method | Cost | Time | Setup |
|--------|------|------|-------|
| DALL-E API (this script) | $1.60 | 5 min | Easy |
| Manual web UI (free) | $0 | 4-8 days | Very Easy |
| Local Stable Diffusion | $0 | 30-60 min | Complex |

## Output

Textures are saved to: `textures/defaults/`

Generated files:
- wall.jpg, door.jpg, window.jpg (structural)
- desk.jpg, chair.jpg, sofa.jpg, bed.jpg (furniture)
- refrigerator.jpg, stove.jpg, oven.jpg (appliances)
- toilet.jpg, sink.jpg, bathtub.jpg (bathroom)
- ceiling_lamp.jpg, power_outlet.jpg (fixtures)
- tree.jpg, lawn.jpg, path.jpg, pool.jpg (landscaping)
- ...and 20 more

## Customization

Edit prompts in `generate_textures_dalle.py`:
```python
TEXTURE_PROMPTS = {
    "wall.jpg": "Your custom prompt here...",
    # ...
}
```

## Troubleshooting

**"No module named 'openai'"**
```bash
pip install openai pillow
```

**"Invalid API key"**
- Get key at: https://platform.openai.com/api-keys
- Set environment variable: `export OPENAI_API_KEY="sk-..."`

**"Rate limit exceeded"**
- Wait a few seconds between generation attempts
- Script includes 1-second delays automatically

## Examples

Generate single texture for testing:
```python
python -c "from scripts.generate_textures_dalle import generate_texture; \
generate_texture('test.jpg', 'oak wood desk surface texture, 4k')"
```

Check API key:
```bash
echo $OPENAI_API_KEY
```

List generated textures:
```bash
ls -lh textures/defaults/
```
