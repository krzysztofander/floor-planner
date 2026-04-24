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

    def __init__(self, label: str | None = None):
        """
        Initialize an instance.

        :param label:
            optional label for the element
        """
        self.label = label
        # Generate unique ID based on class name and label
        self.id = generate_element_id(self.__class__.__name__, label)

    @abstractmethod
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the element."""
        pass

class RectangularElement(Element):
    """Element with rectangular shape."""

    def __init__(self, label: str | None = None):
        """
        Initialize an instance.

        :param label:
            optional label for the element
        """
        super().__init__(label=label)

    def get_draw_color(self) -> str | None:
        """
        Get the color to use for drawing, handling invisible elements.

        :return:
            color string to use for drawing, 'red' if element is invisible and show_invisible is True,
            or None if element is invisible and should not be drawn
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
