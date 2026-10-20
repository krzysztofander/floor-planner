# Floor Planner Documentation

This directory contains documentation for developers and users of the Floor Planner project.

## For Users

- **[Element Parameters Reference](element-parameters-reference.md)** - Parameters of all elements (except landscaping), including [Groups](element-parameters-reference.md#groups), [Group Templates](element-parameters-reference.md#group-templates), [Roofs](element-parameters-reference.md#roofs), external models and glass structures
- **[Landscaping Guide](landscaping-guide.md)** - Vegetation, hardscape, water features and garden structures
- **[Texture Tiling Guide](texture-tiling-guide.md)** - Controlling texture repeat in 3D with `texture_scale`

## For Developers

### 3D Export System
- **[Texture and Material System](texture-material-system.md)** - How textures and materials are resolved for the glTF export
- **[Naming Convention](NAMING_CONVENTION.md)** - Registry-based naming rules for textures and materials
- **[3D Transform Pipeline](3d-transform-pipeline.md)** - How external models are normalized, placed and animated
- **[External Model Library](../models/README.md)** - Layout and metadata of external 3D models

### Feature Development
- **[Feature Development Workflow](features/README.md)** - How to plan and implement new features
- **[Feature Template](features/TEMPLATE.md)** - Copy this to plan complex features

## Quick Start for AI Agents

When working on this project:
1. Review `.github/copilot-instructions.md` for project context
2. Check `docs/features/README.md` for feature development workflow
3. Run `make all` and `make tests` after any source code changes (regression testing)
4. Use feature documents in `docs/features/` for complex implementations

## Documentation Structure

```
docs/
├── README.md                       ← You are here (documentation index)
├── element-parameters-reference.md ← Element parameters
├── landscaping-guide.md            ← Landscaping elements user guide
├── texture-tiling-guide.md         ← texture_scale and UV tiling
├── texture-material-system.md      ← 3D export texture/material architecture
├── NAMING_CONVENTION.md            ← Registry-based naming rules
├── 3d-transform-pipeline.md        ← External model transforms and animation
└── features/                       ← Feature planning and design documents
    ├── README.md                   ← Feature development workflow
    ├── TEMPLATE.md                 ← Template for new features
    └── markdown-report-refactor.md ← Planned: elements report refactor
```
