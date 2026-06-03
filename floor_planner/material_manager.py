"""
Material management for 3D model generation.

This module handles material property resolution from external .mtl files.
Materials are stored alongside textures in per-element subdirectories.

Example directory structure:
    textures/
        fallback/
            wall/
                wall.jpg
                wall.mtl
            door/
                door.jpg
                door.mtl
"""

from pathlib import Path
from typing import Optional

from floor_planner.utils import WarnMsg


class MaterialManager:
    """
    Manages material property resolution from .mtl files.
    
    Responsibilities:
        - Parse .mtl files to extract Ka, Kd, Ks, Ns values
        - Resolve material files based on texture paths
        - Cache loaded materials for performance
        - Provide fallback to default material if .mtl not found
    """
    
    def __init__(self, default_texture_dir: Path, fallback_texture_dir: Optional[Path] = None):
        """
        Initialize material manager.
        
        Args:
            default_texture_dir: Path to default textures folder (e.g., textures/defaults/)
            fallback_texture_dir: Path to fallback textures folder (e.g., textures/fallback/)
        """
        self.default_texture_dir = Path(default_texture_dir)
        self.fallback_texture_dir = Path(fallback_texture_dir) if fallback_texture_dir else None
        self._material_cache = {}  # Cache loaded materials by mtl file path
    
    def parse_mtl_file(self, mtl_path: Path) -> dict:
        """
        Parse a .mtl file and extract material properties.
        
        Args:
            mtl_path: Path to .mtl file
            
        Returns:
            Dictionary with Ka, Kd, Ks, Ns values
            
        Example .mtl file:
            # Material for wall.jpg
            newmtl wall
            Ka 0.800000 0.800000 0.800000
            Kd 0.900000 0.900000 0.900000
            Ks 0.200000 0.200000 0.200000
            Ns 4.0
            map_Kd wall.jpg
        """
        if not mtl_path.exists():
            raise FileNotFoundError(f"Material file not found: {mtl_path}")
        
        # Default values
        material = {
            'Ka': (0.7, 0.7, 0.7),
            'Kd': (0.8, 0.8, 0.8),
            'Ks': (0.2, 0.2, 0.2),
            'Ns': 30.0,
        }
        
        with open(mtl_path, 'r') as f:
            for line in f:
                line = line.strip()
                
                # Skip comments and empty lines
                if not line or line.startswith('#'):
                    continue
                
                # Parse material properties
                parts = line.split()
                if len(parts) < 2:
                    continue
                
                directive = parts[0]
                
                if directive == 'Ka' and len(parts) >= 4:
                    # Ambient color
                    material['Ka'] = (float(parts[1]), float(parts[2]), float(parts[3]))
                elif directive == 'Kd' and len(parts) >= 4:
                    # Diffuse color
                    material['Kd'] = (float(parts[1]), float(parts[2]), float(parts[3]))
                elif directive == 'Ks' and len(parts) >= 4:
                    # Specular color
                    material['Ks'] = (float(parts[1]), float(parts[2]), float(parts[3]))
                elif directive == 'Ns' and len(parts) >= 2:
                    # Shininess
                    material['Ns'] = float(parts[1])
        
        return material
    
    def get_material_for_texture(self, texture_path: Path, element_type: str) -> dict:
        """
        Get material properties for a texture file.
        
        Looks for .mtl file with same base name as texture file,
        in the same directory as the texture.
        
        Args:
            texture_path: Path to texture file (e.g., textures/fallback/wall/wall.jpg)
            element_type: Element type (e.g., 'wall') for fallback logic
            
        Returns:
            Dictionary with Ka, Kd, Ks, Ns values
            
        Example:
            texture_path = Path('textures/fallback/wall/wall.jpg')
            mtl_path = Path('textures/fallback/wall/wall.mtl')
        """
        # Get .mtl path by replacing texture extension
        texture_path = Path(texture_path)
        mtl_path = texture_path.with_suffix('.mtl')
        
        # Check cache first
        cache_key = str(mtl_path)
        if cache_key in self._material_cache:
            return self._material_cache[cache_key].copy()
        
        # Try to load .mtl file
        if mtl_path.exists():
            try:
                material = self.parse_mtl_file(mtl_path)
                self._material_cache[cache_key] = material
                return material.copy()
            except Exception as e:
                WarnMsg(f"Failed to parse {mtl_path}: {e}")
                print(f"  Using default material for {element_type}")
        else:
            # .mtl file doesn't exist
            # Try to find it in the element subdirectory (element_type directly)
            element_subdir = element_type
            
            found = False
            
            # Try in defaults directory first
            default_dir = self.default_texture_dir / element_subdir
            if default_dir.exists():
                # Look for base element .mtl file
                base_mtl = default_dir / f"{element_type}.mtl"
                if base_mtl.exists():
                    try:
                        material = self.parse_mtl_file(base_mtl)
                        self._material_cache[cache_key] = material
                        found = True
                        return material.copy()
                    except Exception as e:
                        WarnMsg(f"Failed to parse {base_mtl}: {e}")
            
            # Try in fallback directory
            if not found and self.fallback_texture_dir:
                fallback_dir = self.fallback_texture_dir / element_subdir
                if fallback_dir.exists():
                    base_mtl = fallback_dir / f"{element_type}.mtl"
                    if base_mtl.exists():
                        try:
                            material = self.parse_mtl_file(base_mtl)
                            self._material_cache[cache_key] = material
                            found = True
                            return material.copy()
                        except Exception as e:
                            WarnMsg(f"Failed to parse {base_mtl}: {e}")
            
            # If still not found, use default material
            if not found:
                WarnMsg(f"Material file not found: {mtl_path}")
                print(f"  Using default material for {element_type}")
        
        # Return default material
        default_material = self.get_default_material()
        self._material_cache[cache_key] = default_material
        return default_material.copy()
    
    def get_default_material(self) -> dict:
        """
        Get default material properties (neutral gray).
        
        Returns:
            Dictionary with Ka, Kd, Ks, Ns values
        """
        return {
            'Ka': (0.7, 0.7, 0.7),
            'Kd': (0.8, 0.8, 0.8),
            'Ks': (0.2, 0.2, 0.2),
            'Ns': 30.0,
        }
    
    def format_mtl_color(self, rgb_tuple: tuple[float, float, float]) -> str:
        """
        Format RGB tuple as MTL color string.
        
        Args:
            rgb_tuple: (R, G, B) values from 0.0 to 1.0
            
        Returns:
            Space-separated color string (e.g., "0.800000 0.800000 0.800000")
        """
        return f"{rgb_tuple[0]:.6f} {rgb_tuple[1]:.6f} {rgb_tuple[2]:.6f}"
    
    def clear_cache(self):
        """Clear the material cache."""
        self._material_cache.clear()


# Example usage
if __name__ == "__main__":
    # Test material manager
    manager = MaterialManager(
        default_texture_dir=Path('textures/defaults'),
        fallback_texture_dir=Path('textures/fallback')
    )
    
    # Test parsing a material file
    test_texture = Path('textures/fallback/wall/wall.jpg')
    if test_texture.exists():
        material = manager.get_material_for_texture(test_texture, 'wall')
        print(f"Wall material: Ka={material['Ka']}, Kd={material['Kd']}, "
              f"Ks={material['Ks']}, Ns={material['Ns']}")
