"""
Draw universal elements that have context-dependent meaning.

Author: Nikolay Lysenko
"""


import matplotlib.axes
from matplotlib import patches

from ..element import Element
from ...utils import renderDim2pts
from ...options import get_label_color

class Line(Element):
    """Line (solid, dashed, or dotted)"""

    style_to_matplotlib_code = {'solid': '-', 'dashed': '--', 'dotted': ':', 'dash_dot': '-.'}

    def __init__(
            self,
            first_point: tuple[float, float],
            second_point: tuple[float, float],
            width: float = 0.5,
            style: str = 'solid',
            color: str = 'black',
            label: str | None = None,
            append_len: bool = False
    ):
        """
        Initialize an instance.

        :param first_point:
            coordinates of the first end (in meters)
        :param second_point:
            coordinates of the second end (in meters)
        :param width:
            width of the line for `matplotlib`
        :param style:
            type of line ('solid', 'dashed', 'dotted', or 'dash_dot')
        :param color:
            color to use for drawing the line
        :param label:
            optional label for the element
        :param append_len
            adds length to label
        """
        super().__init__(label=label, color=color, anchor_point=first_point)
        self.first_point = first_point
        self.second_point = second_point
        self.width = width
        self.style = self.style_to_matplotlib_code[style]
        self.font_size = 10 # fixed for now
        self.append_len = append_len
        self.text_elevation = self.font_size * 0.015   

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw line."""
        ax.plot(
            [self.first_point[0], self.second_point[0]],
            [self.first_point[1], self.second_point[1]],
            lw=self.width,
            ls=self.style,
            color=self.color
        )
        # Render label if present and color is configured
        if self.label is not None:
            label_color = get_label_color(type(self).__name__)
            if label_color is not None:
                renderDim2pts(ax,self.first_point, self.second_point, self.label, self.append_len,
                              self.font_size, self.text_elevation, label_color,  'white')
                              
                              
        

class Polygon(Element):
    """Polygon. In particular, it can be used for wall corners or acute or obtuse angles."""

    def __init__(
            self,
            vertices: list[tuple[float, float]],
            line_width: float = 0.1,
            color: str = 'black',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param vertices:
            list of vertices coordinates (in meters)
        :param line_width:
            width of lines for `matplotlib`
        :param color:
            color to use for drawing the line
        :param label:
            optional label for the element
        :return:
            freshly created instance of `Polygon` class
        """
        super().__init__(label=label, color=color, anchor_point=(0, 0))
        self.vertices = vertices
        self.line_width = line_width

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw polygon"""
        polygon = patches.Polygon(
            self.vertices,
            lw=self.line_width,
            fill=True,
            facecolor=self.color,
            edgecolor=self.color
        )
        polygon.set_zorder(self.get_zorder())
        ax.add_patch(polygon)

class Circle(Element):
    """Circle element"""

    def __init__(
            self,
            anchor_point: tuple[float, float],
            radius: float,
            color: str = 'black',
            label: str | None = None
    ):
        """
        Initialize an instance.

        :param anchor_point:
            coordinates of the center (in meters)
        :param radius:
            radius of the circle (in meters)
        :param color:
            color to use for drawing the circle
        :param label:
            optional label for the element
        """
        super().__init__(label=label, color=color, anchor_point=anchor_point)
        self.center = anchor_point
        self.radius = radius

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw circle"""
        circle = patches.Circle(
            self.center,
            self.radius,
            fill=True,
            facecolor=self.color,
            edgecolor=self.color
        )
        circle.set_zorder(self.get_zorder())
        ax.add_patch(circle)
