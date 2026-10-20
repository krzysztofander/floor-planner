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
import shutil

from floor_planner.utils import WarnMsg

PACKAGE_ROOT = Path(__file__).parent.parent
TEXTURES_DIR = PACKAGE_ROOT / 'textures'
PROCEDURAL_MODELS_DIR = PACKAGE_ROOT / 'models' / 'procedural'
DEFAULT_TEXTURE = 'default.jpg'


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


def read_diffuse_texture_ref(mtl_path: Path) -> str | None:
    """
    Return the first ``map_Kd`` reference of a .mtl file, or None if there is none.
    """
    with open(mtl_path, 'r') as f:
        for line in f:
            parts = line.strip().split(None, 1)
            if len(parts) == 2 and parts[0] == 'map_Kd':
                return parts[1].strip()
    return None


class TextureManager:
    """
    Manages texture file resolution and path handling for 3D export.

    Responsibilities:
        - Locate the material (.mtl) of procedural element types
        - Resolve texture references from .mtl files
        - Copy textures to output directory
    """

    def __init__(
            self,
            output_texture_dir: Path,
            procedural_models_dir: Path = PROCEDURAL_MODELS_DIR,
            textures_dir: Path = TEXTURES_DIR
    ):
        """
        Initialize texture manager.

        Args:
            output_texture_dir: Path to output textures folder (e.g., 3d_output/textures/)
            procedural_models_dir: Folder with per-element-type material folders (models/procedural/)
            textures_dir: Common texture folder (textures/)
        """
        self.output_texture_dir = Path(output_texture_dir)
        self.procedural_models_dir = Path(procedural_models_dir)
        self.textures_dir = Path(textures_dir)
        self._copied_textures = set()  # Track already copied textures to avoid duplicates

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

    def resolve_element_textures(self, element_type: str) -> dict[str, Path]:
        """
        Resolve the texture of a procedural element type.

        The texture is the ``map_Kd`` of the element type's .mtl file; when there is
        no .mtl, no ``map_Kd`` or the file is missing, textures/default.jpg is used.

        Args:
            element_type: Type of element from registry

        Returns:
            Dict mapping face name 'all' to the absolute texture file path
        """
        texture_path = None
        mtl_path = self.get_procedural_mtl(element_type)
        if mtl_path:
            texture_ref = read_diffuse_texture_ref(mtl_path)
            if texture_ref:
                texture_path = self.find_texture(texture_ref, mtl_path.parent)
                if texture_path is None:
                    WarnMsg(f"Texture '{texture_ref}' referenced by {mtl_path} not found")
        if texture_path is None:
            texture_path = (self.textures_dir / DEFAULT_TEXTURE).resolve()
        return {'all': texture_path}

    def copy_texture_to_output(self, texture_path: Path, relative_path: str) -> Path:
        """
        Copy texture file to output directory.

        Args:
            texture_path: Source texture file path
            relative_path: Relative path within output directory (e.g., 'wall.jpg')

        Returns:
            Path to copied texture file in output directory
        """
        output_path = self.output_texture_dir / relative_path

        # Skip if already copied
        if str(output_path) in self._copied_textures:
            return output_path

        # Create parent directories if needed
        output_path.parent.mkdir(parents=True, exist_ok=True)

        # Copy file
        if texture_path.exists():
            shutil.copy2(texture_path, output_path)
            self._copied_textures.add(str(output_path))
        else:
            WarnMsg(f"Cannot copy texture, file not found: {texture_path}")

        return output_path

    def get_relative_texture_path(self, texture_path: Path) -> str:
        """
        Get texture path relative to output directory for MTL file references.

        Args:
            texture_path: Absolute path to texture file

        Returns:
            Relative path string for use in MTL file (e.g., 'textures/wall.jpg')
        """
        # MTL files are in output dir, textures are in output/textures/
        return 'textures/' + texture_path.name


# Export public API
__all__ = [
    'TextureManager',
    'find_texture',
    'read_diffuse_texture_ref',
    'TEXTURES_DIR',
    'PROCEDURAL_MODELS_DIR',
]
