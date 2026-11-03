"""
Layers: filter and restyle elements per floor plan.

Every element belongs to one layer: its YAML ``layer`` parameter, or else the
class default (``default_layer``, one of ``BUILTIN_LAYERS``). Group and Room are
containers and do not belong to a layer; they are always drawn.

A floor plan without ``layers`` draws and exports everything as before. A floor
plan with ``layers`` draws (and exports to 3D) only the elements of the listed
layers. Each layer may set:

- ``z_order`` (0-8, default 0): layers with a higher value are drawn on top;
  within one value the elements keep their own order (``v_anchor``);
- ``force_color``: colour for all lines, edges, fills and texts of the layer;
- ``alpha`` (0-1, default 1): multiplies the opacity of all of them.

White and fully transparent colours are never changed: white fills cover what
is under them (e.g. the hole a door cuts in the wall). Texts of all layers
(labels, IDs) are drawn above everything, at level ``TEXT_Z_ORDER``.

See docs/features/layers.md.
"""

from dataclasses import dataclass
from numbers import Real

from matplotlib.artist import Artist
from matplotlib.collections import Collection
from matplotlib.colors import is_color_like, to_rgba
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from matplotlib.text import Text


BUILTIN_LAYERS = ('construction', 'furniture', 'vegetation', 'electric', 'water', 'roof', 'default')
DEFAULT_LAYER = 'default'

MAX_Z_ORDER = 8
TEXT_Z_ORDER = MAX_Z_ORDER + 1
# A layer's z_order is added as z_order * Z_ORDER_STEP to the matplotlib zorder of
# its artists (elements use their v_anchor, i.e. a few metres at most)
Z_ORDER_STEP = 1000

_LAYER_KEYS = ('name', 'z_order', 'force_color', 'alpha')


@dataclass(frozen=True)
class LayerSpec:
    """One entry of a floor plan's ``layers`` list."""

    name: str
    z_order: int = 0
    force_color: str | tuple | None = None
    alpha: float = 1.0

    @classmethod
    def from_yaml(cls, data, where: str) -> 'LayerSpec':
        """
        Validate one ``layers`` entry and build a ``LayerSpec``.

        :param data:
            mapping from YAML
        :param where:
            location used in error messages, e.g. ``'layers[0]'``
        :raises ValueError:
            if a key is unknown or a value has a wrong type or range
        """
        if not isinstance(data, dict):
            raise ValueError(f"{where}: expected a mapping with 'name', got {data!r}")
        unknown = set(data) - set(_LAYER_KEYS)
        if unknown:
            raise ValueError(f"{where}: unknown key(s) {sorted(unknown)}; allowed: {list(_LAYER_KEYS)}")

        name = data.get('name')
        if not isinstance(name, str) or not name:
            raise ValueError(f"{where}.name: expected a layer name, got {name!r}")

        z_order = data.get('z_order', 0)
        if isinstance(z_order, bool) or not isinstance(z_order, int) or not 0 <= z_order <= MAX_Z_ORDER:
            raise ValueError(f"{where}.z_order: expected an integer 0-{MAX_Z_ORDER}, got {z_order!r}")

        force_color = data.get('force_color')
        if isinstance(force_color, list):
            force_color = tuple(force_color)
        if force_color is not None and not is_color_like(force_color):
            raise ValueError(f"{where}.force_color: not a colour: {force_color!r}")

        alpha = data.get('alpha', 1.0)
        if isinstance(alpha, bool) or not isinstance(alpha, Real) or not 0.0 <= alpha <= 1.0:
            raise ValueError(f"{where}.alpha: expected a number 0-1, got {alpha!r}")

        return cls(name=name, z_order=z_order, force_color=force_color, alpha=float(alpha))


def parse_layers(data, where: str = 'layers') -> dict[str, LayerSpec] | None:
    """
    Validate a floor plan's ``layers`` list.

    :param data:
        list from YAML, or None for a floor plan without layers
    :return:
        layer specs by name (in YAML order), or None if ``data`` is None
    :raises ValueError:
        if the list or one of its entries is invalid, or a name is repeated
    """
    if data is None:
        return None
    if not isinstance(data, list):
        raise ValueError(f"{where}: expected a list of layers, got {data!r}")
    layers = {}
    for i, entry in enumerate(data):
        spec = LayerSpec.from_yaml(entry, f"{where}[{i}]")
        if spec.name in layers:
            raise ValueError(f"{where}[{i}].name: layer {spec.name!r} is listed twice")
        layers[spec.name] = spec
    return layers


def pop_layer(params: dict, where: str) -> str | None:
    """
    Remove the ``layer`` parameter from an element definition and validate it.

    :param params:
        element parameters from YAML (modified in place)
    :param where:
        element type, used in error messages
    :return:
        layer name, or None if not given
    """
    layer = params.pop('layer', None)
    if layer is not None and (not isinstance(layer, str) or not layer):
        raise ValueError(f"{where}.layer: expected a layer name, got {layer!r}")
    return layer


def _keeps_color(rgba: tuple) -> bool:
    """White and fully transparent colours are never changed."""
    return rgba[3] == 0.0 or all(c >= 0.999 for c in rgba[:3])


def _restyled(color, spec: LayerSpec) -> tuple:
    """Colour ``color`` with the layer's ``force_color`` and ``alpha`` applied."""
    rgba = to_rgba(color)
    if _keeps_color(rgba):
        return rgba
    r, g, b = to_rgba(spec.force_color)[:3] if spec.force_color is not None else rgba[:3]
    return (r, g, b, rgba[3] * spec.alpha)


def _restyle_patch(patch: Patch, spec: LayerSpec) -> None:
    face, edge = patch.get_facecolor(), patch.get_edgecolor()
    # The artist's own alpha is already part of the colours read above
    patch.set_alpha(None)
    patch.set_facecolor(_restyled(face, spec))
    patch.set_edgecolor(_restyled(edge, spec))


def _restyle_single_color(artist: Line2D | Text, spec: LayerSpec) -> None:
    color = to_rgba(artist.get_color(), artist.get_alpha())
    artist.set_alpha(None)
    artist.set_color(_restyled(color, spec))


def _restyle_artist(artist: Artist, spec: LayerSpec) -> None:
    """Apply ``force_color`` / ``alpha`` to one artist."""
    if isinstance(artist, Patch):
        _restyle_patch(artist, spec)
    elif isinstance(artist, Line2D):
        face = to_rgba(artist.get_markerfacecolor(), artist.get_alpha())
        edge = to_rgba(artist.get_markeredgecolor(), artist.get_alpha())
        _restyle_single_color(artist, spec)
        artist.set_markerfacecolor(_restyled(face, spec))
        artist.set_markeredgecolor(_restyled(edge, spec))
    elif isinstance(artist, Text):
        _restyle_single_color(artist, spec)
        for patch in (artist.get_bbox_patch(), getattr(artist, 'arrow_patch', None)):
            if patch is not None:
                _restyle_patch(patch, spec)
    elif isinstance(artist, Collection):
        faces, edges = artist.get_facecolor(), artist.get_edgecolor()
        artist.set_alpha(None)
        artist.set_facecolor([_restyled(c, spec) for c in faces])
        artist.set_edgecolor([_restyled(c, spec) for c in edges])


def apply_layer(artists: list[Artist], spec: LayerSpec | None) -> None:
    """
    Apply a layer to the artists drawn by one element.

    Texts move to level ``TEXT_Z_ORDER``, other artists to the layer's ``z_order``;
    both keep their own zorder within the level. ``spec`` None (containers)
    only moves the texts.
    """
    restyle = spec is not None and (spec.force_color is not None or spec.alpha != 1.0)
    for artist in artists:
        if isinstance(artist, Text):
            level = TEXT_Z_ORDER
        elif spec is not None:
            level = spec.z_order
        else:
            continue
        artist.set_zorder(level * Z_ORDER_STEP + artist.get_zorder())
        if restyle:
            _restyle_artist(artist, spec)


__all__ = [
    'BUILTIN_LAYERS',
    'DEFAULT_LAYER',
    'MAX_Z_ORDER',
    'TEXT_Z_ORDER',
    'Z_ORDER_STEP',
    'LayerSpec',
    'parse_layers',
    'pop_layer',
    'apply_layer',
]
