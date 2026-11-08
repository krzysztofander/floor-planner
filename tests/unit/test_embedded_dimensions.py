"""
The ``embedded_dimensions`` flag of Group and Room: when false, dimension arrows
defined within the container (including nested containers) are not created.
"""

import pytest

from floor_planner import elements, options
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


def _arrow(x=0):
    return {'type': 'dimension_arrow', 'anchor_point': [x, 0], 'length': 1}


def _wall(anchor, angle):
    return {'type': 'wall', 'anchor_point': anchor, 'length': 4, 'thickness': 0.2,
            'orientation_angle': angle, 'room_edge': True}


def _room(**extra):
    return {
        'elements': [
            _wall([0, 0], 0), _wall([4, 0], 90), _wall([4, 4], 180), _wall([0, 4], 270),
            _arrow(1),
        ],
        **extra,
    }


def _create(cls, params):
    floor_plan = _CollectingFloorPlan()
    container = cls.create_from_params(params, REGISTRY, floor_plan, [], {})
    arrows = [e for e in floor_plan.elements if isinstance(e, DimensionArrow)]
    return container, arrows


def test_group_default_keeps_arrows():
    group, arrows = _create(Group, {'elements': [_arrow(), {'type': 'group', 'elements': [_arrow(1)]}]})
    assert group.embedded_dimensions is True
    assert len(arrows) == 2


def test_group_disabled_skips_own_and_nested_arrows():
    params = {
        'embedded_dimensions': False,
        'elements': [
            _arrow(),
            # nested container cannot re-enable what its parent disabled
            {'type': 'group', 'embedded_dimensions': True, 'elements': [_arrow(1)]},
            {'type': 'room', **_room()},
        ],
    }
    group, arrows = _create(Group, params)
    assert group.embedded_dimensions is False
    assert arrows == []
    nested = [c for c in group.child_elements if isinstance(c, Group)]
    assert len(nested) == 2 and all(not c.embedded_dimensions for c in nested)


def test_nested_group_disabled_leaves_parent_arrows():
    params = {'elements': [_arrow(), {'type': 'group', 'embedded_dimensions': False, 'elements': [_arrow(1)]}]}
    _, arrows = _create(Group, params)
    assert len(arrows) == 1


@pytest.mark.parametrize('flag, expected', [(None, 1), (True, 1), (False, 0)])
def test_room_flag(flag, expected):
    params = _room() if flag is None else _room(embedded_dimensions=flag)
    room, arrows = _create(Room, params)
    assert room.embedded_dimensions is (flag is not False)
    assert len(arrows) == expected


# ── floor plan option (options.Room / options.Group) ─────────────────────────

@pytest.fixture
def element_options():
    """Set per-floor-plan element options for one test, then clear them."""
    yield options.set_element_options
    options.set_element_options({})


def test_room_option_disables_arrows(element_options):
    element_options({'Room': {'embedded_dimensions': False}})
    room, arrows = _create(Room, _room())
    assert room.embedded_dimensions is False
    assert arrows == []


def test_group_option_disables_arrows(element_options):
    element_options({'Group': {'embedded_dimensions': False}})
    group, arrows = _create(Group, {'elements': [_arrow()]})
    assert group.embedded_dimensions is False
    assert arrows == []


def test_explicit_param_overrides_option(element_options):
    element_options({'Room': {'embedded_dimensions': False}})
    room, arrows = _create(Room, _room(embedded_dimensions=True))
    assert room.embedded_dimensions is True
    assert len(arrows) == 1


def test_option_is_per_class(element_options):
    """options.Room does not affect groups, and options.Group does not affect rooms."""
    element_options({'Room': {'embedded_dimensions': False}})
    _, arrows = _create(Group, {'elements': [_arrow()]})
    assert len(arrows) == 1

    element_options({'Group': {'embedded_dimensions': False}})
    _, arrows = _create(Room, _room())
    assert len(arrows) == 1


def test_group_option_still_covers_nested_rooms(element_options):
    """A group disabled by the option forces its nested rooms off too."""
    element_options({'Group': {'embedded_dimensions': False}})
    _, arrows = _create(Group, {'elements': [{'type': 'room', **_room()}]})
    assert arrows == []
