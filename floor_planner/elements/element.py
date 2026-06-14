"""
Define abstract element.

Author: Nikolay Lysenko
"""


from abc import ABC, abstractmethod

import matplotlib.axes

from ..options import generate_element_id, get_show_invisible
from ..geometry_3d import RectangularGeometry3D, CircularGeometry3D

from ..utils import rotate_point
import math

class ElementBase(ABC):

    def __init__(self):
        self._elList: list[ElementBase] = []

    def addToList(self, element: 'ElementBase') -> None:
        self._elList.append(element)

    def getList(self) -> list['ElementBase']:
        return self._elList
    
    def isList(self) -> bool:
        return len(self._elList) > 0
    
    @abstractmethod
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the element."""
        pass

    @abstractmethod
    def get_id(self) -> str:
        """Get the element ID."""
        pass    

class Element(ElementBase):
    """Abstract element."""

    # Class-level counter for ensuring unique v_anchor values
    _element_counter: int = 0

    def __init__(
            self,
            anchor_point: tuple[float, float],
            color:  str,
            label: str | None = None,
            id: str | None = None,
            v_anchor: float | None = None,
            height: float | None = None,
            texture_scale: float | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            optional coordinates (x, y) in meters; meaning varies by element type
            (e.g., bottom-left for rectangles, center for circles);
            None for elements that use alternative positioning (Line, Polygon)
        :param color:
            color for rendering as RGB tuple or string; 'invisible' for hidden elements
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :param v_anchor:
            optional vertical anchor point in meters (height above floor/ground);
            if None, uses element's default from _default_v_anchor();
            used for z-ordering in 2D rendering and future 3D positioning
        :param height:
            optional physical height of element in meters;
            if None, uses element's default from _default_height();
            used for semantic meaning and future 3D rendering
        :param texture_scale:
            optional texture tiling scale in meters (for 3D export only);
            if set, texture repeats every N meters instead of stretching to fit;
            examples: 0.1 (fine), 0.2 (medium), 0.5 (large tiles);
            if None, texture stretches to fit entire surface (default)
        """
        super().__init__()

        self.anchor_point = anchor_point
        self.color = color
        self.label = label
        # Generate unique ID based on class name and label, or use provided ID
        self._id = id if id else generate_element_id(self.__class__.__name__, label)
        # Room association (set by Room class when element is part of a room)
        self.room_id: str | None = None
        
        # Vertical positioning with element counter for unique v_anchor
        base_v_anchor = v_anchor if v_anchor is not None else self._default_v_anchor()
        
        # Increment class counter for this instance
        Element._element_counter += 1
        self._element_instance_number = Element._element_counter
        
        # Add tiny offset to ensure unique v_anchor for deterministic ordering
        # 0.0001 per element ensures no collisions while keeping semantic meaning
        self.v_anchor = base_v_anchor + (0.0001 * self._element_instance_number)
        
        # Physical height
        self.height = height if height is not None else self._default_height()
        
        # 3D texture specification
        self.texture_scale = texture_scale

    def get_id(self) -> str:
        """Get the element ID."""
        return self._id

    def get_draw_color(self) -> str | tuple[int, int, int] | None:
        """
        Get the color to use for drawing, handling invisible elements.

        :return:
            color string or RGB tuple to use for drawing, 'red' if element is invisible
            and show_invisible is True, or None if element is invisible and should not be drawn
        """
        if self.color == 'invisible':
            if not get_show_invisible():
                return None
            return 'red'
        return self.color

    def _default_v_anchor(self) -> float:
        """
        Get default vertical anchor for this element type.
        
        Override in subclass or use VertInfo mixin for standard levels.
        Base implementation returns 0.0 (floor/ground level).
        
        :return:
            vertical anchor in meters (height above floor/ground)
        """
        return 0.0

    def _default_height(self) -> float:
        """
        Get default physical height for this element type.
        
        Override in subclass to specify element height.
        Base implementation returns 0.0 (no height/point element).
        
        :return:
            element height in meters
        """
        return 0.0

    def get_zorder(self) -> float:
        """
        Calculate matplotlib zorder based on v_anchor.
        
        Returns v_anchor directly - matplotlib accepts float zorder values.
        Element counter offset ensures unique zorder for every element,
        providing deterministic drawing order.
        
        :return:
            zorder value for matplotlib (v_anchor with counter offset)
        """
        return self.v_anchor

    @abstractmethod
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the element."""
        pass

class RectangularElement(RectangularGeometry3D, Element):
    """Element with rectangular shape (line-like or 3D with thickness).
    
    Inherits 3D geometry generation from RectangularGeometry3D mixin.
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float,
            length: float,
            thickness: float,
            color:  str | None = None,
            label: str | None = None,
            id: str | None = None,
            v_anchor: float | None = None,
            height: float | None = None,
            texture_scale: float | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates (x, y) in meters; bottom-left corner of rectangle
        :param orientation_angle:
            angle (in degrees) that specifies orientation;
            measured between X-axis and the element in positive direction (counterclockwise);
            initial element is rotated around anchor point to get the desired orientation
        :param length:
            primary dimension (front face width) in meters
        :param thickness:
            perpendicular/depth dimension in meters (for walls, furniture depth, etc.)
        :param color:
            color for rendering as RGB tuple or string; 'invisible' for hidden elements
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :param v_anchor:
            optional vertical anchor point in meters; if None, uses default
        :param height:
            optional physical height in meters; if None, uses default
        :param texture_scale:
            optional texture tiling scale in meters; if set, texture repeats every N meters
        """
        super().__init__(
            anchor_point=anchor_point,
            color=color,
            label=label,
            id=id,
            v_anchor=v_anchor,
            height=height,
            texture_scale=texture_scale
        )
        self.orientation_angle = orientation_angle
        self.length = length
        self.thickness = thickness

    @abstractmethod
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the element."""
        pass

    def get_corners(self) -> list[tuple[float, float]]:
        """
        Get corners of the rectangle.

        :return:
             list of 4 (x, y) tuples representing corners in order:
             bottom-left, bottom-right, top-right, top-left (before rotation)
        """
        # Define corners relative to anchor point (anchor is bottom-left)
        corners_relative = [
            (0, 0),                         # bottom-left (anchor)
            (self.length, 0),               # bottom-right
            (self.length, self.thickness),  # top-right
            (0, self.thickness)             # top-left
        ]
        corners = []
        for corner in corners_relative:
            corners.append(rotate_point(
                self.anchor_point,
                corner[0],
                corner[1],
                math.radians(self.orientation_angle)
            ))

        return corners


class SurfaceElement(RectangularElement):
    """Element with rectangular surface area (2D plane with length × width).
    
    Inherits 3D geometry generation from RectangularElement (via RectangularGeometry3D mixin).
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float,
            size: tuple[float, float],
            color: str | None = None,
            label: str | None = None,
            id: str | None = None,
            v_anchor: float | None = None,
            height: float | None = None,
            texture_scale: float | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates (x, y) in meters; bottom-left corner of rectangle
        :param orientation_angle:
            angle (in degrees) that specifies orientation;
            measured between X-axis and the element in positive direction (counterclockwise);
            initial element is rotated around anchor point to get the desired orientation
        :param size:
            (x_size, z_size) tuple in meters; x_size is the left/right dimension (2D),
            z_size is the up/down dimension (2D)
        :param color:
            color for rendering as RGB tuple or string; 'invisible' for hidden elements
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :param v_anchor:
            optional vertical anchor point in meters; if None, uses default
        :param height:
            optional physical height in meters; if None, uses default
        :param texture_scale:
            optional texture tiling scale in meters; if set, texture repeats every N meters
        """
        # Pass width as thickness to parent for geometry calculations
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=size[0],    # size[0] maps to length (X axis, left/right)
            thickness=size[1],  # size[1] maps to thickness (Z axis, up/down)
            color=color,
            label=label,
            id=id,
            v_anchor=v_anchor,
            height=height,
            texture_scale=texture_scale
        )
        # Expose as semantic properties for clarity
        self.x_axis_size = size[0]  # Primary dimension along X axis
        self.z_axis_size = size[1]  # Secondary dimension along Z axis

        # Cancel width so it is not accidentally used
        self.width = None   

    @abstractmethod
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the element."""
        pass


class CircularElement(CircularGeometry3D, Element):
    """Element with circular shape (anchor_point is center).
    
    Inherits 3D geometry generation from CircularGeometry3D mixin.
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            diameter: float,
            color: str | None = None,
            label: str | None = None,
            id: str | None = None,
            v_anchor: float | None = None,
            height: float | None = None,
            texture_scale: float | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates (x, y) in meters; center point of the circle
        :param diameter:
            circle diameter in meters
        :param color:
            color for rendering as RGB tuple or string; 'invisible' for hidden elements
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :param v_anchor:
            optional vertical anchor point in meters; if None, uses default
        :param height:
            optional physical height in meters; if None, uses default
        :param texture_scale:
            optional texture tiling scale in meters; if set, texture repeats every N meters
        """
        super().__init__(
            anchor_point=anchor_point,
            color=color,
            label=label,
            id=id,
            v_anchor=v_anchor,
            height=height,
            texture_scale=texture_scale
        )
        self.diameter = diameter

    @property
    def radius(self) -> float:
        """
        Get circle radius.

        :return:
            radius in meters (diameter / 2)
        """
        return self.diameter / 2

    @abstractmethod
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the element."""
        pass
