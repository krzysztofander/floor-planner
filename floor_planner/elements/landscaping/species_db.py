"""
Species characteristics database for vegetation elements.

When a vegetation element (Tree, Shrub, Hedge, external models …) is given a
``species`` name, the corresponding entry from :data:`SPECIES_DB` is used as a
set of *default* parameter values.  Any parameter that is explicitly specified
in the YAML config (or passed directly to ``__init__``) always wins over the
species default.

Resolution order (highest priority first):
  1. Explicitly supplied value (non-``None``)
  2. Species DB value for the given species name
  3. Class-level hardcoded fallback

Adding new species
------------------
Add an entry to :data:`SPECIES_DB`.  Only include keys whose values you want to
provide as defaults — omitting a key is fine; the class default will be used.

Available keys per species entry
---------------------------------
height              : float   – typical height in metres
diameter            : float   – canopy / shrub diameter in metres
color               : str     – canopy fill colour (matplotlib name or hex)
trunk_diameter      : float   – trunk circle diameter in metres (trees only)
trunk_color         : str     – trunk fill colour
bloom_season_start  : str     – bloom start in dd.mm format, e.g. "01.06"
bloom_season_end    : str     – bloom end   in dd.mm format, e.g. "30.06"
bloom_color         : str     – bloom overlay colour
"""

from __future__ import annotations

# ---------------------------------------------------------------------------
# Species database
# ---------------------------------------------------------------------------

SPECIES_DB: dict[str, dict] = {
    # ---- Trees ----
    "Lipa": {
        "height": 20.0,
        "diameter": 12.0,
        "color": "#5B8C3E",
        "trunk_diameter": 0.7,
        "trunk_color": "#8B6914",
        "bloom_season_start": "15.06",
        "bloom_season_end": "15.07",
        "bloom_color": "#FFFACD",
    },
    "Glediczja": {
        "height": 80.0,
        "diameter": 6.0,
        "color": "#5B8C3E",
        "trunk_diameter": 0.7,
        "trunk_color": "#8B6914",
        "bloom_season_start": "15.06",
        "bloom_season_end": "15.07",
        "bloom_color": "#FFFACD",
    },
    "Katalpa": {
        "height": 12.0,
        "diameter": 8.0,
        "color": "#4CAF50",
        "trunk_diameter": 0.4,
        "trunk_color": "#795548",
        "bloom_season_start": "01.07",
        "bloom_season_end": "01.08",
        "bloom_color": "white",
    },
    "Dąb": {
        "height": 25.0,
        "diameter": 15.0,
        "color": "#3E6B28",
        "trunk_diameter": 1.0,
        "trunk_color": "#5D4037",
        "bloom_season_start": "01.04",
        "bloom_season_end": "30.04",
        "bloom_color": "#C8E6C9",
    },
    "Klon": {
        "height": 15.0,
        "diameter": 10.0,
        "color": "#558B2F",
        "trunk_diameter": 0.5,
        "trunk_color": "#6D4C41",
        "bloom_season_start": "01.04",
        "bloom_season_end": "15.04",
        "bloom_color": "#F9A825",
    },
    "Brzoza": {
        "height": 18.0,
        "diameter": 6.0,
        "color": "#7CB342",
        "trunk_diameter": 0.3,
        "trunk_color": "#ECEFF1",
    },
    "Świerk": {
        "height": 20.0,
        "diameter": 5.0,
        "color": "#1B5E20",
        "trunk_diameter": 0.3,
        "trunk_color": "#4E342E",
    },
    "Sosna": {
        "height": 22.0,
        "diameter": 6.0,
        "color": "#2E7D32",
        "trunk_diameter": 0.4,
        "trunk_color": "#6D4C41",
    },
    "Jabłoń": {
        "height": 5.0,
        "diameter": 5.0,
        "color": "#66BB6A",
        "trunk_diameter": 0.2,
        "trunk_color": "#795548",
        "bloom_season_start": "20.04",
        "bloom_season_end": "15.05",
        "bloom_color": "#F8BBD0",
    },
    "Wiśnia": {
        "height": 6.0,
        "diameter": 5.0,
        "color": "#66BB6A",
        "trunk_diameter": 0.2,
        "trunk_color": "#795548",
        "bloom_season_start": "01.04",
        "bloom_season_end": "30.04",
        "bloom_color": "#FFCDD2",
    },
    # ---- Shrubs ----
    "Heptakodium": {
        "height": 3.3,
        "diameter": 2.0,
        "color": "#6B9E4E",
        "bloom_season_start": "01.08",
        "bloom_season_end": "31.08",
        "bloom_color": "pink",
    },
    "Jagoda Kamczacka": {
        "height": 1.0,
        "diameter": 1.2,
        "color": "#4A7C3F",
        "bloom_season_start": "01.04",
        "bloom_season_end": "01.05",
        "bloom_color": "white",
    },
    "Biała Forsycja" :{
        "height": 1.1,
        "diameter": 1.3,
        "color": "#4A7C3F",
        "bloom_season_start": "10.04",
        "bloom_season_end": "20.05",
        "bloom_color": "white",
    },  
    "Kalina Waka": {
        "height": 2.0,
        "diameter": 1.8,
        "color": "#5C8A3C",
        "bloom_season_start": "15.05",
        "bloom_season_end": "31.05",
        "bloom_color": "white",
    },
    "Guzikowiec": {
        "height": 1.5,
        "diameter": 1.7,
        "color": "#6B8E40",
        "bloom_season_start": "15.07",
        "bloom_season_end": "31.07",
        "bloom_color": "white",
    },
    "Krzewuszka": {
        "height": 2.0,
        "diameter": 2.0,
        "color": "#5A8C3E",
        "bloom_season_start": "01.06",
        "bloom_season_end": "01.07",
        "bloom_color": "red",
    },
    "Ligustr": {
        "height": 1.6,
        "diameter": 1.5,
        "color": "#7B9E5A",
        "bloom_season_start": "01.05",
        "bloom_season_end": "31.05",
        "bloom_color": "#EEE8F0",
    },
    "Lilak": {
        "height": 2.5,
        "diameter": 2.2,
        "color": "#7B9E5A",
        "bloom_season_start": "01.05",
        "bloom_season_end": "31.05",
        "bloom_color": "#D1A3E0",
    },
    "Jaśminowiec": {
        "height": 3.0,
        "diameter": 1.5,
        "color": "#6E9E52",
        "bloom_season_start": "15.06",
        "bloom_season_end": "31.07",
        "bloom_color": "white",
    },
    "Forsycja": {
        "height": 2.0,
        "diameter": 1.5,
        "color": "#5E8F3C",
        "bloom_season_start": "15.03",
        "bloom_season_end": "30.04",
        "bloom_color": "#FFD600",
    },
    "Hortensja": {
        "height": 1.6,
        "diameter": 1.5,
        "color": "#64943E",
        "bloom_season_start": "01.07",
        "bloom_season_end": "31.08",
        "bloom_color": "#E3F2FD",
    },
    "Tawuła": {
        "height": 1.5,
        "diameter": 1.4,
        "color": "#5E8A3A",
        "bloom_season_start": "01.05",
        "bloom_season_end": "15.06",
        "bloom_color": "#F8BBD0",
    },
    "Pęcherznica": {
        "height": 2.0,
        "diameter": 2.2,
        "color": "#527A35",
        "bloom_season_start": "15.05",
        "bloom_season_end": "30.06",
        "bloom_color": "white",
    },
    "Kalina Pompon": {
        "height": 2.2,
        "diameter": 2.0,
        "color": "#5C8A3C",
        "bloom_season_start": "15.05",
        "bloom_season_end": "15.06",
        "bloom_color": "white",
    },
    # ---- Berries ----
    "Porz. czerwona": {
        "height": 1.2,
        "diameter": 1.0,
        "color": "#6B9E4E",
        "bloom_season_start": "15.04",
        "bloom_season_end": "30.04",
        "bloom_color":  "#EBD1DA",
    },
    "Porz. biała": {
        "height": 1.2,
        "diameter": 1.0,
        "color": "#7DAD61",
        "bloom_season_start": "15.04",
        "bloom_season_end": "30.04",
        "bloom_color": "white",
    },
    "Porz. czarna": {
        "height": 1.2,
        "diameter": 1.1,
        "color": "#598440",
        "bloom_season_start": "15.04",
        "bloom_season_end": "30.04",
        "bloom_color": "white",
    },
    "Borówka": {
        "height": 1.0,
        "diameter": 1.0,
        "color": "#6B8D57",
        "bloom_season_start": "15.04",
        "bloom_season_end": "30.04",
        "bloom_color": "#F7F1F3",
    },
}  # SPECIES_DB
# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------

def get_species_defaults(species: str) -> dict:
    """Return the characteristics dict for *species* (case-insensitive lookup).

    Returns an empty dict when the species is not in the database — callers
    should treat all keys as optional.
    """
    for key, val in SPECIES_DB.items():
        if key.lower() == species.lower():
            return dict(val)
    return {}


def resolve_species_params(species: str | None, **params) -> dict:
    """Fill ``None`` values in *params* using species defaults.

    Parameters that are explicitly provided (non-``None``) are never
    overridden.  Unknown species names are silently ignored.

    Example::

        resolved = resolve_species_params(
            "Lipa",
            height=None,        # will be filled from DB
            diameter=8.0,       # explicit override — kept as-is
            color=None,         # will be filled from DB
        )

    :param species: species name string, or ``None`` to skip lookup.
    :param params:  keyword arguments mapping param name → current value.
    :return:        dict with the same keys; ``None`` values replaced where
                    possible.
    """
    if not species:
        return params

    defaults = get_species_defaults(species)
    if not defaults:
        return params

    return {
        key: (defaults[key] if value is None and key in defaults else value)
        for key, value in params.items()
    }
