"""

Author: Krzysztof Bartczak
"""

import re

# Matches {variable_name} references used inside string parameter values.
_BRACE_REF_RE = re.compile(r'\{(\w+)\}')

def validate_constants(constants_dict: dict, scope_name: str = "global") -> None:
    """
    Deprecated: Constants validation is no longer needed.
    Kept for backwards compatibility but does nothing.
    
    :param constants_dict:
        dictionary of constant name -> value mappings (ignored)
    :param scope_name:
        name of the scope (ignored)
    """
    pass


def resolve_constants(value, constants_dict: dict):
    """
    Resolve a constant reference or arithmetic expression to its actual value.

    Supports:
    - Direct constant references: "wall_thickness"
    - Arithmetic expressions: "wall_length + 0.5"
    - Expressions with multiple constants: "room1_x + wall_thickness * 2"
    - String-valued variables: if a variable holds a string it is returned
      as-is when directly referenced.  String variables are intentionally
      *not* substituted inside arithmetic expressions; use the ``{var}``
      syntax (see :func:`resolve_string_param`) for string fields.

    When a value cannot be evaluated as an arithmetic expression (after all
    numeric variable substitutions) it is returned unchanged as a string,
    allowing string literals to flow through without raising an error.

    :param value:
        the value to resolve (can be a string reference, number, list, or dict)
    :param constants_dict:
        dictionary of available constants (may contain both numeric and string
        values)
    :return:
        resolved value — float for numeric expressions, str for string
        literals/variables, list/dict with recursively resolved elements
    """
    if isinstance(value, str):
        # Direct reference to a known variable
        if value in constants_dict:
            var_val = constants_dict[value]
            if isinstance(var_val, str):
                return var_val          # string variable: return as-is
            return float(var_val)

        # Arithmetic expression: substitute only numeric (non-string) variables
        expression = value

        # Sort by length descending to avoid partial name replacements
        sorted_constants = sorted(constants_dict.keys(), key=len, reverse=True)

        for const_name in sorted_constants:
            const_val = constants_dict[const_name]
            if isinstance(const_val, str):
                continue            # skip string-valued vars in arithmetic
            pattern = r'\b' + re.escape(const_name) + r'\b'
            expression = re.sub(pattern, str(const_val), expression)

        # Safely evaluate the expression
        try:
            result = eval(expression, {"__builtins__": {}}, {})
            try:
                return float(result)
            except (TypeError, ValueError):
                return result           # result is already a non-numeric value
        except (SyntaxError, NameError, TypeError):
            # Cannot evaluate as arithmetic — treat as a string literal
            return value
    elif isinstance(value, list):
        # Recursively resolve list elements
        return [resolve_constants(item, constants_dict) for item in value]
    elif isinstance(value, dict):
        # Recursively resolve dictionary values
        return {k: resolve_constants(v, constants_dict) for k, v in value.items()}
    elif isinstance(value, (int, float)):
        # Already a number, return as float
        return float(value)
    else:
        # For other types, return as-is
        return value


def resolve_string_param(value, vars_dict: dict) -> str:
    """
    Resolve ``{variable_name}`` references inside a string parameter value.

    This is the counterpart to :func:`resolve_constants` for parameters that
    are expected to hold string values (e.g. ``species``, ``color``,
    ``bloom_color``).  It recognises two forms of the ``{var}`` brace syntax:

    **YAML flow-mapping form** (preferred, no extra quoting needed)::

        species: {gat_1}       # YAML parses as dict {'gat_1': None}

    **Quoted string form** (also accepted)::

        species: "{gat_1}"    # YAML parses as the string '{gat_1}'

    In both cases the value of the variable ``gat_1`` is substituted.  The
    string form also supports partial and multiple substitutions::

        label: "shrub ({gat_1}) h={height}"

    Values without any ``{…}`` references are returned unchanged.

    YAML vars example::

        vars:
          gat_1:       "Heptakodium"
          bloom_clr_1: "pink"
        elements:
          - type: model_leafy_shrub_1
            species:     {gat_1}       # → "Heptakodium"
            bloom_color: {bloom_clr_1} # → "pink"

    :param value:
        raw value from YAML — either a ``str`` with ``{var}`` tokens or a
        single-key dict ``{var_name: None}`` produced by YAML flow-mapping
        parsing
    :param vars_dict:
        merged variable dictionary (global + container vars)
    :return:
        resolved string
    :raises ValueError:
        if a referenced variable name is not found in *vars_dict*
    """
    # YAML interprets bare {var_name} as a flow mapping → dict {var_name: None}
    if isinstance(value, dict) and len(value) == 1:
        (var_name, var_val) = next(iter(value.items()))
        if var_val is None:
            # Written as {var_name} in YAML without quoting
            if var_name not in vars_dict:
                raise ValueError(
                    f"Unknown variable '{var_name}' in string reference '{{{{var_name}}}}'"
                )
            return str(vars_dict[var_name])

    if not isinstance(value, str):
        return value

    if not _BRACE_REF_RE.search(value):
        return value        # nothing to substitute

    # Pure single reference: "{var_name}" → return raw variable value
    full_match = re.fullmatch(r'\s*\{(\w+)\}\s*', value)
    if full_match:
        var_name = full_match.group(1)
        if var_name not in vars_dict:
            raise ValueError(
                f"Unknown variable '{var_name}' in string reference '{value}'"
            )
        return str(vars_dict[var_name])

    # Partial / multiple references: substitute each {var_name} in place
    def _replace(m: re.Match) -> str:
        var_name = m.group(1)
        if var_name not in vars_dict:
            raise ValueError(
                f"Unknown variable '{var_name}' in string value '{value}'"
            )
        return str(vars_dict[var_name])

    return _BRACE_REF_RE.sub(_replace, value)


def resolve_element_params(params: dict, global_vars: dict, room_vars: dict = None) -> dict:
    """
    Resolve variable references in element parameters.

    Handles two kinds of resolution:

    * **Numeric fields** (``anchor_point``, ``length``, ``size``, …) — passed
      through :func:`resolve_constants`, which evaluates arithmetic expressions
      built from numeric variables.
    * **String fields** (``species``, ``color``, ``bloom_color``, …) — passed
      through :func:`resolve_string_param`, which substitutes ``{var_name}``
      references with the variable's string value.

    :param params:
        element parameters dictionary
    :param global_vars:
        global variables dictionary
    :param room_vars:
        room/container-scoped variables dictionary (optional; overrides global)
    :return:
        params dict with all resolvable references substituted
    """
    # Merge vars: container-scoped override global
    merged_values = {**global_vars}
    if room_vars:
        merged_values.update(room_vars)

    # Numeric fields: evaluate arithmetic expressions
    fields_to_resolve = [
        'anchor_point',
        'thickness',
        'length',
        'doorway_width',
        'door_width',
        'overall_thickness',
        'first_point',
        'second_point',
        'radius',
        'width',
        'size',
        'height',
        'v_anchor',
        'diameter',
        'orientation_angle',
        'extension',
        'extension_a',
        'extension_b',
        'roof_thickness',
    ]

    for field in fields_to_resolve:
        if field in params:
            params[field] = resolve_constants(params[field], merged_values)

    # String fields: resolve {variable_name} references
    string_fields = [
        'species',
        'color',
        'trunk_color',
        'bloom_color',
        'bloom_season_start',
        'bloom_season_end',
        'label',
        'material',
    ]

    for field in string_fields:
        if field in params:
            # Apply to str values AND to dict values (YAML parses bare {var}
            # as a flow-mapping dict — resolve_string_param handles both)
            val = params[field]
            if isinstance(val, (str, dict)):
                params[field] = resolve_string_param(val, merged_values)

    # Per-face textures structure (box elements)
    if isinstance(params.get('textures'), dict):
        params['textures'] = _resolve_textures_param(params['textures'], merged_values)

    return params


def _resolve_textures_entry(entry, values: dict):
    """Resolve one ``textures`` entry: numbers/colours as expressions, ``texture`` as ``{var}``."""
    if not isinstance(entry, dict):
        return entry
    resolved = {}
    for key, value in entry.items():
        if key == 'texture':
            resolved[key] = resolve_string_param(value, values) if isinstance(value, (str, dict)) else value
        elif isinstance(value, bool):
            resolved[key] = value  # e.g. double_sided (resolve_constants would turn it into 1.0 / 0.0)
        else:
            resolved[key] = resolve_constants(value, values)
    return resolved


def _resolve_textures_param(textures: dict, values: dict) -> dict:
    """
    Resolve variable references in a ``textures`` structure (see ``floor_planner.face_textures``).

    Numeric keys (``scale_relative``, ``scale_meters``, ``shininess``, ``opacity`` and the
    components of ``diffuse`` / ``specular``) accept arithmetic expressions; ``texture``
    accepts ``{var}`` substitution. The structure itself is validated by the element.
    """
    resolved = {}
    for key, entry in textures.items():
        if key == 'extras' and isinstance(entry, dict):
            resolved[key] = {name: _resolve_textures_entry(e, values) for name, e in entry.items()}
        else:
            resolved[key] = _resolve_textures_entry(entry, values)
    return resolved

