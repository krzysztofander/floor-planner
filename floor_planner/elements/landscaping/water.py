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
from ..element import Element


class Fountain(Element):
    """Fountain element with water spray pattern."""

    def __init__(
            self,
            anchor: tuple[float, float],
            diameter: float,
            height: float = 0.5,
            style: str = 'tiered',
            color: str = '#87CEEB',
            basin_color: str = '#A9A9A9',
            label: str | None = None
    ):
        """
        Initialize a Fountain instance.

        :param anchor:
            coordinates of center point
        :param diameter:
            fountain basin diameter in meters
        :param height:
            fountain height in meters (for label/info)
        :param style:
            fountain style: 'tiered', 'spray', 'simple'
        :param color:
            color for water
        :param basin_color:
            color for the basin/structure
        :param label:
            optional label for the fountain
        """
        super().__init__(label=label)
        self.anchor = anchor
        self.diameter = diameter
        self.height = height
        self.style = style
        self.color = color
        self.basin_color = basin_color

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the fountain with style-specific water pattern."""
        # Draw basin
        basin = Circle(
            self.anchor,
            self.diameter / 2,
            facecolor=self.basin_color,
            edgecolor='black',
            linewidth=1.5,
            alpha=0.8
        )
        ax.add_patch(basin)

        # Draw water surface
        water = Circle(
            self.anchor,
            self.diameter / 2 * 0.9,
            facecolor=self.color,
            edgecolor=self.color,
            linewidth=0.5,
            alpha=0.6
        )
        ax.add_patch(water)

        # Draw water pattern based on style
        if self.style == 'tiered':
            self._draw_tiered_pattern(ax)
        elif self.style == 'spray':
            self._draw_spray_pattern(ax)
        elif self.style == 'simple':
            self._draw_simple_pattern(ax)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_tiered_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw concentric circles for tiered fountain."""
        # Draw 2-3 tiers as concentric circles
        tiers = [0.3, 0.5, 0.7]
        for tier_ratio in tiers:
            radius = (self.diameter / 2) * tier_ratio
            tier_circle = Circle(
                self.anchor,
                radius,
                facecolor='none',
                edgecolor=self.basin_color,
                linewidth=1.0,
                alpha=0.7
            )
            ax.add_patch(tier_circle)
            # Draw small water ripples around each tier
            num_ripples = 8
            for i in range(num_ripples):
                angle = (i / num_ripples) * 2 * math.pi
                x = self.anchor[0] + radius * math.cos(angle)
                y = self.anchor[1] + radius * math.sin(angle)
                ripple = Circle((x, y), 0.05, facecolor=self.color, 
                              edgecolor='none', alpha=0.4)
                ax.add_patch(ripple)

    def _draw_spray_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw radial lines for spray fountain."""
        # Draw radial spray lines from center
        num_sprays = 12
        spray_length = self.diameter / 2 * 0.6
        
        for i in range(num_sprays):
            angle = (i / num_sprays) * 2 * math.pi
            # Main spray line
            x_end = self.anchor[0] + spray_length * math.cos(angle)
            y_end = self.anchor[1] + spray_length * math.sin(angle)
            ax.plot([self.anchor[0], x_end], [self.anchor[1], y_end],
                   color=self.color, linewidth=1.5, alpha=0.6)
            
            # Small droplets at the end
            for j in range(3):
                offset = (j + 1) * 0.1
                x_drop = self.anchor[0] + (spray_length + offset) * math.cos(angle)
                y_drop = self.anchor[1] + (spray_length + offset) * math.sin(angle)
                ax.plot(x_drop, y_drop, 'o', color=self.color, 
                       markersize=2, alpha=0.4)

    def _draw_simple_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw simple ripples for basic fountain."""
        # Draw concentric water ripples
        ripples = [0.3, 0.5, 0.7, 0.9]
        for ripple_ratio in ripples:
            radius = (self.diameter / 2) * ripple_ratio
            ripple = Circle(
                self.anchor,
                radius,
                facecolor='none',
                edgecolor=self.color,
                linewidth=0.8,
                linestyle='--',
                alpha=0.5
            )
            ax.add_patch(ripple)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for fountain."""
        label_text = self._build_label_text()
        if label_text:
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Fountain',
                position=(self.anchor[0], self.anchor[1] + self.diameter / 2 + 0.3),
                rotation=0
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Fountain',
                position=(self.anchor[0], self.anchor[1] + self.diameter / 2 + 0.3),
                rotation=0
            )

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
            anchor: tuple[float, float],
            length: float,
            width: float,
            shape: str = 'oval',
            color: str = '#4682B4',
            border_color: str = '#2F4F4F',
            label: str | None = None
    ):
        """
        Initialize a Pond instance.

        :param anchor:
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
        """
        super().__init__(label=label)
        self.anchor = anchor
        self.length = length
        self.width = width
        self.shape = shape
        self.color = color
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
        self._render_label_and_id(ax)

    def _draw_oval_pond(self, ax: matplotlib.axes.Axes) -> None:
        """Draw oval-shaped pond using ellipse."""
        from matplotlib.patches import Ellipse
        
        # Border
        border = Ellipse(
            self.anchor,
            self.length,
            self.width,
            facecolor=self.border_color,
            edgecolor='black',
            linewidth=1.5,
            alpha=0.8
        )
        ax.add_patch(border)
        
        # Water surface
        water = Ellipse(
            self.anchor,
            self.length * 0.9,
            self.width * 0.9,
            facecolor=self.color,
            edgecolor=self.color,
            linewidth=0.5,
            alpha=0.6
        )
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
            x = self.anchor[0] + r_x * math.cos(angle)
            y = self.anchor[1] + r_y * math.sin(angle)
            points.append([x, y])
        
        # Border
        border = Polygon(points, facecolor=self.border_color, 
                        edgecolor='black', linewidth=1.5, alpha=0.8)
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
            x = self.anchor[0] + r_x * math.cos(angle)
            y = self.anchor[1] + r_y * math.sin(angle)
            water_points.append([x, y])
        
        water = Polygon(water_points, facecolor=self.color,
                       edgecolor=self.color, linewidth=0.5, alpha=0.6)
        ax.add_patch(water)

    def _draw_rectangular_pond(self, ax: matplotlib.axes.Axes) -> None:
        """Draw rectangular pond with rounded corners."""
        from matplotlib.patches import FancyBboxPatch
        
        x = self.anchor[0] - self.length / 2
        y = self.anchor[1] - self.width / 2
        
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
            x = self.anchor[0] + r_x * math.cos(angle)
            y = self.anchor[1] + r_y * math.sin(angle)
            points.append([x, y])
        
        # Border
        border = Polygon(points, facecolor=self.border_color,
                        edgecolor='black', linewidth=1.5, alpha=0.8)
        ax.add_patch(border)
        
        # Water surface (slightly smaller)
        water_points = [[p[0] * 0.95 + self.anchor[0] * 0.05,
                        p[1] * 0.95 + self.anchor[1] * 0.05] for p in points]
        water = Polygon(water_points, facecolor=self.color,
                       edgecolor=self.color, linewidth=0.5, alpha=0.6)
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
            x = self.anchor[0] + offset_x
            y = self.anchor[1] + offset_y
            
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
                ax.add_patch(ripple)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for pond."""
        label_text = self._build_label_text()
        if label_text:
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Pond',
                position=(self.anchor[0], self.anchor[1] + self.width / 2 + 0.3),
                rotation=0
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Pond',
                position=(self.anchor[0], self.anchor[1] + self.width / 2 + 0.3),
                rotation=0
            )

    def _build_label_text(self) -> str:
        """Build label text with shape info."""
        parts = []
        if self.label:
            parts.append(self.label)
        if self.shape:
            parts.append(f"({self.shape})")
        return " ".join(parts) if parts else ""


class RectPool(Element):
    """Rectangular swimming pool element for garden/summer use."""

    def __init__(
            self,
            anchor: tuple[float, float],
            width: float,
            height: float,
            pool_color: str = '#00BFFF',
            border_color: str = '#B0C4DE',
            show_lanes: bool = False,
            show_steps: bool = True,
            label: str | None = None
    ):
        """
        Initialize a RectPool instance.

        :param anchor:
            coordinates of center point
        :param width:
            pool width in meters
        :param height:
            pool height (length) in meters
        :param pool_color:
            color for pool water (default bright blue)
        :param border_color:
            color for pool edge/border
        :param show_lanes:
            whether to show lane lines
        :param show_steps:
            whether to show entry steps
        :param label:
            optional label for the pool
        """
        super().__init__(label=label)
        self.anchor = anchor
        self.width = width
        self.height = height
        self.pool_color = pool_color
        self.border_color = border_color
        self.show_lanes = show_lanes
        self.show_steps = show_steps

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the rectangular swimming pool."""
        x = self.anchor[0] - self.width / 2
        y = self.anchor[1] - self.height / 2

        # Draw pool border/edge
        from matplotlib.patches import Rectangle
        border = Rectangle(
            (x - 0.15, y - 0.15),
            self.width + 0.3,
            self.height + 0.3,
            facecolor=self.border_color,
            edgecolor='black',
            linewidth=2,
            alpha=0.9
        )
        ax.add_patch(border)

        # Draw water surface
        water = Rectangle(
            (x, y),
            self.width,
            self.height,
            facecolor=self.pool_color,
            edgecolor='#4682B4',
            linewidth=1,
            alpha=0.7
        )
        ax.add_patch(water)

        # Draw lane lines if enabled
        if self.show_lanes:
            self._draw_lane_lines(ax, x, y)

        # Draw steps if enabled
        if self.show_steps:
            self._draw_steps(ax, x, y)

        # Draw water shimmer effect
        self._draw_water_shimmer(ax, x, y)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_lane_lines(self, ax: matplotlib.axes.Axes, x: float, y: float) -> None:
        """Draw lane divider lines."""
        # Draw 2-3 vertical lane lines
        num_lanes = max(2, int(self.width / 2.5))
        for i in range(1, num_lanes):
            lane_x = x + (i / num_lanes) * self.width
            # Dashed line
            line_segments = 10
            for j in range(line_segments):
                if j % 2 == 0:  # Draw every other segment
                    seg_y_start = y + (j / line_segments) * self.height
                    seg_y_end = y + ((j + 0.8) / line_segments) * self.height
                    ax.plot([lane_x, lane_x], [seg_y_start, seg_y_end],
                           color='white', linewidth=1, alpha=0.6)

    def _draw_steps(self, ax: matplotlib.axes.Axes, x: float, y: float) -> None:
        """Draw entry steps at one corner."""
        # Draw steps in bottom-left corner
        step_width = min(0.8, self.width * 0.2)
        step_height = min(1.0, self.height * 0.25)
        
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
            ax.add_patch(step_rect)

    def _draw_water_shimmer(self, ax: matplotlib.axes.Axes, x: float, y: float) -> None:
        """Draw subtle water shimmer effects."""
        random.seed(46)
        # Draw a few random light reflections
        num_shimmers = int(self.width * self.height * 0.5)
        for _ in range(num_shimmers):
            shimmer_x = x + random.uniform(0, self.width)
            shimmer_y = y + random.uniform(0, self.height)
            size = random.uniform(0.05, 0.15)
            shimmer = Circle(
                (shimmer_x, shimmer_y),
                size,
                facecolor='white',
                edgecolor='none',
                alpha=random.uniform(0.1, 0.3)
            )
            ax.add_patch(shimmer)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for pool."""
        label_text = self._build_label_text()
        if label_text:
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Pool',
                position=(self.anchor[0], self.anchor[1] + self.height / 2 + 0.4),
                rotation=0
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Pool',
                position=(self.anchor[0], self.anchor[1] + self.height / 2 + 0.4),
                rotation=0
            )

    def _build_label_text(self) -> str:
        """Build label text with dimensions."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.width}m×{self.height}m")
        return " ".join(parts)


class OvalPool(Element):
    """Oval swimming pool element for garden/summer use."""

    def __init__(
            self,
            anchor: tuple[float, float],
            width: float,
            height: float,
            pool_color: str = '#00BFFF',
            border_color: str = '#B0C4DE',
            show_steps: bool = True,
            label: str | None = None
    ):
        """
        Initialize an OvalPool instance.

        :param anchor:
            coordinates of center point
        :param width:
            pool width in meters
        :param height:
            pool height (length) in meters
        :param pool_color:
            color for pool water (default bright blue)
        :param border_color:
            color for pool edge/border
        :param show_steps:
            whether to show entry steps
        :param label:
            optional label for the pool
        """
        super().__init__(label=label)
        self.anchor = anchor
        self.width = width
        self.height = height
        self.pool_color = pool_color
        self.border_color = border_color
        self.show_steps = show_steps

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the oval swimming pool."""
        from matplotlib.patches import Ellipse

        # Draw pool border/edge (slightly larger ellipse)
        border = Ellipse(
            self.anchor,
            self.width + 0.3,
            self.height + 0.3,
            facecolor=self.border_color,
            edgecolor='black',
            linewidth=2,
            alpha=0.9
        )
        ax.add_patch(border)

        # Draw water surface
        water = Ellipse(
            self.anchor,
            self.width,
            self.height,
            facecolor=self.pool_color,
            edgecolor='#4682B4',
            linewidth=1,
            alpha=0.7
        )
        ax.add_patch(water)

        # Draw steps if enabled
        if self.show_steps:
            self._draw_steps(ax)

        # Draw water shimmer effect
        self._draw_water_shimmer(ax)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_steps(self, ax: matplotlib.axes.Axes) -> None:
        """Draw semi-circular entry steps."""
        # Steps on one side (bottom)
        step_center_x = self.anchor[0]
        step_center_y = self.anchor[1] - self.height / 2 + 0.5
        
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
            ax.add_patch(step)

    def _draw_water_shimmer(self, ax: matplotlib.axes.Axes) -> None:
        """Draw subtle water shimmer effects."""
        random.seed(47)
        # Draw random light reflections within ellipse bounds
        num_shimmers = int(self.width * self.height * 0.5)
        for _ in range(num_shimmers):
            # Generate points within ellipse
            angle = random.uniform(0, 2 * math.pi)
            r = random.uniform(0, 1) ** 0.5  # Square root for uniform distribution
            shimmer_x = self.anchor[0] + r * (self.width / 2) * 0.9 * math.cos(angle)
            shimmer_y = self.anchor[1] + r * (self.height / 2) * 0.9 * math.sin(angle)
            size = random.uniform(0.05, 0.15)
            shimmer = Circle(
                (shimmer_x, shimmer_y),
                size,
                facecolor='white',
                edgecolor='none',
                alpha=random.uniform(0.1, 0.3)
            )
            ax.add_patch(shimmer)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for pool."""
        label_text = self._build_label_text()
        if label_text:
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Pool',
                position=(self.anchor[0], self.anchor[1] + self.height / 2 + 0.4),
                rotation=0
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Pool',
                position=(self.anchor[0], self.anchor[1] + self.height / 2 + 0.4),
                rotation=0
            )

    def _build_label_text(self) -> str:
        """Build label text with dimensions."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.width}m×{self.height}m")
        return " ".join(parts)
