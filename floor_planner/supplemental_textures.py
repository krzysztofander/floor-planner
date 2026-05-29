#!/usr/bin/env python3
"""
Define supplemental textures for multi-texture elements.

This registry indicates which elements have additional textures beyond
the base texture. Base texture name matches the element type from registry.
Supplemental textures use: <element_type>_<suffix>.jpg

Example:
  - Element: 'door'
  - Base texture: 'door.jpg'
  - Supplemental: 'door_frame.jpg'
"""

# Map element type → list of supplemental texture suffixes
SUPPLEMENTAL_TEXTURES = {
    # Structural elements
    'door': ['frame'],  # door.jpg + door_frame.jpg
    
    # Furniture with distinct face textures
    'desk': ['sides'],  # desk.jpg (top) + desk_sides.jpg
}


def get_all_texture_names(element_type: str) -> list[str]:
    """
    Get all texture filenames for an element (base + supplemental).
    
    Args:
        element_type: Element type from registry (e.g., 'door', 'generic_storage')
        
    Returns:
        List of texture filenames without extension
        
    Example:
        get_all_texture_names('door') → ['door', 'door_frame']
        get_all_texture_names('wall') → ['wall']
    """
    base_name = element_type
    textures = [base_name]
    
    if element_type in SUPPLEMENTAL_TEXTURES:
        for suffix in SUPPLEMENTAL_TEXTURES[element_type]:
            textures.append(f"{base_name}_{suffix}")
    
    return textures


def has_supplemental_textures(element_type: str) -> bool:
    """Check if element has supplemental textures."""
    return element_type in SUPPLEMENTAL_TEXTURES


def get_supplemental_suffixes(element_type: str) -> list[str]:
    """Get list of supplemental texture suffixes for element."""
    return SUPPLEMENTAL_TEXTURES.get(element_type, [])


__all__ = [
    'SUPPLEMENTAL_TEXTURES',
    'get_all_texture_names',
    'has_supplemental_textures',
    'get_supplemental_suffixes',
]
