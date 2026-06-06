"""
Hardscape elements: fences, paths, walls.

Author: Krzysztof Bartczak
"""

import matplotlib.axes
from matplotlib.patches import Rectangle, FancyBboxPatch
import matplotlib.patches as mpatches

from ...utils import rotate_point, render_label_and_id
from ..element import RectangularElement, SurfaceElement
from ..vertical_levels import VertInfoLvl01, VertInfoLvl00, VertInfoLvlGround


class Fence(VertInfoLvl01, RectangularElement):
    """Fence element with style variations."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            length: float | None = None,
            style: str = 'solid',
            height: float = 1.8,
            thickness: float = 0.1,
            color: str = '#8B4513',
            orientation_angle: float = 0,
            label: str | None = None
    ):
        """
        Initialize a Fence instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param length:
            fence length in meters
        :param style:
            fence style: 'solid', 'picket', 'chain-link', 'rail'
        :param height:
            fence height in meters (for label/info)
        :param thickness:
            visual thickness in meters (for rendering)
        :param color:
            color for the fence
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the fence
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=thickness,
            color=color,
            label=label
        )
        self.style = style
        self.height = height

    def _default_height(self) -> float:
        """Return default height for fence."""
        return 1.8

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the fence with style-specific patterns."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw main fence rectangle
        fence = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor=draw_color,
            edgecolor='black',
            linewidth=1.0,
            alpha=0.8
        )
        fence.set_zorder(self.get_zorder())
        ax.add_patch(fence)

        # Add style-specific pattern
        if self.style == 'picket':
            self._draw_picket_pattern(ax)
        elif self.style == 'chain-link':
            self._draw_chainlink_pattern(ax)
        elif self.style == 'rail':
            self._draw_rail_pattern(ax)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_picket_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw vertical pickets along the fence."""
        import math
        num_pickets = int(self.length / 0.15)  # picket every 15cm
        for i in range(num_pickets):
            offset = i * (self.length / num_pickets)
            picket_start = rotate_point(
                self.anchor_point,
                offset,
                0,
                math.radians(self.orientation_angle)
            )
            picket_end = rotate_point(
                self.anchor_point,
                offset,
                self.thickness,
                math.radians(self.orientation_angle)
            )
            ax.plot(
                [picket_start[0], picket_end[0]],
                [picket_start[1], picket_end[1]],
                color='black',
                linewidth=0.5,
                alpha=0.6
            )

    def _draw_chainlink_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw diagonal cross-hatch for chain-link appearance."""
        import math
        # Draw diagonal lines
        num_lines = int(self.length / 0.2)
        for i in range(num_lines):
            offset = i * (self.length / num_lines)
            # Forward diagonal
            p1 = rotate_point(self.anchor_point, offset, 0, math.radians(self.orientation_angle))
            p2 = rotate_point(self.anchor_point, offset + 0.1, self.thickness, math.radians(self.orientation_angle))
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='gray', linewidth=0.3, alpha=0.5)
            # Backward diagonal
            p3 = rotate_point(self.anchor_point, offset, self.thickness, math.radians(self.orientation_angle))
            p4 = rotate_point(self.anchor_point, offset + 0.1, 0, math.radians(self.orientation_angle))
            ax.plot([p3[0], p4[0]], [p3[1], p4[1]], color='gray', linewidth=0.3, alpha=0.5)

    def _draw_rail_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw horizontal rails for rail fence."""
        import math
        # Draw 2-3 horizontal rails
        rails = [0.25, 0.5, 0.75]
        for rail_pos in rails:
            y_offset = self.thickness * rail_pos
            start = rotate_point(self.anchor_point, 0, y_offset, math.radians(self.orientation_angle))
            end = rotate_point(self.anchor_point, self.length, y_offset, math.radians(self.orientation_angle))
            ax.plot([start[0], end[0]], [start[1], end[1]], color='black', linewidth=1.0, alpha=0.7)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for fence."""
        import math
        label_text = self._build_label_text()
        if label_text:
            center_x = self.length / 2
            center_y = self.thickness / 2
            center = rotate_point(
                self.anchor_point,
                center_x,
                center_y,
                math.radians(self.orientation_angle)
            )
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Fence',
                position=(center[0], center[1] + self.thickness / 2 + 0.2),
                rotation=self.orientation_angle
            )
            self.label = original_label
        elif self.label:
            center_x = self.length / 2
            center_y = self.thickness / 2
            center = rotate_point(
                self.anchor_point,
                center_x,
                center_y,
                math.radians(self.orientation_angle)
            )
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Fence',
                position=(center[0], center[1] + self.thickness / 2 + 0.2),
                rotation=self.orientation_angle
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


class GardenPath(VertInfoLvl00, SurfaceElement):
    """Garden path with material patterns."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            x_axis_size: float | None = None,
            z_axis_size: float | None = None,
            material: str = 'gravel',
            color: str = '#D3D3D3',
            orientation_angle: float = 0,
            label: str | None = None
    ):
        """
        Initialize a GardenPath instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param x_axis_size:
            path size along X axis in meters
        :param z_axis_size:
            path size along Z axis in meters
        :param material:
            path material: 'gravel', 'stone', 'paving', 'wood', 'mulch'
        :param color:
            color for the path
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the path
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            x_axis_size=x_axis_size,
            z_axis_size=z_axis_size,
            color=color,
            label=label
        )
        self.material = material

    def _default_height(self) -> float:
        """Return default height for garden path."""
        return 0.0

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the path with material-specific pattern."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw main path rectangle
        path = Rectangle(
            self.anchor_point,
            self.x_axis_size,
            self.z_axis_size,
            angle=self.orientation_angle,
            facecolor=draw_color,
            edgecolor='#A0A0A0',
            linewidth=1.0,
            alpha=0.7
        )
        path.set_zorder(self.get_zorder())
        ax.add_patch(path)

        # Add material-specific pattern
        if self.material == 'gravel':
            self._draw_gravel_pattern(ax)
        elif self.material == 'stone':
            self._draw_stone_pattern(ax)
        elif self.material == 'paving':
            self._draw_paving_pattern(ax)
        elif self.material == 'wood':
            self._draw_wood_pattern(ax)
        elif self.material == 'mulch':
            self._draw_mulch_pattern(ax)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_gravel_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw small dots to represent gravel."""
        import math
        import random
        random.seed(42)  # Consistent pattern
        num_dots = int(self.x_axis_size * self.z_axis_size * 50)  # density
        for _ in range(num_dots):
            x_offset = random.uniform(0, self.x_axis_size)
            y_offset = random.uniform(0, self.z_axis_size)
            point = rotate_point(
                self.anchor_point,
                x_offset,
                y_offset,
                math.radians(self.orientation_angle)
            )
            ax.plot(point[0], point[1], 'o', color='gray', markersize=0.5, alpha=0.4)

    def _draw_stone_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw irregular stone patterns."""
        import math
        # Draw irregular polygons to simulate flagstones
        num_stones_x = max(2, int(self.x_axis_size / 0.5))
        num_stones_y = max(2, int(self.z_axis_size / 0.5))
        step_x = self.x_axis_size / num_stones_x
        step_y = self.z_axis_size / num_stones_y
        
        for i in range(num_stones_x):
            for j in range(num_stones_y):
                x = i * step_x + step_x * 0.1
                y = j * step_y + step_y * 0.1
                w = step_x * 0.8
                h = step_y * 0.8
                # Draw stone outline
                corners = [
                    rotate_point(self.anchor_point, x, y, math.radians(self.orientation_angle)),
                    rotate_point(self.anchor_point, x + w, y, math.radians(self.orientation_angle)),
                    rotate_point(self.anchor_point, x + w, y + h, math.radians(self.orientation_angle)),
                    rotate_point(self.anchor_point, x, y + h, math.radians(self.orientation_angle))
                ]
                xs = [c[0] for c in corners]
                ys = [c[1] for c in corners]
                ax.plot(xs + [xs[0]], ys + [ys[0]], color='#808080', linewidth=0.5, alpha=0.6)

    def _draw_paving_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw grid pattern for paving stones."""
        import math
        # Draw regular grid
        num_lines_x = max(2, int(self.x_axis_size / 0.3))
        num_lines_y = max(2, int(self.z_axis_size / 0.3))
        
        for i in range(1, num_lines_x):
            offset = i * (self.z_axis_size/ num_lines_x)
            start = rotate_point(self.anchor_point, offset, 0, math.radians(self.orientation_angle))
            end = rotate_point(self.anchor_point, offset, self.x_axis_size, math.radians(self.orientation_angle))
            ax.plot([start[0], end[0]], [start[1], end[1]], color='#606060', linewidth=0.5, alpha=0.5)
        
        for j in range(1, num_lines_y):
            offset = j * (self.z_axis_size / num_lines_y)
            start = rotate_point(self.anchor_point, 0, offset, math.radians(self.orientation_angle))
            end = rotate_point(self.anchor_point, self.x_axis_size, offset, math.radians(self.orientation_angle))
            ax.plot([start[0], end[0]], [start[1], end[1]], color='#606060', linewidth=0.5, alpha=0.5)

    def _draw_wood_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw parallel lines for wood planks."""
        import math
        # Draw planks perpendicular to path direction
        num_planks = max(3, int(self.x_axis_size / 0.2))
        for i in range(1, num_planks):
            offset = i * (self.x_axis_size / num_planks)
            start = rotate_point(self.anchor_point, offset, 0, math.radians(self.orientation_angle))
            end = rotate_point(self.anchor_point, offset, self.z_axis_size, math.radians(self.orientation_angle))
            ax.plot([start[0], end[0]], [start[1], end[1]], color='#654321', linewidth=0.8, alpha=0.6)

    def _draw_mulch_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw organic texture for mulch."""
        import math
        import random
        random.seed(43)
        # Draw short random lines for organic texture
        num_lines = int(self.x_axis_size * self.z_axis_size * 20)
        for _ in range(num_lines):
            x1 = random.uniform(0, self.x_axis_size)
            y1 = random.uniform(0, self.z_axis_size)
            angle = random.uniform(0, 360)
            length = random.uniform(0.05, 0.15)
            x2 = x1 + length * math.cos(math.radians(angle))
            y2 = y1 + length * math.sin(math.radians(angle))
            # Clamp to path bounds
            x2 = max(0, min(self.x_axis_size, x2))
            y2 = max(0, min(self.z_axis_size, y2))
            
            p1 = rotate_point(self.anchor_point, x1, y1, math.radians(self.orientation_angle))
            p2 = rotate_point(self.anchor_point, x2, y2, math.radians(self.orientation_angle))
            ax.plot([p1[0], p2[0]], [p1[1], p2[1]], color='#654321', linewidth=0.3, alpha=0.3)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for path."""
        import math
        label_text = self._build_label_text()
        if label_text:
            center_x = self.x_axis_size / 2
            center_y = self.z_axis_size / 2
            center = rotate_point(
                self.anchor_point,
                center_x,
                center_y,
                math.radians(self.orientation_angle)
            )
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='GardenPath',
                position=(center[0], center[1] + self.z_axis_size / 2 + 0.2),
                rotation=self.orientation_angle
            )
            self.label = original_label
        elif self.label:
            center_x = self.length / 2
            center_y = self.width / 2
            center = rotate_point(
                self.anchor_point,
                center_x,
                center_y,
                math.radians(self.orientation_angle)
            )
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='GardenPath',
                position=(center[0], center[1] + self.width / 2 + 0.2),
                rotation=self.orientation_angle
            )

    def _build_label_text(self) -> str:
        """Build label text with material info."""
        parts = []
        if self.label:
            parts.append(self.label)
        if self.material:
            parts.append(f"({self.material})")
        return " ".join(parts) if parts else ""


class RetainingWall(VertInfoLvl01, RectangularElement):
    """Retaining wall element."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            length: float | None = None,
            height: float | None = None,
            thickness: float = 0.3,
            color: str = '#696969',
            orientation_angle: float = 0,
            label: str | None = None
    ):
        """
        Initialize a RetainingWall instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param length:
            wall length in meters
        :param height:
            wall height in meters (for label/info)
        :param thickness:
            visual thickness in meters (for rendering)
        :param color:
            color for the wall
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the wall
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=thickness,
            color=color,
            label=label
        )
        self.height = height

    def _default_height(self) -> float:
        """Return default height for retaining wall."""
        return 1.0

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the retaining wall with stone texture."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw main wall rectangle
        wall = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor=draw_color,
            edgecolor='black',
            linewidth=1.5,
            alpha=0.9
        )
        wall.set_zorder(self.get_zorder())
        ax.add_patch(wall)

        # Add stone pattern
        self._draw_stone_pattern(ax)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_stone_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw horizontal lines to simulate stacked stones."""
        import math
        # Draw horizontal lines representing stone courses
        num_courses = max(2, int(self.height / 0.3))  # stone course every 30cm
        for i in range(1, num_courses):
            y_offset = i * (self.thickness / num_courses)
            start = rotate_point(self.anchor_point, 0, y_offset, math.radians(self.orientation_angle))
            end = rotate_point(self.anchor_point, self.length, y_offset, math.radians(self.orientation_angle))
            ax.plot([start[0], end[0]], [start[1], end[1]], color='black', linewidth=0.5, alpha=0.4)
        
        # Add some vertical mortar lines
        num_stones = max(3, int(self.length / 0.5))
        for i in range(1, num_stones):
            x_offset = i * (self.length / num_stones)
            start = rotate_point(self.anchor_point, x_offset, 0, math.radians(self.orientation_angle))
            end = rotate_point(self.anchor_point, x_offset, self.thickness, math.radians(self.orientation_angle))
            ax.plot([start[0], end[0]], [start[1], end[1]], color='black', linewidth=0.5, alpha=0.3)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for retaining wall."""
        import math
        label_text = self._build_label_text()
        if label_text:
            center_x = self.length / 2
            center_y = self.thickness / 2
            center = rotate_point(
                self.anchor_point,
                center_x,
                center_y,
                math.radians(self.orientation_angle)
            )
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='RetainingWall',
                position=(center[0], center[1] + self.thickness / 2 + 0.2),
                rotation=self.orientation_angle
            )
            self.label = original_label
        elif self.label:
            center_x = self.length / 2
            center_y = self.thickness / 2
            center = rotate_point(
                self.anchor_point,
                center_x,
                center_y,
                math.radians(self.orientation_angle)
            )
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='RetainingWall',
                position=(center[0], center[1] + self.thickness / 2 + 0.2),
                rotation=self.orientation_angle
            )

    def _build_label_text(self) -> str:
        """Build label text with height info."""
        parts = []
        if self.label:
            parts.append(self.label)
        if self.height:
            parts.append(f"h={self.height}m")
        return " ".join(parts) if parts else ""

class Ground(VertInfoLvlGround, SurfaceElement):
    """Deck/patio platform element."""
    def __init__(
            self,
            anchor_point: tuple[float, float],
            x_axis_size: float,
            z_axis_size: float,
            color: str = '#D2691E',
            orientation_angle: float = 0,
            label: str | None = None
    ):
        """
        Initialize a Ground instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param x_axis_size:
            ground size along X axis in meters
        :param z_axis_size:
            ground size along Z axis in meters
        :param color:
            color for the ground
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the ground
        """
        # Set default texture_scale for Ground to 0.5 (0.5m x 0.5m tiles)
        texture_scale = 0.5

        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            x_axis_size=x_axis_size,
            z_axis_size=z_axis_size,
            color=color,
            label=label,
            texture_scale=texture_scale 
        )

    def _default_height(self) -> float:
        """Return default height for deck."""
        return 0.1

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """The ground is drawn as a thin line. Use color hidden to suppress."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        groundArea = Rectangle(
            self.anchor_point,
            width=self.x_axis_size,
            height=self.z_axis_size,
            angle=self.orientation_angle,
            facecolor='red',
            fill=False,
            edgecolor=draw_color,
            linewidth=0.5,
            alpha=0.7
        )
        groundArea.set_zorder(self.get_zorder())
        ax.add_patch(groundArea)

        self._render_label_and_id(ax)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for Ground."""
        return  # Skip label rendering for Ground
