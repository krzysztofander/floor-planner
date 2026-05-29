"""
Wooden chair element with external 3D model support.
"""
import math

from matplotlib.axes import Axes
from matplotlib.patches import Rectangle

from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.utils import rotate_point, render_label_and_id
from matplotlib.lines import Line2D


class WoodenChair(ExternalModelElement):
    """
    Wooden chair element that references an external 3D model.
    
    This element demonstrates real-world furniture integration with:
    - External OBJ model (chair.obj)
    - Texture mapping (wood_texture.jpg) 
    - Fixed dimensions from model metadata
    - 2D representation for floor plans
    
    When external model exists (models/wooden_chair/):
    - Loads chair.obj with 100x scale reduction
    - Uses dimensions from model.transform.json
    """
    
    _registry_key = 'wooden_chair'
    _requires_external_model = True  # External model is required, abort if missing
    
    def _default_width(self) -> float:
        """Default width when no external model: 0.45m (typical chair)."""
        return 0.45
    
    def _default_length(self) -> float:
        """Default length when no external model: 0.45m (typical chair)."""
        return 0.45
    
    def _default_height(self) -> float:
        """Default height when no external model: 0.85m (typical chair)."""
        return 0.85
    
    def draw(self, ax: Axes) -> None:
        """
        Draw 2D representation of wooden chair.

        Args:
            ax: Matplotlib axes to draw on
        """
        draw_color = "saddlebrown"  # Dark brown for edges, no fill

        # Main seat rectangle
        patch = Rectangle(
            self.anchor_point,
            self.length,
            self.width,
            angle=self.orientation_angle,
            facecolor='none',
            fill=False,
            edgecolor=draw_color,
            linewidth=1.5
        )
        patch.set_zorder(self.get_zorder())
        ax.add_patch(patch)

        # Draw backrest (thicker line at back)
        backrest_start = rotate_point(
            self.anchor_point,
            0,
            0,
            math.radians(self.orientation_angle)
        )
        backrest_end = rotate_point(
            self.anchor_point,
            self.length,
            0,
            math.radians(self.orientation_angle)
        )

        backrest = Line2D(
            [backrest_start[0], backrest_end[0]],
            [backrest_start[1], backrest_end[1]],
            color=draw_color,
            linewidth=3.0,
            linestyle='-'
        )
        ax.add_line(backrest)

        # Render label and ID
        render_label_and_id(
            ax,
            self,
            'WoodenChair',
            self.anchor_point,
            self.orientation_angle
        )
