"""
Base class for elements that reference external 3D models.

Provides infrastructure for integrating pre-made 3D models (glTF, OBJ, etc.)
into the floor planner system. Elements inherit from this class to use
external models instead of procedural geometry generation.

Author: Floor Planner Team
Created: 2026-05-27
"""

from pathlib import Path
from typing import Optional
import numpy as np

from .element import Element
from ..model_metadata import ModelMetadata, load_model_metadata, find_model_metadata
from ..transform import build_normalization_matrix, create_placement_matrix, compose_transforms


class ExternalModelElement(Element):
    """
    Element that references an external 3D model file.
    
    This base class provides functionality for elements that use pre-made
    3D models instead of procedural geometry. It handles:
    - Model metadata loading
    - Fixed dimension enforcement (models can't be scaled)
    - Transform calculation (normalization + placement)
    - Model path resolution
    
    Subclasses should:
    - Override draw() for 2D floor plan rendering
    - Set _registry_key to match the key in create_elements_registry()
    - Optionally override has_external_model() if model is optional
    - Set _requires_external_model = True if the model must exist (script aborts if missing)
    
    Design principle: Elements maintain backward compatibility with 2D drawing.
    They always implement draw() for floor plan rendering, and additionally
    provide external model integration for 3D export when the model exists.
    """
    
    # Subclass should set this to the registry key (e.g., 'chair', 'desk')
    _registry_key: Optional[str] = None
    
    # Set to True in subclass if external model is required (error if missing)
    _requires_external_model: bool = False
    
    @classmethod
    def _get_default_models_dir(cls) -> Path:
        """
        Get the default models directory.
        
        Returns the package's models directory: <package_root>/models
        This allows elements to find models regardless of where the script is run from.
        
        Returns:
            Path to the floor_planner package's models directory
        """
        # __file__ is .../floor_planner/floor_planner/elements/external_models.py
        # Repo root is three levels up, then models/ subdirectory
        repo_root = Path(__file__).parent.parent.parent
        return repo_root / "models"

    # Subdirectories of the models directory searched (after the root) for models.
    # "stubs" holds placeholder cubes and is the last fallback.
    _MODELS_SUBDIRS: tuple[str, ...] = ("local", "models_3rd_party", "stubs")

    # Model file names checked inside a model folder, in priority order: glTF → OBJ → DAE → 3DS
    _MODEL_FILE_NAMES: tuple[str, ...] = ('model.glb', 'model.gltf', 'model.obj', 'model.dae', 'model.3ds')

    def _candidate_models_dirs(self, base_dir: Path) -> list[Path]:
        """Return models directories to search, in priority order."""
        return [base_dir] + [base_dir / subdir for subdir in self._MODELS_SUBDIRS]

    def _resolve_models_dir(self, base_dir: Path) -> Path:
        """
        Find the models directory that contains this element's model.

        Searches base_dir, then base_dir/local, base_dir/models_3rd_party
        and finally base_dir/stubs.
        Falls back to base_dir if the model is not found in any of them.
        """
        registry_key = self.get_registry_key()
        for candidate in self._candidate_models_dirs(base_dir):
            if (candidate / registry_key).is_dir():
                return candidate
        return base_dir

    def __init__(
        self,
        anchor_point: tuple[float, float],
        orientation_angle: float = 0.0,
        color:  str | None = None,
        label: str | None = None,
        id: str | None = None,
        v_anchor: float | None = None,
        texture_scale: float | None = None,
        models_dir: str | Path | None = None,
        **kwargs
    ):
        """
        Initialize external model element.
        
        Args:
            anchor_point: (x, y) position in floor plan (meters)
            orientation_angle: Rotation around vertical Y-axis (degrees)
            color: Color for 2D rendering (string)
            label: Optional label for the element
            id: Optional explicit ID; if None, generated automatically
            v_anchor: Vertical position / Y-coordinate (meters, default 0.0)
            texture_scale: Optional texture tiling scale (meters)
            models_dir: Base directory for model library (default: package models dir)
            **kwargs: Rejected parameters (width, length, height) raise errors
            
        Raises:
            ValueError: If user tries to set width/length/height (dimensions are fixed)
            FileNotFoundError: If model metadata not found or required model doesn't exist
        """
        # Check for rejected dimension overrides
        rejected_params = []
        if 'width' in kwargs:
            rejected_params.append('width')
        if 'length' in kwargs:
            rejected_params.append('length')
        if 'height' in kwargs:
            rejected_params.append('height')
        
        if rejected_params:
            raise ValueError(
                f"Cannot set dimensions for external model element: {', '.join(rejected_params)}. "
                f"Dimensions are fixed by the external model and cannot be overridden."
            )
        
        # Store orientation and models directory before loading metadata
        self.orientation_angle = orientation_angle
        
        # Use default package models directory if not specified
        if models_dir is None:
            base_models_dir = self._get_default_models_dir()
        else:
            base_models_dir = Path(models_dir)
        self._models_dir = self._resolve_models_dir(base_models_dir)

        # Check if external model exists
        has_model = self.has_external_model()
        
        # If model is required but doesn't exist, abort with clear error
        if self._requires_external_model and not has_model:
            registry_key = self.get_registry_key()
            searched_dirs = [
                (d / registry_key).absolute()
                for d in self._candidate_models_dirs(base_models_dir)
            ]
            print(f"\n{'='*80}")
            print(f"ERROR: Required external model not found")
            print(f"{'='*80}")
            print(f"Element type: {self.__class__.__name__}")
            print(f"Registry key: {registry_key}")
            print(f"\nLooked for:")
            for model_dir in searched_dirs:
                print(f"  - {model_dir / 'model.glb'}")
                print(f"  - {model_dir / 'model.obj'}")
            print(f"\nPlease ensure the model files exist in the correct location.")
            print(f"You can specify a different models directory using the 'models_dir' parameter.")
            print(f"{'='*80}\n")
            raise FileNotFoundError(
                f"Required external model not found for {self.__class__.__name__} "
                f"(registry key: '{registry_key}'). "
                f"Searched in: {', '.join(str(d) for d in searched_dirs)}"
            )
        
        # Load model metadata (if external model exists)
        self._model_metadata: Optional[ModelMetadata] = None
        if has_model:
            self._load_model_metadata()
        
        # Set fixed dimensions from metadata (required by Element base class)
        if self._model_metadata:
            width, length, height = self._model_metadata.get_dimensions()
        else:
            # No external model - subclass should provide default dimensions
            width = getattr(self, '_default_width', lambda: 1.0)()
            length = getattr(self, '_default_length', lambda: 1.0)()
            height = getattr(self, '_default_height', lambda: 1.0)()
        
        # Initialize parent (pass dimensions as positional args to avoid **kwargs conflict)
        super().__init__(
            anchor_point=anchor_point,
            color=color,
            label=label,
            id=id,
            v_anchor=v_anchor,
            height=height,
            texture_scale=texture_scale
        )
        
        # Store dimensions as instance attributes (read-only for external models)
        self.width = width
        self.length = length
        # self.height already set by parent __init__
    
    def _load_model_metadata(self) -> None:
        """
        Load model metadata from .transform.json file.
        
        Searches for models/{registry_key}/model.transform.json
        
        Raises:
            FileNotFoundError: If metadata file not found
            ValueError: If metadata is invalid
        """
        registry_key = self.get_registry_key()
        metadata_path = find_model_metadata(registry_key, self._models_dir)
        
        if metadata_path is None:
            raise FileNotFoundError(
                f"Model metadata not found for element type '{registry_key}'. "
                f"Expected: {self._models_dir / registry_key / 'model.transform.json'}"
            )
        
        self._model_metadata = load_model_metadata(metadata_path)
    
    def get_registry_key(self) -> str:
        """
        Get registry key for this element type.
        
        The registry key determines the model folder path:
        models/{registry_key}/model.glb
        
        Returns:
            Registry key string (e.g., 'chair', 'desk', 'external_model_test')
            
        Raises:
            NotImplementedError: If subclass doesn't set _registry_key
        """
        if self._registry_key is None:
            raise NotImplementedError(
                f"{self.__class__.__name__} must set _registry_key class attribute"
            )
        return self._registry_key
    
    def has_external_model(self) -> bool:
        """
        Check if external model exists for this element type.
        
        Subclasses can override this to make external models optional.
        Default implementation checks if model files exist in priority order:
        1. models/{registry_key}/model.glb (preferred for animations)
        2. models/{registry_key}/model.obj + model.mtl (fallback for static)
        
        Returns:
            True if external model exists, False otherwise
        """
        registry_key = self.get_registry_key()
        model_dir = self._models_dir / registry_key
        
        # Priority order: glTF → OBJ → DAE → 3DS
        for name in self._MODEL_FILE_NAMES:
            if (model_dir / name).exists():
                return True
        return False
    
    @property
    def model_metadata(self) -> Optional[ModelMetadata]:
        """
        Get loaded model metadata.
        
        Returns:
            ModelMetadata object if external model exists, None otherwise
        """
        return self._model_metadata
    
    def get_model_format(self) -> Optional[str]:
        """
        Detect the format of the external model.
        
        Returns:
            'gltf' for .glb and .gltf files, 'obj' for .obj files, 'dae' for .dae files, '3ds' for .3ds files, None if no model
        """
        model_path = self.model_path
        if model_path is None:
            return None
        
        return {
            '.glb': 'gltf',
            '.gltf': 'gltf',
            '.obj': 'obj',
            '.dae': 'dae',
            '.3ds': '3ds',
        }.get(model_path.suffix)
    
    @property
    def model_path(self) -> Optional[Path]:
        """
        Get absolute path to external model file.
        
        Returns path in priority order:
        1. model.glb (if exists)
        2. model.obj (if exists)
        3. None (no external model)
        
        Returns:
            Path to model file if external model exists, None otherwise
        """
        if not self.has_external_model():
            return None
        
        registry_key = self.get_registry_key()
        model_dir = self._models_dir / registry_key
        
        # Priority order: glTF → OBJ → DAE → 3DS
        for name in self._MODEL_FILE_NAMES:
            candidate = model_dir / name
            if candidate.exists():
                return candidate
        return None
    
    def get_normalization_transform(self) -> np.ndarray:
        """
        Get 4x4 normalization matrix from model metadata.
        
        This transform brings the model from its native coordinate system
        to the standard space (Y-up, 1 unit = 1 meter, origin at floor center).
        
        Returns:
            4x4 transformation matrix (numpy array)
            
        Raises:
            ValueError: If no external model exists
        """
        if self._model_metadata is None:
            raise ValueError(
                f"No external model metadata loaded for {self.get_registry_key()}. "
                "Cannot get normalization transform."
            )
        
        return self._model_metadata.normalization_matrix
    
    def get_placement_transform(self) -> np.ndarray:
        """
        Get 4x4 placement matrix from element configuration.
        
        This transform positions the model in the scene based on YAML parameters:
        - anchor_point: (x, z) position
        - orientation_angle: Rotation around Y-axis
        - v_anchor: Y-coordinate (height)
        
        Returns:
            4x4 transformation matrix (numpy array)
        """
        return create_placement_matrix(
            anchor_point=self.anchor_point,
            orientation_angle=self.orientation_angle,
            v_anchor=self.v_anchor
        )
    
    # Per-instance secondary transform overrides.
    # Subclasses set these in __init__ when they need to modify the 3D model
    # placement beyond what the static .transform.json normalization provides.
    #
    # secondary_normalization  – dict with optional 'scale', 'rotation', 'translation'
    #                            keys (same format as the normalization section of
    #                            .transform.json).  Applied after the primary
    #                            normalization, before the anchor-offset correction.
    # secondary_anchor_offset  – [x, y, z] list/tuple.  Applied after the primary
    #                            anchor-offset correction, in the same sign convention
    #                            (the value is the current-space position that should
    #                            be moved to the origin, so it is negated internally).
    secondary_normalization: dict | None = None
    secondary_anchor_offset: list | tuple | None = None

    # Per-instance animation descriptor.
    # When set by a subclass __init__, the glTF exporter emits a two-node
    # hierarchy (parent = Placement, child = normalization chain + mesh) and
    # writes this dict into the child node's extras.animation field.
    # The 3D player reads extras.animation to drive interactive animation.
    #
    # Recognised keys (all values in model-local space, metres / degrees):
    #
    #   type            str   'hinge_rotation' | 'slide_translation'
    #   --- hinge_rotation ---
    #   axis            [x,y,z]  unit vector for the rotation axis (Y-up = [0,1,0])
    #   pivot_local     [x,y,z]  pivot point in child-node space (post-normalization)
    #   closed_angle    float    degrees from pivot axis at which door is closed (usually 0)
    #   open_angle      float    degrees at which door is fully open (positive = counter-clockwise)
    #   --- slide_translation ---
    #   axis            [x,y,z]  unit vector in child-node space along which to slide
    #   distance        float    total travel distance in metres
    #   --- common ---
    #   duration        float    animation duration in seconds
    #   trigger         str      'click' | 'auto' (default 'click')
    #
    # None → no animation; exporter emits single node as before.
    animation: dict | None = None

    def get_final_transform(self) -> np.ndarray:
        """
        Get complete transformation matrix for 3D export.

        Transformation pipeline:
        1. ``normalization``          — scale/rotate/translate from model space to normalised space
        2. ``secondary_normalization``— optional per-instance dict override (same format as JSON)
        3. ``anchor_offset``          — translate so the anchor point is at the origin
        4. ``secondary_anchor_offset``— optional additional anchor correction
        5. ``placement``              — rotate by orientation_angle and translate to scene position

        Final transform: Placement × SecAnchor × Anchor × SecNorm × Normalization

        Returns:
            4x4 transformation matrix (numpy array)

        Raises:
            ValueError: If no external model exists
        """
        normalization = self.get_normalization_transform()
        placement = self.get_placement_transform()

        # Step 2 – secondary normalization (optional per-instance dict)
        sec_norm_data = getattr(self, 'secondary_normalization', None)
        sec_norm_matrix = (
            build_normalization_matrix(sec_norm_data)
            if sec_norm_data is not None
            else np.eye(4)
        )

        # Step 3 – primary anchor offset (from .transform.json, negated)
        anchor_offset_matrix = np.eye(4)
        if self._model_metadata and self._model_metadata.anchor_offset != (0.0, 0.0, 0.0):
            off = self._model_metadata.anchor_offset
            anchor_offset_matrix[0, 3] = -off[0]
            anchor_offset_matrix[1, 3] = -off[1]
            anchor_offset_matrix[2, 3] = -off[2]

        # Step 4 – secondary anchor offset (optional per-instance, same sign convention)
        sec_anchor_data = getattr(self, 'secondary_anchor_offset', None)
        sec_anchor_matrix = np.eye(4)
        if sec_anchor_data is not None:
            sec_anchor_matrix[0, 3] = -sec_anchor_data[0]
            sec_anchor_matrix[1, 3] = -sec_anchor_data[1]
            sec_anchor_matrix[2, 3] = -sec_anchor_data[2]

        # Pipeline: normalization → secondary_normalization → anchor_offset
        #           → secondary_anchor_offset → placement
        return compose_transforms(
            placement,
            sec_anchor_matrix,
            anchor_offset_matrix,
            sec_norm_matrix,
            normalization,
        )
    
    def get_bounding_box_corners(self) -> np.ndarray:
        """
        Get 8 corners of axis-aligned bounding box in scene coordinates.
        
        Useful for:
        - Collision detection
        - Spatial queries
        - UI visualization
        
        Returns:
            Array of shape (8, 3) with corner coordinates in scene space
            Order: [min_x, min_z], [max_x, min_z], [max_x, max_z], [min_x, max_z]
                   repeated for bottom (y=min) and top (y=max)
        """
        if self._model_metadata is None or self._model_metadata.bounding_box is None:
            # Fallback: use width/length/height to construct bounding box
            bbox_min = np.array([-self.width/2, 0.0, -self.length/2])
            bbox_max = np.array([self.width/2, self.height, self.length/2])
        else:
            bbox = self._model_metadata.bounding_box
            bbox_min = np.array(bbox.min)
            bbox_max = np.array(bbox.max)
        
        # 8 corners of bounding box in model space
        corners_model = np.array([
            [bbox_min[0], bbox_min[1], bbox_min[2]],  # 0: min x, min y, min z
            [bbox_max[0], bbox_min[1], bbox_min[2]],  # 1: max x, min y, min z
            [bbox_max[0], bbox_min[1], bbox_max[2]],  # 2: max x, min y, max z
            [bbox_min[0], bbox_min[1], bbox_max[2]],  # 3: min x, min y, max z
            [bbox_min[0], bbox_max[1], bbox_min[2]],  # 4: min x, max y, min z
            [bbox_max[0], bbox_max[1], bbox_min[2]],  # 5: max x, max y, min z
            [bbox_max[0], bbox_max[1], bbox_max[2]],  # 6: max x, max y, max z
            [bbox_min[0], bbox_max[1], bbox_max[2]],  # 7: min x, max y, max z
        ])
        
        # Transform to scene space
        if self._model_metadata:
            transform = self.get_final_transform()
        else:
            transform = self.get_placement_transform()
        
        # Apply transform to each corner (homogeneous coordinates)
        corners_homogeneous = np.hstack([corners_model, np.ones((8, 1))])
        corners_scene_homogeneous = (transform @ corners_homogeneous.T).T
        corners_scene = corners_scene_homogeneous[:, :3]
        
        return corners_scene
