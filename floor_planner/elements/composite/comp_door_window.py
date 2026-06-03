"""
Composite elements combining multiple ModelElements into a single logical unit

Author: Krzysztof Bartczak
"""
from ..element import ElementBase
from ..external.window_door import WindowDoor
from ...options import generate_element_id
from ...utils import rotate_point
import matplotlib.axes
import math


class Composite_WindowDoorDouble(ElementBase):
    def __init__(
            self,
            anchor_point: tuple[float, float],
            doorway_width: float,
            door_width: float,
            thickness: float,
            orientation_angle: float = 0,
            to_the_right: bool = False,
            color: str = 'black',
            hinges_point: float = 0.95,
            opening_outside: bool = False,
            label: str | None = None,
            **kwargs
    ):
        super().__init__()

        middle_bar_spacing = 0.00  # Space between the two wings in the 3D model (metres)
        calc_door_width = door_width/2
        calc_doorway_width = (doorway_width - middle_bar_spacing)/2

        rotated_anchor_l = rotate_point( anchor_point, 0,0, math.radians(orientation_angle))
        rotated_anchor_r = rotate_point(rotated_anchor_l, calc_doorway_width + middle_bar_spacing, 0, math.radians(orientation_angle))
        
  
        self.addToList(
            WindowDoor(
                anchor_point=rotated_anchor_l,
                doorway_width=calc_doorway_width,
                door_width=calc_door_width,
                thickness=thickness,
                orientation_angle=orientation_angle,
                to_the_right=False,
                color=color,
                hinges_point=hinges_point,
                opening_outside=opening_outside,
                label=label,
                **kwargs)
        )
        if True:  
            self.addToList(
                WindowDoor(
                    anchor_point=rotated_anchor_r,
                    doorway_width=calc_doorway_width,
                    door_width=calc_door_width,
                    thickness=thickness,
                    orientation_angle=orientation_angle,
                    to_the_right=True,
                    color=color,
                    hinges_point=hinges_point,
                    opening_outside=opening_outside,
                    label=label,
                    **kwargs)
            )
        # Generate unique ID based on class name and label, or use provided ID
        self.id = generate_element_id(self.__class__.__name__, label)
 
    
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        for element in self.getList():
            element.draw(ax)
    
    def get_id(self) -> str:
        """Get the element ID."""
        return self.id