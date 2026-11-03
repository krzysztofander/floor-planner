"""Unit tests: floor plan layers (floor_planner/layers.py)."""

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pytest
from matplotlib.colors import to_rgba
from matplotlib.patches import Rectangle

from floor_planner import elements
from floor_planner.elements.foundation.group import Group
from floor_planner.floor_plan import FloorPlan
from floor_planner.layers import (BUILTIN_LAYERS, TEXT_Z_ORDER, Z_ORDER_STEP, LayerSpec, apply_layer,
                                  parse_layers, pop_layer)
from floor_planner.project import Project


def test_parse_layers_defaults_and_order():
    layers = parse_layers([{'name': 'electric', 'z_order': 1, 'force_color': [1, 0, 0]}, {'name': 'construction'}])
    assert list(layers) == ['electric', 'construction']
    assert layers['electric'] == LayerSpec('electric', 1, (1, 0, 0), 1.0)
    assert layers['construction'] == LayerSpec('construction')
    assert parse_layers(None) is None


@pytest.mark.parametrize('data', [
    {'layers': 'construction'},
    [{'z_order': 1}],
    [{'name': 'a', 'z_order': 9}],
    [{'name': 'a', 'z_order': -1}],
    [{'name': 'a', 'z_order': 1.5}],
    [{'name': 'a', 'alpha': 1.5}],
    [{'name': 'a', 'force_color': 'no-such-colour'}],
    [{'name': 'a', 'colour': 'red'}],
    [{'name': 'a'}, {'name': 'a'}],
])
def test_parse_layers_invalid(data):
    with pytest.raises(ValueError):
        parse_layers(data)


def test_pop_layer():
    params = {'layer': 'construction', 'length': 1}
    assert pop_layer(params, 'generic_storage') == 'construction'
    assert params == {'length': 1}
    assert pop_layer({}, 'door') is None
    with pytest.raises(ValueError):
        pop_layer({'layer': 3}, 'door')


def test_apply_layer_z_order_colour_and_alpha():
    fig, ax = plt.subplots()
    red = ax.add_patch(Rectangle((0, 0), 1, 1, facecolor='red', edgecolor='black', zorder=0.5))
    cover = ax.add_patch(Rectangle((0, 0), 1, 1, facecolor='white', edgecolor='black', zorder=0.6))
    hollow = ax.add_patch(Rectangle((0, 0), 1, 1, facecolor='none', edgecolor='black'))
    line, = ax.plot([0, 1], [0, 1], color='black', alpha=0.5)
    text = ax.text(0, 0, 'label', color='black')

    apply_layer([red, cover, hollow, line, text], LayerSpec('a', z_order=3, force_color='blue', alpha=0.5))

    assert red.get_zorder() == 3 * Z_ORDER_STEP + 0.5
    assert text.get_zorder() == TEXT_Z_ORDER * Z_ORDER_STEP + 3
    assert red.get_facecolor() == to_rgba('blue', 0.5)
    assert red.get_edgecolor() == to_rgba('blue', 0.5)
    assert cover.get_facecolor() == to_rgba('white')            # covering fills are kept
    assert cover.get_edgecolor() == to_rgba('blue', 0.5)
    assert hollow.get_facecolor()[3] == 0.0                     # no fill stays no fill
    assert to_rgba(line.get_color()) == to_rgba('blue', 0.25)   # own alpha × layer alpha
    assert to_rgba(text.get_color()) == to_rgba('blue', 0.5)
    plt.close(fig)


def test_apply_layer_container_moves_only_texts():
    fig, ax = plt.subplots()
    patch = ax.add_patch(Rectangle((0, 0), 1, 1, facecolor='red', zorder=0.5))
    text = ax.text(0, 0, 'room', color='black')
    apply_layer([patch, text], None)
    assert patch.get_zorder() == 0.5
    assert text.get_zorder() == TEXT_Z_ORDER * Z_ORDER_STEP + 3
    plt.close(fig)


def test_floor_plan_shows_listed_layers_and_containers():
    reg = elements.create_elements_registry()
    floor_plan = FloorPlan((0, 0), (5, 5))
    wall = reg['wall']((0, 0), 0, 2, 0.2)
    storage = reg['generic_storage']((1, 1), 0, 0.5, 0.5)
    chimney = reg['generic_storage']((2, 2), 0, 0.5, 0.5)
    chimney.set_layer('construction')
    group = Group(child_elements=[], anchor_point=(0, 0), color='black', label=None)
    for element in (wall, storage, chimney, group):
        floor_plan.add_element(element)

    assert floor_plan.get_shown_elements() == [wall, storage, chimney, group]
    floor_plan.layers = parse_layers([{'name': 'construction'}])
    assert floor_plan.get_shown_elements() == [wall, chimney, group]
    plt.close(floor_plan.fig)


def test_composite_passes_layer_to_sub_elements():
    reg = elements.create_elements_registry()
    door = reg['composite_glass_door']((0, 0), doorway_width=1.6, door_width=1.5, thickness=0.1)
    # The parts (glass doors and an AluFrame, whose own default is 'default') follow the composite
    assert door.get_layer() == 'construction'
    assert {sub.get_layer() for sub in door.getList()} == {'construction'}
    door.set_layer('furniture')
    assert {sub.get_layer() for sub in door.getList()} == {'furniture'}
    door.set_layer(None)
    assert {sub.get_layer() for sub in door.getList()} == {'construction'}


def test_floor_plan_names_must_be_unique():
    first, second = FloorPlan((0, 0), (1, 1)), FloorPlan((0, 0), (1, 1))
    first.title = second.title = 'Ground floor'
    with pytest.raises(ValueError, match='unique'):
        Project([first, second])
    plt.close('all')


@pytest.mark.parametrize('type_name', sorted(elements.create_elements_registry()))
def test_default_layer_is_builtin(type_name):
    assert elements.create_elements_registry()[type_name].default_layer in BUILTIN_LAYERS
