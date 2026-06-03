"""
Master bed (king size) element with external 3D model support.
"""
import math

from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.utils import rotate_point, render_label_and_id


class MasterBed(ExternalModelElement):
    """
    King-size master bed element that references an external 3D model.

    Model dimensions from models/master_bed/model.transform.json:
      - Width (X): ~1.749 m  (side-to-side)
      - Length (Z): ~2.257 m (foot to headboard)
      - Height (Y): ~1.190 m (floor to top of headboard)

    Anchor point: floor-level bottom-left corner at the foot of the bed.
    The headboard is at the far end (anchor local-Y = self.length).

    3D model: OBJ originally in centimetres / Z-up (3DS Max export).
    Normalisation in model.transform.json converts it to metres / Y-up and
    places the origin at the anchor point.
    """

    _registry_key = 'master_bed'
    _requires_external_model = True

    def _default_width(self) -> float:
        """Default width when no external model: 1.75 m (king size)."""
        return 1.75

    def _default_length(self) -> float:
        """Default length when no external model: 2.25 m (king size)."""
        return 2.25

    def _default_height(self) -> float:
        """Default height when no external model: 1.19 m (incl. headboard)."""
        return 1.19

    def draw(self, ax: Axes) -> None:
        """
        Draw 2D top-down representation of the master bed.

        Draws:
          - Full bed outline (rectangle)
          - Headboard (thick line at the head end)
          - Two pillows (rectangles near the headboard)
        """
        draw_color = 'dimgrey'
        angle_rad = math.radians(self.orientation_angle)

        # --- Bed outline ---
        patch = Rectangle(
            self.anchor_point,
            self.width,
            self.length,
            angle=self.orientation_angle,
            facecolor='none',
            fill=False,
            edgecolor=draw_color,
            linewidth=1.5,
        )
        patch.set_zorder(self.get_zorder())
        ax.add_patch(patch)

        # --- Headboard (thick line at head end, dy = self.length) ---
        hb_left = rotate_point(self.anchor_point, 0, self.length, angle_rad)
        hb_right = rotate_point(self.anchor_point, self.width, self.length, angle_rad)
        headboard = Line2D(
            [hb_left[0], hb_right[0]],
            [hb_left[1], hb_right[1]],
            color=draw_color,
            linewidth=4.0,
            linestyle='-',
        )
        headboard.set_zorder(self.get_zorder())
        ax.add_line(headboard)

        # --- Two pillows near headboard ---
        pillow_w = 0.60   # x-extent
        pillow_h = 0.50   # y-extent
        pillow_margin = 0.08
        pillow_dy = self.length - pillow_h - pillow_margin  # near headboard

        for i in range(2):
            pillow_dx = pillow_margin + i * (self.width - pillow_margin - pillow_w)
            pillow_anchor = rotate_point(
                self.anchor_point, pillow_dx, pillow_dy, angle_rad
            )
            pillow = Rectangle(
                pillow_anchor,
                pillow_w,
                pillow_h,
                angle=self.orientation_angle,
                facecolor='whitesmoke',
                edgecolor=draw_color,
                linewidth=1.0,
            )
            pillow.set_zorder(self.get_zorder())
            ax.add_patch(pillow)

        # --- Label ---
        render_label_and_id(
            ax,
            self,
            'Master Bed',
            self.anchor_point,
            self.orientation_angle,
        )
