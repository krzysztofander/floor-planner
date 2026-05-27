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

from ..utils import rotate_point

if TYPE_CHECKING:
    from .element import Element


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
    from .info import DimensionArrow, TextBox
    from ..floor_plan import Room
    
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
        
        # Get geometric offset for z-fighting prevention
        # Elements with higher v_anchor (windows, doors) protrude from walls
        offset = 0.0
        if hasattr(self, '_get_geometric_offset'):
            offset = self._get_geometric_offset()
        
        # Apply offset to dimensions (makes element slightly larger in X and Z)
        length_with_offset = self.length + offset
        thickness_with_offset = self.thickness + offset
        
        # Get bottom corners in 2D (before rotation)
        # Rectangular elements: length along X, thickness along Z
        # Centered offset: extend equally on both sides
        offset_half = offset / 2
        local_corners = [
            (-offset_half, -offset_half),                                    # bottom-left
            (length_with_offset - offset_half, -offset_half),               # bottom-right
            (length_with_offset - offset_half, thickness_with_offset - offset_half),  # top-right
            (-offset_half, thickness_with_offset - offset_half)             # top-left
        ]
        
        # Rotate corners around anchor point
        rotated_corners = self._rotate_corners(local_corners, self.anchor_point, 
                                               self.orientation_angle)
        
        # Generate 3D vertices
        vertices = []
        
        # Bottom face (Y = v_anchor)
        for x, z in rotated_corners:
            vertices.append((x, self.v_anchor, z))
        
        # Top face (Y = v_anchor + height)
        for x, z in rotated_corners:
            vertices.append((x, self.v_anchor + self.height, z))
        
        # Generate triangle indices for 6 faces (12 triangles total)
        # Indices are 0-based relative to this element's vertices
        indices = []
        face_groups = {}
        
        # Bottom face (indices 0-3) - looking down, counterclockwise
        bottom_tris = [
            (0, 2, 1),  # triangle 1
            (0, 3, 2)   # triangle 2
        ]
        indices.extend(bottom_tris)
        face_groups['bottom'] = [0, 1]
        
        # Top face (indices 4-7) - looking up, clockwise
        top_tris = [
            (4, 5, 6),  # triangle 1
            (4, 6, 7)   # triangle 2
        ]
        indices.extend(top_tris)
        face_groups['top'] = [2, 3]
        
        # Front face (bottom edge closest to origin)
        front_tris = [
            (0, 1, 5),  # triangle 1
            (0, 5, 4)   # triangle 2
        ]
        indices.extend(front_tris)
        face_groups['front'] = [4, 5]
        
        # Back face
        back_tris = [
            (2, 3, 7),  # triangle 1
            (2, 7, 6)   # triangle 2
        ]
        indices.extend(back_tris)
        face_groups['back'] = [6, 7]
        
        # Right face
        right_tris = [
            (1, 2, 6),  # triangle 1
            (1, 6, 5)   # triangle 2
        ]
        indices.extend(right_tris)
        face_groups['right'] = [8, 9]
        
        # Left face
        left_tris = [
            (3, 0, 4),  # triangle 1
            (3, 4, 7)   # triangle 2
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
        
        # Get geometric offset for z-fighting prevention
        offset = 0.0
        if hasattr(self, '_get_geometric_offset'):
            offset = self._get_geometric_offset()
        
        center_x, center_z = self.anchor_point
        # Apply offset to radius (makes cylinder slightly larger)
        radius = (self.diameter + offset) / 2
        
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
        
        # Bottom cap triangles (fan from center)
        bottom_tris = []
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.append((bottom_center_idx, next_i, i))
            bottom_tris.append(triangle_idx)
            triangle_idx += 1
        face_groups['bottom'] = bottom_tris
        
        # Top cap triangles (fan from center)
        top_tris = []
        for i in range(segments):
            next_i = (i + 1) % segments
            indices.append((top_center_idx, segments + i, segments + next_i))
            top_tris.append(triangle_idx)
            triangle_idx += 1
        face_groups['top'] = top_tris
        
        # Side faces (2 triangles per segment)
        sides_tris = []
        for i in range(segments):
            next_i = (i + 1) % segments
            
            # Triangle 1: bottom[i], bottom[next], top[next]
            indices.append((i, next_i, segments + next_i))
            sides_tris.append(triangle_idx)
            triangle_idx += 1
            
            # Triangle 2: bottom[i], top[next], top[i]
            indices.append((i, segments + next_i, segments + i))
            sides_tris.append(triangle_idx)
            triangle_idx += 1
        
        face_groups['sides'] = sides_tris
        face_groups['all'] = list(range(len(indices)))
        
        return vertices, indices, face_groups


class SurfaceGeometry3D(RectangularGeometry3D):
    """
    3D geometry generation for surface elements (lawns, paths, decks, floors).
    
    Surface elements use 'width' instead of 'thickness' for semantic clarity,
    but the 3D geometry generation is identical to RectangularGeometry3D.
    
    Note: Surface elements still have height > 0 to be rendered as 3D objects:
        - Lawn: 0.05m (grass height)
        - Path: 0.02m (paving thickness)
        - Deck: 0.3m (elevated platform height)
    
    The parent class SurfaceElement already maps width → thickness internally,
    so this mixin works exactly like RectangularGeometry3D.
    """
    pass  # Inherits all functionality from RectangularGeometry3D


# Export public API
__all__ = [
    'Generate3DMixin',
    'RectangularGeometry3D',
    'CircularGeometry3D',
    'SurfaceGeometry3D',
    'is_3d_eligible',
]
