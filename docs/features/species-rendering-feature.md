# Species and Bloom Rendering Feature

**Implemented**: May 25, 2026  
**Status**: Complete

## Overview
Added the ability to render species names and bloom seasons directly on vegetation elements (Tree, Shrub, Hedge), plus enhanced markdown reports with detailed plant information.

## Features Implemented

### 1. Enhanced Markdown Reports
- Added dedicated sections for Trees, Shrubs, and Hedges with detailed tables
- Each vegetation element now reports:
  - Species name
  - Height (meters)
  - Bloom season (dd.mm - dd.mm format)
  - Bloom color (hex code)
- Reports use `-` for missing/optional values

**Example output**:
```markdown
## Trees

Total count: 3

| ID | Species | Height (m) | Bloom Season | Bloom Color |
|---|---|---|---|---|
| Oak Tree_1 | oak | 8.00 | - | - |
| Cherry Blossom_1 | cherry | 6.00 | 15.04 - 30.04 | #FFB6C1 |
```

### 2. Species Rendering Configuration
Added `show_species` option in floor plan configuration:

```yaml
default_options:
  Tree:
    show_species: true
  Shrub:
    show_species: true
  Hedge:
    show_species: true
```

When enabled, species names render in the center of each plant element.

### 3. Center-Positioned Species Text
**For circular plants (Tree, Shrub)**:
- Species text always renders horizontally (rotation = 0°)
- Positioned at the element's anchor point (center)

**For hedges**:
- Species text follows the hedge rotation angle
- Positioned at geometric center with perpendicular offset when bloom present
- Maintains readability at all angles

### 4. Bloom Season Display
When `bloom_season_start` or `bloom_season_end` is specified:
- Bloom season renders below the species text
- Uses dark red color for text
- Format: "dd.mm-dd.mm" (e.g., "15.04-30.04")
- Vertical offset from species: 0.15m for trees, 0.1m for shrubs

**For hedges**:
- Bloom text positioned perpendicular to species text
- Follows hedge rotation like species

## Code Changes

### Modified Files
1. **floor_planner/elements/options.py**
   - Added `get_show_species()` function

2. **floor_planner/markdown_report.py**
   - Added dedicated vegetation sections with detailed tables
   - Extracted Tree, Shrub, Hedge from "Other Elements"

3. **floor_planner/elements/landscaping/vegetation.py**
   - Added `_render_species_and_bloom()` method to Tree, Shrub, Hedge classes
   - Imported `_render_text` and `get_show_species`
   - Added species/bloom rendering in each `draw()` method

4. **examples/landscaping/vegetation_demo.yml**
   - Enabled show_species for all three element types in default_options

5. **docs/features/landscaping-elements.md**
   - Updated implementation notes with species rendering details

## Usage Example

```yaml
# Enable species rendering
default_options:
  Tree:
    show_species: true
  Shrub:
    show_species: true
  Hedge:
    show_species: true

floor_plans:
  - title:
      text: 'Garden Plan'
    elements:
      - type: tree
        anchor: [5.0, 5.0]
        diameter: 3.0
        height: 6.0
        species: 'cherry'
        bloom_season_start: '15.04'
        bloom_season_end: '30.04'
        bloom_color: '#FFB6C1'
        
      - type: hedge
        anchor: [1.0, 1.0]
        length: 5.0
        thickness: 0.5
        height: 1.5
        orientation_angle: 45  # species text will also rotate 45°
        species: 'ligustrum'
```

## Visual Behavior

### Tree Species Rendering
- Species at center, horizontal
- Bloom season below (if specified), in dark red
- Both texts centered on anchor point
- Vertical spacing: ±0.2m

### Shrub Species Rendering
- Species at center, horizontal
- Bloom season below (if specified), in dark red
- Both texts centered on anchor point
- Vertical spacing: ±0.15m

### Hedge Species Rendering
- Species at center, follows hedge rotation
- Bloom season perpendicular to species (along hedge axis)
- Offset 0.15m perpendicular when bloom present
- Maintains rotation for readability

## Testing
- ✅ Regression test passed: `make all`
- ✅ Markdown reports show all vegetation details
- ✅ Species render correctly in center of elements
- ✅ Circular elements keep text horizontal
- ✅ Hedges rotate text with element
- ✅ Bloom seasons display below species
- ✅ Option can be toggled per element type

## Future Enhancements
- Add text background for better visibility on complex backgrounds
- Support for scientific names vs. common names
- Multi-language support for species names
