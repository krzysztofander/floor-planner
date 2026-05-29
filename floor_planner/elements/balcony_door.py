"""
Balcony Door element.

Draws in 2D identically to Door (frame + opening arc), but uses an external
OBJ model for 3D / glTF export.  The model contains a visible door frame,
a lower solid-wood wing panel, and an upper glass panel.

Author: Krzysztof Bartczak
"""

import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle

from ..constants import RIGHT_ANGLE_IN_DEGREES
from ..utils import rotate_point, render_label_and_id
from .external_models import ExternalModelElement
from .info import DimensionArrow
from .options import get_element_option
from .vertical_levels import VertInfoLvl02


class BalconyDoor(VertInfoLvl02, ExternalModelElement):
    """
    Balcony door element.

    In 2D floor plans this looks exactly like a regular Door (frame bars +
    opening arc).  In 3D / glTF export it uses an external OBJ model that
    shows a wooden frame, a solid lower panel, and a glazed upper panel.

    The external model has fixed dimensions (0.9 m × 2.1 m × 0.12 m).
    The 2D drawing honours the YAML-configured doorway_width, door_width
    and thickness parameters so the floor plan stays accurate.

    YAML parameters (same as Door):
        anchor_point     – (x, y) frame corner on the hinge side
        doorway_width    – total width including both frame sides (metres)
        door_width       – clear opening width (metres)
        thickness        – door / wall thickness (metres)
        orientation_angle – degrees counter-clockwise from X-axis
        to_the_right     – door swings to the right when False (default)
        hinges_point     – relative hinge position along thickness (0–1)
        opening_outside  – door opens outward when True
        color            – 2-D drawing colour (default 'black')
        label            – optional text label
    """

    _registry_key = 'balcony_door'
    _requires_external_model = True

    door_schematic_line_thickness = 0.04

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
        # ExternalModelElement.__init__ rejects 'width', 'length', 'height' in kwargs
        # but accepts all other keyword args (v_anchor, id, textures, etc.)
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs
        )

        # Door-specific 2D parameters (not touched by ExternalModelElement)
        self.doorway_width = doorway_width
        self.door_width = door_width
        self.thickness = thickness
        self.frame_width = (doorway_width - door_width) / 2
        self.to_the_right = to_the_right
        self.hinges_point = (1 - hinges_point) if opening_outside else hinges_point
        self.opening_outside = opening_outside

        # length is used by the parent Element / anchor helpers
        self.length = doorway_width

    # ------------------------------------------------------------------
    # ExternalModelElement hooks
    # ------------------------------------------------------------------

    def _default_width(self) -> float:
        return 0.9

    def _default_length(self) -> float:
        return 0.9

    def _default_height(self) -> float:
        return 2.1

    # ------------------------------------------------------------------
    # 2-D drawing – identical to Door.draw()
    # ------------------------------------------------------------------

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the balcony door exactly like a regular Door in 2D."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        orientation_angle_in_rad = math.radians(self.orientation_angle)

        # Frame section on the hinge side
        frame_with_hinges = Rectangle(
            self.anchor_point,
            self.frame_width,
            self.thickness,
            angle=self.orientation_angle,
            facecolor=draw_color
        )
        frame_with_hinges.set_zorder(self.get_zorder())
        ax.add_patch(frame_with_hinges)

        # White gap (the opening in the wall)
        shift = self.frame_width
        hole_anchor = (
            self.anchor_point[0] + math.cos(orientation_angle_in_rad) * shift,
            self.anchor_point[1] + math.sin(orientation_angle_in_rad) * shift,
        )
        whole_in_a_wall = Rectangle(
            hole_anchor,
            self.door_width,
            self.thickness,
            angle=self.orientation_angle,
            facecolor='white'
        )
        whole_in_a_wall.set_zorder(self.get_zorder())
        ax.add_patch(whole_in_a_wall)

        # Frame section on the latch side
        shift2 = self.frame_width + self.door_width
        frame_opp_anchor = (
            self.anchor_point[0] + math.cos(orientation_angle_in_rad) * shift2,
            self.anchor_point[1] + math.sin(orientation_angle_in_rad) * shift2,
        )
        frame_without_hinges = Rectangle(
            frame_opp_anchor,
            self.frame_width,
            self.thickness,
            angle=self.orientation_angle,
            facecolor=draw_color
        )
        frame_without_hinges.set_zorder(self.get_zorder())
        ax.add_patch(frame_without_hinges)

        # Optional dimension arrow
        if get_element_option("BalconyDoor", "dimensions") or get_element_option("Door", "dimensions"):
            dims_point = rotate_point(
                anchor_point=self.anchor_point,
                offset_x=self.frame_width,
                offset_y=self.thickness * (0.8 if self.opening_outside else 0.2),
                angle_rad=orientation_angle_in_rad
            )
            DimensionArrow(
                anchor_point=dims_point,
                length=self.door_width,
                orientation_angle=self.orientation_angle,
                annotate_above=not self.opening_outside,
                color=get_element_option("Door", "label_color", "black")
            ).draw(ax)

        # Schematic door-wing line + opening arc
        anchor_x_offset = self.door_schematic_line_thickness if self.opening_outside else 0

        if self.to_the_right:
            hinges_pt = rotate_point(
                self.anchor_point,
                -self.door_schematic_line_thickness + self.frame_width + self.door_width + anchor_x_offset,
                self.thickness * self.hinges_point,
                orientation_angle_in_rad
            )
            arc_anchor = rotate_point(
                self.anchor_point,
                -self.door_schematic_line_thickness + self.frame_width + self.door_width,
                self.thickness * self.hinges_point,
                orientation_angle_in_rad
            )
        else:
            hinges_pt = rotate_point(
                self.anchor_point,
                self.frame_width + anchor_x_offset,
                self.thickness * self.hinges_point,
                orientation_angle_in_rad
            )
            arc_anchor = rotate_point(
                self.anchor_point,
                self.frame_width + self.door_schematic_line_thickness,
                self.thickness * self.hinges_point,
                orientation_angle_in_rad
            )

        door_wing = Rectangle(
            hinges_pt,
            self.door_schematic_line_thickness,
            self.door_width,
            angle=self.orientation_angle + (180 if self.opening_outside else 0),
            facecolor=draw_color
        )
        door_wing.set_zorder(self.get_zorder())
        ax.add_patch(door_wing)

        extra = 2  # degrees for smooth arc connection
        if self.opening_outside:
            if self.to_the_right:
                start_angle = RIGHT_ANGLE_IN_DEGREES * 2
                end_angle   = RIGHT_ANGLE_IN_DEGREES * 3 + extra
            else:
                start_angle = -RIGHT_ANGLE_IN_DEGREES - extra
                end_angle   = 0
        else:
            if self.to_the_right:
                start_angle = RIGHT_ANGLE_IN_DEGREES - extra
                end_angle   = RIGHT_ANGLE_IN_DEGREES * 2
            else:
                start_angle = 0
                end_angle   = RIGHT_ANGLE_IN_DEGREES + extra

        arc = Arc(
            arc_anchor,
            2 * (self.door_width - self.door_schematic_line_thickness),
            2 * self.door_width,
            angle=self.orientation_angle,
            theta1=start_angle,
            theta2=end_angle,
            color=draw_color,
            linewidth=1
        )
        arc.set_zorder(self.get_zorder())
        ax.add_patch(arc)

        # Label
        if self.opening_outside:
            text_rot = 40 + (RIGHT_ANGLE_IN_DEGREES * 2 if self.to_the_right else RIGHT_ANGLE_IN_DEGREES * 3)
        else:
            text_rot = 40 + (RIGHT_ANGLE_IN_DEGREES if self.to_the_right else 0)
        text_rot = (360 + text_rot + self.orientation_angle) % 360

        render_label_and_id(
            ax, self, 'BalconyDoor', hinges_pt, text_rot,
            label_prefix="   ---", id_prefix="   ---"
        )
