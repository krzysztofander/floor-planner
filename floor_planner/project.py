"""
Combine all floor plans.

Author: Nikolay Lysenko
"""


import os
from pathlib import Path
from typing import Literal, Union

from matplotlib.backends.backend_pdf import PdfPages

from .floor_plan import FloorPlan


class Project:
    """Collection of floor plans."""

    def __init__(
            self,
            floor_plans: list[FloorPlan],
            dpi: Union[float, Literal["figure"]] = "figure",
            visualisation_dir: str | None = None,
            yaml_dirs: list[Path] | None = None
    ):
        """
        Initialize an instance.

        :param floor_plans:
            floor plans
        :param dpi:
            DPI (dots-per-inch), number of pixels per inch of space in output file
        :param visualisation_dir:
            optional directory for 3D visualization assets; if specified, acts as a switch
            to enable 3D asset generation in the future
        :param yaml_dirs:
            folders of the project's YAML files; textures named in YAML are
            searched relative to them first
        :return:
            freshly created instance of `Project` class
        """
        self.floor_plans = floor_plans
        self.floor_plan_names = [self.floor_plan_name(i, fp) for i, fp in enumerate(floor_plans)]
        for i, name in enumerate(self.floor_plan_names):
            first = self.floor_plan_names.index(name)
            if first != i:
                raise ValueError(f"Floor plans {first} and {i} have the same name {name!r}; "
                                 f"floor plan titles must be unique")
        self.dpi = dpi
        self.visualisation_dir = visualisation_dir
        self.yaml_dirs = yaml_dirs

    @staticmethod
    def floor_plan_name(index: int, floor_plan: FloorPlan) -> str:
        """
        Name of a floor plan in output paths: its title with spaces and slashes
        replaced by underscores, or ``floor_plan_<index>`` without a title.
        """
        if floor_plan.title:
            return floor_plan.title.replace(' ', '_').replace('/', '_')
        return f"floor_plan_{index}"

    def render_to_pdf(self, output_path: str) -> Path:
        """
        Render floor plans to single PDF file with each floor plan on its page.

        :param output_path:
            path to output file
        :return:
            path of the written PDF file
        """
        with PdfPages(output_path) as pdf:
            for floor_plan in self.floor_plans:
                pdf.savefig(floor_plan.fig, dpi=self.dpi)
        return Path(output_path)

    def render_to_png(self, output_dir: str) -> list[Path]:
        """
        Render floor plans to separate PNG files from the same directory.

        :param output_dir:
            path to output directory
        :return:
            paths of the written PNG files, in floor-plan order
        """
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        written = []
        for i, floor_plan in enumerate(self.floor_plans):
            title = floor_plan.title or f"{i}.png"
            if not title.endswith('png'):
                title += '.png'
            png_path = Path(output_dir) / title
            floor_plan.fig.savefig(png_path, dpi=self.dpi)
            written.append(png_path)
        return written
    
    def export_to_gltf(self) -> list[Path]:
        """
        Export floor plans to glTF 2.0 format for 3D visualization.
        
        Only exports if visualisation_dir is set. Each floor plan is exported to its own
        folder ``<visualisation_dir>/<name>/`` as ``<name>.gltf`` (with its ``.bin`` and
        ``textures/``), ``name`` from ``floor_plan_name()``. A floor plan with a ``layers.3d``
        section exports only the elements of those layers; one with ``export_3d: false``
        is not exported.
        
        Creates glTF files with:
        - External model references (from models/ directory)
        - Procedural geometry (walls, doors, windows)
        - Transform hierarchy (placement × normalization)
        - Materials and textures
        
        An error while exporting a floor plan is printed and re-raised.
        
        :return:
            paths of the written glTF files, in floor-plan order (floor plans with
            ``export_3d: false`` are skipped; empty if no visualisation_dir is set)
        """
        if self.visualisation_dir is None:
            # No visualisation directory specified, skip 3D export
            return []
        
        output_dir = Path(self.visualisation_dir)
        
        print(f"\n{'=' * 80}")
        print("3D glTF 2.0 Export")
        print(f"{'=' * 80}")
        print(f"Output directory: {output_dir}")
        print(f"Floor plans: {len(self.floor_plans)}")
        print()
        
        written = []
        for i, floor_plan in enumerate(self.floor_plans):
            if not floor_plan.export_3d:
                print(f"  - Skipped (export_3d: false): {self.floor_plan_names[i]}")
                continue
            try:
                name = self.floor_plan_names[i]
                output_path = floor_plan.export_to_gltf(output_dir / name, f"{name}.gltf",
                                                        v_anchor=floor_plan.v_anchor,
                                                        yaml_dirs=self.yaml_dirs)
                print(f"  ✓ Exported: {output_path.name}")
                written.append(Path(output_path))
            except Exception as e:
                print(f"  ✗ Error exporting floor plan '{floor_plan.title}': {e}")
                raise
        
        print(f"{'=' * 80}")
        print("glTF export complete")
        print(f"{'=' * 80}\n")
        return written
