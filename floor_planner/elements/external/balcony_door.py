"""
Balcony Door element.

Draws in 2D identically to Door (frame + opening arc), but uses an external
OBJ model for 3D / glTF export.  The model contains a visible door frame,
a lower solid-wood wing panel, and an upper glass panel.

Author: Krzysztof Bartczak
"""
import matplotlib.axes
from matplotlib.pylab import cos

from ...constants import RIGHT_ANGLE_IN_DEGREES
from ...utils import rotate_point
from ..external_models import ExternalModelElement
from ...options import get_element_option
from ..vertical_levels import VertInfoDoor
from ..foundation.door import Door2D, Door3D
class BalconyDoor(VertInfoDoor, ExternalModelElement):
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
        door_type        – 'hinged' (default) or 'sliding'
        color            – 2-D drawing colour (default 'black')
        label            – optional text label
    """

    _registry_key = 'balcony_door'
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
            door_type: str = 'hinged',
            label: str | None = None,
            **kwargs
    ):
        # ExternalModelElement.__init__ rejects 'width', 'length', 'height' in kwargs
        # but accepts all other keyword args (v_anchor, id, etc.)
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs
        )

        self.door2d = Door2D(anchor_point, doorway_width, door_width, thickness, door_type,
                orientation_angle, to_the_right, hinges_point,
                opening_outside, door_orientation_in_doorway)

        self.door3d = Door3D(
            doorway_width=doorway_width,
            door_width=door_width,
            thickness=thickness,
            door_type=door_type,
            opening_outside=opening_outside,
            to_the_right=to_the_right,
            hinges_depth=self.door2d.getHingesDepth()
        )

        # length and thickness  used by the parent Element / anchor helpers
        self.length = doorway_width
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
        """Return whether the door opens to the right."""
        return self.door2d.get_to_the_right()
   
    def get_doorway_width(self) -> float:
        """Return the doorway width."""
        return self.door2d.get_doorway_width()
   
    def get_door_width(self) -> float:
        """Return the door width."""
        return self.door2d.get_door_width()


    # ------------------------------------------------------------------
    # 2-D drawing – identical to Door.draw()
    # ------------------------------------------------------------------

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the balcony door exactly like a regular Door in 2D."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return
        z_order = self.get_zorder()
        self.door2d.draw2D(draw_color, z_order, ax)
        self.door2d.render_door_label_and_id(self, self.__class__.__name__, ax)
