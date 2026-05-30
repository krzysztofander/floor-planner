"""
Texture management for 3D model generation.

This module handles texture file resolution, path management for floor plan
elements. Element types from registry determine folder and texture names directly.

Naming convention:
- Element type from registry → folder name and base texture name
- Example: 'generic_storage' → folder 'generic_storage/', file 'generic_storage.jpg'
"""

from pathlib import Path
from typing import Union
import shutil


class TextureManager:
    """
    Manages texture file resolution and path handling for 3D export.
    
    Responsibilities:
        - Resolve default textures per element type
        - Normalize single/multi-texture specifications
        - Copy textures to output directory
        - Validate texture file paths
        - Fallback to dummy textures when real textures not found
    """
    
    def __init__(self, default_texture_dir: Path, output_texture_dir: Path, fallback_texture_dir: Path = None):
        """
        Initialize texture manager.
        
        Args:
            default_texture_dir: Path to default textures folder (e.g., textures/defaults/)
            output_texture_dir: Path to output textures folder (e.g., 3d_output/textures/)
            fallback_texture_dir: Path to fallback textures folder (e.g., textures/fallback/)
        """
        self.default_texture_dir = Path(default_texture_dir)
        self.output_texture_dir = Path(output_texture_dir)
        self.fallback_texture_dir = Path(fallback_texture_dir) if fallback_texture_dir else None
        self._copied_textures = set()  # Track already copied textures to avoid duplicates
    
    def get_default_textures(self, element_type: str) -> dict[str, str]:
        """
        Get default texture filenames for an element type.
        
        Uses registry key as base texture name.
        
        Args:
            element_type: Type of element from registry (e.g., 'wall', 'generic_storage')
            
        Returns:
            Dict mapping face name 'all' to the base texture filename.
            
        Examples:
            get_default_textures('wall') → {'all': 'wall.jpg'}
            get_default_textures('generic_storage') → {'all': 'generic_storage.jpg'}
        """
        return {'all': f"{element_type}.jpg"}
    
    def normalize_texture_spec(self, texture_spec: Union[str, dict[str, str], None], 
                               element_type: str) -> dict[str, str]:
        """
        Normalize texture specification to dict format.
        
        Args:
            texture_spec: User-provided texture spec (string, dict, or None)
            element_type: Type of element from registry (for default lookup)
            
        Returns:
            Dict mapping face names to texture paths
            
        Examples:
            normalize_texture_spec("wood.jpg", "desk")
            -> {'all': 'wood.jpg'}
            
            normalize_texture_spec({'front': 'a.jpg', 'frame': 'b.jpg'}, "door")
            -> {'front': 'a.jpg', 'frame': 'b.jpg'}
            
            normalize_texture_spec(None, "generic_storage")
            -> {'all': '/path/to/textures/defaults/generic_storage/generic_storage.jpg'}
        """
        if texture_spec is None:
            # Use defaults - check both defaults and fallback in per-element subdirectories
            default_textures = self.get_default_textures(element_type)
            result = {}
            
            # Element subdirectory matches element_type exactly
            element_subdir = element_type
            
            for face, filename in default_textures.items():
                # Try .png first (for alpha channel support), then .jpg
                png_filename = filename.replace('.jpg', '.png')
                
                found = False
                
                # Check defaults directory first
                default_dir = self.default_texture_dir / element_subdir
                if default_dir.exists():
                    default_png_path = default_dir / png_filename
                    default_jpg_path = default_dir / filename
                    
                    if default_png_path.exists():
                        result[face] = str(default_png_path.resolve())
                        found = True
                    elif default_jpg_path.exists():
                        result[face] = str(default_jpg_path.resolve())
                        found = True
                
                # Then check fallback directory
                if not found and self.fallback_texture_dir:
                    fallback_dir = self.fallback_texture_dir / element_subdir
                    if fallback_dir.exists():
                        fallback_png = fallback_dir / png_filename
                        fallback_jpg = fallback_dir / filename
                        
                        if fallback_png.exists():
                            result[face] = str(fallback_png.resolve())
                            found = True
                        elif fallback_jpg.exists():
                            result[face] = str(fallback_jpg.resolve())
                            found = True
                
                # If still not found, use default.jpg from default subdirectory
                if not found:
                    default_default = self.fallback_texture_dir / 'default' / 'default.jpg' if self.fallback_texture_dir else None
                    if default_default and default_default.exists():
                        result[face] = str(default_default.resolve())
                    else:
                        # Last resort: use the expected path (will fail later with clear error)
                        result[face] = str((self.default_texture_dir / element_subdir / filename).resolve())
            
            return result
        
        elif isinstance(texture_spec, str):
            # Single texture for all faces
            return {'all': texture_spec}
        
        elif isinstance(texture_spec, dict):
            # Already in dict format
            return texture_spec.copy()
        
        else:
            raise ValueError(f"Invalid texture specification: {texture_spec}. "
                           f"Expected string, dict, or None.")
    
    def resolve_element_textures(self, element_type: str, 
                                 texture_spec: Union[str, dict[str, str], None],
                                 config_dir: Path) -> dict[str, Path]:
        """
        Resolve element textures to absolute paths.
        
        Args:
            element_type: Type of element from registry
            texture_spec: User-provided texture specification
            config_dir: Directory containing the YAML config file (for relative path resolution)
            
        Returns:
            Dict mapping face names to absolute texture file paths
        """
        # Normalize to dict format
        texture_dict = self.normalize_texture_spec(texture_spec, element_type)
        
        # Resolve each texture path
        resolved = {}
        for face, texture_path_str in texture_dict.items():
            texture_path = Path(texture_path_str)
            
            # If relative path, resolve relative to config directory
            if not texture_path.is_absolute():
                texture_path = config_dir / texture_path
            
            # Check if file exists
            if not texture_path.exists():
                print(f"Warning: Texture file not found: {texture_path}")
                print(f"  Looking for fallback texture for {element_type}")
                
                # Fall back to default texture
                default_textures = self.get_default_textures(element_type)
                if face in default_textures:
                    filename = default_textures[face]
                elif 'all' in default_textures:
                    filename = default_textures['all']
                else:
                    filename = f'{element_type}.jpg'
                
                # Try .png first, then .jpg
                png_filename = filename.replace('.jpg', '.png')
                
                # Element subdirectory matches element_type exactly
                element_subdir = element_type
                
                found = False
                
                # Try defaults directory first
                default_dir = self.default_texture_dir / element_subdir
                if default_dir.exists():
                    texture_path = default_dir / png_filename
                    if texture_path.exists():
                        found = True
                    else:
                        texture_path = default_dir / filename
                        if texture_path.exists():
                            found = True
                
                # If still not found, check fallback directory
                if not found and self.fallback_texture_dir:
                    fallback_dir = self.fallback_texture_dir / element_subdir
                    if fallback_dir.exists():
                        fallback_png = fallback_dir / png_filename
                        fallback_jpg = fallback_dir / filename
                        if fallback_png.exists():
                            print(f"  Using fallback: {fallback_png.name}")
                            texture_path = fallback_png
                            found = True
                        elif fallback_jpg.exists():
                            print(f"  Using fallback: {fallback_jpg.name}")
                            texture_path = fallback_jpg
                            found = True
                
                # Last resort: default.jpg in default subdirectory
                if not found:
                    default_default = self.fallback_texture_dir / 'default' / 'default.jpg' if self.fallback_texture_dir else None
                    if default_default and default_default.exists():
                        texture_path = default_default
                    else:
                        print(f"  Fallback not found either: {filename}")
            
            resolved[face] = texture_path.resolve()
        
        return resolved
    
    def copy_texture_to_output(self, texture_path: Path, relative_path: str) -> Path:
        """
        Copy texture file to output directory.
        
        Args:
            texture_path: Source texture file path
            relative_path: Relative path within output directory (e.g., 'defaults/wall.jpg')
            
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
            print(f"Warning: Cannot copy texture, file not found: {texture_path}")
        
        return output_path
    
    def get_relative_texture_path(self, texture_path: Path) -> str:
        """
        Get texture path relative to output directory for MTL file references.
        
        Args:
            texture_path: Absolute path to texture file
            
        Returns:
            Relative path string for use in MTL file (e.g., 'textures/defaults/wall.jpg')
        """
        try:
            # Try to get relative path from output directory's parent
            # (MTL files are in output dir, textures are in output/textures/)
            return 'textures/' + texture_path.name
        except ValueError:
            # If not relative, just use filename
            return 'textures/' + texture_path.name


# Convenience functions for backward compatibility

def get_default_texture(element_type: str) -> str:
    """
    Get default texture filename for an element type (single texture).
    
    Args:
        element_type: Type of element from registry
        
    Returns:
        Default texture filename (e.g., 'generic_storage.jpg')
    """
    # Base texture always uses element_type as filename
    return f"{element_type}.jpg"


def validate_texture_faces(texture_dict: dict[str, str], valid_faces: list[str]) -> bool:
    """
    Validate that texture dict keys match element's valid face names.
    
    Args:
        texture_dict: Dict of face → texture mappings
        valid_faces: List of valid face names for this element
        
    Returns:
        True if all faces are valid, False otherwise (logs warnings)
    """
    valid = True
    for face in texture_dict.keys():
        if face not in valid_faces and face != 'all':
            print(f"Warning: Invalid face name '{face}'. Valid faces: {valid_faces}")
            valid = False
    return valid


# Export public API
__all__ = [
    'TextureManager',
    'get_default_texture',
    'validate_texture_faces',
    'STANDARD_FACE_NAMES',
]
