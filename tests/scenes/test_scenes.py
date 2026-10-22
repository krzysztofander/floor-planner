"""
Scene tests: run each YAML scene project end to end and check the result.

- invariants of the run and of every glTF (docs/features/pytest-regression-suite.md)
- 2D: every rendered PNG (at 100 dpi) against tests/golden/2d/<scene_id>/
- 3D (phase 2, only with --golden-3d): per-mesh summary against tests/golden/3d/<scene_id>/

Write/refresh golden files with ``--update-golden``.
"""

import json
import shutil
from pathlib import Path

import pytest
import yaml
from matplotlib.testing.compare import compare_images

from conftest import GOLDEN_DIR, copy_scene, scene_id
from floor_planner.runner import RunResult, run_project
from scenes.gltf_checks import check_gltf_invariants, compare_summaries, gltf_summary


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


def assert_image_matches_golden(actual: Path, golden: Path, update: bool) -> None:
    """Compare a rendered PNG with its golden image (or write the golden image)."""
    if update:
        golden.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(actual, golden)
        return
    assert golden.exists(), f"no golden image {golden.relative_to(GOLDEN_DIR.parent.parent)}; run pytest with --update-golden"
    failure = compare_images(str(golden), str(actual), tol=IMAGE_TOLERANCE, in_decorator=True)
    if failure is not None:
        pytest.fail(
            f"{actual.name} differs from golden image (RMS {failure['rms']:.2f} > {IMAGE_TOLERANCE}); "
            f"diff image: {failure['diff']}"
        )


def assert_summary_matches_golden(summary: dict, golden: Path, update: bool) -> None:
    """Compare a glTF summary with its golden JSON (or write it)."""
    if update:
        golden.parent.mkdir(parents=True, exist_ok=True)
        golden.write_text(json.dumps(summary, indent=1, sort_keys=True))
        return
    assert golden.exists(), f"no golden summary {golden}; run pytest with --golden-3d --update-golden"
    diffs = compare_summaries(json.loads(golden.read_text()), summary)
    assert not diffs, f"{golden.name}: {len(diffs)} differences, e.g. " + "; ".join(diffs[:10])


@pytest.mark.slow
def test_scene(scene, tmp_path, golden_options):
    config = copy_scene(scene, tmp_path)
    result = run_project(config, dpi=TEST_DPI)          # any error raises and fails the test

    check_run_invariants(config, result)
    for gltf in result.gltf_files:
        check_gltf_invariants(gltf)

    sid = scene_id(scene)
    for png in result.png_files:
        assert_image_matches_golden(png, GOLDEN_DIR / '2d' / sid / png.name, golden_options.update)

    if golden_options.compare_3d:                       # phase 2, off by default
        for gltf in result.gltf_files:
            assert_summary_matches_golden(gltf_summary(gltf), GOLDEN_DIR / '3d' / sid / f'{gltf.stem}.json',
                                          golden_options.update)
