"""
glTF 2.0 Exporter for Floor Plans

Exports floor plan elements to glTF 2.0 format for 3D visualization.
Supports:
- External model references (OBJ/glTF models from models/ directory)
- Procedural geometry generation (walls, doors, windows)
- Transform hierarchy (normalization × placement)
- Material preservation and texture copying
- Multiple instances of same model

glTF 2.0 Specification: https://www.khronos.org/registry/glTF/specs/2.0/glTF-2.0.html
"""

import base64
import json
import shutil
import struct
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import numpy as np

from floor_planner.transform import (
    create_placement_matrix,
    compose_transforms,
    matrix_to_json,
)
from floor_planner.elements.element import Element
from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.elements.geometry_3d import is_3d_eligible
from floor_planner.elements.registry import get_element_type_from_instance
from floor_planner.texture_manager import TextureManager
from floor_planner.elements.basic import WallND
from floor_planner.wall_openings import find_embedded_openings, generate_wall_with_openings


class BufferBuilder:
    """
    Manages binary buffer data for glTF export.
    
    Handles vertex data, indices, and other binary data that goes into
    the .bin file or data URIs.
    """
    
    def __init__(self):
        self.data = bytearray()
        self.views: List[Dict[str, Any]] = []
        self.accessors: List[Dict[str, Any]] = []
    
    def add_data(self, array: np.ndarray, target: Optional[int] = None) -> int:
        """
        Add numpy array to buffer and create accessor.
        
        Args:
            array: Numpy array to add (will be flattened)
            target: Buffer target (34962=ARRAY_BUFFER, 34963=ELEMENT_ARRAY_BUFFER)
        
        Returns:
            Accessor index
        """
        # Ensure array is in correct format
        if array.dtype == np.float64:
            array = array.astype(np.float32)
        elif array.dtype not in [np.float32, np.uint16, np.uint32]:
            raise ValueError(f"Unsupported dtype: {array.dtype}")
        
        # Flatten array
        flat_data = array.flatten()
        byte_data = flat_data.tobytes()
        
        # Calculate alignment padding (align to 4 bytes)
        byte_offset = len(self.data)
        padding = (4 - (byte_offset % 4)) % 4
        if padding > 0:
            self.data.extend(b'\x00' * padding)
            byte_offset += padding
        
        # Add data to buffer
        byte_length = len(byte_data)
        self.data.extend(byte_data)
        
        # Create buffer view
        buffer_view = {
            "buffer": 0,
            "byteOffset": byte_offset,
            "byteLength": byte_length,
        }
        if target is not None:
            buffer_view["target"] = target
        
        buffer_view_index = len(self.views)
        self.views.append(buffer_view)
        
        # Create accessor
        component_type = {
            np.float32: 5126,  # FLOAT
            np.uint16: 5123,   # UNSIGNED_SHORT
            np.uint32: 5125,   # UNSIGNED_INT
        }[array.dtype.type]
        
        # Determine type (SCALAR, VEC2, VEC3, VEC4)
        shape = array.shape
        if len(shape) == 1:
            accessor_type = "SCALAR"
            count = shape[0]
        elif len(shape) == 2:
            accessor_type = {2: "VEC2", 3: "VEC3", 4: "VEC4"}[shape[1]]
            count = shape[0]
        else:
            raise ValueError(f"Unsupported array shape: {shape}")
        
        # Calculate min/max for position data
        accessor = {
            "bufferView": buffer_view_index,
            "componentType": component_type,
            "count": count,
            "type": accessor_type,
        }
        
        # Add min/max for VEC3 position data (required by spec for bounding boxes)
        if accessor_type == "VEC3" and target == 34962:  # ARRAY_BUFFER
            accessor["min"] = array.min(axis=0).tolist()
            accessor["max"] = array.max(axis=0).tolist()
        
        accessor_index = len(self.accessors)
        self.accessors.append(accessor)
        
        return accessor_index
    
    def get_buffer_data(self) -> bytes:
        """Get final buffer data as bytes."""
        return bytes(self.data)
    
    def get_byte_length(self) -> int:
        """Get total buffer length in bytes."""
        return len(self.data)


class GLTFExporter:
    """
    Exports floor plan to glTF 2.0 format.
    
    glTF structure:
    - asset: Metadata about the glTF file
    - scene: Default scene index
    - scenes: Array of scene definitions
    - nodes: Scene graph nodes (transforms + references)
    - meshes: Geometry definitions
    - materials: Material definitions
    - accessors: Data accessors (views into buffers)
    - bufferViews: Buffer views (byte ranges)
    - buffers: Binary data (geometry, animations, etc.)
    """
    
    def __init__(self, output_dir: Path):
        """
        Initialize glTF exporter.
        
        Args:
            output_dir: Directory to write glTF files and textures
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create textures subdirectory (matching OBJ exporter structure)
        self.textures_dir = self.output_dir / 'textures'
        self.textures_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize texture manager for procedural element textures
        floor_planner_dir = Path(__file__).parent.parent
        default_texture_dir = floor_planner_dir / 'textures' / 'defaults'
        fallback_texture_dir = floor_planner_dir / 'textures' / 'fallback'
        self.texture_manager = TextureManager(default_texture_dir, self.textures_dir, fallback_texture_dir)
        
        self.buffer_builder = BufferBuilder()
        self.nodes: List[Dict[str, Any]] = []
        self.meshes: List[Dict[str, Any]] = []
        self.materials: List[Dict[str, Any]] = []
        self.textures: List[Dict[str, Any]] = []
        self.images: List[Dict[str, Any]] = []
        
        # Track glTF extensions used
        self.extensions_used: set = set()
        
        # Track copied texture files to avoid duplicates
        self.texture_paths: Dict[str, int] = {}  # path -> image index
        
        # Cache loaded meshes to reuse for multiple instances
        self.mesh_cache: Dict[str, int] = {}  # model_path -> mesh index
        
        # Material cache
        self.material_cache: Dict[str, int] = {}  # material_name -> material index
        
        # Store all elements for wall opening detection
        self.all_elements: List[Element] = []
    
    def _select_best_mtl_material(
        self, mtl_materials: Dict[str, Dict[str, Any]]
    ) -> Optional[tuple]:
        """
        Select the best material from parsed MTL properties.

        Scoring: prefer materials with diffuse textures (+10), avoid all-black
        diffuse colors (+5 for non-black). Returns (name, props) or None.
        """
        best_material = None
        best_score = -1

        for material_name, material_props in mtl_materials.items():
            score = 0
            if 'diffuse_texture' in material_props:
                score += 10
            if 'diffuse' in material_props:
                if sum(material_props['diffuse']) > 0.01:
                    score += 5
            if score > best_score:
                best_score = score
                best_material = (material_name, material_props)

        return best_material

    def _add_specular_extension(self, material: Dict[str, Any], specular: List[float]) -> None:
        """
        Add KHR_materials_specular extension to material.
        
        Converts MTL specular color (Ks) to glTF specular intensity and color.
        Uses the same calculation as OBJ viewers: intensity = average of RGB.
        
        Args:
            material: glTF material dict to modify
            specular: RGB specular color from MTL [r, g, b]
        """
        if not specular or len(specular) != 3:
            return
        
        # Calculate specular intensity (same as OBJ viewers)
        specular_intensity = (specular[0] + specular[1] + specular[2]) / 3.0
        
        # Skip if negligible specular
        if specular_intensity < 0.001:
            return
        
        # Normalize specular color (separate intensity from color)
        # For grayscale specular (most common), this will be [1, 1, 1]
        specular_color = [
            specular[0] / specular_intensity if specular_intensity > 0 else 1.0,
            specular[1] / specular_intensity if specular_intensity > 0 else 1.0,
            specular[2] / specular_intensity if specular_intensity > 0 else 1.0
        ]
        
        # Clamp intensity to [0, 3] range (arbitrary upper limit to avoid extreme values)
        # Krzysztof: This is the experimentally adjusted value that gives good results 
        specular_factor = min(specular_intensity, 3.0)
        
        # Add extension to material
        if "extensions" not in material:
            material["extensions"] = {}
        
        material["extensions"]["KHR_materials_specular"] = {
            "specularFactor": specular_factor,
            "specularColorFactor": specular_color
        }
        
        # Mark extension as used
        self.extensions_used.add("KHR_materials_specular")
    
    def _parse_mtl_file(self, mtl_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Parse MTL file and extract material properties.
        
        Args:
            mtl_path: Path to MTL file
        
        Returns:
            Dictionary mapping material names to properties
        """
        materials = {}
        current_material = None
        
        if not mtl_path.exists():
            return materials
        
        try:
            with open(mtl_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    if not line or line.startswith('#'):
                        continue
                    
                    parts = line.split(None, 1)
                    if not parts:
                        continue
                    
                    command = parts[0]
                    args = parts[1] if len(parts) > 1 else ""
                    
                    if command == 'newmtl':
                        current_material = args
                        materials[current_material] = {}
                    
                    elif current_material:
                        if command == 'Ka':  # Ambient color
                            materials[current_material]['ambient'] = [float(x) for x in args.split()]
                        elif command == 'Kd':  # Diffuse color
                            materials[current_material]['diffuse'] = [float(x) for x in args.split()]
                        elif command == 'Ks':  # Specular color
                            materials[current_material]['specular'] = [float(x) for x in args.split()]
                        elif command == 'Ns':  # Specular exponent (shininess)
                            materials[current_material]['shininess'] = float(args)
                        elif command == 'map_Kd':  # Diffuse texture map
                            materials[current_material]['diffuse_texture'] = args
                        elif command == 'd' or command == 'Tr':  # Transparency
                            materials[current_material]['transparency'] = float(args)
        
        except Exception as e:
            print(f"Warning: Failed to parse MTL file {mtl_path}: {e}")
        
        return materials
    
    def _copy_texture(self, texture_path: Path, model_dir: Path) -> Optional[int]:
        """
        Copy texture file to export directory and create glTF image entry.
        
        Args:
            texture_path: Relative path to texture (from MTL file)
            model_dir: Directory containing the model files
        
        Returns:
            Image index if successful, None if failed
        """
        # Resolve texture path (can be just filename or relative path)
        source_path = model_dir / texture_path
        
        if not source_path.exists():
            print(f"Warning: Texture file not found: {source_path}")
            return None
        
        # Check cache
        cache_key = str(source_path)
        if cache_key in self.texture_paths:
            return self.texture_paths[cache_key]
        
        try:
            # Copy texture to textures/ subdirectory (matching OBJ exporter structure)
            dest_filename = source_path.name
            dest_path = self.textures_dir / dest_filename
            
            shutil.copy2(source_path, dest_path)
            
            # Create glTF image entry with textures/ prefix in URI
            image = {
                "uri": f"textures/{dest_filename}",
                "name": source_path.stem
            }
            
            image_index = len(self.images)
            self.images.append(image)
            
            # Cache
            self.texture_paths[cache_key] = image_index
            
            return image_index
            
        except Exception as e:
            print(f"Warning: Failed to copy texture {source_path}: {e}")
            return None
    
    def _create_gltf_material(
        self, 
        material_name: str, 
        mtl_properties: Dict[str, Any],
        model_dir: Path
    ) -> int:
        """
        Create glTF material from MTL properties.
        
        Args:
            material_name: Material name
            mtl_properties: Parsed MTL properties
            model_dir: Directory containing model files
        
        Returns:
            Material index
        """
        # Check cache
        if material_name in self.material_cache:
            return self.material_cache[material_name]
        
        # Convert MTL properties to glTF PBR material
        material = {
            "name": material_name,
            "pbrMetallicRoughness": {}
        }
        
        # Base color from diffuse
        if 'diffuse' in mtl_properties:
            diffuse = mtl_properties['diffuse']
            # If diffuse is black but we have a texture, use white to show texture
            if 'diffuse_texture' in mtl_properties and sum(diffuse) < 0.01:
                diffuse = [1.0, 1.0, 1.0]
            material["pbrMetallicRoughness"]["baseColorFactor"] = diffuse + [1.0]  # Add alpha
        else:
            # Default to white if no diffuse specified
            material["pbrMetallicRoughness"]["baseColorFactor"] = [1.0, 1.0, 1.0, 1.0]
        
        # Diffuse texture
        if 'diffuse_texture' in mtl_properties:
            texture_path = Path(mtl_properties['diffuse_texture'])
            image_index = self._copy_texture(texture_path, model_dir)
            
            if image_index is not None:
                # Create texture
                texture_index = len(self.textures)
                self.textures.append({
                    "source": image_index
                })
                
                # Link to material
                material["pbrMetallicRoughness"]["baseColorTexture"] = {
                    "index": texture_index
                }
        
        # Approximate metallic/roughness from specular
        if 'shininess' in mtl_properties:
            # Convert Phong shininess to roughness (inverse relationship)
            shininess = mtl_properties['shininess']
            roughness = 1.0 - min(shininess / 100.0, 1.0)
            material["pbrMetallicRoughness"]["roughnessFactor"] = roughness
        
        # Assume non-metallic for most materials
        material["pbrMetallicRoughness"]["metallicFactor"] = 0.0
        
        # Add specular extension if specular color is present
        if 'specular' in mtl_properties:
            self._add_specular_extension(material, mtl_properties['specular'])
        
        # Add alphaMode if element has transparency (for external models, typically inherit from MTL)
        # Note: External models don't typically have alpha_mode property, handled separately
        
        # Add to materials list
        material_index = len(self.materials)
        self.materials.append(material)
        
        # Cache
        self.material_cache[material_name] = material_index
        
        return material_index
    
    def _parse_obj_with_uvs(self, obj_path: Path):
        """
        Parse OBJ file and expand vertices to handle multiple UVs per vertex.
        
        OBJ files can use the same vertex position with different UV coordinates.
        This creates expanded vertex arrays where each unique (v, vt) pair gets
        a separate vertex entry, ensuring POSITION and TEXCOORD_0 have matching counts.
        
        Args:
            obj_path: Path to OBJ file
        
        Returns:
            Tuple of (vertices, normals, uvs, faces) as numpy arrays, or (None, None, None, None)
        """
        try:
            v_list = []   # Vertex positions
            vt_list = []  # Texture coordinates
            vn_list = []  # Vertex normals
            
            # Map (v_idx, vt_idx, vn_idx) -> expanded vertex index
            vertex_map = {}
            expanded_vertices = []
            expanded_normals = []
            expanded_uvs = []
            expanded_faces = []
            
            with open(obj_path, 'r') as f:
                for line in f:
                    line = line.strip()
                    
                    if line.startswith('v '):
                        # Vertex position
                        parts = line.split()
                        v_list.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    
                    elif line.startswith('vt '):
                        # Texture coordinate
                        parts = line.split()
                        u = float(parts[1])
                        v = float(parts[2]) if len(parts) > 2 else 0.0
                        vt_list.append([u, v])
                    
                    elif line.startswith('vn '):
                        # Vertex normal
                        parts = line.split()
                        vn_list.append([float(parts[1]), float(parts[2]), float(parts[3])])
                    
                    elif line.startswith('f '):
                        # Face definition: f v1/vt1/vn1 v2/vt2/vn2 v3/vt3/vn3 ...
                        parts = line.split()[1:]  # Skip 'f'
                        face_indices = []
                        
                        for part in parts:
                            indices = part.split('/')
                            v_idx = int(indices[0]) - 1  # OBJ is 1-indexed
                            vt_idx = int(indices[1]) - 1 if len(indices) > 1 and indices[1] else -1
                            vn_idx = int(indices[2]) - 1 if len(indices) > 2 and indices[2] else -1
                            
                            # Create unique key for this vertex/uv/normal combination
                            key = (v_idx, vt_idx, vn_idx)
                            
                            if key not in vertex_map:
                                # Create new expanded vertex
                                new_idx = len(expanded_vertices)
                                vertex_map[key] = new_idx
                                
                                expanded_vertices.append(v_list[v_idx])
                                
                                if vt_idx >= 0 and vt_idx < len(vt_list):
                                    expanded_uvs.append(vt_list[vt_idx])
                                else:
                                    expanded_uvs.append([0.0, 0.0])
                                
                                if vn_idx >= 0 and vn_idx < len(vn_list):
                                    expanded_normals.append(vn_list[vn_idx])
                                else:
                                    expanded_normals.append([0.0, 1.0, 0.0])
                            
                            face_indices.append(vertex_map[key])
                        
                        # Triangulate face if needed (for quads, etc.)
                        if len(face_indices) == 3:
                            expanded_faces.append(face_indices)
                        elif len(face_indices) == 4:
                            # Split quad into two triangles
                            expanded_faces.append([face_indices[0], face_indices[1], face_indices[2]])
                            expanded_faces.append([face_indices[0], face_indices[2], face_indices[3]])
                        elif len(face_indices) > 4:
                            # Fan triangulation for n-gons
                            for i in range(1, len(face_indices) - 1):
                                expanded_faces.append([face_indices[0], face_indices[i], face_indices[i+1]])
            
            if not expanded_vertices:
                return None, None, None, None
            
            vertices = np.array(expanded_vertices, dtype=np.float32)
            uvs = np.array(expanded_uvs, dtype=np.float32) if expanded_uvs else None
            normals = np.array(expanded_normals, dtype=np.float32) if expanded_normals else None
            faces = np.array(expanded_faces, dtype=np.uint32)
            
            return vertices, normals, uvs, faces
            
        except Exception as e:
            print(f"Warning: Failed to parse OBJ with UVs from {obj_path}: {e}")
            import traceback
            traceback.print_exc()
            return None, None, None, None
    
    def _load_obj_as_mesh(self, obj_path: Path) -> Optional[int]:
        """
        Load OBJ file and convert to glTF mesh.
        
        Args:
            obj_path: Path to OBJ file
        
        Returns:
            Mesh index if successful, None if failed
        """
        # Check cache first
        cache_key = str(obj_path)
        if cache_key in self.mesh_cache:
            return self.mesh_cache[cache_key]
        
        try:
            # Parse OBJ file with proper UV handling (expands vertices for unique v/vt pairs)
            vertices, normals, uvs, faces = self._parse_obj_with_uvs(obj_path)
            
            if vertices is None:
                print(f"Warning: Failed to parse OBJ file {obj_path}")
                return None
            
            # Create vertex position accessor
            position_accessor = self.buffer_builder.add_data(
                vertices,
                target=34962  # ARRAY_BUFFER
            )
            
            # Create face indices accessor (flatten to 1D)
            indices_flat = faces.flatten()
            indices_accessor = self.buffer_builder.add_data(
                indices_flat,
                target=34963  # ELEMENT_ARRAY_BUFFER
            )
            
            # Create primitive
            primitive = {
                "attributes": {
                    "POSITION": position_accessor
                },
                "indices": indices_accessor,
                "mode": 4  # TRIANGLES
            }
            
            # Add normals if available
            if normals is not None:
                normal_accessor = self.buffer_builder.add_data(
                    normals,
                    target=34962  # ARRAY_BUFFER
                )
                primitive["attributes"]["NORMAL"] = normal_accessor
            
            # Add UV texture coordinates if available
            if uvs is not None:
                texcoord_accessor = self.buffer_builder.add_data(
                    uvs,
                    target=34962  # ARRAY_BUFFER
                )
                primitive["attributes"]["TEXCOORD_0"] = texcoord_accessor
            
            # Parse and apply materials from MTL file
            model_dir = obj_path.parent
            mtl_path = model_dir / obj_path.with_suffix('.mtl').name
            
            if mtl_path.exists():
                mtl_materials = self._parse_mtl_file(mtl_path)

                # Apply best material if found
                best_material = self._select_best_mtl_material(mtl_materials)
                if best_material:
                    material_name, material_props = best_material

                    material_index = self._create_gltf_material(
                        material_name,
                        material_props,
                        model_dir
                    )

                    primitive["material"] = material_index
            
            # Create mesh
            gltf_mesh = {
                "name": obj_path.stem,
                "primitives": [primitive]
            }
            
            mesh_index = len(self.meshes)
            self.meshes.append(gltf_mesh)
            
            # Cache for reuse
            self.mesh_cache[cache_key] = mesh_index
            
            return mesh_index
            
        except Exception as e:
            print(f"Warning: Failed to load OBJ file {obj_path}: {e}")
            return None
    
    def add_element(self, element: Element) -> Optional[int]:
        """
        Add floor plan element to scene.
        
        Args:
            element: Floor plan element to export
        
        Returns:
            Node index if added, None if element cannot be exported
        """
        # Check if element has external model
        if isinstance(element, ExternalModelElement) and element.has_external_model():
            return self._add_external_model_element(element)
        # Check if element has procedural 3D geometry
        elif hasattr(element, 'generate_vertices_and_indices'):
            return self._add_procedural_element(element)
        else:
            # Skip elements without 3D representation (dimensions, labels, rooms)
            return None
    
    def _generate_box_geometry_with_uvs(self, element, vertices: list[tuple[float, float, float]], 
                                         indices: list[tuple[int, int, int]]) -> tuple[list[tuple[float, float, float]], 
                                                                                        list[tuple[int, int, int]], 
                                                                                        list[tuple[float, float]]]:
        """
        Generate box geometry with proper per-face UV mapping.
        
        Expands 8 unique vertices to 24 vertices (4 per face × 6 faces) so each face
        can have independent texture coordinates. Remaps triangle indices accordingly.
        
        Args:
            element: The floor plan element (to access dimensions and texture_scale)
            vertices: List of 8 unique vertex positions
            indices: List of triangle indices referencing the 8 vertices
            
        Returns:
            Tuple of:
            - expanded_vertices: 24 vertices (4 per face × 6 faces)
            - remapped_indices: Triangle indices for expanded vertices
            - texcoords: 24 UV coordinates matching expanded vertices
        """
        vertex_count = len(vertices)
        
        if vertex_count != 8:
            # Fallback for non-box geometries
            return vertices, indices, [(0.0, 0.0)] * vertex_count
        
        # Calculate physical dimensions from vertices
        # Box layout: vertices 0-3 are bottom corners, 4-7 are top corners
        length = ((vertices[1][0] - vertices[0][0])**2 + 
                 (vertices[1][2] - vertices[0][2])**2)**0.5
        thickness = ((vertices[3][0] - vertices[0][0])**2 + 
                    (vertices[3][2] - vertices[0][2])**2)**0.5
        height = abs(vertices[4][1] - vertices[0][1])
        
        # Get texture scale parameter for tiling
        texture_scale = getattr(element, 'texture_scale', None)
        
        # Calculate UV repeats based on physical size
        if texture_scale and texture_scale > 0:
            u_length = length / texture_scale
            u_thickness = thickness / texture_scale
            v_height = height / texture_scale
        else:
            u_length = 1.0
            u_thickness = 1.0
            v_height = 1.0
        
        # Build 24 expanded vertices (4 per face × 6 faces) with proper UVs
        expanded_vertices = []
        texcoords = []
        
        # Bottom face (vertices 0-3): Use original vertices 0,1,2,3
        for i in [0, 1, 2, 3]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([
            (0.0, 0.0),
            (u_length, 0.0),
            (u_length, u_thickness),
            (0.0, u_thickness),
        ])
        
        # Top face (vertices 4-7): Use original vertices 4,5,6,7
        for i in [4, 5, 6, 7]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([
            (0.0, 0.0),
            (u_length, 0.0),
            (u_length, u_thickness),
            (0.0, u_thickness),
        ])
        
        # Front face: Use original vertices 0,1,5,4
        for i in [0, 1, 5, 4]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([
            (0.0, 0.0),
            (u_length, 0.0),
            (u_length, v_height),
            (0.0, v_height),
        ])
        
        # Back face: Use original vertices 2,3,7,6
        for i in [2, 3, 7, 6]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([
            (u_length, 0.0),
            (0.0, 0.0),
            (0.0, v_height),
            (u_length, v_height),
        ])
        
        # Right face: Use original vertices 1,2,6,5
        for i in [1, 2, 6, 5]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([
            (0.0, 0.0),
            (u_thickness, 0.0),
            (u_thickness, v_height),
            (0.0, v_height),
        ])
        
        # Left face: Use original vertices 3,0,4,7
        for i in [3, 0, 4, 7]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([
            (u_thickness, 0.0),
            (0.0, 0.0),
            (0.0, v_height),
            (u_thickness, v_height),
        ])
        
        # Remap triangle indices to expanded vertex layout
        # Original indices reference vertices 0-7
        # New layout: [bottom 0-3, top 4-7, front 8-11, back 12-15, right 16-19, left 20-23]
        
        # Map from (original_triangle_index) to (face_base_index, local_indices)
        # Based on FIXED geometry_3d.py RectangularGeometry3D.generate_vertices_and_indices()
        # Note: Triangle order was fixed to produce correct outward normals
        face_remapping = {
            # Bottom face triangles (0-1) - FIXED winding: (0,1,2) and (0,2,3)
            0: (0, [(0, 0), (1, 1), (2, 2)]),   # Triangle (0,1,2)
            1: (0, [(0, 0), (2, 2), (3, 3)]),   # Triangle (0,2,3)
            
            # Top face triangles (2-3) - FIXED winding: (4,6,5) and (4,7,6)
            2: (4, [(4, 0), (6, 2), (5, 1)]),   # Triangle (4,6,5)
            3: (4, [(4, 0), (7, 3), (6, 2)]),   # Triangle (4,7,6)
            
            # Front face triangles (4-5) - FIXED winding: (0,5,1) and (0,4,5)
            4: (8, [(0, 0), (5, 2), (1, 1)]),   # Triangle (0,5,1)
            5: (8, [(0, 0), (4, 3), (5, 2)]),   # Triangle (0,4,5)
            
            # Back face triangles (6-7) - FIXED winding: (2,7,3) and (2,6,7)
            6: (12, [(2, 0), (7, 2), (3, 1)]),  # Triangle (2,7,3)
            7: (12, [(2, 0), (6, 3), (7, 2)]),  # Triangle (2,6,7)
            
            # Right face triangles (8-9) - FIXED winding: (1,6,2) and (1,5,6)
            8: (16, [(1, 0), (6, 2), (2, 1)]),  # Triangle (1,6,2)
            9: (16, [(1, 0), (5, 3), (6, 2)]),  # Triangle (1,5,6)
            
            # Left face triangles (10-11) - FIXED winding: (3,4,0) and (3,7,4)
            10: (20, [(3, 0), (4, 2), (0, 1)]), # Triangle (3,4,0)
            11: (20, [(3, 0), (7, 3), (4, 2)]), # Triangle (3,7,4)
        }
        
        remapped_indices = []
        for tri_idx, (v1, v2, v3) in enumerate(indices):
            if tri_idx in face_remapping:
                base_idx, local_map = face_remapping[tri_idx]
                # Map each vertex to its position in the face's 4-vertex set
                new_v1 = base_idx + local_map[0][1]
                new_v2 = base_idx + local_map[1][1]
                new_v3 = base_idx + local_map[2][1]
                remapped_indices.append((new_v1, new_v2, new_v3))
            else:
                # Fallback: keep original indices (shouldn't happen for standard boxes)
                remapped_indices.append((v1, v2, v3))
        
        return expanded_vertices, remapped_indices, texcoords
    
    def _generate_normals(self, vertices: list[tuple[float, float, float]], 
                         indices: list[tuple[int, int, int]],
                         triangle_indices_to_process: list[int] = None) -> list[tuple[float, float, float]]:
        """
        Generate per-vertex normals from triangle data.
        
        Uses flat shading approach: each triangle contributes its face normal
        to all vertices it uses. For the expanded 24-vertex box geometry where
        vertices are duplicated per face, this produces correct flat-shaded normals.
        
        Args:
            vertices: List of vertex positions
            indices: List of triangle indices
            triangle_indices_to_process: Optional list of triangle indices to process.
                                        If None, processes all triangles.
            
        Returns:
            List of normal vectors (one per vertex)
        """
        # Initialize normals (will accumulate contributions from triangles)
        normals = [np.array([0.0, 0.0, 0.0]) for _ in vertices]
        
        # Calculate face normal for each triangle and add to vertex normals
        for tri_idx, (v1_idx, v2_idx, v3_idx) in enumerate(indices):
            # Skip triangles not in the process list (if specified)
            if triangle_indices_to_process is not None and tri_idx not in triangle_indices_to_process:
                continue
            
            # Get vertex positions
            v1 = np.array(vertices[v1_idx])
            v2 = np.array(vertices[v2_idx])
            v3 = np.array(vertices[v3_idx])
            
            # Calculate face normal using cross product
            edge1 = v2 - v1
            edge2 = v3 - v1
            face_normal = np.cross(edge1, edge2)
            
            # Normalize (skip zero-length normals from degenerate triangles)
            length = np.linalg.norm(face_normal)
            if length > 1e-6:
                face_normal = face_normal / length
            else:
                face_normal = np.array([0.0, 1.0, 0.0])  # Default up
            
            # Add to all three vertices (for flat shading with duplicated vertices)
            normals[v1_idx] += face_normal
            normals[v2_idx] += face_normal
            normals[v3_idx] += face_normal
        
        # Normalize all vertex normals
        normalized_normals = []
        for normal in normals:
            length = np.linalg.norm(normal)
            if length > 1e-6:
                normal = normal / length
            else:
                normal = np.array([0.0, 1.0, 0.0])  # Default up
            normalized_normals.append((normal[0], normal[1], normal[2]))
        
        return normalized_normals
    
    def _generate_wall_opening_uvs(
        self,
        wall: 'WallND',
        vertices: list[tuple[float, float, float]],
        indices: list[tuple[int, int, int]],
        face_groups: dict[str, list[int]]
    ) -> list[tuple[float, float]]:
        """
        Generate proper UV coordinates for walls with openings.
        
        Each face type gets appropriate UV mapping based on its orientation.
        UVs are assigned per-triangle to handle shared vertices correctly.
        
        Args:
            wall: Wall element
            vertices: List of vertex positions
            indices: List of triangle indices
            face_groups: Dict mapping face names to triangle indices
            
        Returns:
            List of (u, v) texture coordinates for each vertex
        """
        # Initialize UV coords
        texcoords = [(0.0, 0.0) for _ in vertices]
        
        # Get wall properties
        wall_length = wall.length
        wall_thickness = wall.thickness
        wall_height = wall.height
        wall_angle = wall.orientation_angle
        wall_anchor = wall.anchor_point
        wall_v_anchor = wall.v_anchor
        
        # Calculate wall's local coordinate axes in world space
        angle_rad = np.radians(wall_angle)
        # X-axis: along wall length
        x_axis = np.array([np.cos(angle_rad), 0, np.sin(angle_rad)])
        # Y-axis: up (height)
        y_axis = np.array([0, 1, 0])
        # Z-axis: along wall thickness (perpendicular to wall)
        z_axis = np.array([-np.sin(angle_rad), 0, np.cos(angle_rad)])
        
        # Wall anchor in 3D
        anchor_3d = np.array([wall_anchor[0], 0, wall_anchor[1]])
        
        def assign_uvs_for_face(tri_idx: int, face_type: str):
            """Assign UVs to all vertices of a triangle based on face type."""
            i1, i2, i3 = indices[tri_idx]
            
            # For opening edges, determine orientation from triangle geometry
            if face_type == 'opening_edges':
                # Get all three vertex positions in local coordinates
                local_positions = []
                for v_idx in [i1, i2, i3]:
                    vx, vy, vz = vertices[v_idx]
                    v_pos = np.array([vx, vy, vz])
                    relative = v_pos - anchor_3d
                    local_x = np.dot(relative, x_axis)
                    local_y = vy - wall_v_anchor
                    local_z = np.dot(relative, z_axis)
                    local_positions.append((local_x, local_y, local_z))
                
                # Check coordinate variation to determine edge type
                x_coords = [p[0] for p in local_positions]
                y_coords = [p[1] for p in local_positions]
                
                x_range = max(x_coords) - min(x_coords)
                y_range = max(y_coords) - min(y_coords)
                
                # Determine if horizontal (Y constant) or vertical (X constant) edge
                is_horizontal_edge = y_range < 0.01  # Y doesn't vary = horizontal edge
                is_vertical_edge = x_range < 0.01    # X doesn't vary = vertical edge
            
            for v_idx in [i1, i2, i3]:
                vx, vy, vz = vertices[v_idx]
                v_pos = np.array([vx, vy, vz])
                
                # Transform to wall's local coordinate system
                relative = v_pos - anchor_3d
                local_x = np.dot(relative, x_axis)  # Along wall length (0 to wall_length)
                local_y = vy - wall_v_anchor  # Height from wall base (0 to wall_height)
                local_z = np.dot(relative, z_axis)  # Along wall thickness (0 to wall_thickness)
                
                # Calculate UV based on face type
                if face_type == 'front' or face_type == 'back':
                    # Front/back faces: map to wall length × height
                    u = local_x / wall_length
                    v = local_y / wall_height
                
                elif face_type == 'top' or face_type == 'bottom':
                    # Top/bottom faces: map to wall length × thickness
                    u = local_x / wall_length
                    v = local_z / wall_thickness
                
                elif face_type == 'left' or face_type == 'right':
                    # Left/right edge faces: map to thickness × height
                    u = local_z / wall_thickness
                    v = local_y / wall_height
                
                elif face_type == 'opening_edges':
                    # Opening edges connect front to back of wall
                    if is_horizontal_edge:
                        # Horizontal edge (top/bottom of opening): varies in X and Z
                        u = local_x / wall_length
                        v = local_z / wall_thickness
                    elif is_vertical_edge:
                        # Vertical edge (left/right of opening): varies in Y and Z
                        u = local_z / wall_thickness
                        v = local_y / wall_height
                    else:
                        # Fallback: use thickness and height
                        u = local_z / wall_thickness
                        v = local_y / wall_height
                
                else:
                    # Fallback for unknown face types
                    u = local_x / wall_length
                    v = local_y / wall_height
                
                # Clamp UVs to [0, 1] range
                u = max(0.0, min(1.0, u))
                v = max(0.0, min(1.0, v))
                
                texcoords[v_idx] = (u, v)
        
        # Process face groups in priority order
        # Process outer faces first, then opening edges last to ensure they take precedence
        # Skip 'sides' and 'all' as they're aggregate groups that overlap with specific face types
        face_priority = ['bottom', 'top', 'left', 'right', 'front', 'back', 'opening_edges']
        
        for face_type in face_priority:
            if face_type in face_groups:
                for tri_idx in face_groups[face_type]:
                    assign_uvs_for_face(tri_idx, face_type)
        
        return texcoords
    
    def _add_procedural_element(self, element: Element) -> int:
        """
        Add element with procedurally generated 3D geometry.
        
        Args:
            element: Element with generate_vertices_and_indices() method
        
        Returns:
            Node index
        """
        # Apply z-fighting prevention for walls: shrink length and offset position slightly
        if isinstance(element, WallND):
            # Store original values
            original_length = element.length
            original_anchor = element.anchor_point
            
            # Calculate direction vector from orientation angle
            angle_rad = np.radians(element.orientation_angle)
            direction_x = np.cos(angle_rad)
            direction_y = np.sin(angle_rad)
            
            # Adjust: move anchor 0.001m forward, reduce length by 0.002m (0.001m on each end)
            element.anchor_point = (
                original_anchor[0] + 0.001 * direction_x,
                original_anchor[1] + 0.001 * direction_y
            )
            element.length = original_length - 0.002
        
        # Generate geometry (with wall opening detection)
        has_openings = False
        if isinstance(element, WallND) and self.all_elements:
            # Check if this wall has embedded doors/windows
            embedded_openings = find_embedded_openings(element, self.all_elements)
            
            if embedded_openings:
                # Generate wall geometry with holes (returns full 3D mesh)
                vertices, indices, face_groups = generate_wall_with_openings(element, embedded_openings)
                has_openings = True
            else:
                # Standard wall geometry (no openings)
                vertices, indices, face_groups = element.generate_vertices_and_indices()
        else:
            # Standard geometry for non-wall elements
            vertices, indices, face_groups = element.generate_vertices_and_indices()
        
        # Check if this is simple box geometry (8 vertices) or complex mesh
        is_simple_box = (len(vertices) == 8)
        
        if is_simple_box:
            # Generate proper per-face UV mapping (expands 8 vertices to 24)
            expanded_vertices, remapped_indices, texcoords = self._generate_box_geometry_with_uvs(
                element, vertices, indices
            )
        else:
            # Complex geometry (walls with openings) - use vertices directly
            expanded_vertices = vertices
            remapped_indices = indices
            
            # Generate proper per-face UVs for walls with openings
            if has_openings and isinstance(element, WallND):
                texcoords = self._generate_wall_opening_uvs(
                    element, vertices, indices, face_groups
                )
            else:
                # Generic planar UVs for other complex geometry
                texcoords = []
                for x, y, z in vertices:
                    u = (x % 4.0) / 4.0
                    v = (y % 3.0) / 3.0
                    texcoords.append((u, v))
        
        # Convert to numpy arrays
        vertices_array = np.array(expanded_vertices, dtype=np.float32)
        indices_array = np.array(remapped_indices, dtype=np.uint32).flatten()
        texcoords_array = np.array(texcoords, dtype=np.float32)
        
        # Generate normals from triangle geometry
        if has_openings:
            # For walls with openings, generate normals for all triangles
            normals = self._generate_normals(expanded_vertices, remapped_indices)
        else:
            # For simple walls and other elements, generate normals for all triangles
            normals = self._generate_normals(expanded_vertices, remapped_indices)

        normals_array = np.array(normals, dtype=np.float32)

        # Create vertex position accessor
        position_accessor = self.buffer_builder.add_data(
            vertices_array,
            target=34962  # ARRAY_BUFFER
        )
        
        # Create face indices accessor
        indices_accessor = self.buffer_builder.add_data(
            indices_array,
            target=34963  # ELEMENT_ARRAY_BUFFER
        )
        
        # Create texture coordinate accessor
        texcoord_accessor = self.buffer_builder.add_data(
            texcoords_array,
            target=34962  # ARRAY_BUFFER
        )
        
        # Create normal accessor
        normal_accessor = self.buffer_builder.add_data(
            normals_array,
            target=34962  # ARRAY_BUFFER
        )
        
        # Create primitive
        primitive = {
            "attributes": {
                "POSITION": position_accessor,
                "NORMAL": normal_accessor,
                "TEXCOORD_0": texcoord_accessor
            },
            "indices": indices_accessor,
            "mode": 4  # TRIANGLES
        }
        
        # Apply default material based on element type
        material_index = self._get_default_material(element)
        if material_index is not None:
            primitive["material"] = material_index
        
        # Create mesh
        element_type = element.__class__.__name__
        gltf_mesh = {
            "name": f"{element_type}_{element.id}",
            "primitives": [primitive]
        }
        
        mesh_index = len(self.meshes)
        self.meshes.append(gltf_mesh)
        
        # Create node
        node = {
            "name": f"{element_type}_{element.id}",
            "mesh": mesh_index,
            "extras": {
                "element_type": element_type,
                "element_id": element.id,
                "procedural": True
            }
        }
        
        node_index = len(self.nodes)
        self.nodes.append(node)
        
        return node_index
    
    def _get_default_material(self, element: Element) -> Optional[int]:
        """
        Get or create default material for element type with texture support.
        
        Uses TextureManager to resolve textures from fallback directory.
        Reads MTL files for material properties (Kd, Ks, Ns).
        Falls back to solid colors if no MTL found.
        
        Args:
            element: Element to get material for
        
        Returns:
            Material index, or None if no material needed
        """
        # Get element type from registry (snake_case)
        element_type = get_element_type_from_instance(element)
        
        # Check cache (per element type, not per material name)
        if element_type in self.material_cache:
            return self.material_cache[element_type]
        
        # Get texture specification from element
        texture_spec = getattr(element, 'textures', None)
        
        # Resolve textures using TextureManager
        texture_paths = self.texture_manager.resolve_element_textures(
            element_type, texture_spec, Path.cwd()
        )
        
        # Try to find and parse MTL file for this element type
        mtl_properties = None
        texture_path = texture_paths.get('all') or next(iter(texture_paths.values()), None)
        
        if texture_path:
            texture_path = Path(texture_path)
            # MTL file should be in same directory as texture
            mtl_path = texture_path.parent / f"{element_type}.mtl"
            
            if mtl_path.exists():
                mtl_materials = self._parse_mtl_file(mtl_path)

                best_material = self._select_best_mtl_material(mtl_materials)
                if best_material:
                    mtl_properties = best_material[1]
        
        # Create material using MTL properties or defaults
        material_name = f"{element_type}_material"
        material = {
            "name": material_name,
            "pbrMetallicRoughness": {}
        }
        
        # Set base color from MTL diffuse (Kd) or default
        if mtl_properties and 'diffuse' in mtl_properties:
            diffuse = mtl_properties['diffuse']
            # If diffuse is black but we have a texture, use white to show texture
            if 'diffuse_texture' in mtl_properties and sum(diffuse) < 0.01:
                diffuse = [1.0, 1.0, 1.0]
            material["pbrMetallicRoughness"]["baseColorFactor"] = diffuse + [1.0]
        else:
            # Fallback colors if no MTL found
            default_colors = {
                'wall': [0.95, 0.95, 0.95],
                'wall_nd': [0.95, 0.95, 0.95],
                'door': [0.7, 0.4, 0.2],
                'window': [0.8, 0.9, 1.0],
            }
            base_color = default_colors.get(element_type, [0.8, 0.8, 0.8])
            material["pbrMetallicRoughness"]["baseColorFactor"] = base_color + [1.0]
        
        # Set roughness from MTL shininess (Ns) or default
        if mtl_properties and 'shininess' in mtl_properties:
            # Convert Phong shininess to roughness (inverse relationship)
            shininess = mtl_properties['shininess']
            roughness = 1.0 - min(shininess / 100.0, 1.0)
            material["pbrMetallicRoughness"]["roughnessFactor"] = roughness
        else:
            # Default roughness
            material["pbrMetallicRoughness"]["roughnessFactor"] = 0.8
        
        # Metallic factor (typically non-metallic for architectural elements)
        material["pbrMetallicRoughness"]["metallicFactor"] = 0.0
        
        # Add specular extension if specular color is present in MTL
        if mtl_properties and 'specular' in mtl_properties:
            self._add_specular_extension(material, mtl_properties['specular'])
        
        # Add alphaMode if element has transparency
        if hasattr(element, 'alpha_mode') and element.alpha_mode == "BLEND":
            material["alphaMode"] = "BLEND"
        
        # Add texture if available
        if texture_path and texture_path.exists():
            # Check cache to avoid copying same texture multiple times
            cache_key = str(texture_path)
            if cache_key not in self.texture_paths:
                try:
                    # Copy to textures/ subdirectory
                    dest_filename = texture_path.name
                    dest_path = self.textures_dir / dest_filename
                    
                    if not dest_path.exists():
                        shutil.copy2(texture_path, dest_path)
                    
                    # Create glTF image entry
                    image = {
                        "uri": f"textures/{dest_filename}",
                        "name": texture_path.stem
                    }
                    
                    image_index = len(self.images)
                    self.images.append(image)
                    
                    # Cache
                    self.texture_paths[cache_key] = image_index
                    
                except Exception as e:
                    print(f"Warning: Failed to copy texture {texture_path}: {e}")
                    image_index = None
            else:
                image_index = self.texture_paths[cache_key]
            
            # Create texture and link to material
            if image_index is not None:
                texture_index = len(self.textures)
                self.textures.append({
                    "source": image_index
                })
                
                material["pbrMetallicRoughness"]["baseColorTexture"] = {
                    "index": texture_index
                }
        
        material_index = len(self.materials)
        self.materials.append(material)
        
        # Cache
        self.material_cache[element_type] = material_index
        
        return material_index
    
    def _add_external_model_element(self, element: ExternalModelElement) -> int:
        """
        Add element with external 3D model.
        
        Args:
            element: Element with external model
        
        Returns:
            Node index
        """
        # Get model path and format
        model_path = element.model_path
        model_format = element.get_model_format()
        
        # Get placement transform (includes normalization)
        final_transform = element.get_final_transform()
        
        # Create node with transform
        node = {
            "name": f"{element.get_registry_key()}_{len(self.nodes):03d}",
            "matrix": matrix_to_json(final_transform),
            "extras": {
                "element_type": element.get_registry_key(),
                "external_model": True,
                "model_path": str(model_path),
                "model_format": model_format,
            }
        }
        
        # Load mesh geometry if available
        if model_path and model_format == 'obj':
            mesh_index = self._load_obj_as_mesh(model_path)
            if mesh_index is not None:
                node["mesh"] = mesh_index
        elif model_path and model_format == 'gltf':
            # TODO: Implement glTF model loading
            print(f"Warning: glTF model loading not yet implemented for {model_path}")
        
        node_index = len(self.nodes)
        self.nodes.append(node)
        
        return node_index
    
    def export(self, filename: str = "floor_plan_3d.gltf") -> Path:
        """
        Export scene to glTF file.
        
        Args:
            filename: Output filename (default: floor_plan_3d.gltf)
        
        Returns:
            Path to exported glTF file
        """
        output_path = self.output_dir / filename
        
        # Build glTF JSON structure
        gltf = {
            "asset": {
                "version": "2.0",
                "generator": "Floor Planner v2.0",
                "copyright": "Floor Planner"
            },
            "scene": 0,
            "scenes": [
                {
                    "name": "Floor Plan Scene",
                    "nodes": list(range(len(self.nodes)))
                }
            ],
            "nodes": self.nodes,
        }
        
        # Add extensions used (if any)
        if self.extensions_used:
            gltf["extensionsUsed"] = sorted(list(self.extensions_used))
        
        # Add optional sections if they exist
        if self.meshes:
            gltf["meshes"] = self.meshes
        
        if self.materials:
            gltf["materials"] = self.materials
        
        if self.textures:
            gltf["textures"] = self.textures
        
        if self.images:
            gltf["images"] = self.images
        
        if self.buffer_builder.accessors:
            gltf["accessors"] = self.buffer_builder.accessors
        
        if self.buffer_builder.views:
            gltf["bufferViews"] = self.buffer_builder.views
        
        # Add buffer if there's data
        if self.buffer_builder.get_byte_length() > 0:
            # Write binary buffer to separate .bin file
            bin_filename = filename.replace('.gltf', '.bin')
            bin_path = self.output_dir / bin_filename
            
            with open(bin_path, 'wb') as f:
                f.write(self.buffer_builder.get_buffer_data())
            
            gltf["buffers"] = [
                {
                    "byteLength": self.buffer_builder.get_byte_length(),
                    "uri": bin_filename
                }
            ]
        
        # Write glTF JSON file
        with open(output_path, 'w') as f:
            json.dump(gltf, f, indent=2)
        
        return output_path


def export_floor_plan_to_gltf(
    elements: List[Element],
    output_dir: Path,
    filename: str = "floor_plan_3d.gltf"
) -> Path:
    """
    Export floor plan elements to glTF format.
    
    Args:
        elements: List of floor plan elements to export
        output_dir: Directory to write glTF files
        filename: Output filename
    
    Returns:
        Path to exported glTF file
    """
    exporter = GLTFExporter(output_dir)
    
    # Store all elements for wall opening detection (includes invisible elements)
    exporter.all_elements = elements
    
    # Add all 3D-eligible elements (skips invisible, info, Room containers, etc.)
    for element in elements:
        if is_3d_eligible(element):
            exporter.add_element(element)
    
    # Export to file
    return exporter.export(filename)
