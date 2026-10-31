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


# Primitives with more triangle corners than this are summarized (count, bounding box, mean)
# instead of listing every corner, to keep golden files small (e.g. detailed external models).
_MAX_LISTED_CORNERS = 600


def _round(value: float, decimals: int) -> float:
    return round(float(value), decimals) + 0.0  # + 0.0 turns -0.0 into 0.0


def _round_list(values, decimals: int) -> list:
    return [_round(v, decimals) for v in values]


def _node_matrix(node: dict) -> np.ndarray:
    """Local 4x4 transform of a glTF node (``matrix`` or translation/rotation/scale)."""
    if 'matrix' in node:
        return np.array(node['matrix'], dtype=float).reshape(4, 4).T   # glTF stores column-major
    t = np.array(node.get('translation', [0.0, 0.0, 0.0]), dtype=float)
    x, y, z, w = node.get('rotation', [0.0, 0.0, 0.0, 1.0])
    s = np.array(node.get('scale', [1.0, 1.0, 1.0]), dtype=float)
    rotation = np.array([
        [1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
        [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
        [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)],
    ])
    matrix = np.eye(4)
    matrix[:3, :3] = rotation * s
    matrix[:3, 3] = t
    return matrix


def _world_matrices(data: dict) -> dict[int, np.ndarray]:
    """World transform of every node (parent chain composed)."""
    nodes = data.get('nodes', [])
    parent = {child: index for index, node in enumerate(nodes) for child in node.get('children', [])}
    cache: dict[int, np.ndarray] = {}

    def world(index: int) -> np.ndarray:
        if index not in cache:
            local = _node_matrix(nodes[index])
            cache[index] = world(parent[index]) @ local if index in parent else local
        return cache[index]

    return {index: world(index) for index in range(len(nodes))}


def _material_summary(gltf: Gltf, material: dict, decimals: int) -> dict:
    pbr = material.get('pbrMetallicRoughness', {})
    uri = gltf.texture_uri(material)
    specular = material.get('extensions', {}).get('KHR_materials_specular')
    return {
        'texture': Path(uri).name if uri else None,
        'baseColorFactor': _round_list(pbr.get('baseColorFactor', []), decimals),
        'alphaMode': material.get('alphaMode', 'OPAQUE'),
        'roughnessFactor': _round(pbr['roughnessFactor'], decimals) if 'roughnessFactor' in pbr else None,
        'specular': None if specular is None else {
            'specularFactor': _round(specular.get('specularFactor', 1.0), decimals),
            'specularColorFactor': _round_list(specular.get('specularColorFactor', [1.0, 1.0, 1.0]), decimals),
        },
        'doubleSided': bool(material.get('doubleSided', False)),
    }


def _corner_summary(values: np.ndarray, decimals: int) -> list | dict:
    """Per-corner values (rounded), or count/bbox/mean for very large primitives."""
    if len(values) > _MAX_LISTED_CORNERS:
        return {
            'corners': int(len(values)),
            'min': _round_list(values.min(axis=0), decimals),
            'max': _round_list(values.max(axis=0), decimals),
            'mean': _round_list(values.mean(axis=0), decimals),
        }
    return [_round_list(v, decimals) for v in values]


def gltf_summary(path: Path, decimals: int = 5) -> dict:
    """
    Meaning-level summary of a glTF for the 3D golden comparison.

    Keyed by node name (for procedural elements equal to the mesh name; unique for
    external models, whose meshes are all called ``model``). Per node: its world
    transform (only if not identity) and per primitive:
      - material: texture file name, baseColorFactor, alphaMode, roughnessFactor,
        KHR_materials_specular, doubleSided
      - triangles: number of triangles
      - POSITION / TEXCOORD_0: the values at every triangle corner (via the indices,
        so the summary records which faces each material covers), rounded to ``decimals``

    Paths, buffer layout and ``extras`` are not included.
    """
    gltf = Gltf(path)
    data = gltf.data
    materials = data.get('materials', [])
    meshes = data.get('meshes', [])
    world = _world_matrices(data)
    summary: dict[str, dict] = {}

    for node_index, node in enumerate(data.get('nodes', [])):
        if 'mesh' not in node:
            continue
        mesh = meshes[node['mesh']]
        name = node.get('name') or mesh.get('name') or f'node_{node_index}'
        key, n = name, 2
        while key in summary:                       # keep entries for repeated names apart
            key, n = f'{name}#{n}', n + 1

        entry: dict = {}
        if not np.allclose(world[node_index], np.eye(4)):
            entry['world_matrix'] = [_round_list(row, decimals) for row in world[node_index]]
        primitives = []
        for primitive in mesh['primitives']:
            attributes = primitive.get('attributes', {})
            corners = (gltf.accessor(primitive['indices']).reshape(-1) if 'indices' in primitive
                       else np.arange(gltf.data['accessors'][attributes['POSITION']]['count']))
            item: dict = {}
            if primitive.get('material') is not None:
                item['material'] = _material_summary(gltf, materials[primitive['material']], decimals)
            item['triangles'] = int(len(corners) // 3)
            for attribute in ('POSITION', 'TEXCOORD_0'):
                if attribute in attributes:
                    values = gltf.accessor(attributes[attribute]).astype(float)[corners]
                    item[attribute] = _corner_summary(values, decimals)
            primitives.append(item)
        entry['primitives'] = primitives
        summary[key] = entry
    return summary


def write_summary(summary: dict, path: Path) -> None:
    """Write a summary as JSON (nodes in scene order, one vertex per line) for readable diffs."""

    def dump(value, indent: int) -> str:
        pad, inner = ' ' * indent, ' ' * (indent + 1)
        if isinstance(value, dict):
            if not value:
                return '{}'
            items = [f'{inner}{json.dumps(k)}: {dump(v, indent + 1)}' for k, v in value.items()]
            return '{\n' + ',\n'.join(items) + '\n' + pad + '}'
        if isinstance(value, list) and value and not all(isinstance(v, (int, float)) for v in value):
            return '[\n' + ',\n'.join(inner + dump(v, indent + 1) for v in value) + '\n' + pad + ']'
        return json.dumps(value)

    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(dump(summary, 0) + '\n')


def _numbers_differ(expected, actual, atol: float) -> str | None:
    """Describe the difference of two equally shaped numeric lists, or None if within ``atol``."""
    try:
        a, b = np.asarray(expected, dtype=float), np.asarray(actual, dtype=float)
    except ValueError:
        return 'values differ'
    if a.shape != b.shape:
        return f'shape {a.shape} != {b.shape}'
    deviation = np.abs(a - b)
    if np.all(deviation <= atol):
        return None
    return f'{int(np.sum(deviation > atol))} of {deviation.size} values differ, max deviation {deviation.max():.6g}'


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
            return [f"{path}: {len(expected)} entries expected, got {len(actual)}"]
        numeric = expected and all(isinstance(v, (int, float, list)) for v in expected) \
            and not any(isinstance(v, (dict, str, bool)) or v is None for v in expected)
        if numeric:
            problem = _numbers_differ(expected, actual, atol)
            return [] if problem is None else [f"{path}: {problem}"]
        diffs = []
        for i, (e, a) in enumerate(zip(expected, actual)):
            diffs += compare_summaries(e, a, f"{path}[{i}]", atol)
        return diffs
    if isinstance(expected, bool) or isinstance(actual, bool):
        return [] if expected == actual else [f"{path}: {_short(expected)} != {_short(actual)}"]
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)):
        return [] if abs(float(expected) - float(actual)) <= atol else [f"{path}: {expected} != {actual}"]
    return [] if expected == actual else [f"{path}: {_short(expected)} != {_short(actual)}"]


def _short(value, limit: int = 80) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit] + '...'
