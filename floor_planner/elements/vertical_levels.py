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
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D.
        
        Elements with higher v_anchor get larger offsets to protrude from underlying surfaces.
        Returns offset in meters to add to length and thickness.
        """
        return 0.0  # Ground level - no offset needed


class VertInfoLvl01:
    """Structural level (0.01m): walls, decks, fences.
    
    Foundation layer - drawn before objects placed on/near them.
    Used for: WallND, Wall, Deck, Fence, RetainingWall.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for structural level."""
        return 0.01
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D."""
        return -0.00001  # Tiny offset for walls


class VertInfoLvl02:
    """Landscaping/Door level (0.02m): trees, shrubs, doors.
    
    Secondary structures - drawn over walls but under furniture.
    Used for: Door, Tree, Shrub, Hedge, Fountain, Gazebo.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for landscaping/door level."""
        return 0.02
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D."""
        return 0.001  # Small offset for doors to protrude from walls


class VertInfoLvl03:
    """Furniture level (0.03m): tables, chairs, appliances.
    
    Object layer - items placed on floors, drawn over walls/doors.
    Used for: Desk, Table, Chair, Sofa, Bed, all appliances, bathroom fixtures.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for furniture level."""
        return 0.03
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D."""
        return 0.0  # Furniture doesn't overlap with walls, no offset needed


class VertInfoOutlets:
    """Wall outlet level (0.30m): power outlets.
    
    Mid-height wall fixtures.
    Used for: PowerOutlet.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for outlet level."""
        return 0.30
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D."""
        return 0.0003  # Outlets protrude slightly from walls


class VertInfoWindows:
    """Window level (1.00m): windows at sill height.
    
    Standard window sill height.
    Used for: Window.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for window level."""
        return 1.00
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D."""
        return 0.001  # Windows protrude significantly from walls to prevent z-fighting


class VertInfoSwitches:
    """Switch level (1.20m): wall switches.
    
    Standard light switch height.
    Used for: Switch.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for switch level."""
        return 1.20
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D."""
        return 0.0012  # Switches protrude from walls


class VertInfoWallLamps:
    """Wall lamp level (2.00m): sconces.
    
    Upper wall-mounted fixtures.
    Used for: WallSconce.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for wall lamp level."""
        return 2.00
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D."""
        return 0.002  # Wall lamps protrude from walls


class VertInfoCeiling:
    """Ceiling level (2.70m): ceiling lamps.
    
    Standard ceiling height for ceiling-mounted fixtures.
    Used for: CeilingLamp, LightingElement.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for ceiling level."""
        return 2.70
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D."""
        return 0.0  # Ceiling fixtures don't overlap with walls


class VertInfoAnnotations:
    """Annotation level (3.50m): info elements, labels.
    
    Highest drawing layer - always on top.
    Used for: AreaWithText, DimensionArrow, labels, text annotations.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for annotation level."""
        return 3.50
    
    def _get_geometric_offset(self) -> float:
        """Return geometric offset for z-fighting prevention in 3D."""
        return 0.0  # Annotations are not exported to 3D
