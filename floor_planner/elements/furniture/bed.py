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


class DoubleBed(RectangularElement):
    """
    Double bed

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the bed;
            it is measured between X-axis and the bed in positive direction (counterclockwise);
            initial bed is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the bed
        :param label:
            optional label for the element
        :param room_edge:
            if True, this bed forms the boundary of a room (used for room validation and calculations)
        :return:
            freshly created instance of `DoubleBed` class
        """
        super().__init__(label=label)
        self.anchor_point = anchor_point
        self.length = 2.15
        self.thickness = 1.7
        self.orientation_angle = orientation_angle
        self.color = color

        # Room properties (set by Room class if this storage box is part of a room)
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw double bed."""
        # Check if bed is invisible
        if self.color == 'invisible':
            # Skip drawing if show_invisible is not enabled
            if not get_show_invisible():
                return
            # Draw in red if show_invisible is enabled
            draw_color = 'red'
        else:
            draw_color = self.color

        linewidth = self.thickness 

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
       
        pillow_x = 0.6
        pillow_y = 0.65
        for pillow_anchor in [ (self.length - pillow_x -0.1, 0.1), 
                               (self.length - pillow_x -0.1, self.thickness - pillow_y - 0.1) ]:
            pillow_anchor=rotate_point( self.anchor_point, pillow_anchor[0], pillow_anchor[1], math.radians(self.orientation_angle))
            patch = Rectangle(
                pillow_anchor,pillow_x,pillow_y,
                angle=self.orientation_angle,
                facecolor=draw_color,
                fill=False,
                edgecolor=draw_color,
                linewidth=linewidth
            )

            ax.add_patch(patch)

        # Render label and ID
        render_label_and_id(
            ax,
            self,
            'Double Bed',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )
