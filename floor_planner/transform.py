"""
3D transformation utilities for external model integration.

Provides 4x4 transformation matrix system for model normalization and scene placement.
All matrices use column-major order (GPU-standard format).

Author: Floor Planner Team
Created: 2026-05-27
"""

import math
from typing import Tuple
import numpy as np


def create_placement_matrix(
    anchor_point: Tuple[float, float],
    orientation_angle: float,
    v_anchor: float = 0.0
) -> np.ndarray:
    """
    Generate 4x4 placement matrix from YAML config parameters.
    
    Converts floor plan positioning parameters into a transformation matrix
    that places an element in 3D space. The matrix performs:
    1. Rotation around vertical Y-axis by orientation_angle
    2. Translation to anchor_point position at height v_anchor
    
    Args:
        anchor_point: (x, z) position in floor plan coordinates (meters)
        orientation_angle: Rotation around vertical Y-axis (degrees, counter-clockwise)
        v_anchor: Vertical position / Y-coordinate (meters, default 0.0 = floor level)
        
    Returns:
        4x4 column-major transformation matrix (numpy array, shape [4, 4])
        
    Example:
        >>> matrix = create_placement_matrix(
        ...     anchor_point=[2.0, 3.0],
        ...     orientation_angle=45.0,
        ...     v_anchor=0.0
        ... )
        >>> matrix.shape
        (4, 4)
        >>> # Apply to point: result = matrix @ [x, y, z, 1]
        
    Coordinate System:
        - X-axis: horizontal (left-right in floor plan)
        - Y-axis: vertical (up-down, height)
        - Z-axis: horizontal (forward-backward in floor plan)
        - Origin: floor level, center of space
        - 1 unit = 1 meter
    """
    angle_rad = math.radians(orientation_angle)
    cos_a = math.cos(angle_rad)
    sin_a = math.sin(angle_rad)
    
    # 4x4 transformation matrix in standard form:
    # Translation in the last column (not row!)
    # This allows proper composition: final = placement @ normalization
    matrix = np.array([
        [cos_a,   0.0,      -sin_a,          anchor_point[0]],  # X-axis + Tx
        [0.0,     1.0,       0.0,            v_anchor       ],  # Y-axis + Ty
        [sin_a,   0.0,       cos_a,          anchor_point[1]],  # Z-axis + Tz
        [0.0,     0.0,       0.0,            1.0            ]   # Homogeneous coordinate
    ], dtype=np.float64)
    
    return matrix


def create_identity_matrix() -> np.ndarray:
    """
    Create 4x4 identity transformation matrix.
    
    Returns:
        4x4 identity matrix (no transformation)
    """
    return np.eye(4, dtype=np.float64)


def compose_transforms(*matrices: np.ndarray) -> np.ndarray:
    """
    Compose multiple transformation matrices into a single matrix.
    
    Matrices are applied right-to-left (standard matrix multiplication order).
    For example: compose_transforms(A, B, C) computes A @ B @ C, which means:
    - First apply C
    - Then apply B
    - Finally apply A
    
    Args:
        *matrices: Variable number of 4x4 transformation matrices
        
    Returns:
        Composed 4x4 transformation matrix
        
    Example:
        >>> norm = get_normalization_matrix()  # Model-specific normalization
        >>> place = create_placement_matrix([2, 3], 45, 0)  # Scene placement
        >>> final = compose_transforms(place, norm)  # place × norm
        >>> # Applies: first normalize model, then place in scene
    """
    if not matrices:
        return create_identity_matrix()
    
    result = matrices[0]
    for matrix in matrices[1:]:
        result = result @ matrix
    
    return result


def matrix_to_trs(matrix: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Decompose 4x4 transformation matrix into Translation, Rotation, Scale.
    
    Extracts TRS components from a transformation matrix. Useful for:
    - glTF export (glTF uses separate T/R/S properties)
    - Animation keyframes
    - UI display of element properties
    
    Args:
        matrix: 4x4 transformation matrix
        
    Returns:
        Tuple of (translation, rotation_quat, scale):
        - translation: [x, y, z] vector
        - rotation_quat: [x, y, z, w] quaternion (unit quaternion)
        - scale: [sx, sy, sz] scale factors
        
    Note:
        Assumes the matrix is a valid affine transformation (no shear).
        Rotation is extracted as a quaternion (glTF standard format).
    """
    # Extract translation (last column, first 3 rows)
    translation = matrix[:3, 3]
    
    # Extract 3x3 rotation+scale submatrix
    rot_scale = matrix[:3, :3]
    
    # Extract scale (length of each basis vector)
    scale_x = np.linalg.norm(rot_scale[:, 0])
    scale_y = np.linalg.norm(rot_scale[:, 1])
    scale_z = np.linalg.norm(rot_scale[:, 2])
    scale = np.array([scale_x, scale_y, scale_z])
    
    # Extract pure rotation matrix (normalize basis vectors)
    rotation_matrix = rot_scale / scale
    
    # Convert rotation matrix to quaternion (using Shepperd's method)
    rotation_quat = _rotation_matrix_to_quaternion(rotation_matrix)
    
    return translation, rotation_quat, scale


def _rotation_matrix_to_quaternion(rot_matrix: np.ndarray) -> np.ndarray:
    """
    Convert 3x3 rotation matrix to unit quaternion.
    
    Uses Shepperd's method for numerical stability.
    
    Args:
        rot_matrix: 3x3 rotation matrix
        
    Returns:
        [x, y, z, w] quaternion (unit quaternion, w is scalar part)
    """
    trace = rot_matrix[0, 0] + rot_matrix[1, 1] + rot_matrix[2, 2]
    
    if trace > 0:
        s = 0.5 / math.sqrt(trace + 1.0)
        w = 0.25 / s
        x = (rot_matrix[2, 1] - rot_matrix[1, 2]) * s
        y = (rot_matrix[0, 2] - rot_matrix[2, 0]) * s
        z = (rot_matrix[1, 0] - rot_matrix[0, 1]) * s
    elif rot_matrix[0, 0] > rot_matrix[1, 1] and rot_matrix[0, 0] > rot_matrix[2, 2]:
        s = 2.0 * math.sqrt(1.0 + rot_matrix[0, 0] - rot_matrix[1, 1] - rot_matrix[2, 2])
        w = (rot_matrix[2, 1] - rot_matrix[1, 2]) / s
        x = 0.25 * s
        y = (rot_matrix[0, 1] + rot_matrix[1, 0]) / s
        z = (rot_matrix[0, 2] + rot_matrix[2, 0]) / s
    elif rot_matrix[1, 1] > rot_matrix[2, 2]:
        s = 2.0 * math.sqrt(1.0 + rot_matrix[1, 1] - rot_matrix[0, 0] - rot_matrix[2, 2])
        w = (rot_matrix[0, 2] - rot_matrix[2, 0]) / s
        x = (rot_matrix[0, 1] + rot_matrix[1, 0]) / s
        y = 0.25 * s
        z = (rot_matrix[1, 2] + rot_matrix[2, 1]) / s
    else:
        s = 2.0 * math.sqrt(1.0 + rot_matrix[2, 2] - rot_matrix[0, 0] - rot_matrix[1, 1])
        w = (rot_matrix[1, 0] - rot_matrix[0, 1]) / s
        x = (rot_matrix[0, 2] + rot_matrix[2, 0]) / s
        y = (rot_matrix[1, 2] + rot_matrix[2, 1]) / s
        z = 0.25 * s
    
    return np.array([x, y, z, w])


def load_matrix_from_json(matrix_list: list) -> np.ndarray:
    """
    Load 4x4 transformation matrix from JSON format.
    
    Converts nested list representation (from .transform.json files) to numpy array.
    
    Args:
        matrix_list: 4x4 nested list [[row1], [row2], [row3], [row4]]
        
    Returns:
        4x4 numpy array (float64)
        
    Example:
        >>> json_data = {
        ...     "normalization": {
        ...         "matrix": [
        ...             [1.0, 0.0, 0.0, 0.0],
        ...             [0.0, 1.0, 0.0, 0.0],
        ...             [0.0, 0.0, 1.0, 0.0],
        ...             [0.0, 0.0, 0.0, 1.0]
        ...         ]
        ...     }
        ... }
        >>> matrix = load_matrix_from_json(json_data["normalization"]["matrix"])
    """
    if not isinstance(matrix_list, list) or len(matrix_list) != 4:
        raise ValueError("Matrix must be a 4x4 nested list")
    
    for row in matrix_list:
        if not isinstance(row, list) or len(row) != 4:
            raise ValueError("Each row must contain exactly 4 elements")
    
    return np.array(matrix_list, dtype=np.float64)


def matrix_to_json(matrix: np.ndarray) -> list:
    """
    Convert 4x4 numpy matrix to glTF-compliant flat list.
    
    glTF requires matrices in column-major order as a flat array of 16 numbers.
    
    Args:
        matrix: 4x4 numpy array (row-major in memory)
        
    Returns:
        Flat list of 16 numbers in column-major order
        
    Example:
        >>> matrix = create_identity_matrix()
        >>> json_list = matrix_to_json(matrix)
        >>> len(json_list)
        16
    """
    if matrix.shape != (4, 4):
        raise ValueError("Matrix must be 4x4")
    
    # Flatten in column-major order (Fortran order)
    # This transposes and flattens: [col0, col1, col2, col3]
    return matrix.T.flatten().tolist()


def build_normalization_matrix(data: dict) -> np.ndarray:
    """
    Build a 4x4 transform matrix from a normalization dict.

    Accepts the same format used in ``.transform.json`` normalization sections::

        {'scale': [sx,sy,sz], 'rotation': [rx,ry,rz], 'translation': [tx,ty,tz]}

    All keys are optional; missing keys default to identity values
    (``scale=[1,1,1]``, ``rotation=[0,0,0]``, ``translation=[0,0,0]``).

    Transformation order: **Scale → Rotate → Translate**  (identical to the
    ``normalization`` section parser in ``model_metadata.py``).

    Args:
        data: Dict with optional ``'scale'``, ``'rotation'``, ``'translation'`` lists.

    Returns:
        4x4 transformation matrix (numpy array, dtype float64).
    """
    scale = data.get('scale', [1.0, 1.0, 1.0])
    rotation = data.get('rotation', [0.0, 0.0, 0.0])
    translation = data.get('translation', [0.0, 0.0, 0.0])

    # --- Scale ---
    sx, sy, sz = scale
    scale_matrix = np.array([
        [sx, 0, 0, 0],
        [0, sy, 0, 0],
        [0, 0, sz, 0],
        [0, 0, 0,  1],
    ], dtype=np.float64)

    # --- Rotation (Euler angles in degrees, applied X → Y → Z) ---
    rx, ry, rz = [math.radians(a) for a in rotation]

    cos_x, sin_x = math.cos(rx), math.sin(rx)
    rot_x = np.array([
        [1,     0,      0, 0],
        [0, cos_x, -sin_x, 0],
        [0, sin_x,  cos_x, 0],
        [0,     0,      0, 1],
    ], dtype=np.float64)

    cos_y, sin_y = math.cos(ry), math.sin(ry)
    rot_y = np.array([
        [ cos_y, 0, sin_y, 0],
        [     0, 1,     0, 0],
        [-sin_y, 0, cos_y, 0],
        [     0, 0,     0, 1],
    ], dtype=np.float64)

    cos_z, sin_z = math.cos(rz), math.sin(rz)
    rot_z = np.array([
        [cos_z, -sin_z, 0, 0],
        [sin_z,  cos_z, 0, 0],
        [    0,      0, 1, 0],
        [    0,      0, 0, 1],
    ], dtype=np.float64)

    rotation_matrix = rot_z @ rot_y @ rot_x

    # --- Translation ---
    tx, ty, tz = translation
    translation_matrix = np.array([
        [1, 0, 0, tx],
        [0, 1, 0, ty],
        [0, 0, 1, tz],
        [0, 0, 0,  1],
    ], dtype=np.float64)

    # Translation @ Rotation @ Scale
    return translation_matrix @ rotation_matrix @ scale_matrix

