"""
Vegetation elements: trees, shrubs, hedges.

Author: Krzysztof Bartczak
"""

import math

import matplotlib.axes
from matplotlib.patches import Circle, Rectangle

from ...utils import rotate_point, render_label_and_id, _render_text
from ..element import Element, RectangularElement, SurfaceElement, CircularElement
from ...options import get_show_species, get_show_bloom
from ..vertical_levels import VertInfoLvl01, VertInfoLvl00
from .species_db import resolve_species_params


class VegetationElement:
    """Mixin class for vegetation elements with common attributes.
    
    This is a mixin class, not a base class - it provides vegetation-specific
    properties and methods to be used alongside geometric base classes.
    """
    
    def __init__(
            self,
            height: float,
            species: str | None = None,
            bloom_season_start: str | None = None,
            bloom_season_end: str | None = None,
            bloom_color: str | None = None
    ):
        """Initialize common vegetation attributes."""
        self.height = height
        self.species = species
        self.bloom_season_start = bloom_season_start
        self.bloom_season_end = bloom_season_end
        self.bloom_color = bloom_color
    
    def _build_label_text(self) -> str:
        """Build label text with species, height, and bloom info."""
        parts = []
        if self.label:
            parts.append(self.label)
        if self.species:
            parts.append(f"({self.species})")
        if self.height:
            parts.append(f"h={self.height}m")
        if self.bloom_season_start and self.bloom_season_end:
            parts.append(f"bloom: {self.bloom_season_start}-{self.bloom_season_end}")
        return " ".join(parts) if parts else ""
    
    def _render_species_and_bloom(self, ax: matplotlib.axes.Axes, element_type: str, vertical_offset: float, trunk_diameter: float) -> None:
        """Render species and bloom info in center of circular element."""
        has_species = self.species is not None
        has_bloom = self.bloom_season_start or self.bloom_season_end
        show_species = get_show_species(element_type)
        show_bloom = get_show_bloom(element_type)
        
        if not has_species and not has_bloom:
            return
        anchor_point = self.anchor_point
        if hasattr(x_axis_size := getattr(self, 'x_axis_size', None), '__float__'):
            anchor_point = (anchor_point[0] + x_axis_size / 2, anchor_point[1] ) 
        if hasattr(z_axis_size := getattr(self, 'z_axis_size', None), '__float__'):
            anchor_point = (anchor_point[0], anchor_point[1] + z_axis_size / 2)
        if hasattr(length := getattr(self, 'length', None), '__float__'):
            anchor_point = (anchor_point[0] + length / 2, anchor_point[1] )
        if hasattr(thickness := getattr(self, 'thickness', None), '__float__'):
            anchor_point = (anchor_point[0], anchor_point[1] + thickness / 2) 

        fontsize = 10
        
        # Render species at center (always horizontal) if enabled and present
        if show_species and has_species:
            species_y = anchor_point[1] + vertical_offset + trunk_diameter if (show_bloom and has_bloom) else anchor_point[1] + trunk_diameter
            _render_text(
                ax=ax,
                position=(anchor_point[0], species_y),
                text=self.species,
                rotation=0,
                color='black',
                fontsize=fontsize,
                centered=True
            )
        
        # Render bloom info if present and enabled
        if show_bloom and has_bloom:
            bloom_text = ''
            if self.bloom_season_start and self.bloom_season_end:
                bloom_text = f"{self.bloom_season_start}-{self.bloom_season_end}"
            elif self.bloom_season_start:
                bloom_text = self.bloom_season_start
            
            if bloom_text:
                # Position depends on whether species is shown
                bloom_y = anchor_point[1] - vertical_offset + trunk_diameter if (show_species and has_species) else anchor_point[1] + trunk_diameter
                _render_text(
                    ax=ax,
                    position=(anchor_point[0], bloom_y),
                    text=bloom_text,
                    rotation=0,
                    color='darkred',
                    fontsize=fontsize-2,
                    centered=True
                )


class CircularVegetation2D(VegetationElement):
    """Drawing class for circular vegetation elements (Tree, Shrub) in 2D top-down view."""
    def __init__(
            self,
            anchor_point: tuple[float, float],
            diameter: float,
            height: float,
            z_order: float,
            color: str ,
            trunk_diameter: float,
            trunk_color: str,
            vegetation_type: str,
            label: str | None = None,
            species: str | None = None,
            bloom_season_start: str | None = None,
            bloom_season_end: str | None = None,
            bloom_color: str | None = None
            
    ):
        self.anchor_point = anchor_point
        self.diameter = diameter
        self.color = color
        self.label = label
        self.trunk_diameter = trunk_diameter
        self.trunk_color = trunk_color
        self.vegetation_type = vegetation_type
        self.z_order = z_order

        super().__init__(
            height=height,
            species=species,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color
        )
    
    
    def _draw_main_circle(self, ax: matplotlib.axes.Axes, alpha: float = 0.8) -> None:
        """Draw the main circular shape (canopy/bush)."""
        circle = Circle(
            self.anchor_point,
            self.diameter / 2,
            facecolor=self.color,
            edgecolor='darkgreen',
            linewidth=1.5,
            alpha=alpha
        )
        circle.set_zorder(self.z_order)
        ax.add_patch(circle)
    
     
    def _render_label_and_id(self, ax: matplotlib.axes.Axes, element_type: str) -> None:
        from ...utils import render_text_as_label_and_id
        label_text = self._build_label_text()
        position = (self.anchor_point[0], self.anchor_point[1] - self.diameter / 4)
        render_text_as_label_and_id(
            ax=ax,
            element=self,
            text=label_text,
            element_type=element_type,
            position=position,
            rotation=0,
            centered=True
        )
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the shrub or (tree with trunk and canopy)"""
 

        # Draw canopy using base class method
        self._draw_main_circle(ax, alpha=0.7)

        if self.vegetation_type == 'Tree':
            # Draw bloom overlay if enabled and in season
            show_bloom = get_show_bloom(self.vegetation_type)
            if show_bloom and self.bloom_color and self.bloom_season_start and self.bloom_season_end:
                bloom_halo = Circle(
                    self.anchor_point,
                    self.diameter / 2,
                    facecolor='none',
                    edgecolor=self.bloom_color,
                    linewidth=3.0,
                    linestyle='--',
                    alpha=0.6
                )
                bloom_halo.set_zorder(self.z_order)
                ax.add_patch(bloom_halo)
        if self.vegetation_type == 'Shrub':
            # Draw main shrub circle using base class method
            self._draw_main_circle(ax, alpha=0.8)

            # Draw bloom overlay if enabled and in season
            show_bloom = get_show_bloom('Shrub')
            if show_bloom and self.bloom_color and self.bloom_season_start and self.bloom_season_end:
                # Add multiple small circles to represent flowers
                for i in range(5):
                    angle = i * (2 * math.pi / 5)
                    offset_x = (self.diameter / 3) * math.cos(angle)
                    offset_y = (self.diameter / 3) * math.sin(angle)
                    bloom = Circle(
                        (self.anchor_point[0] + offset_x, self.anchor_point[1] + offset_y),
                        self.diameter / 8,
                        facecolor=self.bloom_color,
                        edgecolor=self.bloom_color,
                        linewidth=0.5,
                        alpha=0.7
                    )
                    bloom.set_zorder(self.z_order)
                    ax.add_patch(bloom)
        if self.trunk_diameter > 0:
             # Draw trunk (small circle)
            trunk = Circle(
                self.anchor_point,
                self.trunk_diameter / 2,
                facecolor=self.trunk_color,
                edgecolor='#654321',
            linewidth=1.0
            )
            trunk.set_zorder(self.z_order)
            ax.add_patch(trunk)

        # Render species and bloom text in center
        show_species = get_show_species(self.vegetation_type)
        has_bloom = self.bloom_season_start or self.bloom_season_end
        if show_species or (show_bloom and has_bloom):
            self._render_species_and_bloom(ax, self.vegetation_type, 0.2, self.trunk_diameter)

        # Render label and ID
        self._render_label_and_id(ax, self.vegetation_type)


class CircularVegetation(VertInfoLvl01, CircularElement):
    """Base class for circular vegetation elements (Tree, Shrub)."""
    
    def __init__(
            self,
            anchor_point: tuple[float, float],
            vegetation_type: str,
            diameter: float,
            height: float,
            color: str = 'darkgreen',
            trunk_diameter: float = 0.0,
            trunk_color: str = '#654321',
            label: str | None = None,
            species: str | None = None,
            bloom_season_start: str | None = None,
            bloom_season_end: str | None = None,
            bloom_color: str | None = None
    ):
        """Initialize circular vegetation element."""
        super().__init__(
            anchor_point=anchor_point,
            diameter=diameter,
            height=height,
            color=color,
            label=label
        )
        self.veg2d = CircularVegetation2D(
            anchor_point=anchor_point,
            diameter=diameter,
            height=height,
            color=color, 
            trunk_diameter=trunk_diameter,
            trunk_color=trunk_color,
            vegetation_type=vegetation_type,
            label=label,
            species=species,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color,
            z_order=self.get_zorder()
        )



class Tree(CircularVegetation):
    """Tree with circular canopy and trunk."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            diameter: float | None = None,
            height: float | None = None,
            trunk_diameter: float | None = None,
            color: str | None = None,
            trunk_color: str | None = None,
            label: str | None = None,
            species: str | None = None,
            bloom_season_start: str | None = None,
            bloom_season_end: str | None = None,
            bloom_color: str | None = None
    ):
        """
        Initialize a Tree instance.

        When *species* is given, any parameter left as ``None`` is looked up
        in the species database and filled in automatically.  Explicit values
        always override the species defaults.

        :param anchor_point:
            coordinates of anchor point (center of tree canopy)
        :param diameter:
            canopy diameter in meters (species default or 4.0)
        :param height:
            tree height in meters (species default or 10.0)
        :param trunk_diameter:
            trunk diameter in meters (species default or 0.3)
        :param color:
            color for the canopy (species default or '#228B22')
        :param trunk_color:
            trunk fill color (species default or '#654321')
        :param label:
            optional label for the tree
        :param species:
            optional species name; drives automatic parameter defaults
        :param bloom_season_start:
            optional bloom start date in dd.mm format
        :param bloom_season_end:
            optional bloom end date in dd.mm format
        :param bloom_color:
            optional bloom color (used during bloom season)
        """
        resolved = resolve_species_params(
            species,
            diameter=diameter,
            height=height,
            trunk_diameter=trunk_diameter,
            color=color,
            trunk_color=trunk_color,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color,
        )
        diameter           = resolved['diameter']           if resolved['diameter']           is not None else 4.0
        height             = resolved['height']             if resolved['height']             is not None else 10.0
        trunk_diameter     = resolved['trunk_diameter']     if resolved['trunk_diameter']     is not None else 0.3
        color              = resolved['color']              if resolved['color']              is not None else '#228B22'
        trunk_color        = resolved['trunk_color']        if resolved['trunk_color']        is not None else '#654321'
        bloom_season_start = resolved['bloom_season_start']
        bloom_season_end   = resolved['bloom_season_end']
        bloom_color        = resolved['bloom_color']

        super().__init__(
            anchor_point=anchor_point,
            diameter=diameter,
            height=height,
            vegetation_type='Tree',
            trunk_diameter=trunk_diameter,
            trunk_color=trunk_color,
            color=color,
            label=label,
            species=species,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color
        )
        self.trunk_diameter = trunk_diameter

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the tree with trunk and canopy."""
        self.veg2d.draw(ax)   
    

class Shrub(CircularVegetation):
    """Shrub with circular canopy."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            diameter: float | None = None,
            height: float | None = None,
            color: str | None = None,
            label: str | None = None,
            species: str | None = None,
            bloom_season_start: str | None = None,
            bloom_season_end: str | None = None,
            bloom_color: str | None = None
    ):
        """
        Initialize a Shrub instance.

        When *species* is given, any parameter left as ``None`` is looked up
        in the species database and filled in automatically.  Explicit values
        always override the species defaults.

        :param anchor_point:
            coordinates of anchor point (center of shrub)
        :param diameter:
            shrub diameter in meters (species default or 1.0)
        :param height:
            shrub height in meters (species default or 1.5)
        :param color:
            color for the shrub (species default or '#90EE90')
        :param label:
            optional label for the shrub
        :param species:
            optional species name; drives automatic parameter defaults
        :param bloom_season_start:
            optional bloom start date in dd.mm format
        :param bloom_season_end:
            optional bloom end date in dd.mm format
        :param bloom_color:
            optional bloom color (used during bloom season)
        """
        resolved = resolve_species_params(
            species,
            diameter=diameter,
            height=height,
            color=color,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color,
        )
        diameter           = resolved['diameter'] if resolved['diameter'] is not None else 1.0
        height             = resolved['height']   if resolved['height']   is not None else 1.5
        color              = resolved['color']     if resolved['color']    is not None else '#90EE90'
        bloom_season_start = resolved['bloom_season_start']
        bloom_season_end   = resolved['bloom_season_end']
        bloom_color        = resolved['bloom_color']

        super().__init__(
            anchor_point=anchor_point,
            diameter=diameter,
            height=height,
            vegetation_type='Shrub',
            color=color,
            label=label,
            species=species,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color
        )

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the shrub as a circular bush."""
        self.veg2d.draw(ax)


class Hedge(VertInfoLvl01, VegetationElement, RectangularElement):
    """Linear hedge element."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            length: float | None = None,
            thickness: float | None = None,
            height: float | None = None,
            color: str | None = None,
            orientation_angle: float = 0,
            label: str | None = None,
            species: str | None = None,
            bloom_season_start: str | None = None,
            bloom_season_end: str | None = None,
            bloom_color: str | None = None
    ):
        """
        Initialize a Hedge instance.

        When *species* is given, any parameter left as ``None`` is looked up
        in the species database and filled in automatically.  Explicit values
        always override the species defaults.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param length:
            hedge length in meters
        :param thickness:
            hedge thickness (perpendicular depth) in meters
        :param height:
            hedge height in meters (species default or class default)
        :param color:
            color for the hedge (species default or '#556B2F')
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the hedge
        :param species:
            optional species name; drives automatic parameter defaults
        :param bloom_season_start:
            optional bloom start date in dd.mm format
        :param bloom_season_end:
            optional bloom end date in dd.mm format
        :param bloom_color:
            optional bloom color (used during bloom season)
        """
        resolved = resolve_species_params(
            species,
            height=height,
            color=color,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color,
        )
        height             = resolved['height']
        color              = resolved['color']              if resolved['color']    is not None else '#556B2F'
        bloom_season_start = resolved['bloom_season_start']
        bloom_season_end   = resolved['bloom_season_end']
        bloom_color        = resolved['bloom_color']

        RectangularElement.__init__(
            self,
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=thickness,
            color=color,
            label=label
        )
        VegetationElement.__init__(
            self,
            height=height,
            species=species,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color
        )

    def _default_height(self) -> float:
        """Return default height for hedge."""
        return 1.8
    
    
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the hedge as a thick rectangle."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw main hedge rectangle
        hedge = Rectangle(
            self.anchor_point,
            self.length,
            self.thickness,
            angle=self.orientation_angle,
            facecolor=draw_color,
            edgecolor='darkgreen',
            linewidth=1.5,
            alpha=0.7
        )
        hedge.set_zorder(self.get_zorder())
        ax.add_patch(hedge)

        # Draw bloom overlay if enabled and in season
        show_bloom = get_show_bloom('Hedge')
        if show_bloom and self.bloom_color and self.bloom_season_start and self.bloom_season_end:
            bloom_overlay = Rectangle(
                self.anchor_point,
                self.length,
                self.thickness,
                angle=self.orientation_angle,
                facecolor='none',
                edgecolor=self.bloom_color,
                linewidth=3.0,
                linestyle='--',
                alpha=0.6
            )
            bloom_overlay.set_zorder(self.get_zorder())
            ax.add_patch(bloom_overlay)

        # Render species and bloom info in center
        show_species = get_show_species('Hedge')
        has_bloom = self.bloom_season_start or self.bloom_season_end
        if show_species or (show_bloom and has_bloom):
            self._render_species_and_bloom(ax, 'Hedge', 0.15, 0)

        # Render label and ID
        from ...utils import render_text_as_label_and_id
        label_text = self._build_label_text()
        center_x = self.length / 2
        center_y = self.thickness / 2
        center = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        position = (center[0], center[1] + self.thickness / 2 + 0.2)
        render_text_as_label_and_id(
            ax=ax,
            element=self,
            text=label_text,
            element_type='Hedge',
            position=position,
            rotation=self.orientation_angle
        )

  
class Lawn(VertInfoLvl00, SurfaceElement):
    """Lawn/grass area element."""

    def __init__(
            self,
            anchor_point: tuple[float, float] | None = None,
            size: tuple[float, float] | None = None,
            color: str = '#7CFC00',
            orientation_angle: float = 0,
            label: str | None = None
    ):
        """
        Initialize a Lawn instance.

        :param anchor_point:
            coordinates of anchor point (bottom-left corner)
        :param size:
            (x_size, z_size) tuple: lawn size along X and Z axes in meters
        :param color:
            color for the lawn (default: bright green)
        :param orientation_angle:
            rotation angle in degrees
        :param label:
            optional label for the lawn
        """
        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            size=size,
            color=color,
            label=label
        )

    def _default_height(self) -> float:
        """Return default height for lawn."""
        return 0.0

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the lawn as a filled rectangle with grass texture."""
        draw_color = self.get_draw_color()
        if draw_color is None:
            return

        # Draw main lawn rectangle
        lawn = Rectangle(
            self.anchor_point,
            self.x_axis_size,
            self.z_axis_size,
            angle=self.orientation_angle,
            facecolor=draw_color,
            edgecolor='#228B22',
            linewidth=1.0,
            alpha=0.6
        )
        lawn.set_zorder(self.get_zorder())
        ax.add_patch(lawn)

        # Add subtle grass texture pattern
        self._draw_grass_texture(ax)

        # Render label and ID
        from ...utils import render_text_as_label_and_id
        label_text = self._build_label_text()
        center_x = self.x_axis_size / 2
        center_y = self.z_axis_size / 2
        center = rotate_point(
            self.anchor_point,
            center_x,
            center_y,
            math.radians(self.orientation_angle)
        )
        position = (center[0], center[1])
        render_text_as_label_and_id(
            ax=ax,
            element=self,
            text=label_text,
            element_type='Lawn',
            position=position,
            rotation=self.orientation_angle
        )

    def _draw_grass_texture(self, ax: matplotlib.axes.Axes) -> None:
        """Draw subtle texture lines to indicate grass."""
        import random
        random.seed(42)  # Consistent pattern
        
        # Draw some random short lines to simulate grass blades
        num_lines = int(self.x_axis_size * self.z_axis_size * 2)  # Density based on area
        num_lines = min(num_lines, 50)  # Cap at 50 to avoid clutter
        
        for _ in range(num_lines):
            # Random position within lawn
            local_x = random.uniform(0, self.x_axis_size)
            local_y = random.uniform(0, self.z_axis_size)
            
            # Small random line
            line_length = 0.08
            line_angle = random.uniform(0, 2 * math.pi)
            
            # Start and end points of grass blade (in local coordinates)
            x1_local = local_x
            y1_local = local_y
            x2_local = local_x + line_length * math.cos(line_angle)
            y2_local = local_y + line_length * math.sin(line_angle)
            
            # Rotate points according to lawn orientation
            angle_rad = math.radians(self.orientation_angle)
            p1 = rotate_point(self.anchor_point, x1_local, y1_local, angle_rad)
            p2 = rotate_point(self.anchor_point, x2_local, y2_local, angle_rad)
            
            ax.plot(
                [p1[0], p2[0]],
                [p1[1], p2[1]],
                color='#228B22',
                linewidth=0.3,
                alpha=0.4
            )

    def _build_label_text(self) -> str:
        """Build label text with dimensions."""
        parts = []
        if self.label:
            parts.append(self.label)
        parts.append(f"{self.x_axis_size}m×{self.z_axis_size}m")
        return " ".join(parts)
