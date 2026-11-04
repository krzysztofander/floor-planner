"""
Layers: filter and restyle elements per floor plan, separately in 2D and 3D.

Every element belongs to one layer: its YAML ``layer`` parameter, or else the
class default (``default_layer``, one of ``BUILTIN_LAYERS``). Group and Room are
containers and do not belong to a layer; they are always drawn and exported.

A floor plan's ``layers`` mapping has a ``2d`` and/or a ``3d`` section:

    layers:
      2d:                                   # layer name -> 2D modifiers (or nothing)
        construction: {force_color: grey, alpha: 0.3}
        electric: {z_order: 1, force_color: red}
        furniture:
      3d: [construction, electric]          # layers exported to the glTF

Without a section, everything is drawn (2D, not restyled) or exported (3D). 2D
modifiers of a layer:

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

_SECTIONS = ('2d', '3d')
_MODIFIER_KEYS = ('z_order', 'force_color', 'alpha')


@dataclass(frozen=True)
class LayerSpec:
    """One layer of a floor plan's ``layers.2d`` section and its 2D modifiers."""

    name: str
    z_order: int = 0
    force_color: str | tuple | None = None
    alpha: float = 1.0

    @classmethod
    def from_yaml(cls, name, data, where: str) -> 'LayerSpec':
        """
        Validate one ``layers.2d`` entry and build a ``LayerSpec``.

        :param name:
            layer name (the key of the entry)
        :param data:
            modifiers from YAML, or None for none
        :param where:
            location used in error messages, e.g. ``'layers.2d.construction'``
        :raises ValueError:
            if a key is unknown or a value has a wrong type or range
        """
        _check_name(name, where)
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise ValueError(f"{where}: expected a mapping of modifiers or nothing, got {data!r}")
        unknown = set(data) - set(_MODIFIER_KEYS)
        if unknown:
            raise ValueError(f"{where}: unknown key(s) {sorted(unknown)}; allowed: {list(_MODIFIER_KEYS)}")

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


@dataclass(frozen=True)
class FloorPlanLayers:
    """A floor plan's ``layers``: None in a section = everything, no filtering."""

    layers_2d: dict[str, LayerSpec] | None = None
    layers_3d: frozenset[str] | None = None


def _check_name(name, where: str) -> None:
    if not isinstance(name, str) or not name:
        raise ValueError(f"{where}: expected a layer name, got {name!r}")


def parse_layers(data, where: str = 'layers') -> FloorPlanLayers:
    """
    Validate a floor plan's ``layers`` mapping.

    :param data:
        mapping from YAML with ``2d`` and/or ``3d``, or None for a floor plan without layers
    :return:
        the 2D layer specs by name (in YAML order) and the 3D layer names;
        a section that is not given is None
    :raises ValueError:
        if the mapping, a section or an entry is invalid
    """
    if data is None:
        return FloorPlanLayers()
    if not isinstance(data, dict):
        raise ValueError(f"{where}: expected a mapping with '2d' and/or '3d', got {data!r}")
    unknown = set(data) - set(_SECTIONS)
    if unknown:
        raise ValueError(f"{where}: unknown key(s) {sorted(unknown)}; allowed: {list(_SECTIONS)}")
    if not data:
        raise ValueError(f"{where}: set '2d' and/or '3d'")

    layers_2d = None
    if '2d' in data:
        section = data['2d']
        if not isinstance(section, dict) or not section:
            raise ValueError(f"{where}.2d: expected a mapping of layer names to modifiers, got {section!r}")
        layers_2d = {name: LayerSpec.from_yaml(name, modifiers, f"{where}.2d.{name}")
                     for name, modifiers in section.items()}

    layers_3d = None
    if '3d' in data:
        section = data['3d']
        if not isinstance(section, list) or not section:
            raise ValueError(f"{where}.3d: expected a list of layer names, got {section!r}")
        for i, name in enumerate(section):
            _check_name(name, f"{where}.3d[{i}]")
            if name in section[:i]:
                raise ValueError(f"{where}.3d[{i}]: layer {name!r} is listed twice")
        layers_3d = frozenset(section)

    return FloorPlanLayers(layers_2d, layers_3d)


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
    'FloorPlanLayers',
    'parse_layers',
    'pop_layer',
    'apply_layer',
]
