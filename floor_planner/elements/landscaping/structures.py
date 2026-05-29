"""
Garden structure elements: pergolas, raised beds, gazebos, decks, garden houses.

Author: Krzysztof Bartczak
"""

import matplotlib.axes
from matplotlib.patches import Rectangle, Polygon, Circle, FancyBboxPatch
import matplotlib.patches as mpatches
import math

from ...utils import rotate_point, render_label_and_id
from ..element import RectangularElement, SurfaceElement, CircularElement, Element
from ..vertical_levels import VertInfoLvl01, VertInfoLvl01


class Pergola(SurfaceElement):
    """Pergola structure with posts and beams."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            width: float,
            post_size: float = 0.2,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None
    ):
        """
        Initialize a Pergola instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param length:
            pergola length in meters
        :param width:
            pergola width in meters
        :param post_size:
            size of support posts in meters
        :param orientation_angle:
            rotation angle in degrees
        :param color:
            color for the structure
        :param label:
            optional label for the pergola
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            width=width,
            color=color,
            label=label
        )
        self.post_size = post_size

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the pergola with posts and beams."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw perimeter beams (outline)
        self._draw_perimeter(ax, draw_color)

        # Draw corner posts
        self._draw_posts(ax, draw_color)

        # Draw cross beams
        self._draw_cross_beams(ax, draw_color)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_perimeter(self, ax: matplotlib.axes.Axes, color: str) -> None:
        """Draw perimeter beams."""
        # Draw outline rectangle
        perimeter = Rectangle(
            self.anchor_point,
            self.length,
            self.width,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=color,
            linewidth=2.5,
            alpha=0.8
        )
        perimeter.set_zorder(self.get_zorder())
        ax.add_patch(perimeter)

    def _draw_posts(self, ax: matplotlib.axes.Axes, color: str) -> None:
        """Draw corner posts."""
        corners = [
            (0, 0),
            (self.length, 0),
            (self.length, self.width),
            (0, self.width)
        ]
        
        for corner_x, corner_y in corners:
            # Calculate rotated position
            corner_pos = rotate_point(
                self.anchor_point,
                corner_x,
                corner_y,
                math.radians(self.orientation_angle)
            )
            # Draw post as filled square
            post_anchor = (
                corner_pos[0] - self.post_size / 2,
                corner_pos[1] - self.post_size / 2
            )
            post = Rectangle(
                post_anchor,
                self.post_size,
                self.post_size,
                angle=self.orientation_angle,
                facecolor=color,
                edgecolor='black',
                linewidth=1.0,
                alpha=0.9
            )
            post.set_zorder(self.get_zorder())
            ax.add_patch(post)

    def _draw_cross_beams(self, ax: matplotlib.axes.Axes, color: str) -> None:
        """Draw cross beams for structural detail."""
        # Draw beams along length (parallel to width)
        num_beams = max(2, int(self.width / 1.0))  # beam every ~1m
        for i in range(1, num_beams):
            y_offset = i * (self.width / num_beams)
            start = rotate_point(
                self.anchor_point,
                0,
                y_offset,
                math.radians(self.orientation_angle)
            )
            end = rotate_point(
                self.anchor_point,
                self.length,
                y_offset,
                math.radians(self.orientation_angle)
            )
            ax.plot([start[0], end[0]], [start[1], end[1]],
                   color=color, linewidth=1.5, alpha=0.6, linestyle='--')

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for pergola."""
        center_x = self.length / 2
        center_y = self.width / 2
        center = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        label_text = self._build_label_text()
        if label_text:
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Pergola',
                position=(center[0], center[1]),
                rotation=self.orientation_angle
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Pergola',
                position=(center[0], center[1]),
                rotation=self.orientation_angle
            )

    def _build_label_text(self) -> str:
        """Build label text with dimensions."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.length}×{self.width}m")
        return " ".join(parts) if parts else ""


class RaisedBed(SurfaceElement):
    """Raised garden bed element."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            width: float,
            height: float = 0.4,
            border_thickness: float = 0.15,
            fill_color: str = '#654321',
            border_color: str = '#8B4513',
            orientation_angle: float = 0,
            label: str | None = None
    ):
        """
        Initialize a RaisedBed instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param length:
            bed length in meters
        :param width:
            bed width in meters
        :param height:
            bed height in meters (for label/info)
        :param border_thickness:
            visual thickness of border in meters
        :param fill_color:
            color for soil fill
        :param border_color:
            color for border/frame
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the raised bed
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            width=width,
            color=fill_color,  # Use fill_color as the main color for SurfaceElement
            label=label
        )
        self.height = height
        self.border_thickness = border_thickness
        self.fill_color = fill_color
        self.border_color = border_color

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the raised bed with border and fill."""
        # Draw border (outer rectangle)
        border = Rectangle(
            self.anchor_point,
            self.length,
            self.width,
            angle=self.orientation_angle,
            facecolor=self.border_color,
            edgecolor='black',
            linewidth=1.5,
            alpha=0.9
        )
        border.set_zorder(self.get_zorder())
        ax.add_patch(border)

        # Draw soil fill (inner rectangle)
        fill_anchor = rotate_point(
            self.anchor_point,
            self.border_thickness,
            self.border_thickness,
            math.radians(self.orientation_angle)
        )
        fill = Rectangle(
            fill_anchor,
            self.length - 2 * self.border_thickness,
            self.width - 2 * self.border_thickness,
            angle=self.orientation_angle,
            facecolor=self.fill_color,
            edgecolor='none',
            alpha=0.7
        )
        fill.set_zorder(self.get_zorder())
        ax.add_patch(fill)

        # Render label and ID
        self._render_label_and_id(ax)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for raised bed."""
        center_x = self.length / 2
        center_y = self.width / 2
        center = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        label_text = self._build_label_text()
        if label_text:
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='RaisedBed',
                position=(center[0], center[1]),
                rotation=self.orientation_angle
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='RaisedBed',
                position=(center[0], center[1]),
                rotation=self.orientation_angle
            )

    def _build_label_text(self) -> str:
        """Build label text with dimensions and height."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.length}×{self.width}m")
        if self.height:
            parts.append(f"h={self.height}m")
        return " ".join(parts) if parts else ""


class Gazebo(VertInfoLvl01, CircularElement):
    """Gazebo structure with octagonal shape and roof."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            diameter: float,
            color: str = '#DEB887',
            roof_color: str = '#8B4513',
            label: str | None = None
    ):
        """
        Initialize a Gazebo instance.

        :param anchor_point:
            coordinates of center point
        :param diameter:
            gazebo diameter in meters
        :param color:
            color for the structure
        :param roof_color:
            color for the roof
        :param label:
            optional label for the gazebo
        """
        super().__init__(
            anchor_point=anchor_point,
            diameter=diameter,
            color=color,
            label=label
        )
        self.roof_color = roof_color

    def _default_height(self) -> float:
        """Return default height for gazebo."""
        return 2.5

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the gazebo with octagonal shape and roof."""
        # Draw octagonal floor/platform
        self._draw_octagon(ax, self.diameter / 2, self.color)

        # Draw roof (slightly larger octagon)
        self._draw_octagon(ax, self.diameter / 2 * 1.15, self.roof_color, is_roof=True)

        # Draw corner posts
        self._draw_posts(ax)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_octagon(self, ax: matplotlib.axes.Axes, radius: float, color: str, is_roof: bool = False) -> None:
        """Draw octagonal shape."""
        num_sides = 8
        points = []
        for i in range(num_sides):
            angle = (i / num_sides) * 2 * math.pi
            x = self.anchor_point[0] + radius * math.cos(angle)
            y = self.anchor_point[1] + radius * math.sin(angle)
            points.append([x, y])
        
        alpha = 0.6 if is_roof else 0.8
        linestyle = '--' if is_roof else '-'
        octagon = Polygon(
            points,
            facecolor=color,
            edgecolor='black',
            linewidth=1.5 if not is_roof else 1.0,
            linestyle=linestyle,
            alpha=alpha
        )
        octagon.set_zorder(self.get_zorder())
        ax.add_patch(octagon)

    def _draw_posts(self, ax: matplotlib.axes.Axes) -> None:
        """Draw corner posts at octagon vertices."""
        num_posts = 8
        radius = self.diameter / 2
        post_size = 0.15
        
        for i in range(num_posts):
            angle = (i / num_posts) * 2 * math.pi
            x = self.anchor_point[0] + radius * math.cos(angle)
            y = self.anchor_point[1] + radius * math.sin(angle)
            
            post = Circle(
                (x, y),
                post_size,
                facecolor=self.color,
                edgecolor='black',
                linewidth=0.8,
                alpha=0.9
            )
            post.set_zorder(self.get_zorder())
            ax.add_patch(post)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for gazebo."""
        label_text = self._build_label_text()
        if label_text:
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Gazebo',
                position=(self.anchor_point[0], self.anchor_point[1] + self.diameter / 2 + 0.3),
                rotation=0
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Gazebo',
                position=(self.anchor_point[0], self.anchor_point[1] + self.diameter / 2 + 0.3),
                rotation=0
            )

    def _build_label_text(self) -> str:
        """Build label text with diameter."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"Ø{self.diameter}m")
        return " ".join(parts) if parts else ""


class Deck(VertInfoLvl01, SurfaceElement):
    """Deck/patio platform element."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            width: float,
            color: str = '#D2691E',
            orientation_angle: float = 0,
            label: str | None = None
    ):
        """
        Initialize a Deck instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param length:
            deck length in meters
        :param width:
            deck width in meters
        :param color:
            color for the deck
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the deck
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            width=width,
            color=color,
            label=label
        )

    def _default_height(self) -> float:
        """Return default height for deck."""
        return 0.3

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the deck with wood plank pattern."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw main deck rectangle
        deck = Rectangle(
            self.anchor_point,
            self.length,
            self.width,
            angle=self.orientation_angle,
            facecolor=draw_color,
            edgecolor='black',
            linewidth=1.5,
            alpha=0.7
        )
        deck.set_zorder(self.get_zorder())
        ax.add_patch(deck)

        # Draw wood plank lines (perpendicular to length)
        self._draw_plank_pattern(ax)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_plank_pattern(self, ax: matplotlib.axes.Axes) -> None:
        """Draw parallel lines representing wood planks."""
        num_planks = max(5, int(self.width / 0.15))  # plank every ~15cm
        
        for i in range(1, num_planks):
            y_offset = i * (self.width / num_planks)
            start = rotate_point(
                self.anchor_point,
                0,
                y_offset,
                math.radians(self.orientation_angle)
            )
            end = rotate_point(
                self.anchor_point,
                self.length,
                y_offset,
                math.radians(self.orientation_angle)
            )
            ax.plot([start[0], end[0]], [start[1], end[1]],
                   color='#8B4513', linewidth=0.5, alpha=0.5)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for deck."""
        center_x = self.length / 2
        center_y = self.width / 2
        center = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        label_text = self._build_label_text()
        if label_text:
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Deck',
                position=(center[0], center[1]),
                rotation=self.orientation_angle
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='Deck',
                position=(center[0], center[1]),
                rotation=self.orientation_angle
            )

    def _build_label_text(self) -> str:
        """Build label text with dimensions."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.length}×{self.width}m")
        return " ".join(parts) if parts else ""


class GardenHouse(SurfaceElement):
    """Garden house/shed for equipment storage."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            width: float,
            height: float = 2.5,
            color: str = '#DEB887',
            roof_color: str = '#8B4513',
            orientation_angle: float = 0,
            label: str | None = None
    ):
        """
        Initialize a GardenHouse instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param length:
            house length in meters
        :param width:
            house width in meters (door is on this side)
        :param height:
            house height in meters (for label/info)
        :param color:
            color for the walls
        :param roof_color:
            color for the roof
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the garden house
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            width=width,
            color=color,
            label=label
        )
        self.height = height
        self.color = color
        self.roof_color = roof_color

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the garden house with walls, door, and 4-sided roof."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw main structure (walls)
        walls = Rectangle(
            self.anchor_point,
            self.length,
            self.width,
            angle=self.orientation_angle,
            facecolor=draw_color,
            edgecolor='black',
            linewidth=2.0,
            alpha=0.8
        )
        walls.set_zorder(self.get_zorder())
        ax.add_patch(walls)

        # Draw 4-sided roof (extends beyond walls)
        self._draw_roof(ax)

        # Draw door on the width side (front)
        self._draw_door(ax)

        # Render label and ID
        self._render_label_and_id(ax)

    def _draw_roof(self, ax: matplotlib.axes.Axes) -> None:
        """Draw 4-sided roof with overhang."""
        overhang = 0.3  # roof extends 30cm beyond walls
        
        # Roof as polygon (4 sides with overhang)
        roof_corners = [
            (-overhang, -overhang),
            (self.length + overhang, -overhang),
            (self.length + overhang, self.width + overhang),
            (-overhang, self.width + overhang)
        ]
        
        roof_points = []
        for corner_x, corner_y in roof_corners:
            point = rotate_point(
                self.anchor_point,
                corner_x,
                corner_y,
                math.radians(self.orientation_angle)
            )
            roof_points.append(point)
        
        roof = Polygon(
            roof_points,
            facecolor=self.roof_color,
            edgecolor='black',
            linewidth=1.5,
            linestyle='--',
            alpha=0.6
        )
        roof.set_zorder(self.get_zorder())
        ax.add_patch(roof)
        
        # Draw ridge line (center line showing roof peak)
        ridge_start = rotate_point(
            self.anchor_point,
            -overhang,
            self.width / 2,
            math.radians(self.orientation_angle)
        )
        ridge_end = rotate_point(
            self.anchor_point,
            self.length + overhang,
            self.width / 2,
            math.radians(self.orientation_angle)
        )
        ax.plot([ridge_start[0], ridge_end[0]], [ridge_start[1], ridge_end[1]],
               color='black', linewidth=1.0, alpha=0.7)

    def _draw_door(self, ax: matplotlib.axes.Axes) -> None:
        """Draw door on the width side (front of house) as a line."""
        door_width = min(0.9, self.length * 0.4)  # door is 90cm or 40% of length
        
        # Door centered on the front (width side)
        door_x_start = (self.length - door_width) / 2
        door_x_end = door_x_start + door_width
        door_y = 0  # at the front edge
        
        # Calculate door line endpoints
        door_start = rotate_point(
            self.anchor_point,
            door_x_start,
            door_y,
            math.radians(self.orientation_angle)
        )
        door_end = rotate_point(
            self.anchor_point,
            door_x_end,
            door_y,
            math.radians(self.orientation_angle)
        )
        
        # Draw door as a line (opening in the wall)
        ax.plot(
            [door_start[0], door_end[0]],
            [door_start[1], door_end[1]],
            color='#3D2817',
            linewidth=7.5,
            alpha=1.0
        )

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for garden house."""
        center_x = self.length / 2
        center_y = self.width / 2
        center = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        
        label_text = self._build_label_text()
        if label_text:
            original_label = self.label
            self.label = label_text
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='GardenHouse',
                position=(center[0], center[1] + self.width / 2 + 0.5),
                rotation=self.orientation_angle
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='GardenHouse',
                position=(center[0], center[1] + self.width / 2 + 0.5),
                rotation=self.orientation_angle
            )

    def _build_label_text(self) -> str:
        """Build label text with dimensions and height."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.length}×{self.width}m")
        if self.height:
            parts.append(f"h={self.height}m")
        return " ".join(parts) if parts else ""
