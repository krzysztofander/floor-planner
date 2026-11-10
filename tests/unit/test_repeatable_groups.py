"""
Repeatable groups: ``repeat_count`` / ``repeat_next`` on a group
(docs/features/repeatable-groups.md).
"""

import pytest

from floor_planner import elements
from floor_planner.constants import MAX_REPEAT_COUNT
from floor_planner.elements.foundation.group import Group
from floor_planner.elements.foundation.room import Room
from floor_planner.elements.foundation.surfaces import Floor
from floor_planner.elements.foundation.basic import Wall
from floor_planner.elements.symbols.info import DimensionArrow


REGISTRY = elements.create_elements_registry()


class _CollectingFloorPlan:
    """Minimal stand-in for FloorPlan: just records what would be drawn."""

    def __init__(self):
        self.elements = []

    def add_element(self, element):
        self.elements.append(element)


def _arrow(x=0, y=0, **extra):
    return {'type': 'dimension_arrow', 'anchor_point': [x, y], 'length': 1, **extra}


def _wall(anchor, angle, **extra):
    return {'type': 'wall', 'anchor_point': anchor, 'length': 4, 'thickness': 0.2,
            'orientation_angle': angle, 'room_edge': True, **extra}


def _room(**extra):
    return {
        'type': 'room',
        'elements': [_wall([0, 0], 0, label='south'), _wall([4, 0], 90), _wall([4, 4], 180), _wall([0, 4], 270),
                     {'type': 'floor', 'label': 'parquet'}],
        **extra,
    }


def _create(params, global_vars=None):
    floor_plan = _CollectingFloorPlan()
    elements_by_id = {}
    group = Group.create_from_params(params, REGISTRY, floor_plan, [], elements_by_id, global_vars=global_vars)
    return group, floor_plan.elements, elements_by_id


def _arrows(created):
    return [e for e in created if isinstance(e, DimensionArrow)]


def _points(created):
    return [e.anchor_point for e in _arrows(created)]


def _xs(created):
    return [p[0] for p in _points(created)]


def _repeat(count, step='x + 1', start=0, elements=None, **extra):
    """A group stepping x from ``start`` by ``step``, with one arrow at x."""
    return {
        'vars': {'x': start},
        'repeat_count': count,
        'repeat_next': {'x': step},
        'elements': elements if elements is not None else [_arrow('x')],
        **extra,
    }


@pytest.fixture
def templates():
    """Register group templates for one test, then clear them."""
    yield Group.register_templates
    Group.register_templates({})


# ── repeat_count ─────────────────────────────────────────────────────────────

def test_repeat_three_times():
    group, created, _ = _create(_repeat(3))
    assert _xs(created) == [0.0, 1.0, 2.0]
    assert len(group.child_elements) == 3


def test_example_from_the_doc():
    """vars anchor_x: 100, repeat_next anchor_x + 10, repeat_count 10 -> 100, 110, ..., 190."""
    params = {'vars': {'anchor_x': 100}, 'repeat_next': {'anchor_x': 'anchor_x + 10'}, 'repeat_count': 10,
              'elements': [_arrow('anchor_x')]}
    _, created, _ = _create(params)
    assert _xs(created) == [100.0 + 10 * i for i in range(10)]


@pytest.mark.parametrize('count, global_vars, expected', [
    ('n', {'n': 4}, 4),
    ('n - 1', {'n': 4}, 3),
    (5.0, {}, 5),
    ('total', {}, 2),           # a var of the group itself (see params below)
])
def test_count_forms(count, global_vars, expected):
    params = _repeat(count)
    params['vars']['total'] = 2
    _, created, _ = _create(params, global_vars)
    assert len(_arrows(created)) == expected


@pytest.mark.parametrize('count, message', [
    (-1, 'negative'),
    (2.5, 'whole number'),
    ('abc', 'whole number'),
    (True, 'whole number'),
    (None, 'whole number'),
    (MAX_REPEAT_COUNT + 1, 'limit'),
])
def test_invalid_count(count, message):
    with pytest.raises(ValueError, match=message):
        _create(_repeat(count))


def test_count_zero_creates_nothing_and_never_steps():
    """repeat_next would divide by zero if it was evaluated."""
    params = _repeat(0, step='1 / 0', anchor_point=[3, 4])
    group, created, _ = _create(params)
    assert created == [] and group.child_elements == []
    assert group.anchor_point == (3.0, 4.0)


@pytest.mark.parametrize('flag, expected', [(0, 0), (1, 1)])
def test_count_as_condition(flag, expected, capsys):
    params = _repeat('show', elements=[_arrow('x', label='lamp')])
    _, created, _ = _create(params, {'show': flag})
    arrows = _arrows(created)
    assert len(arrows) == expected
    assert all(a.label == 'lamp' for a in arrows)       # no suffix with a count of 1
    assert 'WARNING' not in capsys.readouterr().out


# ── repeat_next ──────────────────────────────────────────────────────────────

def test_repeat_next_in_order():
    """A later entry sees the new value of an earlier one."""
    params = {'vars': {'a': 0, 'b': 0}, 'repeat_count': 3, 'repeat_next': {'a': 'a + 1', 'b': 'a * 10'},
              'elements': [_arrow('b')]}
    _, created, _ = _create(params)
    assert _xs(created) == [0.0, 10.0, 20.0]


def test_repeat_next_not_applied_after_last_iteration():
    """A third step would compute 1 / (2 - 2)."""
    params = {'vars': {'n': 0, 'x': 0}, 'repeat_count': 2, 'repeat_next': {'n': 'n + 1', 'x': '1 / (2 - n)'},
              'elements': [_arrow('x')]}
    _, created, _ = _create(params)
    assert _xs(created) == [0.0, 1.0]


def test_dependent_var_not_recomputed():
    params = {'vars': {'x': 0, 'x2': 'x + 1'}, 'repeat_count': 3, 'repeat_next': {'x': 'x + 1'},
              'elements': [_arrow('x2')]}
    _, created, _ = _create(params)
    assert _xs(created) == [1.0, 1.0, 1.0]


def test_dependent_var_recomputed_in_repeat_next():
    params = {'vars': {'x': 0, 'x2': 'x + 1'}, 'repeat_count': 3, 'repeat_next': {'x': 'x + 1', 'x2': 'x + 1'},
              'elements': [_arrow('x2')]}
    _, created, _ = _create(params)
    assert _xs(created) == [1.0, 2.0, 3.0]


def test_repeat_next_uses_outer_and_global_vars():
    params = {'vars': {'step': 2}, 'elements': [{'type': 'group', **_repeat(3, step='x + step + offset')}]}
    _, created, _ = _create(params, {'offset': 1})
    assert _xs(created) == [0.0, 3.0, 6.0]


def test_repeat_next_outer_only_var_raises():
    params = {'vars': {'x': 0}, 'elements': [{'type': 'group', 'label': 'inner', 'repeat_count': 2,
                                               'repeat_next': {'x': 'x + 1'}, 'elements': [_arrow('x')]}]}
    with pytest.raises(ValueError, match=r"group 'inner'.*own vars.*\['x'\]"):
        _create(params)


def test_repeat_next_undefined_var_raises():
    params = _repeat(2)
    params['repeat_next']['y'] = '1'
    with pytest.raises(ValueError, match=r"\['y'\]"):
        _create(params)


def test_outer_var_covered_locally_can_be_stepped():
    inner = {'type': 'group', 'vars': {'x': 'x'}, 'repeat_count': 3, 'repeat_next': {'x': 'x + 1'},
             'elements': [_arrow('x')]}
    params = {'vars': {'x': 10}, 'elements': [inner, _arrow('x + 5')]}
    _, created, _ = _create(params)
    assert sorted(_xs(created)) == [10.0, 11.0, 12.0, 15.0]     # outer x is still 10 after the inner group


def test_repeat_next_typo_raises():
    with pytest.raises(ValueError, match=r"repeat_next x: 'x \+ ofset' does not give a number"):
        _create(_repeat(2, step='x + ofset'))


def test_repeat_next_must_be_a_mapping():
    params = _repeat(2)
    params['repeat_next'] = ['x + 1']
    with pytest.raises(ValueError, match='mapping'):
        _create(params)


# ── warnings ─────────────────────────────────────────────────────────────────

def test_warning_repeat_next_without_count(capsys):
    params = _repeat(1, label='lamps')
    del params['repeat_count']
    _, created, _ = _create(params)
    assert len(_arrows(created)) == 1
    out = capsys.readouterr().out
    assert "WARNING: group 'lamps': repeat_next without repeat_count" in out


def test_warning_count_without_repeat_next(capsys):
    params = _repeat(3, label='lamps')
    del params['repeat_next']
    _, created, _ = _create(params)
    assert _xs(created) == [0.0, 0.0, 0.0]
    assert "WARNING: group 'lamps': repeat_count 3 without repeat_next" in capsys.readouterr().out


def test_no_warning_for_a_normal_repetition(capsys):
    _create(_repeat(3))
    assert 'WARNING' not in capsys.readouterr().out


# ── anchors (pattern A and B) ────────────────────────────────────────────────

def test_pattern_a_group_anchor_moves_top_level():
    params = _repeat(3, step='x + 4', anchor_point=['x', 1.5], elements=[_arrow(0.5)])
    group, created, _ = _create(params)
    assert _points(created) == [(0.5, 1.5), (4.5, 1.5), (8.5, 1.5)]
    assert group.anchor_point == (0.0, 1.5)        # the group's own anchor: first iteration


def test_pattern_a_group_anchor_moves_nested():
    inner = {'type': 'group', **_repeat(3, step='x + 4', anchor_point=['x', 0], elements=[_arrow(0.5)])}
    _, created, _ = _create({'anchor_point': [10, 2], 'elements': [inner]})
    assert _points(created) == [(10.5, 2.0), (14.5, 2.0), (18.5, 2.0)]


def test_pattern_b_children_move():
    params = _repeat(3, step='x + 0.5', anchor_point=[2, 0])
    _, created, _ = _create(params)
    assert _xs(created) == [2.0, 2.5, 3.0]


# ── nesting ──────────────────────────────────────────────────────────────────

def _grid(rows=3, cols=4):
    inner = {'type': 'group', 'label': 'row', 'anchor_point': [0, 'y'], 'vars': {'x': 0}, 'repeat_count': cols,
             'repeat_next': {'x': 'x + 1'}, 'elements': [_arrow('x', label='tree')]}
    return {'label': 'grid', 'vars': {'y': 0}, 'repeat_count': rows, 'repeat_next': {'y': 'y + 10'},
            'elements': [inner]}


def test_nested_grid():
    group, created, _ = _create(_grid())
    points = _points(created)
    assert len(points) == 12
    assert points == [(float(x), float(y)) for y in (0, 10, 20) for x in range(4)]   # inner x resets per row
    rows = [c for c in group.child_elements if isinstance(c, Group)]
    assert [r.label for r in rows] == ['row_i1', 'row_i2', 'row_i3']


def test_inner_count_depends_on_outer_var():
    inner = {'type': 'group', 'vars': {'x': 0}, 'repeat_count': 'n', 'repeat_next': {'x': 'x + 1'},
             'elements': [_arrow('x', 'n')]}
    params = {'vars': {'n': 1}, 'repeat_count': 3, 'repeat_next': {'n': 'n + 1'}, 'elements': [inner]}
    _, created, _ = _create(params)
    assert len(_arrows(created)) == 1 + 2 + 3


def test_inner_shadowing_does_not_change_outer():
    inner = {'type': 'group', 'vars': {'y': 'y'}, 'repeat_count': 2, 'repeat_next': {'y': 'y + 100'},
             'elements': [_arrow(0, 'y')]}
    params = {'vars': {'y': 0}, 'repeat_count': 2, 'repeat_next': {'y': 'y + 1'}, 'elements': [inner]}
    _, created, _ = _create(params)
    assert [p[1] for p in _points(created)] == [0.0, 100.0, 1.0, 101.0]


# ── templates ────────────────────────────────────────────────────────────────

_TREE_ROW = {
    'vars': {'tree_x': 0, 'spacing': 2.0, 'trees': 5},
    'repeat_count': 'trees',
    'repeat_next': {'tree_x': 'tree_x + spacing'},
    'elements': [_arrow('tree_x', label='tree')],
}


def test_template_repetition_used_as_is(templates):
    templates({'tree_row': _TREE_ROW})
    _, created, _ = _create({'from_template': 'tree_row'})
    assert _xs(created) == [0.0, 2.0, 4.0, 6.0, 8.0]


def test_template_instance_overrides_vars(templates):
    templates({'tree_row': _TREE_ROW})
    _, created, _ = _create({'from_template': 'tree_row', 'vars': {'trees': 3, 'spacing': 1.5}})
    assert _xs(created) == [0.0, 1.5, 3.0]


def test_template_instance_overrides_count(templates):
    templates({'tree_row': _TREE_ROW})
    _, created, _ = _create({'from_template': 'tree_row', 'repeat_count': 2})
    assert _xs(created) == [0.0, 2.0]


def test_template_repeat_next_merged_per_variable(templates):
    templates({'tree_row': _TREE_ROW})
    params = {'from_template': 'tree_row', 'vars': {'tree_y': 0}, 'repeat_next': {'tree_y': 'tree_y + 1'},
              'elements': [_arrow('tree_x', 'tree_y', label='marker')]}
    _, created, _ = _create(params)
    markers = [a for a in _arrows(created) if a.label.startswith('marker')]
    assert [a.anchor_point for a in markers] == [(2.0 * i, float(i)) for i in range(5)]   # template step kept


def test_template_instance_elements_are_repeated(templates):
    templates({'tree_row': _TREE_ROW})
    _, created, _ = _create({'from_template': 'tree_row', 'elements': [_arrow('tree_x', 1, label='extra')]})
    labels = [a.label for a in _arrows(created)]
    assert labels.count('tree_i1') == 1 and len(labels) == 10
    assert [l for l in labels if l.startswith('extra')] == [f'extra_i{i}' for i in range(1, 6)]


def test_nested_group_label_from_template_gets_suffix(templates):
    """The label comes only from the template, so the nested group must add the suffix itself."""
    templates({'labelled': {'label': 'row', 'id': 'row_id', 'elements': [_arrow()]}})
    params = _repeat(2, elements=[{'type': 'group', 'from_template': 'labelled'}])
    group, _, elements_by_id = _create(params)
    rows = [c for c in group.child_elements if isinstance(c, Group)]
    assert [r.label for r in rows] == ['row_i1', 'row_i2']
    assert [r.get_id() for r in rows] == ['row_id_i1', 'row_id_i2']
    assert {'row_id_i1', 'row_id_i2'} <= set(elements_by_id)


def test_template_repeat_next_not_a_mapping(templates):
    templates({'bad': {**_TREE_ROW, 'repeat_next': 'tree_x + 1'}})
    with pytest.raises(ValueError, match='mapping'):
        _create({'from_template': 'bad'})


def test_nested_template_repetition(templates):
    """Two levels of repetition from a template: an outer repeating group around a template instance."""
    templates({'tree_row': _TREE_ROW})
    inner = {'type': 'group', 'from_template': 'tree_row', 'anchor_point': [0, 'y'], 'vars': {'trees': 2}}
    params = {'vars': {'y': 0}, 'repeat_count': 2, 'repeat_next': {'y': 'y + 5'}, 'elements': [inner]}
    _, created, _ = _create(params)
    assert _points(created) == [(0.0, 0.0), (2.0, 0.0), (0.0, 5.0), (2.0, 5.0)]
    assert [a.label for a in _arrows(created)] == ['tree_i1_i1', 'tree_i1_i2', 'tree_i2_i1', 'tree_i2_i2']


# ── rooms ────────────────────────────────────────────────────────────────────

@pytest.mark.parametrize('key, value', [('repeat_count', 2), ('repeat_next', {'x': 'x + 1'})])
def test_room_rejects_repetition(key, value):
    with pytest.raises(ValueError, match=f'{key} not supported in a room.*group'):
        Room.create_from_params({**_room(), key: value}, REGISTRY, _CollectingFloorPlan(), [], {})


def test_room_rejects_repetition_when_nested():
    with pytest.raises(ValueError, match='not supported in a room'):
        _create({'elements': [_room(repeat_count=2)]})


def test_room_repeated_through_a_group():
    params = _repeat(3, step='x + 5', elements=[_room(label='box', anchor_point=['x', 0])])
    group, created, elements_by_id = _create(params)
    rooms = [c for c in group.child_elements if isinstance(c, Room)]
    assert [r.label for r in rooms] == ['box_i1', 'box_i2', 'box_i3']
    for room, x in zip(rooms, (0.0, 5.0, 10.0)):
        assert room.external_corners[0] == pytest.approx((x, 0.0), abs=1e-9)
    assert [w.label for w in created if isinstance(w, Wall) and w.label] == ['south_i1', 'south_i2', 'south_i3']
    assert [f.label for f in created if isinstance(f, Floor)] == ['parquet_i1', 'parquet_i2', 'parquet_i3']


# ── embedded_dimensions ──────────────────────────────────────────────────────

def test_embedded_dimensions_off_in_every_iteration():
    params = _repeat(3, embedded_dimensions=False,
                     elements=[_arrow('x'), {'type': 'group', 'elements': [_arrow('x')]}])
    _, created, _ = _create(params)
    assert _arrows(created) == []


# ── labels and IDs: the _i<N> suffix ─────────────────────────────────────────

def test_suffix_on_label_and_id():
    params = _repeat(3, elements=[_arrow('x', label='lamp'), _arrow('x', id='post')])
    _, created, elements_by_id = _create(params)
    arrows = _arrows(created)
    assert [a.label for a in arrows if a.label] == ['lamp_i1', 'lamp_i2', 'lamp_i3']
    assert [a.get_id() for a in arrows if a.get_id().startswith('post')] == ['post_i1', 'post_i2', 'post_i3']
    assert [a.get_id() for a in arrows if a.label] == ['lamp_i1_1', 'lamp_i2_1', 'lamp_i3_1']
    assert all(i in elements_by_id for i in ('post_i1', 'post_i2', 'post_i3'))


def test_no_label_no_id_unchanged():
    _, created, _ = _create(_repeat(2))
    arrows = _arrows(created)
    assert [a.label for a in arrows] == [None, None]
    assert all(a.get_id().startswith('dimensionarrow_') for a in arrows)
    assert len({a.get_id() for a in arrows}) == 2


def test_repeating_group_own_label_has_no_suffix():
    group, _, _ = _create(_repeat(3, label='lamps', id='lamps_group'))
    assert group.label == 'lamps' and group.get_id() == 'lamps_group'


def test_suffix_after_var_substitution():
    params = _repeat(2, elements=[_arrow('x', label='{kind}')])
    _, created, _ = _create(params, {'kind': 'oak'})
    assert [a.label for a in _arrows(created)] == ['oak_i1', 'oak_i2']


def test_nested_suffix_outer_first():
    _, created, _ = _create(_grid())
    labels = [a.label for a in _arrows(created)]
    assert labels[:2] == ['tree_i1_i1', 'tree_i1_i2']
    assert labels[-1] == 'tree_i3_i4'
    assert 'tree_i2_i3' in labels


def test_non_repeating_group_in_between_adds_nothing():
    middle = {'type': 'group', 'label': 'middle', 'elements': [_arrow('x', label='tree')]}
    _, created, _ = _create(_repeat(2, elements=[middle]))
    assert [a.label for a in _arrows(created)] == ['tree_i1', 'tree_i2']


def test_count_one_adds_no_suffix_also_when_nested():
    inner = {'type': 'group', **_repeat(3, elements=[_arrow('x', label='apple')])}
    outer = {'label': 'outer', 'vars': {'y': 0}, 'repeat_count': 1, 'repeat_next': {'y': 'y + 1'},
             'elements': [inner]}
    _, created, _ = _create(outer)
    assert [a.label for a in _arrows(created)] == ['apple_i1', 'apple_i2', 'apple_i3']


def test_all_ids_unique():
    _, created, elements_by_id = _create(_grid())
    ids = [e.get_id() for e in created]
    assert len(ids) == len(set(ids))
    assert set(ids) <= set(elements_by_id)


def test_group_without_repetition_unchanged():
    """No repeat keys: one pass, no suffix, no warning."""
    group, created, _ = _create({'label': 'plain', 'anchor_point': [1, 0], 'elements': [_arrow(1, label='a')]})
    assert _points(created) == [(2.0, 0.0)]
    assert [a.label for a in _arrows(created)] == ['a']
    assert group.label == 'plain'
