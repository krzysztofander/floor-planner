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

class GableRoofGeometry3D(Generate3DMixin):
    """
    3D geometry for a gable roof.

    Two sloping rectangular faces meet at a ridge; the two short ends are solid
    triangular gable walls.  No bottom face (open underneath).

    Ridge runs along the longer plan dimension.  When both dimensions are equal
    the ridge runs along X (x_axis_size direction).

    Uses element properties:
        - anchor_point (x, z) - bottom-left corner in 2D floor plan
        - x_axis_size  - horizontal plan dimension (left/right)
        - z_axis_size  - vertical plan dimension (up/down)
        - orientation_angle
        - v_anchor  - Y coordinate of the roof base (eaves)
        - height    - ridge height above v_anchor
    """

    def generate_vertices_and_indices(
        self,
    ) -> tuple[list[tuple[float, float, float]],
               list[tuple[int, int, int]],
               dict[str, list[int]]]:
        """Generate gable roof: 6 vertices, 6 triangles, no bottom."""

        x = self.x_axis_size
        z = self.z_axis_size
        y0 = self.v_anchor
        y1 = self.v_anchor + self.height
        ax0, az0 = self.anchor_point
        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            """Local plan coords → world (x, z) pair."""
            return rotate_point((ax0, az0), lx, lz, angle_rad)

        # Four base (eave) corners
        c0 = w(0, 0)
        c1 = w(x, 0)
        c2 = w(x, z)
        c3 = w(0, z)

        if x >= z:
            # Ridge runs along the X direction, at plan-z = z/2
            r0 = w(0,   z / 2)   # left  ridge end
            r1 = w(x,   z / 2)   # right ridge end
        else:
            # Ridge runs along the Z direction, at plan-x = x/2
            r0 = w(x / 2, 0)     # front ridge end
            r1 = w(x / 2, z)     # back  ridge end

        # Vertex list
        # v0–v3: base corners (y = y0)
        # v4:    near  ridge end (y = y1)
        # v5:    far   ridge end (y = y1)
        vertices = [
            (c0[0], y0, c0[1]),   # v0
            (c1[0], y0, c1[1]),   # v1
            (c2[0], y0, c2[1]),   # v2
            (c3[0], y0, c3[1]),   # v3
            (r0[0], y1, r0[1]),   # v4
            (r1[0], y1, r1[1]),   # v5
        ]

        if x >= z:
            # Ridge along X  →  gable ends at plan-x = 0 (left) and plan-x = x (right)
            #
            #   v3 -------- v2          (base, back)
            #   |    v4---v5  |  <-- ridge at y1
            #   v0 -------- v1          (base, front)
            #
            # Front slope  (plan-z=0 face, outward normal toward –z_3d):
            #   Quad v0–v1–v5–v4  →  (v0,v4,v5) + (v0,v5,v1)
            # Back slope   (plan-z=z face, outward normal toward +z_3d):
            #   Quad v3–v4–v5–v2  →  (v3,v2,v5) + (v3,v5,v4)  ← wait need to verify
            # Left gable   (plan-x=0, outward normal toward –x):
            #   Triangle v0–v3–v4
            # Right gable  (plan-x=x, outward normal toward +x):
            #   Triangle v1–v5–v2
            indices = [
                (0, 4, 5), (0, 5, 1),   # front slope
                (2, 5, 3), (3, 5, 4),   # back slope
                (0, 3, 4),              # left gable
                (1, 5, 2),              # right gable
            ]
            face_groups = {
                'front_slope': [0, 1],
                'back_slope':  [2, 3],
                'left_gable':  [4],
                'right_gable': [5],
                'slopes':      [0, 1, 2, 3],
                'gables':      [4, 5],
                'all':         [0, 1, 2, 3, 4, 5],
            }
        else:
            # Ridge along Z  →  gable ends at plan-z=0 (front) and plan-z=z (back)
            #
            #   v3 ---- v5(top) ---- v2   (back base + back ridge)
            #   |                    |
            #   v0 ---- v4(top) ---- v1   (front base + front ridge)
            #
            # Left slope   (plan-x=0 side):  v0–v3–v5–v4
            # Right slope  (plan-x=x side):  v1–v4–v5–v2
            # Front gable  (plan-z=0):       v0–v4–v1
            # Back gable   (plan-z=z):       v3–v2–v5  (outward +z)
            indices = [
                (0, 3, 5), (0, 5, 4),   # left slope
                (1, 4, 5), (1, 5, 2),   # right slope
                (0, 4, 1),              # front gable
                (3, 2, 5),              # back gable
            ]
            face_groups = {
                'left_slope':  [0, 1],
                'right_slope': [2, 3],
                'front_gable': [4],
                'back_gable':  [5],
                'slopes':      [0, 1, 2, 3],
                'gables':      [4, 5],
                'all':         [0, 1, 2, 3, 4, 5],
            }

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

        return vertices, indices, face_groups


# Export public API
__all__ = [
    'Generate3DMixin',
    'RectangularGeometry3D',
    'CircularGeometry3D',
    'GableRoofGeometry3D',
    'HippedRoofGeometry3D',
    'is_3d_eligible',
]
