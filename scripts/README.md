# Floor Planner Utility Scripts

Utility scripts for model validation and 3D visualization.

## Available Scripts

### `validate_models.py` — Model Validator

Validates all external 3D models and their metadata in the `models/` directory.

**Usage:**
```bash
python scripts/validate_models.py
python scripts/validate_models.py --models-dir=path/to/models
python scripts/validate_models.py --verbose
```

Checks:
- Required files exist (`model.obj`/`model.glb` + `model.transform.json`)
- Metadata structure and field validity
- Bounding box correctness
- Registry key matches directory name

### `run_3d_walker.sh` — OBJ Viewer Launcher

Launches a 3D visualization tool on exported OBJ files.

> **Note:** The primary export format is now **glTF** (`.gltf` + `.bin`). This script is only useful if you have legacy OBJ exports or want to inspect raw OBJ geometry files.

**Requirements:** A 3D viewer executable (e.g., MeshLab, Blender)

**Usage:**
```bash
# 1. Set your 3D viewer path
export WALKER_3D="/usr/local/bin/meshlab"

# 2. Copy script next to the OBJ file
cp scripts/run_3d_walker.sh path/to/directory/

# 3. Run from that directory
cd path/to/directory/
./run_3d_walker.sh
```

Expected directory structure:
```
directory/
├── run_3d_walker.sh
├── your_model.obj
├── your_model.mtl
└── textures/
    ├── texture1.png
    └── texture2.jpg
```
