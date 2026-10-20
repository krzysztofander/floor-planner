"""
Material management for 3D model generation.

This module handles material property resolution from external .mtl files.
Procedural element types keep their material in a per-element folder; the
textures they reference live in the common textures/ folder.

Example directory structure:
    models/procedural/
        wall/
            wall.mtl        (map_Kd wall.jpg)
        door/
            door.mtl        (map_Kd door.jpg)
    textures/
        wall.jpg
        door.jpg
"""

from pathlib import Path
from typing import Optional

from floor_planner.utils import WarnMsg


class MaterialManager:
    """
    Manages material property resolution from .mtl files.
    
    Responsibilities:
        - Parse .mtl files to extract Ka, Kd, Ks, Ns values
        - Cache loaded materials for performance
        - Provide fallback to default material if .mtl not found
    """
    
    def __init__(self):
        """Initialize material manager."""
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
    
    def get_material(self, mtl_path: Optional[Path], element_type: str) -> dict:
        """
        Get material properties from a .mtl file.
        
        Args:
            mtl_path: Path to .mtl file (e.g., models/procedural/wall/wall.mtl), or None
            element_type: Element type (e.g., 'wall'), used in messages
            
        Returns:
            Dictionary with Ka, Kd, Ks, Ns values; default material if the file
            is missing or cannot be parsed
        """
        if mtl_path is None:
            WarnMsg(f"Material file not found for {element_type}")
            print(f"  Using default material for {element_type}")
            return self.get_default_material()
        
        # Check cache first
        cache_key = str(mtl_path)
        if cache_key in self._material_cache:
            return self._material_cache[cache_key].copy()
        
        try:
            material = self.parse_mtl_file(Path(mtl_path))
        except Exception as e:
            WarnMsg(f"Failed to parse {mtl_path}: {e}")
            print(f"  Using default material for {element_type}")
            material = self.get_default_material()
        
        self._material_cache[cache_key] = material
        return material.copy()
    
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
    manager = MaterialManager()
    
    # Test parsing a material file
    test_mtl = Path('models/procedural/wall/wall.mtl')
    if test_mtl.exists():
        material = manager.get_material(test_mtl, 'wall')
        print(f"Wall material: Ka={material['Ka']}, Kd={material['Kd']}, "
              f"Ks={material['Ks']}, Ns={material['Ns']}")
