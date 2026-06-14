"""
Room surface elements: Floor and Ceiling planes.

These are 3D-only surface elements that span the interior of a room.
They are invisible in 2D and are created automatically by the room with
the correct anchor_point and size derived from the room's internal corners.

Author: Krzysztof Bartczak
"""

import matplotlib.axes

from ..element import SurfaceElement
from ..vertical_levels import VertInfoFloors, VertInfoCeilingSurface


class Floor(VertInfoFloors, SurfaceElement):
    """
    Room floor plane (3D only).

    Spans the interior of a room at floor level.  Invisible in 2D.
    anchor_point and size are provided by the room during creation and
    must not be set in YAML — use 'floor:' with no size/anchor parameters.

    Optional YAML parameters:
        v_anchor  – override vertical anchor (default: VertInfoFloors = 0.0 m)
        height    – override slab thickness  (default: 0.02 m)
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            v_anchor: float | None = None,
            height: float | None = None,
            **kwargs
    ):
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=0,
            size=size,
            color='brown',
            v_anchor=v_anchor,
            height=height if height is not None else self._default_height(),
            **kwargs
        )

    def _default_height(self) -> float:
        return 0.02

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Floor is invisible in 2D — nothing to draw."""
        pass


class Ceiling(VertInfoCeilingSurface, SurfaceElement):
    """
    Room ceiling plane (3D only).

    Spans the interior of a room at ceiling level.  Invisible in 2D.
    anchor_point and size are provided by the room during creation and
    must not be set in YAML — use 'ceiling:' with no size/anchor parameters.

    Optional YAML parameters:
        v_anchor  – override vertical anchor (default: VertInfoCeilingSurface = 2.69 m)
        height    – override slab thickness  (default: 0.01 m)
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            v_anchor: float | None = None,
            height: float | None = None,
            **kwargs
    ):
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=0,
            size=size,
            color='white',
            v_anchor=v_anchor,
            height=height if height is not None else self._default_height(),
            **kwargs
        )

    def _default_height(self) -> float:
        return 0.01

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Ceiling is invisible in 2D — nothing to draw."""
        pass
