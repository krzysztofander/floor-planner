"""
Test element for external model integration.

This is a simple test element that demonstrates the hybrid 2D+3D rendering
approach. It draws a simple rectangle in 2D floor plans and can optionally
load an external 3D model when present.

Purpose:
- Validate external model loading pipeline
- Test transform chain (normalization + placement)
- Verify fallback to 2D when model missing
- Demonstrate registry-based model path resolution

Author: Floor Planner Team
Created: 2026-05-27
"""

import matplotlib.axes
import matplotlib.patches as mpatches

from .external_models import ExternalModelElement
from ..utils import rotate_point


class ExternalModelTest(ExternalModelElement):
    """
    Test element for external model integration.
    
    Draws a simple 1m × 0.5m × 0.3m rectangular box in 2D floor plans.
    When external model exists (models/external_model_test/model.glb),
    it will also be exported to 3D. When model is missing, falls back
    to procedural 2D rendering only.
    
    Dimensions are fixed (cannot be changed by user):
    - Width: 1.0 m (X-axis)
    - Length: 0.5 m (Z-axis)
    - Height: 0.3 m (Y-axis)
    
    YAML Configuration:
        - type: external_model_test
          id: test_001
          anchor_point: [2, 3]
          orientation_angle: 45
          v_anchor: 0.0
          color: [200, 150, 100]  # Optional brown color
          label: "Test Element"    # Optional label
    
    Registry key: 'external_model_test'
    Model path: models/external_model_test/model.glb
    Metadata path: models/external_model_test/model.transform.json
    """
    
    _registry_key = 'external_model_test'
    
    def __init__(
        self,
        anchor_point: tuple[float, float],
        orientation_angle: float = 0.0,
        color: tuple[int, int, int] | str | None = None,
        label: str | None = None,
        id: str | None = None,
        v_anchor: float | None = None,
        **kwargs
    ):
        """
        Initialize test element.
        
        Args:
            anchor_point: (x, y) position in floor plan (meters)
            orientation_angle: Rotation around vertical axis (degrees, default 0)
            color: Optional color for 2D rendering (default: brown wood)
            label: Optional label
            id: Optional explicit ID
            v_anchor: Vertical position (meters, default 0.0 = floor level)
            **kwargs: Additional params passed to parent (rejected if width/length/height)
            
        Raises:
            ValueError: If user tries to override width/length/height
        """
        # Set default color if not specified (brown wood)
        if color is None:
            color = (200, 150, 100)
        
        # Initialize parent (handles model loading if exists)
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            id=id,
            v_anchor=v_anchor,
            **kwargs
        )
    
    def _default_width(self) -> float:
        """Fixed width when no external model exists."""
        return 1.0
    
    def _default_length(self) -> float:
        """Fixed length when no external model exists."""
        return 0.5
    
    def _default_height(self) -> float:
        """Fixed height when no external model exists."""
        return 0.3
    
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """
        Draw test element as a simple rectangle in 2D floor plan.
        
        Draws a filled rectangle with the element's color. The rectangle
        represents the top-down view of the element's bounding box.
        
        Args:
            ax: Matplotlib axes to draw on
        """
        # Get color for drawing (handles 'invisible' color)
        draw_color = self.get_draw_color()
        if draw_color is None:
            return  # Element is invisible and should not be drawn
        
        # Calculate four corners of rectangle (bottom-left anchor)
        # In 2D floor plan: anchor is bottom-left, extends right (length) and up (width)
        corners = [
            (0, 0),              # Bottom-left (anchor)
            (self.length, 0),    # Bottom-right
            (self.length, self.width),  # Top-right
            (0, self.width)      # Top-left
        ]
        
        # Rotate corners around anchor point
        import math
        angle_rad = math.radians(self.orientation_angle)
        rotated_corners = [
            rotate_point(self.anchor_point, corner[0], corner[1], angle_rad)
            for corner in corners
        ]
        
        # Create polygon patch
        polygon = mpatches.Polygon(
            rotated_corners,
            closed=True,
            facecolor=draw_color if isinstance(draw_color, str) else [c/255 for c in draw_color],
            edgecolor='black',
            linewidth=0.5,
            zorder=self.get_zorder()
        )
        
        ax.add_patch(polygon)
        
        # Add label if specified
        if self.label:
            # Calculate center of rectangle
            center_x = sum(corner[0] for corner in rotated_corners) / 4
            center_y = sum(corner[1] for corner in rotated_corners) / 4
            
            ax.text(
                center_x, center_y, self.label,
                fontsize=8,
                ha='center', va='center',
                zorder=self.get_zorder() + 0.1
            )
