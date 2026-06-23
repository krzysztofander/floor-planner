"""
Render project.

Author: Nikolay Lysenko
"""


import argparse
import copy
import json
from pathlib import Path
from collections import defaultdict

import yaml

from floor_planner import elements
from floor_planner.floor_plan import FloorPlan
from floor_planner.project import Project
from floor_planner.markdown_report import generate_elements_report
from floor_planner.variables import validate_constants, resolve_constants, resolve_element_params

def load_reusable_elements(reusable_elements_config: dict, config_dir: Path) -> dict:
    """
    Load reusable elements from configuration, including external files.

    :param reusable_elements_config:
        reusable_elements section from main config, can contain inline definitions
        or file references (string values pointing to external YAML files)
    :param config_dir:
        directory containing the main config file (for resolving relative paths)
    :return:
        dictionary of reusable element sets with all external files loaded
    """
    if not reusable_elements_config:
        return {}

    loaded_elements = {}

    for set_name, content in reusable_elements_config.items():
        if isinstance(content, str):
            # It's a file reference - load the external file
            file_path = config_dir / content

            if not file_path.exists():
                raise FileNotFoundError(f"Reusable elements file not found: {file_path}")

            print(f"Loading reusable elements '{set_name}' from {content}")

            with open(file_path) as ext_file:
                external_content = yaml.load(ext_file, Loader=yaml.FullLoader)

            # The external file should contain a list of element definitions
            if not isinstance(external_content, list):
                raise ValueError(
                    f"External reusable elements file '{content}' must contain a list of elements, "
                    f"got {type(external_content).__name__}"
                )

            loaded_elements[set_name] = external_content
        elif isinstance(content, list):
            # It's an inline definition - use as-is
            loaded_elements[set_name] = content
        else:
            raise ValueError(
                f"Reusable element set '{set_name}' must be either a list of elements "
                f"or a string (file path), got {type(content).__name__}"
            )

    return loaded_elements


def _write_camera_json(
        camera_settings: dict | None,
        default_layout: dict,
        output_dir: Path,
) -> None:
    """
    Write camera.json with the initial camera position and look-at target for
    the 3D viewer.

    Defaults are derived from ``default_layout`` so the camera is placed just
    outside (south of) the floor plan, centred horizontally, at eye height,
    looking straight into the scene.

    :param camera_settings:
        Optional dict from YAML ``project.visualisation_camera``.  Recognised
        keys: ``location`` and ``look_at``, each a 3-element ``[x, y, z]`` list.
    :param default_layout:
        The ``default_layout`` section of the YAML (used to compute defaults).
    :param output_dir:
        Destination directory (``visualisation_dir``).  File is written as
        ``<output_dir>/camera.json``.
    """
    blc = default_layout.get('bottom_left_corner', [0, 0])
    trc = default_layout.get('top_right_corner', [10, 10])

    # Default: centred horizontally, eye height, 2 m south of the bottom edge
    default_loc = [
        (blc[0] + trc[0]) / 2.0,   # X: horizontal midpoint of floor plan
        1.6,                         # Y: standing eye height (metres)
        float(blc[1]) - 2.0,        # Z: 2 m south of bottom_left_corner.y
    ]
    # look_at: same position but Z = 0 (camera looks straight along Z axis)
    default_lat = [default_loc[0], default_loc[1], 0.0]

    def _to_xyz(raw, fallback: list) -> list:
        """Accept [x,y,z] list or {x:,y:,z:} dict; fall back to *fallback*."""
        if isinstance(raw, (list, tuple)) and len(raw) >= 3:
            return [float(raw[0]), float(raw[1]), float(raw[2])]
        if isinstance(raw, dict):
            return [
                float(raw.get('x', fallback[0])),
                float(raw.get('y', fallback[1])),
                float(raw.get('z', fallback[2])),
            ]
        return list(map(float, fallback))

    cam = camera_settings or {}
    location = _to_xyz(cam.get('location', default_loc), default_loc)
    look_at  = _to_xyz(cam.get('look_at',  default_lat), default_lat)

    camera_data = {
        # -------------------------------------------------------------------
        # _notes is for tooling / AI agents integrating this into a 3D player.
        # It is safe to ignore at runtime.
        # -------------------------------------------------------------------
        "_notes": {
            "description": (
                "Initial camera configuration for the 3D floor plan viewer. "
                "Auto-generated by the floor_planner tool from the "
                "'visualisation_camera' key in the project: YAML section."
            ),
            "coordinate_system": (
                "Right-handed, Y-up. "
                "X = East  (floor plan horizontal, matches YAML anchor_point[0]). "
                "Y = Up    (vertical; 1.6 m = standing eye height). "
                "Z = South (floor plan vertical, matches -YAML anchor_point[1]). "
                "All values are in metres."
            ),
            "how_to_use": (
                "On scene load: position the camera eye at 'location', then orient "
                "it so the camera looks toward 'look_at'. "
                "Both are world-space coordinates in metres. "
                "A simple implementation: "
                "camera.position = location; camera.lookAt(look_at)."
            ),
            "yaml_override_syntax": (
                "To customise, add to the project: section of your YAML config:\n"
                "  visualisation_camera:\n"
                "    location: [x, y, z]   # camera eye position in metres\n"
                "    look_at:  [x, y, z]   # point the camera looks at"
            ),
            "default_logic": (
                "location.x = (bottom_left_corner.x + top_right_corner.x) / 2  [horizontal centre]. "
                "location.y = 1.6  [eye height]. "
                "location.z = bottom_left_corner.y - 2  [2 m south of layout]. "
                "look_at = same x/y as location, z = 0  [looking straight into scene]."
            ),
        },
        "location": location,
        "look_at":  look_at,
        "bottom_left_corner":  list(map(float, blc)),
        "top_right_corner":    list(map(float, trc)),
        "grid_major_step":     float(default_layout.get('grid_major_step', 1)),
        "grid_minor_step":     float(default_layout.get('grid_minor_step', 0.1)),
    }

    out_path = output_dir / 'camera.json'
    with open(out_path, 'w', encoding='utf-8') as fh:
        json.dump(camera_data, fh, indent=2, ensure_ascii=False)
    print(f"  ✓ Written: camera.json")


def parse_cli_args() -> argparse.Namespace:
    """
    Parse arguments passed via Command Line Interface (CLI).

    :return:
        namespace with arguments
    """
    parser = argparse.ArgumentParser(description='Rendering of renovation project floor plans.')
    parser.add_argument(
        '-c', '--config_path', type=str, default=None, help='path to configuration file'
    )
    cli_args = parser.parse_args()
    return cli_args


def main() -> None:
    """Parse CLI arguments and run requested tasks."""
    cli_args = parse_cli_args()
    config_path = cli_args.config_path
    config_dir = Path(config_path).parent

    with open(config_path) as config_file:
        settings = yaml.load(config_file, Loader=yaml.FullLoader)

    # Reset ID counters for consistent IDs
    elements.reset_id_counters()

    # Load global vars (check both 'vars' and 'constants' for backwards compatibility)
    global_vars = settings.get('vars', settings.get('constants', {}))

    # Load default options (hierarchical structure)
    default_options = settings.get('default_options', {})

    # Remove element types with None values (from commented-out YAML properties)
    cleaned_options = {}
    for element_type, options in default_options.items():
        if options is not None and isinstance(options, dict):
            cleaned_options[element_type] = options
    default_options = cleaned_options

    # Set default options globally
    elements.set_element_options(default_options)

    elements_registry = elements.create_elements_registry()

    # Load reusable elements (including external files)
    reusable_elements = load_reusable_elements(
        settings.get('reusable_elements', {}),
        config_dir
    )

    # Track all elements for report
    all_elements = []
    # Track elements by ID for room creation
    elements_by_id = {}

    def _add_element(element_params, elements_registry, floor_plan, all_elements, elements_by_id, global_vars):
        """
        Add a single element (or container) to the floor plan.

        Container classes (those with IS_CONTAINER = True, e.g. Group and Room)
        are created via their create_from_params() classmethod.  All other
        element types are instantiated directly after variable resolution.
        """
        element_params = copy.deepcopy(element_params)
        element_type = element_params.get('type')
        element_class = elements_registry.get(element_type)
        if element_class is None:
            raise ValueError(f"Unknown element type: {element_type!r}")

        if getattr(element_class, 'IS_CONTAINER', False):
            container = element_class.create_from_params(
                element_params, elements_registry, floor_plan,
                all_elements, elements_by_id, global_vars
            )
            floor_plan.add_element(container)
            all_elements.append(container)
            elements_by_id[container.get_id()] = container
        else:
            element_params.pop('type')
            element_params = resolve_element_params(element_params, global_vars)
            element = element_class(**element_params)
            floor_plan.add_element(element)
            all_elements.append(element)
            elements_by_id[element.get_id()] = element

    floor_plans = []
    for floor_plan_params in settings['floor_plans']:
        # Merge floor plan options with defaults (floor plan options override defaults)
        floor_plan_options = floor_plan_params.get('options', {})
        if floor_plan_options:
            # Create a merged options dict
            merged_options = copy.deepcopy(default_options)
            for element_type, type_options in floor_plan_options.items():
                # Skip if type_options is None (all properties commented out in YAML)
                if type_options is None or not isinstance(type_options, dict):
                    continue
                # Ensure element_type exists in merged_options as a dict
                if element_type not in merged_options or not isinstance(merged_options.get(element_type), dict):
                    merged_options[element_type] = {}
                merged_options[element_type].update(type_options)
            # Apply merged options for this floor plan
            elements.set_element_options(merged_options)
        else:
            # Use default options
            elements.set_element_options(default_options)

        layout_params = floor_plan_params.get('layout') or settings['default_layout']
        floor_plan = FloorPlan(**layout_params)
        floor_plan.v_anchor = float(floor_plan_params.get('v_anchor', 0.0))
        title_params = floor_plan_params.get('title')
        if title_params:
            floor_plan.add_title(**title_params)
        for set_name in floor_plan_params.get('inherited_elements', []):
            for element_params in reusable_elements.get(set_name, []):
                _add_element(element_params, elements_registry, floor_plan, all_elements, elements_by_id, global_vars)
        for element_params in floor_plan_params.get('elements', []):
            _add_element(element_params, elements_registry, floor_plan, all_elements, elements_by_id, global_vars)
        floor_plan.draw_elements()

        # Draw report if specified
        report_params = floor_plan_params.get('report')
        if report_params:
            # Resolve anchor_point with constants if needed
            anchor_point = report_params.get('anchor_point', [0, 0])
            if isinstance(anchor_point, list):
                # Resolve constants in anchor_point
                anchor_point = resolve_constants(anchor_point, global_vars)

            floor_plan.draw_report(
                anchor_point=anchor_point,
                areas=report_params.get('areas', False),
                total_area=report_params.get('total_area', False),
                notes=report_params.get('notes', None),
                fontsize=report_params.get('fontsize', 11)
            )

        floor_plans.append(floor_plan)

    # Handle visualisation_dir option
    visualisation_dir = settings['project'].get('visualisation_dir')
    vis_dir_resolved = None
    if visualisation_dir is not None:
        vis_dir_path = config_dir / visualisation_dir
        if not vis_dir_path.exists():
            vis_dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created visualisation directory: {vis_dir_path}")
        vis_dir_resolved = str(vis_dir_path)

    project = Project(floor_plans, settings['project']['dpi'], vis_dir_resolved)
    pdf_path = settings['project'].get('pdf_file')
    if pdf_path is not None:
        pdf_path = config_dir / pdf_path
        project.render_to_pdf(str(pdf_path))
    png_path = settings['project'].get('png_dir')
    if png_path is not None:
        png_path = config_dir / png_path
        project.render_to_png(str(png_path))
    
    # Export 3D formats if visualisation_dir is set
    if vis_dir_resolved:
        project.export_to_gltf()  # glTF 2.0 (modern, feature-rich)
        # project.export_to_obj(config_dir)  # OBJ/MTL (legacy, commented out)

        # Write camera.json with initial viewer position
        _write_camera_json(
            settings['project'].get('visualisation_camera'),
            settings.get('default_layout', {}),
            vis_dir_path,
        )

    # Generate elements report
    report_path = Path(config_path).with_suffix(".md")
    generate_elements_report(all_elements, str(report_path))
    print(f"Elements report generated: {report_path}")


if __name__ == '__main__':
    main()
