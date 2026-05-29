"""
Wall opening detection and geometry generation for doors and windows.

This module handles detecting when doors/windows are embedded in walls and
generating wall geometry with proper holes/openings.
"""

import math
from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from .elements.element import Element


def _opening_corners_world(opening: 'Element') -> list[tuple[float, float]]:
    """
    Return the four world-space (x, y) corners of a rectangular opening element.

    Corners are computed by rotating the element's local bounding rectangle
    (width=length, height=thickness) by orientation_angle around anchor_point.
    """
    ax_, ay = opening.anchor_point
    L = opening.length
    T = opening.thickness
    angle_rad = math.radians(opening.orientation_angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)

    # Local offsets of the 4 corners: (0,0), (L,0), (L,T), (0,T)
    offsets = [(0.0, 0.0), (L, 0.0), (L, T), (0.0, T)]
    return [
        (ax_ + dx * cos_a - dy * sin_a,
         ay + dx * sin_a + dy * cos_a)
        for dx, dy in offsets
    ]


def is_element_embedded_in_wall(wall: 'Element', opening: 'Element', tolerance: float = 0.1) -> bool:
    """
    Check if a door or window is embedded in a wall.

    An opening is considered embedded when **at least one of its four corners**
    falls inside the wall's bounding rectangle (length × thickness) in the wall's
    local coordinate system, within *tolerance* metres.

    The opening must also be roughly parallel to the wall (within 5°) so that
    perpendicular walls next to each other are not incorrectly matched.

    Args:
        wall: Wall element to check.
        opening: Any element that may cut an opening (door, window, etc.).
        tolerance: Positional tolerance in metres (default 0.1 m = 10 cm).

    Returns:
        True if opening is embedded in wall, False otherwise.
    """
    from .elements.basic import WallND
    from .elements.vertical_levels import VertInfoDoor, VertInfoWindows

    # Wall must be a WallND subclass
    if not isinstance(wall, WallND):
        return False

    # Opening must be a door or window type (VertInfoLvl02 covers Door/BalconyDoor
    # and its subclasses; VertInfoWindows covers Window and _FixedWindow variants).
    # This prevents other walls, furniture, etc. from being falsely detected.
    if not isinstance(opening, (VertInfoDoor, VertInfoWindows)):
        return False

    # Both elements must have the required geometric attributes
    required = ('anchor_point', 'length', 'thickness', 'orientation_angle')
    if not all(hasattr(wall, a) for a in required):
        return False
    if not all(hasattr(opening, a) for a in required):
        return False

    # Opening must be parallel (or anti-parallel) to the wall, within 5°
    angle_diff = abs(wall.orientation_angle - opening.orientation_angle) % 360
    if angle_diff > 180:
        angle_diff = 360 - angle_diff
    if angle_diff > 5.0 and abs(angle_diff - 180) > 5.0:
        return False

    # Transform each of the opening's 4 corners into wall-local coordinates
    # and check whether at least one falls inside the wall rectangle + tolerance.
    wall_ax, wall_ay = wall.anchor_point
    inv_rad = math.radians(-wall.orientation_angle)
    cos_inv = math.cos(inv_rad)
    sin_inv = math.sin(inv_rad)

    for wx, wy in _opening_corners_world(opening):
        dx = wx - wall_ax
        dy = wy - wall_ay
        local_x = dx * cos_inv - dy * sin_inv
        local_y = dx * sin_inv + dy * cos_inv

        in_length_span = -tolerance <= local_x <= wall.length + tolerance
        in_thickness_band = -tolerance <= local_y <= wall.thickness + tolerance

        if in_length_span and in_thickness_band:
            return True

    return False


def find_embedded_openings(wall: 'Element', all_elements: list['Element'], tolerance: float = 0.1) -> list['Element']:
    """
    Find all doors and windows embedded in a specific wall.
    
    Args:
        wall: Wall element to check
        all_elements: List of all floor plan elements
        tolerance: Position tolerance in meters
        
    Returns:
        List of door/window elements embedded in the wall
    """
    embedded = []
    
    for element in all_elements:
        if element is wall:  # Skip self
            continue
        
        if is_element_embedded_in_wall(wall, element, tolerance):
            embedded.append(element)
    
    return embedded


def generate_wall_with_openings(wall: 'Element', openings: list['Element']) -> tuple[
    list[tuple[float, float, float]], 
    list[tuple[int, int, int]], 
    dict[str, list[int]]
]:
    """
    Generate wall geometry with holes for embedded doors/windows.
    
    Creates a mesh with rectangular cutouts for each opening.
    
    Args:
        wall: Wall element
        openings: List of embedded door/window elements
        
    Returns:
        tuple containing:
        - vertices: List of (x, y, z) vertex coordinates
        - indices: List of (v1, v2, v3) triangle indices
        - face_groups: Dict mapping face names to lists of triangle indices
    """
    # If no openings, use standard box geometry
    if not openings:
        return wall.generate_vertices_and_indices()
    
    # Get wall dimensions in local coordinates
    wall_length = wall.length
    wall_thickness = wall.thickness
    wall_height = wall.height
    wall_v_anchor = wall.v_anchor
    wall_anchor = wall.anchor_point
    wall_angle = wall.orientation_angle
    
    # Collect opening info (relative to wall's local coordinate system)
    opening_infos = []
    for opening in openings:
        # Transform opening to wall's local coordinates
        opening_anchor = opening.anchor_point
        dx = opening_anchor[0] - wall_anchor[0]
        dy = opening_anchor[1] - wall_anchor[1]
        
        # Rotate to local coordinates
        angle_rad = math.radians(-wall_angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)
        
        local_x = dx * cos_a - dy * sin_a
        local_y = dx * sin_a + dy * cos_a
        
        # For pass-through holes, create opening on BOTH faces
        # (doors and windows should cut through the entire wall thickness)
        opening_info_base = {
            'element': opening,
            'start_x': local_x,
            'end_x': local_x + opening.length,
            'width': opening.length,
            'height': opening.height if hasattr(opening, 'height') else wall_height,
            'bottom_y': opening.v_anchor if hasattr(opening, 'v_anchor') else wall_v_anchor,
        }
        
        # Add the opening to both front and back faces
        opening_info_front = {**opening_info_base, 'face': 'front'}
        opening_info_back = {**opening_info_base, 'face': 'back'}
        opening_infos.append(opening_info_front)
        opening_infos.append(opening_info_back)
    
    # Sort openings by position for easier processing
    opening_infos.sort(key=lambda o: o['start_x'])
    
    # Generate wall geometry with holes
    vertices = []
    indices = []
    face_groups = {}
    
    # Generate front and back faces with holes
    front_openings = [o for o in opening_infos if o['face'] == 'front']
    back_openings = [o for o in opening_infos if o['face'] == 'back']
    
    # Generate front face with holes
    front_verts_local, front_indices_local = _generate_face_with_holes(
        wall_length, wall_height, wall_v_anchor, front_openings
    )
    
    # Transform front face vertices to world coordinates (y=0 in local, front face)
    front_verts_start_idx = len(vertices)
    for x, y in front_verts_local:
        # Local position: (x, 0, y) -> (x along wall, z=0 front face, y is height)
        world_pos = _local_to_world(x, 0, y, wall_anchor, wall_angle)
        vertices.append(world_pos)
    
    # Add front face indices (reverse winding for outward normal pointing -Z)
    front_tri_start_idx = len(indices)
    for i1, i2, i3 in front_indices_local:
        indices.append((front_verts_start_idx + i1, front_verts_start_idx + i3, front_verts_start_idx + i2))
    
    face_groups['front'] = list(range(front_tri_start_idx, len(indices)))
    
    # Generate back face with holes
    back_verts_local, back_indices_local = _generate_face_with_holes(
        wall_length, wall_height, wall_v_anchor, back_openings
    )
    
    # Transform back face vertices to world coordinates (y=thickness in local, back face)
    back_verts_start_idx = len(vertices)
    for x, y in back_verts_local:
        world_pos = _local_to_world(x, wall_thickness, y, wall_anchor, wall_angle)
        vertices.append(world_pos)
    
    # Add back face indices (use as-is for outward normal pointing +Z)
    back_tri_start_idx = len(indices)
    for i1, i2, i3 in back_indices_local:
        indices.append((back_verts_start_idx + i1, back_verts_start_idx + i2, back_verts_start_idx + i3))
    
    face_groups['back'] = list(range(back_tri_start_idx, len(indices)))
    
    # Generate side faces (top, bottom, left, right, and around openings)
    side_tri_start_idx = len(indices)
    side_verts_start_idx = len(vertices)
    
    # Bottom face (entire bottom edge)
    bottom_verts = [
        (0, 0, wall_v_anchor),
        (wall_length, 0, wall_v_anchor),
        (wall_length, wall_thickness, wall_v_anchor),
        (0, wall_thickness, wall_v_anchor)
    ]
    bottom_vert_indices = []
    for x, y, z in bottom_verts:
        world_pos = _local_to_world(x, y, z, wall_anchor, wall_angle)
        vertices.append(world_pos)
        bottom_vert_indices.append(len(vertices) - 1)
    
    # Bottom triangles - winding for downward normal (0, -1, 0)
    indices.append((bottom_vert_indices[0], bottom_vert_indices[1], bottom_vert_indices[2]))
    indices.append((bottom_vert_indices[0], bottom_vert_indices[2], bottom_vert_indices[3]))
    
    # Top face (entire top edge)
    top_verts = [
        (0, 0, wall_v_anchor + wall_height),
        (wall_length, 0, wall_v_anchor + wall_height),
        (wall_length, wall_thickness, wall_v_anchor + wall_height),
        (0, wall_thickness, wall_v_anchor + wall_height)
    ]
    top_vert_indices = []
    for x, y, z in top_verts:
        world_pos = _local_to_world(x, y, z, wall_anchor, wall_angle)
        vertices.append(world_pos)
        top_vert_indices.append(len(vertices) - 1)
    
    # Top triangles - winding for upward normal (0, 1, 0)
    indices.append((top_vert_indices[0], top_vert_indices[2], top_vert_indices[1]))
    indices.append((top_vert_indices[0], top_vert_indices[3], top_vert_indices[2]))
    
    # Left face (x=0 edge)
    left_verts = [
        (0, 0, wall_v_anchor),
        (0, wall_thickness, wall_v_anchor),
        (0, wall_thickness, wall_v_anchor + wall_height),
        (0, 0, wall_v_anchor + wall_height)
    ]
    left_vert_indices = []
    for x, y, z in left_verts:
        world_pos = _local_to_world(x, y, z, wall_anchor, wall_angle)
        vertices.append(world_pos)
        left_vert_indices.append(len(vertices) - 1)
    
    # Left face triangles - winding for -X normal (outward)
    indices.append((left_vert_indices[0], left_vert_indices[1], left_vert_indices[2]))
    indices.append((left_vert_indices[0], left_vert_indices[2], left_vert_indices[3]))
    
    # Right face (x=wall_length edge)
    right_verts = [
        (wall_length, 0, wall_v_anchor),
        (wall_length, wall_thickness, wall_v_anchor),
        (wall_length, wall_thickness, wall_v_anchor + wall_height),
        (wall_length, 0, wall_v_anchor + wall_height)
    ]
    right_vert_indices = []
    for x, y, z in right_verts:
        world_pos = _local_to_world(x, y, z, wall_anchor, wall_angle)
        vertices.append(world_pos)
        right_vert_indices.append(len(vertices) - 1)
    
    # Right face triangles - winding for +X normal (outward)
    indices.append((right_vert_indices[0], right_vert_indices[2], right_vert_indices[1]))
    indices.append((right_vert_indices[0], right_vert_indices[3], right_vert_indices[2]))
    
    # Generate faces around each opening's perimeter (thickness sides of holes)
    opening_edges_start_idx = len(indices)
    for opening_info in front_openings:  # Process each unique opening once
        start_x = opening_info['start_x']
        end_x = opening_info['end_x']
        bottom_z = opening_info['bottom_y']
        top_z = bottom_z + opening_info['height']
        
        # Bottom edge of opening (horizontal strip below the hole)
        bottom_edge_verts = [
            (start_x, 0, bottom_z),
            (end_x, 0, bottom_z),
            (end_x, wall_thickness, bottom_z),
            (start_x, wall_thickness, bottom_z)
        ]
        bottom_edge_indices = []
        for x, y, z in bottom_edge_verts:
            world_pos = _local_to_world(x, y, z, wall_anchor, wall_angle)
            vertices.append(world_pos)
            bottom_edge_indices.append(len(vertices) - 1)
        
        # Bottom edge triangles (upward facing into the opening)
        indices.append((bottom_edge_indices[0], bottom_edge_indices[2], bottom_edge_indices[1]))
        indices.append((bottom_edge_indices[0], bottom_edge_indices[3], bottom_edge_indices[2]))
        
        # Top edge of opening (horizontal strip above the hole)
        top_edge_verts = [
            (start_x, 0, top_z),
            (end_x, 0, top_z),
            (end_x, wall_thickness, top_z),
            (start_x, wall_thickness, top_z)
        ]
        top_edge_indices = []
        for x, y, z in top_edge_verts:
            world_pos = _local_to_world(x, y, z, wall_anchor, wall_angle)
            vertices.append(world_pos)
            top_edge_indices.append(len(vertices) - 1)
        
        # Top edge triangles (downward facing into the opening)
        indices.append((top_edge_indices[0], top_edge_indices[1], top_edge_indices[2]))
        indices.append((top_edge_indices[0], top_edge_indices[2], top_edge_indices[3]))
        
        # Left edge of opening (vertical strip on left side of hole)
        left_edge_verts = [
            (start_x, 0, bottom_z),
            (start_x, wall_thickness, bottom_z),
            (start_x, wall_thickness, top_z),
            (start_x, 0, top_z)
        ]
        left_edge_indices = []
        for x, y, z in left_edge_verts:
            world_pos = _local_to_world(x, y, z, wall_anchor, wall_angle)
            vertices.append(world_pos)
            left_edge_indices.append(len(vertices) - 1)
        
        # Left edge triangles (facing left/outward from opening)
        indices.append((left_edge_indices[0], left_edge_indices[2], left_edge_indices[1]))
        indices.append((left_edge_indices[0], left_edge_indices[3], left_edge_indices[2]))
        
        # Right edge of opening (vertical strip on right side of hole)
        right_edge_verts = [
            (end_x, 0, bottom_z),
            (end_x, wall_thickness, bottom_z),
            (end_x, wall_thickness, top_z),
            (end_x, 0, top_z)
        ]
        right_edge_indices = []
        for x, y, z in right_edge_verts:
            world_pos = _local_to_world(x, y, z, wall_anchor, wall_angle)
            vertices.append(world_pos)
            right_edge_indices.append(len(vertices) - 1)
        
        # Right edge triangles (facing right/outward from opening)
        indices.append((right_edge_indices[0], right_edge_indices[1], right_edge_indices[2]))
        indices.append((right_edge_indices[0], right_edge_indices[2], right_edge_indices[3]))
    
    face_groups['sides'] = list(range(side_tri_start_idx, len(indices)))
    face_groups['top'] = [side_tri_start_idx + 2, side_tri_start_idx + 3]
    face_groups['bottom'] = [side_tri_start_idx, side_tri_start_idx + 1]
    face_groups['left'] = [side_tri_start_idx + 4, side_tri_start_idx + 5]
    face_groups['right'] = [side_tri_start_idx + 6, side_tri_start_idx + 7]
    face_groups['opening_edges'] = list(range(opening_edges_start_idx, len(indices)))
    face_groups['all'] = list(range(len(indices)))
    
    return vertices, indices, face_groups


def _generate_face_with_holes(width: float, height: float, base_y: float, 
                              openings: list[dict]) -> tuple[list[tuple[float, float]], list[tuple[int, int, int]]]:
    """
    Generate 2D face (in XY plane) with rectangular holes.
    
    Args:
        width: Face width (wall length)
        height: Face height (wall height)
        base_y: Base Y coordinate (wall v_anchor)
        openings: List of opening info dicts with 'start_x', 'width', 'bottom_y', 'height'
        
    Returns:
        tuple of (vertices_2d, triangle_indices)
        vertices_2d: List of (x, y) coordinates
        triangle_indices: List of (i1, i2, i3) triangle vertex indices
    """
    if not openings:
        # Simple rectangle: 4 vertices, 2 triangles
        vertices = [
            (0, base_y),
            (width, base_y),
            (width, base_y + height),
            (0, base_y + height)
        ]
        triangles = [(0, 1, 2), (0, 2, 3)]
        return vertices, triangles
    
    # Create horizontal strips separated by opening boundaries
    # Collect all Y coordinates (horizontal divisions)
    y_coords = {base_y, base_y + height}
    for opening in openings:
        y_coords.add(opening['bottom_y'])
        y_coords.add(opening['bottom_y'] + opening['height'])
    
    y_coords = sorted(y_coords)
    
    # Collect all X coordinates (vertical divisions)
    x_coords = {0, width}
    for opening in openings:
        x_coords.add(max(0, opening['start_x']))
        x_coords.add(min(width, opening['end_x']))
    
    x_coords = sorted(x_coords)
    
    # Generate grid vertices
    vertices = []
    vertex_grid = {}  # (xi, yi) -> vertex_index
    
    for yi, y in enumerate(y_coords):
        for xi, x in enumerate(x_coords):
            vertex_grid[(xi, yi)] = len(vertices)
            vertices.append((x, y))
    
    # Generate triangles for each grid cell, skipping cells inside openings
    triangles = []
    
    for yi in range(len(y_coords) - 1):
        for xi in range(len(x_coords) - 1):
            # Check if this cell is inside any opening
            cell_x = (x_coords[xi] + x_coords[xi + 1]) / 2
            cell_y = (y_coords[yi] + y_coords[yi + 1]) / 2
            
            is_inside_opening = False
            for opening in openings:
                if (opening['start_x'] <= cell_x <= opening['end_x'] and
                    opening['bottom_y'] <= cell_y <= opening['bottom_y'] + opening['height']):
                    is_inside_opening = True
                    break
            
            if not is_inside_opening:
                # Add two triangles for this cell
                v0 = vertex_grid[(xi, yi)]
                v1 = vertex_grid[(xi + 1, yi)]
                v2 = vertex_grid[(xi + 1, yi + 1)]
                v3 = vertex_grid[(xi, yi + 1)]
                
                triangles.append((v0, v1, v2))
                triangles.append((v0, v2, v3))
    
    return vertices, triangles


def _local_to_world(x: float, y: float, z: float, anchor: tuple[float, float], 
                   angle_degrees: float) -> tuple[float, float, float]:
    """
    Transform local coordinates to world coordinates.
    
    Local coords: x along wall length, y along wall thickness, z is height
    World coords: rotated by wall angle, translated by anchor
    
    Args:
        x, y, z: Local coordinates
        anchor: Wall anchor point (world X, Z)
        angle_degrees: Wall orientation angle
        
    Returns:
        (world_x, world_y, world_z) coordinates
    """
    # Rotate XY plane (Z remains Z)
    angle_rad = math.radians(angle_degrees)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    world_x = x * cos_a - y * sin_a + anchor[0]
    world_z = x * sin_a + y * cos_a + anchor[1]
    world_y = z  # Height remains height
    
    return (world_x, world_y, world_z)
