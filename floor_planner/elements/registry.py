"""
Map element names to their classes.

Author: Nikolay Lysenko
"""

from .basic import Wall, WallND, Window
from .balcony_door import BalconyDoor
from .window_door import WindowDoor, SolidDoor1, SolidDoor2, WindowDoorDouble
from .fixed_windows import Window140x120, Window90x120, WindowDouble160x120, WindowDouble160x140
from .door import Door
from .electricity import ElectricalCable, PowerOutlet
from .element import Element
from .external_model_test import ExternalModelTest
from .wooden_chair import WoodenChair
from .master_bed import MasterBed
from .sofa_model import SofaModel
from .blender_furniture import (
    Armchair, Chair20, ChaiseLongue1, Desk1,
    Sofa22, Sofa23, Stool7, Table01,
)
from .info import DimensionArrow, TextBox
from .lighting import CeilingLamp, LEDStrip, Switch, WallLamp
from .multipurpose import Line, Polygon, Circle
from .room import Room
from .furniture.storage import GenericStorage, Storage40, Storage60, Tabletop
from .furniture.bed import DoubleBed, SingleBed
from .furniture.appliances import (
    Dishwasher, Fridge, Freezer, WashingMachine, Dryer, Stovetop, SingleSink, DoubleSink
)
from .furniture.bathroom import Shower, Bathtub, Basin, Toilet
from .furniture.furniture import Desk, DiningTable, Chair, Sofa
from .furniture.decorations import FishTank
from .landscaping import Tree, Shrub, Hedge, Lawn, Fence, GardenPath, RetainingWall, Fountain, Pond, Pergola, RaisedBed, Gazebo, Deck, GardenHouse, RectPool, OvalPool


def create_elements_registry() -> dict[str, type[Element]]:
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
        'model_window_140x120': Window140x120,
        'model_window_90x120': Window90x120,
        'model_window_double_160x120': WindowDouble160x120,
        'model_window_double_160x140': WindowDouble160x140,
        'electrical_cable': ElectricalCable,
        'model_external_model_test': ExternalModelTest,
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
        'led_strip': LEDStrip,
        'line': Line,
        'polygon': Polygon,
        'power_outlet': PowerOutlet,
        'room': Room,
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
        'retaining_wall': RetainingWall,
        'fountain': Fountain,
        'pond': Pond,
        'rect_pool': RectPool,
        'oval_pool': OvalPool,
        'pergola': Pergola,
        'raised_bed': RaisedBed,
        'gazebo': Gazebo,
        'deck': Deck,
        'garden_house': GardenHouse
    }
    return registry

def get_element_type_from_instance(element: Element) -> str:
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


def element_sorter_by_type(element: Element) -> int:
    """
    Provide a sorting key for elements based on their type.
    :param element:
        element to be sorted
    :return:
        sorting key (lower values are sorted first)
    """

    if isinstance(element, (Wall, WallND)):
        return 0  # Walls first
    elif isinstance(element, Door):
        return 1  # Doors second
    elif isinstance(element, Window):
        return 2  # Windows third
    else:
        return 3  # Other elements last