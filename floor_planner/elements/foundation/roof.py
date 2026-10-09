"""
Roof elements: gable, hipped, single-slope, octant pieces, and internal-corner
octant pieces (valley octants).

These are separate from landscaping/structures.py so that the garden-structure
module stays focused on ground-level objects while the more specialised roof
geometry lives here, alongside the other architectural foundation elements.

Author: Krzysztof Bartczak
"""

import math

import matplotlib.axes
from matplotlib.patches import Rectangle, Polygon

from ...utils import rotate_point, render_label_and_id
from ..element import Element
from ..vertical_levels import VertInfoRoof
from ...geometry_3d import (GableRoofGeometry3D, HippedRoofGeometry3D,
                             SingleSlopeRoofGeometry3D, HippedRoofOctantGeometry3D,
                             HippedInternalOctantGeometry3D, GableEndWallGeometry3D)


# ──────────────────────────────────────────────────────────────────────────────
# Shared base
# ──────────────────────────────────────────────────────────────────────────────

class _RoofBase(Element):
    """
    Shared base for roof elements.

    In 2D draws a thin, unfilled dashed rectangle showing the roof footprint.
    In 3D generates a proper roof shape via the geometry mixin.

    YAML parameters (common to GableRoof and HippedRoof):
        anchor_point      – bottom-left corner of the roof footprint
        size              – (x_size, z_size) tuple in metres:
                            x_size = horizontal (left/right in plan view),
                            z_size = vertical   (up/down in plan view)
        height            – ridge height above v_anchor  (default from VertInfoRoof)
        v_anchor          – 3D Y of roof base, i.e. top of supporting walls
                            (default 2.70 m from VertInfoRoof)
        orientation_angle – rotation in degrees  (default 0)
        color             – outline colour in 2D  (default '#8B4513')
        label             – optional label string
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float | None = None,
            color: str = '#8B4513',
            label: str | None = None,
            draw_edge_a: bool = True,
            draw_edge_b: bool = True,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            color=color,
            label=label,
            v_anchor=v_anchor,
            height=height if height is not None else self._default_height(),
            texture_scale=3,
            **kwargs,
        )
        self.x_axis_size = size[0]
        self.z_axis_size = size[1]
        self.orientation_angle = orientation_angle
        self.draw_edge_a = draw_edge_a
        self.draw_edge_b = draw_edge_b

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """
        Draw roof footprint as dashed lines.

        The two edges parallel to the ridge are always drawn; the edges
        perpendicular to the ridge are drawn conditionally: ``draw_edge_a`` for
        the one at local 0, ``draw_edge_b`` for the one at the far end.
        """
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        x = self.x_axis_size
        z = self.z_axis_size
        angle_rad = math.radians(self.orientation_angle if self.orientation_angle else 0)

        def w(lx, lz):
            return rotate_point(self.anchor_point, lx, lz, angle_rad)

        # Same ridge-direction rule as GableRoof.draw
        if (self.orientation_angle is not None) or x >= z:
            # Ridge along X: parallel edges at lz=0 / lz=z, perpendicular at lx=0 / lx=x
            edges = [
                ((0, 0), (x, 0), True),
                ((0, z), (x, z), True),
                ((0, 0), (0, z), self.draw_edge_a),
                ((x, 0), (x, z), self.draw_edge_b),
            ]
        else:
            # Ridge along Z: parallel edges at lx=0 / lx=x, perpendicular at lz=0 / lz=z
            edges = [
                ((0, 0), (0, z), True),
                ((x, 0), (x, z), True),
                ((0, 0), (x, 0), self.draw_edge_a),
                ((0, z), (x, z), self.draw_edge_b),
            ]

        for start, end, enabled in edges:
            if not enabled:
                continue
            p0 = w(*start)
            p1 = w(*end)
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                    color=draw_color, linewidth=1.5, linestyle='--',
                    zorder=self.get_zorder())

        if self.label:
            center = rotate_point(
                self.anchor_point,
                self.x_axis_size / 2,
                self.z_axis_size / 2,
                math.radians(self.orientation_angle if self.orientation_angle  else 0),
            )
            render_label_and_id(
                ax=ax,
                element=self,
                element_type=self.__class__.__name__,
                position=center,
                rotation=self.orientation_angle if self.orientation_angle  else 0
            )


# ──────────────────────────────────────────────────────────────────────────────
# Rectangular roof types
# ──────────────────────────────────────────────────────────────────────────────

class GableRoof(VertInfoRoof, GableRoofGeometry3D, _RoofBase):
    """
    Gable roof element.

    Two sloping planes meeting at a ridge; triangular gable walls at each end.
    The ridge runs along the *longer* plan dimension (or along X when square).

    In 2D: unfilled dashed rectangle showing the footprint.
    In 3D: proper gable roof geometry with no bottom face.

    YAML type: ``gable_roof``

    Extra YAML parameters beyond _RoofBase:
        extension_a  – extend the "a" slope plane outward in plan (metres, default 0)
        extension_b  – extend the "b" slope plane outward in plan (metres, default 0)

        When the ridge runs along X (x_axis_size >= z_axis_size):
          extension_a extends the front slope (plan-z = 0 side)
          extension_b extends the back  slope (plan-z = z side)
        When the ridge runs along Z:
          extension_a extends the left  slope (plan-x = 0 side)
          extension_b extends the right slope (plan-x = x side)

        The extension value is the 2D horizontal distance; the slope plane simply
        grows outward — its ridge line stays in place.
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float | None = None,
            color: str = '#8B4513',
            label: str | None = None,
            extension_a: float = 0,
            extension_b: float = 0,
            roof_thickness: float = 0.4,
            draw_edge_a: bool = True,
            draw_edge_b: bool = True,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            size=size,
            height=height,
            v_anchor=v_anchor,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            draw_edge_a=draw_edge_a,
            draw_edge_b=draw_edge_b,
            **kwargs,
        )
        self.extension_a = extension_a or 0
        self.extension_b = extension_b or 0
        self.roof_thickness = roof_thickness or 0.4

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw roof footprint + extension indicators."""
        super().draw(ax)

        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        x = self.x_axis_size
        z = self.z_axis_size
        angle_rad = math.radians(self.orientation_angle if self.orientation_angle  else 0)

        def w(lx, lz):
            return rotate_point(self.anchor_point, lx, lz, angle_rad)

        if (self.orientation_angle is not None) or x >= z:
            # Ridge along X; extensions in the z direction
            # If orientation_angle is specified always assume to draw as if the ridge was along X, no automation
            if self.extension_a > 0:
                p0 = w(0, -self.extension_a)
                p1 = w(x, -self.extension_a)
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())
            if self.extension_b > 0:
                p0 = w(0, z + self.extension_b)
                p1 = w(x, z + self.extension_b)
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())
        else:
            # Ridge along Z; extensions in the x direction
            if self.extension_a > 0:
                p0 = w(-self.extension_a, 0)
                p1 = w(-self.extension_a, z)
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())
            if self.extension_b > 0:
                p0 = w(x + self.extension_b, 0)
                p1 = w(x + self.extension_b, z)
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())


class HippedRoof(VertInfoRoof, HippedRoofGeometry3D, _RoofBase):
    """
    Hipped roof element.

    All four sides slope toward the centre.
    Square plan → pyramid.  Rectangular plan → elongated hipped roof with
    a short ridge and triangular hip faces at the short ends.

    In 2D: unfilled dashed rectangle showing the footprint.
    In 3D: proper hipped/pyramid geometry with no bottom face.

    YAML type: ``hipped_roof``

    Parameters: see _RoofBase.
    Extra parameter: roof_thickness (default 0.4)
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None,
            roof_thickness: float = 0.4,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            size=size,
            height=height,
            v_anchor=v_anchor,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs,
        )
        self.roof_thickness = roof_thickness or 0.4


class SingleSlopeRoof(VertInfoRoof, SingleSlopeRoofGeometry3D, _RoofBase):
    """
    Single-slope (mono-pitch / lean-to) roof element.

    One rectangular sloping plane:
      - the low eave runs along plan-z = 0 at v_anchor
      - the high eave runs along plan-z = z_axis_size at v_anchor + height

    In 2D: unfilled dashed rectangle showing the footprint plus a dotted line
           on the low eave if ``extension`` > 0.
    In 3D: single sloping quad, no gable end caps.

    YAML type: ``single_slope_roof``

    Extra YAML parameters beyond _RoofBase:
        extension   – extend the low-eave edge outward in the plan-z direction
                      (horizontal distance in metres, default 0)
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None,
            extension: float = 0,
            roof_thickness: float = 0.4,
            draw_edge_a: bool = True,
            draw_edge_b: bool = True,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            size=size,
            height=height,
            v_anchor=v_anchor,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            draw_edge_a=draw_edge_a,
            draw_edge_b=draw_edge_b,
            **kwargs,
        )
        self.extension = extension or 0
        self.roof_thickness = roof_thickness or 0.4

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw footprint dashed rectangle + optional extension dotted line."""
        super().draw(ax)

        if self.extension <= 0:
            return
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point(self.anchor_point, lx, lz, angle_rad)

        p0 = w(0,               -self.extension)
        p1 = w(self.x_axis_size, -self.extension)
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())


# ──────────────────────────────────────────────────────────────────────────────
# External corner octant elements (apex / pyramid pieces)
# ──────────────────────────────────────────────────────────────────────────────

class _HippedRoofOctantBase(VertInfoRoof, HippedRoofOctantGeometry3D, _RoofBase):
    """
    Base for 1/8th pyramid octant pieces.

    A true octant covers a 45° sector of a square pyramid, formed by cutting
    along all 4 axes of symmetry.  Its eave edge runs from an edge-midpoint
    to the adjacent base corner — a right-angle triangle in plan.

    ``anchor_point`` is the **apex** (ridge tip) — rotation pivot in both plan
    and 3D.  ``size = (x_axis_size, z_axis_size)``:
      - x_axis_size: lateral offset from midpoint to corner (= half the pyramid
                     base width for a square pyramid)
      - z_axis_size: depth from apex to eave (= half the pyramid base depth)

    For a square pyramid of base 2d×2d use size=[d, d].
    Combine 4 right + 4 left at 0°/90°/180°/270° to form a complete pyramid.

    YAML types: ``hipped_roof_octant_left``, ``hipped_roof_octant_right``

    Extra YAML parameter:
        extension  – extend the eave outward from the apex, preserving slope
                     angle (horizontal metres, default 0)
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None,
            extension: float = 0,
            roof_thickness: float = 0.4,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            size=size,
            height=height,
            v_anchor=v_anchor,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs,
        )
        self.extension = extension or 0
        self.roof_thickness = roof_thickness or 0.4

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the right-triangle footprint with its apex at anchor_point."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        x = self.x_axis_size
        z = self.z_axis_size
        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point(self.anchor_point, lx, lz, angle_rad)

        tip    = self.anchor_point
        mid    = w(0,                                   z)   # edge midpoint
        corner = w(-x if self._octant_left else x,      z)   # base corner

        triangle = Polygon(
            [tip, mid, corner],
            closed=True,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.5,
            linestyle='--',
        )
        triangle.set_zorder(self.get_zorder())
        ax.add_patch(triangle)

        if self.extension > 0:
            z_ext = z + self.extension
            x_ext = x + self.extension
            p0 = w(0,                                        z_ext)
            p1 = w(-x_ext if self._octant_left else x_ext,  z_ext)
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                    color=draw_color, linewidth=0.8, linestyle=':',
                    zorder=self.get_zorder())

        if self.label:
            cx = (tip[0] + mid[0] + corner[0]) / 3
            cz = (tip[1] + mid[1] + corner[1]) / 3
            render_label_and_id(
                ax=ax,
                element=self,
                element_type=self.__class__.__name__,
                position=(cx, cz),
                rotation=self.orientation_angle,
            )


class HippedRoofOctantLeft(_HippedRoofOctantBase):
    """
    Left octant (1/8th pyramid): the base corner lies to the LEFT of the
    pointing direction when orientation_angle=0.

    Combine with HippedRoofOctantRight at the same anchor_point and
    orientations to assemble a pyramid or complex hipped roof.

    YAML type: ``hipped_roof_octant_left``
    """
    _octant_left = True


class HippedRoofOctantRight(_HippedRoofOctantBase):
    """
    Right octant (1/8th pyramid): the base corner lies to the RIGHT of the
    pointing direction when orientation_angle=0.

    YAML type: ``hipped_roof_octant_right``
    """
    _octant_left = False


# ──────────────────────────────────────────────────────────────────────────────
# Internal corner octant elements (valley / drain-to-centre)
# ──────────────────────────────────────────────────────────────────────────────

class _HippedInternalOctantBase(VertInfoRoof, HippedInternalOctantGeometry3D, _RoofBase):
    """
    Base for 1/8th inverted-pyramid octant pieces.

    Models the **inside** corner of a complex roof — a valley where two roof
    planes meet and water drains inward.  It is the dual of
    ``_HippedRoofOctantBase``:

    * External octant: anchor_point is the **apex** (HIGH ridge tip); the
      triangular slope descends from there to the LOW eave.
    * Internal octant: anchor_point is the **valley** (LOW drain point); the
      triangular slope ascends from there to the HIGH eave/ridge edges.

    ``anchor_point`` is the **valley bottom** — the lowest point and the
    rotation pivot in both plan and 3D.

    The plan-view triangle is identical to the external octant:
      - anchor/valley at (0, 0)      ← LOW  (v_anchor)
      - mid            at (0, z)     ← HIGH (v_anchor + height)
      - corner (right) at (+x, z)    ← HIGH
      - corner (left)  at (-x, z)    ← HIGH

    Combine 4 right + 4 left at 0°/90°/180°/270° (all at the same centre
    valley point) to form a complete inverted pyramid (drain-to-centre patio
    roof).

    YAML types: ``hipped_internal_octant_left``, ``hipped_internal_octant_right``

    YAML parameters:
        anchor_point      – valley bottom (LOW), rotation pivot
        size              – (x_axis_size, z_axis_size) in metres
        height            – vertical rise from valley to eave (default from VertInfoRoof)
        v_anchor          – 3D Y of valley base (default 2.70 m from VertInfoRoof)
        orientation_angle – rotation in degrees  (default 0)
        color             – outline colour in 2D  (default '#8B4513')
        label             – optional label string
        extension         – extend the HIGH eave edge outward (horizontal metres, default 0)
        roof_thickness    – inner surface offset for 3D export (default 0.4)
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None,
            extension: float = 0,
            roof_thickness: float = 0.4,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            size=size,
            height=height,
            v_anchor=v_anchor,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs,
        )
        self.extension = extension or 0
        self.roof_thickness = roof_thickness or 0.4

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the right-triangle footprint with its valley at anchor_point."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        x = self.x_axis_size
        z = self.z_axis_size
        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point(self.anchor_point, lx, lz, angle_rad)

        tip    = self.anchor_point
        mid    = w(0,                                   z)   # eave midpoint
        corner = w(-x if self._octant_left else x,      z)   # eave corner

        triangle = Polygon(
            [tip, mid, corner],
            closed=True,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.5,
            linestyle='-.',
        )
        triangle.set_zorder(self.get_zorder())
        ax.add_patch(triangle)

        if self.extension > 0:
            z_ext = z + self.extension
            x_ext = x + self.extension
            p0 = w(0,                                        z_ext)
            p1 = w(-x_ext if self._octant_left else x_ext,  z_ext)
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                    color=draw_color, linewidth=0.8, linestyle=':',
                    zorder=self.get_zorder())

        if self.label:
            cx = (tip[0] + mid[0] + corner[0]) / 3
            cz = (tip[1] + mid[1] + corner[1]) / 3
            render_label_and_id(
                ax=ax,
                element=self,
                element_type=self.__class__.__name__,
                position=(cx, cz),
                rotation=self.orientation_angle,
            )


class HippedInternalOctantLeft(_HippedInternalOctantBase):
    """
    Left internal octant (1/8th inverted pyramid): the eave corner lies to the
    LEFT of the pointing direction when orientation_angle=0.

    YAML type: ``hipped_internal_octant_left``
    """
    _octant_left = True


class HippedInternalOctantRight(_HippedInternalOctantBase):
    """
    Right internal octant (1/8th inverted pyramid): the eave corner lies to the
    RIGHT of the pointing direction when orientation_angle=0.

    YAML type: ``hipped_internal_octant_right``
    """
    _octant_left = False


# ──────────────────────────────────────────────────────────────────────────────
# Gable end wall / glass elements  (3-D only, no 2-D drawing)
# ──────────────────────────────────────────────────────────────────────────────

class _GableEndBase(VertInfoRoof, GableEndWallGeometry3D, Element):
    """
    Shared base for gable-end triangular panels (wall or glass).

    These fill the vertical triangular gap between the top of the supporting
    walls (v_anchor) and the gable ridge (v_anchor + height) at one end of a
    gable roof.  They have **no 2-D floor-plan representation**; only 3-D
    geometry is generated.

    Use the **same** anchor_point / size / height / v_anchor /
    orientation_angle values as the matching GableRoof element so the
    triangles slot in exactly.

    YAML parameters:
        anchor_point      – bottom-left of the roof footprint (= GableRoof)
        size              – (x_size, z_size) in metres          (= GableRoof)
        height            – ridge height above v_anchor          (= GableRoof)
        v_anchor          – 3D Y of the wall plate  (default 2.70 m, VertInfoRoof)
        orientation_angle – rotation in degrees (default 0)
        color             – unused in 2D; kept for API consistency
        label             – optional label string
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            color: str = '#D3D3D3',
            label: str | None = None,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            color=color,
            label=label,
            v_anchor=v_anchor,
            height=height if height is not None else self._default_height(),
            **kwargs,
        )
        self.x_axis_size       = size[0]
        self.z_axis_size       = size[1]
        self.orientation_angle = orientation_angle

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """No 2-D drawing — gable end panels are 3-D only."""
        pass


class GableEndWallLeft(_GableEndBase):
    """
    Left gable end wall: opaque triangular vertical panel at the left end of
    a gable roof (x = 0 when ridge runs along X, z = 0 when along Z).

    Use the same parameters as the matching GableRoof to ensure a perfect fit.

    YAML type: ``gable_end_wall_left``
    """
    _gable_end_right = False


class GableEndWallRight(_GableEndBase):
    """
    Right gable end wall: opaque triangular panel at the right end.

    YAML type: ``gable_end_wall_right``
    """
    _gable_end_right = True


class GableEndGlassLeft(_GableEndBase):
    """
    Left gable end glass panel: transparent triangular panel at the left end
    of a gable roof — for glazed gable ends or winter gardens.

    YAML type: ``gable_end_glass_left``
    """
    _gable_end_right = False


class GableEndGlassRight(_GableEndBase):
    """
    Right gable end glass panel: transparent triangular panel at the right end.

    YAML type: ``gable_end_glass_right``
    """
    _gable_end_right = True
