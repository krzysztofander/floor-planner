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

from floor_planner.elements.element import ElementBase

from ...constants import RIGHT_ANGLE_IN_DEGREES
from ...utils import rotate_point, render_label_and_id
from .balcony_door import BalconyDoor
from ..symbols.info import DimensionArrow
from ...options import generate_element_id, get_element_option
from ..foundation.door import Door2D


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

class SolidDoor1(BalconyDoor):
    """
    Solid door with a single full-height panel.

    Identical to BalconyDoor in every way except the 3D model — this one shows
    a solid panel from sill to top bar with no glass section.

    YAML parameters: same as BalconyDoor / Door.
    """

    _registry_key = 'solid_door_1'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 0.9

    def _default_length(self) -> float:
        return 0.9

class SolidDoor2(SolidDoor1):
    _registry_key = 'solid_door_2'

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
        # but accepts all other keyword args (v_anchor, id, etc.)
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

        
        rotated_anchor_l = rotate_point( anchor_point, 0,0, math.radians(orientation_angle))
        rotated_anchor_r = rotate_point(rotated_anchor_l, doorway_width/2, 0, math.radians(orientation_angle))

        self.door2d_l = Door2D(
                                anchor_point = rotated_anchor_l,
                                doorway_width = doorway_width /2,
                                door_width = door_width /2,
                                thickness = thickness,
                                orientation_angle = orientation_angle,
                                to_the_right = False,
                                hinges_point = hinges_point,
                                opening_outside = opening_outside)
    
        self.door2d_r = Door2D(
                                anchor_point = rotated_anchor_r,
                                doorway_width = doorway_width /2,
                                door_width = door_width /2,
                                thickness = thickness,
                                orientation_angle = orientation_angle,
                                to_the_right = True,
                                hinges_point = hinges_point,
                                opening_outside = opening_outside)
    
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

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw double door: outer frame + two symmetric wing arcs."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return
        z_order = self.get_zorder()
        self.door2d_l.draw2D(draw_color, z_order, ax)
        self.door2d_r.draw2D(draw_color, z_order, ax)
        self.door2d_l.render_door_label_and_id(self, self.__class__.__name__, ax)
