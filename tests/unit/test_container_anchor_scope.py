"""
Variable scoping of containers (Group, Room) and where their anchor_point is resolved.

Rules (docs/features/repeatable-groups.md, "Variable scoping"):

* inner definitions cover outer ones, for everything inside the container;
* a ``vars`` section is evaluated in order: in ``X: X + 1`` the right-hand ``X``
  is the outer one, a later ``Y: X`` sees the new, inner ``X``;
* a container's ``anchor_point`` is resolved in the container's own scope and
  translated by the anchor of the enclosing container, at top level and when
  nested alike; without ``anchor_point`` the container sits at the parent's anchor.
"""

import pytest

from floor_planner import elements
from floor_planner.elements.foundation.group import Group
from floor_planner.elements.foundation.room import Room
from floor_planner.elements.symbols.info import DimensionArrow


REGISTRY = elements.create_elements_registry()


class _CollectingFloorPlan:
    """Minimal stand-in for FloorPlan: just records what would be drawn."""

    def __init__(self):
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)


def _arrow(x=0, y=0):
    return {'type': 'dimension_arrow', 'anchor_point': [x, y], 'length': 1}


def _wall(anchor, angle):
    return {'type': 'wall', 'anchor_point': anchor, 'length': 4, 'thickness': 0.2,
            'orientation_angle': angle, 'room_edge': True}


def _room(**extra):
    return {
        'type': 'room',
        'elements': [_wall([0, 0], 0), _wall([4, 0], 90), _wall([4, 4], 180), _wall([0, 4], 270)],
        **extra,
    }


def _create(params, global_vars=None, cls=Group):
    floor_plan = _CollectingFloorPlan()
    container = cls.create_from_params(params, REGISTRY, floor_plan, [], {}, global_vars=global_vars)
    return container, floor_plan.elements


def _arrow_xs(created):
    return [e.anchor_point[0] for e in created if isinstance(e, DimensionArrow)]


def _nested(container, cls=Group):
    return [c for c in container.child_elements if isinstance(c, cls)]


# ── anchor_point of nested containers ───────────────────────────────────────

def test_top_level_anchor_uses_own_vars():
    group, created = _create({'vars': {'ax': 2}, 'anchor_point': ['ax', 0], 'elements': [_arrow(1)]})
    assert group.anchor_point == (2.0, 0.0)
    assert _arrow_xs(created) == [3.0]


def test_nested_group_anchor_uses_own_vars():
    """Raised TypeError before: the parent resolved the anchor without the nested vars."""
    params = {
        'anchor_point': [10, 0],
        'elements': [{'type': 'group', 'vars': {'ax': 2}, 'anchor_point': ['ax', 1], 'elements': [_arrow(1)]}],
    }
    group, created = _create(params)
    assert _nested(group)[0].anchor_point == (12.0, 1.0)
    assert _arrow_xs(created) == [13.0]


def test_nested_room_anchor_uses_own_vars():
    params = {'anchor_point': [10, 0], 'elements': [_room(vars={'ax': 2}, anchor_point=['ax', 0])]}
    group, _ = _create(params)
    room = _nested(group, Room)[0]
    assert room.anchor_point == (12.0, 0.0)
    assert room.external_corners[0] == pytest.approx((12.0, 0.0))


def test_nested_anchor_redefined_name_uses_own_value():
    """Used the outer value before (anchor 1), while a top-level group used its own (100)."""
    params = {
        'vars': {'X': 1},
        'elements': [{'type': 'group', 'vars': {'X': 100}, 'anchor_point': ['X', 0], 'elements': [_arrow()]}],
    }
    group, created = _create(params)
    assert _nested(group)[0].anchor_point == (100.0, 0.0)
    assert _arrow_xs(created) == [100.0]


def test_nested_anchor_sees_parent_vars():
    params = {
        'vars': {'shift': 3},
        'anchor_point': [10, 0],
        'elements': [{'type': 'group', 'anchor_point': ['shift', 0], 'elements': [_arrow()]}],
    }
    _, created = _create(params)
    assert _arrow_xs(created) == [13.0]


def test_nested_anchor_self_reference_uses_outer_value():
    params = {
        'vars': {'X': 1},
        'elements': [{'type': 'group', 'vars': {'X': 'X + 1'}, 'anchor_point': ['X', 0], 'elements': [_arrow()]}],
    }
    _, created = _create(params)
    assert _arrow_xs(created) == [2.0]


def test_nested_container_without_anchor_sits_at_parent_anchor():
    """Was placed at (0, 0) before, ignoring the parent's anchor."""
    params = {'anchor_point': [5, 0], 'elements': [{'type': 'group', 'elements': [_arrow(1)]}]}
    group, created = _create(params)
    assert _nested(group)[0].anchor_point == (5.0, 0.0)
    assert _arrow_xs(created) == [6.0]


def test_deep_nesting_accumulates_offsets():
    inner = {'type': 'group', 'vars': {'c': 100}, 'anchor_point': ['c', 0], 'elements': [_arrow(1)]}
    middle = {'type': 'group', 'vars': {'b': 10}, 'anchor_point': ['b', 0], 'elements': [inner]}
    _, created = _create({'vars': {'a': 1}, 'anchor_point': ['a', 0], 'elements': [middle]})
    assert _arrow_xs(created) == [112.0]


def test_unresolvable_anchor_raises_value_error():
    params = {'elements': [{'type': 'group', 'label': 'g', 'anchor_point': ['nope', 0], 'elements': []}]}
    with pytest.raises(ValueError, match='anchor_point'):
        _create(params)


# ── scoping of vars (current behaviour, pinned) ─────────────────────────────

def test_self_reference_uses_outer_value():
    _, created = _create({'vars': {'X': 'X + 1'}, 'elements': [_arrow('X')]}, global_vars={'X': 10})
    assert _arrow_xs(created) == [11.0]


def test_later_entry_sees_new_inner_value():
    _, created = _create({'vars': {'X': 'X + 1', 'Y': 'X'}, 'elements': [_arrow('Y')]}, global_vars={'X': 10})
    assert _arrow_xs(created) == [11.0]


def test_entry_sees_earlier_new_name():
    _, created = _create({'vars': {'A': 2, 'B': 'A * 3'}, 'elements': [_arrow('B')]})
    assert _arrow_xs(created) == [6.0]


def test_inner_covers_outer_in_elements_and_nested_containers():
    params = {
        'vars': {'X': 1},
        'elements': [
            _arrow('X'),
            {'type': 'group', 'vars': {'X': 5}, 'elements': [
                _arrow('X'),
                {'type': 'group', 'elements': [_arrow('X')]},
            ]},
        ],
    }
    _, created = _create(params, global_vars={'X': 100})
    assert sorted(_arrow_xs(created)) == [1.0, 5.0, 5.0]


def test_nested_redefinition_chains():
    params = {
        'vars': {'X': 'X + 1'},
        'elements': [_arrow('X'), {'type': 'group', 'vars': {'X': 'X + 1'}, 'elements': [_arrow('X')]}],
    }
    _, created = _create(params, global_vars={'X': 10})
    assert sorted(_arrow_xs(created)) == [11.0, 12.0]


def test_inner_definition_does_not_leak_to_siblings():
    params = {
        'vars': {'X': 1},
        'elements': [
            {'type': 'group', 'vars': {'X': 5}, 'elements': [_arrow('X')]},
            _arrow('X'),
        ],
    }
    _, created = _create(params)
    assert sorted(_arrow_xs(created)) == [1.0, 5.0]
