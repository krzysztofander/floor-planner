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


class Door3DHinged:
    """
    Helper that computes the 3D wing-animation normalization and offset for a
    door element.  Shared by BalconyDoor (external-model path) and Door /
    SolidGlassDoor (procedural path).

    Three parameters drive the geometry mapping:

    TODO: Fix that after AI as the `model_depth` not entirely works
    --------------------------------------------------------------

    ``model_door_width``   – Width of the door model mesh (metres).
                             Sets stretch = doorway_width / model_door_width.
                             • External model (balcony_door / window_door): 0.9 m
                             • Procedural Door: pass doorway_width → stretch = 1

    ``wing_width_on_model``– Z-depth of the door-wing mesh in model coordinates.
                             Used for pre_translation[2] (move hinge to origin)
                             and as the ``W`` term in the z_shift formula.
                             • External model: 0.12 m (back of the wing)
                             • Procedural Door: thickness × hinges_depth

    ``model_depth``        – Total Z-depth of the model frame (metres).
                             Used only in the z_shift formula:
                               z_shift = W + (thickness − model_depth) × H
                             Defaults to ``wing_width_on_model``.
                             • External model: 0.12 m (same as wing_width_on_model)
                             • Procedural Door: thickness (full wall depth)

    Why three parameters?  The z_shift formula `W + (T − W) × H` gives T×H only
    when W = 0, but pre_translation[2] = −W needs W = T×H.  Making model_depth
    independent of W resolves the conflict: with W = T×H and model_depth = T the
    formula gives  T×H + (T − T)×H = T×H  ✓ and pre[2] = −T×H ✓.
    """

    def __init__(
            self,
            doorway_width: float,
            door_width: float,
            thickness: float,
            opening_outside: bool = False,
            to_the_right: bool = False,
            hinges_depth: float = 0.95,
            model_door_width: float = 0.9,
            wing_width_on_model: float = 0.12,
            model_depth: float | None = None,
    ):
        self.doorway_width   = doorway_width
        self.door_width      = door_width
        self.opening_outside = opening_outside
        self.to_the_right    = to_the_right
        self.thickness       = thickness
        self.hinges_depth    = hinges_depth
        self.model_door_width      = model_door_width
        self.wing_width_on_model   = wing_width_on_model
        self.model_depth           = model_depth if model_depth is not None else wing_width_on_model
        self.secondary_normalization  = {'scale': [1,1,1], 'rotation': [0,0,0], 'translation': [0,0,0]}
        self.secondary_anchor_offset  = [0, 0, 0]

    def getSecondaryNormalization(self): return self.secondary_normalization
    def getSecondaryAnchorOffset(self):  return self.secondary_anchor_offset
    def getPreAnimationTRS(self):  return {'pre_translation': self.pre_translation,  'pre_rotation': self.pre_rotation,  'pre_scale': self.pre_scale}
    def getPostAnimationTRS(self): return {'post_translation': self.post_translation, 'post_rotation': self.post_rotation, 'post_scale': self.post_scale}

    def getTranslation(self): return [0,0,0]
    def getRotation(self): return [0, self.openingMaxAngle, 0]
    def getScale(self): return [1,1,1]

    def calcNormalisationAndOffset(self):
        WW     = self.wing_width_on_model
        MD     = self.model_door_width
        depth  = self.model_depth   # replaces WING_WIDTH in the (T – depth) term
        stretch = self.doorway_width / MD

        self.pre_translation = [0, 0, 0]
        self.pre_rotation    = [0, 0, 0]
        self.pre_scale       = [stretch, 1, 1]

        if self.opening_outside:
            if self.to_the_right:
                open_deg   = 180
                hinge_pt   = [0, WW]
                x_shift    = self.doorway_width
                z_shift    = (self.thickness - depth) * self.hinges_depth
                self.pre_translation[2] = WW
                self.pre_rotation[1]    = 180
                self.openingMaxAngle    = -90
            else:
                open_deg   = 0
                hinge_pt   = [0, 0]
                x_shift    = 0
                z_shift    = (self.thickness - depth) * self.hinges_depth
                self.pre_translation[2] = 0
                self.pre_rotation[1]    = 0
                self.openingMaxAngle    = 90
        else:
            if self.to_the_right:
                open_deg   = 180
                hinge_pt   = [0, 0]
                x_shift    = self.doorway_width
                z_shift    = WW + (self.thickness - depth) * self.hinges_depth
                self.pre_translation[2] = 0
                self.pre_rotation[1]    = 180
                self.openingMaxAngle    = 90
            else:
                open_deg   = 0
                hinge_pt   = [0, WW]
                x_shift    = 0
                z_shift    = WW + (self.thickness - depth) * self.hinges_depth
                self.pre_translation[2] = -WW
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


class Door2DHinged():
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
        shift = self.frame_width_left + self.door_width
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


# ──────────────────────────────────────────────────────────────────────────────
# Sliding door helpers
# ──────────────────────────────────────────────────────────────────────────────

class SlidingDoor2D:
    """
    2-D floor-plan representation of a sliding door.

    In plan view the door is drawn as:
      • Two solid frame bars on either side of the opening (same as Door2D).
      • A white gap clearing the wall at the opening.
      • A filled rectangle representing the door panel in the CLOSED position
        (thin, parallel to the wall, spanning the full door_width).
      • A dashed rectangle at the OPEN position (panel slid by door_width in
        the slide direction).
      • A short arrow indicating the slide direction.
    """

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
            door_orientation_in_doorway: float = 0.5,
    ):
        self.anchor_point = anchor_point
        self.orientation_angle = orientation_angle
        self.doorway_width = doorway_width
        self.thickness = thickness
        self.door_width = door_width
        self.frame_width_left  = (doorway_width - door_width) * door_orientation_in_doorway
        self.frame_width_right = (doorway_width - door_width) * (1 - door_orientation_in_doorway)
        self.to_the_right = to_the_right
        # Re-use Door2D convention: hinges_depth determines panel depth in wall
        self.hinges_depth = (1 - hinges_point) if opening_outside else hinges_point
        self.opening_outside = opening_outside

    def getHingesDepth(self) -> float:
        return self.hinges_depth

    def getTextRotation(self) -> float:
        return (360 + 40 + self.orientation_angle) % 360

    def render_door_label_and_id(
            self, parent, element_type, ax: matplotlib.axes.Axes
    ) -> None:
        angle_rad = math.radians(self.orientation_angle)
        label_pt = rotate_point(
            anchor_point=self.anchor_point,
            offset_x=self.frame_width_left + self.door_width / 2,
            offset_y=self.thickness / 2,
            angle_rad=angle_rad,
        )
        render_label_and_id(
            ax, parent, element_type, label_pt,
            self.getTextRotation(),
            label_prefix='   ---', id_prefix='   ---',
        )

    def draw2D(self, draw_color, z_order, ax: matplotlib.axes.Axes) -> None:
        """Draw the sliding door in 2D floor-plan style."""
        if draw_color is None:
            return

        angle_rad = math.radians(self.orientation_angle)

        # ── Left frame bar ────────────────────────────────────────────────────
        frame_left = Rectangle(
            self.anchor_point,
            self.frame_width_left, self.thickness,
            angle=self.orientation_angle,
            facecolor=draw_color,
        )
        frame_left.set_zorder(z_order)
        ax.add_patch(frame_left)

        # ── White gap (hole in wall at door opening) ──────────────────────────
        gap_anchor = rotate_point(self.anchor_point, self.frame_width_left, 0, angle_rad)
        gap = Rectangle(
            gap_anchor,
            self.door_width, self.thickness,
            angle=self.orientation_angle,
            facecolor='white',
        )
        gap.set_zorder(z_order)
        ax.add_patch(gap)

        # ── Right frame bar ───────────────────────────────────────────────────
        right_anchor = rotate_point(
            self.anchor_point,
            self.frame_width_left + self.door_width, 0,
            angle_rad,
        )
        frame_right = Rectangle(
            right_anchor,
            self.frame_width_right, self.thickness,
            angle=self.orientation_angle,
            facecolor=draw_color,
        )
        frame_right.set_zorder(z_order)
        ax.add_patch(frame_right)

        # ── Door panel – CLOSED position (solid thin rectangle along wall) ────
        panel_y = (self.thickness * self.hinges_depth
                   - self.door_schematic_line_thickness / 2)
        panel_anchor = rotate_point(
            self.anchor_point,
            self.frame_width_left, panel_y, angle_rad,
        )
        panel = Rectangle(
            panel_anchor,
            self.door_width, self.door_schematic_line_thickness,
            angle=self.orientation_angle,
            facecolor=draw_color,
        )
        panel.set_zorder(z_order)
        ax.add_patch(panel)

        # ── Door panel – OPEN position (dashed rectangle, slid to one side) ───
        slide_sign = 1 if self.to_the_right else -1
        open_panel_anchor = rotate_point(
            self.anchor_point,
            self.frame_width_left + slide_sign * self.door_width,
            panel_y,
            angle_rad,
        )
        open_panel = Rectangle(
            open_panel_anchor,
            self.door_width, self.door_schematic_line_thickness,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=0.8,
            linestyle='--',
        )
        open_panel.set_zorder(z_order)
        ax.add_patch(open_panel)

        # ── Arrow indicating slide direction (drawn along the wall) ──────────
        cx = self.frame_width_left + self.door_width / 2
        cy = panel_y + self.door_schematic_line_thickness / 2
        arrow_len = self.door_width * 0.35 * slide_sign

        tail = rotate_point(self.anchor_point, cx - arrow_len / 2, cy, angle_rad)
        head = rotate_point(self.anchor_point, cx + arrow_len / 2, cy, angle_rad)
        ax.annotate(
            '', xy=(head[0], head[1]), xytext=(tail[0], tail[1]),
            arrowprops=dict(arrowstyle='->', color=draw_color, lw=1.0),
            zorder=z_order,
        )


class SlidingDoor3D:
    """
    Helper that computes the 3-D slide-animation data for a sliding door.

    Same API as Door3D (``calcNormalisationAndOffset``, ``getPreAnimationTRS``,
    ``getPostAnimationTRS``, ``getSecondaryNormalization``, …) so it can be
    dropped into BalconyDoor-style elements without changing the surrounding
    code.

    Parameters share defaults with Door3D:
        model_door_width      – model mesh width (default 0.9 m for balcony_door)
        wing_width_on_model   – Z-depth of the wing in model coordinates (0.12 m)
        model_depth           – total frame depth used in z_shift formula

    The animation ``TRS`` carries the slide vector:
        translation = [±door_width, 0, 0]   (X = along wall direction)
        rotation    = [0, 0, 0]             (no rotation)
    """

    def __init__(
            self,
            doorway_width: float,
            door_width: float,
            thickness: float,
            opening_outside: bool = False,
            to_the_right: bool = False,
            hinges_depth: float = 0.95,
            model_door_width: float = 0.9,
            wing_width_on_model: float = 0.12,
            model_depth: float | None = None,
    ):
        self.doorway_width        = doorway_width
        self.door_width           = door_width
        self.opening_outside      = opening_outside
        self.to_the_right         = to_the_right
        self.thickness            = thickness
        self.hinges_depth         = hinges_depth
        self.model_door_width     = model_door_width
        self.wing_width_on_model  = wing_width_on_model
        self.model_depth          = (model_depth if model_depth is not None
                                     else wing_width_on_model)
        self.secondary_normalization = {'scale': [1,1,1], 'rotation': [0,0,0], 'translation': [0,0,0]}
        self.secondary_anchor_offset = [0, 0, 0]

    def getSecondaryNormalization(self): return self.secondary_normalization
    def getSecondaryAnchorOffset(self):  return self.secondary_anchor_offset
    def getPreAnimationTRS(self):
        return {'pre_translation': self.pre_translation,
                'pre_rotation':    self.pre_rotation,
                'pre_scale':       self.pre_scale}
    def getPostAnimationTRS(self):
        return {'post_translation': self.post_translation,
                'post_rotation':    self.post_rotation,
                'post_scale':       self.post_scale}
    def getOpenTranslation(self) -> list:
         """Return the slide vector [tx, 0, 0] for the open position."""
         return self.open_translation

    def getTranslation(self): return self.open_translation
    def getRotation(self): return [0, 0, 0]
    def getScale(self): return [1,1,1]


    def calcNormalisationAndOffset(self):
        WW    = self.wing_width_on_model
        depth = self.model_depth
        stretch = self.doorway_width / self.model_door_width

        # Z depth of panel in wall. Different formula as  wanting to move door outside of frame
        z_shift = WW + (self.thickness) * self.hinges_depth

        # Static closed position (identical to Door3D left-inside convention)
        self.secondary_normalization = {
            'scale':       [stretch, 1, 1],
            'rotation':    [0, 0, 0],
            'translation': [0, 0, -WW],
        }
        self.secondary_anchor_offset = [0, 0, -z_shift]

        # Slide direction: to_the_right=True → +X, False → –X
        slide_sign = 1 if self.to_the_right else -1
        slide_x    = slide_sign * self.door_width

        # Pre/post: place the mesh at the correct wall depth, then restore
        self.pre_translation  = [0, 0, -WW]
        self.pre_rotation     = [0, 0, 0]
        self.pre_scale        = [stretch, 1, 1]

        self.open_translation = [slide_x * stretch*0.999 , 0, 0]   # the slide (used in addTRS)
                                                                   # 0.999 to avoid z-fighting with the wall 

        self.post_translation = [0, 0, z_shift]
        self.post_rotation    = [0, 0, 0]
        self.post_scale       = [1, 1, 1]

class Door2D():
    """Helper for drawing a door, used both for programmatic doors and models """
    def __init__(
            self,
            anchor_point: tuple[float, float],
            doorway_width: float,
            door_width: float,
            thickness: float,
            door_type: str, 
            orientation_angle: float = 0,
            to_the_right: bool = False,
            hinges_point: float = 0.95,
            opening_outside: bool = False,
            door_orientation_in_doorway: float = 0.5
     ):
        if door_type == 'hinged':
            self.door2D = Door2DHinged(
                anchor_point,doorway_width,door_width,thickness,
                orientation_angle,to_the_right,hinges_point,
                opening_outside,door_orientation_in_doorway)
        elif door_type == 'sliding':
            self.door2D = SlidingDoor2D(
                anchor_point, doorway_width, door_width, thickness,
                orientation_angle, to_the_right, hinges_point,
                opening_outside, door_orientation_in_doorway)
        else:
            raise ValueError("need type")

    def render_door_label_and_id(self, parent, element_type, ax: matplotlib.axes.Axes) -> None:
        self.door2D.render_door_label_and_id(parent, element_type, ax)

    def draw2D(self, draw_color, z_order, ax: matplotlib.axes.Axes) -> None:
        self.door2D.draw2D(draw_color, z_order, ax)

    def getHingesDepth(self):
        return self.door2D.getHingesDepth()

    def get_to_the_right(self) -> bool:
        """Return whether the door opens to the right."""
        return self.door2D.to_the_right
   
    def get_doorway_width(self) -> float:
        """Return the doorway width."""
        return self.door2D.doorway_width
   
    def get_door_width(self) -> float:
        """Return the door width."""
        return self.door2D.door_width


class Door3D:
    """ Helper that computes the 3D animation normalization and offset for a door element."""
    def __init__(
            self,
            doorway_width: float,
            door_width: float,
            thickness: float,
            door_type: str, 
            opening_outside: bool = False,
            to_the_right: bool = False,
            hinges_depth: float = 0.95,
            model_door_width: float = 0.9,
            wing_width_on_model: float = 0.12,
            model_depth: float | None = None,
    ):
        self.secondary_normalization  = {'scale': [1,1,1], 'rotation': [0,0,0], 'translation': [0,0,0]}
        self.secondary_anchor_offset  = [0, 0, 0]
        if door_type == 'hinged':
            self.door3D = Door3DHinged(
                doorway_width=doorway_width,
                door_width=door_width,
                thickness=thickness,
                opening_outside=opening_outside,
                to_the_right=to_the_right,
                hinges_depth= hinges_depth,
                model_door_width = model_door_width,
                wing_width_on_model = wing_width_on_model,
                model_depth=model_depth)        
        elif door_type == 'sliding':
            self.door3D = SlidingDoor3D(
                doorway_width=doorway_width,
                door_width=door_width,
                thickness=thickness,
                opening_outside=opening_outside,
                to_the_right=to_the_right,
                hinges_depth= hinges_depth,
                model_door_width = model_door_width,
                wing_width_on_model = wing_width_on_model,
                model_depth=model_depth) 
        elif door_type == 'fixture':
            self.door3D = None;
        else:
            raise ValueError("need type")

    def getSecondaryNormalization(self): return self.secondary_normalization
    def getSecondaryAnchorOffset(self):  return self.secondary_anchor_offset
    def getAnimation(self):
        if self.door3D:
            self.door3D.calcNormalisationAndOffset()
            anim_meta = AnimationMetadata(AnimationMetadata.TriggerType.PROXIMITY)
            anim_meta.addPreTRS(
                translation=self.door3D.getPreAnimationTRS()['pre_translation'],
                rotation=self.door3D.getPreAnimationTRS()['pre_rotation'],
                scale=self.door3D.getPreAnimationTRS()['pre_scale'],
            )
            anim_meta.addTRS(
                translation=self.door3D.getTranslation(),
                rotation=self.door3D.getRotation(),
                scale=self.door3D.getScale(),
            )
            anim_meta.addPostTRS(
                translation=self.door3D.getPostAnimationTRS()['post_translation'],
                rotation=self.door3D.getPostAnimationTRS()['post_rotation'],
                scale=self.door3D.getPostAnimationTRS()['post_scale'],
            )
            anim_meta.addActivation(
                point=(self.door3D.doorway_width / 2, 1.2, -0.5 if self.door3D.opening_outside else 0.5),
                distance=(2.0, 1),
            )
            return anim_meta.getAnimation()
        else:
            return None

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
            door_type: str='hinged',
            id: str | None = None,
            v_anchor: float | None = None,
            height: float | None = None,
            textures: dict | None = None
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
        :param door_type:
            'hinged' (default) or 'sliding'
        :param id:
            optional explicit ID; if None, generated from class name and label
        :param v_anchor:
            optional vertical anchor point in meters; if None, uses element's default vertical level
        :param height:
            optional height of the door in meters; if None, uses element's default height
        :param textures:
            optional per-face textures and lighting for the 3D export
            (see ``floor_planner.face_textures``); None = class defaults and .mtl
        :return:
            freshly created instance of `Door` class
        """
        self.door2d = Door2D(anchor_point, doorway_width, door_width, thickness,
                        door_type, orientation_angle, to_the_right, hinges_point,
                        opening_outside)

        #RectangularElement:
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=doorway_width,
            thickness=thickness,
            color=color,
            label=label,
            id=id,
            v_anchor=v_anchor,
            height=height,
            textures=textures
        )

        # ── 3-D door-swing animation ─────────────────────────────────────────
        # Reuse Door3D with procedural parameters so the same class drives
        # both external-model and procedural doors.
        #
        # model_door_width = doorway_width  → stretch = 1 (geometry is already
        #                                     at actual scale, no mesh distortion)
        # wing_width_on_model = T × H       → correct Z pre-translation so the
        #                                     hinge sits at origin before rotation
        # model_depth = thickness            → fixes z_shift = W+(T-depth)×H
        #                                     = T×H (not T×H×(2-H))
        #
        # The X hinge position (pre_translation[0]) defaults to 0 in Door3D
        # (external models have their hinge at x=0).  For procedural geometry
        # the hinge is inside the frame bar, so we override it afterwards.

        hinges_depth = self.door2d.getHingesDepth()
        door3d = Door3D(
            doorway_width=doorway_width,
            door_width=door_width,
            thickness=thickness,
            door_type=door_type,
            opening_outside=opening_outside,
            to_the_right=to_the_right,
            hinges_depth=hinges_depth,
            model_door_width=doorway_width,                 # stretch = 1
            wing_width_on_model=thickness,
            model_depth=thickness,                          # full wall depth
        )
        self.animation = door3d.getAnimation()

    def get_to_the_right(self) -> bool:
        """Return whether the door opens to the right."""
        return self.door2d.get_to_the_right()
    def get_doorway_width(self) -> float:
        """Return the doorway width."""
        return self.door2d.get_doorway_width()
    def get_door_width(self) -> float:
        """Return the door width."""
        return self.door2d.get_door_width()


    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the door """
        draw_color = self.get_draw_color()
        if draw_color is None:
            return
        z_order = self.get_zorder()
        self.door2d.draw2D(draw_color, z_order, ax)
        self.door2d.render_door_label_and_id(self, self.__class__.__name__, ax)


