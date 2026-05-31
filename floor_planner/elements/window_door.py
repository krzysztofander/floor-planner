"""
WindowDoor and WindowDoorDouble elements.

Both use external OBJ models for 3D export.
- WindowDoor: single full-height glass wing (no lower wood panel)
- WindowDoorDouble: two full-height glass wings side by side (1.80 m wide)

Author: Krzysztof Bartczak
"""

import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle

from ..constants import RIGHT_ANGLE_IN_DEGREES
from ..utils import rotate_point, render_label_and_id
from .balcony_door import BalconyDoor
from .info import DimensionArrow
from .options import get_element_option


class WindowDoor(BalconyDoor):
    """
    Window door with a single full-height glass wing (no lower wood panel).

    Identical to BalconyDoor in every way except the 3D model — this one shows
    glass from sill to top bar with no solid lower section.

    YAML parameters: same as BalconyDoor / Door.
    """

    _registry_key = 'window_door'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 0.9

    def _default_length(self) -> float:
        return 0.9

    def _default_height(self) -> float:
        return 2.1


class WindowDoorDouble(BalconyDoor):
    """
    Double window door: two full-height glass wings side by side (1.80 m wide).

    In 2D the floor plan shows two wing arcs opening symmetrically outward
    from the center — left wing hinged on the left, right wing hinged on the right.
    In 3D it uses an external OBJ model with a visible center divider bar.

    YAML parameters (same as BalconyDoor / Door, but doorway_width defaults
    to the full 1.80 m model width):
        anchor_point     – (x, y) frame corner on the left side
        doorway_width    – total width including both frame sides (metres, typically 1.80)
        door_width       – combined clear opening width (metres, typically 1.68)
        thickness        – door / wall thickness (metres)
        orientation_angle – degrees counter-clockwise from X-axis
        opening_outside  – both wings open outward when True
        color            – 2-D drawing colour (default 'black')
        label            – optional text label
    """
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
            doorway_width=doorway_width,
            door_width=door_width,
            thickness=thickness,
            orientation_angle=orientation_angle,
            to_the_right=to_the_right,
            color=color,
            hinges_point=hinges_point,
            opening_outside=opening_outside,
            label=label,
            **kwargs
        )
        _MODEL_DEPTH = 0.12
        if not opening_outside:
            self.secondary_normalization = {
                'rotation':    [0, 180, 0],
                #'translation': [self._default_width(), 0, _MODEL_DEPTH],
                'translation': [self._default_width(), 0, thickness*2/3],
            }
        else:
            self.secondary_normalization = {
                'rotation':    [0, 0, 0],
                #'translation': [self._default_width(), 0, _MODEL_DEPTH],
                'translation': [0, 0, thickness/3],
            }
        self.secondary_anchor_offset = None
        self.door_width = self.get_door_width()
        self.doorway_width = self.get_doorway_width()
        self.frame_width = self.doorway_width - self.door_width
        self.opening_outside = opening_outside
        self.hinges_point = hinges_point

    _registry_key = 'window_door_double'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 1.8

    def _default_length(self) -> float:
        return 1.8

    def _default_height(self) -> float:
        return 2.1

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw double door: outer frame + two symmetric wing arcs."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        angle_rad = math.radians(self.orientation_angle)
        half_door = self.door_width / 2
        sl = self.door_schematic_line_thickness  # shorthand
        extra = 2  # degrees for smooth arc connection

        # --- Frame ---
        # Left frame bar
        left_frame = Rectangle(
            self.anchor_point, self.frame_width, self.thickness,
            angle=self.orientation_angle, facecolor=draw_color
        )
        left_frame.set_zorder(self.get_zorder())
        ax.add_patch(left_frame)

        # White gap for full opening
        hole_anchor = (
            self.anchor_point[0] + math.cos(angle_rad) * self.frame_width,
            self.anchor_point[1] + math.sin(angle_rad) * self.frame_width,
        )
        gap = Rectangle(
            hole_anchor, self.door_width, self.thickness,
            angle=self.orientation_angle, facecolor='white'
        )
        gap.set_zorder(self.get_zorder())
        ax.add_patch(gap)

        # Right frame bar
        shift_r = self.frame_width + self.door_width
        right_anchor = (
            self.anchor_point[0] + math.cos(angle_rad) * shift_r,
            self.anchor_point[1] + math.sin(angle_rad) * shift_r,
        )
        right_frame = Rectangle(
            right_anchor, self.frame_width, self.thickness,
            angle=self.orientation_angle, facecolor=draw_color
        )
        right_frame.set_zorder(self.get_zorder())
        ax.add_patch(right_frame)

        # --- Optional dimension arrow ---
        if get_element_option("WindowDoorDouble", "dimensions") or get_element_option("Door", "dimensions"):
            dims_pt = rotate_point(
                self.anchor_point,
                self.frame_width,
                self.thickness * (0.8 if self.opening_outside else 0.2),
                angle_rad
            )
            DimensionArrow(
                anchor_point=dims_pt,
                length=self.door_width,
                orientation_angle=self.orientation_angle,
                annotate_above=not self.opening_outside,
                color=get_element_option("Door", "label_color", "black")
            ).draw(ax)

        # --- Left wing (hinged at left edge of opening, to_the_right=False style) ---
        if self.opening_outside:
            left_hinge_x = sl + self.frame_width   # offset for outside rect rotation
        else:
            left_hinge_x = self.frame_width

        left_hinge_pt = rotate_point(
            self.anchor_point, left_hinge_x, self.thickness * self.hinges_point, angle_rad
        )
        left_arc_anchor = rotate_point(
            self.anchor_point, self.frame_width + sl, self.thickness * self.hinges_point, angle_rad
        )

        left_wing = Rectangle(
            left_hinge_pt, sl, half_door,
            angle=self.orientation_angle + (180 if self.opening_outside else 0),
            facecolor=draw_color
        )
        left_wing.set_zorder(self.get_zorder())
        ax.add_patch(left_wing)

        if self.opening_outside:
            l_start, l_end = -RIGHT_ANGLE_IN_DEGREES - extra, 0
        else:
            l_start, l_end = 0, RIGHT_ANGLE_IN_DEGREES + extra

        left_arc = Arc(
            left_arc_anchor,
            2 * (half_door - sl), 2 * half_door,
            angle=self.orientation_angle,
            theta1=l_start, theta2=l_end,
            color=draw_color, linewidth=1
        )
        left_arc.set_zorder(self.get_zorder())
        ax.add_patch(left_arc)

        # --- Right wing (hinged at right edge of opening, to_the_right=True style) ---
        if self.opening_outside:
            right_hinge_x = self.frame_width + self.door_width - sl + sl  # +sl for outside offset
        else:
            right_hinge_x = self.frame_width + self.door_width - sl

        right_hinge_pt = rotate_point(
            self.anchor_point, right_hinge_x, self.thickness * self.hinges_point, angle_rad
        )
        right_arc_anchor = rotate_point(
            self.anchor_point,
            self.frame_width + self.door_width - sl,
            self.thickness * self.hinges_point, angle_rad
        )

        right_wing = Rectangle(
            right_hinge_pt, sl, half_door,
            angle=self.orientation_angle + (180 if self.opening_outside else 0),
            facecolor=draw_color
        )
        right_wing.set_zorder(self.get_zorder())
        ax.add_patch(right_wing)

        if self.opening_outside:
            r_start, r_end = RIGHT_ANGLE_IN_DEGREES * 2, RIGHT_ANGLE_IN_DEGREES * 3 + extra
        else:
            r_start, r_end = RIGHT_ANGLE_IN_DEGREES - extra, RIGHT_ANGLE_IN_DEGREES * 2

        right_arc = Arc(
            right_arc_anchor,
            2 * (half_door - sl), 2 * half_door,
            angle=self.orientation_angle,
            theta1=r_start, theta2=r_end,
            color=draw_color, linewidth=1
        )
        right_arc.set_zorder(self.get_zorder())
        ax.add_patch(right_arc)

        # --- Label at centre of opening ---
        center_pt = rotate_point(
            self.anchor_point,
            self.frame_width + self.door_width / 2,
            self.thickness * 0.5,
            angle_rad
        )
        text_rot = (360 + 40 + self.orientation_angle) % 360
        render_label_and_id(
            ax, self, 'WindowDoorDouble', center_pt, text_rot,
            label_prefix="   ---", id_prefix="   ---"
        )
