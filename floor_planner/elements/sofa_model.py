"""
Realistic sofa element with external 3D model support.
"""
import math

from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.utils import rotate_point, render_label_and_id


class SofaModel(ExternalModelElement):
    """
    Realistic sofa element that references an external 3D model.

    Model dimensions from models/sofa_model/model.transform.json:
      - Width  (X): 0.490 m  (front-to-back depth)
      - Length (Z): 1.368 m  (arm-to-arm)
      - Height (Y): 0.489 m  (floor to top of back cushion)

    Anchor point: floor-level bottom-left corner.

    3D model: OBJ exported from Cinema 4D in millimetres / Y-up.
    Normalisation in model.transform.json converts it to metres and
    places the origin at the anchor point.

    YAML key: ``sofa_model``

    Example usage::

        - type: sofa_model
          anchor_point: [1.0, 0.5]
          orientation_angle: 180   # sofa faces South (front toward viewer)
    """

    _registry_key = 'sofa_model'
    _requires_external_model = True

    def _default_width(self) -> float:
        """Default front-to-back depth: 0.49 m."""
        return 0.49

    def _default_length(self) -> float:
        """Default arm-to-arm length: 1.37 m."""
        return 1.37

    def _default_height(self) -> float:
        """Default floor-to-top-of-back height: 0.49 m."""
        return 0.49

    def draw(self, ax: Axes) -> None:
        """
        Draw 2D top-down representation of the sofa.

        Draws:
          - Full sofa outline (rectangle)
          - Backrest (thick line at back edge, local Y = 0)
          - Seat cushions (two rectangles)
        """
        draw_color = 'saddlebrown'
        angle_rad = math.radians(self.orientation_angle)

        # --- Sofa body outline ---
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

        # --- Backrest (thick line at local Y=0 edge, dx=0..width) ---
        back_l = rotate_point(self.anchor_point, 0, 0, angle_rad)
        back_r = rotate_point(self.anchor_point, self.width, 0, angle_rad)
        backrest = Line2D(
            [back_l[0], back_r[0]],
            [back_l[1], back_r[1]],
            color=draw_color,
            linewidth=4.0,
            linestyle='-',
        )
        backrest.set_zorder(self.get_zorder())
        ax.add_line(backrest)

        # --- Two seat cushions ---
        cushion_margin = 0.04
        # Each cushion takes half the arm-to-arm length (self.length)
        cush_h = (self.length - 3 * cushion_margin) / 2
        cush_w = self.width * 0.60   # cushion depth = 60% of sofa depth
        cush_x = (self.width - cush_w) / 2  # centred front-to-back
        backrest_thickness = 0.12

        for i in range(2):
            cush_y = backrest_thickness + cushion_margin + i * (cush_h + cushion_margin)
            ca = rotate_point(self.anchor_point, cush_x, cush_y, angle_rad)
            cushion = Rectangle(
                ca,
                cush_w,
                cush_h,
                angle=self.orientation_angle,
                facecolor='none',
                edgecolor=draw_color,
                linewidth=0.8,
            )
            cushion.set_zorder(self.get_zorder())
            ax.add_patch(cushion)

        # --- Label ---
        render_label_and_id(
            ax,
            self,
            'Sofa',
            self.anchor_point,
            self.orientation_angle,
        )
