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
            visualisation_dir: str | None = None
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
        :return:
            freshly created instance of `Project` class
        """
        self.floor_plans = floor_plans
        self.dpi = dpi
        self.visualisation_dir = visualisation_dir

    def render_to_pdf(self, output_path: str) -> None:
        """
        Render floor plans to single PDF file with each floor plan on its page.

        :param output_path:
            path to output file
        :return:
            None
        """
        with PdfPages(output_path) as pdf:
            for floor_plan in self.floor_plans:
                pdf.savefig(floor_plan.fig, dpi=self.dpi)

    def render_to_png(self, output_dir: str) -> None:
        """
        Render floor plans to separate PNG files from the same directory.

        :param output_dir:
            path to output directory
        :return:
            None
        """
        if not os.path.exists(output_dir):
            os.mkdir(output_dir)
        for i, floor_plan in enumerate(self.floor_plans):
            title = floor_plan.title or f"{i}.png"
            if not title.endswith('png'):
                title += '.png'
            floor_plan.fig.savefig(os.path.join(output_dir, title), dpi=self.dpi)
    
    def export_to_gltf(self) -> None:
        """
        Export floor plans to glTF 2.0 format for 3D visualization.
        
        Only exports if visualisation_dir is set. Each floor plan is exported to a separate
        glTF file in the visualisation_dir directory.
        
        Creates glTF files with:
        - External model references (from models/ directory)
        - Procedural geometry (walls, doors, windows)
        - Transform hierarchy (placement × normalization)
        - Materials and textures
        
        :return:
            None
        """
        if self.visualisation_dir is None:
            # No visualisation directory specified, skip 3D export
            return
        
        output_dir = Path(self.visualisation_dir)
        
        print(f"\n{'=' * 80}")
        print("3D glTF 2.0 Export")
        print(f"{'=' * 80}")
        print(f"Output directory: {output_dir}")
        print(f"Floor plans: {len(self.floor_plans)}")
        print()
        
        for i, floor_plan in enumerate(self.floor_plans):
            try:
                # Generate filename from floor plan title
                if floor_plan.title:
                    # Sanitize title for filename
                    filename = floor_plan.title.replace(' ', '_').replace('/', '_')
                    if not filename.endswith('.gltf'):
                        filename += '.gltf'
                else:
                    filename = f"floor_plan_{i}.gltf"
                
                output_path = floor_plan.export_to_gltf(output_dir, filename, v_anchor=floor_plan.v_anchor)
                print(f"  ✓ Exported: {output_path.name}")
            except Exception as e:
                print(f"  ✗ Error exporting floor plan '{floor_plan.title}': {e}")
                import traceback
                traceback.print_exc()
        
        print(f"{'=' * 80}")
        print("glTF export complete")
        print(f"{'=' * 80}\n")
