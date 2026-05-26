"""
Texture management for 3D model generation.

This module handles texture file resolution, path management, and multi-texture
support for floor plan elements. Elements can specify textures as:
- Single string: applies to all faces
- Dict: different textures for different faces

All texture specifications are normalized to dict format internally for consistent processing.
"""

from pathlib import Path
from typing import Union
import shutil


# Standard face names for multi-texture support
STANDARD_FACE_NAMES = [
    'all',      # All faces (default for single texture)
    'front',    # Front face
    'back',     # Back face
    'top',      # Top face
    'bottom',   # Bottom face
    'sides',    # All vertical sides
    'left',     # Left side
    'right',    # Right side
    'frame',    # Frame/edge (e.g., door frame)
]


# Default texture mappings per element type
# Maps element type to dict of face names → texture filenames
DEFAULT_TEXTURES = {
    # Structural elements
    'wall': {'all': 'wall.jpg'},
    'window': {'all': 'window.jpg'},
    'door': {
        'front': 'door.jpg',
        'back': 'door.jpg',
        'frame': 'door_frame.jpg',
    },
    'floor': {'all': 'floor.jpg'},
    
    # Furniture
    'desk': {
        'top': 'desk.jpg',
        'sides': 'desk.jpg',
    },
    'table': {
        'top': 'table.jpg',
        'sides': 'table.jpg',
    },
    'chair': {'all': 'chair.jpg'},
    'sofa': {'all': 'sofa.jpg'},
    'bed': {'all': 'bed.jpg'},
    'wardrobe': {'all': 'wardrobe.jpg'},
    'bookshelf': {'all': 'bookshelf.jpg'},
    'dresser': {'all': 'dresser.jpg'},
    'nightstand': {'all': 'nightstand.jpg'},
    'tvstand': {'all': 'tvstand.jpg'},
    
    # Appliances
    'refrigerator': {'all': 'refrigerator.jpg'},
    'stove': {'all': 'stove.jpg'},
    'oven': {'all': 'oven.jpg'},
    'dishwasher': {'all': 'dishwasher.jpg'},
    'washer': {'all': 'washer.jpg'},
    'dryer': {'all': 'dryer.jpg'},
    'microwave': {'all': 'microwave.jpg'},
    'rangehood': {'all': 'rangehood.jpg'},
    
    # Bathroom
    'toilet': {'all': 'toilet.jpg'},
    'sink': {'all': 'sink.jpg'},
    'bathtub': {'all': 'bathtub.jpg'},
    'shower': {'all': 'shower.jpg'},
    'bidet': {'all': 'bidet.jpg'},
    
    # Lighting
    'ceiling_lamp': {'all': 'ceiling_lamp.jpg'},
    'wall_lamp': {'all': 'wall_lamp.jpg'},
    
    # Electrical
    'power_outlet': {'all': 'power_outlet.jpg'},
    'switch': {'all': 'switch.jpg'},
    
    # Landscaping
    'tree': {'all': 'tree.jpg'},
    'shrub': {'all': 'shrub.jpg'},
    'hedge': {'all': 'hedge.jpg'},
    'lawn': {'all': 'lawn.jpg'},
    'path': {'all': 'path.jpg'},
    'deck': {'all': 'deck.jpg'},
    'fence': {'all': 'fence.jpg'},
    'pool': {'all': 'pool.jpg'},
    'fountain': {'all': 'fountain.jpg'},
    'pond': {'all': 'pond.jpg'},
    
    # Default fallback
    'default': {'all': 'default.jpg'},
}


class TextureManager:
    """
    Manages texture file resolution and path handling for 3D export.
    
    Responsibilities:
        - Resolve default textures per element type
        - Normalize single/multi-texture specifications
        - Copy textures to output directory
        - Validate texture file paths
    """
    
    def __init__(self, default_texture_dir: Path, output_texture_dir: Path):
        """
        Initialize texture manager.
        
        Args:
            default_texture_dir: Path to default textures folder (e.g., textures/defaults/)
            output_texture_dir: Path to output textures folder (e.g., 3d_output/textures/)
        """
        self.default_texture_dir = Path(default_texture_dir)
        self.output_texture_dir = Path(output_texture_dir)
        self._copied_textures = set()  # Track already copied textures to avoid duplicates
    
    def get_default_textures(self, element_type: str) -> dict[str, str]:
        """
        Get default texture filenames for an element type.
        
        Args:
            element_type: Type of element (e.g., 'wall', 'desk', 'door')
            
        Returns:
            Dict mapping face names to texture filenames
            e.g., {'all': 'wall.jpg'} or {'top': 'desk.jpg', 'sides': 'desk.jpg'}
        """
        # Normalize element type (lowercase, no underscores)
        normalized_type = element_type.lower().replace('_', '')
        
        # Try exact match first
        if element_type in DEFAULT_TEXTURES:
            return DEFAULT_TEXTURES[element_type].copy()
        
        # Try normalized match
        for key in DEFAULT_TEXTURES:
            if key.replace('_', '') == normalized_type:
                return DEFAULT_TEXTURES[key].copy()
        
        # Return default fallback
        return DEFAULT_TEXTURES['default'].copy()
    
    def normalize_texture_spec(self, texture_spec: Union[str, dict[str, str], None], 
                               element_type: str) -> dict[str, str]:
        """
        Normalize texture specification to dict format.
        
        Args:
            texture_spec: User-provided texture spec (string, dict, or None)
            element_type: Type of element (for default lookup)
            
        Returns:
            Dict mapping face names to texture paths
            
        Examples:
            normalize_texture_spec("wood.jpg", "desk")
            -> {'all': 'wood.jpg'}
            
            normalize_texture_spec({'front': 'a.jpg', 'back': 'b.jpg'}, "door")
            -> {'front': 'a.jpg', 'back': 'b.jpg'}
            
            normalize_texture_spec(None, "wall")
            -> {'all': 'textures/defaults/wall.jpg'}
        """
        if texture_spec is None:
            # Use defaults
            default_textures = self.get_default_textures(element_type)
            # Prepend default texture directory path
            return {
                face: str(self.default_texture_dir / filename)
                for face, filename in default_textures.items()
            }
        
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
            element_type: Type of element
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
                print(f"  Falling back to default for {element_type}")
                # Fall back to default
                default_textures = self.get_default_textures(element_type)
                if face in default_textures:
                    texture_path = self.default_texture_dir / default_textures[face]
                elif 'all' in default_textures:
                    texture_path = self.default_texture_dir / default_textures['all']
                else:
                    texture_path = self.default_texture_dir / 'default.jpg'
            
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
        element_type: Type of element
        
    Returns:
        Default texture filename
    """
    textures = DEFAULT_TEXTURES.get(element_type, DEFAULT_TEXTURES['default'])
    return textures.get('all', list(textures.values())[0])


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
    'normalize_texture_spec',
    'validate_texture_faces',
    'STANDARD_FACE_NAMES',
    'DEFAULT_TEXTURES',
]
