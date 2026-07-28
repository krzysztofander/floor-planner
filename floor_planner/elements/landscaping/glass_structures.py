"""
Glass structural elements: GlassDoor, GlassPanel, GlassSlope,
SolidGlassDoor, AluFrame.

These model winter-garden / conservatory construction:
- GlassDoor:      animated full-height glass door with aluminium frame
                  (same door-swing mechanics as WindowDoor/BalconyDoor)
- GlassPanel:     static glass wall panel with aluminium frame,
                  positioned like a Wall (anchor_point, length, thickness, height)
- GlassSlope:     tilted glass roof slope with aluminium frame,
                  configured like SingleSlopeRoof (anchor_point, size, height, …)
- SolidGlassDoor: procedural frameless glass door (thin glass panel only),
                  acts like Door in 2D, default thickness 0.01 m
- AluFrame:       aluminium frame without glass — same interface as GlassPanel

Author: Krzysztof Bartczak
"""

from __future__ import annotations

import math

import matplotlib.axes
from matplotlib.patches import Arc, Rectangle, Polygon

from ...utils import rotate_point, render_label_and_id
from ..external_models import ExternalModelElement
from ..vertical_levels import VertInfoLvl01, VertInfoRoof
from ..external.window_door import WindowDoor
from ..foundation.door import Door


# ──────────────────────────────────────────────────────────────────────────────
# GlassDoor
# ──────────────────────────────────────────────────────────────────────────────

class GlassDoor(WindowDoor):
    """
    Full-height glass door with aluminium frame and animated door swing.

    Identical to WindowDoor in every way (same 2D drawing, same animation,
    same YAML parameters) except the 3D model uses an aluminium frame instead
    of a wooden one.

    YAML type: ``glass_door``

    YAML parameters: same as WindowDoor / BalconyDoor / Door.
    """

    _registry_key = 'glass_door'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 0.9

    def _default_length(self) -> float:
        return 0.9


# ──────────────────────────────────────────────────────────────────────────────
# GlassPanel
# ──────────────────────────────────────────────────────────────────────────────

_GLASS_PANEL_BASE_W = 1.00   # OBJ model width  (m)
_GLASS_PANEL_BASE_H = 2.10   # OBJ model height (m)
_GLASS_PANEL_BASE_D = 0.08   # OBJ model depth  (m)


class GlassPanel(VertInfoLvl01, ExternalModelElement):
    """
    Static glass wall panel with aluminium frame.

    Placed and sized like a Wall: ``anchor_point`` is the bottom-left corner of
    the frame, ``length`` runs along X before rotation, ``thickness`` runs
    along Z (wall-depth direction), and ``height`` is the Y extent.

    In 2D: drawn as a semi-transparent blue rectangle with a fine frame outline
           to distinguish it from solid walls.
    In 3D: scaled version of the ``glass_panel`` OBJ model (aluminium bars +
           glass pane).  The base model (1 m × 2.1 m × 0.08 m) is scaled to
           the actual dimensions via ``secondary_normalization``.

    YAML type: ``glass_panel``

    YAML parameters:
        anchor_point      – (x, y) bottom-left corner of the panel frame
        length            – panel width in metres
        thickness         – frame depth (wall thickness) in metres
        height            – panel height in metres (default 2.5 m)
        orientation_angle – rotation in degrees (default 0)
        label             – optional label string
        v_anchor          – 3D Y of panel base (default: ground level, VertInfoLvl01)
    """

    _registry_key = 'glass_panel'
    _requires_external_model = True

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            thickness: float,
            height: float | None = None,
            orientation_angle: float = 0,
            color: str = '#C8E8F4',
            label: str | None = None,
            v_anchor: float | None = None,
            **kwargs,
    ):
        # ExternalModelElement rejects 'height', 'length', 'width' in **kwargs,
        # so we accept them as explicit named params and pass only what's needed.
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            v_anchor=v_anchor,
        )
        self.length = length
        self.thickness = thickness
        self.height = height if height is not None else self._default_height()

        # Scale base model to actual dimensions
        self.secondary_normalization = {
            'scale': [
                self.length    / _GLASS_PANEL_BASE_W,
                self.height    / _GLASS_PANEL_BASE_H,
                self.thickness / _GLASS_PANEL_BASE_D,
            ]
        }

    def _default_height(self) -> float:
        return 2.5

    # ------------------------------------------------------------------
    # 2-D drawing
    # ------------------------------------------------------------------

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw glass panel as semi-transparent blue rectangle with frame lines."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        angle_rad = math.radians(self.orientation_angle)

        # Semi-transparent glass fill
        fill = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor=draw_color,
            edgecolor='#3A6080',
            linewidth=1.5,
            alpha=0.35,
        )
        fill.set_zorder(self.get_zorder())
        ax.add_patch(fill)

        # Inner frame lines (show aluminium border inset 5 cm)
        inset = min(0.05, self.thickness * 0.3)
        inner = Rectangle(
            rotate_point(self.anchor_point, inset, inset, angle_rad),
            self.length - 2 * inset,
            self.thickness - 2 * inset,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor='#607090',
            linewidth=0.6,
            alpha=0.7,
        )
        inner.set_zorder(self.get_zorder())
        ax.add_patch(inner)

        render_label_and_id(
            ax=ax,
            element=self,
            element_type='GlassPanel',
            position=rotate_point(
                self.anchor_point,
                self.length / 2,
                self.thickness / 2,
                angle_rad,
            ),
            rotation=self.orientation_angle,
        )


# ──────────────────────────────────────────────────────────────────────────────
# GlassSlope
# ──────────────────────────────────────────────────────────────────────────────

class GlassSlope(VertInfoRoof, ExternalModelElement):
    """
    Tilted glass slope panel with aluminium frame.

    Configured like ``SingleSlopeRoof`` (same YAML parameters).  The low eave
    runs along plan-z = 0 at ``v_anchor``; the high eave runs along
    plan-z = ``z_size`` at ``v_anchor + height``.

    In 2D: dashed rectangle footprint identical to SingleSlopeRoof, plus an
           optional dotted line showing the extension overhang.
    In 3D: the flat ``glass_slope`` OBJ model (1 m × 1 m, lying in X-Z plane)
           is scaled and tilted via ``secondary_normalization``:
             - scale X → ``x_size``, scale Z → slope hypotenuse
             - rotate about X by ``-slope_angle`` (tilts near edge down)
           If ``extension > 0`` a translation offsets the model so z = 0 of
           the footprint stays at the scene origin rather than z = -extension.

    YAML type: ``glass_slope``

    YAML parameters:
        anchor_point      – bottom-left corner of the slope footprint
        size              – (x_size, z_size) tuple in metres
        height            – vertical rise from low eave to high eave (default 1.5 m)
        v_anchor          – 3D Y of the low eave (default 2.70 m, VertInfoRoof)
        orientation_angle – rotation in degrees (default 0)
        extension         – extend the low-eave edge outward in metres (default 0)
        color             – 2-D outline colour (default '#C8E8F4')
        label             – optional label string
    """

    _registry_key = 'glass_slope'
    _requires_external_model = True

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            extension: float = 0,
            color: str = '#C8E8F4',
            label: str | None = None,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            v_anchor=v_anchor,
        )
        x, z = size[0], size[1]
        self.x_axis_size = x
        self.z_axis_size = z
        self.height = height if height is not None else self._default_height()
        self.extension = extension or 0

        # ── Compute slope transform ──────────────────────────────────────────
        h   = self.height
        ext = self.extension
        z_total = z + ext                         # total horizontal depth including overhang

        # Guard against degenerate dimensions
        sl = math.sqrt(z_total ** 2 + h ** 2) if (z_total or h) else 0.001
        angle_deg = math.degrees(math.atan2(h, z_total)) if z_total else 90.0

        if ext > 0:
            # Translate so that plan-z = 0 (footprint near edge) aligns with
            # the model origin after scale + rotation.
            # After scale(x, 1, sl) + rotX(-angle): model point (0, 0, ext)
            #   maps to (0,  ext*h/sl,  ext*z_total/sl) in world space.
            # Negate that to bring it to origin.
            tx = 0.0
            ty = -(ext * h / sl)
            tz = -(ext * z_total / sl)
            self.secondary_normalization = {
                'scale':       [x, 1.0, sl],
                'rotation':    [-angle_deg, 0.0, 0.0],
                'translation': [tx, ty, tz],
            }
        else:
            self.secondary_normalization = {
                'scale':    [x, 1.0, sl],
                'rotation': [-angle_deg, 0.0, 0.0],
            }

    def _default_height(self) -> float:
        return 1.5

    # ------------------------------------------------------------------
    # 2-D drawing (identical style to SingleSlopeRoof)
    # ------------------------------------------------------------------

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw slope footprint as dashed rectangle + optional extension line."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Dashed footprint outline
        outline = Rectangle(
            self.anchor_point,
            width=self.x_axis_size,
            height=self.z_axis_size,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.5,
            linestyle='--',
        )
        outline.set_zorder(self.get_zorder())
        ax.add_patch(outline)

        if self.label:
            angle_rad = math.radians(self.orientation_angle)
            center = rotate_point(
                self.anchor_point,
                self.x_axis_size / 2,
                self.z_axis_size / 2,
                angle_rad,
            )
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='GlassSlope',
                position=center,
                rotation=self.orientation_angle,
            )

        if self.extension <= 0:
            return

        # Dotted line showing the extended low-eave edge
        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point(self.anchor_point, lx, lz, angle_rad)

        p0 = w(0,               -self.extension)
        p1 = w(self.x_axis_size, -self.extension)
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                color=draw_color, linewidth=0.8, linestyle=':',
                zorder=self.get_zorder())


# ──────────────────────────────────────────────────────────────────────────────
# SolidGlassDoor
# ──────────────────────────────────────────────────────────────────────────────

class SolidGlassDoor(Door):
    """
    Frameless glass door: a thin, plain glass panel that swings like a door.

    Identical to Door in 2D (same door-arc drawing) but:
      - Default ``thickness`` is 0.01 m (the glass panel depth).
      - Default colour is a semi-transparent blue.
      - In 3D the element exports as a thin glass box via the
        procedural RectangularGeometry3D mixin (no external model);
        the ``solid_glass_door`` registry key points to the glass
        fallback texture so 3D viewers render it as transparent glass.

    YAML type: ``solid_glass_door``

    YAML parameters: same as Door, but ``thickness`` defaults to 0.01 m.
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            doorway_width: float,
            door_width: float,
            thickness: float = 0.01,
            orientation_angle: float = 0,
            to_the_right: bool = False,
            color: str = '#C8E8F4',
            hinges_point: float = 0.95,
            opening_outside: bool = False,
            label: str | None = None,
            **kwargs,
    ):
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
            **kwargs,
        )


# ──────────────────────────────────────────────────────────────────────────────
# AluFrame
# ──────────────────────────────────────────────────────────────────────────────

class AluFrame(GlassPanel):
    """
    Aluminium frame without glass infill.

    Identical interface to GlassPanel (``anchor_point``, ``length``,
    ``thickness``, ``height``) but uses the ``alu_frame`` OBJ model which
    contains only the four perimeter bars — no central glass pane.

    In 2D: silver/grey rectangle with a white hollow interior, visually
           showing the frame cross-section.
    In 3D: scaled ``alu_frame`` OBJ model (four aluminium bars only).

    YAML type: ``alu_frame``

    YAML parameters: same as GlassPanel.
    """

    _registry_key = 'alu_frame'
    _requires_external_model = True

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw aluminium frame: silver bars with hollow interior."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        angle_rad = math.radians(self.orientation_angle)

        # Outer rectangle — represents the aluminium bar cross-section
        outer = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor='#A8AAAE',
            edgecolor='#505458',
            linewidth=1.5,
            alpha=0.85,
        )
        outer.set_zorder(self.get_zorder())
        ax.add_patch(outer)

        # Hollow interior (white): shows the open centre of the frame
        bar = min(0.04, self.thickness * 0.35)
        if self.length > 2 * bar and self.thickness > 2 * bar:
            inner = Rectangle(
                rotate_point(self.anchor_point, bar, bar, angle_rad),
                self.length   - 2 * bar,
                self.thickness - 2 * bar,
                angle=self.orientation_angle,
                facecolor='white',
                edgecolor='none',
                alpha=0.9,
            )
            inner.set_zorder(self.get_zorder())
            ax.add_patch(inner)

        render_label_and_id(
            ax=ax,
            element=self,
            element_type='AluFrame',
            position=rotate_point(
                self.anchor_point,
                self.length / 2,
                self.thickness / 2,
                angle_rad,
            ),
            rotation=self.orientation_angle,
        )
