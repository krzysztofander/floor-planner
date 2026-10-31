"""
Water Tanks

Author: Krzysztof Bartczak
"""

import matplotlib.axes
from matplotlib.patches import Rectangle, Polygon, Circle
import math

from ...utils import rotate_point, render_label_and_id
from ..element import  CircularElement
from ..vertical_levels import VertInfoLvl03
#from ...geometry_3d import CircularGeometry3D


class GenericTank(VertInfoLvl03, CircularElement):
    """Generic water tank"""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            diameter: float = 0.6,
            height: float = 1.32,
            v_anchor: float = 0.05,
            color: str = "#7B7060",
            label: str | None = None,
            id: str | None = None,
    ):
        super().__init__(
            anchor_point=anchor_point,
            diameter=diameter,
            height=height,
            v_anchor=v_anchor, 
            color=color,
            label=label,
            id=id,
        )

    def _default_height(self) -> float:
        """Return default height for tank."""
        # At diameter 0.6 this will give 150 liters
        return 1.32

    def _draw_main_circle(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the main circular shape."""
        circle = Circle(
            self.anchor_point,
            self.diameter / 2,
            facecolor='none',
            edgecolor=self.color,
            linewidth=1.5
        )
        ax.add_patch(circle)
    
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the water tank symbol."""
        self._draw_main_circle(ax)
        self._render_label_and_id(ax)
    
    def _build_label_text(self) -> str:
        """Build label text with diameter."""
        parts = []
        if self.label:
            parts.append(self.label)
        self.height
        parts.append(f"\nØ{round(self.diameter*100)}x{round(self.height*100)}cm")
        return " ".join(parts) if parts else ""

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        if self.label:
            label_text = self._build_label_text()
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Tank',
                position=(self.anchor_point[0], self.anchor_point[1]),
                rotation=45,
                centered= True
            )
            self.label = original_label

