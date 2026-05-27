# Floor Plan Elements Report

## Walls

| ID | Length (m) | Thickness (m) | Corner 1 (x,y) | Corner 2 (x,y) | Corner 3 (x,y) | Corner 4 (x,y) |
|---|---|---|---|---|---|---|
| wall_south | 4.0 | 0.2 | (0.500, 0.500) | (4.500, 0.500) | (4.500, 0.700) | (0.500, 0.700) |
| wall_east | 3.0 | 0.2 | (4.500, 0.500) | (4.500, 3.500) | (4.300, 3.500) | (4.300, 0.500) |
| wall_north | 4.0 | 0.2 | (4.500, 3.500) | (0.500, 3.500) | (0.500, 3.300) | (4.500, 3.300) |
| wall_west | 3.0 | 0.2 | (0.500, 3.500) | (0.500, 0.500) | (0.700, 0.500) | (0.700, 3.500) |

## Windows

| ID | Length (m) | Overall Thickness (m) | Corner 1 (x,y) | Corner 2 (x,y) | Corner 3 (x,y) | Corner 4 (x,y) |
|---|---|---|---|---|---|---|
| window_invisible | 1.5 | 0.2 | (4.500, 1.200) | (4.500, 2.700) | (4.300, 2.700) | (4.300, 1.200) |

## Doors

| ID | Doorway Width (m) | Door Width (m) | Opens to Right | Corner 1 (x,y) | Corner 2 (x,y) | Corner 3 (x,y) | Corner 4 (x,y) |
|---|---|---|---|---|---|---|---|
| door_invisible | 1.0 | 0.9 | Yes | (0.500, 2.000) | (0.500, 1.000) | (0.700, 1.000) | (0.700, 2.000) |

## Rooms

### test room with invisible openings_1

**Label:** test room with invisible openings

**Anchor Point:** (0.500, 0.500)

**Color:** black

**Dimensions:**

- Inner horizontal length: 3.600 m
- Inner vertical length: 2.600 m
- Outer horizontal length: 4.000 m
- Outer vertical length: 3.000 m
- Inner area: 9.360 m²
- Outer area: 12.000 m²

**External Corners:**

- Corner 1: (0.500, 0.500)
- Corner 2: (4.500, 0.500)
- Corner 3: (4.500, 3.500)
- Corner 4: (0.500, 3.500)

**Internal Corners:**

- Corner 1: (0.700, 0.700)
- Corner 2: (4.300, 0.700)
- Corner 3: (4.300, 3.300)
- Corner 4: (0.700, 3.300)

**Room Edge Walls:**

| Wall ID | Orientation | Length (m) | Thickness (m) |
|---|---|---|---|
| wall_south | Horizontal | 4.000 | 0.200 |
| wall_east | Vertical | 3.000 | 0.200 |
| wall_north | Horizontal | 4.000 | 0.200 |
| wall_west | Vertical | 3.000 | 0.200 |

**Other Elements in Room:**

| Element ID | Type |
|---|---|
| window_invisible | Window |
| door_invisible | Door |

## Summary

| Element Type | Count |
|---|---|
| Wall | 4 |
| Room | 1 |
| Door | 1 |
| Window | 1 |
