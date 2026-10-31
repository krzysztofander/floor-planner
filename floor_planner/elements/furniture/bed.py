"""
Draw storage furniture elements

Author: Krzysztof Bartczak
"""


import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle

from ...utils import rotate_point, render_label_and_id
from ..element import Element, RectangularElement
from ..symbols.info import DimensionArrow
from ..vertical_levels import VertInfoLvl03

class MultiBed(VertInfoLvl03, RectangularElement):
    """
    Multibed draws single or double bed.

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float,
            length: float,
            thickness: float,
            color: str,
            label: str | None = None,
            id: str | None = None,
            textures: dict | None = None,
    ):
        super().__init__(

            anchor_point=anchor_point,

            orientation_angle=orientation_angle,

            length=length,

            thickness=thickness,

            color=color,

            label=label,
            id=id,
            textures=textures,

        )
        self.is_double = thickness > 1.2

        # Room properties (set by Room class if this storage box is part of a room)

    def _default_height(self) -> float:
        """Return default height for bed."""
        return 0.5

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw double bed."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

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
        patch.set_zorder(self.get_zorder())
        ax.add_patch(patch)
       
        pillow_x = 0.6
        pillow_y = 0.65

        if self.is_double:
            pillow_anchors = [ (self.length - pillow_x -0.1, 0.1), 
                                (self.length - pillow_x -0.1, self.thickness - pillow_y - 0.1) ]
        else:
            pillow_anchors = [ (self.length - pillow_x - 0.1, (self.thickness - pillow_y) / 2) ]


        for pillow_anchor in pillow_anchors:
            pillow_anchor=rotate_point( self.anchor_point, pillow_anchor[0], pillow_anchor[1], math.radians(self.orientation_angle))
            patch = Rectangle(
                pillow_anchor,pillow_x,pillow_y,
                angle=self.orientation_angle,
                facecolor=draw_color,
                fill=False,
                edgecolor=draw_color,
                linewidth=linewidth
            )
            patch.set_zorder(self.get_zorder())
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


class DoubleBed(MultiBed):
    """
    Double bed

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'grey',
            label: str | None = None,
            id: str | None = None,
            textures: dict | None = None,
    ):
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=2.15,
            thickness=1.7,
            color=color,
            label=label,
            id=id,
            textures=textures,
        )
class SingleBed(MultiBed):
    """
    Single bed

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'grey',
            label: str | None = None,
            id: str | None = None,
            textures: dict | None = None,
    ):       
        super().__init__(label=label,
                            anchor_point=anchor_point,
                            orientation_angle=orientation_angle,
                            length=2.0,
                            thickness=0.9,
                            color=color,
                            id=id,
                            textures=textures)
