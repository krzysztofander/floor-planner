"""
Room element: a Group whose children include exactly 4 room-edge walls
forming a rectangle, plus optional windows, doors and other elements.

Author: Krzysztof Bartczak
"""


import math
import matplotlib.axes

from ...variables import resolve_element_params
from ..symbols.info import DimensionArrow, TextBox
from ...options import get_label_color, get_element_option
from .surfaces import Floor, Ceiling
from .group import Group

_SURFACE_TYPES = {'floor': Floor, 'ceiling': Ceiling}


class Room(Group):
    """
    Room defined by 4 walls forming a rectangle, with optional other elements.

    Extends Group: inherits anchor-based element grouping and the shared
    ``_resolve_params`` / ``_create_children`` helpers.  Additionally validates
    that the room contains exactly 4 walls with ``room_edge=True`` that form a
    proper axis-aligned rectangle, and computes geometric properties
    (inner/outer dimensions, areas, corner coordinates).
    """

    def __init__(
            self,
            walls: list,
            other_elements: list | None = None,
            anchor_point: tuple[float, float] = (0, 0),
            color: str = 'black',
            label: str | None = None,
            purpose: str | None = None
    ):
        """
        Initialize a room from walls and optional other elements.

        :param walls:
            list of wall objects (Wall or WallND); exactly 4 must have room_edge=True
        :param other_elements:
            optional list of other element objects (windows, doors, etc.) inside the room
        :param anchor_point:
            coordinates (x, y) of the room's reference point (bottom-left corner)
        :param color:
            default color for room walls if they don't have explicit color
        :param label:
            optional label for the room
        :param purpose:
            optional purpose of a room e.g. living space, outdoor, storage, etc.
        :raises ValueError:
            if walls don't form a valid rectangle or exactly 4 walls don't have room_edge=True
        """
        all_children = list(walls) + list(other_elements or [])
        super().__init__(child_elements=all_children, anchor_point=anchor_point, color=color, label=label)

        self.walls = walls
        self.other_elements = other_elements or []
        self.purpose = purpose
        print (f"S: {self.label}, {self.purpose}" )

        # Mark walls as room walls
        for wall in walls:
            wall.is_room_wall = True
            wall.room_id = self.get_id()

        # Validate and organize walls, then calculate geometric properties
        self._validate_and_organize_walls()
        self._calculate_properties()

    # ------------------------------------------------------------------
    # Factory – overrides Group.create_from_params to handle surfaces and
    # wall validation.  Reuses the shared _resolve_params / _create_children.
    # ------------------------------------------------------------------

    @classmethod
    def create_from_params(cls, params: dict, elements_registry: dict, floor_plan,
                           all_elements: list, elements_by_id: dict,
                           global_vars: dict = None):
        """
        Create a Room from YAML parameters with nested elements.

        :param params:
            dictionary with 'elements' list containing wall/window/door definitions,
            optional 'anchor_point', 'color', 'label', and 'vars'
        :param elements_registry:
            registry mapping element type names to classes
        :param floor_plan:
            floor plan to add child elements to
        :param all_elements:
            list to track all created elements
        :param elements_by_id:
            dictionary to track elements by ID
        :param global_vars:
            global variables dictionary (optional)
        :return:
            Room instance
        """
        if global_vars is None:
            global_vars = {}

        room_vars, anchor, color, label = cls._resolve_params(params, global_vars)
        purpose = params.get('purpose',None)

        element_defs = params.get('elements', [])
        if not element_defs:
            raise ValueError("Room must have 'elements' list containing wall and other element definitions")

        # Separate floor/ceiling surface defs — they need room.internal_corners,
        # which are only available after the Room instance is constructed.
        surface_defs = [d for d in element_defs if d.get('type') in _SURFACE_TYPES]
        regular_defs = [d for d in element_defs if d.get('type') not in _SURFACE_TYPES]

        children = cls._create_children(
            regular_defs,
            elements_registry, floor_plan, all_elements, elements_by_id,
            global_vars, room_vars, anchor, color,
        )

        walls = [c for c in children if c.__class__.__name__ in ('Wall', 'WallND')]
        other = [c for c in children if c.__class__.__name__ not in ('Wall', 'WallND')]

        if not walls:
            raise ValueError("Room must contain at least one wall")

        room = cls(walls=walls, other_elements=other, anchor_point=anchor, color=color, label=label, purpose = purpose )

        if surface_defs:
            cls._create_surface_elements(
                room, surface_defs, floor_plan, all_elements, elements_by_id,
                global_vars, room_vars
            )

        return room

    # ------------------------------------------------------------------
    # Surface helper
    # ------------------------------------------------------------------

    @classmethod
    def _create_surface_elements(cls, room, surface_defs, floor_plan,
                                 all_elements, elements_by_id, global_vars, room_vars):
        """Create Floor/Ceiling elements after the Room is built."""
        inner_bl = room.internal_corners[0]   # bottom-left
        inner_tr = room.internal_corners[2]   # top-right
        inner_anchor = inner_bl
        inner_size = (inner_tr[0] - inner_bl[0], inner_tr[1] - inner_bl[1])

        for surface_def in surface_defs:
            surface_def = dict(surface_def)
            surface_type = surface_def.pop('type')
            surface_class = _SURFACE_TYPES[surface_type]

            surface_def = resolve_element_params(surface_def, global_vars, room_vars)
            surface_def['anchor_point'] = inner_anchor
            surface_def['size'] = inner_size

            element = surface_class(**surface_def)
            floor_plan.add_element(element)
            all_elements.append(element)
            elements_by_id[element.get_id()] = element

    # ------------------------------------------------------------------
    # Wall validation
    # ------------------------------------------------------------------

    def _validate_and_organize_walls(self):
        """Validate walls form a rectangle and organize them."""
        room_edge_walls = [wall for wall in self.walls if wall.room_edge]

        if len(room_edge_walls) != 4:
            raise ValueError(
                f"Room requires exactly 4 walls with room_edge=True, got {len(room_edge_walls)}. "
                f"Total walls in room: {len(self.walls)}"
            )

        horizontal_walls = []
        vertical_walls = []

        for wall in room_edge_walls:
            angle = wall.orientation_angle % 360
            if angle in (0, 180):
                horizontal_walls.append(wall)
            elif angle in (90, 270):
                vertical_walls.append(wall)
            else:
                raise ValueError(
                    f"Wall with orientation {wall.orientation_angle}° is neither horizontal nor vertical"
                )

        if len(horizontal_walls) != 2:
            raise ValueError(f"Room requires exactly 2 horizontal walls, got {len(horizontal_walls)}")
        if len(vertical_walls) != 2:
            raise ValueError(f"Room requires exactly 2 vertical walls, got {len(vertical_walls)}")

        self.room_edge_walls = room_edge_walls
        self._validate_corner_alignment()

    def _validate_corner_alignment(self):
        """Validate that wall corners align to form a rectangle."""
        all_corners = []
        for wall in self.room_edge_walls:
            all_corners.extend(wall.get_corners())

        x_coords = [c[0] for c in all_corners]
        y_coords = [c[1] for c in all_corners]
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        self.external_corners = [
            (min_x, min_y),   # 0: bottom-left
            (max_x, min_y),   # 1: bottom-right
            (max_x, max_y),   # 2: top-right
            (min_x, max_y)    # 3: top-left
        ]

        self.bottom_wall = self.top_wall = self.left_wall = self.right_wall = None

        for wall in self.room_edge_walls:
            wall_corners = wall.get_corners()
            matched = set()
            for wc in wall_corners:
                for i, ec in enumerate(self.external_corners):
                    if (math.isclose(wc[0], ec[0], abs_tol=1e-9) and
                            math.isclose(wc[1], ec[1], abs_tol=1e-9)):
                        matched.add(i)
                        break

            if len(matched) != 2:
                print(f"DEBUG: Wall '{wall.label}' has {len(matched)} corners matching external corners (expected 2)")
                print(f"       Wall corners: {[(f'({c[0]:.3f}, {c[1]:.3f})') for c in wall_corners]}")
                print(f"       External corners: {[(f'({c[0]:.3f}, {c[1]:.3f})') for c in self.external_corners]}")
                raise ValueError(
                    f"Invalid rectangle: Wall '{wall.label}' has {len(matched)} corners matching "
                    f"external rectangle corners (expected exactly 2). "
                    f"Check that the wall connects properly at room corners."
                )

            if matched == {0, 1}:
                self.bottom_wall = wall
            elif matched == {1, 2}:
                self.right_wall = wall
            elif matched == {2, 3}:
                self.top_wall = wall
            elif matched == {0, 3}:
                self.left_wall = wall

        if not all([self.bottom_wall, self.top_wall, self.left_wall, self.right_wall]):
            raise ValueError(
                f"Failed to identify all wall positions. "
                f"Bottom: {self.bottom_wall is not None}, Top: {self.top_wall is not None}, "
                f"Left: {self.left_wall is not None}, Right: {self.right_wall is not None}"
            )

    # ------------------------------------------------------------------
    # Geometric properties
    # ------------------------------------------------------------------

    def _calculate_properties(self):
        """Calculate room dimensions and areas."""
        ox_min = self.external_corners[0][0]
        ox_max = self.external_corners[1][0]
        oy_min = self.external_corners[0][1]
        oy_max = self.external_corners[2][1]

        self.outer_horizontal_length = ox_max - ox_min
        self.outer_vertical_length   = oy_max - oy_min
        self.outer_area              = self.outer_horizontal_length * self.outer_vertical_length

        ix_min = ox_min + self.left_wall.thickness
        ix_max = ox_max - self.right_wall.thickness
        iy_min = oy_min + self.bottom_wall.thickness
        iy_max = oy_max - self.top_wall.thickness

        self.inner_horizontal_length = ix_max - ix_min
        self.inner_vertical_length   = iy_max - iy_min
        self.inner_area              = self.inner_horizontal_length * self.inner_vertical_length

        self.internal_corners = [
            (ix_min, iy_min),   # 0: bottom-left
            (ix_max, iy_min),   # 1: bottom-right
            (ix_max, iy_max),   # 2: top-right
            (ix_min, iy_max)    # 3: top-left
        ]

    # ------------------------------------------------------------------
    # Drawing
    # ------------------------------------------------------------------

    def draw(self, ax: matplotlib.axes.Axes) -> None:
        """
        Draw room label and dimensions if options are configured.
        Room walls are drawn separately.
        """
        label_color = get_label_color('Room')
        if label_color is not None and self.label is not None:
            label_x = self.internal_corners[0][0] + 0.2
            label_y = self.internal_corners[0][1] + 0.2
            ax.text(
                label_x, label_y, self.label,
                fontsize=14, color=label_color,
                horizontalalignment='left', verticalalignment='bottom'
            )

        dimensions_enabled = get_element_option('Room', 'dimensions', False)
        if dimensions_enabled:
            horizontal_offset = self.inner_vertical_length / 5
            DimensionArrow(
                anchor_point=(
                    self.internal_corners[0][0],
                    self.internal_corners[0][1] + horizontal_offset
                ),
                length=self.inner_horizontal_length,
                orientation_angle=0, color='black', annotate_above=True
            ).draw(ax)

            vertical_offset = self.inner_horizontal_length * 4 / 5
            DimensionArrow(
                anchor_point=(
                    self.internal_corners[0][0] + vertical_offset,
                    self.internal_corners[0][1]
                ),
                length=self.inner_vertical_length,
                orientation_angle=90, color='black', annotate_above=True
            ).draw(ax)

        inner_area_enabled = get_element_option('Room', 'inner_area', False)
        if inner_area_enabled:
            cx = (self.internal_corners[0][0] + self.internal_corners[2][0]) / 2
            cy = (self.internal_corners[0][1] + self.internal_corners[2][1]) / 2
            TextBox(
                anchor_point=(cx, cy),
                lines=[f"{round(self.inner_area, 1):.1f}m²"],
                font_size=14, color='gray', edgecolor='none'
            ).draw(ax)

        inner_corner_color = get_element_option('Room', 'inner_corner_label_color')
        if inner_corner_color is not None:
            corner_parameters = [
                (45,  'left',  'bottom'),
                (135, 'right', 'bottom'),
                (225, 'right', 'top'),
                (315, 'left',  'top'),
            ]
            for i, corner in enumerate(self.internal_corners):
                ax.text(
                    corner[0], corner[1],
                    f" ({round(corner[0], 2)}, {round(corner[1], 2)})",
                    fontsize=6, color=inner_corner_color,
                    rotation=corner_parameters[i][0],
                    horizontalalignment=corner_parameters[i][1],
                    verticalalignment=corner_parameters[i][2]
                )

        outer_corner_color = get_element_option('Room', 'outer_corner_label_color')
        if outer_corner_color is not None:
            corner_parameters = [
                (225, 'right', 'top'),
                (315, 'left',  'top'),
                (45,  'left',  'bottom'),
                (135, 'right', 'bottom'),
            ]
            for i, corner in enumerate(self.external_corners):
                ax.text(
                    corner[0], corner[1],
                    f" ({round(corner[0], 2)}, {round(corner[1], 2)})",
                    fontsize=6, color=outer_corner_color,
                    rotation=corner_parameters[i][0],
                    horizontalalignment=corner_parameters[i][1],
                    verticalalignment=corner_parameters[i][2]
                )

