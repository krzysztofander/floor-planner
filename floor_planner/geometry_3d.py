"""
3D geometry generation mixins for floor plan elements.

This module provides mixin classes that add 3D geometry generation capabilities
to 2D floor plan elements. Elements can generate vertices, faces, and texture
coordinates for export to OBJ/MTL format.

The geometry generation uses the existing vertical positioning system (v_anchor, height)
to extrude 2D elements into 3D objects.
"""

from abc import ABC, abstractmethod
import math
from typing import TYPE_CHECKING

from .utils import rotate_point

if TYPE_CHECKING:
    from .elements.element import Element


def is_3d_eligible(element: 'Element') -> bool:
    """
    Check if an element is eligible for 3D model generation.
    
    Args:
        element: The element to check
        
    Returns:
        True if element should be exported to 3D, False otherwise
        
    Excludes:
        - Info elements (DimensionArrow, TextBox) - non-physical annotations
        - Room containers - just coordinate systems, children are generated
        - Elements with height = 0.0
        - Elements with color = 'invisible'
        - Elements with zero dimensions (length, thickness, diameter)
    """
    from .elements.symbols.info import DimensionArrow, TextBox
    from .floor_plan import Room

    if element.isList():
        return any(is_3d_eligible(sub_element) for sub_element in element.getList())

    if isinstance(element, (DimensionArrow, TextBox, Room)):
        return False
    
    if element.height == 0.0:
        return False
    
    if hasattr(element, 'color') and element.color == 'invisible':
        return False
    
    # Check for zero dimensions
    if hasattr(element, 'length') and element.length == 0.0:
        return False
    
    if hasattr(element, 'thickness') and element.thickness == 0.0:
        return False
    
    if hasattr(element, 'diameter') and element.diameter == 0.0:
        return False
    
    return True


class Generate3DMixin(ABC):
    """
    Abstract base class for 3D geometry generation.
    
    Subclasses must implement generate_vertices_and_indices() to provide
    3D geometry data for OBJ export.
    """
    
    @abstractmethod
    def generate_vertices_and_indices(self) -> tuple[list[tuple[float, float, float]], 
                                                      list[tuple[int, int, int]], 
                                                      dict[str, list[int]]]:
        """
        Generate 3D vertices, triangle indices, and face groups for this element.
        
        Returns:
            tuple containing:
            - vertices: List of (x, y, z) vertex coordinates
            - indices: List of (v1, v2, v3) triangle indices (0-based, relative to this element)
            - face_groups: Dict mapping face names to lists of triangle indices
                          e.g., {'front': [0, 1], 'back': [2, 3], 'top': [4, 5]}
                          Used for multi-texture support
        """
        pass


class RectangularGeometry3D(Generate3DMixin):
    """
    3D geometry generation for rectangular elements (walls, doors, windows, furniture).
    
    Generates a box with 8 vertices (4 bottom, 4 top) and 12 triangles (2 per face, 6 faces).
    
    Uses element properties:
        - anchor_point (x, z) - bottom-left corner in 2D floor plan
        - length, thickness - horizontal dimensions
        - orientation_angle - rotation around vertical axis
        - v_anchor - Y coordinate of bottom
        - height - Y extent (top = v_anchor + height)
    """
    
    def generate_vertices_and_indices(self) -> tuple[list[tuple[float, float, float]], 
                                                      list[tuple[int, int, int]], 
                                                      dict[str, list[int]]]:
        """Generate box geometry with 8 vertices and 12 triangles."""
        
        # Get expansion for z-fighting prevention.
        # Preferred interface: _get_3d_expansion() returns (length_exp, thickness_exp, height_exp)
        # each value is the total expansion; half is applied on each side.
        # Legacy fallback: _get_geometric_offset() returns one value for both length and thickness.
        if hasattr(self, '_get_3d_expansion'):
            length_exp, thickness_exp, height_exp = self._get_3d_expansion()
        elif hasattr(self, '_get_geometric_offset'):
            geo_offset = self._get_geometric_offset()
            length_exp = geo_offset
            thickness_exp = geo_offset
            height_exp = 0.0
        else:
            length_exp = thickness_exp = height_exp = 0.0

        length_half = length_exp / 2
        thickness_half = thickness_exp / 2
        height_half = height_exp / 2

        # Get bottom corners in 2D (before rotation)
        # Rectangular elements: length along X, thickness along Z
        # Centered expansion: extend equally on both sides
        local_corners = [
            (-length_half, -thickness_half),                                          # bottom-left
            (self.length + length_half, -thickness_half),                             # bottom-right
            (self.length + length_half, self.thickness + thickness_half),             # top-right
            (-length_half, self.thickness + thickness_half)                           # top-left
        ]

        # Rotate corners around anchor point
        rotated_corners = self._rotate_corners(local_corners, self.anchor_point,
                                               self.orientation_angle)

        # Generate 3D vertices
        vertices = []

        # Bottom face (Y = v_anchor - height_half)
        for x, z in rotated_corners:
            vertices.append((x, self.v_anchor - height_half, z))

        # Top face (Y = v_anchor + height + height_half)
        for x, z in rotated_corners:
            vertices.append((x, self.v_anchor + self.height + height_half, z))
        
        # Generate triangle indices for 6 faces (12 triangles total)
        # Indices are 0-based relative to this element's vertices
        # Winding order: counter-clockwise when viewed from OUTSIDE produces outward normals
        indices = []
        face_groups = {}
        
        # Bottom face (indices 0-3) - normal should point down (0, -1, 0)
        # When looking from below (outside), vertices should be counter-clockwise
        bottom_tris = [
            (0, 1, 2),  # triangle 1: left → right → top-right (CCW from below)
            (0, 2, 3)   # triangle 2: left → top-right → top-left (CCW from below)
        ]
        indices.extend(bottom_tris)
        face_groups['bottom'] = [0, 1]
        
        # Top face (indices 4-7) - normal should point up (0, 1, 0)
        # When looking from above (outside), vertices should be counter-clockwise
        top_tris = [
            (4, 6, 5),  # triangle 1: left → top-right → right (CCW from above)
            (4, 7, 6)   # triangle 2: left → top-left → top-right (CCW from above)
        ]
        indices.extend(top_tris)
        face_groups['top'] = [2, 3]
        
        # Front face (bottom edge closest to origin) - normal should point out in -Z
        # Reverse winding to point outward: was (0,1,5), (0,5,4), now (0,5,1), (0,4,5)
        front_tris = [
            (0, 5, 1),  # triangle 1
            (0, 4, 5)   # triangle 2
        ]
        indices.extend(front_tris)
        face_groups['front'] = [4, 5]
        
        # Back face - normal should point out in +Z
        # Reverse winding to point outward: was (2,3,7), (2,7,6), now (2,7,3), (2,6,7)
        back_tris = [
            (2, 7, 3),  # triangle 1
            (2, 6, 7)   # triangle 2
        ]
        indices.extend(back_tris)
        face_groups['back'] = [6, 7]
        
        # Right face - normal should point out in +X
        # Reverse winding to point outward: was (1,2,6), (1,6,5), now (1,6,2), (1,5,6)
        right_tris = [
            (1, 6, 2),  # triangle 1
            (1, 5, 6)   # triangle 2
        ]
        indices.extend(right_tris)
        face_groups['right'] = [8, 9]
        
        # Left face - normal should point out in -X
        # Reverse winding to point outward: was (3,0,4), (3,4,7), now (3,4,0), (3,7,4)
        left_tris = [
            (3, 4, 0),  # triangle 1
            (3, 7, 4)   # triangle 2
        ]
        indices.extend(left_tris)
        face_groups['left'] = [10, 11]
        
        # Add 'sides' group for convenience (all 4 vertical faces)
        face_groups['sides'] = [4, 5, 6, 7, 8, 9, 10, 11]
        
        # Add 'all' group for single-texture elements
        face_groups['all'] = list(range(12))
        
        return vertices, indices, face_groups
    
    def _rotate_corners(self, corners: list[tuple[float, float]], 
                       anchor: tuple[float, float], 
                       angle_degrees: float) -> list[tuple[float, float]]:
        """
        Rotate 2D corners around anchor point.
        
        Args:
            corners: List of (x, z) coordinates relative to anchor
            anchor: (x, z) anchor point
            angle_degrees: Rotation angle in degrees (counterclockwise)
            
        Returns:
            List of rotated (x, z) coordinates in world space
        """
        if angle_degrees == 0:
            # No rotation, just translate to anchor
            return [(anchor[0] + x, anchor[1] + z) for x, z in corners]
        
        # Convert to radians once for all corners
        angle_rad = math.radians(angle_degrees)
        
        # Use rotate_point utility for each corner (benefits from caching)
        rotated = [rotate_point(anchor, x, z, angle_rad) for x, z in corners]
        
        return rotated


class CircularGeometry3D(Generate3DMixin):
    """
    3D geometry generation for circular elements (lamps, circular tables, columns).
    
    Generates a cylinder with configurable number of segments (default 16).
    Creates vertices for bottom and top circles, plus triangulated caps and side faces.
    
    Uses element properties:
        - anchor_point (x, z) - center point in 2D
        - diameter - circle diameter
        - v_anchor - Y coordinate of bottom
        - height - Y extent
        - circle_segments (optional) - number of segments for smoother/coarser circles
    """
    
    CIRCLE_SEGMENTS = 16  # Default number of vertices around circle
    
    def generate_vertices_and_indices(self) -> tuple[list[tuple[float, float, float]], 
                                                      list[tuple[int, int, int]], 
                                                      dict[str, list[int]]]:
        """Generate cylinder geometry with n-segment circles."""
        
        # Get expansion for z-fighting prevention.
        # For circular elements length_exp is used as the diameter expansion.
        if hasattr(self, '_get_3d_expansion'):
            diameter_exp, _, _ = self._get_3d_expansion()
        elif hasattr(self, '_get_geometric_offset'):
            diameter_exp = self._get_geometric_offset()
        else:
            diameter_exp = 0.0

        center_x, center_z = self.anchor_point
        # Apply expansion to radius (makes cylinder slightly larger/smaller)
        radius = (self.diameter + diameter_exp) / 2
        
        # Use element-specific segments if provided, otherwise use class default
        segments = getattr(self, 'circle_segments', self.CIRCLE_SEGMENTS)
        
        # Clamp segments to reasonable range (3 minimum for a shape, 64 maximum for performance)
        segments = max(3, min(64, segments))
        
        vertices = []
        
        # Generate bottom circle vertices (Y = v_anchor)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = center_x + radius * math.cos(angle)
            z = center_z + radius * math.sin(angle)
            vertices.append((x, self.v_anchor, z))
        
        # Generate top circle vertices (Y = v_anchor + height)
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = center_x + radius * math.cos(angle)
            z = center_z + radius * math.sin(angle)
            vertices.append((x, self.v_anchor + self.height, z))
        
        # Add center vertices for cap triangulation
        # Bottom center
        vertices.append((center_x, self.v_anchor, center_z))
        bottom_center_idx = len(vertices) - 1
        
        # Top center
        vertices.append((center_x, self.v_anchor + self.height, center_z))
        top_center_idx = len(vertices) - 1
        
        # Generate triangle indices
        indices = []
        face_groups = {}
        triangle_idx = 0
        
        # Bottom cap triangles (fan from center).
        # Vertices go CCW from above, so (center, next_i, i) produces a +Y normal (inward).
        # Reverse to (center, i, next_i) for outward -Y normal.
        bottom_tris = []
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.append((bottom_center_idx, i, next_i))
            bottom_tris.append(triangle_idx)
            triangle_idx += 1
        face_groups['bottom'] = bottom_tris
        
        # Top cap triangles (fan from center).
        # (center, top[i], top[next_i]) produces a -Y normal (inward).
        # Reverse to (center, top[next_i], top[i]) for outward +Y normal.
        top_tris = []
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.append((top_center_idx, segments + next_i, segments + i))
            top_tris.append(triangle_idx)
            triangle_idx += 1
        face_groups['top'] = top_tris
        
        # Side faces (2 triangles per segment)
        # Winding is CCW when viewed from outside (outward normals).
        # Vertices go CCW from above, so from outside the cylinder the quad is:
        #   bottom[i] (left), bottom[next] (right), top[next] (top-right), top[i] (top-left)
        # CCW from outside: bottom[i] → top[next] → bottom[next]  (tri 1)
        #                   bottom[i] → top[i]    → top[next]     (tri 2)
        sides_tris = []
        for i in range(segments):
            next_i = (i + 1) % segments
            
            # Triangle 1: bottom[i], top[next], bottom[next]  (CCW from outside)
            indices.append((i, segments + next_i, next_i))
            sides_tris.append(triangle_idx)
            triangle_idx += 1
            
            # Triangle 2: bottom[i], top[i], top[next]  (CCW from outside)
            indices.append((i, segments + i, segments + next_i))
            sides_tris.append(triangle_idx)
            triangle_idx += 1
        
        face_groups['sides'] = sides_tris
        face_groups['all'] = list(range(len(indices)))
        
        return vertices, indices, face_groups

def _add_roof_inner_surface(
    vertices: list[tuple[float, float, float]],
    indices: list[tuple[int, int, int]],
    face_groups: dict[str, list[int]],
    y_shift: float = 0.4,
) -> tuple[list[tuple[float, float, float]],
           list[tuple[int, int, int]],
           dict[str, list[int]]]:  # noqa: E501
    """
    Build a thick roof shell from inner (underside/ceiling) surface vertices.

    Input ``vertices`` sit at ``v_anchor`` — the inner surface visible from
    inside the building.  This function creates the outer (weather-facing)
    surface by shifting every vertex **vertically** upward by ``y_shift``.

    The perpendicular distance between the two parallel slope planes equals
    ``y_shift * cos(slope_angle)``.  Each geometry class therefore computes
    ``y_shift = roof_thickness / cos(slope_angle)`` so the shell is exactly
    ``roof_thickness`` thick regardless of slope steepness.

    With a pure vertical shift, all octants whose inner apices share the same
    (plan_x, height, plan_z) will have outer apices at the same position too,
    so they continue to meet at the peak.

    Vertex layout in the returned array::

        0 … n-1    outer surface  (inner + y_shift, original winding)
        n … 2n-1   inner surface  (at v_anchor, reversed winding)

    ``face_groups`` (referencing 0 … n-1) therefore address the outer
    surface, which is correct for texture and material assignment.
    """
    n = len(vertices)
    outer_verts = [(x, y + y_shift, z) for (x, y, z) in vertices]
    inner_indices = [
        (i0 + n, i2 + n, i1 + n)   # reversed winding → inward normals
        for (i0, i1, i2) in indices
    ]

    # ── Closing strips: connect outer perimeter to inner perimeter ────────────
    # A boundary edge is a directed half-edge (a→b) whose reverse (b→a) does
    # not appear in any triangle.  For each such edge we add a quad strip
    # (two triangles) bridging the outer and inner surfaces.
    #
    # Winding for the strip, viewed from outside the eave (outward normal):
    #   For boundary edge a→b on the outer CCW surface:
    #   tri1: (a, b, n+b)   — outer_a, outer_b, inner_b
    #   tri2: (a, n+b, n+a) — outer_a, inner_b, inner_a
    half_edges: set[tuple[int, int]] = set()
    for i0, i1, i2 in indices:
        half_edges.add((i0, i1))
        half_edges.add((i1, i2))
        half_edges.add((i2, i0))

    strip_indices: list[tuple[int, int, int]] = []
    for a, b in half_edges:
        if (b, a) not in half_edges:
            # Correct outward-facing winding for the closing quad (outer_a →
            # inner_a → inner_b → outer_b, CCW from outside):
            strip_indices.append((a, n + a, n + b))
            strip_indices.append((a, n + b, b))

    new_vertices  = outer_verts + list(vertices)
    new_indices   = list(indices) + inner_indices + strip_indices

    inner_tri_start = len(indices)
    inner_and_strip_range = list(range(inner_tri_start,
                                       inner_tri_start + len(inner_indices) + len(strip_indices)))
    new_face_groups = {k: list(v) for k, v in face_groups.items()}
    new_face_groups['all'] = (
        list(face_groups.get('all', list(range(len(indices))))) + inner_and_strip_range
    )

    return new_vertices, new_indices, new_face_groups


class GableRoofGeometry3D(Generate3DMixin):
    """
    3D geometry for a gable roof.

    Only the two sloping planes — no gable-end triangles.
    Ridge runs along the longer plan dimension (or X when square).

    Extensions (extension_a / extension_b) extend the slope planes beyond the
    footprint while preserving the original slope angle: the eave height drops
    below v_anchor by (extension × slope_rate).

    Uses element properties:
        - anchor_point (x, z) - bottom-left corner in 2D floor plan
        - x_axis_size, z_axis_size, orientation_angle
        - v_anchor, height
        - extension_a, extension_b  (optional, default 0)
    """

    def generate_vertices_and_indices(
        self,
    ) -> tuple[list[tuple[float, float, float]],
               list[tuple[int, int, int]],
               dict[str, list[int]]]:

        x = self.x_axis_size
        z = self.z_axis_size
        y0 = self.v_anchor
        y1 = self.v_anchor + self.height
        ax0, az0 = self.anchor_point
        angle_rad = math.radians(self.orientation_angle)
        ext_a = getattr(self, 'extension_a', 0) or 0
        ext_b = getattr(self, 'extension_b', 0) or 0

        def w(lx, lz):
            return rotate_point((ax0, az0), lx, lz, angle_rad)

        if x >= z:
            # Ridge along X; slopes rise from z=0 and z=z toward z=z/2
            slope_rate = self.height / (z / 2)  # height-drop per metre of horizontal extension

            y_a = y0 - ext_a * slope_rate   # front eave y (below y0 when extended)
            y_b = y0 - ext_b * slope_rate   # back  eave y

            c0e = w(0, -ext_a)     # front-left  eave (plan z = -ext_a)
            c1e = w(x, -ext_a)     # front-right eave
            c2e = w(x, z + ext_b)  # back-right  eave (plan z = z + ext_b)
            c3e = w(0, z + ext_b)  # back-left   eave
            r0  = w(0, z / 2)      # left  ridge end
            r1  = w(x, z / 2)      # right ridge end

            vertices = [
                (c0e[0], y_a, c0e[1]),   # v0  front-left  eave
                (c1e[0], y_a, c1e[1]),   # v1  front-right eave
                (c2e[0], y_b, c2e[1]),   # v2  back-right  eave
                (c3e[0], y_b, c3e[1]),   # v3  back-left   eave
                (r0[0],  y1,  r0[1]),    # v4  left  ridge
                (r1[0],  y1,  r1[1]),    # v5  right ridge
            ]
            indices = [
                (0, 4, 5), (0, 5, 1),   # front slope
                (2, 5, 3), (3, 5, 4),   # back  slope
            ]
            face_groups = {
                'front_slope': [0, 1],
                'back_slope':  [2, 3],
                'slopes':      [0, 1, 2, 3],
                'all':         [0, 1, 2, 3],
            }
        else:
            # Ridge along Z; slopes rise from x=0 and x=x toward x=x/2
            slope_rate = self.height / (x / 2)

            y_a = y0 - ext_a * slope_rate   # left  eave y
            y_b = y0 - ext_b * slope_rate   # right eave y

            c0e = w(-ext_a,    0)   # front-left  eave (plan x = -ext_a)
            c1e = w(x + ext_b, 0)   # front-right eave
            c2e = w(x + ext_b, z)   # back-right  eave
            c3e = w(-ext_a,    z)   # back-left   eave
            r0  = w(x / 2, 0)       # front ridge end
            r1  = w(x / 2, z)       # back  ridge end

            vertices = [
                (c0e[0], y_a, c0e[1]),   # v0  front-left  eave
                (c1e[0], y_b, c1e[1]),   # v1  front-right eave
                (c2e[0], y_b, c2e[1]),   # v2  back-right  eave
                (c3e[0], y_a, c3e[1]),   # v3  back-left   eave
                (r0[0],  y1,  r0[1]),    # v4  front ridge
                (r1[0],  y1,  r1[1]),    # v5  back  ridge
            ]
            indices = [
                (0, 3, 5), (0, 5, 4),   # left  slope
                (1, 4, 5), (1, 5, 2),   # right slope
            ]
            face_groups = {
                'left_slope':  [0, 1],
                'right_slope': [2, 3],
                'slopes':      [0, 1, 2, 3],
                'all':         [0, 1, 2, 3],
            }

        # Use a flat vertical y_shift equal to roof_thickness.
        # This guarantees that any two pieces sharing an inner vertex (same
        # v_anchor + height) will also share the same outer vertex, keeping
        # ridge/apex junctions watertight even when adjacent pieces have
        # different slope angles.
        thickness = getattr(self, 'roof_thickness', 0.4) or 0.4
        vertices, indices, face_groups = _add_roof_inner_surface(vertices, indices, face_groups, thickness)
        return vertices, indices, face_groups


class SingleSlopeRoofGeometry3D(Generate3DMixin):
    """
    3D geometry for a single-slope (mono-pitch / lean-to) roof.

    One rectangular sloping plane only — no gable end caps.
    The low eave runs along plan-z=0, the high eave along plan-z=z_axis_size.

    ``extension`` extends the slope plane beyond the footprint in the downhill
    direction while preserving the slope angle: the extended eave y-coordinate
    drops below v_anchor by (extension × slope_rate).

    Uses element properties:
        - anchor_point, x_axis_size, z_axis_size, orientation_angle
        - v_anchor, height
        - extension  (optional, default 0)
    """

    def generate_vertices_and_indices(
        self,
    ) -> tuple[list[tuple[float, float, float]],
               list[tuple[int, int, int]],
               dict[str, list[int]]]:

        x  = self.x_axis_size
        z  = self.z_axis_size
        y1 = self.v_anchor + self.height   # high eave
        ax0, az0 = self.anchor_point
        angle_rad = math.radians(self.orientation_angle)
        ext = getattr(self, 'extension', 0) or 0

        # Slope rate: height drop per metre of horizontal extension
        slope_rate = self.height / z if z else 0
        y_low = self.v_anchor - ext * slope_rate   # extended low eave y

        def w(lx, lz):
            return rotate_point((ax0, az0), lx, lz, angle_rad)

        le0 = w(0, -ext)   # low-left  (extended in plan)
        le1 = w(x, -ext)   # low-right (extended in plan)
        he0 = w(0, z)      # high-left
        he1 = w(x, z)      # high-right

        vertices = [
            (le0[0], y_low, le0[1]),   # v0 low-left
            (le1[0], y_low, le1[1]),   # v1 low-right
            (he1[0], y1,    he1[1]),   # v2 high-right
            (he0[0], y1,    he0[1]),   # v3 high-left
        ]

        indices = [
            (0, 2, 1),   # slope tri 1
            (0, 3, 2),   # slope tri 2
        ]
        face_groups = {
            'slope': [0, 1],
            'all':   [0, 1],
        }

        # Flat vertical y_shift = roof_thickness (see GableRoof comment).
        thickness = getattr(self, 'roof_thickness', 0.4) or 0.4
        vertices, indices, face_groups = _add_roof_inner_surface(vertices, indices, face_groups, thickness)
        return vertices, indices, face_groups


class HippedRoofOctantGeometry3D(Generate3DMixin):
    """
    3D geometry for a true 1/8th pyramid octant.

    A pyramid cut along all 4 axes of symmetry (2 cardinal + 2 diagonal) yields
    8 equal right-triangle pieces — octants.  Each is a triangular slope whose
    base edge runs from an edge-midpoint to the adjacent base corner.

    Local layout (orientation_angle=0, pointing in +z direction):

        apex (0, 0)  ← anchor_point / rotation pivot (high: v_anchor+height)
            |
            |  z_axis_size
            |
        midpoint (0, z)          eave midpoint (on main axis)

    Right variant (_octant_left=False):  corner at (+x_axis_size, z_axis_size)
    Left  variant (_octant_left=True):   corner at (-x_axis_size, z_axis_size)

    For a square pyramid with half-span d, use x_axis_size = z_axis_size = d.
    Combine 4 right + 4 left at 0°/90°/180°/270° to form the full pyramid.

    The 3D apex sits at (anchor_x, v_anchor+height, anchor_z); the two eave
    vertices sit at v_anchor.  Both 2D and 3D rotation pivot is anchor_point.
    """

    # Set by subclass: True = corner is to the LEFT, False = to the RIGHT
    _octant_left: bool = False

    def generate_vertices_and_indices(
        self,
    ) -> tuple[list[tuple[float, float, float]],
               list[tuple[int, int, int]],
               dict[str, list[int]]]:

        x   = self.x_axis_size   # lateral offset from midpoint to corner
        z   = self.z_axis_size   # depth from apex to eave
        ext = getattr(self, 'extension', 0) or 0
        y0  = self.v_anchor
        y1  = self.v_anchor + self.height
        ax0, az0 = self.anchor_point
        angle_rad = math.radians(self.orientation_angle)

        # Slope preserving: eave drops by (extension × slope_rate) below v_anchor
        slope_rate = self.height / z if z else 0
        y_eave = y0 - ext * slope_rate
        z_eave = z + ext   # plan depth of the (optionally extended) eave

        def w(lx, lz):
            return rotate_point((ax0, az0), lx, lz, angle_rad)

        tip    = w(0,                                         0)       # apex plan projection
        mid    = w(0,                                         z_eave)  # eave midpoint (on main axis)
        corner = w(-(x + ext) if self._octant_left else x + ext,
                                                         z_eave)  # eave corner (diagonal move)

        vertices = [
            (tip[0],    y1,     tip[1]),     # v0 — apex    (high)
            (mid[0],    y_eave, mid[1]),     # v1 — midpoint (low)
            (corner[0], y_eave, corner[1]),  # v2 — corner  (low)
        ]

        # Winding chosen so the outward normal points upward and away from the
        # pyramid interior.  Verified analytically:
        #   Right: (v1−v0)×(v2−v0) = (0, d², hd) — up + outward ✓
        #   Left:  (v2−v0)×(v1−v0) = (0, d², hd) — same ✓
        if self._octant_left:
            indices = [(0, 2, 1)]
        else:
            indices = [(0, 1, 2)]

        face_groups = {'slope': [0], 'all': [0]}

        # Flat vertical y_shift = roof_thickness (see GableRoof comment).
        thickness = getattr(self, 'roof_thickness', 0.4) or 0.4
        vertices, indices, face_groups = _add_roof_inner_surface(vertices, indices, face_groups, thickness)
        return vertices, indices, face_groups


class HippedInternalOctantGeometry3D(Generate3DMixin):
    """
    3D geometry for a 1/8th inverted-pyramid octant — the dual of
    HippedRoofOctantGeometry3D.  Models the inside (valley) corner of a
    complex roof, such as the interior corner of an L-shaped building or
    a patio roof that drains toward a central valley.

    The anchor_point is the **valley** (the lowest point / rotation pivot),
    mirroring how the external octant's anchor_point is the apex.

    Local layout (orientation_angle=0, pointing in +z direction):

        valley (0, 0)  ← anchor_point / rotation pivot (low: v_anchor)
            |
            |  z_axis_size
            |
        midpoint (0, z)          eave midpoint (on main axis, HIGH)

    Right variant (_octant_left=False):  corner at (+x_axis_size, z_axis_size) HIGH
    Left  variant (_octant_left=True):   corner at (-x_axis_size, z_axis_size) HIGH

    The same plan-view triangle tiles the area as with external octants:
    combine 4 right + 4 left at 0°/90°/180°/270° (all at the same centre
    valley point) to form a complete inverted pyramid (drain-to-centre patio
    roof).
    """

    _octant_left: bool = False

    def generate_vertices_and_indices(
        self,
    ) -> tuple[list[tuple[float, float, float]],
               list[tuple[int, int, int]],
               dict[str, list[int]]]:

        x   = self.x_axis_size   # lateral offset from midpoint to corner
        z   = self.z_axis_size   # depth from valley to eave
        ext = getattr(self, 'extension', 0) or 0
        y0  = self.v_anchor              # LOW (valley)
        y1  = self.v_anchor + self.height  # HIGH (eave, no extension)
        ax0, az0 = self.anchor_point
        angle_rad = math.radians(self.orientation_angle)

        # Slope-preserving extension: eave edge rises above v_anchor+height
        slope_rate = self.height / z if z else 0
        y_eave = y1 + ext * slope_rate   # eave rises with extension
        z_eave = z + ext
        x_eave = x + ext

        def w(lx, lz):
            return rotate_point((ax0, az0), lx, lz, angle_rad)

        tip    = w(0, 0)                                               # valley (LOW)
        mid    = w(0,  z_eave)                                         # eave midpoint (HIGH)
        corner = w(-(x_eave) if self._octant_left else x_eave,
                     z_eave)                                           # eave corner (HIGH)

        vertices = [
            (tip[0],    y0,      tip[1]),    # v0 — valley (LOW)
            (mid[0],    y_eave,  mid[1]),    # v1 — mid eave (HIGH)
            (corner[0], y_eave,  corner[1]), # v2 — corner eave (HIGH)
        ]

        # Winding so that the outward normal points upward and inward (toward
        # the valley centre).  Verified analytically:
        #   Right (0,1,2): (v1−v0)×(v2−v0) = (0, xz, −hx) — up + inward ✓
        #   Left  (0,2,1): (v2−v0)×(v1−v0) = (0, xz, −hx) — same ✓
        if self._octant_left:
            indices = [(0, 2, 1)]
        else:
            indices = [(0, 1, 2)]

        face_groups = {'slope': [0], 'all': [0]}

        thickness = getattr(self, 'roof_thickness', 0.4) or 0.4
        vertices, indices, face_groups = _add_roof_inner_surface(vertices, indices, face_groups, thickness)
        return vertices, indices, face_groups


class GableEndWallGeometry3D(Generate3DMixin):
    """
    3D geometry for a gable end wall — the triangular vertical panel that
    fills the gap between the wall plate (v_anchor) and the gable ridge
    (v_anchor + height) at one end of a gable roof.

    Parametrized identically to GableRoofGeometry3D so it can be dropped in
    with the same anchor_point / size / height / v_anchor / orientation_angle.

    For x_axis_size >= z_axis_size (ridge along X):
        Left  (_gable_end_right=False): triangle at local x = 0
        Right (_gable_end_right=True) : triangle at local x = x_axis_size

    For z_axis_size > x_axis_size (ridge along Z):
        Left  (_gable_end_right=False): triangle at local z = 0
        Right (_gable_end_right=True) : triangle at local z = z_axis_size

    Two overlapping triangles with reversed winding make the panel
    double-sided (visible from both inside and outside the building).

    Face groups:
        'wall'  – both triangles
        'all'   – both triangles
    """

    _gable_end_right: bool = False

    def generate_vertices_and_indices(
        self,
    ) -> tuple[list[tuple[float, float, float]],
               list[tuple[int, int, int]],
               dict[str, list[int]]]:

        x   = self.x_axis_size
        z   = self.z_axis_size
        y0  = self.v_anchor
        y1  = self.v_anchor + self.height
        ax0, az0 = self.anchor_point
        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point((ax0, az0), lx, lz, angle_rad)

        if x >= z:
            # Ridge along X; gable ends at x=0 (left) and x=x (right)
            px  = x if self._gable_end_right else 0.0
            c0  = w(px, 0)        # eave corner at z=0
            c1  = w(px, z)        # eave corner at z=z
            ap  = w(px, z / 2)    # apex (ridge mid-point projected to this end)
        else:
            # Ridge along Z; gable ends at z=0 (left) and z=z (right)
            pz  = z if self._gable_end_right else 0.0
            c0  = w(0,      pz)   # eave corner at x=0
            c1  = w(x,      pz)   # eave corner at x=x
            ap  = w(x / 2,  pz)   # apex

        vertices = [
            (c0[0], y0, c0[1]),   # v0 – eave corner 1 (wall-plate level)
            (c1[0], y0, c1[1]),   # v1 – eave corner 2 (wall-plate level)
            (ap[0], y1, ap[1]),   # v2 – apex (ridge level)
        ]

        # Two triangles: opposite windings → double-sided panel
        indices = [
            (0, 1, 2),  # outward-facing winding
            (0, 2, 1),  # inward-facing  winding
        ]

        face_groups = {
            'wall': [0, 1],
            'all':  [0, 1],
        }

        return vertices, indices, face_groups


class GreenhouseGeometry3D(Generate3DMixin):
    """
    3D geometry for a greenhouse: four glass walls plus a gable glass roof.

    The walls extend from v_anchor to v_anchor + height.
    The gable roof apex sits at v_anchor + height + roof_height.
    The ridge runs along the longer plan dimension (x_axis_size when x >= z).

    Uses element properties:
        - anchor_point, x_axis_size, z_axis_size, orientation_angle
        - v_anchor, height          (wall base and wall height)
        - roof_height               (additional height from wall-top to ridge apex)

    Face groups:
        'walls'  – 8 triangles (4 wall quads)
        'roof'   – 6 triangles (2 slopes + 2 gable ends)
        'all'    – all 14 triangles
    """

    def generate_vertices_and_indices(
        self,
    ) -> tuple[list[tuple[float, float, float]],
               list[tuple[int, int, int]],
               dict[str, list[int]]]:

        x   = self.x_axis_size
        z   = self.z_axis_size
        y0  = self.v_anchor            # bottom of walls
        y1  = self.v_anchor + self.height  # top of walls / base of roof
        rh  = getattr(self, 'roof_height', 1.2) or 1.2
        y2  = y1 + rh                  # roof apex
        ax0, az0 = self.anchor_point
        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point((ax0, az0), lx, lz, angle_rad)

        c0 = w(0, 0);  c1 = w(x, 0);  c2 = w(x, z);  c3 = w(0, z)

        # v0-v3: base corners (y0), v4-v7: wall-top corners (y1)
        vertices = [
            (c0[0], y0, c0[1]),   # v0  base  front-left
            (c1[0], y0, c1[1]),   # v1  base  front-right
            (c2[0], y0, c2[1]),   # v2  base  back-right
            (c3[0], y0, c3[1]),   # v3  base  back-left
            (c0[0], y1, c0[1]),   # v4  wall-top front-left
            (c1[0], y1, c1[1]),   # v5  wall-top front-right
            (c2[0], y1, c2[1]),   # v6  wall-top back-right
            (c3[0], y1, c3[1]),   # v7  wall-top back-left
        ]

        # Ridge vertices v8, v9
        if x >= z:
            r0 = w(0, z / 2);  r1 = w(x, z / 2)   # ridge along x
        else:
            r0 = w(x / 2, 0);  r1 = w(x / 2, z)   # ridge along z
        vertices.append((r0[0], y2, r0[1]))   # v8
        vertices.append((r1[0], y2, r1[1]))   # v9

        indices: list[tuple[int, int, int]] = []
        face_groups: dict[str, list[int]] = {}

        # ─── Walls (8 triangles, same winding as RectangularGeometry3D) ──────
        # Front (-z), Back (+z), Left (-x), Right (+x)
        wall_tris = [
            (0, 5, 1), (0, 4, 5),   # front wall
            (2, 7, 3), (2, 6, 7),   # back wall
            (3, 4, 0), (3, 7, 4),   # left wall
            (1, 6, 2), (1, 5, 6),   # right wall
        ]
        indices.extend(wall_tris)
        face_groups['walls'] = list(range(len(wall_tris)))

        # ─── Roof (6 triangles) ──────────────────────────────────────────────
        if x >= z:
            # Ridge along x (at z_mid); v8=left ridge, v9=right ridge
            # Front slope faces –z/up, back slope faces +z/up,
            # gable ends face ±x.
            roof_tris = [
                (4, 8, 9), (4, 9, 5),   # front slope  (–z / up)
                (6, 9, 7), (7, 9, 8),   # back slope   (+z / up)
                (4, 7, 8),              # left  gable end (–x)
                (5, 9, 6),              # right gable end (+x)
            ]
        else:
            # Ridge along z (at x_mid); v8=front ridge, v9=back ridge
            roof_tris = [
                (4, 7, 9), (4, 9, 8),   # left slope  (–x / up)
                (5, 8, 9), (5, 9, 6),   # right slope (+x / up)
                (4, 8, 5),              # front gable end (–z)
                (7, 6, 9),              # back  gable end (+z)
            ]
        i0 = len(indices)
        indices.extend(roof_tris)
        face_groups['roof'] = list(range(i0, i0 + len(roof_tris)))

        face_groups['all'] = list(range(len(indices)))
        return vertices, indices, face_groups


class HippedRoofGeometry3D(Generate3DMixin):
    """
    3D geometry for a hipped roof.

    All four sides slope toward the centre.  When the plan is square the roof
    degenerates to a pyramid (single apex).  When the plan is rectangular, a
    short ridge runs along the longer dimension and four trapezoidal/triangular
    hip faces slope down to the eaves.  No bottom face.

    Uses the same element properties as GableRoofGeometry3D.
    """

    _RIDGE_MIN = 0.05   # treat ridge as pyramid when shorter than this (m)

    def generate_vertices_and_indices(
        self,
    ) -> tuple[list[tuple[float, float, float]],
               list[tuple[int, int, int]],
               dict[str, list[int]]]:
        """Generate hipped roof geometry, no bottom."""

        x = self.x_axis_size
        z = self.z_axis_size
        y0 = self.v_anchor
        y1 = self.v_anchor + self.height
        ax0, az0 = self.anchor_point
        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point((ax0, az0), lx, lz, angle_rad)

        # Four base corners (shared by all cases)
        c0 = w(0, 0)
        c1 = w(x, 0)
        c2 = w(x, z)
        c3 = w(0, z)

        base_verts = [
            (c0[0], y0, c0[1]),   # v0
            (c1[0], y0, c1[1]),   # v1
            (c2[0], y0, c2[1]),   # v2
            (c3[0], y0, c3[1]),   # v3
        ]

        if x >= z:
            hip_depth = z / 2
            ridge_len  = x - 2 * hip_depth      # = x - z
        else:
            hip_depth = x / 2
            ridge_len  = z - 2 * hip_depth      # = z - x

        if ridge_len < self._RIDGE_MIN:
            # ── Pyramid ──────────────────────────────────────────────────
            apex = w(x / 2, z / 2)
            vertices = base_verts + [(apex[0], y1, apex[1])]  # v4 = apex

            # Four triangular faces (outward normals away from interior)
            # Front  (plan-z=0): v0, v1, apex
            # Right  (plan-x=x): v1, v2, apex
            # Back   (plan-z=z): v2, v3, apex
            # Left   (plan-x=0): v3, v0, apex
            indices = [
                (0, 1, 4),   # front
                (1, 2, 4),   # right
                (2, 3, 4),   # back
                (3, 0, 4),   # left
            ]
            face_groups = {
                'front': [0], 'right': [1], 'back': [2], 'left': [3],
                'all':   [0, 1, 2, 3],
            }
        else:
            # ── True hipped (elongated) ───────────────────────────────────
            if x >= z:
                # Ridge runs along X; hip triangles at left and right ends
                rx0 = hip_depth          # ridge start x
                rx1 = x - hip_depth      # ridge end   x
                r0 = w(rx0, z / 2)
                r1 = w(rx1, z / 2)
            else:
                # Ridge runs along Z; hip triangles at front and back ends
                rz0 = hip_depth
                rz1 = z - hip_depth
                r0 = w(x / 2, rz0)
                r1 = w(x / 2, rz1)

            # v0–v3: base, v4: near ridge end, v5: far ridge end
            vertices = base_verts + [
                (r0[0], y1, r0[1]),   # v4
                (r1[0], y1, r1[1]),   # v5
            ]

            if x >= z:
                # Ridge along X
                # Front slope  (plan-z=0): trapezoid v0–v1–v5–v4
                # Back slope   (plan-z=z): trapezoid v3–v4–v5–v2
                # Left hip     (plan-x=0): triangle  v0–v3–v4
                # Right hip    (plan-x=x): triangle  v1–v5–v2
                indices = [
                    (0, 4, 5), (0, 5, 1),   # front slope
                    (2, 5, 3), (3, 5, 4),   # back slope
                    (0, 3, 4),              # left  hip
                    (1, 5, 2),              # right hip
                ]
                face_groups = {
                    'front_slope': [0, 1],
                    'back_slope':  [2, 3],
                    'left_hip':    [4],
                    'right_hip':   [5],
                    'slopes':      [0, 1, 2, 3],
                    'hips':        [4, 5],
                    'all':         [0, 1, 2, 3, 4, 5],
                }
            else:
                # Ridge along Z
                # Left slope   (plan-x=0): trapezoid v0–v3–v5–v4
                # Right slope  (plan-x=x): trapezoid v1–v4–v5–v2
                # Front hip    (plan-z=0): triangle  v0–v4–v1
                # Back hip     (plan-z=z): triangle  v3–v2–v5
                indices = [
                    (0, 3, 5), (0, 5, 4),   # left  slope
                    (1, 4, 5), (1, 5, 2),   # right slope
                    (0, 4, 1),              # front hip
                    (3, 2, 5),              # back  hip
                ]
                face_groups = {
                    'left_slope':  [0, 1],
                    'right_slope': [2, 3],
                    'front_hip':   [4],
                    'back_hip':    [5],
                    'slopes':      [0, 1, 2, 3],
                    'hips':        [4, 5],
                    'all':         [0, 1, 2, 3, 4, 5],
                }

        # Flat vertical y_shift = roof_thickness (see GableRoof comment).
        thickness = getattr(self, 'roof_thickness', 0.4) or 0.4
        vertices, indices, face_groups = _add_roof_inner_surface(vertices, indices, face_groups, thickness)
        return vertices, indices, face_groups


__all__ = [
    'Generate3DMixin',
    'RectangularGeometry3D',
    'CircularGeometry3D',
    'GableRoofGeometry3D',
    'HippedRoofGeometry3D',
    'SingleSlopeRoofGeometry3D',
    'HippedRoofOctantGeometry3D',
    'HippedInternalOctantGeometry3D',
    'GreenhouseGeometry3D',
    'GableEndWallGeometry3D',
    'is_3d_eligible',
]
