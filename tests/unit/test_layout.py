"""Unit tests: a floor plan's `layout` overrides single keys of `default_layout` (floor_planner/runner.py)."""

import pytest
import yaml

from floor_planner.constants import METERS_PER_INCH
from floor_planner.runner import run_project


def _run(tmp_path, floor_plans):
    config = {
        'project': {'dpi': 50},
        'default_layout': {'bottom_left_corner': [0, 0], 'top_right_corner': [10, 5],
                           'scale_numerator': 1, 'scale_denominator': 100},
        'floor_plans': floor_plans,
    }
    path = tmp_path / 'project.yml'
    path.write_text(yaml.safe_dump(config))
    return run_project(path).project.floor_plans


def test_layout_overrides_single_keys(tmp_path):
    default, finer, other_area = _run(tmp_path, [
        {'elements': []},
        {'layout': {'scale_denominator': 50}, 'elements': []},
        {'layout': {'top_right_corner': [20, 5]}, 'elements': []},
    ])
    assert tuple(default.fig.get_size_inches()) == pytest.approx((10 / 100 / METERS_PER_INCH, 5 / 100 / METERS_PER_INCH))
    # Same area as default_layout, scale 1:50
    assert tuple(finer.fig.get_size_inches()) == pytest.approx((10 / 50 / METERS_PER_INCH, 5 / 50 / METERS_PER_INCH))
    assert finer.ax.get_xlim() == (0, 10)
    # Same scale as default_layout, other area
    assert tuple(other_area.fig.get_size_inches()) == pytest.approx((20 / 100 / METERS_PER_INCH, 5 / 100 / METERS_PER_INCH))


def test_layout_must_be_a_mapping(tmp_path):
    with pytest.raises(ValueError, match='layout'):
        _run(tmp_path, [{'layout': [1, 50], 'elements': []}])
