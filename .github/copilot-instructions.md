# Floor Planner - Agent Instructions

## Project Overview
This is a Python-based floor plan drawing tool controlled via YAML configuration files. It's a fork of [renovation](https://github.com/Nikolay-Lysenko/renovation) with enhanced features for technical users who prefer config-based interfaces over GUI drag-and-drop tools.

## Key Concepts

### Architecture
- **No GUI** - purely YAML-driven CLI tool
- **Room-based hierarchy** - rooms contain elements (walls, doors, windows, furniture)
- **Anchor point system** - elements positioned relative to room anchors for easy repositioning
- **Reusable templates** - shared element definitions across floor plans

### Important Additions (vs original renovation)
- Arithmetic expressions and variables in configs
- Room variables with expression evaluation
- External YAML file support for modular designs
- Markdown reports generation
- Enhanced room configuration options

## Development Workflow

### Running the Tool
```bash
# Activate virtual environment first
python -m floor_planner -c /path/to/config.yml

# Generate all examples
make all
```

### Testing & Regression Tests
**CRITICAL: After ANY source code changes, ALWAYS run:**
```bash
make check
```

This runs the pytest suite (`tests/`): every scene project in a temporary folder with
glTF invariants and a comparison of each PNG against `tests/golden/`, plus contract tests
over the element registry. Scenes listed in `GOLDEN_3D_SCENES` (`tests/conftest.py`) also compare
their glTF with a golden summary in `tests/golden/3d/`. After an intended visual or 3D change, refresh
the golden files with `.venv/bin/python -m pytest -m slow -n auto --update-golden` and review the
image and JSON diffs.

To also rebuild the images in the repository:
```bash
make clean; make tests
```

This ensures a clean build and runs all test configurations:
- `make clean` - removes all generated files to ensure fresh build
- `make tests` - builds all test floor plans

For full regression testing including examples:
```bash
make clean; make all
```

This builds all example floor plans and serves as comprehensive regression testing:
- `room_templates` - tests room-based designs
- `elements` - tests individual element rendering
- `furniture` - tests furniture and rotation
- `playground` - tests doors/windows
- `simple` - tests basic floor plans

The Makefile tracks source dependencies and rebuilds automatically, but `make clean` ensures no stale artifacts remain.

### Manual Testing
- Last successful run: `python -m floor_planner -c ../rzuty/dom_projekt3.yml`
- Test configs in `rzuty/` folder (separate workspace)
- Example configs in `examples/` folder

### Best Practices
1. **Use rooms instead of raw elements** - easier to move and modify
2. **Start from templates** - copy from `examples/templates/rooms/` 
3. **Use variables** - for "what if" scenarios and easier adjustments
4. **Keep rooms in separate YAML files** - better organization and reusability
5. **Version control** - track floor plan changes with Git

## Config File Structure
YAML configs have these main sections:
- `project` - output format (PDF/PNG), DPI, file location
- `default_layout` - area dimensions (real-world meters), scale, grid settings
- `default_options`/`options` - label colors, auto-dimensions, identifier colors
- `vars` - global variables for calculations
- `reusable_elements` - shared wall/door/window definitions (can load from external files)
- Floor plan definitions - rooms with nested elements

### Room Structure
Rooms have:
- `vars` - room-level variables (can be simple values or arithmetic expressions referencing global vars and previously defined room vars)
- Elements positioned relative to room's anchor point

## File Locations
- **Source code**: `/home/krzysztof/work/excercises/floor_planner/floor_planner/`
- **Examples**: `/home/krzysztof/work/excercises/floor_planner/examples/`
- **Actual floor plans**: `/home/krzysztof/work/excercises/rzuty/`
- **Virtual env**: `.venv/` in floor_planner folder

## Feature Development Workflow

### For Complex Multi-Step Features
1. Check `docs/features/` for existing feature design documents
2. Check `/memories/repo/planned-features.md` for planned work
3. If implementing from a feature doc, follow its implementation plan
4. Use session memory to track progress during development
5. Update feature docs with learnings and decisions

### For Simple Features
- Add to `/memories/repo/planned-features.md` with steps
- Implement directly with session memory tracking

## When Helping with Development
- Check element types in `floor_planner/elements/` for available classes
- Reference examples in `examples/templates/rooms/` for patterns
- Respect the anchor point system when positioning elements
- Use variables for dimensions that might change
- Test changes by running against example configs
- See `docs/features/README.md` for detailed feature development workflow

## Adding New Element Types

**CRITICAL: When creating new element classes, you MUST update ALL of these files:**

### Required Steps (All Mandatory):

1. **Create the element class** in appropriate module:
   - Basic elements: `floor_planner/elements/basic.py`
   - Furniture: `floor_planner/elements/furniture/`
   - Landscaping: `floor_planner/elements/landscaping/`
   - Lighting: `floor_planner/elements/lighting.py`
   - etc.

2. **Export from package `__init__.py`**:
   - Add import to `floor_planner/elements/landscaping/__init__.py` (or relevant subpackage)
   - Add class name to `__all__` list
   - Example: `from .water import Fountain, Pond, RectPool, OvalPool`

3. **Export from main elements `__init__.py`**:
   - Add import to `floor_planner/elements/__init__.py`
   - Add class name to `__all__` list

4. **Register in elements registry** (MOST COMMONLY FORGOTTEN):
   - Add import at top of `floor_planner/elements/registry.py`
   - Add entry to `create_elements_registry()` dict with snake_case type name
   - Example: `'rect_pool': RectPool, 'oval_pool': OvalPool`
   - **Without this step, the element type will not be recognized in YAML configs!**
   - **Registry key becomes the source of truth for texture/material naming**

5. **Create textures and materials for 3D export** (MANDATORY for furniture/physical elements):
   - **The registry key (WITH underscores) determines the material folder and file names**
   - Add texture file to the common folder: `textures/<registry_key>.jpg` (or reuse an existing texture)
   - Create directory: `mkdir -p models/procedural/<registry_key>/`
   - Create material file: `models/procedural/<registry_key>/<registry_key>.mtl` with `map_Kd` naming the texture
   
   **Example for registry key `'rect_pool'`:**
   ```bash
   # Add texture (9.2KB placeholder or actual texture); names in textures/ must be unique
   cp path/to/texture.jpg textures/rect_pool.jpg
   
   # Create material directory (matches registry key exactly)
   mkdir -p models/procedural/rect_pool/
   
   # Create MTL file
   cat > models/procedural/rect_pool/rect_pool.mtl << 'EOF'
   # Material for rect_pool
   newmtl rect_pool
   Ka 0.700000 0.700000 0.700000
   Kd 0.800000 0.800000 0.800000
   Ks 0.200000 0.200000 0.200000
   Ns 30.0
   map_Kd rect_pool.jpg
   EOF
   ```
   
   **Naming Rules:**
   - Material directory = `models/procedural/<registry_key>/` (WITH underscores): `'generic_storage'` → `models/procedural/generic_storage/`
   - Material file = `<registry_key>.mtl`: `generic_storage.mtl`
   - MTL newmtl = Registry key: `newmtl generic_storage`
   - MTL map_Kd = name of a texture file in `textures/` (searched next to the `.mtl` first, then in `textures/`): `map_Kd wood/pear_wood.jpg` (textures can be shared between element types)
   
   **Skip textures only for:**
   - Abstract/UI elements: `line`, `polygon`, `circle`, `dimension_arrow`, `text_box`, `room`
   - Elements without physical 3D representation

6. **Update documentation**:
   - Add parameters to relevant guide in `docs/` (e.g., `docs/landscaping-guide.md`)
   - Update or create example YAML files in `examples/`

7. **Run regression tests**:
   - Execute `make check` (and `make all`) to ensure nothing broke
   - New scene projects: add them to `SCENES` in `tests/conftest.py` and generate their golden images
   - Verify new elements render correctly in 2D
   - Test 3D export with `visualisation_dir` to verify textures copy correctly

### Common Mistakes
1. **Registry not updated** (step #4): Element class can be perfectly implemented, but if it's not registered, users will get `KeyError: 'element_type'` when trying to use it in YAML configs.
2. **Textures not created** (step #5): Element works in 2D but fails in 3D export or shows default gray texture. Missing textures cause warnings: "Texture file not found"
3. **Wrong naming convention**: Using class name instead of registry key for folders/files. Registry key is the source of truth!

### Verification Checklist
After adding a new element, verify:
- [ ] Class implements `draw()` method inheriting from `Element`
- [ ] Imported in subpackage `__init__.py`
- [ ] Imported in `floor_planner/elements/__init__.py`
- [ ] **Registered in `registry.py` with correct snake_case type name**
- [ ] **Material file exists: `models/procedural/<registry_key>/<registry_key>.mtl`**
- [ ] **MTL `map_Kd` names a texture that exists in `textures/`**
- [ ] Documented in appropriate guide
- [ ] Example added to relevant demo YAML
- [ ] `make all` runs without errors
- [ ] Element renders correctly in generated 2D images
- [ ] Element exports correctly to 3D (textures copy to `visualisation_dir`)
- [ ] Validation passes: `python scripts/validate_texture_material_structure.py`
