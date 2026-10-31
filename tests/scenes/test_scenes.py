"""
Scene tests: run each YAML scene project end to end and check the result.

- invariants of the run and of every glTF (docs/features/pytest-regression-suite.md)
- 2D: every rendered PNG (at 100 dpi) against tests/golden/2d/<scene_id>/
- 3D, for scenes in GOLDEN_3D_SCENES: per-node summary of every glTF against
  tests/golden/3d/<scene_id>/<gltf name>.json

Write/refresh golden files with ``--update-golden``.
"""

import json
import shutil
from pathlib import Path

import pytest
import yaml
from matplotlib.testing.compare import compare_images

from conftest import GOLDEN_3D_SCENES, GOLDEN_DIR, copy_scene, scene_id
from floor_planner.runner import RunResult, run_project
from scenes.gltf_checks import check_gltf_invariants, compare_summaries, gltf_summary, write_summary


TEST_DPI = 100
IMAGE_TOLERANCE = 2.0  # RMS difference allowed by compare_images


def check_run_invariants(config_path: Path, result: RunResult) -> None:
    """(a) the run produced one PNG / glTF (with its .bin) per floor plan where configured."""
    settings = yaml.load(config_path.read_text(), Loader=yaml.FullLoader)
    floor_plans = len(settings['floor_plans'])
    project = settings['project']

    if project.get('png_dir') is not None:
        assert len(result.png_files) == floor_plans, \
            f"expected {floor_plans} PNG files, got {[p.name for p in result.png_files]}"
        for png in result.png_files:
            assert png.exists(), f"PNG {png} was not written"

    if project.get('visualisation_dir') is not None:
        assert len(result.gltf_files) == floor_plans, \
            f"expected {floor_plans} glTF files, got {[p.name for p in result.gltf_files]}"
        for gltf in result.gltf_files:
            assert gltf.exists(), f"glTF {gltf} was not written"
            for buffer in json.loads(gltf.read_text()).get('buffers', []):
                if not buffer['uri'].startswith('data:'):
                    assert (gltf.parent / buffer['uri']).exists(), f"{gltf.name}: buffer {buffer['uri']} missing"


def _repo_relative(path: Path) -> Path:
    return path.relative_to(GOLDEN_DIR.parent.parent)


def image_vs_golden(actual: Path, golden: Path, update: bool) -> str | None:
    """Compare a rendered PNG with its golden image (or write it); return a problem or None."""
    if update:
        golden.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(actual, golden)
        return None
    if not golden.exists():
        return f"no golden image {_repo_relative(golden)}; run pytest with --update-golden"
    failure = compare_images(str(golden), str(actual), tol=IMAGE_TOLERANCE, in_decorator=True)
    if failure is not None:
        return (f"2D: {actual.name} differs from golden image (RMS {failure['rms']:.2f} > {IMAGE_TOLERANCE}); "
                f"diff image: {failure['diff']}")
    return None


def summary_vs_golden(gltf: Path, golden: Path, update: bool) -> str | None:
    """Compare the 3D summary of a glTF with its golden JSON (or write it); return a problem or None."""
    summary = gltf_summary(gltf)
    if update:
        write_summary(summary, golden)
        return None
    if not golden.exists():
        return f"no golden 3D summary {_repo_relative(golden)}; run pytest with --update-golden"
    diffs = compare_summaries(json.loads(golden.read_text()), summary)
    if diffs:
        listed = '\n    '.join(diffs[:15])
        more = f"\n    ... and {len(diffs) - 15} more" if len(diffs) > 15 else ''
        return f"3D: {gltf.name} differs from {_repo_relative(golden)} in {len(diffs)} places:\n    {listed}{more}"
    return None


@pytest.mark.slow
def test_scene(scene, tmp_path, golden_options):
    config = copy_scene(scene, tmp_path)
    result = run_project(config, dpi=TEST_DPI)          # any error raises and fails the test

    check_run_invariants(config, result)
    for gltf in result.gltf_files:
        check_gltf_invariants(gltf)

    sid = scene_id(scene)
    problems = []
    for png in result.png_files:
        problems.append(image_vs_golden(png, GOLDEN_DIR / '2d' / sid / png.name, golden_options.update))

    if scene in GOLDEN_3D_SCENES:
        assert result.gltf_files, f"{scene} is in GOLDEN_3D_SCENES but produced no glTF"
        for gltf in result.gltf_files:
            problems.append(summary_vs_golden(gltf, GOLDEN_DIR / '3d' / sid / f'{gltf.stem}.json',
                                              golden_options.update))

    problems = [p for p in problems if p]
    if problems:
        pytest.fail('\n'.join(problems), pytrace=False)
