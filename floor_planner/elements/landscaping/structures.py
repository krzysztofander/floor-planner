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
from ..vertical_levels import VertInfoLvl01, VertInfoLvl01, VertInfoRoof
from ...geometry_3d import (GableRoofGeometry3D, HippedRoofGeometry3D,
                             SingleSlopeRoofGeometry3D, HippedRoofOctantGeometry3D)


class Pergola(SurfaceElement):
    """Pergola structure with posts and beams."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            post_size: float = 0.2,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None
    ):
        """
        Initialize a Pergola instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param size:
            (x_size, z_size) tuple: pergola size along X and Z axes in meters
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
            size=size,
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
            self.x_axis_size,
            self.z_axis_size,
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
            (self.x_axis_size, 0),
            (self.x_axis_size, self.z_axis_size),
            (0, self.z_axis_size)
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
        num_beams = max(2, int(self.z_axis_size / 1.0))  # beam every ~1m
        for i in range(1, num_beams):
            y_offset = i * (self.z_axis_size / num_beams)
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
        center_x = self.x_axis_size / 2
        center_y = self.z_axis_size / 2
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
        parts.append(f"{self.x_axis_size}×{self.z_axis_size}m")
        return " ".join(parts) if parts else ""


class RaisedBed(SurfaceElement):
    """Raised garden bed element."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
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
        :param size:
            (x_size, z_size) tuple: bed size along X and Z axes in meters
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
            size=size,
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
            width = self.x_axis_size,
            height = self.z_axis_size,
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
            width = self.x_axis_size - 2 * self.border_thickness,
            height = self.z_axis_size - 2 * self.border_thickness,
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
        center_x = self.x_axis_size / 2
        center_y = self.z_axis_size / 2
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
        parts.append(f"{self.x_axis_size}×{self.z_axis_size}m")
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

class GenericSurface(VertInfoLvl01, SurfaceElement):
    """generic surface e.g. concrete element."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            color: str = "#6D645E",
            orientation_angle: float = 0,
            label: str | None = None,
            v_anchor: float | None = None,
            height: float | None = None,
    ):
        """
        Initialize a GenericSurface instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param size:
            (x_size, z_size) tuple: surface size along X and Z axes in meters
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
            size=size,
            color=color,
            label=label,
            texture_scale=1.0 # Default texture scale 
        )
        self.v_anchor = v_anchor if v_anchor is not None else self._default_v_anchor()
        self.height = height if height is not None else self._default_height()

    def _default_height(self) -> float:
        """Return default height for surface element."""
        return 0.30

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the deck with wood plank pattern."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw main surface rectangle
        surf = Rectangle(
            self.anchor_point,
            width=self.x_axis_size,
            height=self.z_axis_size,
            angle=self.orientation_angle,
            facecolor=draw_color,
            edgecolor='black',
            linewidth=1.5,
            alpha=0.1
        )
        surf.set_zorder(self.get_zorder())
        ax.add_patch(surf)

        # Render label and ID
        self._render_label_and_id(ax)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for deck."""
        center_x = self.x_axis_size / 2
        center_y = self.z_axis_size / 2
        center = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
    
        render_label_and_id(
                ax=ax,
                element=self,
                element_type='GenericSurface',
                position=(center[0], center[1]),
                rotation=self.orientation_angle,
                centered=True
            )

class Deck(VertInfoLvl01, SurfaceElement):
    """Deck/patio platform element."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            color: str = '#D2691E',
            orientation_angle: float = 0,
            label: str | None = None,
            v_anchor: float | None = None,
            height: float | None = None,
    ):
        """
        Initialize a Deck instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param size:
            (x_size, z_size) tuple: deck size along X and Z axes in meters
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
            size=size,
            color=color,
            label=label,
            texture_scale=0.6  # Default texture scale for deck (0.2m x 0.2m tiles)
        )
        self.v_anchor = v_anchor if v_anchor is not None else self._default_v_anchor()
        self.height = height if height is not None else self._default_height()

    def _default_height(self) -> float:
        """Return default height for deck."""
        return 0.015

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the deck with wood plank pattern."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw main deck rectangle
        deck = Rectangle(
            self.anchor_point,
            width=self.x_axis_size,
            height=self.z_axis_size,
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
        num_planks = max(5, int(self.x_axis_size / 0.15))  # plank every ~15cm
        
        for i in range(1, num_planks):
            x_offset = i * (self.x_axis_size / num_planks)
            start = rotate_point(
                self.anchor_point,
                x_offset,
                0,
                math.radians(self.orientation_angle)
            )
            end = rotate_point(
                self.anchor_point,
                x_offset,
                self.z_axis_size,
                math.radians(self.orientation_angle)
            )
            ax.plot([start[0], end[0]], [start[1], end[1]],
                   color='#8B4513', linewidth=0.5, alpha=0.5)

    def _render_label_and_id(self, ax: matplotlib.axes.Axes) -> None:
        """Render label and ID for deck."""
        center_x = self.x_axis_size / 2
        center_y = self.z_axis_size / 2
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
        parts.append(f"{self.x_axis_size}m×{self.z_axis_size}m")
        return " ".join(parts) if parts else ""


class GardenHouse(SurfaceElement):
    """Garden house/shed for equipment storage."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
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
        :param size:
            (x_size, z_size) tuple: house size along X and Z axes in meters
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
            size=size,
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
            width = self.x_axis_size,
            height = self.z_axis_size,
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
            (self.x_axis_size + overhang, -overhang),
            (self.x_axis_size + overhang, self.z_axis_size + overhang),
            (-overhang, self.z_axis_size + overhang)
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
            self.z_axis_size / 2,
            math.radians(self.orientation_angle)
        )
        ridge_end = rotate_point(
            self.anchor_point,
            self.x_axis_size + overhang,
            self.z_axis_size / 2,
            math.radians(self.orientation_angle)
        )
        ax.plot([ridge_start[0], ridge_end[0]], [ridge_start[1], ridge_end[1]],
               color='black', linewidth=1.0, alpha=0.7)

    def _draw_door(self, ax: matplotlib.axes.Axes) -> None:
        """Draw door on the width side (front of house) as a line."""
        door_width = min(0.9, self.x_axis_size * 0.4)  # door is 90cm or 40% of length
        
        # Door centered on the front (width side)
        door_x_start = (self.x_axis_size - door_width) / 2
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
        center_x = self.x_axis_size / 2
        center_y = self.z_axis_size / 2
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
                position=(center[0], center[1] + self.z_axis_size / 2 + 0.5),
                rotation=self.orientation_angle
            )
            self.label = original_label
        elif self.label:
            render_label_and_id(
                ax=ax,
                element=self,
                element_type='GardenHouse',
                position=(center[0], center[1] + self.z_axis_size / 2 + 0.5),
                rotation=self.orientation_angle
            )

    def _build_label_text(self) -> str:
        """Build label text with dimensions and height."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.x_axis_size}×{self.z_axis_size}m")
        if self.height:
            parts.append(f"h={self.height}m")
        return " ".join(parts) if parts else ""


# ──────────────────────────────────────────────────────────────────────────────
# Roof elements
# ──────────────────────────────────────────────────────────────────────────────

class _RoofBase(Element):
    """
    Shared base for roof elements.

    In 2D draws a thin, unfilled dashed rectangle showing the roof footprint.
    In 3D generates a proper roof shape via the geometry mixin.

    YAML parameters (common to GableRoof and HippedRoof):
        anchor_point      – bottom-left corner of the roof footprint
        size              – (x_size, z_size) tuple in metres:
                            x_size = horizontal (left/right in plan view),
                            z_size = vertical   (up/down in plan view)
        height            – ridge height above v_anchor  (default from VertInfoRoof)
        v_anchor          – 3D Y of roof base, i.e. top of supporting walls
                            (default 2.70 m from VertInfoRoof)
        orientation_angle – rotation in degrees  (default 0)
        color             – outline colour in 2D  (default '#8B4513')
        label             – optional label string
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            color=color,
            label=label,
            v_anchor=v_anchor,
            height=height if height is not None else self._default_height(),
            texture_scale=0.3,
            **kwargs,
        )
        self.x_axis_size = size[0]
        self.z_axis_size = size[1]
        self.orientation_angle = orientation_angle
        self.texture_scale = 0.3  # Default texture scale for roof (0.2m x 0.2m tiles)

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw roof footprint as an unfilled dashed rectangle."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        outline = Rectangle(
            self.anchor_point,
            width=self.x_axis_size,
            height=self.z_axis_size,
            angle=self.orientation_angle,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.5,
            linestyle='--',
        )
        outline.set_zorder(self.get_zorder())
        ax.add_patch(outline)

        if self.label:
            center = rotate_point(
                self.anchor_point,
                self.x_axis_size / 2,
                self.z_axis_size / 2,
                math.radians(self.orientation_angle),
            )
            render_label_and_id(
                ax=ax,
                element=self,
                element_type=self.__class__.__name__,
                position=center,
                rotation=self.orientation_angle,
            )


class GableRoof(VertInfoRoof, GableRoofGeometry3D, _RoofBase):
    """
    Gable roof element.

    Two sloping planes meeting at a ridge; triangular gable walls at each end.
    The ridge runs along the *longer* plan dimension (or along X when square).

    In 2D: unfilled dashed rectangle showing the footprint.
    In 3D: proper gable roof geometry with no bottom face.

    YAML type: ``gable_roof``

    Extra YAML parameters beyond _RoofBase:
        extension_a  – extend the "a" slope plane outward in plan (metres, default 0)
        extension_b  – extend the "b" slope plane outward in plan (metres, default 0)

        When the ridge runs along X (x_axis_size >= z_axis_size):
          extension_a extends the front slope (plan-z = 0 side)
          extension_b extends the back  slope (plan-z = z side)
        When the ridge runs along Z:
          extension_a extends the left  slope (plan-x = 0 side)
          extension_b extends the right slope (plan-x = x side)

        The extension value is the 2D horizontal distance; the slope plane simply
        grows outward — its ridge line stays in place.
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None,
            extension_a: float = 0,
            extension_b: float = 0,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            size=size,
            height=height,
            v_anchor=v_anchor,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs,
        )
        self.extension_a = extension_a or 0
        self.extension_b = extension_b or 0

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw roof footprint + extension indicators."""
        super().draw(ax)

        # Draw thin dashed lines showing the extended eave edges
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        x = self.x_axis_size
        z = self.z_axis_size
        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point(self.anchor_point, lx, lz, angle_rad)

        if x >= z:
            # Ridge along X; extensions in the z direction
            if self.extension_a > 0:
                p0 = w(0, -self.extension_a)
                p1 = w(x, -self.extension_a)
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())
            if self.extension_b > 0:
                p0 = w(0, z + self.extension_b)
                p1 = w(x, z + self.extension_b)
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())
        else:
            # Ridge along Z; extensions in the x direction
            if self.extension_a > 0:
                p0 = w(-self.extension_a, 0)
                p1 = w(-self.extension_a, z)
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())
            if self.extension_b > 0:
                p0 = w(x + self.extension_b, 0)
                p1 = w(x + self.extension_b, z)
                ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                        color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())


class HippedRoof(VertInfoRoof, HippedRoofGeometry3D, _RoofBase):
    """
    Hipped roof element.

    All four sides slope toward the centre.
    Square plan → pyramid.  Rectangular plan → elongated hipped roof with
    a short ridge and triangular hip faces at the short ends.

    In 2D: unfilled dashed rectangle showing the footprint.
    In 3D: proper hipped/pyramid geometry with no bottom face.

    YAML type: ``hipped_roof``

    Parameters: see _RoofBase.
    """


class SingleSlopeRoof(VertInfoRoof, SingleSlopeRoofGeometry3D, _RoofBase):
    """
    Single-slope (mono-pitch / lean-to) roof element.

    One rectangular sloping plane:
      - the low eave runs along plan-z = 0 at v_anchor
      - the high eave runs along plan-z = z_axis_size at v_anchor + height

    In 2D: unfilled dashed rectangle showing the footprint plus a dotted line
           on the low eave if ``extension`` > 0.
    In 3D: single sloping quad, no gable end caps.

    YAML type: ``single_slope_roof``

    Extra YAML parameters beyond _RoofBase:
        extension   – extend the low-eave edge outward in the plan-z direction
                      (horizontal distance in metres, default 0)
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None,
            extension: float = 0,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            size=size,
            height=height,
            v_anchor=v_anchor,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs,
        )
        self.extension = extension or 0

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw footprint dashed rectangle + optional extension dotted line."""
        super().draw(ax)

        if self.extension <= 0:
            return
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point(self.anchor_point, lx, lz, angle_rad)

        # Dotted line showing extended low eave
        p0 = w(0,               -self.extension)
        p1 = w(self.x_axis_size, -self.extension)
        ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                color=draw_color, linewidth=0.8, linestyle=':', zorder=self.get_zorder())


class _HippedRoofOctantBase(VertInfoRoof, HippedRoofOctantGeometry3D, _RoofBase):
    """
    Base for 1/8th pyramid octant pieces.

    A true octant covers a 45° sector of a square pyramid, formed by cutting
    along all 4 axes of symmetry.  Its eave edge runs from an edge-midpoint
    to the adjacent base corner — a right-angle triangle in plan.

    ``anchor_point`` is the **apex** (ridge tip) — rotation pivot in both plan
    and 3D.  ``size = (x_axis_size, z_axis_size)``:
      - x_axis_size: lateral offset from midpoint to corner (= half the pyramid
                     base width for a square pyramid)
      - z_axis_size: depth from apex to eave (= half the pyramid base depth)

    For a square pyramid of base 2d×2d use size=[d, d].
    Combine 4 right + 4 left at 0°/90°/180°/270° to form a complete pyramid.

    YAML types: ``hipped_roof_octant_left``, ``hipped_roof_octant_right``

    Extra YAML parameter:
        extension  – extend the eave outward from the apex, preserving slope
                     angle (horizontal metres, default 0)
    """

    def __init__(
            self,
            anchor_point: tuple[float, float],
            size: tuple[float, float],
            height: float | None = None,
            v_anchor: float | None = None,
            orientation_angle: float = 0,
            color: str = '#8B4513',
            label: str | None = None,
            extension: float = 0,
            **kwargs,
    ):
        super().__init__(
            anchor_point=anchor_point,
            size=size,
            height=height,
            v_anchor=v_anchor,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            **kwargs,
        )
        self.extension = extension or 0

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the right-triangle footprint with its apex at anchor_point."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        x = self.x_axis_size
        z = self.z_axis_size
        angle_rad = math.radians(self.orientation_angle)

        def w(lx, lz):
            return rotate_point(self.anchor_point, lx, lz, angle_rad)

        tip    = self.anchor_point
        mid    = w(0,                                   z)  # edge midpoint
        corner = w(-x if self._octant_left else x,      z)  # base corner

        triangle = Polygon(
            [tip, mid, corner],
            closed=True,
            facecolor='none',
            edgecolor=draw_color,
            linewidth=1.5,
            linestyle='--',
        )
        triangle.set_zorder(self.get_zorder())
        ax.add_patch(triangle)

        # Dotted line showing the extended eave edge (slope-preserving overhang)
        # Corner moves diagonally (x+ext, z+ext) so adjacent octants stay sealed.
        if self.extension > 0:
            z_ext = z + self.extension
            x_ext = x + self.extension
            p0 = w(0,                                    z_ext)
            p1 = w(-x_ext if self._octant_left else x_ext, z_ext)
            ax.plot([p0[0], p1[0]], [p0[1], p1[1]],
                    color=draw_color, linewidth=0.8, linestyle=':',
                    zorder=self.get_zorder())

        if self.label:
            cx = (tip[0] + mid[0] + corner[0]) / 3
            cz = (tip[1] + mid[1] + corner[1]) / 3
            render_label_and_id(
                ax=ax,
                element=self,
                element_type=self.__class__.__name__,
                position=(cx, cz),
                rotation=self.orientation_angle,
            )


class HippedRoofOctantLeft(_HippedRoofOctantBase):
    """
    Left octant (1/8th pyramid): the base corner lies to the LEFT of the
    pointing direction when orientation_angle=0.

    Combine with HippedRoofOctantRight at the same anchor_point and
    orientations to assemble a pyramid or complex hipped roof.

    YAML type: ``hipped_roof_octant_left``
    """
    _octant_left = True


class HippedRoofOctantRight(_HippedRoofOctantBase):
    """
    Right octant (1/8th pyramid): the base corner lies to the RIGHT of the
    pointing direction when orientation_angle=0.

    YAML type: ``hipped_roof_octant_right``
    """
    _octant_left = False
