"""
Draw a window

"""


import math

import matplotlib.axes
from matplotlib.patches import Rectangle

from ...utils import rotate_point, render_label_and_id, text_readability_rotation, assert_has_attrs
from ..element import Element, RectangularElement
from ..vertical_levels import VertInfoWindows

class Window2D:
    """2D geometry for a window.
    
    Used for: Window kind of types.
    """
    def __init__(self, handled_element):
        required_attrs = ['anchor_point', 
                            'length',
                            'overall_thickness',
                            'single_line_thickness',
                            'orientation_angle',
                            'color',
                            'label'
        ]
        assert_has_attrs(handled_element, *required_attrs)
        assert isinstance(handled_element, Element)

        self.handled_element = handled_element

        internal_thickness = handled_element.overall_thickness - 2 * handled_element.single_line_thickness
        if internal_thickness <= 0:
            raise ValueError(
                "Window cannot be drawn: overall_thickness is too small relative "
                "to single_line_thickness."
            )


    def draw(self, ax: matplotlib.axes.Axes, z_order: float) -> None:
        
        """Draw window on 2D plan view using Matplotlib."""
        # Check if element should be drawn (handles invisible color)
        draw_color = self.handled_element.get_draw_color()
        if draw_color is None:
            return
        
        first_line = Rectangle(
            self.handled_element.anchor_point,
            self.handled_element.length,
            self.handled_element.single_line_thickness,
            angle=self.handled_element.orientation_angle,
            facecolor=draw_color
        )
        first_line.set_zorder(z_order)
        ax.add_patch(first_line)

        window_emptyness_anchor_point = rotate_point(anchor_point=self.handled_element.anchor_point,
                                    offset_x=0,
                                    offset_y=self.handled_element.single_line_thickness ,
                                    angle_rad=(math.radians(self.handled_element.orientation_angle)))
        window_emptyness = Rectangle(
            window_emptyness_anchor_point,
            self.handled_element.length,
            self.handled_element.overall_thickness - 2*self.handled_element.single_line_thickness,
            angle=self.handled_element.orientation_angle,
            facecolor='white'
        )
        window_emptyness.set_zorder(z_order)
        ax.add_patch(window_emptyness)

        second_anchor_point = rotate_point(anchor_point=self.handled_element.anchor_point,
                                    offset_x=0,
                                    offset_y=self.handled_element.overall_thickness -self.handled_element.single_line_thickness ,
                                    angle_rad=(math.radians(self.handled_element.orientation_angle)))
        second_line = Rectangle(
            second_anchor_point,
            self.handled_element.length,
            self.handled_element.single_line_thickness,
            angle=self.handled_element.orientation_angle,
            facecolor=draw_color
        )
        second_line.set_zorder(z_order)
        ax.add_patch(second_line)


    def render_window_label_and_id(self, element_type_overwrite, ax: matplotlib.axes.Axes) -> None:
        # Render label and ID at midpoint between the two lines and centered horizontally
        label_position = rotate_point(anchor_point=self.handled_element.anchor_point,
                                    offset_x=self.handled_element.length /2,
                                    offset_y=self.handled_element.overall_thickness /2,
                                    angle_rad=(math.radians(self.handled_element.orientation_angle)))
        render_label_and_id(
            ax,
            self.handled_element,
            element_type_overwrite,
            label_position,
            text_readability_rotation(self.handled_element.orientation_angle),
            centered=True
        )
  
  

class Window(VertInfoWindows, RectangularElement):
    """Window in a wall."""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            length: float,
            overall_thickness: float,
            single_line_thickness: float = -1,
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None,
            **kwargs
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates (in meters) of anchor point;
            bottom left point is anchor point if `orientation_angle == 0`
        :param length:
            length of the window (in meters)
        :param overall_thickness:
            total thickness of the window (in meters)
        :param single_line_thickness:
            thickness of a single outer line forming window (in meters)
        :param orientation_angle:
            angle (in degrees) that specifies orientation of the window;
            it is measured between X-axis and the window in positive direction (counterclockwise);
            initial window is rotated around anchor point to get the desired orientation
        :param color:
            color to use for drawing the window
        :param label:
            optional label for the element
        :param kwargs:
            additional parameters (e.g., texture_scale, v_anchor, height, id);
            texture_scale defaults to 0.2 (0.2m x 0.2m tiles) for windows if not specified
        :return:
            freshly created instance of `Window` class
        """

        if single_line_thickness <= 0:
            single_line_thickness = overall_thickness / 10
        
        self.single_line_thickness = single_line_thickness
        self.overall_thickness = overall_thickness
        self.alpha_mode = "BLEND"  # Windows use alpha blending for transparency

        # Set default texture_scale for windows to 0.2 (0.2m x 0.2m tiles)
        if 'texture_scale' not in kwargs:
            kwargs['texture_scale'] = 0.2

        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            length=length,
            thickness=overall_thickness,
            color=color,
            label=label,
            **kwargs
        )

        self.window2d = Window2D(self)

    def _default_height(self) -> float:
        """Return default height for windows."""
        return 1.4
    
    def draw(self, ax):
        """Draw the window."""
        self.window2d.draw(ax, z_order=self.get_zorder())
        # Note: if color is "invisible", the label is still drawn
        self.window2d.render_window_label_and_id(element_type_overwrite="Window", ax=ax)
        
  
