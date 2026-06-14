"""
Vertical level mixins for element z-ordering.

These mixins provide default v_anchor values for different semantic layers
in floor plans. Elements inherit from the appropriate mixin to automatically
get the correct vertical positioning for drawing order.

Author: Floor Planner Team
"""

class VertInfoLvlGround:
    """Below ground surface, earthworks.
    
    (below) Lowest drawing layer - always drawn even firster
    Used for: Ground, Ground works
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for ground surface level."""
        return -0.10
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (-0.0033, -0.0033, 0.0033)  
class VertInfoFloors:
    """Floor surface level (0.005m): room floor planes.
    
    Just above ground-level decorations, below all furniture.
    Used for: Floor surface element.
    """

    def _default_v_anchor(self) -> float:
        """Return v_anchor for floor surface level."""
        return 0.0

    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (0.0, 0.0, 0.0)
class VertInfoLvl00:
    """Ground surfaces (0.00m): lawns, paths, pool surfaces.
    
    Lowest drawing layer - always drawn first.
    Used for: Lawn, GardenPath, floor decorations.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for ground surface level."""
        return -0.01
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (0.0, -0.0022, 0.0)  # Ground level - some shrink


class VertInfoLvl01:
    """Structural level (0.01m): walls, decks, fences.
    
    Foundation layer - drawn before objects placed on/near them.
    Used for: WallND, Wall, Deck, Fence, RetainingWall.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for structural level."""
        return 0.01
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (-0.00001, -0.00001, 0.0)  # Tiny shrink for walls


class VertInfoDoor:
    """Door level (0.02m): doors and balcony doors.
    
    Secondary structures - drawn over walls but under furniture.
    Used for: Door, BalconyDoor, WindowDoor, SolidDoorN, WindowDoorDouble.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for landscaping/door level."""
        return 0.02
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (0.001, 0.001, 0.0)  # Small expansion for doors to protrude from walls


class VertInfoLvl03:
    """Furniture level (0.03m): tables, chairs, appliances.
    
    Object layer - items placed on floors, drawn over walls/doors.
    Used for: Desk, Table, Chair, Sofa, Bed, all appliances, bathroom fixtures.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for furniture level."""
        return 0.03
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (-0.012, -0.012, 0.0)  # Shrink furniture to avoid overlapping walls

class VertInfoLvl04:
    """Furniture level (0.04m): Storage boxes, cabinets.
    
    Object layer - items placed on floors, drawn over walls/doors.
    Used for: Desk, Table, Chair, Sofa, Bed, all appliances, bathroom fixtures.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for furniture level."""
        return 0.04
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (-0.011, -0.011, 0.0)  # Shrink storage to avoid overlapping walls and adjacent elements

class VertInfoOutlets:
    """Wall outlet level (0.30m): power outlets.
    
    Mid-height wall fixtures.
    Used for: PowerOutlet.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for outlet level."""
        return 0.30
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (0.0003, 0.0003, 0.0)  # Outlets protrude slightly from walls


class VertInfoWindows:
    """Window level (1.00m): windows at sill height.
    
    Standard window sill height.
    Used for: Window.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for window level."""
        return 1.00

    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry.

        Windows extend 0.002m beyond the wall on each end (length) and 0.002m
        above/below (height) to prevent z-fighting at the wall boundary.
        Thickness is not expanded — the window already fills the full wall depth.
        """
        return (0.004, 0.0, 0.004)


class VertInfoSwitches:
    """Switch level (1.20m): wall switches.
    
    Standard light switch height.
    Used for: Switch.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for switch level."""
        return 1.20
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (0.0012, 0.0012, 0.0)  # Switches protrude from walls


class VertInfoWallLamps:
    """Wall lamp level (2.00m): sconces.
    
    Upper wall-mounted fixtures.
    Used for: WallSconce.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for wall lamp level."""
        return 2.00
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (0.002, 0.002, 0.0)  # Wall lamps protrude from walls


class VertInfoCeiling:
    """Ceiling level (2.70m): ceiling lamps.
    
    Standard ceiling height for ceiling-mounted fixtures.
    Used for: CeilingLamp, LightingElement.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for ceiling level."""
        return 2.70
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (0.0, 0.0, 0.0)  # Ceiling fixtures don't overlap with walls





class VertInfoCeilingSurface:
    """Ceiling surface level (2.69m): room ceiling planes.
    
    Just below ceiling-mounted fixtures, above all furniture.
    Used for: Ceiling surface element.
    """

    def _default_v_anchor(self) -> float:
        """Return v_anchor for ceiling surface level."""
        return 2.69

    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (0.0, 0.0, 0.0)


class VertInfoAnnotations:
    """Annotation level (3.50m): info elements, labels.
    
    Highest drawing layer - always on top.
    Used for: AreaWithText, DimensionArrow, labels, text annotations.
    """
    
    def _default_v_anchor(self) -> float:
        """Return v_anchor for annotation level."""
        return 3.50
    
    def _get_3d_expansion(self) -> tuple[float, float, float]:
        """Return (length_exp, thickness_exp, height_exp) for 3D geometry."""
        return (0.0, 0.0, 0.0)  # Annotations are not exported to 3D
