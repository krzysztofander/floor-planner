"""
glTF helpers for the scene tests: loading, invariants and a meaning-level summary.

Invariants (docs/features/pytest-regression-suite.md, decision 8):
  (b) every primitive has a material; every texture it uses exists next to the .gltf
  (c) POSITION / NORMAL / TEXCOORD_0 counts match, no NaN/inf, indices in range
"""

import base64
import json
from pathlib import Path

import numpy as np


_COMPONENT_TYPES = {5120: np.int8, 5121: np.uint8, 5122: np.int16,
                    5123: np.uint16, 5125: np.uint32, 5126: np.float32}
_COMPONENT_COUNTS = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT2': 4, 'MAT3': 9, 'MAT4': 16}
_VERTEX_ATTRIBUTES = ('POSITION', 'NORMAL', 'TEXCOORD_0')


class Gltf:
    """A loaded glTF file with its buffers."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = json.loads(self.path.read_text())
        self.buffers = [self._load_buffer(b) for b in self.data.get('buffers', [])]

    def _load_buffer(self, buffer: dict) -> bytes:
        uri = buffer['uri']
        if uri.startswith('data:'):
            return base64.b64decode(uri.split(',', 1)[1])
        buffer_path = self.path.parent / uri
        assert buffer_path.exists(), f"{self.path.name}: buffer file {uri} does not exist"
        return buffer_path.read_bytes()

    def accessor(self, index: int) -> np.ndarray:
        """Decode accessor ``index`` into an array of shape (count, components)."""
        acc = self.data['accessors'][index]
        view = self.data['bufferViews'][acc['bufferView']]
        dtype = _COMPONENT_TYPES[acc['componentType']]
        components = _COMPONENT_COUNTS[acc['type']]
        offset = view.get('byteOffset', 0) + acc.get('byteOffset', 0)
        values = np.frombuffer(self.buffers[view['buffer']], dtype=dtype,
                               count=acc['count'] * components, offset=offset)
        return values.reshape(acc['count'], components)

    def primitives(self):
        """Yield (mesh name, primitive index, primitive) for all primitives."""
        for mesh_index, mesh in enumerate(self.data.get('meshes', [])):
            name = mesh.get('name', f'mesh_{mesh_index}')
            for prim_index, primitive in enumerate(mesh['primitives']):
                yield name, prim_index, primitive

    def texture_uri(self, material: dict) -> str | None:
        texture = material.get('pbrMetallicRoughness', {}).get('baseColorTexture')
        if texture is None:
            return None
        return self.data['images'][self.data['textures'][texture['index']]['source']]['uri']


def check_gltf_invariants(path: Path) -> None:
    """
    Check invariants (b) and (c) of one glTF file; raise AssertionError with
    all problems found.
    """
    gltf = Gltf(path)
    materials = gltf.data.get('materials', [])
    problems = []

    for mesh, prim_index, primitive in gltf.primitives():
        where = f"{mesh} primitive {prim_index}"

        # (b) material and its texture
        material_index = primitive.get('material')
        if material_index is None or not 0 <= material_index < len(materials):
            problems.append(f"{where}: no valid material (material={material_index})")
        else:
            uri = gltf.texture_uri(materials[material_index])
            if uri is not None and not (gltf.path.parent / uri).exists():
                problems.append(f"{where}: texture {uri} does not exist")

        # (c) vertex attributes and indices
        attributes = primitive.get('attributes', {})
        counts = {}
        for name in _VERTEX_ATTRIBUTES:
            if name in attributes:
                values = gltf.accessor(attributes[name])
                counts[name] = len(values)
                if not np.all(np.isfinite(values)):
                    problems.append(f"{where}: {name} contains NaN or inf")
        if len(set(counts.values())) > 1:
            problems.append(f"{where}: attribute counts differ {counts}")
        if 'indices' in primitive and 'POSITION' in counts:
            indices = gltf.accessor(primitive['indices'])
            if indices.size and int(indices.max()) >= counts['POSITION']:
                problems.append(f"{where}: index {int(indices.max())} >= POSITION count {counts['POSITION']}")

    assert not problems, f"{path.name}: " + "; ".join(problems)


def gltf_summary(path: Path, decimals: int = 5) -> dict:
    """
    Meaning-level summary of a glTF for the 3D golden comparison, keyed by mesh name.

    Per primitive: material (texture file name, baseColorFactor, alphaMode,
    roughnessFactor, specular extension) and POSITION / TEXCOORD_0 rounded to
    ``decimals``. Paths, buffer layout and node matrices are not included.
    """
    gltf = Gltf(path)
    materials = gltf.data.get('materials', [])
    summary: dict[str, list] = {}
    for mesh, _, primitive in gltf.primitives():
        entry = {}
        material_index = primitive.get('material')
        if material_index is not None:
            material = materials[material_index]
            pbr = material.get('pbrMetallicRoughness', {})
            uri = gltf.texture_uri(material)
            entry['material'] = {
                'texture': Path(uri).name if uri else None,
                'baseColorFactor': [round(c, decimals) for c in pbr.get('baseColorFactor', [])],
                'alphaMode': material.get('alphaMode', 'OPAQUE'),
                'roughnessFactor': round(pbr['roughnessFactor'], decimals) if 'roughnessFactor' in pbr else None,
                'specular': material.get('extensions', {}).get('KHR_materials_specular'),
            }
        attributes = primitive.get('attributes', {})
        for name in ('POSITION', 'TEXCOORD_0'):
            if name in attributes:
                entry[name] = np.round(gltf.accessor(attributes[name]).astype(float), decimals).tolist()
        summary.setdefault(mesh, []).append(entry)
    return summary


def compare_summaries(expected, actual, path: str = '', atol: float = 2e-5) -> list[str]:
    """Return a list of differences between two summaries (numbers compared with ``atol``)."""
    if isinstance(expected, dict) and isinstance(actual, dict):
        diffs = []
        for key in sorted(set(expected) | set(actual)):
            if key not in actual:
                diffs.append(f"{path}/{key}: missing")
            elif key not in expected:
                diffs.append(f"{path}/{key}: unexpected")
            else:
                diffs += compare_summaries(expected[key], actual[key], f"{path}/{key}", atol)
        return diffs
    if isinstance(expected, list) and isinstance(actual, list):
        if len(expected) != len(actual):
            return [f"{path}: length {len(expected)} != {len(actual)}"]
        if expected and all(isinstance(v, (int, float, list)) for v in expected):
            try:
                a, b = np.asarray(expected, dtype=float), np.asarray(actual, dtype=float)
                return [] if a.shape == b.shape and np.allclose(a, b, atol=atol) else [f"{path}: values differ"]
            except ValueError:
                pass
        diffs = []
        for i, (e, a) in enumerate(zip(expected, actual)):
            diffs += compare_summaries(e, a, f"{path}[{i}]", atol)
        return diffs
    if isinstance(expected, float) or isinstance(actual, float):
        try:
            return [] if abs(float(expected) - float(actual)) <= atol else [f"{path}: {expected} != {actual}"]
        except (TypeError, ValueError):
            pass
    return [] if expected == actual else [f"{path}: {expected!r} != {actual!r}"]
