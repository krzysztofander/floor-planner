"""
Shared pytest configuration: the explicit list of scene projects, scene copying
and the reset of process-wide state. The command-line options are defined in the
repository-root conftest.py.

See docs/features/pytest-regression-suite.md.
"""

import shutil
from dataclasses import dataclass
from pathlib import Path

import pytest

from floor_planner.state import reset_global_state


REPO_ROOT = Path(__file__).resolve().parent.parent
GOLDEN_DIR = REPO_ROOT / 'tests' / 'golden'

# Scene projects run by the scene tests (the configs the Makefile builds, plus test-only scenes).
# Listed explicitly on purpose; automatic discovery may come later.
SCENES = [
    # room templates
    'examples/templates/rooms/room_north/project_main.yml',
    'examples/templates/rooms/room_south/project_main.yml',
    'examples/templates/rooms/room_east/project_main.yml',
    'examples/templates/rooms/room_west/project_main.yml',
    'examples/templates/rooms/play_with_doors/project_main.yml',
    # group templates
    'examples/templates/groups/group_east/project_main.yml',
    'examples/templates/groups/group_template_demo/project_main.yml',
    # elements, furniture, simple
    'examples/elements/all_elements.yml',
    'examples/elements/furniture_demo.yml',
    'examples/simple_no_rooms/simple_floor_plan.yml',
    # landscaping
    'examples/landscaping/vegetation_demo.yml',
    'examples/landscaping/hardscape_demo.yml',
    'examples/landscaping/water_features_demo.yml',
    'examples/landscaping/structures_demo.yml',
    'examples/landscaping/site_plan_complete.yml',
    # roofs, glass structures
    'examples/roofs/roofs_demo.yml',
    'examples/glass_structures/glass_demo.yml',
    # 3D visualization
    'examples/3d_visualization/simple_room.yml',
    'examples/3d_visualization/furnished_room.yml',
    'examples/3d_visualization/face_textures_demo.yml',
    # tests
    'tests/test_invisible_openings/project_main.yml',
    'tests/doors_and_windows/doors_and_windows.yml',
    'tests/test_shadows_with_opened_walls/project_main.yml',
    'tests/test_wall_openings/project_main.yml',
    'tests/play_with_doors/project_main.yml',
    'tests/all_elements/project_main.yml',
    'tests/play_with_double_doors/project_main.yml',
    'tests/vege/project_main.yml',
    'tests/play_with_textures/face_textures_test.yml',
    'tests/play_with_textures/face_textures_walls_test.yml',
]

# Scenes whose 3D output (glTF) is also compared with a golden summary in tests/golden/3d/.
# A subset of SCENES, picked one by one once a scene is stable; each needs a visualisation_dir.
# Avoid scenes that use models from models/models_3rd_party (not available everywhere).
GOLDEN_3D_SCENES = [
    'tests/play_with_textures/face_textures_test.yml',
    'tests/play_with_textures/face_textures_walls_test.yml',
]

# Generated outputs that are not copied with a scene (inputs only)
_OUTPUT_PATTERNS = ('*.png', '*.pdf', '*.gltf', '*.bin', '*.md', 'camera.json')


def scene_id(scene: str) -> str:
    """Scene id: config path relative to the repository, without suffix."""
    return str(Path(scene).with_suffix(''))


@dataclass
class GoldenOptions:
    """How golden files are used."""

    update: bool


def pytest_generate_tests(metafunc):
    """Parametrize tests that take ``scene`` with the (filtered) scene list."""
    if 'scene' in metafunc.fixturenames:
        filters = metafunc.config.getoption('--scene')
        scenes = [s for s in SCENES if not filters or any(f in s for f in filters)]
        metafunc.parametrize('scene', scenes, ids=[scene_id(s) for s in scenes])


@pytest.fixture
def golden_options(request) -> GoldenOptions:
    return GoldenOptions(update=request.config.getoption('--update-golden'))


@pytest.fixture(autouse=True)
def _reset_floor_planner_state():
    """Reset process-wide floor_planner state before and after every test."""
    reset_global_state()
    yield
    reset_global_state()


def copy_scene(scene: str, destination: Path) -> Path:
    """
    Copy a scene's folder (its config and included files, without generated
    outputs) to ``destination``, so the run writes nothing into the repository.

    :return:
        path of the copied config file
    """
    source = REPO_ROOT / scene
    target_dir = destination / source.parent.name
    shutil.copytree(source.parent, target_dir, ignore=shutil.ignore_patterns(*_OUTPUT_PATTERNS),
                    ignore_dangling_symlinks=True)
    return target_dir / source.name
