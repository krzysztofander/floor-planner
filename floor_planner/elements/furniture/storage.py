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
from ..options import get_dimensions, get_element_option
from ..vertical_levels import VertInfoLvl03


class GenericStorage(VertInfoLvl03, RectangularElement):
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
        super().__init__(

            anchor_point=anchor_point,

            orientation_angle=orientation_angle,

            length=length,

            thickness=thickness,

            color=color,

            label=label

        )

        # Room properties (set by Room class if this storage box is part of a room)

    def _default_height(self) -> float:
        """Return default height for storage."""
        return 2.0

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw storage box."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

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
        patch.set_zorder(self.get_zorder())
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
        
        # Display thickness value at center
        center_x = self.length / 2
        center_y = self.thickness / 2
        center = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        thickness_cm = self.thickness * 100
        text_angle = text_readability_rotation(self.orientation_angle)
        ax.text(
            center[0],
            center[1],
            f"{thickness_cm:.0f}",
            fontsize=10,
            color=draw_color,
            ha='center',
            va='center',
            rotation=text_angle,
            weight='normal',
            bbox=dict(
                facecolor='white',
                alpha=0.8,
                edgecolor='none',
                boxstyle='round,pad=0.3'
            )
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


class Tabletop(VertInfoLvl03, RectangularElement):
    """
    Storage box

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            thickness: float = 0.6,
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None
    ):
     
        super().__init__(

     
            anchor_point=anchor_point,

     
            orientation_angle=orientation_angle,

     
            length=length,

     
            thickness=thickness,

     
            color=color,

     
            label=label

     
        )

        # Room properties (set by Room class if this storage box is part of a room)

    def _default_height(self) -> float:
        """Return default height for tabletop."""
        return 0.75

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw storage box."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

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
        patch.set_zorder(self.get_zorder())
        ax.add_patch(patch)
        
        patch = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness*0.9,
            angle=self.orientation_angle,
            facecolor=draw_color,
            fill=False,
            edgecolor=draw_color,
            linewidth=linewidth / 3
        )
        patch.set_zorder(self.get_zorder())
        ax.add_patch(patch)

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