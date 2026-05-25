# Landscaping Elements Documentation

## Element Parameters Reference

### Vegetation

#### Tree
- `anchor`: tuple[float, float] - Center point of canopy
- `diameter`: float - Canopy diameter in meters
- `height`: float - Tree height in meters (for label)
- `trunk_diameter`: float - Trunk diameter in meters
- `color`: str - Canopy color (hex or color name)
- `species`: str | None - Species name (optional)
- `bloom_season_start`: str | None - Bloom start date in dd.mm format (optional)
- `bloom_season_end`: str | None - Bloom end date in dd.mm format (optional)
- `bloom_color`: str | None - Bloom color (hex or color name, optional)
- `label`: str | None - Custom label (optional)

#### Shrub
- `anchor`: tuple[float, float] - Center point of shrub
- `diameter`: float - Shrub diameter in meters
- `height`: float - Shrub height in meters (for label)
- `color`: str - Shrub color (hex or color name)
- `species`: str | None - Species name (optional)
- `bloom_season_start`: str | None - Bloom start date in dd.mm format (optional)
- `bloom_season_end`: str | None - Bloom end date in dd.mm format (optional)
- `bloom_color`: str | None - Bloom color (hex or color name, optional)
- `label`: str | None - Custom label (optional)

#### Hedge
- `anchor`: tuple[float, float] - Bottom-left corner point
- `length`: float - Hedge length in meters
- `thickness`: float - Hedge thickness in meters
- `height`: float - Hedge height in meters (for label)
- `orientation_angle`: float - Rotation angle in degrees (default: 0)
- `color`: str - Hedge color (default: '#556B2F')
- `species`: str | None - Species name (optional)
- `bloom_season_start`: str | None - Bloom start date in dd.mm format (optional)
- `bloom_season_end`: str | None - Bloom end date in dd.mm format (optional)
- `bloom_color`: str | None - Bloom color (hex or color name, optional)
- `label`: str | None - Custom label (optional)

#### Lawn
- `anchor`: tuple[float, float] - Bottom-left corner point
- `length`: float - Lawn length in meters
- `width`: float - Lawn width in meters
- `color`: str - Grass color (default: '#7CFC00' - bright green)
- `orientation_angle`: float - Rotation angle in degrees (default: 0)
- `label`: str | None - Custom label (optional)

### Hardscaping

#### Fence
- `anchor`: tuple[float, float] - Start point (bottom-left)
- `length`: float - Fence length in meters
- `style`: str - Fence style: 'solid', 'picket', 'chain-link', 'rail'
- `height`: float - Fence height in meters
- `thickness`: float - Fence thickness in meters
- `orientation_angle`: float - Rotation angle in degrees (default: 0)
- `color`: str - Fence color (hex or color name)
- `label`: str | None - Custom label (optional)

#### GardenPath
- `anchor`: tuple[float, float] - Start point (bottom-left)
- `length`: float - Path length in meters
- `width`: float - Path width in meters
- `material`: str - Path material: 'gravel', 'stone', 'paving', 'wood', 'mulch'
- `orientation_angle`: float - Rotation angle in degrees (default: 0)
- `color`: str - Path color (hex or color name)
- `label`: str | None - Custom label (optional)

#### RetainingWall
- `anchor`: tuple[float, float] - Start point (bottom-left)
- `length`: float - Wall length in meters
- `height`: float - Wall height in meters
- `thickness`: float - Wall thickness in meters
- `orientation_angle`: float - Rotation angle in degrees (default: 0)
- `color`: str - Wall color (default: '#696969')
- `label`: str | None - Custom label (optional)

### Water Features

#### Fountain
- `anchor`: tuple[float, float] - Center point of fountain
- `diameter`: float - Basin diameter in meters
- `height`: float - Fountain height in meters
- `style`: str - Fountain style: 'tiered', 'spray', 'simple'
- `color`: str - Water color (default: '#87CEEB')
- `basin_color`: str - Basin color (default: '#708090')
- `label`: str | None - Custom label (optional)

#### Pond
- `anchor`: tuple[float, float] - Center point of pond
- `length`: float - Pond length in meters
- `width`: float - Pond width in meters
- `shape`: str - Pond shape: 'oval', 'kidney', 'rectangular', 'irregular'
- `color`: str - Water color (default: '#4682B4')
- `border_color`: str - Border/edge color (default: '#2F4F4F')
- `label`: str | None - Custom label (optional)

#### RectPool
- `anchor`: tuple[float, float] - Center point of pool
- `width`: float - Pool width in meters
- `height`: float - Pool length in meters
- `pool_color`: str - Pool water color (default: '#00BFFF' - bright blue)
- `border_color`: str - Pool edge/border color (default: '#B0C4DE' - light steel blue)
- `show_lanes`: bool - Whether to show lane lines (default: True)
- `show_steps`: bool - Whether to show entry steps (default: True)
- `label`: str | None - Custom label (optional)

#### OvalPool
- `anchor`: tuple[float, float] - Center point of pool
- `width`: float - Pool width in meters
- `height`: float - Pool length in meters
- `pool_color`: str - Pool water color (default: '#00BFFF' - bright blue)
- `border_color`: str - Pool edge/border color (default: '#B0C4DE' - light steel blue)
- `show_steps`: bool - Whether to show entry steps (default: True)
- `label`: str | None - Custom label (optional)

### Garden Structures

#### Pergola
- `anchor`: tuple[float, float] - Bottom-left corner
- `length`: float - Pergola length in meters
- `width`: float - Pergola width in meters
- `post_size`: float - Post dimension in meters (default: 0.2)
- `orientation_angle`: float - Rotation angle in degrees (default: 0)
- `color`: str - Structure color (default: '#8B4513')
- `label`: str | None - Custom label (optional)

#### RaisedBed
- `anchor`: tuple[float, float] - Bottom-left corner
- `length`: float - Bed length in meters
- `width`: float - Bed width in meters
- `height`: float - Bed height in meters
- `border_thickness`: float - Border thickness in meters (default: 0.15)
- `orientation_angle`: float - Rotation angle in degrees (default: 0)
- `fill_color`: str - Soil color (default: '#8B4513')
- `border_color`: str - Border color (default: '#654321')
- `label`: str | None - Custom label (optional)

#### Gazebo
- `anchor`: tuple[float, float] - Center point
- `diameter`: float - Gazebo diameter in meters
- `color`: str - Floor color (default: '#DEB887')
- `roof_color`: str - Roof color (default: '#8B4513')
- `label`: str | None - Custom label (optional)

#### Deck
- `anchor`: tuple[float, float] - Bottom-left corner
- `length`: float - Deck length in meters
- `width`: float - Deck width in meters
- `orientation_angle`: float - Rotation angle in degrees (default: 0)
- `color`: str - Deck color (default: '#D2B48C')
- `label`: str | None - Custom label (optional)

#### GardenHouse
- `anchor`: tuple[float, float] - Bottom-left corner
- `length`: float - House length in meters
- `width`: float - House width in meters
- `height`: float - House height in meters
- `orientation_angle`: float - Rotation angle in degrees (default: 0)
- `color`: str - Wall color (default: '#DEB887')
- `roof_color`: str - Roof color (default: '#8B4513')
- `label`: str | None - Custom label (optional)

## Color Palette Suggestions

### Natural Green Tones (Vegetation)
- `#228B22` - Forest Green (mature trees)
- `#32CD32` - Lime Green (spring foliage)
- `#3CB371` - Medium Sea Green (healthy trees)
- `#90EE90` - Light Green (young trees, shrubs)
- `#98D8C8` - Pale Turquoise (decorative shrubs)
- `#556B2F` - Dark Olive Green (hedges)

### Earth Tones (Structures & Hardscaping)
- `#8B4513` - Saddle Brown (wood structures)
- `#D2B48C` - Tan (decks, light wood)
- `#DEB887` - Burlywood (natural wood)
- `#654321` - Dark Brown (borders, aged wood)
- `#696969` - Dim Gray (stone, concrete)
- `#A9A9A9` - Dark Gray (gravel paths)
- `#B0B0B0` - Light Gray (paving)

### Water Colors
- `#4682B4` - Steel Blue (pond water)
- `#87CEEB` - Sky Blue (fountain water)
- `#2F4F4F` - Dark Slate Gray (water edges)
- `#708090` - Slate Gray (fountain basins)

### Bloom Colors
- `#FFB6C1` - Light Pink (cherry blossoms)
- `#FF69B4` - Hot Pink (roses)
- `#E6E6FA` - Lavender (lavender flowers)
- `#ADD8E6` - Light Blue (hydrangea)
- `#FF1493` - Deep Pink (azalea)
- `#FFD700` - Gold (yellow flowers)

### Fencing
- `#FFFFFF` - White (picket fences)
- `#8B4513` - Brown (natural wood fences)
- `#708090` - Slate Gray (chain-link)

## Landscaping Best Practices

### Planning & Layout

1. **Start with Perimeter Elements**
   - Define property boundaries first
   - Add fences, hedges, or retaining walls along edges
   - This provides context for interior elements

2. **Work from Large to Small**
   - Place large trees first
   - Add structures (sheds, gazebos, pergolas)
   - Then add paths and beds
   - Finish with shrubs and decorative elements

3. **Use Consistent Scale**
   - Keep scale_denominator consistent across site plans
   - Typical scales: 1:50 for detailed gardens, 1:100 for larger sites
   - Use grid settings for alignment: `grid_major_step: 5`, `grid_minor_step: 1`

### Design Principles

4. **Balance and Symmetry**
   - Create visual balance with paired elements (trees, shrubs)
   - Use symmetry for formal designs
   - Use asymmetry for natural, informal looks

5. **Layering**
   - Back layer: tall trees and hedges (2-12m)
   - Middle layer: shrubs and small trees (1-3m)
   - Front layer: low beds, paths, groundcover

6. **Focal Points**
   - Use gazebos, ponds, or specimen trees as focal points
   - Add paths leading to focal areas
   - Use bloom colors to draw attention seasonally

### Technical Tips

7. **Rotation for Natural Placement**
   - Use `orientation_angle` to vary fence and path directions
   - Rotate structures to avoid grid-like appearance
   - Typical angles: 0, 45, 90, 135 degrees

8. **Bloom Seasons**
   - Use `bloom_season_start` and `bloom_season_end` for temporal planning
   - Format: 'dd.mm' (e.g., '15.04' for April 15)
   - Plan for continuous blooms: early spring → summer → fall

9. **Species Labels**
   - Enable with `show_species: true` in options
   - Helps with plant selection and contractor communication
   - Use common or botanical names consistently

10. **Color Coordination**
    - Use analogous colors for harmony (greens with blues)
    - Use complementary colors for contrast (green with red/pink blooms)
    - Keep hardscaping neutral to highlight vegetation

### Reusable Elements

11. **Create Templates**
    - Save common combinations as reusable elements
    - Example: patio set (deck + pergola + raised beds)
    - Store in separate YAML files for easy reuse

12. **Use Room Concept**
    - Define outdoor "rooms" (patio area, vegetable garden, etc.)
    - Each room has its own anchor point
    - Easy to move entire sections

### Rendering Options

13. **DPI Settings**
    - Use 300 DPI for print-quality plans
    - Keep images under 8000 pixels per dimension
    - For large sites: reduce DPI or increase scale_denominator

14. **Labels and IDs**
    - Use labels for presentation plans
    - Use IDs for construction documents
    - Set `id_color: 'gray'` for subtle identifiers

15. **Markdown Reports**
    - Automatically generated with element counts
    - Includes species, dimensions, bloom seasons
    - Reference for plant ordering and installation


