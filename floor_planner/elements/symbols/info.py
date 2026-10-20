"""
Draw elements that do not represent any real objects, but provide info about them.

Author: Nikolay Lysenko
"""


import math

import matplotlib.axes
import numpy as np
from matplotlib.patches import Polygon

from ..element import Element
from ..vertical_levels import VertInfoAnnotations
from ...utils import renderDim


class DimensionArrow(VertInfoAnnotations, Element):
    """Dimension arrow."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            orientation_angle: float = 0,
            width: int = 0.01,
            tip_length: float = 0.1,
            font_size: int = 10,
            annotate_above: bool = False,
            color: str = 'black',
            label: str | None = None,
            id: str | None = None,
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates (in meters) of anchor point;
            the leftmost point is anchor point if `orientation_angle == 0`
        :param length:
            length of the wall (in meters); this value is also placed to annotation
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the arrow;
            it is measured between X-axis and the arrow in positive direction (counterclockwise);
            initial arrow is rotated around anchor point to get the desired orientation
        :param width:
            width of lines (in meters before scaling)
        :param tip_length:
            length of single arrow tip (in meters before scaling)
        :param font_size:
            font size
        :param annotate_above:
            if it is set to `True`, annotation is placed above the arrow (prior to its rotation)
        :param color:
            color to use for drawing the arrow and its annotation
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :return:
            freshly created instance of `DimensionArrow` class
        """
        super().__init__(anchor_point=anchor_point, label=label, id=id, color=color)
        self.length = length
        self.orientation_angle = orientation_angle
        self.width = width
        self.tip_length = tip_length
        self.font_size = font_size
        self.annotate_above = annotate_above

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw dimension arrow."""
        tip_angle = math.radians(30)
        initial_vertices = np.array([
            [0, 0],
            [
                self.tip_length - math.sin(tip_angle) * self.width,
                math.tan(tip_angle) * (self.tip_length - math.sin(tip_angle) * self.width)
            ],
            [
                self.tip_length,
                math.tan(tip_angle) * (self.tip_length - math.sin(tip_angle) * self.width)
                - math.cos(tip_angle) * self.width
            ],
            [
                self.width / 2 / math.tan(tip_angle) + self.width / math.sin(tip_angle),
                self.width / 2
            ],
            [
                self.length
                - self.width / 2 / math.tan(tip_angle) - self.width / math.sin(tip_angle),
                self.width / 2
            ],
            [
                self.length - self.tip_length,
                math.tan(tip_angle) * (self.tip_length - math.sin(tip_angle) * self.width)
                - math.cos(tip_angle) * self.width
            ],
            [
                self.length - self.tip_length + math.sin(tip_angle) * self.width,
                math.tan(tip_angle) * (self.tip_length - math.sin(tip_angle) * self.width)
            ],
            [self.length, 0],
            [
                self.length - self.tip_length + math.sin(tip_angle) * self.width,
                -math.tan(tip_angle) * (self.tip_length - math.sin(tip_angle) * self.width)
            ],
            [
                self.length - self.tip_length,
                -math.tan(tip_angle) * (self.tip_length - math.sin(tip_angle) * self.width)
                + math.cos(tip_angle) * self.width
            ],
            [
                self.length
                - self.width / 2 / math.tan(tip_angle) - self.width / math.sin(tip_angle),
                -self.width / 2
            ],
            [
                self.width / 2 / math.tan(tip_angle) + self.width / math.sin(tip_angle),
                -self.width / 2
            ],
            [
                self.tip_length,
                -math.tan(tip_angle) * (self.tip_length - math.sin(tip_angle) * self.width)
                + math.cos(tip_angle) * self.width
            ],
            [
                self.tip_length - math.sin(tip_angle) * self.width,
                -math.tan(tip_angle) * (self.tip_length - math.sin(tip_angle) * self.width)
            ],
        ])
        rotation_angle = math.radians(self.orientation_angle)
        rotation_matrix = np.array([
            [math.cos(rotation_angle), -math.sin(rotation_angle)],
            [math.sin(rotation_angle), math.cos(rotation_angle)],
        ])
        rotated_vertices = np.dot(rotation_matrix, initial_vertices.T).T
        shift_vector = np.array([[self.anchor_point[0], self.anchor_point[1]]])
        vertices = rotated_vertices + shift_vector
        arrow = Polygon(vertices, facecolor=self.color)
        arrow.set_zorder(self.get_zorder())
        ax.add_patch(arrow)

        initial_text_center = [
            self.length / 2,
            (self.font_size * 0.0125 if self.annotate_above else -self.font_size * 0.0125)
        ]

        text_elevation = (self.font_size * 0.0125 if self.annotate_above else -self.font_size * 0.0125)

        text = str(round(self.length,3))
        renderDim(ax,
                self.anchor_point,
                text,
                self.length,
                self.orientation_angle,
                self.font_size,
                text_elevation,
                self.color)
                  


class TextBox(VertInfoAnnotations, Element):
    """Text box."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            lines: list[str],
            font_size: int = 10,
            color: str = 'black',
            transparency: float = 0.75,
            edgecolor: str = 'black',
            label: str | None = None,
            id: str | None = None,
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates (in meters) of anchor point; the center of a text box is its anchor point
        :param lines:
            text lines to be printed
        :param font_size:
            font size
        :param color:
            color to use for drawing the text and the bounding box
        :param transparency:
            transparency of the bounding box
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        """
        super().__init__(label=label, id=id, anchor_point=anchor_point, color=color)
        self.lines = lines
        self.font_size = font_size
        self.transparency = transparency
        self.edgecolor = edgecolor

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw text box."""
        ax.text(
            self.anchor_point[0],
            self.anchor_point[1],
            '\n'.join(self.lines),
            verticalalignment='center',
            horizontalalignment='center',
            color = self.color,
            fontsize = self.font_size,
            bbox={'boxstyle': 'round', 'facecolor': 'white', 'alpha': self.transparency, 'edgecolor': self.edgecolor}
        )
