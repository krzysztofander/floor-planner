"""Unit tests: textures named in YAML are searched relative to the YAML files (floor_planner/texture_manager.py)."""

from floor_planner.texture_manager import TextureManager


def _touch(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(b'')
    return path


def test_yaml_texture_found_relative_to_yaml_dir(tmp_path):
    texture = _touch(tmp_path / 'tekstury' / 'glass.jpg')
    (tmp_path / 'project').mkdir()
    manager = TextureManager(textures_dir=tmp_path / 'textures', yaml_dirs=[tmp_path / 'project'])
    assert manager.find_texture('../tekstury/glass.jpg', tmp_path / 'mtl', from_yaml=True) == texture.resolve()


def test_yaml_dirs_searched_in_order_before_mtl_and_textures(tmp_path):
    first = _touch(tmp_path / 'first' / 'wood.jpg')
    _touch(tmp_path / 'second' / 'wood.jpg')
    _touch(tmp_path / 'mtl' / 'wood.jpg')
    _touch(tmp_path / 'textures' / 'wood.jpg')
    manager = TextureManager(textures_dir=tmp_path / 'textures',
                             yaml_dirs=[tmp_path / 'first', tmp_path / 'second'])
    assert manager.find_texture('wood.jpg', tmp_path / 'mtl', from_yaml=True) == first.resolve()


def test_yaml_texture_falls_back_to_mtl_dir_and_textures(tmp_path):
    in_textures = _touch(tmp_path / 'textures' / 'wood' / 'oak.jpg')
    manager = TextureManager(textures_dir=tmp_path / 'textures', yaml_dirs=[tmp_path / 'project'])
    assert manager.find_texture('wood/oak.jpg', tmp_path / 'mtl', from_yaml=True) == in_textures.resolve()


def test_mtl_texture_ignores_yaml_dirs(tmp_path):
    _touch(tmp_path / 'project' / 'oak.jpg')
    in_mtl_dir = _touch(tmp_path / 'mtl' / 'oak.jpg')
    manager = TextureManager(textures_dir=tmp_path / 'textures', yaml_dirs=[tmp_path / 'project'])
    assert manager.find_texture('oak.jpg', tmp_path / 'mtl') == in_mtl_dir.resolve()
    assert manager.find_texture('missing.jpg', tmp_path / 'mtl', from_yaml=True) is None
