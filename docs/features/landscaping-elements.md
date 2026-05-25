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
  canopy_diameter: 4.0
  trunk_diameter: 0.5
  species: 'oak'  # optional, for label
  color: '#228B22'  # forest green
  label: 'Oak Tree'

- type: Shrub
  anchor: [2.0, 1.0]
  diameter: 1.5
  color: '#90EE90'  # light green
  count: 3  # optional, for grouped shrubs
  spacing: 0.5  # distance between if count > 1

- type: Hedge
  anchor: [0, 0]
  length: 10.0
  thickness: 0.6
  height: 1.5  # for info/label
  color: '#556B2F'  # dark olive green

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

- type: RetainingWall
  anchor: [10, 0]
  length: 6.0
  height: 0.8
  thickness: 0.3
  material: 'stone'
  color: '#808080'

# Water Features
- type: Pond
  anchor: [8, 8]
  shape: 'irregular'  # circle, oval, irregular, kidney
  width: 3.0
  length: 4.0  # for oval/irregular
  color: '#4682B4'  # steel blue
  border_width: 0.3  # optional shore/border

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
    def __init__(self, anchor_point, canopy_diameter, trunk_diameter, color, ...):
        # Two circles: trunk (small) + canopy (large)
        
class Hedge(RectangularElement):
    """Linear hedge element"""
    # Similar to Wall but with vegetation styling

# hardscape.py  
class Fence(RectangularElement):
    """Fence with optional patterns"""
    # Line with optional pattern rendering
    
class GardenPath(RectangularElement):
    """Textured path element"""
    # Rectangle with material patterns
```

#### Rendering Strategy
- **Trees**: Two concentric circles (trunk + canopy), optional leaf texture
- **Shrubs**: Single circle or cluster of circles
- **Hedges**: Thick line with green fill, optional texture pattern
- **Fences**: Line with vertical/horizontal pattern based on style
- **Paths**: Rectangle with material texture (dots for gravel, grid for paving)
- **Ponds**: Irregular polygon or ellipse with wavy border
- **Structures**: Outline/wireframe rendering showing posts and beams

## Implementation Plan

### Phase 1: Vegetation Foundation (4-6 hours)
- [ ] Create `floor_planner/elements/landscaping/` package structure
- [ ] Implement `Tree` class (circular canopy + trunk)
- [ ] Implement `Shrub` class (single or grouped)
- [ ] Implement `Hedge` class (extends RectangularElement)
- [ ] Register vegetation elements in registry
- [ ] Create `examples/landscaping/vegetation_demo.yml`
- [ ] Run `make all` to test

### Phase 2: Hardscaping (3-4 hours)
- [ ] Implement `Fence` class with style variations
- [ ] Implement `GardenPath` class with material patterns
- [ ] Implement `RetainingWall` class
- [ ] Add pattern rendering for different materials
- [ ] Create `examples/landscaping/hardscape_demo.yml`
- [ ] Run `make all` to test

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
- Tree rendering at various sizes
- Grouped shrubs with different spacing
- Fence patterns render correctly
- Pond shape variations
- Element rotation for all types

### Integration Tests

Create demonstration configs:

1. **`vegetation_demo.yml`** - All vegetation types with labels
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
- Plant growth simulation (show mature sizes)
- Seasonal palettes (spring, summer, fall, winter)
- Irrigation system elements
- Lighting plan elements (outdoor lights)
- Property line and setback visualization
