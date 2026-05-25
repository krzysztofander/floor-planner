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
- Constants and arithmetic expressions in configs
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
make all
```

This builds all example floor plans and serves as regression testing:
- `room_templates` - tests room-based designs
- `elements` - tests individual element rendering
- `furniture` - tests furniture and rotation
- `playground` - tests doors/windows
- `simple` - tests basic floor plans

The Makefile tracks source dependencies and rebuilds automatically.

### Manual Testing
- Last successful run: `python -m floor_planner -c ../rzuty/dom_projekt3.yml`
- Test configs in `rzuty/` folder (separate workspace)
- Example configs in `examples/` folder

### Best Practices
1. **Use rooms instead of raw elements** - easier to move and modify
2. **Start from templates** - copy from `examples/templates/rooms/` 
3. **Use constants and variables** - for "what if" scenarios and easier adjustments
4. **Keep rooms in separate YAML files** - better organization and reusability
5. **Version control** - track floor plan changes with Git

## Config File Structure
YAML configs have these main sections:
- `project` - output format (PDF/PNG), DPI, file location
- `default_layout` - area dimensions (real-world meters), scale, grid settings
- `default_options`/`options` - label colors, auto-dimensions, identifier colors
- `constants` - global variables for calculations
- `reusable_elements` - shared wall/door/window definitions (can load from external files)
- Floor plan definitions - rooms with nested elements

### Room Structure
Rooms have:
- `constants` - room-level constants
- `variables` - computed values using arithmetic expressions
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
- Use constants/variables for dimensions that might change
- Test changes by running against example configs
- See `docs/features/README.md` for detailed feature development workflow
