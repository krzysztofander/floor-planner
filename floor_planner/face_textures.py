"""
Per-face textures and lighting for box-like elements (fine-grained-textures-for-boxes).

Box elements (``RectangularGeometry3D``) accept a ``textures`` YAML structure:

    textures:
      default:   {texture: wood/pear_wood.jpg, scale_relative: 2.0}   # all faces (and extras)
      sides:     {diffuse: [0.9, 0.9, 0.9]}               # front, back, left, right
      top:       {texture: plain_named/brown-wood-table.jpg, scale_meters: 0.3}
      extras:                                              # free face names
        inside_bottom: {texture: window_sill.jpg}

Each property of a face is resolved through these levels (first one that sets it wins):

    box face:    face entry    -> sides (vertical faces) -> default -> class default -> .mtl -> built-in
    extra face:  extras.<name>                            -> default -> class default -> .mtl -> built-in

See docs/features/fine-grained-textures-for-boxes.md.
"""

from dataclasses import dataclass, fields
from numbers import Real
from pathlib import Path


BOX_FACES = ('front', 'back', 'left', 'right', 'top', 'bottom')
SIDE_FACES = ('front', 'back', 'left', 'right')
GROUP_KEYS = ('default', 'sides')
EXTRAS_KEY = 'extras'


class _Unset:
    """Marker for a key that is not given (as opposed to an explicit ``null``)."""

    def __repr__(self) -> str:
        return 'UNSET'


UNSET = _Unset()


def _check_number(where: str, key: str, value, minimum: float | None = None,
                  maximum: float | None = None, exclusive_minimum: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, Real):
        raise ValueError(f"{where}.{key}: expected a number, got {value!r}")
    value = float(value)
    if minimum is not None and (value <= minimum if exclusive_minimum else value < minimum):
        relation = '>' if exclusive_minimum else '>='
        raise ValueError(f"{where}.{key}: must be {relation} {minimum}, got {value}")
    if maximum is not None and value > maximum:
        raise ValueError(f"{where}.{key}: must be <= {maximum}, got {value}")
    return value


def _check_color(where: str, key: str, value, maximum: float | None) -> tuple[float, float, float]:
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError(f"{where}.{key}: expected [r, g, b], got {value!r}")
    return tuple(_check_number(where, key, c, minimum=0.0, maximum=maximum) for c in value)


@dataclass(frozen=True)
class FaceSpec:
    """One entry of the ``textures`` structure (a face, a group, or an extra face)."""

    texture: str | None | _Unset = UNSET
    scale_relative: float | _Unset = UNSET
    scale_meters: float | _Unset = UNSET
    diffuse: tuple[float, float, float] | _Unset = UNSET
    specular: tuple[float, float, float] | _Unset = UNSET
    shininess: float | _Unset = UNSET
    opacity: float | _Unset = UNSET
    double_sided: bool | _Unset = UNSET

    @classmethod
    def from_yaml(cls, data, where: str) -> 'FaceSpec':
        """
        Validate one entry and build a ``FaceSpec``.

        :param data:
            mapping from YAML (``None`` is treated as an empty entry)
        :param where:
            location used in error messages, e.g. ``'textures.top'``
        :raises ValueError:
            if a key is unknown or a value has a wrong type or range
        """
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise ValueError(f"{where}: expected a mapping, got {data!r}")

        known = {f.name for f in fields(cls)}
        unknown = set(data) - known
        if unknown:
            raise ValueError(f"{where}: unknown key(s) {sorted(unknown)}; allowed: {sorted(known)}")
        if 'scale_relative' in data and 'scale_meters' in data:
            raise ValueError(f"{where}: set either 'scale_relative' or 'scale_meters', not both")
        for key, value in data.items():
            if value is None and key != 'texture':
                raise ValueError(f"{where}.{key}: null is only allowed for 'texture'")

        values = {}
        if 'texture' in data:
            texture = data['texture']
            if texture is not None and (not isinstance(texture, str) or not texture):
                raise ValueError(f"{where}.texture: expected a file name or null, got {texture!r}")
            values['texture'] = texture
        if 'scale_relative' in data:
            values['scale_relative'] = _check_number(where, 'scale_relative', data['scale_relative'],
                                                     minimum=0.0, exclusive_minimum=True)
        if 'scale_meters' in data:
            values['scale_meters'] = _check_number(where, 'scale_meters', data['scale_meters'],
                                                   minimum=0.0, exclusive_minimum=True)
        if 'diffuse' in data:
            values['diffuse'] = _check_color(where, 'diffuse', data['diffuse'], maximum=1.0)
        if 'specular' in data:
            values['specular'] = _check_color(where, 'specular', data['specular'], maximum=None)
        if 'shininess' in data:
            values['shininess'] = _check_number(where, 'shininess', data['shininess'], minimum=0.0)
        if 'opacity' in data:
            values['opacity'] = _check_number(where, 'opacity', data['opacity'], minimum=0.0, maximum=1.0)
        if 'double_sided' in data:
            if not isinstance(data['double_sided'], bool):
                raise ValueError(f"{where}.double_sided: expected true or false, got {data['double_sided']!r}")
            values['double_sided'] = data['double_sided']
        return cls(**values)

    def scale(self) -> tuple[str, float] | _Unset:
        """Return ``('relative', r)``, ``('meters', m)`` or ``UNSET``."""
        if self.scale_relative is not UNSET:
            return ('relative', self.scale_relative)
        if self.scale_meters is not UNSET:
            return ('meters', self.scale_meters)
        return UNSET


_EMPTY = FaceSpec()


class FaceTextures:
    """Validated ``textures`` structure of one element (or one class default)."""

    def __init__(self, default: FaceSpec = _EMPTY, sides: FaceSpec = _EMPTY,
                 faces: dict[str, FaceSpec] | None = None, extras: dict[str, FaceSpec] | None = None):
        self.default = default
        self.sides = sides
        self.faces = faces or {}
        self.extras = extras or {}

    @classmethod
    def from_yaml(cls, data: dict | None, where: str = 'textures') -> 'FaceTextures':
        """
        Validate a ``textures`` structure.

        :param data:
            mapping from YAML, or ``None`` for an element without ``textures``
        :param where:
            location used in error messages
        :raises ValueError:
            for unknown face names, invalid entries or invalid ``extras`` names
        """
        if data is None:
            return cls()
        if not isinstance(data, dict):
            raise ValueError(f"{where}: expected a mapping, got {data!r}")

        allowed = set(GROUP_KEYS) | set(BOX_FACES) | {EXTRAS_KEY}
        unknown = set(data) - allowed
        if unknown:
            raise ValueError(
                f"{where}: unknown face(s) {sorted(unknown)}; allowed: {sorted(allowed)} "
                f"(put other face names under '{EXTRAS_KEY}')"
            )

        extras_data = data.get(EXTRAS_KEY) or {}
        if not isinstance(extras_data, dict):
            raise ValueError(f"{where}.{EXTRAS_KEY}: expected a mapping, got {extras_data!r}")
        reserved = set(GROUP_KEYS) | set(BOX_FACES) | {EXTRAS_KEY}
        extras = {}
        for name, entry in extras_data.items():
            if not isinstance(name, str) or not name:
                raise ValueError(f"{where}.{EXTRAS_KEY}: invalid face name {name!r}")
            if name in reserved:
                raise ValueError(f"{where}.{EXTRAS_KEY}.{name}: '{name}' is not allowed as an extra face name")
            extras[name] = FaceSpec.from_yaml(entry, f"{where}.{EXTRAS_KEY}.{name}")

        return cls(
            default=FaceSpec.from_yaml(data.get('default'), f"{where}.default"),
            sides=FaceSpec.from_yaml(data.get('sides'), f"{where}.sides"),
            faces={face: FaceSpec.from_yaml(data[face], f"{where}.{face}") for face in BOX_FACES if face in data},
            extras=extras,
        )

    def chain(self, name: str) -> list[FaceSpec]:
        """Return the entries that apply to face ``name``, most specific first."""
        if name in BOX_FACES:
            specs = [self.faces.get(name, _EMPTY)]
            if name in SIDE_FACES:
                specs.append(self.sides)
        else:
            specs = [self.extras.get(name, _EMPTY)]
        specs.append(self.default)
        return specs

    def is_empty(self) -> bool:
        """True if no entry sets anything."""
        specs = [self.default, self.sides, *self.faces.values(), *self.extras.values()]
        return all(spec == _EMPTY for spec in specs)


@dataclass(frozen=True)
class ResolvedFace:
    """
    Final look of one face.

    ``None`` means "not set anywhere" (the exporter then uses its built-in value);
    ``texture_path`` is ``None`` for an untextured face.
    """

    texture_path: Path | None
    diffuse: tuple[float, ...] | None
    diffuse_from_mtl: bool
    specular: tuple[float, ...] | None
    shininess: float | None
    opacity: float | None
    scale_mode: str
    scale_value: float
    double_sided: bool = False

    @property
    def material_key(self) -> tuple:
        """Everything that affects the material (i.e. all but the scale)."""
        return (self.texture_path, self.diffuse, self.diffuse_from_mtl,
                self.specular, self.shininess, self.opacity, self.double_sided)


def resolve_face(name: str, element_textures: FaceTextures, class_textures: FaceTextures,
                 mtl_props: dict, find_texture) -> ResolvedFace:
    """
    Resolve the look of face ``name``.

    :param name:
        box face name (``front``, ``back``, ...) or extra face name
    :param element_textures:
        the element's ``textures`` structure
    :param class_textures:
        the element class's default ``textures`` structure
    :param mtl_props:
        properties of the element type's ``.mtl`` as parsed by the glTF exporter
        (``diffuse_texture``, ``diffuse``, ``specular``, ``shininess``, ``transparency``)
    :param find_texture:
        callable ``(texture_ref, source) -> Path``; resolves a texture reference and
        raises/reports if it cannot be found (``source`` describes where it came from)
    """
    specs = element_textures.chain(name) + class_textures.chain(name)

    def first(attr: str):
        for spec in specs:
            value = getattr(spec, attr)
            if value is not UNSET:
                return value
        return UNSET

    texture = first('texture')
    if texture is UNSET:
        texture_ref = mtl_props.get('diffuse_texture')
        texture_path = find_texture(texture_ref, '.mtl map_Kd') if texture_ref else None
    else:
        texture_path = find_texture(texture, f"textures.{name}") if texture is not None else None

    diffuse = first('diffuse')
    diffuse_from_mtl = diffuse is UNSET and 'diffuse' in mtl_props
    if diffuse is UNSET:
        diffuse = tuple(mtl_props['diffuse']) if diffuse_from_mtl else None

    specular = first('specular')
    if specular is UNSET:
        specular = tuple(mtl_props['specular']) if 'specular' in mtl_props else None

    shininess = first('shininess')
    if shininess is UNSET:
        shininess = mtl_props.get('shininess')

    opacity = first('opacity')
    if opacity is UNSET:
        opacity = float(mtl_props['transparency']) if 'transparency' in mtl_props else None

    scale = UNSET
    for spec in specs:
        scale = spec.scale()
        if scale is not UNSET:
            break
    scale_mode, scale_value = scale if scale is not UNSET else ('relative', 1.0)

    # No .mtl equivalent; glTF default is single-sided (back faces culled)
    double_sided = first('double_sided')
    double_sided = False if double_sided is UNSET else double_sided

    return ResolvedFace(texture_path, diffuse, diffuse_from_mtl, specular, shininess, opacity,
                        scale_mode, scale_value, double_sided)


def uv_repeats(resolved: ResolvedFace, width: float, height: float) -> tuple[float, float]:
    """
    UV range (u_max, v_max) of a face of ``width`` x ``height`` metres.

    Stretched / ``scale_relative: r`` -> (r, r); ``scale_meters: m`` -> (width / m, height / m).
    """
    if resolved.scale_mode == 'meters':
        return width / resolved.scale_value, height / resolved.scale_value
    return resolved.scale_value, resolved.scale_value


__all__ = [
    'BOX_FACES',
    'SIDE_FACES',
    'UNSET',
    'FaceSpec',
    'FaceTextures',
    'ResolvedFace',
    'resolve_face',
    'uv_repeats',
]
