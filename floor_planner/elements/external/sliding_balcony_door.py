"""
SlidingBalconyDoor element.

Like BalconyDoor but animates with a slide (translation) instead of
a hinge rotation.  Uses the same external OBJ model as the balcony_door
(one model ↔ one element rule: the model is copied to the
``sliding_balcony_door`` directory so each registry key maps to exactly
one model directory).

Author: Krzysztof Bartczak
"""

import math

import matplotlib.axes

from ...utils import rotate_point
from ..external_models import ExternalModelElement
from ..vertical_levels import VertInfoDoor
from ..foundation.door import Door2D,  Door3D
from floor_planner.motion_3d import AnimationMetadata


class SlidingBalconyDoor(VertInfoDoor, ExternalModelElement):
    """
    Sliding balcony door element.

    In 2D the floor plan shows:
      - Frame bars on the sides of the opening.
      - A filled rectangle representing the closed door panel (parallel to wall).
      - A dashed rectangle showing the panel in the fully-open position.
      - A short arrow indicating the slide direction.

    In 3D / glTF the element uses the same external OBJ model as
    ``model_balcony_door``, but the proximity-triggered animation drives a
    **translation** (slide) instead of a rotation.

    YAML type: ``model_sliding_balcony_door``

    YAML parameters (same as model_balcony_door):
        anchor_point      – (x, y) frame corner on the slide side
        doorway_width     – total frame width in metres
        door_width        – clear panel width in metres
        thickness         – wall / frame depth in metres
        orientation_angle – degrees counter-clockwise from X-axis (default 0)
        to_the_right      – panel slides to the RIGHT when True (default False)
        hinges_point      – panel depth fraction in wall (0 = front, 1 = back)
        opening_outside   – affects which face the panel sits on (default False)
        color             – 2-D drawing colour (default 'black')
        label             – optional text label
    """

    _registry_key = 'sliding_balcony_door'
    _requires_external_model = True

    def __init__(
            self,
            anchor_point: tuple[float, float],
            doorway_width: float,
            door_width: float,
            thickness: float,
            door_orientation_in_doorway: float = 0.5,
            orientation_angle: float = 0,
            to_the_right: bool = False,
            color: str = 'black',
            hinges_point: float = 0.95,
            opening_outside: bool = False,
            label: str | None = None,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs,
        )

        self.door2d = Door2D(
            anchor_point, doorway_width, door_width, thickness, 'sliding',
            orientation_angle, to_the_right, hinges_point,
            opening_outside, door_orientation_in_doorway,
        )

        self.door3d = Door3D(
            doorway_width=doorway_width,
            door_width=door_width,
            thickness=thickness,
            door_type='sliding',
            opening_outside=opening_outside,
            to_the_right=to_the_right,
            hinges_depth=(1 - hinges_point) if opening_outside else hinges_point,
            # External model constants (same as balcony_door model)
            model_door_width=0.9,
            wing_width_on_model=0.12,
            model_depth=0.12,
        )

        self.length    = doorway_width
        self.thickness = thickness
        self.animation = self.door3d.getAnimation()
    # ------------------------------------------------------------------
    # ExternalModelElement hooks
    # ------------------------------------------------------------------

    def _default_width(self) -> float:
        return 0.9

    def _default_length(self) -> float:
        return 0.9

    def get_to_the_right(self) -> bool:
        return self.door2d.to_the_right

    def get_doorway_width(self) -> float:
        return self.door2d.doorway_width

    def get_door_width(self) -> float:
        return self.door2d.door_width

    # ------------------------------------------------------------------
    # 2-D drawing
    # ------------------------------------------------------------------

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the sliding door in 2D floor plan."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return
        z_order = self.get_zorder()
        self.door2d.draw2D(draw_color, z_order, ax)
        self.door2d.render_door_label_and_id(self, self.__class__.__name__, ax)
