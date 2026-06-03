"""
Furniture elements for floor plans.

Author: Krzysztof Bartczak
"""

from .appliances import Dishwasher, Dryer, Freezer, Fridge, Stovetop, WashingMachine, SingleSink, DoubleSink
from .bathroom import Bathtub, Basin, Shower, Toilet
from .bed import DoubleBed, MultiBed, SingleBed
from .decorations import FishTank
from .furniture import Chair, Desk, DiningTable, Sofa
from .storage import GenericStorage, Storage40, Storage60, Tabletop


__all__ = [
    # appliances
    'Dishwasher',
    'Dryer',
    'Freezer',
    'Fridge',
    'Stovetop',
    'WashingMachine',
    'SingleSink',
    'DoubleSink',
    # bathroom
    'Bathtub',
    'Basin',
    'Shower',
    'Toilet',
    # bed
    'DoubleBed',
    'MultiBed',
    'SingleBed',
    # decorations
    'FishTank',
    # furniture
    'Chair',
    'Desk',
    'DiningTable',
    'Sofa',
    # storage
    'GenericStorage',
    'Storage40',
    'Storage60',
    'Tabletop',
]
