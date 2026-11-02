"""Unit tests: hollow 3D geometry of vessel elements (floor_planner/geometry_3d.py VesselGeometry3D)."""

import pytest

from floor_planner.elements.furniture import Basin, Bathtub, Toilet
from floor_planner.elements.furniture.appliances import DoubleSink, SingleSink
from floor_planner.elements.landscaping.water import RectPool
from floor_planner.geometry_3d import VESSEL_INSIDE_FACES


def _key(point):
    return tuple(round(c, 6) for c in point)


def _signed_volume(vertices, indices):
    """Volume enclosed by the mesh; positive when all normals point outwards."""
    volume = 0.0
    for a, b, c in indices:
        (ax, ay, az), (bx, by, bz), (cx, cy, cz) = vertices[a], vertices[b], vertices[c]
        volume += (ax * (by * cz - bz * cy) - ay * (bx * cz - bz * cx) + az * (bx * cy - by * cx)) / 6
    return volume


@pytest.mark.parametrize('angle', [0, 90, 33])
def test_winding_and_normals_point_out_of_the_material(angle):
    tub = Bathtub((1.0, 2.0), angle, length=1.7, thickness=0.8, height=0.6, depth=0.45, vessel_wall_thickness=0.1)
    vertices, indices, _ = tub.generate_vertices_and_indices()

    # Consistent winding: no edge is used twice in the same direction
    edges = {}
    for tri in indices:
        for i in range(3):
            edge = (_key(vertices[tri[i]]), _key(vertices[tri[(i + 1) % 3]]))
            edges[edge] = edges.get(edge, 0) + 1
    # All normals point out of the material: the signed volume equals the material volume
    length, thickness = 1.7 - 0.012, 0.8 - 0.012   # VertInfoLvl03 shrinks furniture by 0.012
    expected = length * thickness * 0.6 - (1.7 - 0.2) * (0.8 - 0.2) * 0.45
    assert _signed_volume(vertices, indices) == pytest.approx(expected, rel=1e-6)
    assert all(count == 1 for count in edges.values()), "an edge is used twice in the same direction"


def test_face_groups():
    _, indices, face_groups = Basin((0, 0)).generate_vertices_and_indices()
    expected = {'front', 'back', 'left', 'right', 'bottom', 'top', *VESSEL_INSIDE_FACES}
    assert set(face_groups) == expected
    assert sorted(t for tris in face_groups.values() for t in tris) == list(range(len(indices)))
    assert len(face_groups['top']) == 8   # rim: 4 strips


@pytest.mark.parametrize('cls, kwargs', [
    (Bathtub, {}), (Basin, {}), (Toilet, {}), (SingleSink, {}), (DoubleSink, {}),
    (RectPool, {'length': 8.0, 'thickness': 4.0}),
])
def test_defaults(cls, kwargs):
    element = cls(anchor_point=(0, 0), **kwargs)
    assert element.depth == pytest.approx(0.8 * element.height)
    assert element.vessel_wall_thickness == pytest.approx(0.1 * min(element.length, element.thickness))


@pytest.mark.parametrize('kwargs', [
    {'depth': 0}, {'depth': 0.6}, {'depth': 0.7},
    {'vessel_wall_thickness': 0}, {'vessel_wall_thickness': 0.4},
])
def test_invalid_parameters(kwargs):
    with pytest.raises(ValueError):
        Bathtub((0, 0), height=0.6, thickness=0.8, **kwargs)
