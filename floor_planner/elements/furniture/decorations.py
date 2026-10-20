"""
Draw decorative elements

Author: Krzysztof Bartczak
"""


import math

import matplotlib.axes
from matplotlib.patches import Rectangle, Ellipse, Polygon, Circle
from matplotlib.lines import Line2D

from ...utils import rotate_point, render_label_and_id, text_readability_rotation
from ..element import RectangularElement
from ..vertical_levels import VertInfoLvl03


class FishTank(VertInfoLvl03, RectangularElement):
    """
    Fish tank / aquarium

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            length: float = 0.6,
            thickness: float = 0.3,
            v_anchor: float = 0.6,
            color: str = 'blue',
            label: str | None = None,
            id: str | None = None,
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the fish tank;
            it is measured between X-axis and the fish tank in positive direction (counterclockwise);
            initial fish tank is rotated around anchor point to get the desired orientation
        :param length:
            length of the fish tank
        :param thickness:
            depth of the fish tank
        :param color:
            color to use for drawing the fish tank
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :return:
            freshly created instance of `FishTank` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=thickness,
            v_anchor=v_anchor,
            color=color,
            label=label,
            id=id,
        )
        self.alpha_mode = "BLEND"  # Fish tank glass uses alpha blending

    def _default_height(self) -> float:
        """Return default height for fish tank."""
        return 0.5

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw fish tank with a fish symbol."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Main rectangle (tank)
        patch = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor='none',
            fill=False,
            edgecolor=draw_color,
            linewidth=2
        )
        patch.set_zorder(self.get_zorder())
        ax.add_patch(patch)
       
        # Draw a fish symbol in the center
        center_x = self.length / 2
        center_y = self.thickness / 2
        
        # Fish body (ellipse)
        fish_body_width = self.length * 0.3
        fish_body_height = self.thickness * 0.4
        
        fish_center = rotate_point(
            self.anchor_point,
            center_x - fish_body_width * 0.1,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        fish_body = Ellipse(
            fish_center,
            width=fish_body_width,
            height=fish_body_height,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        fish_body.set_zorder(self.get_zorder())
        ax.add_patch(fish_body)
        
        # Fish tail (triangle)
        tail_base_x = center_x - fish_body_width * 0.6
        tail_tip_x = tail_base_x - fish_body_width * 0.4
        tail_height = fish_body_height * 0.9
        
        # Triangle points (in local coordinates)
        tail_points = [
            (tail_tip_x, center_y + tail_height / 2),
            (tail_tip_x, center_y - tail_height / 2),
            (tail_base_x, center_y)
        ]
        
        # Rotate all points
        rotated_tail_points = [
            rotate_point(self.anchor_point, x, y, math.radians(self.orientation_angle ))
            for x, y in tail_points
        ]
        
        tail = Polygon(
            rotated_tail_points,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        tail.set_zorder(self.get_zorder())
        ax.add_patch(tail)
        
        # Fish eye (small circle)
        eye_x = center_x + fish_body_width * 0.15
        eye_y = center_y + fish_body_height * 0.15
        
        eye_pos = rotate_point(
            self.anchor_point,
            eye_x,
            eye_y,
            math.radians(self.orientation_angle)
        )
        
        eye = Circle(
            eye_pos,
            radius=0.02,
            facecolor=draw_color,
            edgecolor=draw_color,
            linewidth=0.5
        )
        eye.set_zorder(self.get_zorder())
        ax.add_patch(eye)
