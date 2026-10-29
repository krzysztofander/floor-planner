# Floor Planner

## Overview

This is a drawing tool that produces floor plans. It is controlled through YAML config files and has no built-in GUI (only CLI is provided). Although it may look like a drawback, people with technical background may find it more convenient. Compared with drag-and-drop tools, config-based interface simplifies fine-grained control and allows versioning projects with VCSs like Git.

This is a fork of [renovation](https://github.com/Nikolay-Lysenko/renovation)
by Nikolay Lysenko, with additional features added by Krzysztof Bartczak:
- Arithmetic expressions and variables in configs
- Room variables
- External YAML file support
- Floor plan reports
- Enhanced room options
- Groups and group templates
- Many new element categories (furniture, landscaping, roofs, glass structures, ...)
- 3D export to glTF, including external (pre-made) 3D models

The below figure demonstrates some of available elements.

![elements.png](https://github.com/krzysztofander/floor-planner/blob/master/examples/images/elements.png)

## Motivation
I needed some tool for drawing floor plans and other schematics.
There is plenty of free or paid drawing tools, but non of free was available offline such that I control the tool and the plans I create.
I found out the original module (base for this fork) but it turned out to be insufficient and difficult to use for bigger projects.

## Usage
Create Python virtual environment, download this module and install all requirements.
```bash
pip install -r requirements.txt            # runtime
pip install -r requirements/dev.txt        # runtime + test tools (pytest, pytest-xdist)
```

To generate floor plans, run:
```bash
python -m floor_planner -c /path/to/config.yml
```

To generate images of templates and other examples use make
```bash
make all
```

### Testing
The pytest suite runs every scene project (in a temporary folder) and checks it: the run succeeds, the glTF files are consistent, and each PNG matches its golden image in `tests/golden/2d/`. For the scenes listed in `GOLDEN_3D_SCENES` (`tests/conftest.py`), the 3D output is also compared with a golden summary in `tests/golden/3d/` (materials, textures and geometry per element). Contract tests check rules that all element types must follow.
```bash
pip install -r requirements/dev.txt
make check          # full suite, in parallel (about 10 s)
make check-fast     # contract tests only
python -m pytest -m slow --scene vege          # selected scenes
python -m pytest -m slow -n auto --update-golden   # refresh golden files (2D, and 3D for GOLDEN_3D_SCENES) after an intended change
```
See `docs/features/pytest-regression-suite.md`.

The module uses the config in YAML where properties of each element are set. These properties include location, orientation, size, color and so on.
There are also global properties that control appearance of some embedded elements line dimension lines, labels, room area, etc.

The section named `project` defines properties of output such as:
* Extension (multi-page PDF document, directory with PNG images, or both)
* Location
* DPI (dots-per-inch, resolution)

In the section named `default_layout`, below parameters are set for floor plans that do not override them in their `layout` sections:
* Dimensions of area to be drawn (in real-world meters, i.e., meters prior to scaling)
* Scale
* Grid settings

The sections named `default_options` and  `options` allows to modify options for floor plans
In this section it is possible to configure:
* Color of labels. Labels are not printed if color is not specified.
* Adding automatic dimensions to walls.
* Color of element's identifiers. Identifiers are not printed if their color is not specified.

The section named `vars` can be used to define variables that can be later used in definitions of elements. Variables can be simple numeric values or arithmetic expressions referencing other variables.

The section named `reusable_elements` is designed to store arbitrary collections of elements that can be used by individual floor plans. Demo example uses it to define walls, windows, and doors.
Reusable elements can be loaded from separate YAML files. Please see the `examples`.

Finally, settings of individual floor plans are listed. These settings might include:
* Title
* Layout
* Report
* Names of element collections to reuse
* Extra elements for given floor
* Override of options

## Rooms
This fork adds a concept of rooms as an additional level of hierarchy.
Rooms have their own `vars` section where variables can be defined as simple values or arithmetic expressions referencing global vars or previously defined room vars.
Elements defined within a room are anchored to the room anchor point. This gives flexibility in moving or drawing a whole room as there is no longer need to pre-calculate anchor points of individual elements.
It is recommended to work with rooms instead of individual elements.
*Easiest start is to copy room and main project file from `examples/templates/rooms`*

## Groups
A `group` is a lightweight container: like a room, it has its own `anchor_point` and `vars`, but it does not require walls. Groups can be nested, and a group may contain rooms. Rooms are now implemented as a special case of a group.

Reusable blueprints can be defined in the top-level `group_templates` section and instantiated with `from_template`. An instance can override template `vars`, and its own `elements` are appended to those from the template:
```yaml
- type: group
  from_template: bedroom
  anchor_point: [4, 0]
  vars:
    w: 4   # wider variant
```
See `examples/templates/groups` and the *Groups* section of `docs/element-parameters-reference.md`.

## Element Categories
Elements are grouped in `floor_planner/elements/`:
- **Foundation** - walls, windows, doors (hinged and sliding), rooms, groups, floors, ceilings, generic surfaces, roofs
-- Roofs include gable, hipped (with octants) and single-slope roofs, plus gable end walls. See `examples/roofs`
-- Glass structures include a greenhouse, glass panels, slopes and doors. See `examples/glass_structures`.
- **Symbols** - electricity (outlets, cables, ground cables), info (dimension arrows, text boxes), basic shapes
- **Lighting** - ceiling and wall lamps, LED strips, switches
- **Furniture** - storage, beds, kitchen appliances, bathroom fixtures, tables, chairs, sofas, TV, decorations
- **Devices** - generic tanks
- **Landscaping** - vegetation, hardscape, water features, garden structures, glass structures
- **Composite** - elements built from other elements, e.g. double window-doors or glass doors in an aluminium frame
- **External** - elements rendered in 3D from pre-made models (windows, doors, furniture, trees)


## Landscaping Elements
This fork includes comprehensive landscaping elements for creating site plans and garden designs:

### Vegetation
- **Trees** - with canopy, trunk, species, bloom seasons, and height labels
- **Shrubs** - circular bushes with optional bloom patterns
- **Hedges** - linear hedges with rotation, species, and bloom overlays
- **Lawns**
- **Species database** - default sizes and bloom seasons by species name

### Hardscaping
- **Fences** - multiple styles (solid, picket, chain-link, rail)
- **Garden Paths** - various materials (gravel, stone, paving, wood, mulch)
- **Retaining Walls** - stone course patterns
- **Ground** - base terrain surface

### Water Features
- **Fountains** - tiered, spray, and simple styles
- **Ponds** - multiple shapes (oval, kidney, rectangular, irregular)
- **Pools** - rectangular and oval

### Garden Structures
- **Pergolas** - posts and beam outlines
- **Raised Beds** - for vegetable gardens
- **Gazebos** - octagonal structures
- **Decks** - wooden plank patterns
- **Garden Houses** - sheds with doors and roofs

All landscaping elements support:
- Rotation via `orientation_angle` parameter
- Custom colors and labels
- Integration with floor plans and site layouts

See `examples/landscaping/` for demonstrations of each element type and `docs/landscaping-guide.md` for their parameters.

## 3D Visualization

This fork includes 3D export capabilities to generate glTF 2.0 scenes with textures:

### Features
- **Automatic 3D geometry generation** - 2D floor plan elements are automatically extruded to 3D
- **External models** - selected elements (windows, doors, furniture, trees) use pre-made OBJ or GLB models instead of procedural geometry
- **Animations** - doors can be exported with opening animations
- **Phong material properties** - Ka (ambient), Kd (diffuse), Ks (specular), Ns (shininess) for realistic materials
- **Texture support** - PNG (with alpha channel) and JPG textures with automatic fallback
- **Per-face textures** - Texture, tiling (`scale_relative` / `scale_meters`), lighting and opacity per face of box elements with the `textures` parameter
- **Wall opening detection** - Doors and windows automatically create cutouts in walls for realistic visualization
- **Multi-texture elements** - Different textures for different faces (e.g., door vs door frame)

### Wall Opening Detection
When doors or windows are positioned in walls, the system automatically:
1. Detects spatial overlap using orientation and position checks
2. Generates subdivided wall geometry with rectangular cutouts
3. Preserves proper face normals and winding order
4. Creates realistic openings without manual mesh editing

### Usage
Enable 3D export in your YAML config:
```yaml
project:
  visualisation_dir: "visualisation_3d"  # Output directory for glTF files
```

Elements with `color: invisible` are excluded from 3D export. Set `v_anchor` and `height` on individual elements to control vertical positioning within a floor plan.

Use the floor plan-level `v_anchor` to stack multiple floors vertically in the exported 3D scene:
```yaml
floor_plans:
  - title: parter
    v_anchor: 0.0   # ground floor (default)
    ...
  - title: pietro
    v_anchor: 3.0   # first floor, 3 m up
    ...
```

See `docs/element-parameters-reference.md` — *Floor Plan v_anchor (3D Elevation)* for details.

### Texture and Material System
The 3D export uses a registry-based texture/material system:

**Key Principle:** Element types from the registry determine material folder and file names exactly. Materials (`.mtl`) reference textures by file name; all textures live in one common folder.

**Directory Structure:**
```
models/
├── procedural/        # Materials of procedural elements
│   ├── double_bed/
│   │   └── double_bed.mtl
│   └── generic_storage/
│       └── generic_storage.mtl
└── balcony_door/      # External model with its own model.mtl
textures/              # All texture images, in subfolders (unique file names)
├── plain_named/white-cream-bed.jpg
├── wood/pear_wood.jpg       # shared, e.g. by generic_storage and storage40/60
└── wood/exotic_wood_1.jpg
```

**Material Files (.mtl):**
Each procedural element type has `models/procedural/<element_type>/<element_type>.mtl` defining material properties and its texture:
```mtl
newmtl generic_storage
Ka 0.500000 0.300000 0.200000    # Ambient color
Kd 0.580000 0.380000 0.230000    # Diffuse color
Ks 1.200000 1.200000 1.200000    # Specular color
Ns 250.0                         # Shininess
map_Kd wood/pear_wood.jpg              # Texture reference
```

**Texture lookup:** a `map_Kd` texture is searched in the folder of the `.mtl` file first, then in `textures/`. The same rule applies to procedural elements and external models, so they can share textures.

**Custom Textures:**
Add the image to `textures/` and change `map_Kd` in the element's `.mtl`.

See:
- `docs/NAMING_CONVENTION.md` - Complete naming convention specification
- `docs/texture-material-system.md` - Texture lookup and material rules

### External Models
External models live in `models/<registry_key>/` (`model.glb` or `model.obj` + `model.mtl`, plus `model.transform.json`). Models are looked up in this order:
1. `models/`
2. `models/local/` - private models
3. `models/models_3rd_party/` - third-party models kept outside this repository
4. `models/stubs/` - 1x1x1 m cube placeholders used when the real model is not available

See `models/README.md` for details.

See:
- `examples/3d_visualization/` - Demos of 3D export with textures and wall openings
- `docs/features/wall-opening-detection.md` - Detailed documentation of wall opening feature
- `docs/texture-tiling-guide.md` - Guide to texture tiling (`scale_relative` / `scale_meters`, `texture_scale` for roofs)

## Capabilities
There are no build in limitations. With this module it is possible to draw a complex plans like below.
Use of rooms in separate YAML files and variables helps in offsetting one piece to another and lets to simulate 'what if' in case one wonder if moving or making a wall or door in given place make sense.

![dom.png](https://github.com/krzysztofander/floor-planner/blob/master/examples/images/dom.png)
