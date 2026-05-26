"""
Draw kitchen and laundry appliances

Author: Krzysztof Bartczak
"""


import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle, Circle
from matplotlib.lines import Line2D

from ...utils import rotate_point, render_label_and_id, text_readability_rotation
from ..element import RectangularElement


class Dishwasher(RectangularElement):
    """
    Dishwasher appliance

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'grey',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the appliance;
            it is measured between X-axis and the appliance in positive direction (counterclockwise);
            initial appliance is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the appliance
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Dishwasher` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=0.6,
            thickness=0.6,
            color=color,
            label=label
        )  # Standard dishwasher width  # Standard dishwasher depth
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw dishwasher."""
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
        ax.add_patch(patch)
       
        # Draw double S pattern (mirrored and turned 90 degrees) with circle through middle
        center_x = self.length / 2
        center_y = self.thickness / 2
        
        # S-curve parameters
        curve_width = 0.3
        curve_height = 0.12
        
        # First S curve (upper)
        # Create S using two arcs
        # Upper right arc
        upper_right_arc = Arc(
            rotate_point(
                self.anchor_point,
                center_x + curve_width / 4,
                center_y + curve_height / 2,
                math.radians(self.orientation_angle)
            ),
            curve_width / 2,
            curve_height,
            angle=self.orientation_angle,
            theta1=180,
            theta2=0,
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(upper_right_arc)
        
        # Upper left arc
        upper_left_arc = Arc(
            rotate_point(
                self.anchor_point,
                center_x - curve_width / 4,
                center_y + curve_height / 2,
                math.radians(self.orientation_angle)
            ),
            curve_width / 2,
            curve_height,
            angle=self.orientation_angle,
            theta1=0,
            theta2=180,
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(upper_left_arc)
        
        # Second S curve (lower) - mirrored
        # Lower right arc
        lower_right_arc = Arc(
            rotate_point(
                self.anchor_point,
                center_x + curve_width / 4,
                center_y - curve_height / 2,
                math.radians(self.orientation_angle)
            ),
            curve_width / 2,
            curve_height,
            angle=self.orientation_angle,
            theta1=180,
            theta2=0,
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(lower_right_arc)
        
        # Lower left arc
        lower_left_arc = Arc(
            rotate_point(
                self.anchor_point,
                center_x - curve_width / 4,
                center_y - curve_height / 2,
                math.radians(self.orientation_angle)
            ),
            curve_width / 2,
            curve_height,
            angle=self.orientation_angle,
            theta1=0,
            theta2=180,
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(lower_left_arc)
        
        # Circle crossing through the middle of the SS pattern
        circle_pos = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        middle_circle = Circle(
            circle_pos,
            radius=0.084,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(middle_circle)

        render_label_and_id(
            ax,
            self,
            'Dishwasher',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class Fridge(RectangularElement):
    """
    Refrigerator appliance

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            length: float = 0.6,  # Standard fridge width
            thickness: float = 0.6,  # Standard fridge depth
            color: str = 'grey',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the appliance
        :param length:
            length of the appliance (in meters)
        :param thickness:
            thickness of the appliance (in meters)  
        :param color:
            color to use for drawing the appliance
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Fridge` class
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
        """Draw fridge."""
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
        ax.add_patch(patch)
       
        # Draw snowflake symbol in center
        center_x = self.length / 2
        center_y = self.thickness / 2
        snowflake_size = 0.15
        
        # Draw 6 lines radiating from center (snowflake pattern)
        for i in range(6):
            angle = i * math.pi / 3  # 60 degrees apart
            
            # Main arm
            start_x = center_x
            start_y = center_y
            end_x = center_x + snowflake_size * math.cos(angle)
            end_y = center_y + snowflake_size * math.sin(angle)
            
            start_point = rotate_point(
                self.anchor_point,
                start_x,
                start_y,
                math.radians(self.orientation_angle)
            )
            end_point = rotate_point(
                self.anchor_point,
                end_x,
                end_y,
                math.radians(self.orientation_angle)
            )
            
            line = Line2D(
                [start_point[0], end_point[0]],
                [start_point[1], end_point[1]],
                color=draw_color,
                linewidth=0.8
            )
            ax.add_line(line)

        render_label_and_id(
            ax,
            self,
            'Fridge',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class Freezer(RectangularElement):
    """
    Freezer appliance

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            length: float = 0.6,  # Standard freezer width
            thickness: float = 0.6,  # Standard freezer depth
            color: str = 'grey',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the appliance
        :param length:
            length of the appliance (in meters)
        :param thickness:
            thickness of the appliance (in meters)
        :param color:
            color to use for drawing the appliance
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Freezer` class
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
        """Draw freezer."""
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
        ax.add_patch(patch)
       
        # Draw two snowflakes
        snowflake_size = 0.12
        
        # Position for two snowflakes (left and right of center)
        snowflake_positions = [
            (self.length * 0.35, self.thickness / 2),
            (self.length * 0.65, self.thickness / 2)
        ]
        
        for sf_center_x, sf_center_y in snowflake_positions:
            # Draw 6 lines radiating from center (snowflake pattern)
            for i in range(6):
                angle = i * math.pi / 3  # 60 degrees apart
                
                # Main arm
                start_x = sf_center_x
                start_y = sf_center_y
                end_x = sf_center_x + snowflake_size * math.cos(angle)
                end_y = sf_center_y + snowflake_size * math.sin(angle)
                
                start_point = rotate_point(
                    self.anchor_point,
                    start_x,
                    start_y,
                    math.radians(self.orientation_angle)
                )
                end_point = rotate_point(
                    self.anchor_point,
                    end_x,
                    end_y,
                    math.radians(self.orientation_angle)
                )
                
                line = Line2D(
                    [start_point[0], end_point[0]],
                    [start_point[1], end_point[1]],
                    color=draw_color,
                    linewidth=0.8
                )
                ax.add_line(line)

        render_label_and_id(
            ax,
            self,
            'Freezer',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class WashingMachine(RectangularElement):
    """
    Washing machine appliance

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'grey',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the appliance
        :param color:
            color to use for drawing the appliance
        :param label:
            optional label for the element
        :return:
            freshly created instance of `WashingMachine` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=0.6,
            thickness=0.6,
            color=color,
            label=label
        )  # Standard washing machine width  # Standard washing machine depth
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw washing machine."""
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
        ax.add_patch(patch)
       
        # Draw two concentric circles representing the drum
        center_x = self.length / 2
        center_y = self.thickness / 2
        center_rotated = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        # Outer circle
        outer_circle = Circle(
            center_rotated,
            radius=0.2,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(outer_circle)
        
        # Inner circle
        inner_circle = Circle(
            center_rotated,
            radius=0.13,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(inner_circle)

        render_label_and_id(
            ax,
            self,
            'Washing Machine',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class Dryer(RectangularElement):
    """
    Dryer appliance

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'grey',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the appliance
        :param color:
            color to use for drawing the appliance
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Dryer` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=0.6,
            thickness=0.6,
            color=color,
            label=label
        )  # Standard dryer width  # Standard dryer depth
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw dryer."""
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
        ax.add_patch(patch)
       
        # Draw two concentric circles representing the drum (same as washing machine)
        center_x = self.length / 2
        center_y = self.thickness / 2
        center_rotated = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        # Outer circle
        outer_circle = Circle(
            center_rotated,
            radius=0.2,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(outer_circle)
        
        # Inner circle
        inner_circle = Circle(
            center_rotated,
            radius=0.13,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(inner_circle)
        
        # Solid small circle in the center (differentiates from washing machine)
        center_dot = Circle(
            center_rotated,
            radius=0.04,
            facecolor=draw_color,
            edgecolor=draw_color
        )
        ax.add_patch(center_dot)

        render_label_and_id(
            ax,
            self,
            'Dryer',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class Stovetop(RectangularElement):
    """
    Stovetop appliance

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'grey',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the appliance
        :param color:
            color to use for drawing the appliance
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Stovetop` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=0.6,
            thickness=0.6,
            color=color,
            label=label
        )  # Standard stovetop width  # Standard stovetop depth
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw stovetop."""
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
        ax.add_patch(patch)
       
        # Draw 4 circles representing burners/heat plates (2x2 grid)
        burner_radius = 0.08
        spacing_x = self.length / 3
        spacing_y = self.thickness / 3
        
        # Positions for 4 burners
        burner_positions = [
            (spacing_x, spacing_y),  # Bottom left
            (spacing_x * 2, spacing_y),  # Bottom right
            (spacing_x, spacing_y * 2),  # Top left
            (spacing_x * 2, spacing_y * 2)  # Top right
        ]
        
        for burner_x, burner_y in burner_positions:
            burner_pos = rotate_point(
                self.anchor_point,
                burner_x,
                burner_y,
                math.radians(self.orientation_angle)
            )
            
            burner = Circle(
                burner_pos,
                radius=burner_radius,
                facecolor='none',
                edgecolor=draw_color,
                linewidth=1.0
            )
            ax.add_patch(burner)

        render_label_and_id(
            ax,
            self,
            'Stovetop',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class SingleSink(RectangularElement):
    """
    Single sink appliance

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'grey',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the appliance
        :param color:
            color to use for drawing the appliance
        :param label:
            optional label for the element
        :return:
            freshly created instance of `SingleSink` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=0.9,
            thickness=0.6,
            color=color,
            label=label
        )  # Single sink length  # Single sink width
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw single sink."""
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
        ax.add_patch(patch)
       
        # Left half: rectangle representing the basin
        basin_width = self.length / 2 - 0.1
        basin_height = self.thickness - 0.2
        basin_x = 0.05
        basin_y = 0.1
        
        basin_pos = rotate_point(
            self.anchor_point,
            basin_x,
            basin_y,
            math.radians(self.orientation_angle)
        )
        
        basin = Rectangle(
            basin_pos,
            basin_width,
            basin_height,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(basin)
        
        # Right half: 4 parallel lines representing drain/drying area
        num_lines = 4
        line_start_x = self.length / 2 + 0.1
        line_end_x = self.length - 0.1
        
        for i in range(num_lines):
            y_pos = 0.15 + i * (self.thickness - 0.3) / (num_lines - 1)
            
            start_point = rotate_point(
                self.anchor_point,
                line_start_x,
                y_pos,
                math.radians(self.orientation_angle)
            )
            end_point = rotate_point(
                self.anchor_point,
                line_end_x,
                y_pos,
                math.radians(self.orientation_angle)
            )
            
            line = Line2D(
                [start_point[0], end_point[0]],
                [start_point[1], end_point[1]],
                color=draw_color,
                linewidth=0.5
            )
            ax.add_line(line)

        render_label_and_id(
            ax,
            self,
            'Single Sink',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )


class DoubleSink(RectangularElement):
    """
    Double sink appliance

    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            orientation_angle: float = 0,
            color: str = 'grey',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of anchor point (in meters);
            bottom left point is anchor point if `orientation_angle == 0`
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the appliance
        :param color:
            color to use for drawing the appliance
        :param label:
            optional label for the element
        :return:
            freshly created instance of `DoubleSink` class
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=1.2,
            thickness=0.6,
            color=color,
            label=label
        )  # Double sink length (wider than single)  # Double sink width
        self.room_id = None

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw double sink."""
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
        ax.add_patch(patch)
       
        # Left basin: rectangle
        basin_width = self.length / 2 - 0.15
        basin_height = self.thickness - 0.2
        
        # Left basin
        left_basin_x = 0.05
        left_basin_y = 0.1
        
        left_basin_pos = rotate_point(
            self.anchor_point,
            left_basin_x,
            left_basin_y,
            math.radians(self.orientation_angle)
        )
        
        left_basin = Rectangle(
            left_basin_pos,
            basin_width,
            basin_height,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(left_basin)
        
        # Right basin
        right_basin_x = self.length / 2 + 0.1
        right_basin_y = 0.1
        
        right_basin_pos = rotate_point(
            self.anchor_point,
            right_basin_x,
            right_basin_y,
            math.radians(self.orientation_angle)
        )
        
        right_basin = Rectangle(
            right_basin_pos,
            basin_width,
            basin_height,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.0
        )
        ax.add_patch(right_basin)

        render_label_and_id(
            ax,
            self,
            'Double Sink',
            self.anchor_point,
            self.orientation_angle,
            label_prefix="",
            id_prefix=""
        )
