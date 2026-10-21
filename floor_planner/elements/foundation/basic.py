"""
Draw basic elements that represent walls, windows, and doors.

Author: Nikolay Lysenko
"""


import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle

from ...utils import rotate_point, render_label_and_id, text_readability_rotation
from ..element import Element, RectangularElement
from ..symbols.info import DimensionArrow
from ...options import get_dimensions, get_element_option
from ..vertical_levels import VertInfoLvl01, VertInfoWindows


class WallND(VertInfoLvl01, RectangularElement):
    """
    Straight wall without dimensions.

    For corners of acute or obtuse angles please consider `renovation.elements.Polygon` class.
    """

    # Extra faces read from ``textures.extras``: reveals of embedded doors/windows
    _extra_faces = ('inside_left', 'inside_right', 'inside_top', 'inside_bottom')

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            thickness: float,
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None,
            room_edge: bool = False,
            id: str | None = None,
            v_anchor: float | None = None,
            height: float | None = None,
            textures: dict | None = None
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
        :param id:
            optional explicit ID; if None, generated from class name and label
        :param v_anchor:
            optional vertical anchor point in meters; if None, uses element's default vertical level
        :param height:
            optional height of the wall in meters; if None, uses default (2.7m)
        :param textures:
            optional per-face textures and lighting for the 3D export
            (see ``floor_planner.face_textures``); None = class defaults and .mtl
        :return:
            freshly created instance of `WallND` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=thickness,
            color=color,
            label=label,
            id=id,
            v_anchor=v_anchor,
            height=height,
            textures=textures
        )
        self.room_edge = room_edge

        # Room properties (set by Room class if this wall is part of a room)
        self.is_room_wall = False

    def _default_height(self) -> float:
        """Return default height for walls (standard room height)."""
        return 2.7

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
        patch.set_zorder(self.get_zorder())
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

