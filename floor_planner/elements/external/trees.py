"""

"""
import math

from matplotlib.axes import Axes
from matplotlib.patches import Rectangle
from matplotlib.lines import Line2D

from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.elements.landscaping import CircularVegetation2D
from floor_planner.utils import rotate_point, render_label_and_id
from floor_planner.elements.vertical_levels import VertInfoLvl01



class LeafyTree(ExternalModelElement, VertInfoLvl01):
    """
    
    """
    def __init__(
        self,
        anchor_point: tuple[float, float],
        diameter: float = 4.0,
        height: float = 10.0,
        trunk_diameter: float = 0.3,
        color: str = '#228B22',
        trunk_color: str = '#654321',
        label: str | None = None,
        species: str | None = None,
        bloom_season_start: str | None = None,
        bloom_season_end: str | None = None,
        bloom_color: str | None = None,
        textures: str | dict[str, str] | None = None,
        texture_scale: float | None = None,
        **kwargs
    ):
        super().__init__(
            anchor_point=anchor_point,
            color=color,
            label=label,
            textures=textures,
            texture_scale=texture_scale,
            **kwargs
            )
        self.veg2d = CircularVegetation2D(
            anchor_point=anchor_point,
            diameter=diameter,
            height=height,
            color=color, 
            trunk_diameter=trunk_diameter,
            trunk_color=trunk_color,
            vegetation_type='Tree',
            label=label,
            species=species,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color,
            z_order=self.get_zorder()
        )
        # base on height, change the normalisation so its scaled
        # based on orientation angle, rotate it.
        #self.secondary_normalization = self.door3d.getSecondaryNormalization()
        #self.secondary_anchor_offset = self.door3d.getSecondaryAnchorOffset()

    _registry_key = 'leafy_tree'
    _requires_external_model = True

    def _default_width(self) -> float:
        """Default front-to-back depth: 0.49 m."""
        return 2

    def _default_length(self) -> float:
        """Default arm-to-arm length: 1.37 m."""
        return 2

    def _default_height(self) -> float:
        """Default floor-to-top-of-back height: 0.49 m."""
        return 6

    def draw(self, ax: Axes) -> None:
        """
        Draw 2D top-down representation of the tree.

        """
        self.veg2d.draw(ax)
        