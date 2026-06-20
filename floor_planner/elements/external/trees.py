"""

"""
import random

from matplotlib.axes import Axes

from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.elements.landscaping import CircularVegetation2D
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
        texture_scale: float | None = None,
        **kwargs
    ):
        super().__init__(
            anchor_point=anchor_point,
            color=color,
            label=label,
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

        
        scale_h = diameter / self._default_width()
        scale_v = height / self._default_height()
        
        self.secondary_normalization = {
                'scale':       [scale_h, scale_v, scale_h],
                'rotation':    [0, random.uniform(0, 360), 0], # Random rotation around vertical axis for natural variation
                'translation': [0, 0, 0],
            }


    _registry_key = 'leafy_tree'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 4.4

    def _default_length(self) -> float:
        return 4.4

    def _default_height(self) -> float:
        return 7.4

    def draw(self, ax: Axes) -> None:
        """
        Draw 2D top-down representation of the tree.

        """
        self.veg2d.draw(ax)
        
class LeafyShrub1(ExternalModelElement, VertInfoLvl01):
    """
    
    """
    def __init__(
        self,
        anchor_point: tuple[float, float],
        diameter: float = 2.0,
        height: float = 2.0,
        color: str = '#228B22',
        label: str | None = None,
        species: str | None = None,
        bloom_season_start: str | None = None,
        bloom_season_end: str | None = None,
        bloom_color: str | None = None,
        texture_scale: float | None = None,
        **kwargs
    ):
        super().__init__(
            anchor_point=anchor_point,
            color=color,
            label=label,
            texture_scale=texture_scale,
            **kwargs
            )
        self.veg2d = CircularVegetation2D(
            anchor_point=anchor_point,
            diameter=diameter,
            height=height,
            color=color, 
            trunk_diameter=0.01,
            trunk_color='red',
            vegetation_type='Shrub',
            label=label,
            species=species,
            bloom_season_start=bloom_season_start,
            bloom_season_end=bloom_season_end,
            bloom_color=bloom_color,
            z_order=self.get_zorder()
        )

        
        scale_h = diameter / self._default_width()
        scale_v = height / self._default_height()
        #for test
        #scale_h = 1
        #scale_v = 1

        self.secondary_normalization = {
                'scale':       [scale_h, scale_v, scale_h],
                'rotation':    [0, random.uniform(0, 360), 0], # Random rotation around vertical axis for natural variation
                'translation': [0, 0, 0],
            }


    _registry_key = 'leafy_shrub_1'
    _requires_external_model = True

    def _default_width(self) -> float:
        return 2

    def _default_length(self) -> float:
        return 2

    def _default_height(self) -> float:
        return 2

    def draw(self, ax: Axes) -> None:
        """
        Draw 2D top-down representation of the shrub.

        """
        self.veg2d.draw(ax)
        