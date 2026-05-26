"""
Draw general furniture elements

Author: Krzysztof Bartczak
"""


import math

import matplotlib.axes
from matplotlib.patches import Rectangle, Circle
from matplotlib.lines import Line2D

from ...utils import rotate_point, render_label_and_id, text_readability_rotation
from ..element import RectangularElement


class Desk(RectangularElement):
    """
    Desk with standard dimensions

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            length: float = 1.4,  
            thickness: float = 0.65,
            color: str = 'brown',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the desk;
            it is measured between X-axis and the desk in positive direction (counterclockwise);
            initial desk is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the desk
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Desk` class
        """
        super().__init__(

            anchor_point=anchor_point,

            orientation_angle=orientation_angle,

            length=length,

            thickness=thickness,

            color=color,

            label=label

        )  # Standard desk width  # Standard desk depth
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw desk."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Main desktop rectangle
        patch = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor='none',
            fill=False,
            edgecolor=draw_color,
            linewidth=2.0
        )
        ax.add_patch(patch)
       
        # Draw desk legs (small circles at corners)
        leg_radius = 0.03
        leg_inset = 0.1
        
        leg_positions = [
            (leg_inset, leg_inset),
            (self.length - leg_inset, leg_inset),
            (leg_inset, self.thickness - leg_inset),
            (self.length - leg_inset, self.thickness - leg_inset)
        ]
        
        for leg_x, leg_y in leg_positions:
            leg_center = rotate_point(
                self.anchor_point,
                leg_x,
                leg_y,
                math.radians(self.orientation_angle)
            )
            leg = Circle(
                leg_center,
                leg_radius,
                facecolor=draw_color,
                edgecolor=draw_color,
                linewidth=1.0
            )
            ax.add_patch(leg)
        
        # Render label and ID
        render_label_and_id(
            ax,
            self,
            'Desk',
            self.anchor_point,
            self.orientation_angle
        )


class DiningTable(RectangularElement):
    """
    Dining table with configurable dimensions

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            thickness: float,
            orientation_angle: float = 0,
            color: str = 'brown',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param length:
            length of the table (in meters)
        :param thickness:
            width of the table (in meters)
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the table;
            it is measured between X-axis and the table in positive direction (counterclockwise);
            initial table is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the table
        :param label:
            optional label for the element
        :return:
            freshly created instance of `DiningTable` class
        """
        super().__init__(

            anchor_point=anchor_point,

            orientation_angle=orientation_angle,

            length=length,

            thickness=thickness,

            color=color,

            label=label

        )
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw dining table."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Main table top
        patch = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor='none',
            fill=False,
            edgecolor=draw_color,
            linewidth=2.5
        )
        ax.add_patch(patch)
       
        # Draw table legs (circles at corners)
        leg_radius = 0.04
        leg_inset = 0.15
        
        leg_positions = [
            (leg_inset, leg_inset),
            (self.length - leg_inset, leg_inset),
            (leg_inset, self.thickness - leg_inset),
            (self.length - leg_inset, self.thickness - leg_inset)
        ]
        
        for leg_x, leg_y in leg_positions:
            leg_center = rotate_point(
                self.anchor_point,
                leg_x,
                leg_y,
                math.radians(self.orientation_angle)
            )
            leg = Circle(
                leg_center,
                leg_radius,
                facecolor=draw_color,
                edgecolor=draw_color,
                linewidth=1.0
            )
            ax.add_patch(leg)
        
        # Render label and ID
        render_label_and_id(
            ax,
            self,
            'DiningTable',
            self.anchor_point,
            self.orientation_angle
        )


class Chair(RectangularElement):
    """
    Chair with standard dimensions

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'darkgray',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the chair;
            it is measured between X-axis and the chair in positive direction (counterclockwise);
            initial chair is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the chair
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Chair` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=0.45,  # Standard chair width
            thickness=0.45,  # Standard chair depth
            color=color,
            label=label
        )
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw chair."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Main seat rectangle
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
        ax.add_patch(patch)
       
        # Draw backrest (thicker line at back)
        backrest_y = 0
        backrest_thickness = 0.12
        
        backrest_start = rotate_point(
            self.anchor_point,
            0,
            backrest_y,
            math.radians(self.orientation_angle)
        )
        backrest_end = rotate_point(
            self.anchor_point,
            self.length,
            backrest_y,
            math.radians(self.orientation_angle)
        )
        
        backrest = Line2D(
            [backrest_start[0], backrest_end[0]],
            [backrest_start[1], backrest_end[1]],
            color=draw_color,
            linewidth=3.0
        )
        ax.add_line(backrest)
        
        # Render label and ID
        render_label_and_id(
            ax,
            self,
            'Chair',
            self.anchor_point,
            self.orientation_angle
        )


class Sofa(RectangularElement):
    """
    N-element sofa with configurable number of seats

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            num_seats: int,
            orientation_angle: float = 0,
            color: str = 'darkslateblue',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param num_seats:
            number of seats in the sofa (1, 2, 3, etc.)
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the sofa;
            it is measured between X-axis and the sofa in positive direction (counterclockwise);
            initial sofa is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the sofa
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Sofa` class
        """
        self.num_seats = num_seats
        self.seat_width = 0.8  # Width per seat
        sofa_length = num_seats * self.seat_width  # Total length
        sofa_thickness = 0.9  # Standard sofa depth
        
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=sofa_length,
            thickness=sofa_thickness,
            color=color,
            label=label
        )
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw sofa."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Main sofa body
        patch = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor='none',
            fill=False,
            edgecolor=draw_color,
            linewidth=2.5
        )
        ax.add_patch(patch)
       
        # Draw backrest (thicker line at back)
        backrest_y = 0
        
        backrest_start = rotate_point(
            self.anchor_point,
            0,
            backrest_y,
            math.radians(self.orientation_angle)
        )
        backrest_end = rotate_point(
            self.anchor_point,
            self.length,
            backrest_y,
            math.radians(self.orientation_angle)
        )
        
        backrest = Line2D(
            [backrest_start[0], backrest_end[0]],
            [backrest_start[1], backrest_end[1]],
            color=draw_color,
            linewidth=4.0
        )
        ax.add_line(backrest)
        
        # Draw armrests on both sides (rectangles)
        armrest_width = 0.15
        armrest_depth = self.thickness * 0.7
        
        # Left armrest
        left_armrest_anchor = rotate_point(
            self.anchor_point,
            -armrest_width,
            (self.thickness - armrest_depth) / 2,
            math.radians(self.orientation_angle)
        )
        left_armrest = Rectangle(
            left_armrest_anchor,
            armrest_width,
            armrest_depth,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=2.0
        )
        ax.add_patch(left_armrest)
        
        # Right armrest
        right_armrest_anchor = rotate_point(
            self.anchor_point,
            self.length,
            (self.thickness - armrest_depth) / 2,
            math.radians(self.orientation_angle)
        )
        right_armrest = Rectangle(
            right_armrest_anchor,
            armrest_width,
            armrest_depth,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=2.0
        )
        ax.add_patch(right_armrest)
        
        # Draw seat dividers (vertical lines between seats)
        if self.num_seats > 1:
            divider_margin = 0.15
            for i in range(1, self.num_seats):
                divider_x = i * self.seat_width
                divider_start = rotate_point(
                    self.anchor_point,
                    divider_x,
                    divider_margin,
                    math.radians(self.orientation_angle)
                )
                divider_end = rotate_point(
                    self.anchor_point,
                    divider_x,
                    self.thickness - divider_margin,
                    math.radians(self.orientation_angle)
                )
                
                divider = Line2D(
                    [divider_start[0], divider_end[0]],
                    [divider_start[1], divider_end[1]],
                    color=draw_color,
                    linewidth=1.0,
                    linestyle='--'
                )
                ax.add_line(divider)
        
        # Render label and ID
        render_label_and_id(
            ax,
            self,
            f'Sofa ({self.num_seats})',
            self.anchor_point,
            self.orientation_angle
        )
