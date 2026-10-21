"""
Texture management for 3D model generation.

Materials (.mtl files) reference texture files with ``map_Kd``. The same
lookup is used for procedurally generated elements and for external models:

1. the folder that contains the .mtl file (external models that ship their
   own textures, e.g. models/models_3rd_party/<model>/),
2. the common texture folder ``textures/``.

Procedural elements take their material from
``models/procedural/<element_type>/<element_type>.mtl``.
Example: 'generic_storage' → models/procedural/generic_storage/generic_storage.mtl
"""

from pathlib import Path

PACKAGE_ROOT = Path(__file__).parent.parent
TEXTURES_DIR = PACKAGE_ROOT / 'textures'
PROCEDURAL_MODELS_DIR = PACKAGE_ROOT / 'models' / 'procedural'


def find_texture(texture_ref: str | Path, mtl_dir: Path, textures_dir: Path = TEXTURES_DIR) -> Path | None:
    """
    Find a texture referenced from a .mtl file.

    Args:
        texture_ref: Texture reference as written in the .mtl file (e.g. 'wall.jpg')
        mtl_dir: Folder that contains the .mtl file
        textures_dir: Common texture folder

    Returns:
        Absolute path to the texture file, or None if not found
    """
    for base in (Path(mtl_dir), Path(textures_dir)):
        candidate = base / texture_ref
        if candidate.exists():
            return candidate.resolve()
    return None


class TextureManager:
    """
    Manages material and texture file resolution for 3D export.

    Responsibilities:
        - Locate the material (.mtl) of procedural element types
        - Resolve texture references from .mtl files
    """

    def __init__(
            self,
            procedural_models_dir: Path = PROCEDURAL_MODELS_DIR,
            textures_dir: Path = TEXTURES_DIR
    ):
        """
        Initialize texture manager.

        Args:
            procedural_models_dir: Folder with per-element-type material folders (models/procedural/)
            textures_dir: Common texture folder (textures/)
        """
        self.procedural_models_dir = Path(procedural_models_dir)
        self.textures_dir = Path(textures_dir)

    def get_procedural_mtl(self, element_type: str) -> Path | None:
        """
        Get the .mtl file of a procedural element type.

        Args:
            element_type: Type of element from registry (e.g., 'wall', 'generic_storage')

        Returns:
            Path to models/procedural/<element_type>/<element_type>.mtl, or None if it does not exist
        """
        mtl_path = self.procedural_models_dir / element_type / f"{element_type}.mtl"
        return mtl_path if mtl_path.exists() else None

    def find_texture(self, texture_ref: str | Path, mtl_dir: Path) -> Path | None:
        """
        Find a texture referenced from a .mtl file located in ``mtl_dir``.

        Searches ``mtl_dir`` first, then the common texture folder.
        """
        return find_texture(texture_ref, mtl_dir, self.textures_dir)


# Export public API
__all__ = [
    'TextureManager',
    'find_texture',
    'TEXTURES_DIR',
    'PROCEDURAL_MODELS_DIR',
]
