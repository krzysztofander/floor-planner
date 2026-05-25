# Feature: Landscaping Elements

**Status:** Planning  
**Priority:** High  
**Estimated Effort:** 3-5 Days

## Overview
Add landscaping elements to allow creating site plans and garden designs, including vegetation (trees, shrubs, hedges), hardscaping (fences, walls, paths), and water features (ponds, fountains).

## Motivation
Currently the floor planner focuses on interior floor plans. Users want to:
- Design complete site plans showing building placement on plots
- Plan gardens and landscaping around buildings
- Visualize outdoor spaces with vegetation, fences, paths, and water features
- Create presentation-quality property layouts
- Track dimensions for landscaping contractors

Real-world use cases:
- Home garden planning
- Site plans for building permits
- Landscape architect presentations
- Property development layouts
- Outdoor living space design

## Design

### User-Facing Changes

Users will be able to add landscaping elements with natural YAML syntax:

```yaml
# Vegetation
- type: Tree
  anchor: [5.0, 3.0]
  diameter: 4.0  # canopy diameter
  height: 8.0  # tree height in meters
  trunk_diameter: 0.5
  species: 'oak'  # optional
  color: '#228B22'  # forest green
  label: 'Oak Tree'  # optional
  bloom_season_start: '15.04'  # optional, dd.mm format
  bloom_season_end: '30.05'  # optional, dd.mm format
  bloom_color: '#FFB6C1'  # optional, light pink

- type: Shrub
  anchor: [2.0, 1.0]
  diameter: 1.5
  height: 1.2  # shrub height in meters
  color: '#90EE90'  # light green
  species: 'krzewuszka'  # optional
  label: 'Rose Bush'  # optional
  bloom_season_start: '01.06'  # optional, dd.mm format
  bloom_season_end: '30.09'  # optional, dd.mm format
  bloom_color: '#FF69B4'  # optional, hot pink

- type: Hedge
  anchor: [0, 0]
  length: 10.0
  thickness: 0.6
  height: 1.5
  species: 'ligustr'  # optional
  color: '#556B2F'  # dark olive green
  label: 'Privacy Hedge'  # optional
  bloom_season_start: '01.05'  # optional, dd.mm format
  bloom_season_end: '15.06'  # optional, dd.mm format
  bloom_color: '#FFFFFF'  # optional, white flowers

# Hardscaping
- type: Fence
  anchor: [0, 0]
  length: 15.0
  style: 'picket'  # picket, chain-link, solid, rail
  height: 1.8  # for label
  color: '#8B4513'  # saddle brown
  pattern: 'vertical_boards'  # optional texture

- type: GardenPath
  anchor: [2, 2]
  length: 8.0
  width: 1.2
  material: 'gravel'  # gravel, stone, paving, wood
  color: '#D3D3D3'  # light gray
  pattern: 'gravel'  # optional texture

# Water Features
- type: Fountain
  anchor: [15, 15]
  diameter: 1.5
  color: '#87CEEB'  # sky blue

# Garden Structures
- type: Pergola
  anchor: [12, 5]
  length: 4.0
  width: 3.0
  orientation_angle: 45
  post_size: 0.2
  color: '#8B4513'

- type: RaisedBed
  anchor: [20, 10]
  length: 3.0
  width: 1.2
  height: 0.4  # for label
  color: '#654321'
  border_color: '#8B4513'
```

### Technical Changes

#### New Files to Create
1. **`floor_planner/elements/landscaping/`** - new package
   - `__init__.py` - exports all landscaping elements
   - `vegetation.py` - Tree, Shrub, Hedge classes
   - `hardscape.py` - Fence, GardenPath, RetainingWall classes
   - `water.py` - Pond, Fountain classes
   - `structures.py` - Pergola, RaisedBed, Gazebo classes

2. **`examples/landscaping/`** - demonstration configs
   - `vegetation_demo.yml`
   - `complete_site_plan.yml`
   - `garden_design.yml`

#### Modifications to Existing Files
1. **`floor_planner/elements/__init__.py`**
   - Import and expose landscaping elements

2. **`floor_planner/elements/registry.py`**
   - Register all new element types

3. **`examples/templates/`**
   - Add landscaping templates

### Implementation Details

#### Base Classes
Most elements will extend `RectangularElement` or create custom shapes:

```python
# vegetation.py
class Tree(Element):
    """Circular canopy tree representation"""
    def __init__(self, anchor_point, diameter, height, trunk_diameter, color,
                 label=None, species=None, bloom_season_start=None, 
                 bloom_season_end=None, bloom_color=None):
        # Two circles: trunk (small) + canopy (large)
        # Height used for label/info display
        # Bloom season rendering if dates provided

class Shrub(Element):
    """Single shrub element"""
    def __init__(self, anchor_point, diameter, height, color,
                 label=None, species=None, bloom_season_start=None,
                 bloom_season_end=None, bloom_color=None):
        # Single circle representing shrub canopy
        # Height for label/info display
        # Bloom rendering if season provided
        
class Hedge(RectangularElement):
    """Linear hedge element"""
    def __init__(self, anchor_point, length, thickness, height, color,
                 label=None, species=None, bloom_season_start=None,
                 bloom_season_end=None, bloom_color=None):
        # Similar to Wall but with vegetation styling
        # Bloom rendering for flowering hedges

# hardscape.py  
class Fence(RectangularElement):
    """Fence with optional patterns"""
    # Line with optional pattern rendering
    
class GardenPath(RectangularElement):
    """Textured path element"""
    # Rectangle with material patterns
```

#### Rendering Strategy
- **Trees**: Two concentric circles (trunk + canopy), optional leaf texture, height shown in label, bloom color overlay if in season
- **Shrubs**: Single circle, height shown in label, bloom color overlay if in season
- **Hedges**: Thick line with green fill, optional texture pattern, height in label, bloom color overlay if in season
- **Fences**: Line with vertical/horizontal pattern based on style, height in label
- **Paths**: Rectangle with material texture (dots for gravel, grid for paving)
- **Ponds**: Irregular polygon or ellipse with wavy border
- **Structures**: Outline/wireframe rendering showing posts and beams

#### Bloom Season Rendering
Vegetation elements with bloom_season_start and bloom_season_end will:
- Display bloom_color as an overlay or halo during bloom period
- Show bloom dates in label/info if displayed
- Use dd.mm format for date ranges (e.g., "15.04-30.05")

## Implementation Plan

### Phase 1: Vegetation Foundation ✅ COMPLETE (May 25, 2024)
- ✅ Create `floor_planner/elements/landscaping/` package structure
- ✅ Implement `Tree` class with diameter, height, trunk_diameter, bloom attributes
- ✅ Implement `Shrub` class with diameter, height, bloom attributes
- ✅ Implement `Hedge` class with length, thickness, height, bloom attributes
- ✅ Add bloom season rendering logic (color overlay for trees/hedges, flower circles for shrubs)
- ✅ Register vegetation elements in registry
- ✅ Create example config: `examples/landscaping/vegetation_demo.yml`
- ✅ Add Makefile target: `make landscaping`
- ✅ Verify with full regression test: `make all`

**Implementation Notes**:
- Registry keys must be lowercase ('tree', 'shrub', 'hedge')
- Project config requires `dpi`, `pdf_file`, and `png_dir` keys
- `render_label_and_id()` signature: `(ax, element, element_type, position, rotation, ...)`
- Bloom overlays: dashed halos for trees/hedges, small circles for shrubs
- All elements support species, height, and optional bloom seasons (dd.mm format)
- **Species rendering**: Enable with `show_species: true` in element options (Tree/Shrub/Hedge)
  - Species text renders in center of element
  - Circular elements (Tree, Shrub): always horizontal text
  - Hedges: text follows hedge rotation
  - Bloom season renders below species when specified
  - Bloom text color matches bloom_color attribute
- **Markdown reports**: Include species, height, bloom season, and bloom color for all vegetation elements
- [✅] Create `examples/landscaping/vegetation_demo.yml` with bloom examples
- [✅] Run `make all` to test

### Phase 2: Hardscaping ✅ COMPLETE (May 25, 2024)
- ✅ Implement `Fence` class with style variations
- ✅ Implement `GardenPath` class with material patterns
- ✅ Implement `RetainingWall` class
- ✅ Add pattern rendering for different materials
- ✅ Create `examples/landscaping/hardscape_demo.yml`
- ✅ Run `make all` to test

**Implementation Notes**:
- Created `floor_planner/elements/landscaping/hardscape.py` with three classes
- **Fence styles**: 'solid', 'picket', 'chain-link', 'rail'
  - Picket: vertical lines every 15cm
  - Chain-link: diagonal cross-hatch pattern
  - Rail: 3 horizontal rails at 0.25, 0.5, 0.75 positions
- **GardenPath materials**: 'gravel', 'stone', 'paving', 'wood', 'mulch'
  - Gravel: random dots for texture (seed 42 for consistency)
  - Stone: irregular polygons for flagstones
  - Paving: regular grid pattern
  - Wood: parallel lines for planks (perpendicular to path)
  - Mulch: random short lines for organic texture (seed 43)
- **RetainingWall**: horizontal courses + vertical mortar lines for stone texture
- All elements extend `RectangularElement` and support rotation via `orientation_angle`
- Registry keys: 'fence', 'garden_path', 'retaining_wall' (lowercase, underscores)
- Added to `Makefile` with separate target for hardscape demo
- Full regression test passes: `make all`

### Phase 3: Water Features (2-3 hours)
- [ ] Implement `Pond` class with shape variations
- [ ] Implement `Fountain` class
- [ ] Add water texture/pattern rendering
- [ ] Create `examples/landscaping/water_features_demo.yml`
- [ ] Run `make all` to test

### Phase 4: Garden Structures (3-4 hours)
- [ ] Implement `Pergola` class (posts + beams outline)
- [ ] Implement `RaisedBed` class
- [ ] Optional: `Gazebo`, `Deck` classes
- [ ] Create `examples/landscaping/structures_demo.yml`
- [ ] Run `make all` to test

### Phase 5: Integration & Documentation (2-3 hours)
- [ ] Create comprehensive site plan example
- [ ] Create room template for outdoor spaces
- [ ] Update Makefile to include landscaping examples
- [ ] Add landscaping section to README.md
- [ ] Document all element parameters
- [ ] Add color palette suggestions for natural elements
- [ ] Create landscaping best practices guide

### Phase 6: Advanced Features (Optional, 4-6 hours)
- [ ] Plant symbols library (top-down botanical symbols)
- [ ] Path curves and corners
- [ ] Irregular pond shapes with bezier curves
- [ ] Seasonal color variations
- [ ] Shadow/sun direction indicators
- [ ] Scale-appropriate detail (hide texture at small scales)

## Testing Strategy

### Unit Tests (if framework exists)
- Tree rendering at various sizes and heights
- Tree and shrub bloom season rendering with date ranges
- Shrub rendering with height labels
- Hedge bloom color overlays
- Fence patterns render correctly
- Pond shape variations
- Element rotation for all types
- Bloom date parsing (dd.mm format validation)

### Integration Tests

Create demonstration configs:

1. **`vegetation_demo.yml`** - All vegetation types with labels, heights, and bloom season examples
2. **`hardscape_demo.yml`** - Fences, paths, walls in various styles
3. **`water_features_demo.yml`** - Ponds and fountains
4. **`complete_site_plan.yml`** - Full property with:
   - Building outline (existing functionality)
   - Trees around perimeter
   - Garden beds with hedges
   - Patio with furniture
   - Driveway and paths
   - Fence boundary
   - Small pond feature

### Manual Testing
- Render at different scales (1:50, 1:100, 1:200)
- Test with both PDF and PNG output
- Verify elements work within Room containers
- Test rotation of all landscaping elements
- Verify label positioning for circular elements
- Check dimension lines work with landscaping

### Add to Makefile
```makefile
LANDSCAPING_PNG = examples/landscaping/Complete\ Site\ Plan.png
landscaping: $(LANDSCAPING_PNG)

$(LANDSCAPING_PNG): examples/landscaping/complete_site_plan.yml $(PYSRC)
	@echo "Processing $<"
	$(PYTHON) -m floor_planner -c $<
```

Update `all` target: `all: room_templates elements furniture playground simple landscaping`

## Open Questions

### Design Decisions
- **Should trees have perspective (top-down vs 3D)?** → Start with top-down circles
- **How detailed should plant symbols be?** → Simple geometric shapes first, optional botanical symbols later
- **Support curved paths?** → Phase 6, start with straight segments
- **Layer ordering (trees over paths vs paths over trees)?** → Follow element order in config (painter's algorithm)
- **Bloom season rendering?** → Show bloom_color as overlay/halo, include dates in labels (dd.mm format)

### Technical Considerations
- **Performance with many trees?** → Monitor, optimize if needed
- **Pattern rendering approach?** → Reuse wall pattern system if implemented
- **Color palette presets?** → Add suggested colors in documentation
- **Integration with existing furniture?** → Outdoor furniture already exists, works as-is

### User Experience
- **Template library for common gardens?** → Create 3-4 templates (formal, cottage, modern, vegetable)
- **Symbol library vs custom each time?** → Both - provide templates but allow full customization
- **Dimension rules for landscape?** → Follow same rules as walls, make optional

## Success Criteria
- [ ] Users can create basic site plans with building + landscaping
- [ ] At least 8 landscaping element types work reliably
- [ ] Examples render correctly in PDF and PNG
- [ ] Documentation covers all element parameters
- [ ] `make all` passes with landscaping examples included
- [ ] Elements work within rooms for modular outdoor spaces

## References
- Landscape architecture symbols: [CAD symbols reference]
- Similar tools: SketchUp, SmartDraw landscape features
- Existing codebase: `floor_planner/elements/furniture/` for patterns
- User request: From rzuty/ workspace - site plan examples needed

## Future Enhancements (Beyond This Feature)
- Topography lines for sloped properties
- Sun path and shadow analysis
- Plant growth simulation (show mature sizes vs young plants)
- Advanced seasonal palettes (spring foliage, fall colors, winter bare branches) - basic bloom season already implemented
- Irrigation system elements
- Lighting plan elements (outdoor lights)
- Property line and setback visualization
