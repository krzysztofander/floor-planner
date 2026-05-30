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

The below figure demonstrates available elements.

![elements.png](https://github.com/krzysztofander/floor-planner/blob/master/examples/images/elements.png)

## Motivation
I needed some tool for drawing floor plans and other schematics.
There is plenty of free or paid drawing tools, but non of free was available offline such that I control the tool and the plans I create.
I found out the original module (base for this fork) but it turned out to be insufficient and difficult to use for bigger projects.

## Usage
Create Python virtual environment, download this module and install all requirements.

To generate floor plans, run:
```bash
python -m floor_planner -c /path/to/config.yml
```

To generate images of templates and other examples use make
```bash
make all
```

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

## Landscaping Elements
This fork includes comprehensive landscaping elements for creating site plans and garden designs:

### Vegetation
- **Trees** - with canopy, trunk, species, bloom seasons, and height labels
- **Shrubs** - circular bushes with optional bloom patterns
- **Hedges** - linear hedges with rotation, species, and bloom overlays

### Hardscaping
- **Fences** - multiple styles (solid, picket, chain-link, rail)
- **Garden Paths** - various materials (gravel, stone, paving, wood, mulch)
- **Retaining Walls** - stone course patterns

### Water Features
- **Fountains** - tiered, spray, and simple styles
- **Ponds** - multiple shapes (oval, kidney, rectangular, irregular)

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

See `examples/landscaping/` for demonstrations of each element type, and `examples/templates/rooms/backyard_garden/` for a reusable outdoor space template.

## 3D Visualization

This fork includes 3D export capabilities to generate Wavefront OBJ/MTL models with textures:

### Features
- **Automatic 3D geometry generation** - 2D floor plan elements are automatically extruded to 3D
- **Phong material properties** - Ka (ambient), Kd (diffuse), Ks (specular), Ns (shininess) for realistic materials
- **Texture support** - PNG (with alpha channel) and JPG textures with automatic fallback
- **Texture tiling** - Control texture repeat with `texture_scale` parameter
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
  visualisation_dir: "visualisation_3d"  # Output directory for OBJ/MTL files
```

Elements with `color: invisible` are excluded from 3D export. Set `v_anchor` and `height` to control vertical positioning.

### Texture and Material System
The 3D export uses a registry-based texture/material system:

**Key Principle:** Element types from the registry determine folder and file names exactly.

**Directory Structure:**
```
textures/
├── fallback/          # System default textures
│   ├── double_bed/
│   │   ├── double_bed.jpg
│   │   └── double_bed.mtl
│   ├── generic_storage/
│   │   ├── generic_storage.jpg
│   │   └── generic_storage.mtl
│   └── door/
│       ├── door.jpg
│       ├── door_frame.jpg      # Supplemental texture
│       └── door.mtl
└── defaults/          # User custom textures (optional overrides)
    └── ...
```

**Naming Convention:**
- Registry key (WITH underscores) = folder name = base texture name
- Example: `'generic_storage'` → `generic_storage/` → `generic_storage.jpg`
- Multi-texture elements use: `<element_type>_<descriptor>.jpg` (e.g., `door_frame.jpg`)

**Material Files (.mtl):**
Each texture has a corresponding `.mtl` file defining material properties:
```mtl
newmtl generic_storage
Ka 0.500000 0.300000 0.200000    # Ambient color
Kd 0.580000 0.380000 0.230000    # Diffuse color
Ks 1.200000 1.200000 1.200000    # Specular color
Ns 250.0                         # Shininess
map_Kd generic_storage.jpg       # Texture reference
```

**Custom Textures:**
Place custom textures in `textures/defaults/<element_type>/` to override system defaults.

See:
- `docs/NAMING_CONVENTION.md` - Complete naming convention specification
- `scripts/validate_texture_material_structure.py` - Validation tool

See:
- `examples/3d_visualization/` - Demos of 3D export with textures and wall openings
- `docs/features/wall-opening-detection.md` - Detailed documentation of wall opening feature
- `docs/texture-tiling-guide.md` - Guide to texture tiling and `texture_scale` parameter

## Capabilities
There are no build in limitations. With this module it is possible to draw a complex plans like below.
Use of rooms in separate YAML files and variables helps in offsetting one piece to another and lets to simulate 'what if' in case one wonder if moving or making a wall or door in given place make sense.

![dom.png](https://github.com/krzysztofander/floor-planner/blob/master/examples/images/dom.png)
