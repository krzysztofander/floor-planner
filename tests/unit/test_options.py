"""Unit tests: element options are matched case-insensitively (floor_planner/options.py)."""

import pytest

from floor_planner.options import get_element_option, set_element_options


@pytest.mark.parametrize('yaml_type, yaml_option', [
    ('Wall', 'label_color'),
    ('wall', 'LABEL_COLOR'),
    ('WALL', 'Label_Color'),
])
@pytest.mark.parametrize('code_type, code_option', [
    ('Wall', 'label_color'),
    ('wall', 'Label_Color'),
])
def test_option_found_regardless_of_case(yaml_type, yaml_option, code_type, code_option):
    set_element_options({yaml_type: {yaml_option: 'blue'}})
    assert get_element_option(code_type, code_option) == 'blue'


def test_family_fallback_is_case_insensitive():
    set_element_options({'door': {'LABEL_COLOR': 'red'}, 'WINDOW': {'dimensions': True}})
    assert get_element_option('BalconyDoor', 'label_color') == 'red'
    assert get_element_option('balconydoor', 'Label_Color') == 'red'
    assert get_element_option('Window140x120', 'Dimensions') is True


def test_exact_type_wins_over_family():
    set_element_options({'Door': {'label_color': 'red'}, 'balconydoor': {'Label_Color': 'green'}})
    assert get_element_option('BalconyDoor', 'label_color') == 'green'
    assert get_element_option('WindowDoor', 'label_color') == 'red'


def test_spellings_of_same_name_are_merged_later_wins():
    # e.g. default_options has 'Wall', a floor plan's options add 'wall' (appended later)
    set_element_options({
        'Wall': {'label_color': 'blue', 'dimensions': True},
        'wall': {'LABEL_COLOR': 'red'},
    })
    assert get_element_option('Wall', 'label_color') == 'red'
    assert get_element_option('Wall', 'dimensions') is True


def test_default_when_missing():
    set_element_options({'Wall': {'label_color': 'blue'}})
    assert get_element_option('Wall', 'id_color', 'none') == 'none'
    assert get_element_option('Fence', 'label_color') is None
