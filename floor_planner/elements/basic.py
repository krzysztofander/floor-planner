"""
Draw basic elements that represent walls, windows, and doors.

Author: Nikolay Lysenko
"""


import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle

from ..utils import rotate_point, render_label_and_id, text_readability_rotation
from .element import Element, RectangularElement
from .info import DimensionArrow
from .options import get_dimensions, get_element_option


class WallND(RectangularElement):
    """
    Straight wall without dimensions.

    For corners of acute or obtuse angles please consider `renovation.elements.Polygon` class.
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            thickness: float,
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None,
            room_edge: bool = False
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param length:
            length of the wall (in meters)
        :param thickness:
            thickness of the wall (in meters)
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the wall;
            it is measured between X-axis and the wall in positive direction (counterclockwise);
            initial wall is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the wall
        :param label:
            optional label for the element
        :param room_edge:
            if True, this wall forms the boundary of a room (used for room validation and calculations)
        :return:
            freshly created instance of `WallND` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            label=label
        )
        self.length = length
        self.thickness = thickness
        self.color = color
        self.room_edge = room_edge

        # Room properties (set by Room class if this wall is part of a room)
        self.is_room_wall = False
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw straight wall."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # It this wall have thickness < 0.01 than make it 0.01 so it is actually drawn.
        # future feature: used dashed line here.
        # Additionally draw it semi-transparently
        alfa = 1.0
        thickness = self.thickness
        if self.thickness < 0.01:
            thickness = 0.01
            alfa = 0.3

        patch = Rectangle(
            self.anchor_point,
            self.length,
            thickness,
            angle=self.orientation_angle,
            facecolor=draw_color,
            alpha=alfa
        )
        ax.add_patch(patch)

        # Render label and ID
        render_label_and_id(
            ax,
            self,
            'Wall',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="__",
            id_prefix="__"
        )

class Wall(WallND):
    """
    Wall with dimensions.

    Same as WallND, but includes a dimension arrow from the anchor point to the end of the wall
    when dimensions option is enabled.
    """

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw straight wall with optional dimension."""
        # Draw the wall using parent class
        super().draw(ax)

        # Skip dimension drawing if wall is invisible and show_invisible is not enabled
        if self.get_draw_color() is None:
            return

        # Check if dimensions should be drawn
        if get_dimensions():
            dimension_anchor = rotate_point(anchor_point=self.anchor_point,
                                    offset_x=0,
                                    offset_y=-min(max(0.3,self.thickness * 2),0.6),
                                    angle_rad=(math.radians(self.orientation_angle)))

            dimension = DimensionArrow(
                anchor_point=dimension_anchor,
                length=self.length,
                orientation_angle=self.orientation_angle,
                annotate_above=True,
                color='black'
            )
            dimension.draw(ax)

class Window(RectangularElement):
    """Window in a wall."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            overall_thickness: float,
            single_line_thickness: float = -1,
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates (in meters) of anchor point;
            bottom left point is anchor point if `orientation_angle == 0`
        :param length:
            length of the window (in meters)
        :param overall_thickness:
            total thickness of the window (in meters)
        :param single_line_thickness:
            thickness of a single outer line forming window (in meters)
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the window;
            it is measured between X-axis and the window in positive direction (counterclockwise);
            initial window is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the window
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Window` class
        """

        if single_line_thickness <= 0:
            single_line_thickness = overall_thickness / 10

        internal_thickness = overall_thickness - 2 * single_line_thickness
        if internal_thickness <= 0:
            raise ValueError("Window can not be drawn due to invalid thicknesses.")


        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            label=label
        )
        self.length = length
        self.overall_thickness = overall_thickness
        self.thickness = overall_thickness  #for get_corners function
        self.single_line_thickness = single_line_thickness
        self.color = color

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw window."""
        first_line = Rectangle(
            self.anchor_point,
            self.length,
            self.single_line_thickness,
            angle=self.orientation_angle,
            facecolor=self.color
        )
        ax.add_patch(first_line)

        window_emptyness_anchor_point = rotate_point(anchor_point=self.anchor_point,
                                    offset_x=0,
                                    offset_y=self.single_line_thickness ,
                                    angle_rad=(math.radians(self.orientation_angle)))
        window_emptyness = Rectangle(
            window_emptyness_anchor_point,
            self.length,
            self.overall_thickness - 2*self.single_line_thickness,
            angle=self.orientation_angle,
            facecolor='white'
        )
        ax.add_patch(window_emptyness)

        second_anchor_point = rotate_point(anchor_point=self.anchor_point,
                                    offset_x=0,
                                    offset_y=self.overall_thickness -self.single_line_thickness ,
                                    angle_rad=(math.radians(self.orientation_angle)))
        second_line = Rectangle(
            second_anchor_point,
            self.length,
            self.single_line_thickness,
            angle=self.orientation_angle,
            facecolor=self.color
        )
        ax.add_patch(second_line)

        # Render label and ID at midpoint between the two lines and centered horizontally
        label_position = rotate_point(anchor_point=self.anchor_point,
                                    offset_x=self.length /2,
                                    offset_y=self.overall_thickness /2,
                                    angle_rad=(math.radians(self.orientation_angle)))
        render_label_and_id(
            ax,
            self,
            'Window',
            label_position,
            text_readability_rotation(self.orientation_angle),
            centered=True
        )

