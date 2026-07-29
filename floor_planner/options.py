"""
Configuration options for floor plan elements.

Author: Krzysztof Bartczak
"""

# Global configuration for element-specific options
# Structure: {element_type: {option_name: value}}
_element_options = {}

# Global counter for element IDs
_id_counters = {}

# Canonical fallback families: any element type in a set falls back to the
# canonical key if no exact match is found in _element_options.
_DOOR_TYPES: frozenset[str] = frozenset({
    'Door', 'BalconyDoor', 'WindowDoor', 'SolidDoor1', 'SolidDoor2', 'WindowDoorDouble', 'SlidingBalconyDoor'
})
_WINDOW_TYPES: frozenset[str] = frozenset({
    'Window', 'Window140x120', 'Window90x120',
    'WindowDouble160x120', 'WindowDouble160x140' , 'WindowSingleAny'
})
_VEGE_TYPES: frozenset[str] = frozenset({
    'Tree', 'Shrub', 'Hedge', 'Lawn', 'CircularVegetation2D', 'VegetationElement',
    'LeafyTree', 'LeafyShrub1', 'LeafyShrub2', 'LeafyShrub3', 'LeafyShrub4', 'LeafyShrub5',
})
_ROOF_TYPES: frozenset[str] = frozenset({
    'GableRoof', 'HippedRoof', 'SingleSlopeRoof',
    'HippedRoofOctantLeft', 'HippedRoofOctantRight',
    'HippedInternalOctantLeft', 'HippedInternalOctantRight',
})

_CANONICAL_FALLBACK: dict[frozenset[str], str] = {
    _DOOR_TYPES: 'Door',
    _WINDOW_TYPES: 'Window',
    _VEGE_TYPES: 'Vegetation',
    _ROOF_TYPES: 'Roof',
}


def set_element_options(options: dict) -> None:
    """
    Set options for element types.
    
    :param options:
        dictionary with element type as key and option dict as value
        Example: {'Wall': {'label_color': 'blue', 'dimensions': True}, 'Door': {'id_color': 'red'}}
    """
    global _element_options
    _element_options = options or {}


def get_element_option(element_type: str, option_name: str, default=None):
    """
    Get specific option value for an element type.

    Lookup order:
      1. Exact ``element_type`` key in the options dict.
      2. The canonical family key (``'Door'`` for all door variants,
         ``'Window'`` for all window variants) if the exact key is absent
         or has no entry for ``option_name``.
      3. ``default``.

    :param element_type:
        type of the element (e.g., 'Wall', 'Door', 'BalconyDoor')
    :param option_name:
        name of the option (e.g., 'label_color', 'dimensions')
    :param default:
        default value if option not found
    :return:
        option value or default
    """
    # 1. Exact match
    type_options = _element_options.get(element_type)
    if isinstance(type_options, dict) and option_name in type_options:
        return type_options[option_name]

    # 2. Canonical family fallback
    for family, canonical in _CANONICAL_FALLBACK.items():
        if element_type in family and element_type != canonical:
            canonical_options = _element_options.get(canonical)
            if isinstance(canonical_options, dict) and option_name in canonical_options:
                return canonical_options[option_name]
            break  # element is in this family; no need to check others

    return default


def get_label_color(element_type: str) -> str | None:
    """Get label color for element type, or None if not configured."""
    return get_element_option(element_type, 'label_color')


def get_id_color(element_type: str) -> str | None:
    """Get id color for element type, or None if not configured."""
    color = get_element_option(element_type, 'id_color')
    # Handle None value explicitly set in YAML
    return None if color == 'None' else color


def get_dimensions() -> bool:
    """Get dimensions configuration for Wall elements."""
    return get_element_option('Wall', 'dimensions', False)


def get_show_invisible() -> bool:
    """Get show_invisible configuration for Wall elements."""
    return get_element_option('Wall', 'show_invisible', False)


def get_show_species(element_type: str) -> bool:
    """Get show_species configuration for landscaping elements (Tree, Shrub, Hedge)."""
    return get_element_option(element_type, 'show_species', False)


def get_show_bloom(element_type: str) -> bool:
    """Get show_bloom configuration for landscaping elements (Tree, Shrub, Hedge)."""
    return get_element_option(element_type, 'show_bloom', False)


def generate_element_id(element_type: str, label: str | None = None) -> str:
    """Generate unique ID for an element.
    
    :param element_type:
        type of the element (class name)
    :param label:
        optional label of the element
    :return:
        unique ID in format <label>_<number> or <lowercase_type>_<number>
    """
    global _id_counters
    
    # Determine prefix based on label or type
    if label:
        prefix = label
    else:
        prefix = element_type.lower()
    
    # Increment counter for this prefix
    if prefix not in _id_counters:
        _id_counters[prefix] = 0
    _id_counters[prefix] += 1
    
    return f"{prefix}_{_id_counters[prefix]}"


def reset_id_counters() -> None:
    """Reset all ID counters."""
    global _id_counters
    _id_counters = {}
