"""
Water feature elements: fountains, ponds.

Author: Krzysztof Bartczak
"""

import matplotlib.axes
from matplotlib.patches import Circle, Polygon
import matplotlib.patches as mpatches
import math
import random

from ...utils import rotate_point, render_label_and_id
from ..element import Element, CircularElement, SurfaceElement, RectangularElement
from ..vertical_levels import VertInfoLvl01


class Fountain(VertInfoLvl01, CircularElement):
    """Fountain element with water spray pattern."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            diameter: float | None = None,
            height: float = 0.5,
            style: str = 'tiered',
            color: str = '#87CEEB',
            basin_color: str = '#A9A9A9',
            label: str | None = None,
            id: str | None = None,
    ):
        """
        Initialize a Fountain instance.

        :param anchor_point:
            coordinates of center point
        :param diameter:
            fountain basin diameter in meters
        :param length:
            fountain height in meters (for label/info)
        :param style:
            fountain style: 'tiered', 'spray', 'simple'
        :param color:
            color for water
        :param basin_color:
            color for the basin/structure
        :param label:
            optional label for the fountain
        :param id:
            optional explicit ID; if None, generated from class name and label
        """
        super().__init__(
            anchor_point=anchor_point,
            diameter=diameter,
            color=color,
            label=label,
            id=id,
        )
        self.height = height
        self.style = style
        self.basin_color = basin_color

    def _default_height(self) -> float:
        """Return default height for fountain."""
        return 1.0

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the fountain with style-specific water pattern."""
        # Draw basin
        basin = Circle(
            self.anchor_point,
            self.diameter / 2,
            facecolor=self.basin_color,
            edgecolor='black',
            linewidth=1.5,
            alpha=0.8
        )
        basin.set_zorder(self.get_zorder())
        ax.add_patch(basin)

        # Draw water surface
        water = Circle(
            self.anchor_point,
            self.diameter / 2 * 0.9,
            facecolor=self.color,
            edgecolor=self.color,
            linewidth=0.5,
            alpha=0.6
        )
        water.set_zorder(self.get_zorder())
        ax.add_patch(water)

        # Draw water pattern based on style
        if self.style == 'tiered':
            self._draw_tiered_pattern(ax)
        elif self.style == 'spray':
            self._draw_spray_pattern(ax)
        elif self.style == 'simple':
            self._draw_simple_pattern(ax)

        # Render label and ID
        from ...utils import render_text_as_label_and_id
        label_text = self._build_label_text()
        position = (self.anchor_point[0], self.anchor_point[1] + self.diameter / 2 + 0.3)
        render_text_as_label_and_id(
            ax=ax,
            element=self,
            text=label_text,
            element_type='Fountain',
            position=position,
            rotation=0
        )

    def _draw_tiered_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw concentric circles for tiered fountain."""
        # Draw 2-3 tiers as concentric circles
        tiers = [0.3, 0.5, 0.7]
        for tier_ratio in tiers:
            radius = (self.diameter / 2) * tier_ratio
            tier_circle = Circle(
                self.anchor_point,
                radius,
                facecolor='none',
                edgecolor=self.basin_color,
                linewidth=1.0,
                alpha=0.7
            )
            tier_circle.set_zorder(self.get_zorder())
            ax.add_patch(tier_circle)
            # Draw small water ripples around each tier
            num_ripples = 8
            for i in range(num_ripples):
                angle = (i / num_ripples) * 2 * math.pi
                x = self.anchor_point[0] + radius * math.cos(angle)
                y = self.anchor_point[1] + radius * math.sin(angle)
                ripple = Circle((x, y), 0.05, facecolor=self.color, 
                              edgecolor='none', alpha=0.4)
                ripple.set_zorder(self.get_zorder())
                ax.add_patch(ripple)

    def _draw_spray_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw radial lines for spray fountain."""
        # Draw radial spray lines from center
        num_sprays = 12
        spray_length = self.diameter / 2 * 0.6
        
        for i in range(num_sprays):
            angle = (i / num_sprays) * 2 * math.pi
            # Main spray line
            x_end = self.anchor_point[0] + spray_length * math.cos(angle)
            y_end = self.anchor_point[1] + spray_length * math.sin(angle)
            ax.plot([self.anchor_point[0], x_end], [self.anchor_point[1], y_end],
                   color=self.color, linewidth=1.5, alpha=0.6)
            
            # Small droplets at the end
            for j in range(3):
                offset = (j + 1) * 0.1
                x_drop = self.anchor_point[0] + (spray_length + offset) * math.cos(angle)
                y_drop = self.anchor_point[1] + (spray_length + offset) * math.sin(angle)
                ax.plot(x_drop, y_drop, 'o', color=self.color, 
                       markersize=2, alpha=0.4)

    def _draw_simple_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw simple ripples for basic fountain."""
        # Draw concentric water ripples
        ripples = [0.3, 0.5, 0.7, 0.9]
        for ripple_ratio in ripples:
            radius = (self.diameter / 2) * ripple_ratio
            ripple = Circle(
                self.anchor_point,
                radius,
                facecolor='none',
                edgecolor=self.color,
                linewidth=0.8,
                linestyle='--',
                alpha=0.5
            )
            ripple.set_zorder(self.get_zorder())
            ax.add_patch(ripple)

    def _build_label_text(self) -> str:
        """Build label text with style and height info."""
        parts = []
        if self.label:
            parts.append(self.label)
        if self.style:
            parts.append(f"({self.style})")
        if self.height:
            parts.append(f"h={self.height}m")
        return " ".join(parts) if parts else ""


class Pond(Element):
    """Pond element with organic shape and water texture."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            length: float | None = None,
            width: float | None = None,
            shape: str = 'oval',
            color: str = '#4682B4',
            border_color: str = '#2F4F4F',
            label: str | None = None,
            id: str | None = None,
    ):
        """
        Initialize a Pond instance.

        :param anchor_point:
            coordinates of center point
        :param length:
            pond length in meters
        :param width:
            pond width in meters
        :param shape:
            pond shape: 'oval', 'kidney', 'rectangular', 'irregular'
        :param color:
            color for water
        :param border_color:
            color for the pond edge/border
        :param label:
            optional label for the pond
        :param id:
            optional explicit ID; if None, generated from class name and label
        """
        super().__init__(anchor_point=anchor_point, label=label, id=id, color=color)
        self.length = length
        self.width = width
        self.shape = shape
        self.border_color = border_color

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the pond with shape-specific rendering."""
        if self.shape == 'oval':
            self._draw_oval_pond(ax)
        elif self.shape == 'kidney':
            self._draw_kidney_pond(ax)
        elif self.shape == 'rectangular':
            self._draw_rectangular_pond(ax)
        elif self.shape == 'irregular':
            self._draw_irregular_pond(ax)

        # Draw water ripples
        self._draw_water_ripples(ax)

        # Render label and ID
        from ...utils import render_text_as_label_and_id
        label_text = self._build_label_text()
        position = (self.anchor_point[0], self.anchor_point[1] + self.width / 2 + 0.3)
        render_text_as_label_and_id(
            ax=ax,
            element=self,
            text=label_text,
            element_type='Pond',
            position=position,
            rotation=0
        )

    def _draw_oval_pond(self, ax: matplotlib.axes.Axes) -> None:
        """Draw oval-shaped pond using ellipse."""
        from matplotlib.patches import Ellipse
        
        # Border
        border = Ellipse(
            self.anchor_point,
            self.length,
            self.width,
            facecolor=self.border_color,
            edgecolor='black',
            linewidth=1.5,
            alpha=0.8
        )
        border.set_zorder(self.get_zorder())
        ax.add_patch(border)
        
        # Water surface
        water = Ellipse(
            self.anchor_point,
            self.length * 0.9,
            self.width * 0.9,
            facecolor=self.color,
            edgecolor=self.color,
            linewidth=0.5,
            alpha=0.6
        )
        water.set_zorder(self.get_zorder())
        ax.add_patch(water)

    def _draw_kidney_pond(self, ax: matplotlib.axes.Axes) -> None:
        """Draw kidney-shaped pond using bezier curves approximation."""
        # Simplified kidney shape using polygon with curved effect
        num_points = 32
        points = []
        
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            # Modify radius to create kidney indent
            indent_factor = 1.0
            if math.pi * 0.3 < angle < math.pi * 0.7:
                indent_factor = 0.6  # Create indent on one side
            
            r_x = (self.length / 2) * indent_factor
            r_y = self.width / 2
            x = self.anchor_point[0] + r_x * math.cos(angle)
            y = self.anchor_point[1] + r_y * math.sin(angle)
            points.append([x, y])
        
        # Border
        border = Polygon(points, facecolor=self.border_color, 
                        edgecolor='black', linewidth=1.5, alpha=0.8)
        border.set_zorder(self.get_zorder())
        ax.add_patch(border)
        
        # Water surface (slightly smaller)
        water_points = []
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            indent_factor = 1.0
            if math.pi * 0.3 < angle < math.pi * 0.7:
                indent_factor = 0.6
            
            r_x = (self.length / 2) * 0.9 * indent_factor
            r_y = (self.width / 2) * 0.9
            x = self.anchor_point[0] + r_x * math.cos(angle)
            y = self.anchor_point[1] + r_y * math.sin(angle)
            water_points.append([x, y])
        
        water = Polygon(water_points, facecolor=self.color,
                       edgecolor=self.color, linewidth=0.5, alpha=0.6)
        water.set_zorder(self.get_zorder())
        ax.add_patch(water)

    def _draw_rectangular_pond(self, ax: matplotlib.axes.Axes) -> None:
        """Draw rectangular pond with rounded corners."""
        from matplotlib.patches import FancyBboxPatch
        
        x = self.anchor_point[0] - self.length / 2
        y = self.anchor_point[1] - self.width / 2
        
        # Border with rounded corners
        border = FancyBboxPatch(
            (x, y),
            self.length,
            self.width,
            boxstyle="round,pad=0.1",
            facecolor=self.border_color,
            edgecolor='black',
            linewidth=1.5,
            alpha=0.8
        )
        border.set_zorder(self.get_zorder())
        ax.add_patch(border)
        
        # Water surface
        water = FancyBboxPatch(
            (x + 0.1, y + 0.1),
            self.length * 0.9,
            self.width * 0.9,
            boxstyle="round,pad=0.08",
            facecolor=self.color,
            edgecolor=self.color,
            linewidth=0.5,
            alpha=0.6
        )
        water.set_zorder(self.get_zorder())
        ax.add_patch(water)

    def _draw_irregular_pond(self, ax: matplotlib.axes.Axes) -> None:
        """Draw irregular organic-shaped pond."""
        random.seed(44)  # Consistent randomness
        num_points = 20
        points = []
        
        for i in range(num_points):
            angle = (i / num_points) * 2 * math.pi
            # Vary radius randomly for organic shape
            r_variation = random.uniform(0.7, 1.0)
            r_x = (self.length / 2) * r_variation
            r_y = (self.width / 2) * r_variation
            x = self.anchor_point[0] + r_x * math.cos(angle)
            y = self.anchor_point[1] + r_y * math.sin(angle)
            points.append([x, y])
        
        # Border
        border = Polygon(points, facecolor=self.border_color,
                        edgecolor='black', linewidth=1.5, alpha=0.8)
        border.set_zorder(self.get_zorder())
        ax.add_patch(border)
        
        # Water surface (slightly smaller)
        water_points = [[p[0] * 0.95 + self.anchor_point[0] * 0.05,
                        p[1] * 0.95 + self.anchor_point[1] * 0.05] for p in points]
        water = Polygon(water_points, facecolor=self.color,
                       edgecolor=self.color, linewidth=0.5, alpha=0.6)
        water.set_zorder(self.get_zorder())
        ax.add_patch(water)

    def _draw_water_ripples(self, ax: matplotlib.axes.Axes) -> None:
        """Draw subtle water ripples on surface."""
        random.seed(45)
        # Draw a few random ripples
        num_ripples = 5
        for _ in range(num_ripples):
            # Random position within pond bounds
            offset_x = random.uniform(-self.length * 0.3, self.length * 0.3)
            offset_y = random.uniform(-self.width * 0.3, self.width * 0.3)
            x = self.anchor_point[0] + offset_x
            y = self.anchor_point[1] + offset_y
            
            # Draw concentric ripples
            for r in [0.1, 0.15, 0.2]:
                ripple = Circle(
                    (x, y),
                    r,
                    facecolor='none',
                    edgecolor='white',
                    linewidth=0.5,
                    linestyle='--',
                    alpha=0.3
                )
                ripple.set_zorder(self.get_zorder())
                ax.add_patch(ripple)

    def _build_label_text(self) -> str:
        """Build label text with shape info."""
        parts = []
        if self.label:
            parts.append(self.label)
        if self.shape:
            parts.append(f"({self.shape})")
        return " ".join(parts) if parts else ""


class RectPool(VertInfoLvl01, RectangularElement):
    """Rectangular swimming pool element for garden/summer use."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            length: float | None = None,
            thickness: float | None = None,
            pool_color: str = '#00BFFF',
            border_color: str = '#B0C4DE',
            show_lanes: bool = False,
            show_steps: bool = True,
            orientation_angle: float = 0,
            label: str | None = None,
            id: str | None = None,
            textures: dict | None = None,
    ):
        """
        Initialize a RectPool instance.

        :param anchor_point:
            coordinates of bottom-left corner
        :param length:
            pool length in meters
        :param thickness:
            pool thickness (width) in meters
        :param pool_color:
            color for pool water (default bright blue)
        :param border_color:
            color for pool edge/border
        :param show_lanes:
            whether to show lane lines
        :param show_steps:
            whether to show entry steps
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the pool
        :param id:
            optional explicit ID; if None, generated from class name and label
        :param textures:
            optional per-face textures and lighting for the 3D export (see ``floor_planner.face_textures``)
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=thickness,
            color=pool_color,
            label=label,
            id=id,
            textures=textures,
        )
        self.pool_color = pool_color
        self.border_color = border_color
        self.show_lanes = show_lanes
        self.show_steps = show_steps

    def _default_height(self) -> float:
        """Return default height for rectangular pool."""
        return 1.4

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the rectangular swimming pool."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw pool border/edge
        from matplotlib.patches import Rectangle
        border = Rectangle(
            (self.anchor_point[0] - 0.15, self.anchor_point[1] - 0.15),
            self.length + 0.3,
            self.thickness + 0.3,
            angle=self.orientation_angle,
            facecolor=self.border_color,
            edgecolor='black',
            linewidth=2,
            alpha=0.9
        )
        border.set_zorder(self.get_zorder())
        ax.add_patch(border)

        # Draw water surface
        water = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor=self.pool_color,
            edgecolor='#4682B4',
            linewidth=1,
            alpha=0.7
        )
        water.set_zorder(self.get_zorder())
        ax.add_patch(water)

        # Draw lane lines if enabled
        if self.show_lanes:
            self._draw_lane_lines(ax)

        # Draw steps if enabled
        if self.show_steps:
            self._draw_steps(ax)


        # Render label and ID
        from ...utils import render_text_as_label_and_id
        label_text = self._build_label_text()
        position = (self.anchor_point[0] + self.length / 2, self.anchor_point[1] + self.thickness + 0.4)
        render_text_as_label_and_id(
            ax=ax,
            element=self,
            text=label_text,
            element_type='Pool',
            position=position,
            rotation=0
        )

    def _draw_lane_lines(self, ax: matplotlib.axes.Axes) -> None:
        """Draw lane divider lines."""
        x = self.anchor_point[0]
        y = self.anchor_point[1]
        # Draw 2-3 vertical lane lines
        num_lanes = max(2, int(self.length / 2.5))
        for i in range(1, num_lanes):
            lane_x = x + (i / num_lanes) * self.length
            # Dashed line
            line_segments = 10
            for j in range(line_segments):
                if j % 2 == 0:  # Draw every other segment
                    seg_y_start = y + (j / line_segments) * self.thickness
                    seg_y_end = y + ((j + 0.8) / line_segments) * self.thickness
                    ax.plot([lane_x, lane_x], [seg_y_start, seg_y_end],
                           color='white', linewidth=1, alpha=0.6)

    def _draw_steps(self, ax: matplotlib.axes.Axes) -> None:
        """Draw entry steps at one corner."""
        x = self.anchor_point[0]
        y = self.anchor_point[1]
        # Draw steps in bottom-left corner
        step_width = min(0.8, self.thickness * 0.2)
        step_height = min(1.0, self.length * 0.25)
        
        num_steps = 3
        for i in range(num_steps):
            step_offset = (i / num_steps) * step_width
            step_rect = mpatches.Rectangle(
                (x + step_offset, y),
                step_width - step_offset,
                step_height,
                facecolor='#4169E1',
                edgecolor='white',
                linewidth=0.8,
                alpha=0.5
            )
            step_rect.set_zorder(self.get_zorder())
            ax.add_patch(step_rect)

    def _build_label_text(self) -> str:
        """Build label text with dimensions."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.length}m×{self.thickness}m")
        return " ".join(parts)


class OvalPool(VertInfoLvl01, RectangularElement):
    """Oval swimming pool element for garden/summer use."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            length: float | None = None,
            thickness: float | None = None,
            pool_color: str = '#00BFFF',
            border_color: str = '#B0C4DE',
            show_steps: bool = True,
            orientation_angle: float = 0,
            label: str | None = None,
            id: str | None = None,
            textures: dict | None = None,
    ):
        """
        Initialize an OvalPool instance.

        :param anchor_point:
            coordinates of bottom-left corner
        :param length:
            pool length in meters
        :param thickness:
            pool thickness (width) in meters
        :param pool_color:
            color for pool water (default bright blue)
        :param border_color:
            color for pool edge/border
        :param show_steps:
            whether to show entry steps
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the pool
        :param id:
            optional explicit ID; if None, generated from class name and label
        :param textures:
            optional per-face textures and lighting for the 3D export (see ``floor_planner.face_textures``)
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=thickness,
            color=pool_color,
            label=label,
            id=id,
            textures=textures,
        )
        self.pool_color = pool_color
        self.border_color = border_color
        self.show_steps = show_steps

    def _default_height(self) -> float:
        """Return default height for oval pool."""
        return 0.0

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the oval swimming pool."""
        from matplotlib.patches import Ellipse
        from matplotlib.transforms import Affine2D
        import numpy as np

        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Create transformation for rotation
        transform = Affine2D().rotate_deg_around(
            self.anchor_point[0] + self.length / 2,
            self.anchor_point[1] + self.thickness / 2,
            self.orientation_angle
        ) + ax.transData

        # Calculate center for ellipse (centered in the rectangular area)
        center_x = self.anchor_point[0] + self.length / 2
        center_y = self.anchor_point[1] + self.thickness / 2

        # Draw pool border/edge (slightly larger ellipse)
        border = Ellipse(
            (center_x, center_y),
            self.length + 0.3,
            self.thickness + 0.3,
            facecolor=self.border_color,
            edgecolor='black',
            linewidth=2,
            alpha=0.9,
            transform=transform
        )
        border.set_zorder(self.get_zorder())
        ax.add_patch(border)

        # Draw water surface
        water = Ellipse(
            (center_x, center_y),
            self.length,
            self.thickness,
            facecolor=self.pool_color,
            edgecolor='#4682B4',
            linewidth=1,
            alpha=0.7,
            transform=transform
        )
        water.set_zorder(self.get_zorder())
        ax.add_patch(water)

        # Draw steps if enabled
        if self.show_steps:
            self._draw_steps(ax)

        # Render label and ID
        from ...utils import render_text_as_label_and_id
        label_text = self._build_label_text()
        center_x = self.anchor_point[0] + self.length / 2
        center_y = self.anchor_point[1] + self.thickness / 2
        position = (center_x, center_y + self.thickness / 2 + 0.4)
        render_text_as_label_and_id(
            ax=ax,
            element=self,
            text=label_text,
            element_type='Pool',
            position=position,
            rotation=0
        )

    def _draw_steps(self, ax: matplotlib.axes.Axes) -> None:
        """Draw semi-circular entry steps."""
        # Steps on one side (bottom of the ellipse)
        center_x = self.anchor_point[0] + self.length / 2
        center_y = self.anchor_point[1] + self.thickness / 2
        step_center_x = center_x
        step_center_y = center_y - self.thickness / 2 + 0.5
        
        # Draw 2-3 semi-circular steps
        step_radii = [0.3, 0.5, 0.7]
        for radius in step_radii:
            step = Circle(
                (step_center_x, step_center_y),
                radius,
                facecolor='#4169E1',
                edgecolor='white',
                linewidth=0.8,
                alpha=0.4
            )
            step.set_zorder(self.get_zorder())
            ax.add_patch(step)

    def _build_label_text(self) -> str:
        """Build label text with dimensions."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.length}m×{self.thickness}m")
        return " ".join(parts)
