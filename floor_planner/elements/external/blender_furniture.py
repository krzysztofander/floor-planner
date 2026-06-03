"""
Furniture elements sourced from Blender (.blend) models.

Each class references an external OBJ model exported from Blender with
Y-up / right-handed convention (up_axis='Y', forward_axis='NEGATIVE_Z').
All models are in meters, no additional scale is needed.

Model directory structure:
    models/<registry_key>/model.obj
    models/<registry_key>/model.mtl
    models/<registry_key>/<registry_key>_diffuse.png
    models/<registry_key>/model.transform.json
"""
import math

from matplotlib.axes import Axes
from matplotlib.patches import Rectangle, Arc, FancyArrow
from matplotlib.lines import Line2D

from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.utils import rotate_point, render_label_and_id


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _rect(ax: Axes, anchor, width, length, angle_rad, color, lw=1.0):
    """Draw a rotated rectangle (floor-plan outline helper)."""
    patch = Rectangle(
        anchor,
        width,
        length,
        linewidth=lw,
        edgecolor=color,
        facecolor='white',
        angle=math.degrees(angle_rad),
        rotation_point='xy',
    )
    ax.add_patch(patch)


def _thick_line(ax: Axes, p0, p1, color, lw):
    """Draw a thick line between two points."""
    ax.add_line(Line2D([p0[0], p1[0]], [p0[1], p1[1]],
                       linewidth=lw, color=color, solid_capstyle='round'))


def _rotated_corner(anchor, dx, dy, angle_rad):
    """Translate (dx, dy) relative to anchor, then rotate around anchor."""
    return rotate_point(anchor, dx, dy, angle_rad)


# ---------------------------------------------------------------------------
# Armchair  (0.776 × 0.825 × 0.747 m)
# ---------------------------------------------------------------------------

class Armchair(ExternalModelElement):
    """
    Bergère / club armchair with external 3D model.

    Dimensions from model.transform.json:
      Width  (X): 0.776 m
      Length (Y): 0.825 m
      Height (Z): 0.747 m

    Anchor: bottom-left-front corner.
    Long axis runs in Y (depth) direction at orientation_angle=0.
    """

    _registry_key = 'armchair'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 0.776

    def _default_length(self) -> float:
        return 0.825

    def _default_height(self) -> float:
        return 0.747

    def draw(self, ax: Axes) -> None:
        color = 'saddlebrown'
        angle_rad = math.radians(self.orientation_angle)
        w, l = self.width, self.length

        # Outline
        _rect(ax, self.anchor_point, w, l, angle_rad, color)

        # Backrest: thick line at far Y edge
        bl = _rotated_corner(self.anchor_point, 0, l * 0.85, angle_rad)
        br = _rotated_corner(self.anchor_point, w, l * 0.85, angle_rad)
        _thick_line(ax, bl, br, color, lw=4)

        # Armrests: thick lines along both X sides
        la0 = _rotated_corner(self.anchor_point, 0, 0, angle_rad)
        la1 = _rotated_corner(self.anchor_point, 0, l * 0.9, angle_rad)
        ra0 = _rotated_corner(self.anchor_point, w, 0, angle_rad)
        ra1 = _rotated_corner(self.anchor_point, w, l * 0.9, angle_rad)
        _thick_line(ax, la0, la1, color, lw=3)
        _thick_line(ax, ra0, ra1, color, lw=3)

        # Seat cushion area (inner rectangle)
        pad_x, pad_y = w * 0.12, l * 0.07
        seat = Rectangle(
            _rotated_corner(self.anchor_point, pad_x, pad_y, angle_rad),
            w * 0.76, l * 0.7,
            linewidth=0.5, edgecolor=color, facecolor='none',
            angle=math.degrees(angle_rad), rotation_point='xy',
        )
        ax.add_patch(seat)

        render_label_and_id(ax, self, 'Armchair', self.anchor_point, self.orientation_angle)


# ---------------------------------------------------------------------------
# Chair 20  (0.661 × 0.687 × 1.295 m  — high-back dining/accent chair)
# ---------------------------------------------------------------------------

class Chair20(ExternalModelElement):
    """
    High-back accent / dining chair with external 3D model.

    Dimensions:
      Width  (X): 0.661 m
      Length (Y): 0.687 m
      Height (Z): 1.295 m  (tall back-rest)

    Anchor: bottom-left-front corner.
    """

    _registry_key = 'chair_20'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 0.661

    def _default_length(self) -> float:
        return 0.687

    def _default_height(self) -> float:
        return 1.295

    def draw(self, ax: Axes) -> None:
        color = 'sienna'
        angle_rad = math.radians(self.orientation_angle)
        w, l = self.width, self.length

        _rect(ax, self.anchor_point, w, l, angle_rad, color)

        # Backrest at far Y edge
        bl = _rotated_corner(self.anchor_point, 0, l * 0.82, angle_rad)
        br = _rotated_corner(self.anchor_point, w, l * 0.82, angle_rad)
        _thick_line(ax, bl, br, color, lw=4)

        # Seat
        seat = Rectangle(
            _rotated_corner(self.anchor_point, w * 0.1, l * 0.05, angle_rad),
            w * 0.8, l * 0.7,
            linewidth=0.5, edgecolor=color, facecolor='none',
            angle=math.degrees(angle_rad), rotation_point='xy',
        )
        ax.add_patch(seat)

        render_label_and_id(ax, self, 'Chair20', self.anchor_point, self.orientation_angle)


# ---------------------------------------------------------------------------
# Chaise Longue 1  (0.783 × 1.649 × 0.808 m)
# ---------------------------------------------------------------------------

class ChaiseLongue1(ExternalModelElement):
    """
    Chaise longue / daybed with external 3D model.

    Dimensions:
      Width  (X): 0.783 m
      Length (Y): 1.649 m
      Height (Z): 0.808 m

    Anchor: bottom-left-front corner.
    Long axis runs in Y at orientation_angle=0.
    """

    _registry_key = 'chaise_longue_1'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 0.783

    def _default_length(self) -> float:
        return 1.649

    def _default_height(self) -> float:
        return 0.808

    def draw(self, ax: Axes) -> None:
        color = 'peru'
        angle_rad = math.radians(self.orientation_angle)
        w, l = self.width, self.length

        _rect(ax, self.anchor_point, w, l, angle_rad, color)

        # Backrest along one X side (left side at angle=0)
        p0 = _rotated_corner(self.anchor_point, 0, 0, angle_rad)
        p1 = _rotated_corner(self.anchor_point, 0, l, angle_rad)
        _thick_line(ax, p0, p1, color, lw=4)

        # Headrest bump at far Y end
        hr0 = _rotated_corner(self.anchor_point, 0, l * 0.85, angle_rad)
        hr1 = _rotated_corner(self.anchor_point, w * 0.55, l * 0.85, angle_rad)
        _thick_line(ax, hr0, hr1, color, lw=3)

        render_label_and_id(ax, self, 'ChaiseLongue1', self.anchor_point, self.orientation_angle)


# ---------------------------------------------------------------------------
# Desk 1  (2.059 × 0.971 × 1.095 m — large desk with overhead hutch)
# ---------------------------------------------------------------------------

class Desk1(ExternalModelElement):
    """
    Large office/study desk (with upper hutch) from external 3D model.

    Dimensions:
      Width  (X): 2.059 m
      Length (Y): 0.971 m
      Height (Z): 1.095 m

    Anchor: bottom-left-front corner.
    Long axis runs in X at orientation_angle=0.
    """

    _registry_key = 'desk_1'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 2.059

    def _default_length(self) -> float:
        return 0.971

    def _default_height(self) -> float:
        return 1.095

    def draw(self, ax: Axes) -> None:
        color = 'chocolate'
        angle_rad = math.radians(self.orientation_angle)
        w, l = self.width, self.length

        _rect(ax, self.anchor_point, w, l, angle_rad, color)

        # Back wall (hutch backing) at far Y
        bl = _rotated_corner(self.anchor_point, 0, l * 0.85, angle_rad)
        br = _rotated_corner(self.anchor_point, w, l * 0.85, angle_rad)
        _thick_line(ax, bl, br, color, lw=3)

        # Desktop surface line
        ds0 = _rotated_corner(self.anchor_point, w * 0.05, l * 0.15, angle_rad)
        ds1 = _rotated_corner(self.anchor_point, w * 0.95, l * 0.15, angle_rad)
        _thick_line(ax, ds0, ds1, color, lw=1)

        render_label_and_id(ax, self, 'Desk1', self.anchor_point, self.orientation_angle)


# ---------------------------------------------------------------------------
# Sofa 22  (2.835 × 0.904 × 0.702 m — large 3-seat sofa)
# ---------------------------------------------------------------------------

class Sofa22(ExternalModelElement):
    """
    Large 3-seat sofa with external 3D model.

    Dimensions:
      Width  (X): 2.835 m
      Length (Y): 0.904 m
      Height (Z): 0.702 m

    Anchor: bottom-left-front corner.
    Long axis runs in X at orientation_angle=0.
    Backrest is at the far Y edge (place against a wall with orientation 0).
    """

    _registry_key = 'sofa_22'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 2.835

    def _default_length(self) -> float:
        return 0.904

    def _default_height(self) -> float:
        return 0.702

    def draw(self, ax: Axes) -> None:
        color = 'slategray'
        angle_rad = math.radians(self.orientation_angle)
        w, l = self.width, self.length

        _rect(ax, self.anchor_point, w, l, angle_rad, color)

        # Backrest at far Y
        bl = _rotated_corner(self.anchor_point, 0, l * 0.80, angle_rad)
        br = _rotated_corner(self.anchor_point, w, l * 0.80, angle_rad)
        _thick_line(ax, bl, br, color, lw=5)

        # Three cushion dividers
        for frac in (1/3, 2/3):
            p0 = _rotated_corner(self.anchor_point, w * frac, 0, angle_rad)
            p1 = _rotated_corner(self.anchor_point, w * frac, l * 0.78, angle_rad)
            _thick_line(ax, p0, p1, color, lw=0.8)

        # Armrests
        la0 = _rotated_corner(self.anchor_point, 0, 0, angle_rad)
        la1 = _rotated_corner(self.anchor_point, 0, l * 0.88, angle_rad)
        ra0 = _rotated_corner(self.anchor_point, w, 0, angle_rad)
        ra1 = _rotated_corner(self.anchor_point, w, l * 0.88, angle_rad)
        _thick_line(ax, la0, la1, color, lw=3)
        _thick_line(ax, ra0, ra1, color, lw=3)

        render_label_and_id(ax, self, 'Sofa22', self.anchor_point, self.orientation_angle)


# ---------------------------------------------------------------------------
# Sofa 23  (2.003 × 0.903 × 0.702 m — medium 2-seat sofa)
# ---------------------------------------------------------------------------

class Sofa23(ExternalModelElement):
    """
    Medium 2-seat sofa with external 3D model.

    Dimensions:
      Width  (X): 2.003 m
      Length (Y): 0.903 m
      Height (Z): 0.702 m

    Anchor: bottom-left-front corner.
    Long axis runs in X at orientation_angle=0.
    """

    _registry_key = 'sofa_23'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 2.003

    def _default_length(self) -> float:
        return 0.903

    def _default_height(self) -> float:
        return 0.702

    def draw(self, ax: Axes) -> None:
        color = 'steelblue'
        angle_rad = math.radians(self.orientation_angle)
        w, l = self.width, self.length

        _rect(ax, self.anchor_point, w, l, angle_rad, color)

        # Backrest
        bl = _rotated_corner(self.anchor_point, 0, l * 0.80, angle_rad)
        br = _rotated_corner(self.anchor_point, w, l * 0.80, angle_rad)
        _thick_line(ax, bl, br, color, lw=5)

        # Two cushion divider
        p0 = _rotated_corner(self.anchor_point, w * 0.5, 0, angle_rad)
        p1 = _rotated_corner(self.anchor_point, w * 0.5, l * 0.78, angle_rad)
        _thick_line(ax, p0, p1, color, lw=0.8)

        # Armrests
        la0 = _rotated_corner(self.anchor_point, 0, 0, angle_rad)
        la1 = _rotated_corner(self.anchor_point, 0, l * 0.88, angle_rad)
        ra0 = _rotated_corner(self.anchor_point, w, 0, angle_rad)
        ra1 = _rotated_corner(self.anchor_point, w, l * 0.88, angle_rad)
        _thick_line(ax, la0, la1, color, lw=3)
        _thick_line(ax, ra0, ra1, color, lw=3)

        render_label_and_id(ax, self, 'Sofa23', self.anchor_point, self.orientation_angle)


# ---------------------------------------------------------------------------
# Stool 7  (0.297 × 0.297 × 0.670 m — round/square bar stool)
# ---------------------------------------------------------------------------

class Stool7(ExternalModelElement):
    """
    Bar / counter stool with external 3D model.

    Dimensions (roughly square footprint):
      Width  (X): 0.297 m
      Length (Y): 0.297 m
      Height (Z): 0.670 m

    Anchor: bottom-left-front corner.
    """

    _registry_key = 'stool_7'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 0.297

    def _default_length(self) -> float:
        return 0.297

    def _default_height(self) -> float:
        return 0.670

    def draw(self, ax: Axes) -> None:
        color = 'gray'
        angle_rad = math.radians(self.orientation_angle)
        w, l = self.width, self.length

        _rect(ax, self.anchor_point, w, l, angle_rad, color)

        # Cross to indicate seat
        cx = _rotated_corner(self.anchor_point, w * 0.5, l * 0.5, angle_rad)
        r = min(w, l) * 0.35
        from matplotlib.patches import Circle
        seat = Circle(cx, r, linewidth=1, edgecolor=color, facecolor='none')
        ax.add_patch(seat)

        render_label_and_id(ax, self, 'Stool7', self.anchor_point, self.orientation_angle)


# ---------------------------------------------------------------------------
# Table 01  (4.123 × 1.671 × 0.854 m — large dining / conference table)
# ---------------------------------------------------------------------------

class Table01(ExternalModelElement):
    """
    Large dining / conference table with external 3D model.

    Dimensions:
      Width  (X): 4.123 m
      Length (Y): 1.671 m
      Height (Z): 0.854 m

    Anchor: bottom-left-front corner.
    Long axis runs in X at orientation_angle=0.
    """

    _registry_key = 'table_01'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 4.123

    def _default_length(self) -> float:
        return 1.671

    def _default_height(self) -> float:
        return 0.854

    def draw(self, ax: Axes) -> None:
        color = 'burlywood'
        angle_rad = math.radians(self.orientation_angle)
        w, l = self.width, self.length

        _rect(ax, self.anchor_point, w, l, angle_rad, color, lw=1.5)

        # Inset surface to indicate table top
        pad = min(w, l) * 0.04
        top = Rectangle(
            _rotated_corner(self.anchor_point, pad, pad, angle_rad),
            w - 2 * pad, l - 2 * pad,
            linewidth=0.5, edgecolor=color, facecolor='none',
            angle=math.degrees(angle_rad), rotation_point='xy',
        )
        ax.add_patch(top)

        # Leg dots at four corners
        margin = min(w, l) * 0.06
        for dx, dy in [(margin, margin), (w - margin, margin),
                       (margin, l - margin), (w - margin, l - margin)]:
            pt = _rotated_corner(self.anchor_point, dx, dy, angle_rad)
            from matplotlib.patches import Circle
            ax.add_patch(Circle(pt, 0.03, color=color))

        render_label_and_id(ax, self, 'Table01', self.anchor_point, self.orientation_angle)
