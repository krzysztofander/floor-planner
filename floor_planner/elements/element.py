"""
Define abstract element.

Author: Nikolay Lysenko
"""


from abc import ABC, abstractmethod

import matplotlib.axes

from .options import generate_element_id, get_show_invisible

from ..utils import rotate_point
import math



class Element(ABC):
    """Abstract element."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            color: tuple[int, int, int] | str | None = None,
            label: str | None = None,
            id: str | None = None
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
        """
        self.anchor_point = anchor_point
        self.color = color
        self.label = label
        # Generate unique ID based on class name and label, or use provided ID
        self.id = id if id else generate_element_id(self.__class__.__name__, label)

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

    @abstractmethod
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the element."""
        pass

class RectangularElement(Element):
    """Element with rectangular shape (line-like or 3D with thickness)."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float,
            length: float,
            thickness: float,
            color: tuple[int, int, int] | str | None = None,
            label: str | None = None,
            id: str | None = None
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
        """
        super().__init__(anchor_point=anchor_point, color=color, label=label, id=id)
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
    """Element with rectangular surface area (2D plane with length × width)."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float,
            length: float,
            width: float,
            color: tuple[int, int, int] | str | None = None,
            label: str | None = None,
            id: str | None = None
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
            primary dimension (first face) in meters
        :param width:
            second face dimension in meters (for decks, paths, lawns, pools)
        :param color:
            color for rendering as RGB tuple or string; 'invisible' for hidden elements
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        """
        # Pass width as thickness to parent for geometry calculations
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=width,  # width maps to thickness for geometry
            color=color,
            label=label,
            id=id
        )
        # Expose width as semantic property for clarity
        self.width = width

    @abstractmethod
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the element."""
        pass


class CircularElement(Element):
    """Element with circular shape (anchor_point is center)."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            diameter: float,
            color: tuple[int, int, int] | str | None = None,
            label: str | None = None,
            id: str | None = None
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
        """
        super().__init__(anchor_point=anchor_point, color=color, label=label, id=id)
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
