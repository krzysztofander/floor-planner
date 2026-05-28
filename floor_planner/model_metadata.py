"""
Model metadata management for external 3D model integration.

Handles loading, validation, and processing of .transform.json metadata files
that accompany external 3D models. These files define normalization transforms,
bounding boxes, dimensions, and other model-specific properties.

Author: Floor Planner Team
Created: 2026-05-27
"""

import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Tuple, Optional
import numpy as np

from .transform import load_matrix_from_json


@dataclass
class BoundingBox:
    """Axis-aligned bounding box in normalized model space."""
    
    min: Tuple[float, float, float]  # [x, y, z] minimum corner
    max: Tuple[float, float, float]  # [x, y, z] maximum corner
    
    @property
    def width(self) -> float:
        """Width (X-axis extent) in meters."""
        return self.max[0] - self.min[0]
    
    @property
    def height(self) -> float:
        """Height (Y-axis extent) in meters."""
        return self.max[1] - self.min[1]
    
    @property
    def length(self) -> float:
        """Length (Z-axis extent) in meters."""
        return self.max[2] - self.min[2]
    
    @property
    def center(self) -> Tuple[float, float, float]:
        """Center point of bounding box."""
        return (
            (self.min[0] + self.max[0]) / 2,
            (self.min[1] + self.max[1]) / 2,
            (self.min[2] + self.max[2]) / 2
        )
    
    @property
    def volume(self) -> float:
        """Volume of bounding box in cubic meters."""
        return self.width * self.height * self.length
    
    def contains_point(self, x: float, y: float, z: float) -> bool:
        """Check if point is inside bounding box."""
        return (
            self.min[0] <= x <= self.max[0] and
            self.min[1] <= y <= self.max[1] and
            self.min[2] <= z <= self.max[2]
        )
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        return {
            'min': list(self.min),
            'max': list(self.max)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'BoundingBox':
        """Create from dictionary (loaded from JSON)."""
        return cls(
            min=tuple(data['min']),
            max=tuple(data['max'])
        )


@dataclass
class InteractionMetadata:
    """Metadata for interactive element behavior (animations, etc.)."""
    
    type: str  # 'animation', 'continuous_rotation', 'physics', etc.
    animation_name: Optional[str] = None
    trigger: Optional[str] = None  # 'click', 'hover', 'proximity', 'none'
    duration: Optional[float] = None  # seconds
    reversible: bool = False
    default_state: Optional[str] = None
    axis: Optional[str] = None  # 'X', 'Y', 'Z'
    range: Optional[Tuple[float, float]] = None
    speed: Optional[float] = None
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        result = {'type': self.type}
        if self.animation_name:
            result['animation_name'] = self.animation_name
        if self.trigger:
            result['trigger'] = self.trigger
        if self.duration is not None:
            result['duration'] = self.duration
        if self.reversible:
            result['reversible'] = self.reversible
        if self.default_state:
            result['default_state'] = self.default_state
        if self.axis:
            result['axis'] = self.axis
        if self.range:
            result['range'] = list(self.range)
        if self.speed is not None:
            result['speed'] = self.speed
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'InteractionMetadata':
        """Create from dictionary (loaded from JSON)."""
        return cls(
            type=data['type'],
            animation_name=data.get('animation_name'),
            trigger=data.get('trigger'),
            duration=data.get('duration'),
            reversible=data.get('reversible', False),
            default_state=data.get('default_state'),
            axis=data.get('axis'),
            range=tuple(data['range']) if 'range' in data else None,
            speed=data.get('speed')
        )


@dataclass
class ModelMetadata:
    """
    Complete metadata for an external 3D model.
    
    Loaded from .transform.json files that accompany external model files.
    Contains all information needed to properly integrate the model into
    the floor plan system.
    """
    
    # Required fields
    model_file: str  # Filename of the 3D model (e.g., "model.glb", "model.obj")
    format_version: str  # Metadata format version (e.g., "1.0")
    element_type: str  # Element type name (e.g., "chair", "desk")
    registry_key: str  # Registry key from create_elements_registry()
    model_format: str = "gltf"  # Model file format: "gltf" (.glb) or "obj" (.obj)
    
    # Coordinate system
    units: str = "meters"  # "meters", "centimeters", "inches"
    up_axis: str = "Y"  # "Y" or "Z"
    
    # Normalization transform
    normalization_matrix: np.ndarray = field(default_factory=lambda: np.eye(4))
    normalization_description: str = ""
    
    # Spatial properties
    anchor_point_name: str = "bottom_center"  # Semantic anchor point name
    anchor_offset: Tuple[float, float, float] = (0.0, 0.0, 0.0)
    bounding_box: Optional[BoundingBox] = None
    
    # Dimensions (calculated from bounding box, or specified explicitly)
    width: Optional[float] = None
    length: Optional[float] = None
    height: Optional[float] = None
    
    # Visual properties
    color: Optional[Tuple[float, float, float]] = None
    material_type: Optional[str] = None
    thumbnail: Optional[str] = None
    
    # Interactions (animations, physics, etc.)
    interactions: Dict[str, InteractionMetadata] = field(default_factory=dict)
    
    # General metadata
    author: Optional[str] = None
    license: Optional[str] = None
    source: Optional[str] = None
    created: Optional[str] = None
    tags: List[str] = field(default_factory=list)
    
    @property
    def model_path_relative(self) -> str:
        """Get relative path to model file from project root."""
        return f"models/{self.registry_key}/{self.model_file}"
    
    def get_dimensions(self) -> Tuple[float, float, float]:
        """
        Get (width, length, height) dimensions in meters.
        
        Returns dimensions from explicit fields if available,
        otherwise calculates from bounding box.
        """
        if self.width is not None and self.length is not None and self.height is not None:
            return (self.width, self.length, self.height)
        
        if self.bounding_box:
            return (
                self.bounding_box.width,
                self.bounding_box.length,
                self.bounding_box.height
            )
        
        raise ValueError(
            f"No dimensions available for model '{self.model_file}'. "
            "Specify either explicit dimensions or bounding_box."
        )
    
    def to_dict(self) -> dict:
        """Convert to JSON-serializable dictionary."""
        from .transform import matrix_to_json
        
        result = {
            'model_file': self.model_file,
            'model_format': self.model_format,
            'format_version': self.format_version,
            'element_type': self.element_type,
            'registry_key': self.registry_key,
            'units': self.units,
            'up_axis': self.up_axis,
            'normalization': {
                'description': self.normalization_description,
                'matrix': matrix_to_json(self.normalization_matrix)
            },
            'anchor_point': self.anchor_point_name,
            'anchor_offset': list(self.anchor_offset)
        }
        
        if self.bounding_box:
            result['bounding_box'] = self.bounding_box.to_dict()
        
        if self.width is not None:
            result.setdefault('dimensions', {})['width'] = self.width
        if self.length is not None:
            result.setdefault('dimensions', {})['length'] = self.length
        if self.height is not None:
            result.setdefault('dimensions', {})['height'] = self.height
        
        if self.color or self.material_type or self.thumbnail:
            visual = {}
            if self.color:
                visual['color'] = list(self.color)
            if self.material_type:
                visual['material_type'] = self.material_type
            if self.thumbnail:
                visual['thumbnail'] = self.thumbnail
            result['visual_properties'] = visual
        
        if self.interactions:
            result['interactions'] = {
                name: interaction.to_dict()
                for name, interaction in self.interactions.items()
            }
        
        if self.author or self.license or self.source or self.created or self.tags:
            metadata = {}
            if self.author:
                metadata['author'] = self.author
            if self.license:
                metadata['license'] = self.license
            if self.source:
                metadata['source'] = self.source
            if self.created:
                metadata['created'] = self.created
            if self.tags:
                metadata['tags'] = self.tags
            result['metadata'] = metadata
        
        return result
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ModelMetadata':
        """Create from dictionary (loaded from JSON file)."""
        # Required fields
        model_file = data['model_file']
        format_version = data['format_version']
        element_type = data['element_type']
        registry_key = data.get('registry_key', element_type)  # Default to element_type
        model_format = data.get('model_format', 'gltf')  # Default to glTF for backward compatibility
        
        # Coordinate system
        units = data.get('units', 'meters')
        up_axis = data.get('up_axis', 'Y')
        
        # Normalization
        norm_data = data.get('normalization', {})
        norm_matrix = load_matrix_from_json(
            norm_data.get('matrix', [[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]])
        )
        norm_description = norm_data.get('description', '')
        
        # Spatial properties
        anchor_point_name = data.get('anchor_point', 'bottom_center')
        anchor_offset = tuple(data.get('anchor_offset', [0, 0, 0]))
        
        bounding_box = None
        if 'bounding_box' in data:
            bounding_box = BoundingBox.from_dict(data['bounding_box'])
        
        # Dimensions
        dims = data.get('dimensions', {})
        width = dims.get('width')
        length = dims.get('length')
        height = dims.get('height')
        
        # Visual properties
        visual = data.get('visual_properties', {})
        color = tuple(visual['color']) if 'color' in visual else None
        material_type = visual.get('material_type')
        thumbnail = visual.get('thumbnail')
        
        # Interactions
        interactions = {}
        if 'interactions' in data:
            for name, interaction_data in data['interactions'].items():
                interactions[name] = InteractionMetadata.from_dict(interaction_data)
        
        # General metadata
        meta = data.get('metadata', {})
        author = meta.get('author')
        license_info = meta.get('license')
        source = meta.get('source')
        created = meta.get('created')
        tags = meta.get('tags', [])
        
        return cls(
            model_file=model_file,
            format_version=format_version,
            element_type=element_type,
            registry_key=registry_key,
            model_format=model_format,
            units=units,
            up_axis=up_axis,
            normalization_matrix=norm_matrix,
            normalization_description=norm_description,
            anchor_point_name=anchor_point_name,
            anchor_offset=anchor_offset,
            bounding_box=bounding_box,
            width=width,
            length=length,
            height=height,
            color=color,
            material_type=material_type,
            thumbnail=thumbnail,
            interactions=interactions,
            author=author,
            license=license_info,
            source=source,
            created=created,
            tags=tags
        )


def load_model_metadata(metadata_path: str | Path) -> ModelMetadata:
    """
    Load model metadata from .transform.json file.
    
    Args:
        metadata_path: Path to .transform.json file
        
    Returns:
        ModelMetadata object
        
    Raises:
        FileNotFoundError: If metadata file doesn't exist
        ValueError: If metadata format is invalid
        json.JSONDecodeError: If JSON is malformed
    """
    metadata_path = Path(metadata_path)
    
    if not metadata_path.exists():
        raise FileNotFoundError(f"Metadata file not found: {metadata_path}")
    
    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    try:
        return ModelMetadata.from_dict(data)
    except KeyError as e:
        raise ValueError(f"Missing required field in metadata: {e}")
    except Exception as e:
        raise ValueError(f"Invalid metadata format: {e}")


def save_model_metadata(metadata: ModelMetadata, metadata_path: str | Path) -> None:
    """
    Save model metadata to .transform.json file.
    
    Args:
        metadata: ModelMetadata object to save
        metadata_path: Path where to save the file
    """
    metadata_path = Path(metadata_path)
    
    # Create parent directory if needed
    metadata_path.parent.mkdir(parents=True, exist_ok=True)
    
    data = metadata.to_dict()
    
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def find_model_metadata(registry_key: str, models_dir: str | Path = "models") -> Optional[Path]:
    """
    Find metadata file for a given registry key.
    
    Searches for models/{registry_key}/model.transform.json
    
    Args:
        registry_key: Element type registry key (e.g., 'chair', 'desk')
        models_dir: Base directory for model library (default: "models")
        
    Returns:
        Path to metadata file if found, None otherwise
    """
    models_dir = Path(models_dir)
    metadata_path = models_dir / registry_key / "model.transform.json"
    
    return metadata_path if metadata_path.exists() else None


def validate_model_metadata(metadata: ModelMetadata) -> List[str]:
    """
    Validate model metadata for common issues.
    
    Args:
        metadata: ModelMetadata object to validate
        
    Returns:
        List of warning/error messages (empty if valid)
    """
    warnings = []
    
    # Check required fields
    if not metadata.model_file:
        warnings.append("Missing model_file")
    
    if not metadata.registry_key:
        warnings.append("Missing registry_key")
    
    # Check normalization matrix
    if metadata.normalization_matrix.shape != (4, 4):
        warnings.append(f"Normalization matrix has wrong shape: {metadata.normalization_matrix.shape}")
    
    # Check determinant (should be non-zero for valid transform)
    det = np.linalg.det(metadata.normalization_matrix[:3, :3])
    if abs(det) < 1e-6:
        warnings.append(f"Normalization matrix is singular (determinant near zero: {det})")
    
    # Check dimensions
    try:
        width, length, height = metadata.get_dimensions()
        if width <= 0 or length <= 0 or height <= 0:
            warnings.append(f"Invalid dimensions: {width} × {length} × {height} (all must be positive)")
    except ValueError as e:
        warnings.append(str(e))
    
    # Check bounding box consistency
    if metadata.bounding_box:
        bbox = metadata.bounding_box
        if any(bbox.min[i] >= bbox.max[i] for i in range(3)):
            warnings.append(f"Invalid bounding box: min {bbox.min} >= max {bbox.max}")
    
    # Check units
    valid_units = ['meters', 'centimeters', 'inches', 'feet']
    if metadata.units not in valid_units:
        warnings.append(f"Unknown units '{metadata.units}' (expected one of {valid_units})")
    
    # Check model_format
    valid_formats = ['gltf', 'obj']
    if metadata.model_format not in valid_formats:
        warnings.append(f"Unknown model_format '{metadata.model_format}' (expected 'gltf' or 'obj')")
    
    # Check up_axis
    if metadata.up_axis not in ['Y', 'Z']:
        warnings.append(f"Invalid up_axis '{metadata.up_axis}' (expected 'Y' or 'Z')")
    
    return warnings
