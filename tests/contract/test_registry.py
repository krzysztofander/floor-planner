"""
Contract tests: rules every registered element type (and the scene list) must follow.

See docs/features/pytest-regression-suite.md ("Contract tests").
"""

import inspect
import re
from pathlib import Path

import pytest
import yaml

from conftest import GOLDEN_3D_SCENES, REPO_ROOT, SCENES
from floor_planner import elements
from floor_planner.elements.element import ElementBase
from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.face_textures import FaceTextures
from floor_planner.geometry_3d import RectangularGeometry3D
from floor_planner.texture_manager import TextureManager


REGISTRY = elements.create_elements_registry()

# Types positioned by their points; their anchor point is derived, not a parameter
NO_ANCHOR_POINT = {'line', 'polygon', 'ground_cable'}
# Procedural 3D types that intentionally have no .mtl (colour only)
COLOUR_ONLY = set()
# Elements that inherit RectangularGeometry3D but replace the box geometry
NOT_A_BOX = {'Greenhouse'}


def _all_subclasses(cls):
    for sub in cls.__subclasses__():
        yield sub
        yield from _all_subclasses(sub)


def _parameters(cls) -> dict:
    return inspect.signature(cls.__init__).parameters


def _is_plain_box(cls) -> bool:
    return isinstance(cls, type) and issubclass(cls, RectangularGeometry3D) and cls.__name__ not in NOT_A_BOX


ELEMENT_CLASSES = sorted(set(_all_subclasses(ElementBase)), key=lambda c: (c.__module__, c.__name__))
BOX_TYPES = sorted(t for t, c in REGISTRY.items() if _is_plain_box(c))
PROCEDURAL_3D_TYPES = sorted(
    t for t, c in REGISTRY.items()
    if hasattr(c, 'generate_vertices_and_indices') and not issubclass(c, ExternalModelElement)
)
EXTERNAL_MODEL_TYPES = sorted(t for t, c in REGISTRY.items() if issubclass(c, ExternalModelElement))


@pytest.mark.parametrize('cls', ELEMENT_CLASSES, ids=lambda c: c.__name__)
def test_no_var_kwargs(cls):
    """No element constructor accepts arbitrary keyword arguments."""
    if '__init__' not in cls.__dict__:
        pytest.skip('inherits __init__')
    var_keyword = [p.name for p in _parameters(cls).values() if p.kind == p.VAR_KEYWORD]
    assert not var_keyword, f"{cls.__name__}.__init__ takes **{var_keyword[0]}"


@pytest.mark.parametrize('type_name', sorted(REGISTRY))
def test_common_parameters(type_name):
    """Every registered type takes id and label, and anchor_point unless positioned by points."""
    params = _parameters(REGISTRY[type_name])
    required = {'id', 'label'} | (set() if type_name in NO_ANCHOR_POINT else {'anchor_point'})
    missing = required - set(params)
    assert not missing, f"{type_name} does not take {sorted(missing)}"


@pytest.mark.parametrize('type_name', BOX_TYPES)
def test_box_takes_textures(type_name):
    """Box elements take the per-face `textures` structure and not `texture_scale`."""
    params = _parameters(REGISTRY[type_name])
    assert 'textures' in params, f"{type_name} does not take textures"
    assert 'texture_scale' not in params, f"{type_name} still takes texture_scale"


@pytest.mark.parametrize('type_name', BOX_TYPES)
def test_default_textures_valid(type_name):
    """Class-level `_default_textures` pass validation."""
    cls = REGISTRY[type_name]
    FaceTextures.from_yaml(cls._default_textures, f"{cls.__name__}._default_textures")


@pytest.mark.parametrize('type_name', PROCEDURAL_3D_TYPES)
def test_procedural_type_has_mtl(type_name):
    """Every procedural 3D type has models/procedural/<type>/<type>.mtl (or is colour-only)."""
    if type_name in COLOUR_ONLY:
        pytest.skip('colour only')
    assert TextureManager().get_procedural_mtl(type_name) is not None, \
        f"missing models/procedural/{type_name}/{type_name}.mtl"


def _repository_mtl_files() -> list[Path]:
    models = REPO_ROOT / 'models'
    files = list((models / 'procedural').glob('*/*.mtl'))
    files += [p for p in models.glob('*/model.mtl')]
    files += [p for p in (models / 'stubs').glob('*/model.mtl')]
    return sorted(files)


@pytest.mark.parametrize('mtl_path', _repository_mtl_files(), ids=lambda p: str(p.relative_to(REPO_ROOT)))
def test_texture_references_resolve(mtl_path):
    """Every map_Kd in the repository's .mtl files resolves (next to the .mtl, then textures/)."""
    texture_manager = TextureManager()
    missing = []
    for line in mtl_path.read_text().splitlines():
        match = re.match(r'\s*map_Kd\s+(.+?)\s*$', line)
        if match and texture_manager.find_texture(match.group(1), mtl_path.parent) is None:
            missing.append(match.group(1))
    assert not missing, f"{mtl_path.name}: unresolved map_Kd {missing}"


@pytest.mark.parametrize('type_name', EXTERNAL_MODEL_TYPES)
def test_external_model_folder_exists(type_name):
    """Every external model type finds a model folder (models/, local/, models_3rd_party/ or stubs/)."""
    cls = REGISTRY[type_name]
    key = cls._registry_key
    if key is None:
        pytest.skip('no _registry_key (abstract base)')
    base = cls._get_default_models_dir()
    candidates = [base] + [base / sub for sub in cls._MODELS_SUBDIRS]
    found = [d / key for d in candidates if any((d / key / name).exists() for name in cls._MODEL_FILE_NAMES)]
    if cls._requires_external_model:
        assert found, f"{type_name}: no model folder '{key}' in {[str(d) for d in candidates]}"


@pytest.mark.parametrize('scene_path', SCENES)
def test_scene_list_entry_valid(scene_path):
    """Every listed scene exists and is a project config (has floor_plans)."""
    path = REPO_ROOT / scene_path
    assert path.exists(), f"listed scene {scene_path} does not exist"
    settings = yaml.load(path.read_text(), Loader=yaml.FullLoader)
    assert isinstance(settings, dict) and 'floor_plans' in settings, f"{scene_path} has no floor_plans"


@pytest.mark.parametrize('scene_path', GOLDEN_3D_SCENES)
def test_golden_3d_scene_entry_valid(scene_path):
    """Every 3D golden scene is also a listed scene and exports 3D (has a visualisation_dir)."""
    assert scene_path in SCENES, f"{scene_path} is in GOLDEN_3D_SCENES but not in SCENES"
    settings = yaml.load((REPO_ROOT / scene_path).read_text(), Loader=yaml.FullLoader)
    assert settings.get('project', {}).get('visualisation_dir'), f"{scene_path} has no project.visualisation_dir"
