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
    matrix_to_trs,
)
from floor_planner.elements.element import Element
from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.geometry_3d import is_3d_eligible
from floor_planner.elements.registry import get_element_type_from_instance
from floor_planner.texture_manager import TextureManager
from floor_planner.face_textures import BOX_FACES, FaceTextures, ResolvedFace, resolve_face, uv_repeats
from floor_planner.elements.foundation.basic import WallND
from floor_planner.wall_openings import find_embedded_openings, generate_wall_with_openings
from floor_planner.utils import WarnMsg


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
        
        # Create textures subdirectory
        self.textures_dir = self.output_dir / 'textures'
        self.textures_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize texture manager (procedural materials and texture lookup)
        self.texture_manager = TextureManager()
        
        self.buffer_builder = BufferBuilder()
        self.nodes: List[Dict[str, Any]] = []
        # Indices of nodes that should appear as scene roots.
        # Child nodes (e.g. animation children) are NOT added here.
        self.root_node_indices: List[int] = []
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
        self.material_cache: Dict[str, int] = {}  # "model_dir/material_name" -> material index
        # Procedural materials: (element_type, ResolvedFace.material_key, element blend) -> material index
        self.procedural_material_cache: Dict[tuple, int] = {}
        self._procedural_material_counts: Dict[str, int] = {}  # element_type -> materials created
        self._procedural_mtl_cache: Dict[str, tuple] = {}  # element_type -> (props, mtl_dir, mtl_path)
        
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
            WarnMsg(f"Failed to parse MTL file {mtl_path}: {e}")
        
        return materials
    
    def _copy_texture(self, texture_path: Path, model_dir: Path) -> Optional[int]:
        """
        Copy texture file to export directory and create glTF image entry.
        
        Args:
            texture_path: Relative path to texture (from MTL file)
            model_dir: Directory containing the model files (and the MTL file)
        
        Returns:
            Image index if successful, None if failed
        """
        # Search next to the MTL file first, then the common texture folder
        source_path = self.texture_manager.find_texture(texture_path, model_dir)
        if source_path is None:
            WarnMsg(f"Texture file not found: {texture_path} (searched {model_dir} and "
                    f"{self.texture_manager.textures_dir})")
            return None
        
        # Check cache
        cache_key = str(source_path)
        if cache_key in self.texture_paths:
            return self.texture_paths[cache_key]
        
        try:
            # Copy texture to textures/ subdirectory
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
            WarnMsg(f"Failed to copy texture {source_path}: {e}")
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
        # Check cache — scoped by model directory to avoid name collisions across models
        cache_key = f"{model_dir.name}/{material_name}"
        if cache_key in self.material_cache:
            return self.material_cache[cache_key]
        
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
        
        # Handle transparency from MTL 'd' value (d=1.0 = opaque, d=0.0 = fully transparent)
        if 'transparency' in mtl_properties:
            alpha = float(mtl_properties['transparency'])
            if alpha < 0.99:
                material["alphaMode"] = "BLEND"
                base_color = material["pbrMetallicRoughness"].get("baseColorFactor", [1.0, 1.0, 1.0, 1.0])
                base_color[3] = alpha
                material["pbrMetallicRoughness"]["baseColorFactor"] = base_color

        # Add to materials list
        material_index = len(self.materials)
        self.materials.append(material)
        
        # Cache (scoped key)
        self.material_cache[cache_key] = material_index
        
        return material_index
    
    def _parse_obj_by_materials(self, obj_path: Path):
        """
        Parse OBJ file grouped by material, expanding vertices for unique v/vt/vn combos.

        Supports multi-material OBJ files with multiple `usemtl` groups. Each material
        group gets its own set of expanded vertex arrays so each group can reference its
        own (position, UV, normal) tuples independently.

        Args:
            obj_path: Path to OBJ file

        Returns:
            List of (material_name, vertices, normals, uvs, faces) tuples, one per
            material group.  material_name may be None for faces before the first
            `usemtl`.  Returns None on parse failure.
        """
        try:
            v_list: list = []   # Global vertex positions
            vt_list: list = []  # Global texture coordinates
            vn_list: list = []  # Global vertex normals

            # per-material storage keyed by material name
            current_material: Optional[str] = None
            material_groups: Dict[Optional[str], dict] = {}
            material_order: list = []

            def _get_group(name: Optional[str]) -> dict:
                if name not in material_groups:
                    material_groups[name] = {
                        'vertex_map': {},
                        'vertices': [],
                        'normals': [],
                        'uvs': [],
                        'faces': [],
                    }
                    material_order.append(name)
                return material_groups[name]

            def _add_face_verts(group: dict, parts: list) -> list:
                """Expand one face definition into per-group vertex indices."""
                face_indices = []
                for part in parts:
                    segs = part.split('/')
                    v_idx = int(segs[0]) - 1
                    vt_idx = int(segs[1]) - 1 if len(segs) > 1 and segs[1] else -1
                    vn_idx = int(segs[2]) - 1 if len(segs) > 2 and segs[2] else -1

                    key = (v_idx, vt_idx, vn_idx)
                    if key not in group['vertex_map']:
                        new_idx = len(group['vertices'])
                        group['vertex_map'][key] = new_idx
                        group['vertices'].append(v_list[v_idx])
                        group['uvs'].append(vt_list[vt_idx] if 0 <= vt_idx < len(vt_list) else [0.0, 0.0])
                        group['normals'].append(vn_list[vn_idx] if 0 <= vn_idx < len(vn_list) else [0.0, 1.0, 0.0])

                    face_indices.append(group['vertex_map'][key])
                return face_indices

            with open(obj_path, 'r') as fh:
                for raw_line in fh:
                    line = raw_line.strip()
                    if line.startswith('v '):
                        p = line.split()
                        v_list.append([float(p[1]), float(p[2]), float(p[3])])
                    elif line.startswith('vt '):
                        p = line.split()
                        vt_list.append([float(p[1]), float(p[2]) if len(p) > 2 else 0.0])
                    elif line.startswith('vn '):
                        p = line.split()
                        vn_list.append([float(p[1]), float(p[2]), float(p[3])])
                    elif line.startswith('usemtl '):
                        current_material = line.split(None, 1)[1].strip()
                    elif line.startswith('f '):
                        parts = line.split()[1:]
                        grp = _get_group(current_material)
                        fi = _add_face_verts(grp, parts)
                        # Triangulate
                        if len(fi) == 3:
                            grp['faces'].append(fi)
                        elif len(fi) == 4:
                            grp['faces'].append([fi[0], fi[1], fi[2]])
                            grp['faces'].append([fi[0], fi[2], fi[3]])
                        elif len(fi) > 4:
                            for i in range(1, len(fi) - 1):
                                grp['faces'].append([fi[0], fi[i], fi[i + 1]])

            result = []
            for mat_name in material_order:
                grp = material_groups[mat_name]
                if not grp['vertices']:
                    continue
                vertices = np.array(grp['vertices'], dtype=np.float32)
                normals  = np.array(grp['normals'],  dtype=np.float32) if grp['normals'] else None
                uvs      = np.array(grp['uvs'],      dtype=np.float32) if grp['uvs']     else None
                faces    = np.array(grp['faces'],    dtype=np.uint32)
                result.append((mat_name, vertices, normals, uvs, faces))

            return result if result else None

        except Exception as e:
            WarnMsg(f"Failed to parse multi-material OBJ from {obj_path}: {e}")
            import traceback
            traceback.print_exc()
            return None
    
    def _load_obj_as_mesh(self, obj_path: Path) -> Optional[int]:
        """
        Load OBJ file and convert to glTF mesh.

        Supports multi-material OBJ files: creates one glTF primitive per material
        group so each part can use a different texture/material.

        Args:
            obj_path: Path to OBJ file

        Returns:
            Mesh index if successful, None if failed
        """
        cache_key = str(obj_path)
        if cache_key in self.mesh_cache:
            return self.mesh_cache[cache_key]

        try:
            model_dir = obj_path.parent
            mtl_path = model_dir / obj_path.with_suffix('.mtl').name
            mtl_materials: Dict[str, Any] = {}
            if mtl_path.exists():
                mtl_materials = self._parse_mtl_file(mtl_path)

            # Parse OBJ grouped by material (handles both single- and multi-material files)
            material_groups = self._parse_obj_by_materials(obj_path)
            if not material_groups:
                WarnMsg(f"Failed to parse OBJ file {obj_path}")
                return None

            primitives = []
            for mat_name, vertices, normals, uvs, faces in material_groups:
                position_accessor = self.buffer_builder.add_data(vertices, target=34962)
                indices_accessor  = self.buffer_builder.add_data(faces.flatten(), target=34963)

                primitive: Dict[str, Any] = {
                    "attributes": {"POSITION": position_accessor},
                    "indices": indices_accessor,
                    "mode": 4,  # TRIANGLES
                }

                if normals is not None:
                    primitive["attributes"]["NORMAL"] = self.buffer_builder.add_data(normals, target=34962)

                if uvs is not None:
                    primitive["attributes"]["TEXCOORD_0"] = self.buffer_builder.add_data(uvs, target=34962)

                # Assign material: prefer exact name match, then fallback to best available
                if mat_name and mat_name in mtl_materials:
                    mat_idx = self._create_gltf_material(mat_name, mtl_materials[mat_name], model_dir)
                    primitive["material"] = mat_idx
                elif mtl_materials:
                    best = self._select_best_mtl_material(mtl_materials)
                    if best:
                        mat_idx = self._create_gltf_material(best[0], best[1], model_dir)
                        primitive["material"] = mat_idx

                primitives.append(primitive)

            gltf_mesh = {"name": obj_path.stem, "primitives": primitives}
            mesh_index = len(self.meshes)
            self.meshes.append(gltf_mesh)
            self.mesh_cache[cache_key] = mesh_index
            return mesh_index

        except Exception as e:
            WarnMsg(f"Failed to load OBJ file {obj_path}: {e}")
            return None

    # ------------------------------------------------------------------
    # .glb / glTF loader  (binary glTF 2.0, no extra dependency)
    # ------------------------------------------------------------------

    def _load_glb_as_mesh(self, glb_path: Path) -> Optional[int]:
        """
        Merge a binary glTF (.glb) file into the current export as one or more meshes.

        The source GLB's geometry, materials, and textures are appended to the
        target buffers / accessor lists with re-indexed references.  All meshes
        found in the source are merged into a single glTF mesh with one primitive
        per source primitive, so the caller gets back a single mesh index.

        Args:
            glb_path: Path to the .glb file.

        Returns:
            Mesh index on success, None on failure.
        """
        WarnMsg(f"glTF model loading may not fully work yet. For {glb_path}")

        cache_key = str(glb_path)
        if cache_key in self.mesh_cache:
            return self.mesh_cache[cache_key]

        try:
            raw = glb_path.read_bytes()

            # ---- Parse GLB container ----
            magic, version, total_length = struct.unpack_from('<III', raw, 0)
            if magic != 0x46546C67:  # 'glTF'
                WarnMsg(f"Not a valid GLB file (bad magic): {glb_path}")
                return None
            if version != 2:
                WarnMsg(f"Unsupported GLB version {version} (only v2 supported): {glb_path}")
                return None

            offset = 12
            json_data: Optional[bytes] = None
            bin_data: Optional[bytes] = None

            while offset < total_length:
                chunk_length, chunk_type = struct.unpack_from('<II', raw, offset)
                offset += 8
                chunk_bytes = raw[offset: offset + chunk_length]
                offset += chunk_length
                if chunk_type == 0x4E4F534A:   # JSON
                    json_data = chunk_bytes
                elif chunk_type == 0x004E4942:  # BIN
                    bin_data = chunk_bytes

            if json_data is None:
                WarnMsg(f"GLB has no JSON chunk: {glb_path}")
                return None

            src = json.loads(json_data.decode('utf-8'))
            bin_bytes = bin_data or b''

            # ---- Index offsets into target lists ----
            buf_view_offset  = len(self.buffer_builder.views)
            accessor_offset  = len(self.buffer_builder.accessors)
            mat_offset       = len(self.materials)
            tex_offset       = len(self.textures) if hasattr(self, 'textures') else 0
            img_offset       = len(self.images)   if hasattr(self, 'images')   else 0
            sampler_offset   = len(self.samplers) if hasattr(self, 'samplers') else 0

            # ---- Copy binary buffer, recording byte offset in target buffer ----
            bin_base = len(self.buffer_builder.data)
            self.buffer_builder.data.extend(bin_bytes)

            # ---- Re-index bufferViews ----
            for bv in src.get('bufferViews', []):
                new_bv = dict(bv)
                new_bv['buffer'] = 0                              # always buffer 0 in target
                new_bv['byteOffset'] = bv.get('byteOffset', 0) + bin_base
                self.buffer_builder.views.append(new_bv)

            # ---- Re-index accessors ----
            for acc in src.get('accessors', []):
                new_acc = dict(acc)
                if 'bufferView' in new_acc:
                    new_acc['bufferView'] += buf_view_offset
                self.buffer_builder.accessors.append(new_acc)

            # ---- Re-index images ----
            src_images = src.get('images', [])
            for img in src_images:
                new_img = dict(img)
                if 'bufferView' in new_img:
                    new_img['bufferView'] += buf_view_offset
                # base64 uri images are copied as-is
                if not hasattr(self, 'images'):
                    self.images = []
                self.images.append(new_img)

            # ---- Re-index samplers ----
            for smp in src.get('samplers', []):
                if not hasattr(self, 'samplers'):
                    self.samplers = []
                self.samplers.append(dict(smp))

            # ---- Re-index textures ----
            for tex in src.get('textures', []):
                new_tex = dict(tex)
                if 'source' in new_tex:
                    new_tex['source'] += img_offset
                if 'sampler' in new_tex:
                    new_tex['sampler'] += sampler_offset
                if not hasattr(self, 'textures'):
                    self.textures = []
                self.textures.append(new_tex)

            # ---- Re-index materials ----
            def _remap_tex_index(d: dict, key: str) -> dict:
                d = dict(d)
                if key in d:
                    d[key] = dict(d[key])
                    if 'index' in d[key]:
                        d[key]['index'] += tex_offset
                return d

            for mat in src.get('materials', []):
                new_mat: Dict[str, Any] = dict(mat)
                pbr = new_mat.get('pbrMetallicRoughness')
                if pbr:
                    pbr = _remap_tex_index(pbr, 'baseColorTexture')
                    pbr = _remap_tex_index(pbr, 'metallicRoughnessTexture')
                    new_mat['pbrMetallicRoughness'] = pbr
                new_mat = _remap_tex_index(new_mat, 'normalTexture')
                new_mat = _remap_tex_index(new_mat, 'occlusionTexture')
                new_mat = _remap_tex_index(new_mat, 'emissiveTexture')
                self.materials.append(new_mat)

            # ---- Collect all primitives from all source meshes ----
            primitives: List[Dict[str, Any]] = []
            for src_mesh in src.get('meshes', []):
                for prim in src_mesh.get('primitives', []):
                    new_prim: Dict[str, Any] = {}
                    # Re-index attribute accessors
                    new_attrs = {}
                    for attr_name, acc_idx in prim.get('attributes', {}).items():
                        new_attrs[attr_name] = acc_idx + accessor_offset
                    new_prim['attributes'] = new_attrs
                    if 'indices' in prim:
                        new_prim['indices'] = prim['indices'] + accessor_offset
                    if 'material' in prim:
                        new_prim['material'] = prim['material'] + mat_offset
                    new_prim['mode'] = prim.get('mode', 4)  # TRIANGLES default
                    primitives.append(new_prim)

            if not primitives:
                WarnMsg(f"GLB has no mesh primitives: {glb_path}")
                return None

            gltf_mesh = {"name": glb_path.stem, "primitives": primitives}
            mesh_index = len(self.meshes)
            self.meshes.append(gltf_mesh)
            self.mesh_cache[cache_key] = mesh_index
            return mesh_index

        except Exception as e:
            WarnMsg(f"Failed to load GLB file {glb_path}: {e}")
            return None

    # ------------------------------------------------------------------
    # .3ds loader (built-in, no extra dependency)
    # ------------------------------------------------------------------

    def _load_3ds_as_mesh(self, file_path: Path) -> Optional[int]:
        """
        Load a .3ds file and convert to a glTF mesh.

        Implements a minimal but complete reader for the 3DS chunk format:
        vertices, faces, per-vertex UVs, flat normals (computed), and
        per-material face groups.  Materials map to the same
        ``_create_gltf_material`` pipeline as the OBJ loader.

        Args:
            file_path: Path to the .3ds file.

        Returns:
            Mesh index on success, None on failure.
        """
        cache_key = str(file_path)
        if cache_key in self.mesh_cache:
            return self.mesh_cache[cache_key]

        try:
            raw = file_path.read_bytes()

            # ---- chunk helpers (closures over raw) ----
            def read_header(off: int):
                cid, clen = struct.unpack_from('<HI', raw, off)
                return cid, clen, off + 6

            def read_cstr(off: int):
                end = raw.index(b'\x00', off)
                return raw[off:end].decode('latin-1', errors='replace'), end + 1

            # ---- collected data ----
            materials: Dict[str, Dict[str, Any]] = {}
            meshes_raw: list = []          # list of dicts

            # ---- material parsers ----
            def parse_color(off: int, end: int):
                while off + 6 <= end:
                    cid, clen, ds = read_header(off)
                    if cid in (0x0011, 0x0012):        # COLOR_24 / LIN_COLOR_24
                        r, g, b = struct.unpack_from('BBB', raw, ds)
                        return [r / 255.0, g / 255.0, b / 255.0]
                    if cid in (0x0010, 0x0013):        # COLOR_F / LIN_COLOR_F
                        r, g, b = struct.unpack_from('<fff', raw, ds)
                        return [float(r), float(g), float(b)]
                    off += clen
                return [0.8, 0.8, 0.8]

            def parse_texmap(off: int, end: int):
                while off + 6 <= end:
                    cid, clen, ds = read_header(off)
                    if cid == 0xA300:                   # MAT_MAPNAME
                        name, _ = read_cstr(ds)
                        return name
                    off += clen
                return None

            def parse_material(off: int, end: int):
                mat: Dict[str, Any] = {}
                name: Optional[str] = None
                while off + 6 <= end:
                    cid, clen, ds = read_header(off)
                    ce = off + clen
                    if cid == 0xA000:   mat_name, _ = read_cstr(ds); name = mat_name  # noqa: E702
                    elif cid == 0xA020: mat['diffuse'] = parse_color(ds, ce)           # MAT_DIFFUSE
                    elif cid == 0xA200:                                                # MAT_TEXMAP
                        tex = parse_texmap(ds, ce)
                        if tex:
                            mat['diffuse_texture'] = tex
                    off = ce
                if name is not None:
                    materials[name] = mat

            # ---- trimesh / face-group parsers ----
            def parse_mat_groups(off: int, end: int, mesh: dict):
                while off + 6 <= end:
                    cid, clen, ds = read_header(off)
                    if cid == 0x4130:                   # TRI_MATERIAL
                        mat_name, no = read_cstr(ds)
                        count = struct.unpack_from('<H', raw, no)[0]
                        fidxs = list(struct.unpack_from(f'<{count}H', raw, no + 2))
                        mesh['mat_groups'].append((mat_name, fidxs))
                    off += clen

            def parse_trimesh(off: int, end: int):
                mesh: Dict[str, Any] = {
                    'vertices': None, 'uvs': None, 'faces': None, 'mat_groups': []
                }
                while off + 6 <= end:
                    cid, clen, ds = read_header(off)
                    ce = off + clen

                    if cid == 0x4110:   # TRI_VERTEXL
                        count = struct.unpack_from('<H', raw, ds)[0]
                        vals = struct.unpack_from(f'<{count * 3}f', raw, ds + 2)
                        mesh['vertices'] = np.array(vals, dtype=np.float32).reshape(-1, 3)

                    elif cid == 0x4140: # TRI_MAPPINGCOORS
                        count = struct.unpack_from('<H', raw, ds)[0]
                        vals = struct.unpack_from(f'<{count * 2}f', raw, ds + 2)
                        mesh['uvs'] = np.array(vals, dtype=np.float32).reshape(-1, 2)

                    elif cid == 0x4120: # TRI_FACEL1
                        count = struct.unpack_from('<H', raw, ds)[0]
                        vals = struct.unpack_from(f'<{count * 4}H', raw, ds + 2)
                        # 4 shorts per face: a, b, c, flags — keep only first 3
                        mesh['faces'] = np.array(vals, dtype=np.uint32).reshape(-1, 4)[:, :3]
                        # TRI_MATERIAL sub-chunks follow face data
                        parse_mat_groups(ds + 2 + count * 8, ce, mesh)

                    off = ce

                if mesh['vertices'] is not None and mesh['faces'] is not None:
                    meshes_raw.append(mesh)

            def walk_chunks(off: int, end: int):
                while off + 6 <= end:
                    cid, clen, ds = read_header(off)
                    ce = off + clen
                    if   cid == 0x3D3D: walk_chunks(ds, ce)    # EDIT3DS
                    elif cid == 0xAFFF: parse_material(ds, ce) # EDIT_MATERIAL
                    elif cid == 0x4000:                         # EDIT_OBJECT
                        _, ne = read_cstr(ds)
                        walk_chunks(ne, ce)
                    elif cid == 0x4100: parse_trimesh(ds, ce)  # OBJ_TRIMESH
                    off = ce

            # Validate MAIN3DS header
            if len(raw) < 6:
                return None
            root_id, root_len, root_ds = read_header(0)
            if root_id != 0x4D4D:
                WarnMsg(f"Not a valid .3ds file: {file_path}")
                return None
            walk_chunks(root_ds, root_len)

            if not meshes_raw:
                WarnMsg(f"No mesh data in .3ds file {file_path}")
                return None

            model_dir = file_path.parent
            all_primitives: list = []

            for mesh in meshes_raw:
                verts: np.ndarray = mesh['vertices']
                faces: np.ndarray = mesh['faces']
                uvs: Optional[np.ndarray] = mesh['uvs']

                # Compute flat (per-face) normals via cross-product
                v0, v1, v2 = verts[faces[:, 0]], verts[faces[:, 1]], verts[faces[:, 2]]
                fn = np.cross(v1 - v0, v2 - v0).astype(np.float32)
                nlen = np.linalg.norm(fn, axis=1, keepdims=True)
                fn /= np.where(nlen == 0, 1.0, nlen)

                def _build_prim(face_sel: np.ndarray, mat_name: Optional[str]) -> Optional[dict]:
                    if len(face_sel) == 0:
                        return None
                    sel_faces = faces[face_sel]
                    positions = verts[sel_faces.reshape(-1)]           # (Nf*3, 3)
                    normals_e = np.repeat(fn[face_sel], 3, axis=0)    # (Nf*3, 3)
                    seq = np.arange(len(positions), dtype=np.uint32).reshape(-1, 3)

                    pos_acc = self.buffer_builder.add_data(positions, target=34962)
                    idx_acc = self.buffer_builder.add_data(seq.flatten(), target=34963)
                    prim: Dict[str, Any] = {
                        "attributes": {"POSITION": pos_acc,
                                       "NORMAL": self.buffer_builder.add_data(normals_e, target=34962)},
                        "indices": idx_acc,
                        "mode": 4,
                    }
                    if uvs is not None and len(uvs) == len(verts):
                        uv_e = uvs[sel_faces.reshape(-1)]
                        prim["attributes"]["TEXCOORD_0"] = self.buffer_builder.add_data(uv_e, target=34962)

                    if mat_name and mat_name in materials:
                        props = dict(materials[mat_name])
                        props.setdefault('diffuse', [0.8, 0.8, 0.8])
                        prim["material"] = self._create_gltf_material(mat_name, props, model_dir)
                    elif materials:
                        best = self._select_best_mtl_material(materials)
                        if best:
                            props = dict(best[1])
                            props.setdefault('diffuse', [0.8, 0.8, 0.8])
                            prim["material"] = self._create_gltf_material(best[0], props, model_dir)
                    return prim

                mat_groups = mesh['mat_groups']
                if mat_groups:
                    assigned: set = set()
                    for mat_name, fidxs in mat_groups:
                        fidxs = [i for i in fidxs if i < len(faces)]
                        assigned.update(fidxs)
                        p = _build_prim(np.array(fidxs, dtype=np.intp), mat_name)
                        if p:
                            all_primitives.append(p)
                    unassigned = list(set(range(len(faces))) - assigned)
                    if unassigned:
                        p = _build_prim(np.array(unassigned, dtype=np.intp), None)
                        if p:
                            all_primitives.append(p)
                else:
                    p = _build_prim(np.arange(len(faces), dtype=np.intp), None)
                    if p:
                        all_primitives.append(p)

            if not all_primitives:
                return None

            gltf_mesh = {"name": file_path.stem, "primitives": all_primitives}
            mesh_index = len(self.meshes)
            self.meshes.append(gltf_mesh)
            self.mesh_cache[cache_key] = mesh_index
            return mesh_index

        except Exception as e:
            WarnMsg(f"Failed to load .3ds file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return None

    # ------------------------------------------------------------------
    # .dae (COLLADA) loader — requires pycollada
    # ------------------------------------------------------------------

    def _load_dae_as_mesh(self, file_path: Path) -> Optional[int]:
        """
        Load a COLLADA .dae file and convert to a glTF mesh.

        Uses the ``pycollada`` library (``pip install pycollada``).
        Each COLLADA geometry primitive becomes one glTF primitive.
        UV V-coordinates are flipped (COLLADA origin is bottom-left,
        glTF origin is top-left).

        Args:
            file_path: Path to the .dae file.

        Returns:
            Mesh index on success, None on failure.
        """
        cache_key = str(file_path)
        if cache_key in self.mesh_cache:
            return self.mesh_cache[cache_key]

        try:
            try:
                import collada                                      # pycollada
                import collada.triangleset
            except ImportError:
                print(
                    f"Warning: pycollada is not installed — cannot load {file_path}. "
                    "Install it with: pip install pycollada"
                )
                return None

            model_dir = file_path.parent
            c = collada.Collada(
                str(file_path),
                ignore=[collada.DaeUnsupportedError, collada.DaeBrokenRefError],
            )

            all_primitives: list = []

            for bound_geom in c.scene.objects('geometry'):
                for prim in bound_geom.primitives():
                    # Only handle triangle sets; skip lines, polylist if not triangulated
                    if not hasattr(prim, 'vertex_index') or prim.vertex_index is None:
                        continue

                    v_idx = prim.vertex_index.reshape(-1)           # (Nt*3,)
                    positions = np.array(prim.vertex[v_idx], dtype=np.float32)

                    normals_exp: Optional[np.ndarray] = None
                    if (prim.normal is not None
                            and hasattr(prim, 'normal_index')
                            and prim.normal_index is not None):
                        n_idx = prim.normal_index.reshape(-1)
                        normals_exp = np.array(prim.normal[n_idx], dtype=np.float32)

                    uvs_exp: Optional[np.ndarray] = None
                    if prim.texcoordset and prim.texcoord_indexset:
                        uv_idx = prim.texcoord_indexset[0].reshape(-1)
                        uv_data = prim.texcoordset[0][uv_idx].copy().astype(np.float32)
                        uv_data[:, 1] = 1.0 - uv_data[:, 1]        # flip V
                        uvs_exp = uv_data

                    n_verts = len(positions)
                    seq_faces = np.arange(n_verts, dtype=np.uint32).reshape(-1, 3)

                    pos_acc = self.buffer_builder.add_data(positions, target=34962)
                    idx_acc = self.buffer_builder.add_data(seq_faces.flatten(), target=34963)
                    gltf_prim: Dict[str, Any] = {
                        "attributes": {"POSITION": pos_acc},
                        "indices": idx_acc,
                        "mode": 4,
                    }
                    if normals_exp is not None:
                        gltf_prim["attributes"]["NORMAL"] = self.buffer_builder.add_data(
                            normals_exp, target=34962
                        )
                    if uvs_exp is not None:
                        gltf_prim["attributes"]["TEXCOORD_0"] = self.buffer_builder.add_data(
                            uvs_exp, target=34962
                        )

                    # Material
                    mat_props = self._dae_material_props(prim, model_dir)
                    if mat_props:
                        mat_name = mat_props.get('name', 'dae_mat')
                        gltf_prim["material"] = self._create_gltf_material(
                            mat_name, mat_props, model_dir
                        )

                    all_primitives.append(gltf_prim)

            if not all_primitives:
                WarnMsg(f"No geometry found in DAE file {file_path}")
                return None

            gltf_mesh = {"name": file_path.stem, "primitives": all_primitives}
            mesh_index = len(self.meshes)
            self.meshes.append(gltf_mesh)
            self.mesh_cache[cache_key] = mesh_index
            return mesh_index

        except Exception as e:
            WarnMsg(f"Failed to load DAE file {file_path}: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _dae_material_props(
        self, prim, model_dir: Path
    ) -> Optional[Dict[str, Any]]:
        """
        Extract material properties from a pycollada bound primitive into the
        same dict format used by ``_create_gltf_material``.

        Returns None when no material is bound or extraction fails.
        """
        try:
            mat = getattr(prim, 'material', None)
            if mat is None:
                return None
            effect = getattr(mat, 'effect', None)
            if effect is None:
                return None

            props: Dict[str, Any] = {
                'name': getattr(mat, 'id', None) or getattr(mat, 'name', 'dae_mat') or 'dae_mat'
            }

            diffuse = getattr(effect, 'diffuse', None)
            if isinstance(diffuse, tuple):
                props['diffuse'] = list(diffuse[:3])
            elif diffuse is not None:
                # Texture map — try to extract filename
                props['diffuse'] = [1.0, 1.0, 1.0]
                try:
                    image = diffuse.sampler.surface.image
                    img_path = Path(image.path) if getattr(image, 'path', None) else None
                    if img_path and img_path.name:
                        props['diffuse_texture'] = img_path.name
                except Exception:
                    pass

            shininess = getattr(effect, 'shininess', None)
            if shininess is not None:
                props['shininess'] = float(shininess)

            transparency = getattr(effect, 'transparency', None)
            if transparency is not None:
                alpha = float(transparency)
                if alpha < 0.99:
                    props['transparency'] = alpha

            return props
        except Exception:
            return None

    def add_element(self, element: Element) -> Optional[int]:
        """
        Add floor plan element to scene.
        
        Args:
            element: Floor plan element to export
        
        Returns:
            Node index if added, None if element cannot be exported
        """
        # Check if this is a list, iterate over sub-elements
        if element.isList():
            for sub in element.getList():
                self.add_element(sub)
            return None

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
                                         indices: list[tuple[int, int, int]],
                                         resolved_faces: Optional[Dict[str, ResolvedFace]] = None
                                         ) -> tuple[list[tuple[float, float, float]], 
                                                    list[tuple[int, int, int]], 
                                                    list[tuple[float, float]]]:
        """
        Generate box geometry with proper per-face UV mapping.
        
        Expands 8 unique vertices to 24 vertices (4 per face × 6 faces) so each face
        can have independent texture coordinates. Remaps triangle indices accordingly.
        The UV range of each face follows its resolved scale: stretched /
        ``scale_relative: r`` → 0…r, ``scale_meters: m`` → 0…size/m.
        
        Args:
            element: The floor plan element
            vertices: List of 8 unique vertex positions
            indices: List of triangle indices referencing the 8 vertices
            resolved_faces: Resolved look per box face (None = all faces stretched)
            
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
        
        # UV range (u_max, v_max) of each face from its resolved scale and size
        face_sizes = {
            'bottom': (length, thickness),
            'top': (length, thickness),
            'front': (length, height),
            'back': (length, height),
            'right': (thickness, height),
            'left': (thickness, height),
        }
        uv_max = {}
        for face, (width, face_height) in face_sizes.items():
            if resolved_faces and face in resolved_faces:
                uv_max[face] = uv_repeats(resolved_faces[face], width, face_height)
            else:
                uv_max[face] = (1.0, 1.0)  # stretched
        
        # Build 24 expanded vertices (4 per face × 6 faces) with proper UVs
        expanded_vertices = []
        texcoords = []
        
        # Bottom face (vertices 0-3): Use original vertices 0,1,2,3
        u, v = uv_max['bottom']
        for i in [0, 1, 2, 3]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([(0.0, 0.0), (u, 0.0), (u, v), (0.0, v)])
        
        # Top face (vertices 4-7): Use original vertices 4,5,6,7
        u, v = uv_max['top']
        for i in [4, 5, 6, 7]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([(0.0, 0.0), (u, 0.0), (u, v), (0.0, v)])
        
        # Front face: Use original vertices 0,1,5,4
        u, v = uv_max['front']
        for i in [0, 1, 5, 4]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([(0.0, 0.0), (u, 0.0), (u, v), (0.0, v)])
        
        # Back face: Use original vertices 2,3,7,6
        u, v = uv_max['back']
        for i in [2, 3, 7, 6]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([(u, 0.0), (0.0, 0.0), (0.0, v), (u, v)])
        
        # Right face: Use original vertices 1,2,6,5
        u, v = uv_max['right']
        for i in [1, 2, 6, 5]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([(0.0, 0.0), (u, 0.0), (u, v), (0.0, v)])
        
        # Left face: Use original vertices 3,0,4,7
        u, v = uv_max['left']
        for i in [3, 0, 4, 7]:
            expanded_vertices.append(vertices[i])
        texcoords.extend([(u, 0.0), (0.0, 0.0), (0.0, v), (u, v)])
        
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
    
    def _generate_slope_uvs_expanded(
        self,
        element,
        vertices: list[tuple[float, float, float]],
        indices: list[tuple[int, int, int]],
    ) -> tuple[list[tuple[float, float, float]], list[tuple[int, int, int]], list[tuple[float, float]]]:
        """
        Generate per-face UV coordinates for arbitrary slope/roof geometry.

        Each triangle is expanded into 3 independent vertices so that each face
        can have its own UV space.  UVs are computed by projecting each vertex
        onto the face's local 2D plane (U along the first edge, V perpendicular
        in that plane), then divided by ``texture_scale`` for tiling.

        Args:
            element:   Source element (read ``texture_scale`` from it).
            vertices:  Flat vertex list referenced by ``indices``.
            indices:   List of (i0, i1, i2) triangle index triples.

        Returns:
            (expanded_vertices, remapped_indices, texcoords)
        """
        texture_scale = getattr(element, 'texture_scale', None)
        if not texture_scale or texture_scale <= 0:
            texture_scale = 1.0

        expanded_vertices: list[tuple[float, float, float]] = []
        remapped_indices: list[tuple[int, int, int]] = []
        texcoords: list[tuple[float, float]] = []

        for i0, i1, i2 in indices:
            v0 = np.array(vertices[i0], dtype=np.float64)
            v1 = np.array(vertices[i1], dtype=np.float64)
            v2 = np.array(vertices[i2], dtype=np.float64)

            # Local U axis: along first edge
            edge01 = v1 - v0
            edge01_len = np.linalg.norm(edge01)
            u_axis = edge01 / edge01_len if edge01_len > 1e-10 else np.array([1.0, 0.0, 0.0])

            # Face normal
            edge02 = v2 - v0
            face_normal = np.cross(edge01, edge02)
            fn_len = np.linalg.norm(face_normal)
            face_normal = face_normal / fn_len if fn_len > 1e-10 else np.array([0.0, 1.0, 0.0])

            # V axis: perpendicular to u_axis in the face plane
            v_axis = np.cross(face_normal, u_axis)

            # Project each vertex onto the local 2D frame
            uv0 = (0.0, 0.0)
            uv1 = (float(np.dot(v1 - v0, u_axis)) / texture_scale,
                   float(np.dot(v1 - v0, v_axis)) / texture_scale)
            uv2 = (float(np.dot(v2 - v0, u_axis)) / texture_scale,
                   float(np.dot(v2 - v0, v_axis)) / texture_scale)

            base = len(expanded_vertices)
            expanded_vertices.extend([tuple(v0), tuple(v1), tuple(v2)])
            remapped_indices.append((base, base + 1, base + 2))
            texcoords.extend([uv0, uv1, uv2])

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
        face_groups: dict[str, list[int]],
        resolved_faces: Optional[Dict[str, ResolvedFace]] = None
    ) -> list[tuple[float, float]]:
        """
        Generate proper UV coordinates for walls with openings.
        
        Each face type gets appropriate UV mapping based on its orientation.
        UVs are assigned per-triangle to handle shared vertices correctly.

        Stretched / ``scale_relative: r``: UV = local position / wall size
        (length, height, thickness), multiplied by ``r`` and clamped to 0…r.
        ``scale_meters: m``: UV = local position in metres / m (continuous tiling).
        The reveals (``inside_*``) use the same wall-based coordinates.
        
        Args:
            wall: Wall element
            vertices: List of vertex positions
            indices: List of triangle indices
            face_groups: Dict mapping face names to triangle indices
            resolved_faces: Resolved look per face (None = all faces stretched)
            
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
        # Z-axis: along wall thickness (perpendicular to wall)
        z_axis = np.array([-np.sin(angle_rad), 0, np.cos(angle_rad)])
        
        # Wall anchor in 3D
        anchor_3d = np.array([wall_anchor[0], 0, wall_anchor[1]])

        # Local axes used for (u, v) per face, and the wall size along each axis
        face_axes = {
            'front': ('x', 'y'), 'back': ('x', 'y'),
            'top': ('x', 'z'), 'bottom': ('x', 'z'),
            'left': ('z', 'y'), 'right': ('z', 'y'),
            'inside_top': ('x', 'z'), 'inside_bottom': ('x', 'z'),
            'inside_left': ('z', 'y'), 'inside_right': ('z', 'y'),
        }
        axis_size = {'x': wall_length, 'y': wall_height, 'z': wall_thickness}
        
        def assign_uvs_for_face(tri_idx: int, face_type: str):
            """Assign UVs to all vertices of a triangle based on face type."""
            u_axis, v_axis = face_axes[face_type]
            resolved = resolved_faces.get(face_type) if resolved_faces else None
            if resolved is not None and resolved.scale_mode == 'meters':
                mode, scale = 'meters', resolved.scale_value
            else:
                mode, scale = 'relative', (resolved.scale_value if resolved is not None else 1.0)
            
            for v_idx in indices[tri_idx]:
                vx, vy, vz = vertices[v_idx]
                relative = np.array([vx, vy, vz]) - anchor_3d
                local = {
                    'x': np.dot(relative, x_axis),  # Along wall length (0 to wall_length)
                    'y': vy - wall_v_anchor,        # Height from wall base (0 to wall_height)
                    'z': np.dot(relative, z_axis),  # Along wall thickness (0 to wall_thickness)
                }
                if mode == 'meters':
                    u = local[u_axis] / scale
                    v = local[v_axis] / scale
                else:
                    # Normalized to the wall size, clamped to 0…r
                    u = max(0.0, min(1.0, local[u_axis] / axis_size[u_axis])) * scale
                    v = max(0.0, min(1.0, local[v_axis] / axis_size[v_axis])) * scale
                texcoords[v_idx] = (u, v)
        
        # Process face groups (outer faces first, then the reveals of the openings)
        # Skip 'sides', 'all' and 'opening_edges': aggregate groups that overlap with these
        face_priority = ['bottom', 'top', 'left', 'right', 'front', 'back',
                         'inside_bottom', 'inside_top', 'inside_left', 'inside_right']
        
        for face_type in face_priority:
            if face_type in face_groups:
                for tri_idx in face_groups[face_type]:
                    assign_uvs_for_face(tri_idx, face_type)
        
        return texcoords
    
    def _generate_local_geometry(self, element: Element):
        """
        Generate element geometry in local space for animated procedural elements.

        Temporarily sets anchor_point=(0,0), orientation_angle=0 and v_anchor=0
        so the returned vertices are centred at the origin.  The placement matrix
        in the parent glTF node handles the world-space position.

        Args:
            element: Element with generate_vertices_and_indices()

        Returns:
            (vertices, indices, face_groups) in local space
        """
        orig_anchor        = element.anchor_point
        orig_angle         = element.orientation_angle
        orig_v_anchor      = element.v_anchor
        try:
            element.anchor_point      = (0.0, 0.0)
            element.orientation_angle = 0
            element.v_anchor          = 0.0
            return element.generate_vertices_and_indices()
        finally:
            element.anchor_point      = orig_anchor
            element.orientation_angle = orig_angle
            element.v_anchor          = orig_v_anchor

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
            # For animated procedural elements generate geometry in local space
            # (anchor_point = origin, orientation_angle = 0, v_anchor = 0) so
            # the placement matrix can position/rotate the mesh at runtime.
            if getattr(element, 'animation', None) is not None:
                vertices, indices, face_groups = self._generate_local_geometry(element)
            else:
                # Standard geometry for non-wall elements
                vertices, indices, face_groups = element.generate_vertices_and_indices()
        
        # Check if this is simple box geometry (8 vertices, 12 triangles with the
        # box face groups) or complex mesh.  A vertex count alone is not enough:
        # e.g. a single-slope roof shell also has exactly 8 vertices.
        is_simple_box = (len(vertices) == 8 and len(indices) == 12
                         and 'top' in face_groups and 'bottom' in face_groups)
        
        # Per-face looks (textures structure → class default → MTL) for boxes and
        # walls with openings; other geometry uses one material for the whole element
        resolved_faces = None
        if (is_simple_box or has_openings) and hasattr(element, 'get_face_textures'):
            face_names = [name for name in BOX_FACES if name in face_groups]
            face_names += [name for name in getattr(element, '_extra_faces', ()) if name in face_groups]
            resolved_faces = self._resolve_element_faces(element, face_names + ['default'])
        
        if is_simple_box:
            # Generate proper per-face UV mapping (expands 8 vertices to 24)
            expanded_vertices, remapped_indices, texcoords = self._generate_box_geometry_with_uvs(
                element, vertices, indices, resolved_faces
            )
        else:
            # Complex geometry
            if has_openings and isinstance(element, WallND):
                # Walls with openings: keep original vertex layout, generate wall UVs
                expanded_vertices = vertices
                remapped_indices = indices
                texcoords = self._generate_wall_opening_uvs(
                    element, vertices, indices, face_groups, resolved_faces
                )
            else:
                # Roofs and other slope geometry: per-face UV expansion
                # (respects texture_scale and maps correctly onto angled surfaces)
                expanded_vertices, remapped_indices, texcoords = self._generate_slope_uvs_expanded(
                    element, vertices, indices
                )
        
        # Convert to numpy arrays
        vertices_array = np.array(expanded_vertices, dtype=np.float32)
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
        
        # Material per triangle: per-face looks, or one material for the whole element
        if resolved_faces is not None:
            triangle_materials = [None] * len(remapped_indices)
            for name, resolved in resolved_faces.items():
                if name == 'default':
                    continue
                material_index = self._get_procedural_material(element, resolved)
                for tri_idx in face_groups[name]:
                    triangle_materials[tri_idx] = material_index
            # Triangles outside the named faces use the 'default' look
            default_material = None
            for tri_idx, material_index in enumerate(triangle_materials):
                if material_index is None:
                    if default_material is None:
                        default_material = self._get_procedural_material(element, resolved_faces['default'])
                    triangle_materials[tri_idx] = default_material
        else:
            triangle_materials = [self._get_default_material(element)] * len(remapped_indices)
        
        # Group triangles by material (in triangle order), one primitive per group
        material_groups: Dict[int, list] = {}
        for tri, material_index in zip(remapped_indices, triangle_materials):
            material_groups.setdefault(material_index, []).append(tri)
        
        # Create face indices accessors (one per material group)
        group_index_accessors = []
        for material_index, group_triangles in material_groups.items():
            group_indices_array = np.array(group_triangles, dtype=np.uint32).flatten()
            accessor = self.buffer_builder.add_data(
                group_indices_array,
                target=34963  # ELEMENT_ARRAY_BUFFER
            )
            group_index_accessors.append((material_index, accessor))
        
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
        
        # Create primitives (shared vertex attributes, one index list per material)
        primitives = []
        for material_index, indices_accessor in group_index_accessors:
            primitive = {
                "attributes": {
                    "POSITION": position_accessor,
                    "NORMAL": normal_accessor,
                    "TEXCOORD_0": texcoord_accessor
                },
                "indices": indices_accessor,
                "mode": 4  # TRIANGLES
            }
            if material_index is not None:
                primitive["material"] = material_index
            primitives.append(primitive)
        
        # Create mesh
        element_type = element.__class__.__name__
        gltf_mesh = {
            "name": f"{element_type}_{element.get_id()}",
            "primitives": primitives
        }
        
        mesh_index = len(self.meshes)
        self.meshes.append(gltf_mesh)

        # ── Animated procedural element ─────────────────────────────────────
        # If the element carries animation metadata (e.g. Door with door-swing),
        # emit a two-node hierarchy:
        #   Parent – Placement matrix only (static world position)
        #   Child  – TRS decomposed from (SecAnchor × SecNorm) + mesh + extras.animation
        #
        # The geometry was generated in local space (anchor=(0,0), angle=0,
        # v_anchor=0) so the placement matrix can move it to world position.
        anim_data = getattr(element, 'animation', None)

        if anim_data is not None:
            from floor_planner.transform import (
                build_normalization_matrix, create_placement_matrix,
                compose_transforms, matrix_to_trs
            )

            # Placement matrix  (anchor_point, orientation_angle, v_anchor)
            placement_matrix = create_placement_matrix(
                anchor_point=element.anchor_point,
                orientation_angle=element.orientation_angle,
                v_anchor=element.v_anchor,
            )

            # Secondary normalization (open-angle transform)
            sec_norm_data = getattr(element, 'secondary_normalization', None)
            sec_norm_matrix = (
                build_normalization_matrix(sec_norm_data)
                if sec_norm_data is not None
                else np.eye(4)
            )

            # Secondary anchor offset
            sec_anchor_data = getattr(element, 'secondary_anchor_offset', None)
            sec_anchor_matrix = np.eye(4)
            if sec_anchor_data is not None:
                sec_anchor_matrix[0, 3] = -sec_anchor_data[0]
                sec_anchor_matrix[1, 3] = -sec_anchor_data[1]
                sec_anchor_matrix[2, 3] = -sec_anchor_data[2]

            child_matrix = sec_anchor_matrix @ sec_norm_matrix
            translation, rotation_quat, scale = matrix_to_trs(child_matrix)

            child_idx = len(self.nodes) + 1  # will be appended right after parent

            parent_node = {
                "name":     f"{element_type}_{element.get_id()}_placement",
                "matrix":   matrix_to_json(placement_matrix),
                "children": [child_idx],
                "extras":   {
                    "element_type": element_type,
                    "procedural":   True,
                },
            }
            child_node = {
                "name":        f"{element_type}_{element.get_id()}_anim",
                "translation": translation.tolist(),
                "rotation":    rotation_quat.tolist(),
                "scale":       scale.tolist(),
                "mesh":        mesh_index,
                "extras":      {"animation": anim_data},
            }

            parent_idx = len(self.nodes)
            self.nodes.append(parent_node)
            self.nodes.append(child_node)
            self.root_node_indices.append(parent_idx)
            return parent_idx

        # ── Static procedural element (original behaviour) ───────────────────
        # Create node
        node = {
            "name": f"{element_type}_{element.get_id()}",
            "mesh": mesh_index,
            "extras": {
                "element_type": element_type,
                "element.get_id()": element.get_id(),
                "procedural": True
            }
        }
        
        node_index = len(self.nodes)
        self.nodes.append(node)
        self.root_node_indices.append(node_index)
        
        return node_index
    
    def _read_procedural_mtl(self, element_type: str) -> tuple[dict, Path, Optional[Path]]:
        """
        Read the MTL file of a procedural element type (cached per type).

        Args:
            element_type: Registry key of the element

        Returns:
            (properties of the best material in models/procedural/<type>/<type>.mtl,
             folder where its texture references are searched first, path of the MTL
             or None if the type has no MTL)
        """
        if element_type not in self._procedural_mtl_cache:
            mtl_props: Dict[str, Any] = {}
            mtl_dir = self.texture_manager.textures_dir
            mtl_path = self.texture_manager.get_procedural_mtl(element_type)
            if mtl_path:
                mtl_dir = mtl_path.parent
                best_material = self._select_best_mtl_material(self._parse_mtl_file(mtl_path))
                if best_material:
                    mtl_props = best_material[1]
            self._procedural_mtl_cache[element_type] = (mtl_props, mtl_dir, mtl_path)
        return self._procedural_mtl_cache[element_type]

    def _resolve_element_faces(self, element: Element, names: List[str]) -> Dict[str, ResolvedFace]:
        """
        Resolve the look of the given faces of a procedural element.

        Box elements use their ``textures`` structure and class default; other elements
        resolve from the MTL file only (see floor_planner.face_textures).

        Args:
            element: Procedural element
            names: Face names (box faces, extra faces, or 'default' for the whole element)

        Returns:
            Dict mapping face name to ResolvedFace
        """
        element_type = get_element_type_from_instance(element)
        mtl_props, mtl_dir, mtl_path = self._read_procedural_mtl(element_type)
        if hasattr(element, 'get_face_textures'):
            element_textures = element.get_face_textures()
            class_textures = type(element).get_default_face_textures()
        else:
            element_textures = class_textures = FaceTextures()

        def find(texture_ref: str, source: str) -> Optional[Path]:
            texture_path = self.texture_manager.find_texture(texture_ref, mtl_dir)
            if texture_path is None:
                where = mtl_path if source == '.mtl map_Kd' else f"{source} of element '{element.get_id()}'"
                WarnMsg(f"Texture '{texture_ref}' referenced by {where} not found")
            return texture_path

        return {name: resolve_face(name, element_textures, class_textures, mtl_props, find) for name in names}

    def _get_default_material(self, element: Element) -> Optional[int]:
        """
        Get or create the material of a procedural element as a whole.

        Used for geometry without per-face materials (roofs, circular elements, ...):
        the material comes from the element type's MTL file
        (models/procedural/<type>/<type>.mtl) and its map_Kd texture.

        Args:
            element: Element to get material for

        Returns:
            Material index
        """
        resolved = self._resolve_element_faces(element, ['default'])['default']
        return self._get_procedural_material(element, resolved)

    def _get_procedural_material(self, element: Element, resolved: ResolvedFace) -> int:
        """
        Get or create the glTF material for one resolved face look of a procedural element.

        Materials are shared by all faces/elements of the same type with the same look.
        The first material of a type is named ``<type>_material``, further variants
        ``<type>_material_<n>``. Falls back to built-in colours for values that are
        set neither in YAML nor in the MTL file.

        Args:
            element: Element the face belongs to
            resolved: Resolved face look (texture, Kd, Ks, Ns, opacity)

        Returns:
            Material index
        """
        element_type = get_element_type_from_instance(element)
        element_blend = getattr(element, 'alpha_mode', None) == "BLEND"
        cache_key = (element_type, resolved.material_key, element_blend)
        if cache_key in self.procedural_material_cache:
            return self.procedural_material_cache[cache_key]

        variant = self._procedural_material_counts.get(element_type, 0)
        self._procedural_material_counts[element_type] = variant + 1
        material_name = f"{element_type}_material" if variant == 0 else f"{element_type}_material_{variant}"
        material = {
            "name": material_name,
            "pbrMetallicRoughness": {}
        }

        # Opacity (MTL 'd': 1.0 = opaque, 0.0 = fully transparent)
        alpha = resolved.opacity if resolved.opacity is not None else 1.0
        if alpha < 0.99:
            material["alphaMode"] = "BLEND"

        # Base color from diffuse (Kd) or default
        if resolved.diffuse is not None:
            diffuse = list(resolved.diffuse)
            # If the MTL diffuse is black but there is a texture, use white to show the texture
            if resolved.diffuse_from_mtl and resolved.texture_path is not None and sum(diffuse) < 0.01:
                diffuse = [1.0, 1.0, 1.0]
            material["pbrMetallicRoughness"]["baseColorFactor"] = diffuse + [alpha]
        else:
            # Fallback colors if no diffuse is set
            default_colors = {
                'wall': [0.95, 0.95, 0.95],
                'wall_nd': [0.95, 0.95, 0.95],
                'door': [0.7, 0.4, 0.2],
                'window': [0.8, 0.9, 1.0],
            }
            base_color = default_colors.get(element_type, [0.8, 0.8, 0.8])
            material["pbrMetallicRoughness"]["baseColorFactor"] = base_color + [alpha]
        
        # Roughness from shininess (Ns) or default
        if resolved.shininess is not None:
            # Convert Phong shininess to roughness (inverse relationship)
            roughness = 1.0 - min(resolved.shininess / 100.0, 1.0)
            material["pbrMetallicRoughness"]["roughnessFactor"] = roughness
        else:
            material["pbrMetallicRoughness"]["roughnessFactor"] = 0.8
        
        # Metallic factor (typically non-metallic for architectural elements)
        material["pbrMetallicRoughness"]["metallicFactor"] = 0.0
        
        # Specular extension if a specular color is set
        if resolved.specular is not None:
            self._add_specular_extension(material, list(resolved.specular))
        
        # Add alphaMode if element has transparency
        if element_blend:
            material["alphaMode"] = "BLEND"
        
        # Double-sided (back faces not culled); glTF default is single-sided, so only written when set
        if resolved.double_sided:
            material["doubleSided"] = True
        
        # Add texture if available
        texture_path = resolved.texture_path
        if texture_path and texture_path.exists():
            # Check cache to avoid copying same texture multiple times
            cache_key_tex = str(texture_path)
            if cache_key_tex not in self.texture_paths:
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
                    self.texture_paths[cache_key_tex] = image_index
                    
                except Exception as e:
                    WarnMsg(f"Failed to copy texture {texture_path}: {e}")
                    image_index = None
            else:
                image_index = self.texture_paths[cache_key_tex]
            
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
        self.procedural_material_cache[cache_key] = material_index
        
        return material_index
    
    def _add_external_model_element(self, element: ExternalModelElement) -> int:
        """
        Add element with external 3D model.

        For unanimated elements emits a single node carrying the fully-composed
        matrix (Steps 1-5 baked together).

        For animated elements (element.animation is not None) emits two nodes:
          - Parent node: Placement matrix only (static, never changes).
          - Child node:  Steps 1-4 as separate TRS fields + mesh + extras.animation.
            The 3D player animates the child node's TRS in response to user
            interaction; the parent Placement is automatically composed by the
            glTF scene graph.

        Args:
            element: Element with external model

        Returns:
            Node index of the (parent) node added to self.nodes
        """
        model_path = element.model_path
        model_format = element.get_model_format()

        def _load_mesh(node: dict) -> None:
            """Attach mesh geometry to node in-place if model file is readable."""
            if model_path and model_format == 'obj':
                mesh_index = self._load_obj_as_mesh(model_path)
                if mesh_index is not None:
                    node["mesh"] = mesh_index
            elif model_path and model_format == '3ds':
                mesh_index = self._load_3ds_as_mesh(model_path)
                if mesh_index is not None:
                    node["mesh"] = mesh_index
            elif model_path and model_format == 'dae':
                mesh_index = self._load_dae_as_mesh(model_path)
                if mesh_index is not None:
                    node["mesh"] = mesh_index
            elif model_path and model_format == 'gltf':
                mesh_index = self._load_glb_as_mesh(model_path)
                if mesh_index is not None:
                    node["mesh"] = mesh_index

        anim_data = getattr(element, 'animation', None)

        if anim_data is None:
            # ── Non-animated: single node, fully-baked matrix (original behaviour) ──
            final_transform = element.get_final_transform()
            node = {
                "name": f"{element.get_registry_key()}_{len(self.nodes):03d}",
                "matrix": matrix_to_json(final_transform),
                "extras": {
                    "element_type": element.get_registry_key(),
                    "external_model": True,
                    "model_path": str(model_path),
                    "model_format": model_format,
                },
            }
            _load_mesh(node)
            node_index = len(self.nodes)
            self.nodes.append(node)
            self.root_node_indices.append(node_index)
            return node_index

        # ── Animated: parent (Placement) + child (Steps 1-4, animatable TRS) ──
        #
        # glTF spec: a node with `matrix` may NOT also carry TRS or be an
        # animation target.  So the parent uses `matrix` (Placement only, static)
        # and the child uses separate translation/rotation/scale (TRS) fields so
        # the player can drive animation channels on it.

        # Parent: Placement only
        placement_matrix = element.get_placement_transform()
        child_index = len(self.nodes) + 1          # will be appended right after parent

        parent_node = {
            "name": f"{element.get_registry_key()}_{len(self.nodes):03d}_placement",
            "matrix": matrix_to_json(placement_matrix),
            "children": [child_index],
            "extras": {
                "element_type": element.get_registry_key(),
                "external_model": True,
                "model_path": str(model_path),
                "model_format": model_format,
            },
        }

        # Child: Steps 1-4 (normalization chain, no Placement) decomposed to TRS
        # so animation channels can target translation/rotation/scale independently.
        from floor_planner.transform import build_normalization_matrix

        normalization = element.get_normalization_transform()

        sec_norm_data = getattr(element, 'secondary_normalization', None)
        sec_norm_matrix = (
            build_normalization_matrix(sec_norm_data)
            if sec_norm_data is not None
            else np.eye(4)
        )

        anchor_offset_matrix = np.eye(4)
        if element._model_metadata and element._model_metadata.anchor_offset != (0.0, 0.0, 0.0):
            off = element._model_metadata.anchor_offset
            anchor_offset_matrix[0, 3] = -off[0]
            anchor_offset_matrix[1, 3] = -off[1]
            anchor_offset_matrix[2, 3] = -off[2]

        sec_anchor_data = getattr(element, 'secondary_anchor_offset', None)
        sec_anchor_matrix = np.eye(4)
        if sec_anchor_data is not None:
            sec_anchor_matrix[0, 3] = -sec_anchor_data[0]
            sec_anchor_matrix[1, 3] = -sec_anchor_data[1]
            sec_anchor_matrix[2, 3] = -sec_anchor_data[2]

        child_matrix = compose_transforms(
            sec_anchor_matrix,
            anchor_offset_matrix,
            sec_norm_matrix,
            normalization,
        )

        translation, rotation_quat, scale = matrix_to_trs(child_matrix)

        child_node = {
            # glTF TRS fields — required for animation targeting
            "name": f"{element.get_registry_key()}_{child_index:03d}_anim",
            "translation": translation.tolist(),
            "rotation":    rotation_quat.tolist(),   # [x, y, z, w]
            "scale":       scale.tolist(),
            "extras": {
                "animation": anim_data,
            },
        }
        _load_mesh(child_node)

        parent_idx = len(self.nodes)
        self.nodes.append(parent_node)
        self.nodes.append(child_node)
        # Only the parent is a scene root; the child is referenced via parent.children
        self.root_node_indices.append(parent_idx)
        return parent_idx
    
    def export(self, filename: str = "floor_plan_3d.gltf", v_anchor: float = 0.0) -> Path:
        """
        Export scene to glTF file.
        
        Args:
            filename: Output filename (default: floor_plan_3d.gltf)
            v_anchor: Y-axis elevation for the entire floor plan (metres).  When
                      non-zero a single wrapper node with translation [0, v_anchor, 0]
                      is inserted as the sole scene root and all element nodes become
                      its children.  This lets multiple floor plans (storeys) share
                      one glTF scene with correct vertical stacking.
        
        Returns:
            Path to exported glTF file
        """
        output_path = self.output_dir / filename
        
        # Optionally wrap all element nodes in a floor-level translation node.
        # This allows multiple floor plans (storeys) to be stacked correctly on Y.
        if v_anchor != 0.0 and self.root_node_indices:
            floor_node = {
                "name": "floor_level",
                "translation": [0.0, float(v_anchor), 0.0],
                "children": list(self.root_node_indices),
            }
            floor_node_index = len(self.nodes)
            self.nodes.append(floor_node)
            scene_roots = [floor_node_index]
        else:
            scene_roots = self.root_node_indices

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
                    "nodes": scene_roots
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
    filename: str = "floor_plan_3d.gltf",
    v_anchor: float = 0.0
) -> Path:
    """
    Export floor plan elements to glTF format.
    
    Args:
        elements: List of floor plan elements to export
        output_dir: Directory to write glTF files
        filename: Output filename
        v_anchor: Y-axis elevation for the entire floor plan (metres); adds a root
                  translation node so all geometry is offset by this amount on Y.
    
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
    return exporter.export(filename, v_anchor=v_anchor)
