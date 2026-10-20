"""
Draw bathroom fixtures

Author: Krzysztof Bartczak
"""


import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle, Circle, Ellipse
from matplotlib.lines import Line2D

from ...utils import rotate_point, render_label_and_id, text_readability_rotation
from ..element import Element, RectangularElement
from ..vertical_levels import VertInfoLvl03


class Shower(VertInfoLvl03, RectangularElement):
    """
    Shower stall

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None,
            id: str | None = None,
            length: float = 0.9,  # Standard shower stall size
            thickness: float = 0.9  # Standard shower stall size

    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the fixture
        :param color:
            color to use for drawing the fixture
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :return:
            freshly created instance of `Shower` class
        """
        super().__init__(

            anchor_point=anchor_point,

            orientation_angle=orientation_angle,

            length=length,

            thickness=thickness,

            color=color,

            label=label,
            id=id,

        )
        self.alpha_mode = "BLEND"  # Shower glass uses alpha blending

    def _default_height(self) -> float:
        """Return default height for shower."""
        return 2.1

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw shower."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Main rectangle
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
       
        # Showerhead in corner (top corner)
        showerhead_x = self.length * 0.2
        showerhead_y = self.thickness * 0.8
        
        showerhead_pos = rotate_point(
            self.anchor_point,
            showerhead_x,
            showerhead_y,
            math.radians(self.orientation_angle)
        )
        
        # Showerhead circle
        showerhead = Circle(
            showerhead_pos,
            radius=0.06,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        showerhead.set_zorder(self.get_zorder())
        ax.add_patch(showerhead)
        
        # Water spray lines
        num_spray_lines = 5
        spray_length = 0.15
        for i in range(num_spray_lines):
            angle_offset = -60 + i * 30  # Spray pattern
            spray_angle = math.radians(angle_offset)
            
            spray_end_x = showerhead_x + spray_length * math.cos(spray_angle)
            spray_end_y = showerhead_y + spray_length * math.sin(spray_angle)
            
            spray_end = rotate_point(
                self.anchor_point,
                spray_end_x,
                spray_end_y,
                math.radians(self.orientation_angle)
            )
            
            spray_line = Line2D(
                [showerhead_pos[0], spray_end[0]],
                [showerhead_pos[1], spray_end[1]],
                color=draw_color,
                linewidth=0.5
            )
            ax.add_line(spray_line)

        render_label_and_id(
            ax,
            self,
            'Shower',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class Bathtub(VertInfoLvl03, RectangularElement):
    """
    Bathtub

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            length: float = 1.7,
            thickness: float = 0.8,
            height: float = 0.6,
            color: str = 'black',
            label: str | None = None,
            id: str | None = None,
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the fixture
        :param color:
            color to use for drawing the fixture
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :return:
            freshly created instance of `Bathtub` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=thickness,
            color=color,
            label=label,
            id=id,
            height = height
        )

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw bathtub."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Main rectangle
        patch = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor='none',
            fill=False,
            edgecolor=draw_color,
            linewidth=1.5
        )
        patch.set_zorder(self.get_zorder())
        ax.add_patch(patch)
       
        # Inner oval representing the tub basin
        center_x = self.length / 2
        center_y = self.thickness / 2
        
        center_rotated = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        # Ellipse for bathtub basin
        tub_ellipse = Ellipse(
            center_rotated,
            width=self.length - 0.2,
            height=self.thickness - 0.2,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        tub_ellipse.set_zorder(self.get_zorder())
        ax.add_patch(tub_ellipse)

        render_label_and_id(
            ax,
            self,
            'Bathtub',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class Basin(VertInfoLvl03, RectangularElement):
    """
    Bathroom basin/sink

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            height: float = 0.85,
            color: str = 'black',
            label: str | None = None,
            id: str | None = None,
            
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the fixture
        :param color:
            color to use for drawing the fixture
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :return:
            freshly created instance of `Basin` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=0.6,
            thickness=0.5,
            height=height,
            color=color,
            label=label,
            id=id,
        )  # Basin width  # Basin depth

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw basin."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Main rectangle
        patch = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor='none',
            fill=False,
            edgecolor=draw_color,
            linewidth=1.5
        )
        patch.set_zorder(self.get_zorder())
        ax.add_patch(patch)
       
        # Basin bowl (circle or oval)
        center_x = self.length / 2
        center_y = self.thickness / 2
        
        center_rotated = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        # Circle for basin bowl
        basin_bowl = Circle(
            center_rotated,
            radius=0.15,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        basin_bowl.set_zorder(self.get_zorder())
        ax.add_patch(basin_bowl)
        
        # Faucet indicator (small circle at back)
        faucet_x = center_x
        faucet_y =  0.1
        
        faucet_pos = rotate_point(
            self.anchor_point,
            faucet_x,
            faucet_y,
            math.radians(self.orientation_angle)
        )
        
        faucet = Circle(
            faucet_pos,
            radius=0.03,
            facecolor=draw_color,
            edgecolor=draw_color
        )
        faucet.set_zorder(self.get_zorder())
        ax.add_patch(faucet)

        render_label_and_id(
            ax,
            self,
            'Basin',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class Toilet(VertInfoLvl03, RectangularElement):
    """
    Toilet

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None,
            id: str | None = None,
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the fixture
        :param color:
            color to use for drawing the fixture
        :param label:
            optional label for the element
        :param id:
            optional explicit ID; if None, generated from class name and label
        :return:
            freshly created instance of `Toilet` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=0.7,
            thickness=0.4,
            color=color,
            label=label,
            id=id,
        )  # Standard toilet length (front to back)  # Standard toilet width

    def _default_height(self) -> float:
        """Return default height for toilet."""
        return 0.5

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw toilet."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw toilet with tank facing down at orientation 0
        center_x = self.thickness / 2
        center_y = self.length / 2
        
        center = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        # Main outer ellipse
        outer_ellipse = Ellipse(
            center,
            width=self.thickness,
            height=self.length,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.5
        )
        outer_ellipse.set_zorder(self.get_zorder())
        ax.add_patch(outer_ellipse)
       
        # Tank
        tank_width = self.thickness * 0.84
        tank_height = 0.18
        tank_x = (self.thickness - tank_width) / 2
        tank_y = 0
        
        tank_anchor = rotate_point(
            self.anchor_point,
            tank_x,
            tank_y,
            math.radians(self.orientation_angle)
        )
        
        tank = Rectangle(
            tank_anchor,
            tank_width,
            tank_height,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        tank.set_zorder(self.get_zorder())
        ax.add_patch(tank)
       
        # Inner ellipse (toilet bowl opening)
        bowl_center_x = self.thickness / 2
        bowl_center_y = self.length * 0.65
        
        bowl_center = rotate_point(
            self.anchor_point,
            bowl_center_x,
            bowl_center_y,
            math.radians(self.orientation_angle)
        )
        
        inner_ellipse = Ellipse(
            bowl_center,
            width=self.thickness - 0.15,
            height=0.35,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        inner_ellipse.set_zorder(self.get_zorder())
        ax.add_patch(inner_ellipse)

        render_label_and_id(
            ax,
            self,
            'Toilet',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )
