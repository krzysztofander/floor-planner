"""
Vertical level mixins for element z-ordering.

These mixins provide default v_anchor values for different semantic layers
in floor plans. Elements inherit from the appropriate mixin to automatically
get the correct vertical positioning for drawing order.

Author: Floor Planner Team
"""


class VertInfoLvl00:
    """Ground surfaces (0.00m): lawns, paths, pool surfaces.
    
    Lowest drawing layer - always drawn first.
    Used for: Lawn, GardenPath, floor decorations.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for ground surface level."""
        return 0.00


class VertInfoLvl01:
    """Structural level (0.01m): walls, decks, fences.
    
    Foundation layer - drawn before objects placed on/near them.
    Used for: WallND, Wall, Deck, Fence, RetainingWall.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for structural level."""
        return 0.01


class VertInfoLvl02:
    """Landscaping/Door level (0.02m): trees, shrubs, doors.
    
    Secondary structures - drawn over walls but under furniture.
    Used for: Door, Tree, Shrub, Hedge, Fountain, Gazebo.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for landscaping/door level."""
        return 0.02


class VertInfoLvl03:
    """Furniture level (0.03m): tables, chairs, appliances.
    
    Object layer - items placed on floors, drawn over walls/doors.
    Used for: Desk, Table, Chair, Sofa, Bed, all appliances, bathroom fixtures.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for furniture level."""
        return 0.03


class VertInfoOutlets:
    """Wall outlet level (0.30m): power outlets.
    
    Mid-height wall fixtures.
    Used for: PowerOutlet.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for outlet level."""
        return 0.30


class VertInfoWindows:
    """Window level (1.00m): windows at sill height.
    
    Standard window sill height.
    Used for: Window.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for window level."""
        return 1.00


class VertInfoSwitches:
    """Switch level (1.20m): wall switches.
    
    Standard light switch height.
    Used for: Switch.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for switch level."""
        return 1.20


class VertInfoWallLamps:
    """Wall lamp level (2.00m): sconces.
    
    Upper wall-mounted fixtures.
    Used for: WallSconce.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for wall lamp level."""
        return 2.00


class VertInfoCeiling:
    """Ceiling level (2.70m): ceiling lamps.
    
    Standard ceiling height for ceiling-mounted fixtures.
    Used for: CeilingLamp, LightingElement.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for ceiling level."""
        return 2.70


class VertInfoAnnotations:
    """Annotation level (3.50m): info elements, labels.
    
    Highest drawing layer - always on top.
    Used for: AreaWithText, DimensionArrow, labels, text annotations.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for annotation level."""
        return 3.50
