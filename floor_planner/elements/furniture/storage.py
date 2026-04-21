"""
Draw storage furniture elements

Author: Krzysztof Bartczak
"""


import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle

from ...utils import rotate_point, render_label_and_id, text_readability_rotation
from ..element import Element, RectangularElement
from ..info import DimensionArrow
from ..options import get_dimensions, get_element_option, get_show_invisible


class GenericStorage(RectangularElement):
    """
    Storage box

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            thickness: float,
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param length:
            length of the storage box (in meters)
        :param thickness:
            thickness of the storage box (in meters)
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the storage box;
            it is measured between X-axis and the storage box in positive direction (counterclockwise);
            initial storage box is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the storage box
        :param label:
            optional label for the element
        :param room_edge:
            if True, this storage box forms the boundary of a room (used for room validation and calculations)
        :return:
            freshly created instance of `GenericStorage` class
        """
        super().__init__(label=label)
        self.anchor_point = anchor_point
        self.length = length
        self.thickness = thickness
        self.orientation_angle = orientation_angle
        self.color = color

        # Room properties (set by Room class if this storage box is part of a room)
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw storage box."""
        # Check if storage box is invisible
        if self.color == 'invisible':
            # Skip drawing if show_invisible is not enabled
            if not get_show_invisible():
                return
            # Draw in red if show_invisible is enabled
            draw_color = 'red'
        else:
            draw_color = self.color

        linewidth = self.thickness * 3

        patch = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor=draw_color,
            fill=False,
            edgecolor=draw_color,
            linewidth=linewidth
        )
        ax.add_patch(patch)

        corners = self.get_corners()

        ax.plot(
            [corners[0][0], corners[2][0]],
            [corners[0][1], corners[2][1]],
            lw=linewidth,
            ls='solid',
            color=draw_color
        )
        ax.plot(
            [corners[1][0], corners[3][0]],
            [corners[1][1], corners[3][1]],
            lw=linewidth,
            ls='solid',
            color=draw_color
        )
        # Render label and ID
        render_label_and_id(
            ax,
            self,
            'Storage',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="__",
            id_prefix="__"
        )


class Storage60(GenericStorage):
    """
    Storage box with thickness of 60 cm

    """
    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None
    ):
        super().__init__(
            anchor_point=anchor_point,
            length=length,
            thickness=0.6,
            orientation_angle=orientation_angle,
            color=color,
            label=label
        )

class Storage40(GenericStorage):
    """
    Storage box with thickness of 40 cm

    """
    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None
    ):
        super().__init__(
            anchor_point=anchor_point,
            length=length,
            thickness=0.4,
            orientation_angle=orientation_angle,
            color=color,
            label=label
        )