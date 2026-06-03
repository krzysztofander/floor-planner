"""
Draw Doors

Author: Krzysztof Bartczak
"""


import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle

from ...constants import RIGHT_ANGLE_IN_DEGREES
from ...utils import rotate_point, render_label_and_id
from ..element import RectangularElement
from ..symbols.info import DimensionArrow
from ...options import get_element_option
from ..vertical_levels import VertInfoDoor

class Door2D():
    """Helper for drawing a door, used both for programmatic doors and models """
    
    door_schematic_line_thickness = 0.04

    def __init__(
            self,
            anchor_point: tuple[float, float],
            doorway_width: float,
            door_width: float,
            thickness: float,
            orientation_angle: float = 0,
            to_the_right: bool = False,
            hinges_point: float = 0.95,
            opening_outside: bool = False,
     ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates (in meters) of anchor point; here, it is the door frame corner
            that is on the same side with hinges and is on the side where the door opens
            (given `to_the_right` is set to `False`, else it is on the opposite side)
        :param doorway_width:
            width of the doorway (in meters), i.e. width of the door itself
            plus the width of both sides of the door frame
        :param door_width:
            width of the door itself (in meters)
        :param thickness:
            thickness of the door (in meters)
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the doorway;
            it is measured between X-axis and the doorway in positive direction (counterclockwise);
            initial doorway is rotated around anchor point to get the desired orientation
        :param to_the_right:
            binary indicator whether the door opens to the right if someone looks at it
            from the hinges point along the doorway
        :param color:
            color to use for drawing the window
        :param hinges_point:
            relative position of the hinges along the doorway (0.0 = start, 1.0 = end, 0.5 = middle)
        :param label:
            optional label for the element
        :param kwargs:
            additional parameters (e.g., texture_scale, textures, v_anchor, height, id)
        :return:
            freshly created instance of `Door` class
        """
        self.anchor_point=anchor_point
        self.orientation_angle = orientation_angle
        self.doorway_width = doorway_width
        self.thickness = thickness
        self.door_width = door_width
        self.frame_width = (doorway_width - door_width) / 2
        self.to_the_right = to_the_right
        # If opening outside, take the opposite hinges point so "1.0" is always extended hinges
        self.hinges_depth = 1 - hinges_point  if opening_outside else hinges_point
        self.opening_outside = opening_outside

    def getHingesDepth(self) -> float:
        """Return the relative position of the hinges along the doorway."""
        return self.hinges_depth

    def getHingesAndArcAnchorPoint(self, door_wing_thickness: float) -> tuple[tuple[float, float], tuple[float, float]]:
        """Return coordinates of the hinges point and the arc anchor point."""
        return self.getHingesAndArcAnchorPointAt(self.anchor_point, door_wing_thickness)

    def getTextRotation(self) -> float:
        """Calculate text rotation angle to maintain readability based on door orientation."""
        if self.opening_outside:
            base_rotation = 40 + ( RIGHT_ANGLE_IN_DEGREES *2 if self.to_the_right else RIGHT_ANGLE_IN_DEGREES *3 )
        else:
            base_rotation = 40 + ( RIGHT_ANGLE_IN_DEGREES if self.to_the_right else 0 )
        return (360 + base_rotation + self.orientation_angle) % 360

    def render_door_label_and_id(self, parent, element_type, ax: matplotlib.axes.Axes) -> None:
        hinges_point, _ = self.getHingesAndArcAnchorPoint(self.door_schematic_line_thickness)
        # Render label and ID at hinges point with rotation offset
        textrotation = self.getTextRotation()
        
        render_label_and_id(
            ax,
            parent,
            element_type,
            hinges_point,
            textrotation,
            label_prefix="   ---",
            id_prefix="   ---"
        )


    def getHingesAndArcAnchorPointAt(self, anchor_point, door_wing_thickness: float) -> tuple[tuple[float, float], tuple[float, float]]:
        """Return coordinates of the hinges point and the arc anchor point."""
        orientation_angle_in_rad = math.radians(self.orientation_angle)
        # If doors are opening outside, need to offset for thickness as the rectangle gets rotated additional 180
        if self.opening_outside:
            anchor_point_x_offset = door_wing_thickness
        else:
            anchor_point_x_offset = 0
        
        if self.to_the_right:
            hinges_point = rotate_point(anchor_point=anchor_point,
                                     offset_x=-door_wing_thickness + self.frame_width + self.door_width + anchor_point_x_offset,
                                     offset_y=self.thickness * self.hinges_depth,
                                     angle_rad=orientation_angle_in_rad)
            arc_anchor_point = rotate_point(anchor_point=anchor_point,
                                     offset_x=-door_wing_thickness +self.frame_width + self.door_width ,
                                     offset_y=self.thickness * self.hinges_depth,
                                     angle_rad=orientation_angle_in_rad)

        else:
            hinges_point = rotate_point(anchor_point=anchor_point,
                                     offset_x=self.frame_width + anchor_point_x_offset,
                                     offset_y=self.thickness * self.hinges_depth,
                                     angle_rad=orientation_angle_in_rad)
            arc_anchor_point = rotate_point(anchor_point=anchor_point,
                                     offset_x=self.frame_width + door_wing_thickness,
                                     offset_y=self.thickness * self.hinges_depth,
                                     angle_rad=orientation_angle_in_rad)
        return hinges_point, arc_anchor_point
    

    def draw2D(self, draw_color, z_orderm, ax: matplotlib.axes.Axes) -> None:
        """Draw the door, its opening trajectory, and the door frame."""
        # Check if element should be drawn (handles invisible color)
        
        if draw_color is None:
            return
        
        orientation_angle_in_rad = math.radians(self.orientation_angle)

        frame_orientation_angle = self.orientation_angle

        # Draw a part of frame up to the hinges
        frame_with_hinges = Rectangle(
            self.anchor_point,
            self.frame_width,
            self.thickness,
            angle=frame_orientation_angle,
            facecolor=draw_color
        )
        frame_with_hinges.set_zorder(z_orderm)
        ax.add_patch(frame_with_hinges)
        # Draw a whole in the wall
        shift = self.frame_width
        whole_in_the_wall_anchor = (
            self.anchor_point[0] + math.cos(orientation_angle_in_rad) * shift,
            self.anchor_point[1] + math.sin(orientation_angle_in_rad) * shift
        )
        whole_in_a_wall = Rectangle(
            whole_in_the_wall_anchor,
            self.door_width,
            self.thickness,
            angle=frame_orientation_angle,
            facecolor='white'
        )
        whole_in_a_wall.set_zorder(z_orderm)
        ax.add_patch(whole_in_a_wall)
        # Draw a part of frame opposite to the hinges.
        shift = self.frame_width + self.door_width
        frame_without_hinges_anchor_point = (
            self.anchor_point[0] + math.cos(orientation_angle_in_rad) * shift,
            self.anchor_point[1] + math.sin(orientation_angle_in_rad) * shift
        )
        frame_without_hinges = Rectangle(
            frame_without_hinges_anchor_point,
            self.frame_width,
            self.thickness,
            angle=frame_orientation_angle,
            facecolor=draw_color
        )
        frame_without_hinges.set_zorder(z_orderm)
        ax.add_patch(frame_without_hinges)
        # Draw dimension arrow for the doorway width if specified in options
        if get_element_option("Door","dimensions"):
            dims_point = rotate_point(anchor_point=self.anchor_point,
                                    offset_x=self.frame_width,
                                    offset_y=self.thickness * 0.8 if self.opening_outside else self.thickness * 0.2,
                                    angle_rad=orientation_angle_in_rad)
            dimension = DimensionArrow(
                anchor_point=dims_point,
                length=self.door_width,
                orientation_angle=frame_orientation_angle,
                annotate_above=not self.opening_outside,
                color=get_element_option("Door","label_color", "black")
            )
            dimension.draw(ax)

        hinges_point, arc_anchor_point = self.getHingesAndArcAnchorPoint(self.door_schematic_line_thickness)

        door = Rectangle(
                        hinges_point,
                        self.door_schematic_line_thickness, self.door_width,
                        angle=self.orientation_angle + (180 if self.opening_outside else 0), # Additional rot if opening outside
                        facecolor=draw_color
                        #facecolor='orange'
            )
        door.set_zorder(z_orderm)
        ax.add_patch(door)

        extra_degrees_for_smooth_connection = 2
        if self.opening_outside:
            if self.to_the_right:
                start_angle = RIGHT_ANGLE_IN_DEGREES + RIGHT_ANGLE_IN_DEGREES
                end_angle = RIGHT_ANGLE_IN_DEGREES *3 + extra_degrees_for_smooth_connection
            else:
                start_angle = -RIGHT_ANGLE_IN_DEGREES - extra_degrees_for_smooth_connection
                end_angle =  0
        else:
            if self.to_the_right:
                start_angle = RIGHT_ANGLE_IN_DEGREES - extra_degrees_for_smooth_connection
                end_angle = RIGHT_ANGLE_IN_DEGREES + RIGHT_ANGLE_IN_DEGREES
            else:
                start_angle = 0
                end_angle = RIGHT_ANGLE_IN_DEGREES + extra_degrees_for_smooth_connection
        arc = Arc(
            arc_anchor_point,
            2 * (self.door_width - self.door_schematic_line_thickness),
            2 * self.door_width,
            angle=self.orientation_angle,
            theta1=start_angle,
            theta2=end_angle,
            color=draw_color,
            linewidth=1
        )
        arc.set_zorder(z_orderm)
        ax.add_patch(arc)

class Door(VertInfoDoor, RectangularElement):
    door_schematic_line_thickness = 0.04
    """Single door."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            doorway_width: float,
            door_width: float,
            thickness: float,
            orientation_angle: float = 0,
            to_the_right: bool = False,
            color: str = 'black',
            hinges_point: float = 0.95,
            opening_outside: bool = False,
            label: str | None = None,
            **kwargs
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates (in meters) of anchor point; here, it is the door frame corner
            that is on the same side with hinges and is on the side where the door opens
            (given `to_the_right` is set to `False`, else it is on the opposite side)
        :param doorway_width:
            width of the doorway (in meters), i.e. width of the door itself
            plus the width of both sides of the door frame
        :param door_width:
            width of the door itself (in meters)
        :param thickness:
            thickness of the door (in meters)
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the doorway;
            it is measured between X-axis and the doorway in positive direction (counterclockwise);
            initial doorway is rotated around anchor point to get the desired orientation
        :param to_the_right:
            binary indicator whether the door opens to the right if someone looks at it
            from the hinges point along the doorway
        :param color:
            color to use for drawing the window
        :param hinges_point:
            relative position of the hinges along the doorway (0.0 = start, 1.0 = end, 0.5 = middle)
        :param label:
            optional label for the element
        :param kwargs:
            additional parameters (e.g., texture_scale, textures, v_anchor, height, id)
        :return:
            freshly created instance of `Door` class
        """
        self.door2d = Door2D(anchor_point,doorway_width,door_width,thickness,
                        orientation_angle,to_the_right,hinges_point,
                        opening_outside)

        #RectangularElement:
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=doorway_width,
            thickness=thickness,
            color=color,
            label=label,
            **kwargs
        )

    def _default_height(self) -> float:
        """Return default height for doors (standard door height)."""
        return 2.1

    def get_to_the_right(self) -> bool:
        """Return whether the door opens to the right."""
        return self.door2d.to_the_right
    def get_doorway_width(self) -> float:
        """Return the doorway width."""
        return self.door2d.doorway_width
    def get_door_width(self) -> float:
        """Return the door width."""
        return self.door2d.door_width


    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the door """
        draw_color = self.get_draw_color()
        if draw_color is None:
            return
        z_order = self.get_zorder()
        self.door2d.draw2D(draw_color, z_order, ax)
        self.door2d.render_door_label_and_id(self, self.__class__.__name__, ax)



