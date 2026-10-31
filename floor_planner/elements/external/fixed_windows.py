"""
Fixed-size window elements with external 3D models.

All four classes draw identically to the standard Window element in 2D.
Each has its own OBJ/MTL model and dedicated texture files for 3D export.

Sizes (width × height):
  Window140x120      — 1.40 m × 1.20 m, single pane
  Window90x120       — 0.90 m × 1.20 m, single pane
  WindowDouble160x120 — 1.60 m × 1.20 m, two panes
  WindowDouble160x140 — 1.60 m × 1.40 m, two panes

YAML type keys:
  window_140x120 / window_90x120
  window_double_160x120 / window_double_160x140
"""

import math

import matplotlib.axes
from matplotlib.patches import Rectangle

from ...utils import rotate_point, render_label_and_id, text_readability_rotation
from ..external_models import ExternalModelElement
from ..vertical_levels import VertInfoWindows
from ...options import get_element_option
from ...options import generate_element_id
from ..foundation.windows import Window2D
from ..element import ElementBase

class _FixedWindow(VertInfoWindows, ExternalModelElement):
    """
    Internal base: fixed-size window that draws like the standard Window.

    Subclasses must set _registry_key to match their model directory name.
    """

    _requires_external_model = True

    def __init__(
        self,
        anchor_point: tuple[float, float],
        overall_thickness: float,
        single_line_thickness: float = -1,
        orientation_angle: float = 0,
        color: str = 'black',
        label: str | None = None,
        id: str | None = None,
        v_anchor: float | None = None,
        models_dir: str | None = None
    ):
        """
        Args:
            anchor_point: (x, y) position of the bottom-left frame corner (metres).
            overall_thickness: Total wall/window depth (metres), used for 2D drawing.
            single_line_thickness: Thickness of each glazing bar line in 2D.
                Defaults to overall_thickness / 10.
            orientation_angle: CCW rotation from X-axis (degrees).
            color: 2D drawing colour.
            label: Optional text label.
            id: Optional explicit ID; generated when omitted.
            v_anchor: Optional 3D elevation of the base (metres).
            models_dir: Optional base model directory.
        """
        if single_line_thickness <= 0:
            single_line_thickness = overall_thickness / 10
        # Store 2D geometry params before super() sets dimensions from model.
        self.overall_thickness = overall_thickness
        self.thickness = overall_thickness  # exposed for wall-opening detection
        self.single_line_thickness = single_line_thickness
        self.alpha_mode = "BLEND"

        super().__init__(
            anchor_point=anchor_point,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            id=id,
            v_anchor=v_anchor,
            models_dir=models_dir
        )

        self.window2d = Window2D(self)

    # ------------------------------------------------------------------
    # 2D drawing — identical to Window.draw()
    # ------------------------------------------------------------------

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """Draw the window."""
        self.window2d.draw(ax, z_order=self.get_zorder())
        # Note: if color is "invisible", the label is still drawn
        self.window2d.render_window_label_and_id(element_type_overwrite="Window", ax=ax)


# ── Concrete classes ───────────────────────────────────────────────────────────

class WindowSingleAny(_FixedWindow):
    """Single-pane window, 1.40 m wide × 1.20 m tall."""
    _registry_key = 'window_single_any'

    def __init__(
        self,
        anchor_point: tuple[float, float],
        overall_thickness: float,
        single_line_thickness: float = -1,
        length: float = 1.4,
        height: float = 1.2,
        orientation_angle: float = 0,
        color: str = 'black',
        label: str | None = None,
        id: str | None = None,
        v_anchor: float | None = None,
        models_dir: str | None = None
    ):
        super().__init__(
            anchor_point=anchor_point,
            overall_thickness=overall_thickness,
            single_line_thickness=single_line_thickness,
            orientation_angle=orientation_angle,
            color=color,
            label=label,
            id=id,
            v_anchor=v_anchor,
            models_dir=models_dir
        )
        self.length = length
        self.height = height


        self.secondary_normalization =      {
                'scale':       [length / self._default_length(), height / self._default_height(), 1],
                'rotation':    [0,0,0],
                'translation': [0,0,0],
            }
        self.secondary_anchor_offset = [0,0,0]


    def _default_width(self) -> float:
        return 1.40

    def _default_length(self) -> float:
        return 1.40

    def _default_height(self) -> float:
        return 1.20

class Composite_WindowDouble(ElementBase):
    def __init__(
            self,
            anchor_point: tuple[float, float],
            overall_thickness: float,
            single_line_thickness: float = -1,
            length: float = 1.4,
            height: float = 1.2,
            orientation_angle: float = 0,
            color: str = 'black',
            label: str | None = None,
            id: str | None = None,
            v_anchor: float | None = None,
            models_dir: str | None = None
    ):
        super().__init__()

        middle_bar_spacing = 0.00  # Space between the two wings in the 3D model (metres)
        calc_single_w_length = length/2
        calc_overall_width = (length - middle_bar_spacing)/2

        rotated_anchor_l = rotate_point( anchor_point, 0,0, math.radians(orientation_angle))
        rotated_anchor_r = rotate_point(rotated_anchor_l, calc_overall_width + middle_bar_spacing, 0, math.radians(orientation_angle))
        
  
        self.addToList(
            WindowSingleAny(
                anchor_point = rotated_anchor_l,
                overall_thickness = overall_thickness,
                single_line_thickness = single_line_thickness,
                length =  calc_single_w_length,
                height = height,
                orientation_angle = orientation_angle,
                color = color,
                label=label,
                v_anchor=v_anchor,
                models_dir=models_dir)
        )
        self.addToList(
                WindowSingleAny(
                anchor_point=  rotated_anchor_r,
                overall_thickness = overall_thickness,
                single_line_thickness = single_line_thickness,
                length =  calc_single_w_length,
                height = height,
                orientation_angle = orientation_angle,
                color = color,
                label=label,
                v_anchor=v_anchor,
                models_dir=models_dir)
        )
        # Generate unique ID based on class name and label, or use provided ID
        self.id = id if id else generate_element_id(self.__class__.__name__, label)
 
    
    def draw(self, ax: matplotlib.axes.Axes) -> None:
        for element in self.getList():
            element.draw(ax)
    
    def get_id(self) -> str:
        """Get the element ID."""
        return self.id

class Window140x120(_FixedWindow):
    """Single-pane window, 1.40 m wide × 1.20 m tall."""
    _registry_key = 'window_140x120'

    def _default_width(self) -> float:
        return 1.40

    def _default_length(self) -> float:
        return 1.40

    def _default_height(self) -> float:
        return 1.20


class Window90x120(_FixedWindow):
    """Single-pane window, 0.90 m wide × 1.20 m tall."""
    _registry_key = 'window_90x120'

    def _default_width(self) -> float:
        return 0.90

    def _default_length(self) -> float:
        return 0.90

    def _default_height(self) -> float:
        return 1.20


class WindowDouble160x120(_FixedWindow):
    """Double-pane window (two glass panels), 1.60 m wide × 1.20 m tall."""
    _registry_key = 'window_double_160x120'

    def _default_width(self) -> float:
        return 1.60

    def _default_length(self) -> float:
        return 1.60

    def _default_height(self) -> float:
        return 1.20


class WindowDouble160x140(_FixedWindow):
    """Double-pane window (two glass panels), 1.60 m wide × 1.40 m tall."""
    _registry_key = 'window_double_160x140'

    def _default_width(self) -> float:
        return 1.60

    def _default_length(self) -> float:
        return 1.60

    def _default_height(self) -> float:
        return 1.40
