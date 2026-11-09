"""
Draw single floor plan.

Author: Nikolay Lysenko
"""


from pathlib import Path
from typing import Optional
from collections import defaultdict

import matplotlib.pyplot as plt
import numpy as np

from .constants import METERS_PER_INCH
from .elements import ElementBase, Room
from .layers import FloorPlanLayers, apply_layer

class FloorPlan:
    """Floor plan."""

    def __init__(
            self,
            bottom_left_corner: tuple[float, float],
            top_right_corner: tuple[float, float],
            scale_numerator: int = 1,
            scale_denominator: int = 100,
            grid_major_step: Optional[float] = None,
            grid_minor_step: Optional[float] = None,
    ):
        """
        Initialize an instance.

        :param bottom_left_corner:
            coordinates (in meters before scaling) of the bottom left corner of the floor plan
        :param top_right_corner:
            coordinates (in meters before scaling) of the top right corner of the floor plan
        :param scale_numerator:
            scale numerator
        :param scale_denominator:
            scale denominator
        :param grid_major_step:
            step (in meters before scaling) between major grid lines
        :param grid_minor_step:
            step (in meters before scaling) between minor grid lines
        :return:
            freshly created instance of `FloorPlan` class
        """
        horizontal_len = top_right_corner[0] - bottom_left_corner[0]
        vertical_len = top_right_corner[1] - bottom_left_corner[1]
        scale = scale_numerator / scale_denominator
        fig_width = horizontal_len * scale / METERS_PER_INCH
        fig_height = vertical_len * scale / METERS_PER_INCH

        fig = plt.figure(figsize=(fig_width, fig_height))
        ax = fig.add_subplot(111)
        # Adjust margins (values are fractions of figure width/height, 0-1)
        fig.subplots_adjust(left=0.025, right=0.975, bottom=0.025, top=0.975)
        ax.set_aspect('equal')
        ax.tick_params(
            which='both',
            left=False, right=False, bottom=False, top=False,
            labelleft=False, labelright=False, labelbottom=False, labeltop=False,
        )
        ax.spines['left'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.spines['bottom'].set_visible(False)
        ax.spines['top'].set_visible(False)

        if grid_major_step is not None:
            major_xticks = np.arange(
                bottom_left_corner[0],
                top_right_corner[0] + 0.5 * grid_major_step,
                grid_major_step
            )
            major_yticks = np.arange(
                bottom_left_corner[1],
                top_right_corner[1] + 0.5 * grid_major_step,
                grid_major_step
            )
            ax.set_xticks(major_xticks)
            ax.set_yticks(major_yticks)
            ax.grid(which='major', color='orange', alpha=0.25)
        if grid_minor_step is not None:
            minor_xticks = np.arange(
                bottom_left_corner[0],
                top_right_corner[0] + 0.5 * grid_minor_step,
                grid_minor_step
            )
            minor_yticks = np.arange(
                bottom_left_corner[1],
                top_right_corner[1] + 0.5 * grid_minor_step,
                grid_minor_step
            )
            ax.set_xticks(minor_xticks, minor=True)
            ax.set_yticks(minor_yticks, minor=True)
            ax.grid(which='minor', color='orange', alpha=0.1)

        ax.set_xlim(bottom_left_corner[0], top_right_corner[0])
        ax.set_ylim(bottom_left_corner[1], top_right_corner[1])

        self.fig = fig
        self.ax = ax
        self.title = None
        self.elements: list[ElementBase] = []
        self.v_anchor: float = 0.0  # Y-axis elevation for 3D export (set from YAML)
        # Layers to draw (2D) and export (3D), see floor_planner.layers; default = everything
        self.layers = FloorPlanLayers()
        # False = no 3D export of this floor plan (set from YAML)
        self.export_3d: bool = True

    def add_title(
            self, text: str, font_size: int, rel_x: float = 0.5, rel_y: float = 0.95, **kwargs
    ) -> None:
        """
        Add title to the floor plan.

        :param text:
            title text
        :param font_size:
            font size
        :param rel_x:
            relative horizontal position of the text center;
            a float between 0 and 1;
            value of 0 corresponds to the left edge and value of 1 corresponds to the right edge
        :param rel_y:
            relative vertical position of the text center;
            a float between 0 and 1;
            value of 0 corresponds to the bottom edge and value of 1 corresponds to the top edge
        :return:
            None
        """
        self.fig.text(
            rel_x, rel_y, text,
            horizontalalignment='center', transform=self.fig.transFigure, size=font_size, **kwargs
        )
        self.title = text

    def add_element(self, element: ElementBase) -> None:
        """
        Add element.

        :param element:
            element to be added
        :return:
            None
        """
        self.elements.append(element)

    def draw_elements(self) -> None:
        """
        Draw elements added by add_element method.

        :param elements:
            None
        :return:
            None
        """
        print (f"Drawing floor plan {self.title} elements...")

        layers_2d = self.layers.layers_2d
        self._print_excluded_layers(layers_2d)
        if layers_2d is None:
            for element in self.elements:
                element.draw(self.ax)
            return

        for element in self.get_drawn_elements():
            before = set(self.ax.get_children())
            element.draw(self.ax)
            drawn = [artist for artist in self.ax.get_children() if artist not in before]
            spec = None if self._is_container(element) else layers_2d[element.get_layer()]
            apply_layer(drawn, spec)

    @staticmethod
    def _is_container(element: ElementBase) -> bool:
        """Group and Room do not belong to a layer."""
        return getattr(element, 'IS_CONTAINER', False)

    def _elements_on(self, layer_names) -> list[ElementBase]:
        """All elements if ``layer_names`` is None, else containers and the elements on those layers."""
        if layer_names is None:
            return list(self.elements)
        return [element for element in self.elements
                if self._is_container(element) or element.get_layer() in layer_names]

    def excluded_layers(self, layer_names) -> list[str]:
        """
        Layers that elements of this floor plan are on but that ``layer_names`` does not list.

        :param layer_names:
            the layers drawn (``layers.2d``) or exported (``layers.3d``); None = no filtering
        :return:
            sorted layer names; empty if nothing is filtered out
        """
        if layer_names is None:
            return []
        used = {element.get_layer() for element in self.elements if not self._is_container(element)}
        return sorted(used - set(layer_names))

    def _print_excluded_layers(self, layer_names) -> None:
        """Tell which layers of this floor plan are left out of the 2D drawing / 3D export."""
        for name in self.excluded_layers(layer_names):
            print(f"    Elements of layer '{name}' not included")

    def get_drawn_elements(self) -> list[ElementBase]:
        """Elements drawn in 2D (``layers.2d``)."""
        return self._elements_on(self.layers.layers_2d)

    def get_exported_elements(self) -> list[ElementBase]:
        """Elements exported to 3D (``layers.3d``); only they cut openings in the exported walls."""
        return self._elements_on(self.layers.layers_3d)

    def draw_report(
            self, 
            anchor_point: tuple[float, float],
            areas: bool = False,
            total_area: bool = False,
            notes: list[str] = None,
            fontsize: int = 11
    ) -> None:
        """
        Draw a report at the specified location on the floor plan.
        
        :param anchor_point:
            (x, y) coordinates where report should be drawn
        :param areas:
            if True, list all rooms with their areas
        :param total_area:
            if True, display sum of all room areas
        :param notes:
            optional list of note strings to display at the top of report
        :param fontsize:
            font size for the report text
        :return:
            None
        """
        x, y = anchor_point
        line_height = 0.3 * fontsize /11 # Spacing between lines
        row_width = fontsize/4
        current_y = y
        room_list_y = y
        font_size = fontsize
        
        # Draw notes first
        if notes:
            for note in notes:
                self.ax.text(
                    x, current_y, note,
                    fontsize=font_size,
                    verticalalignment='top',
                    horizontalalignment='left',
                    style='italic'
                )
                current_y -= line_height
            
            # Add extra spacing after notes
            current_y -= line_height * 0.5
            room_list_y = current_y
        
        # Get all Room elements
        rooms = [elem for elem in self.elements if isinstance(elem, Room)]
        
        # Filter rooms that have labels
        all_labeled_rooms = [room for room in rooms if room.label]

        # Grouped iteration over labeled rooms, the grouping element is room's purpose
        # (lists keep the declaration order, so the output is the same in every run)
        purposed_room_group = defaultdict(list)
        for lroom in all_labeled_rooms:
            purposed_room_group[lroom.purpose].append(lroom)

        for purpose, labeled_rooms in purposed_room_group.items():
            title = f"{purpose if purpose is not None else 'Other'} room areas:"
            current_y = room_list_y
            # Draw room areas
            if areas and labeled_rooms:
                # Header
                self.ax.text(
                    x, current_y, title,
                    fontsize=font_size + 1,
                    verticalalignment='top',
                    horizontalalignment='left',
                    weight='bold'
                )
                current_y -= line_height
                
                # List each room
                for room in labeled_rooms:
                    #print (f"Room: {room.label}, {room.purpose}" )
                    self.ax.text(
                        x, current_y, f"  • {room.label}:",
                        fontsize=font_size,
                        verticalalignment='top',
                        horizontalalignment='left'
                    )
                    self.ax.text(
                        x + row_width*0.9, current_y, f"{room.inner_area:.2f}m²",
                        fontsize=font_size,
                        verticalalignment='top',
                        horizontalalignment='right'
                    )

                    current_y -= line_height
                
                # Add spacing before total
                current_y -= line_height * 0.3
            
            # Draw total area
            if total_area and labeled_rooms:
                total = sum(room.inner_area for room in labeled_rooms)
                total_text = f"Total Area: {total:.2f} m²"
                self.ax.text(
                    x, current_y, total_text,
                    fontsize=font_size + 1,
                    verticalalignment='top',
                    horizontalalignment='left',
                    weight='bold'
                )
            # increase x so next group is next row
            x += row_width
    
    def export_to_gltf(
            self,
            output_dir: str | Path,
            filename: str = "floor_plan_3d.gltf",
            v_anchor: float | None = None,
            yaml_dirs: list[Path] | None = None,
    ) -> Path:
        """
        Export floor plan to glTF 2.0 format for 3D visualization.
        
        Creates a glTF file with:
        - External model references (from models/ directory)
        - Transform hierarchy (placement × normalization)
        - Materials and textures
        
        Args:
            output_dir: Directory to write glTF files and textures
            filename: Output filename (default: floor_plan_3d.gltf)
            yaml_dirs: Folders of the project's YAML files; textures named in
                       YAML are searched relative to them first
        
        Returns:
            Path to exported glTF file
        
        Example:
            >>> floor_plan.export_to_gltf("output/3d", "my_floor_plan.gltf")
        """
        from floor_planner.gltf_exporter import export_floor_plan_to_gltf
        
        output_path = export_floor_plan_to_gltf(
            elements=self.get_exported_elements(),
            output_dir=Path(output_dir),
            filename=filename,
            v_anchor=self.v_anchor if v_anchor is None else v_anchor,
            yaml_dirs=yaml_dirs
        )
        
        print(f"Exported glTF file: {output_path}")
        self._print_excluded_layers(self.layers.layers_3d)
        return output_path
