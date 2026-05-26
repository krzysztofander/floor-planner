"""
Default material properties for 3D OBJ/MTL export.

This file defines the ambient (Ka), diffuse (Kd), specular (Ks) color components
and shininess (Ns) for each element type. These properties control how the 3D
models appear when rendered with lighting in 3D software.

Material Property Reference:
- Ka (Ambient):   Base color visible even without direct light (0.0-1.0 RGB)
- Kd (Diffuse):   Main surface color under diffuse lighting (0.0-1.0 RGB)
- Ks (Specular):  Highlight color from reflections (0.0-1.0 RGB)
- Ns (Shininess): Sharpness of specular highlights (0-1000, higher = shinier)

Color values are RGB tuples (R, G, B) where each component is 0.0 to 1.0.
Example: (1.0, 1.0, 1.0) = white, (0.5, 0.5, 0.5) = gray, (1.0, 0.0, 0.0) = red
"""

# Default material properties by element category
MATERIAL_PROPERTIES = {
    # ==========================================================================
    # STRUCTURAL ELEMENTS
    # ==========================================================================
    'wall': {
        'Ka': (0.8, 0.8, 0.8),      # Light gray ambient
        'Kd': (0.9, 0.9, 0.9),      # White-gray diffuse (paint/drywall)
        'Ks': (0.1, 0.1, 0.1),      # Low specular (matte finish)
        'Ns': 10.0,                  # Low shininess (flat paint)
    },
    
    'door': {
        'Ka': (0.5, 0.3, 0.2),      # Brown ambient
        'Kd': (0.6, 0.4, 0.2),      # Wood brown diffuse
        'Ks': (0.2, 0.2, 0.2),      # Slight specular (semi-gloss wood)
        'Ns': 30.0,                  # Medium-low shininess
    },
    
    'window': {
        'Ka': (0.7, 0.8, 0.9),      # Light blue ambient
        'Kd': (0.8, 0.9, 1.0),      # Glass blue-tint diffuse
        'Ks': (0.9, 0.9, 0.9),      # High specular (glass reflective)
        'Ns': 200.0,                 # High shininess (glass)
    },
    
    'floor': {
        'Ka': (0.6, 0.5, 0.4),      # Tan/beige ambient
        'Kd': (0.7, 0.6, 0.5),      # Wood/tile diffuse
        'Ks': (0.3, 0.3, 0.3),      # Medium specular (polished)
        'Ns': 50.0,                  # Medium shininess
    },
    
    # ==========================================================================
    # FURNITURE
    # ==========================================================================
    'desk': {
        'Ka': (0.5, 0.3, 0.2),      # Wood brown ambient
        'Kd': (0.6, 0.4, 0.25),     # Wood diffuse
        'Ks': (0.2, 0.2, 0.2),      # Low specular (matte wood)
        'Ns': 25.0,                  # Low-medium shininess
    },
    
    'chair': {
        'Ka': (0.5, 0.3, 0.2),      # Wood/fabric ambient
        'Kd': (0.6, 0.4, 0.3),      # Mixed material diffuse
        'Ks': (0.15, 0.15, 0.15),   # Low specular (fabric/wood mix)
        'Ns': 20.0,                  # Low shininess
    },
    
    'sofa': {
        'Ka': (0.4, 0.4, 0.4),      # Fabric gray ambient
        'Kd': (0.5, 0.5, 0.5),      # Upholstery gray diffuse
        'Ks': (0.1, 0.1, 0.1),      # Very low specular (fabric)
        'Ns': 10.0,                  # Very low shininess (matte fabric)
    },
    
    'bed': {
        'Ka': (0.8, 0.8, 0.7),      # Light fabric ambient
        'Kd': (0.9, 0.9, 0.85),     # Bedding/fabric diffuse
        'Ks': (0.05, 0.05, 0.05),   # Minimal specular (soft fabric)
        'Ns': 5.0,                   # Very low shininess
    },
    
    'table': {
        'Ka': (0.5, 0.3, 0.2),      # Wood ambient
        'Kd': (0.6, 0.4, 0.25),     # Wood diffuse
        'Ks': (0.3, 0.3, 0.3),      # Medium specular (polished wood)
        'Ns': 40.0,                  # Medium shininess
    },
    
    'wardrobe': {
        'Ka': (0.5, 0.3, 0.2),      # Wood ambient
        'Kd': (0.55, 0.35, 0.22),   # Dark wood diffuse
        'Ks': (0.2, 0.2, 0.2),      # Low specular
        'Ns': 30.0,                  # Medium-low shininess
    },
    
    'bookshelf': {
        'Ka': (0.5, 0.3, 0.2),      # Wood ambient
        'Kd': (0.6, 0.4, 0.25),     # Wood diffuse
        'Ks': (0.15, 0.15, 0.15),   # Low specular
        'Ns': 20.0,                  # Low shininess
    },
    
    # ==========================================================================
    # APPLIANCES
    # ==========================================================================
    'refrigerator': {
        'Ka': (0.85, 0.85, 0.85),   # Metallic white ambient
        'Kd': (0.9, 0.9, 0.9),      # Stainless/white diffuse
        'Ks': (0.6, 0.6, 0.6),      # High specular (metal)
        'Ns': 150.0,                 # High shininess (polished metal)
    },
    
    'stove': {
        'Ka': (0.2, 0.2, 0.2),      # Dark metal ambient
        'Kd': (0.3, 0.3, 0.3),      # Dark metal diffuse
        'Ks': (0.5, 0.5, 0.5),      # High specular (metal)
        'Ns': 120.0,                 # High shininess
    },
    
    'oven': {
        'Ka': (0.3, 0.3, 0.3),      # Metal ambient
        'Kd': (0.4, 0.4, 0.4),      # Metal diffuse
        'Ks': (0.5, 0.5, 0.5),      # High specular
        'Ns': 100.0,                 # High shininess
    },
    
    'dishwasher': {
        'Ka': (0.7, 0.7, 0.7),      # Light metal ambient
        'Kd': (0.8, 0.8, 0.8),      # Stainless diffuse
        'Ks': (0.5, 0.5, 0.5),      # High specular
        'Ns': 120.0,                 # High shininess
    },
    
    'washer': {
        'Ka': (0.85, 0.85, 0.85),   # White metal ambient
        'Kd': (0.9, 0.9, 0.9),      # White appliance diffuse
        'Ks': (0.4, 0.4, 0.4),      # Medium-high specular
        'Ns': 80.0,                  # Medium-high shininess
    },
    
    'dryer': {
        'Ka': (0.85, 0.85, 0.85),   # White metal ambient
        'Kd': (0.9, 0.9, 0.9),      # White appliance diffuse
        'Ks': (0.4, 0.4, 0.4),      # Medium-high specular
        'Ns': 80.0,                  # Medium-high shininess
    },
    
    # ==========================================================================
    # BATHROOM FIXTURES
    # ==========================================================================
    'toilet': {
        'Ka': (0.9, 0.9, 0.9),      # Porcelain white ambient
        'Kd': (0.95, 0.95, 0.95),   # White ceramic diffuse
        'Ks': (0.7, 0.7, 0.7),      # High specular (glazed ceramic)
        'Ns': 200.0,                 # Very high shininess (glossy)
    },
    
    'sink': {
        'Ka': (0.85, 0.85, 0.85),   # Ceramic/metal ambient
        'Kd': (0.9, 0.9, 0.9),      # White/chrome diffuse
        'Ks': (0.6, 0.6, 0.6),      # High specular
        'Ns': 180.0,                 # High shininess
    },
    
    'bathtub': {
        'Ka': (0.9, 0.9, 0.9),      # Porcelain ambient
        'Kd': (0.95, 0.95, 0.95),   # White ceramic diffuse
        'Ks': (0.6, 0.6, 0.6),      # High specular
        'Ns': 150.0,                 # High shininess
    },
    
    'shower': {
        'Ka': (0.8, 0.8, 0.8),      # Tile/glass ambient
        'Kd': (0.85, 0.85, 0.85),   # Tile diffuse
        'Ks': (0.5, 0.5, 0.5),      # Medium-high specular
        'Ns': 120.0,                 # Medium-high shininess
    },
    
    'bidet': {
        'Ka': (0.9, 0.9, 0.9),      # Porcelain ambient
        'Kd': (0.95, 0.95, 0.95),   # White ceramic diffuse
        'Ks': (0.7, 0.7, 0.7),      # High specular
        'Ns': 200.0,                 # Very high shininess
    },
    
    # ==========================================================================
    # LIGHTING FIXTURES
    # ==========================================================================
    'ceiling_lamp': {
        'Ka': (0.9, 0.9, 0.8),      # Light yellow ambient (light source)
        'Kd': (1.0, 1.0, 0.9),      # Warm white diffuse
        'Ks': (0.8, 0.8, 0.8),      # High specular (glass/metal)
        'Ns': 150.0,                 # High shininess
    },
    
    'wall_lamp': {
        'Ka': (0.9, 0.9, 0.8),      # Light ambient
        'Kd': (0.95, 0.95, 0.85),   # Warm diffuse
        'Ks': (0.7, 0.7, 0.7),      # High specular
        'Ns': 120.0,                 # High shininess
    },
    
    # ==========================================================================
    # ELECTRICAL ELEMENTS
    # ==========================================================================
    'power_outlet': {
        'Ka': (0.85, 0.85, 0.85),   # Plastic white ambient
        'Kd': (0.9, 0.9, 0.9),      # Plastic diffuse
        'Ks': (0.3, 0.3, 0.3),      # Medium specular (plastic)
        'Ns': 60.0,                  # Medium shininess
    },
    
    'switch': {
        'Ka': (0.85, 0.85, 0.85),   # Plastic ambient
        'Kd': (0.9, 0.9, 0.9),      # Plastic diffuse
        'Ks': (0.3, 0.3, 0.3),      # Medium specular
        'Ns': 60.0,                  # Medium shininess
    },
    
    # ==========================================================================
    # LANDSCAPING ELEMENTS
    # ==========================================================================
    'tree': {
        'Ka': (0.2, 0.4, 0.15),     # Green/brown ambient
        'Kd': (0.3, 0.6, 0.2),      # Foliage green diffuse
        'Ks': (0.1, 0.1, 0.1),      # Low specular (organic)
        'Ns': 5.0,                   # Very low shininess (matte)
    },
    
    'shrub': {
        'Ka': (0.3, 0.5, 0.2),      # Green ambient
        'Kd': (0.4, 0.7, 0.3),      # Bright green diffuse
        'Ks': (0.1, 0.1, 0.1),      # Low specular
        'Ns': 5.0,                   # Very low shininess
    },
    
    'hedge': {
        'Ka': (0.25, 0.4, 0.2),     # Dark green ambient
        'Kd': (0.35, 0.55, 0.25),   # Hedge green diffuse
        'Ks': (0.1, 0.1, 0.1),      # Low specular
        'Ns': 5.0,                   # Very low shininess
    },
    
    'lawn': {
        'Ka': (0.3, 0.5, 0.2),      # Grass green ambient
        'Kd': (0.4, 0.7, 0.3),      # Lawn green diffuse
        'Ks': (0.05, 0.05, 0.05),   # Very low specular
        'Ns': 3.0,                   # Very low shininess
    },
    
    'path': {
        'Ka': (0.6, 0.55, 0.5),     # Stone gray ambient
        'Kd': (0.7, 0.65, 0.6),     # Concrete/stone diffuse
        'Ks': (0.15, 0.15, 0.15),   # Low specular
        'Ns': 20.0,                  # Low shininess
    },
    
    'deck': {
        'Ka': (0.5, 0.35, 0.2),     # Wood brown ambient
        'Kd': (0.6, 0.4, 0.25),     # Outdoor wood diffuse
        'Ks': (0.2, 0.2, 0.2),      # Low specular (weathered)
        'Ns': 15.0,                  # Low shininess
    },
    
    'fence': {
        'Ka': (0.5, 0.35, 0.25),    # Wood ambient
        'Kd': (0.6, 0.45, 0.3),     # Weathered wood diffuse
        'Ks': (0.1, 0.1, 0.1),      # Very low specular
        'Ns': 10.0,                  # Very low shininess
    },
    
    'pool': {
        'Ka': (0.4, 0.6, 0.8),      # Blue water ambient
        'Kd': (0.5, 0.7, 0.9),      # Water blue diffuse
        'Ks': (0.8, 0.8, 0.8),      # High specular (water reflective)
        'Ns': 180.0,                 # High shininess (water surface)
    },
    
    'fountain': {
        'Ka': (0.5, 0.65, 0.8),     # Water/stone ambient
        'Kd': (0.6, 0.75, 0.85),    # Water diffuse
        'Ks': (0.7, 0.7, 0.7),      # High specular
        'Ns': 150.0,                 # High shininess
    },
    
    'pond': {
        'Ka': (0.3, 0.5, 0.6),      # Dark water ambient
        'Kd': (0.4, 0.6, 0.7),      # Natural water diffuse
        'Ks': (0.6, 0.6, 0.6),      # Medium-high specular
        'Ns': 100.0,                 # Medium-high shininess
    },
    
    # ==========================================================================
    # DEFAULT FALLBACK
    # ==========================================================================
    'default': {
        'Ka': (0.7, 0.7, 0.7),      # Neutral gray ambient
        'Kd': (0.8, 0.8, 0.8),      # Light gray diffuse
        'Ks': (0.2, 0.2, 0.2),      # Low specular
        'Ns': 30.0,                  # Medium-low shininess
    },
}


def get_material_properties(element_type: str) -> dict:
    """
    Get material properties for a given element type.
    
    Args:
        element_type: Type of element (e.g., 'wall', 'desk', 'refrigerator')
        
    Returns:
        Dictionary with Ka, Kd, Ks, and Ns values
    """
    # Normalize element type (convert to lowercase, remove underscores)
    normalized_type = element_type.lower().replace('_', '')
    
    # Try exact match first
    if element_type in MATERIAL_PROPERTIES:
        return MATERIAL_PROPERTIES[element_type].copy()
    
    # Try normalized match
    for key in MATERIAL_PROPERTIES:
        if key.replace('_', '') == normalized_type:
            return MATERIAL_PROPERTIES[key].copy()
    
    # Return default if not found
    return MATERIAL_PROPERTIES['default'].copy()


def format_mtl_color(rgb_tuple: tuple[float, float, float]) -> str:
    """
    Format RGB tuple as MTL color string.
    
    Args:
        rgb_tuple: (R, G, B) values from 0.0 to 1.0
        
    Returns:
        Space-separated color string (e.g., "0.8 0.8 0.8")
    """
    return f"{rgb_tuple[0]:.6f} {rgb_tuple[1]:.6f} {rgb_tuple[2]:.6f}"


# Example usage:
if __name__ == "__main__":
    # Test material lookup
    wall_mat = get_material_properties('wall')
    print(f"Wall material: Ka={wall_mat['Ka']}, Kd={wall_mat['Kd']}, "
          f"Ks={wall_mat['Ks']}, Ns={wall_mat['Ns']}")
    
    # Test formatting
    print(f"Formatted Ka: {format_mtl_color(wall_mat['Ka'])}")
