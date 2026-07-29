"""
Map element names to their classes.

Author: Nikolay Lysenko
"""


from .foundation.basic import Wall, WallND
from .foundation.windows import Window
from .foundation.surfaces import Floor, Ceiling
from .external import *
from .foundation.door import Door
from .symbols.electricity import ElectricalCable, PowerOutlet
from .element import ElementBase

from .symbols.info import DimensionArrow, TextBox
from .lightning.lighting import CeilingLamp, LEDStrip, Switch, WallLamp
from .symbols.multipurpose import Line, Polygon, Circle
from .foundation.room import Room
from .foundation.group import Group
from .composite import *
from .furniture import *
from .landscaping import * 
from .foundation.roof import (GableRoof, HippedRoof, SingleSlopeRoof,
                               HippedRoofOctantLeft, HippedRoofOctantRight,
                               HippedInternalOctantLeft, HippedInternalOctantRight,
                               GableEndWallLeft, GableEndWallRight,
                               GableEndGlassLeft, GableEndGlassRight)
from .landscaping.structures import Greenhouse
from .landscaping.glass_structures import GlassDoor, GlassPanel, GlassSlope, SolidGlassDoor, AluFrame, Composite_GlassDoor


def create_elements_registry() -> dict[str, type['ElementBase']]:
    """
    Create registry of implemented elements.

    :return:
        mapping from element type to element class
    """
    registry = {
        'ceiling_lamp': CeilingLamp,
        'dimension_arrow': DimensionArrow,
        'door': Door,
        'model_balcony_door': BalconyDoor,
        'model_window_door': WindowDoor,
        'model_solid_door_1': SolidDoor1,
        'model_solid_door_2': SolidDoor2,
        'model_window_door_double': WindowDoorDouble,
        'composite_model_window_door_double': Composite_WindowDoorDouble,
        'model_window_140x120': Window140x120,
        'model_window_single_any': WindowSingleAny,
        'model_window_90x120': Window90x120,
        'model_window_double_160x120': WindowDouble160x120,
        'model_window_double_160x140': WindowDouble160x140,
        'electrical_cable': ElectricalCable,
        'model_wooden_chair': WoodenChair,
        'model_master_bed': MasterBed,
        'model_sofa_model': SofaModel,
        'model_armchair': Armchair,
        'model_chair_20': Chair20,
        'model_chaise_longue_1': ChaiseLongue1,
        'model_desk_1': Desk1,
        'model_sofa_22': Sofa22,
        'model_sofa_23': Sofa23,
        'model_stool_7': Stool7,
        'model_table_01': Table01,
        'model_well': Well,
        'model_leafy_tree': LeafyTree,
        'model_leafy_shrub_1': LeafyShrub1,
        'led_strip': LEDStrip,
        'line': Line,
        'polygon': Polygon,
        'power_outlet': PowerOutlet,
        'group': Group,
        'room': Room,
        'floor': Floor,
        'ceiling': Ceiling,
        'switch': Switch,
        'text_box': TextBox,
        'wall': Wall,
        'wallnd': WallND,
        'wall_lamp': WallLamp,
        'window': Window,
        'circle': Circle,
        'generic_storage': GenericStorage,
        'storage60': Storage60,
        'storage40': Storage40,
        'tabletop': Tabletop,
        'double_bed': DoubleBed,
        'single_bed': SingleBed,
        'dishwasher': Dishwasher,
        'fridge': Fridge,
        'freezer': Freezer,
        'washing_machine': WashingMachine,
        'dryer': Dryer,
        'stovetop': Stovetop,
        'single_sink': SingleSink,
        'double_sink': DoubleSink,
        'shower': Shower,
        'bathtub': Bathtub,
        'basin': Basin,
        'toilet': Toilet,
        'desk': Desk,
        'dining_table': DiningTable,
        'chair': Chair,
        'sofa': Sofa,
        'fish_tank': FishTank,
        'tree': Tree,
        'shrub': Shrub,
        'hedge': Hedge,
        'lawn': Lawn,
        'fence': Fence,
        'garden_path': GardenPath,
        'ground': Ground,
        'retaining_wall': RetainingWall,
        'fountain': Fountain,
        'pond': Pond,
        'rect_pool': RectPool,
        'oval_pool': OvalPool,
        'pergola': Pergola,
        'raised_bed': RaisedBed,
        'gazebo': Gazebo,
        'deck': Deck,
        'surface': GenericSurface,
        'garden_house': GardenHouse,
        'gable_roof': GableRoof,
        'hipped_roof': HippedRoof,
        'single_slope_roof': SingleSlopeRoof,
        'hipped_roof_octant_left': HippedRoofOctantLeft,
        'hipped_roof_octant_right': HippedRoofOctantRight,
        'hipped_internal_octant_left': HippedInternalOctantLeft,
        'hipped_internal_octant_right': HippedInternalOctantRight,
        'gable_end_wall_left': GableEndWallLeft,
        'gable_end_wall_right': GableEndWallRight,
        'gable_end_glass_left': GableEndGlassLeft,
        'gable_end_glass_right': GableEndGlassRight,
        'greenhouse': Greenhouse,
        'glass_door': GlassDoor,
        'glass_panel': GlassPanel,
        'glass_slope': GlassSlope,
        'solid_glass_door': SolidGlassDoor,
        'alu_frame': AluFrame,
        'composite_glass_door': Composite_GlassDoor,
    }
    return registry

def get_element_type_from_instance(element: ElementBase) -> str:
    """
    Get registry key (element type) from an element instance.
    
    This provides the reverse mapping: Class → registry key.
    Essential for texture/material resolution where registry keys
    define folder and file names.
    
    Args:
        element: Element instance
        
    Returns:
        Registry key (e.g., 'double_bed', 'generic_storage')
        
    Raises:
        ValueError: If element class not found in registry
        
    Example:
        bed = DoubleBed(...)
        get_element_type_from_instance(bed)  # Returns: 'double_bed'
    """
    from .external_models import ExternalModelElement
    # For external model elements, return the _registry_key directly.
    # This keeps file-system paths (models/, textures/fallback/) stable
    # regardless of the model_ prefix used in YAML configs.
    if isinstance(element, ExternalModelElement):
        return element.get_registry_key()

    registry = create_elements_registry()
    element_class = type(element)

    # Search registry for matching class
    for key, cls in registry.items():
        if cls is element_class:
            return key

    raise ValueError(f"Element class {element_class.__name__} not found in registry. Please add it to the registry or ensure it's an ExternalModelElement with a defined _registry_key.")
    # Fallback: convert class name to lowercase with underscores
    class_name = element_class.__name__
    import re
    snake_case = re.sub(r'(?<!^)(?=[A-Z])', '_', class_name).lower()
    return snake_case

