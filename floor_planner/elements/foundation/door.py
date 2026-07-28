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
from floor_planner.motion_3d import AnimationMetadata


class Door3D:
    """
    Helper that computes the 3D wing-animation normalization and offset for a
    door element.  Shared by BalconyDoor (external-model path) and Door /
    SolidGlassDoor (procedural path).
    """

    def __init__(
            self,
            doorway_width: float,
            door_width: float,
            thickness: float,
            opening_outside: bool = False,
            to_the_right: bool = False,
            hinges_depth: float = 0.95,
    ):
        self.doorway_width   = doorway_width
        self.door_width      = door_width
        self.opening_outside = opening_outside
        self.to_the_right    = to_the_right
        self.thickness       = thickness
        self.hinges_depth    = hinges_depth
        self.secondary_normalization  = {'scale': [1,1,1], 'rotation': [0,0,0], 'translation': [0,0,0]}
        self.secondary_anchor_offset  = [0, 0, 0]

    def getSecondaryNormalization(self): return self.secondary_normalization
    def getSecondaryAnchorOffset(self):  return self.secondary_anchor_offset
    def getPreAnimationTRS(self):  return {'pre_translation': self.pre_translation,  'pre_rotation': self.pre_rotation,  'pre_scale': self.pre_scale}
    def getPostAnimationTRS(self): return {'post_translation': self.post_translation, 'post_rotation': self.post_rotation, 'post_scale': self.post_scale}
    def getOpeningAngle(self):     return self.openingMaxAngle

    def calcNormalisationAndOffset(self):
        WING_WIDTH_ON_MODEL  = 0.12
        MODEL_DOOR_WIDTH     = 0.9
        stretch              = self.doorway_width / MODEL_DOOR_WIDTH

        self.pre_translation = [0, 0, 0]
        self.pre_rotation    = [0, 0, 0]
        self.pre_scale       = [stretch, 1, 1]

        if self.opening_outside:
            if self.to_the_right:
                open_deg   = 180
                hinge_pt   = [0, WING_WIDTH_ON_MODEL]
                x_shift    = self.doorway_width
                z_shift    = (self.thickness - WING_WIDTH_ON_MODEL) * self.hinges_depth
                self.pre_translation[2] = WING_WIDTH_ON_MODEL
                self.pre_rotation[1]    = 180
                self.openingMaxAngle    = -90
            else:
                open_deg   = 0
                hinge_pt   = [0, 0]
                x_shift    = 0
                z_shift    = (self.thickness - WING_WIDTH_ON_MODEL) * self.hinges_depth
                self.pre_translation[2] = 0
                self.pre_rotation[1]    = 0
                self.openingMaxAngle    = 90
        else:
            if self.to_the_right:
                open_deg   = 180
                hinge_pt   = [0, 0]
                x_shift    = self.doorway_width
                z_shift    = WING_WIDTH_ON_MODEL + (self.thickness - WING_WIDTH_ON_MODEL) * self.hinges_depth
                self.pre_translation[2] = 0
                self.pre_rotation[1]    = 180
                self.openingMaxAngle    = 90
            else:
                open_deg   = 0
                hinge_pt   = [0, WING_WIDTH_ON_MODEL]
                x_shift    = 0
                z_shift    = WING_WIDTH_ON_MODEL + (self.thickness - WING_WIDTH_ON_MODEL) * self.hinges_depth
                self.pre_translation[2] = -WING_WIDTH_ON_MODEL
                self.pre_rotation[1]    = 0
                self.openingMaxAngle    = -90

        pt = rotate_point([0, 0], hinge_pt[0], hinge_pt[1], math.radians(open_deg))
        self.secondary_normalization  = {
            'scale':       [stretch, 1, 1],
            'rotation':    [0, open_deg, 0],
            'translation': [pt[0], 0, -pt[1]],
        }
        self.secondary_anchor_offset  = [-x_shift, 0, -z_shift]
        self.post_translation = [x_shift, 0, z_shift]
        self.post_rotation    = [0, 0, 0]
        self.post_scale       = [1, 1, 1]


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
            door_orientation_in_doorway: float = 0.5
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
            additional parameters (e.g., texture_scale,  v_anchor, height, id)
        :return:
            freshly created instance of `Door` class
        """
        self.anchor_point=anchor_point
        self.orientation_angle = orientation_angle
        self.doorway_width = doorway_width
        self.thickness = thickness
        self.door_width = door_width
        self.frame_width_left = (doorway_width - door_width) * door_orientation_in_doorway 
        self.frame_width_right = (doorway_width - door_width) * (1 - door_orientation_in_doorway)
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
                                     offset_x=-door_wing_thickness + self.frame_width_left + self.door_width + anchor_point_x_offset,
                                     offset_y=self.thickness * self.hinges_depth,
                                     angle_rad=orientation_angle_in_rad)
            arc_anchor_point = rotate_point(anchor_point=anchor_point,
                                     offset_x=-door_wing_thickness +self.frame_width_left + self.door_width ,
                                     offset_y=self.thickness * self.hinges_depth,
                                     angle_rad=orientation_angle_in_rad)

        else:
            hinges_point = rotate_point(anchor_point=anchor_point,
                                     offset_x=self.frame_width_left + anchor_point_x_offset,
                                     offset_y=self.thickness * self.hinges_depth,
                                     angle_rad=orientation_angle_in_rad)
            arc_anchor_point = rotate_point(anchor_point=anchor_point,
                                     offset_x=self.frame_width_left + door_wing_thickness,
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
            self.frame_width_left,
            self.thickness,
            angle=frame_orientation_angle,
            facecolor=draw_color
        )
        frame_with_hinges.set_zorder(z_orderm)
        ax.add_patch(frame_with_hinges)
        # Draw a whole in the wall
        shift = self.frame_width_left
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
        shift = self.frame_width_right + self.door_width
        frame_without_hinges_anchor_point = (
            self.anchor_point[0] + math.cos(orientation_angle_in_rad) * shift,
            self.anchor_point[1] + math.sin(orientation_angle_in_rad) * shift
        )
        frame_without_hinges = Rectangle(
            frame_without_hinges_anchor_point,
            self.frame_width_right,
            self.thickness,
            angle=frame_orientation_angle,
            facecolor=draw_color
        )
        frame_without_hinges.set_zorder(z_orderm)
        ax.add_patch(frame_without_hinges)
        # Draw dimension arrow for the doorway width if specified in options
        if get_element_option("Door","dimensions"):
            dims_point = rotate_point(anchor_point=self.anchor_point,
                                    offset_x=self.frame_width_left,
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
            additional parameters (e.g., texture_scale, v_anchor, height, id)
        :return:
            freshly created instance of `Door` class
        """
        self.door2d = Door2D(anchor_point, doorway_width, door_width, thickness,
                        orientation_angle, to_the_right, hinges_point,
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

        # ── 3-D door-swing animation (procedural – correct pivot) ─────────────
        # For procedural geometry the mesh is already at actual scale, so we
        # skip Door3D's model-specific stretch / WING_WIDTH constants and
        # compute the pivot directly from the element's own dimensions.
        #
        # The local geometry (generated with anchor=0, v_anchor=0) spans:
        #   X [0 … doorway_width],  Z [0 … thickness],  Y [0 … height]
        #
        # Hinge axis is a vertical line at:
        #   x = frame_width_left  (left-side hinge) or doorway_width - frame_width_right
        #   z = thickness × hinges_depth
        #
        # To rotate around this axis we translate the hinge to the Y-axis,
        # apply the Y-rotation, then translate back.

        hinge_x = self.door2d.frame_width_left
        if to_the_right:
            hinge_x = self.door2d.frame_width_left + self.door2d.door_width
        hinge_z = self.door2d.hinges_depth * thickness

        # Swing direction:
        #   left-inside  → −90°   (door swings into room, +Z direction)
        #   right-inside → +90°
        #   left-outside → +90°   (door swings out, −Z direction)
        #   right-outside→ −90°
        if (not to_the_right and not opening_outside) or (to_the_right and opening_outside):
            open_angle = -90.0
        else:
            open_angle = +90.0

        # secondary_normalization / secondary_anchor_offset are intentionally
        # left un-set here (they remain None via getattr in the exporter).
        # The door renders in CLOSED position by default; the 3-D player
        # drives it open via extras.animation.

        anim_meta = AnimationMetadata(AnimationMetadata.TriggerType.PROXIMITY)
        anim_meta.addPreTRS(
            translation=[-hinge_x, 0.0, -hinge_z],
            rotation=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0],
        )
        anim_meta.addTRS(
            translation=[0.0, 0.0, 0.0],
            rotation=[0.0, open_angle, 0.0],
            scale=[1.0, 1.0, 1.0],
        )
        anim_meta.addPostTRS(
            translation=[hinge_x, 0.0, hinge_z],
            rotation=[0.0, 0.0, 0.0],
            scale=[1.0, 1.0, 1.0],
        )
        anim_meta.addActivation(
            point=(doorway_width / 2, 1.2, -0.5 if opening_outside else 0.5),
            distance=(2.0, 1),
        )
        self.animation = anim_meta.getAnimation()

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



