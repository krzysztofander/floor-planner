# 3D Transform Pipeline for External Model Elements

This document describes how each transform is computed, in which order they are
applied, and what is done by the Python floor-planner tool vs. the 3D player at
runtime.

glTF 2.0 is the only active 3D exporter (`project.export_to_gltf()` in
`floor_planner/__main__.py`; the legacy OBJ export call is commented out).
External models in `.glb`/`.gltf`, `.obj`, `.dae` or `.3ds` format are all
converted into glTF meshes by `floor_planner/gltf_exporter.py`.

---

## Coordinate system

| Axis | Direction | Unit |
|------|-----------|------|
| **X** | floor-plan x | metre |
| **Y** | Up — vertical height | metre |
| **Z** | floor-plan y | metre |

A floor-plan `anchor_point: [2.5, 3.0]` therefore maps to world position
`X = 2.5 m`, `Z = 3.0 m`.  The element's `v_anchor` sets the `Y` position
(height above the floor level).

---

## Model lookup

The model directory for an element is `<models_dir>/<registry_key>/`, where the
default base `models_dir` is the repo's `models/`.  `ExternalModelElement._resolve_models_dir()`
searches, in order:

```
models/  →  models/local/  →  models/models_3rd_party/  →  models/stubs/
```

The first base directory containing a `<registry_key>/` folder wins (`stubs/`
holds placeholder cubes as the last fallback).  Inside it the model file is
picked in priority order `model.glb`, `model.gltf`, `model.obj`, `model.dae`,
`model.3ds`, and metadata is read from `model.transform.json`.  If
`_requires_external_model = True` and no model file is found, a
`FileNotFoundError` listing all searched paths is raised.

---

## Data sources

| Name | Where defined | Python attribute |
|------|---------------|-----------------|
| `normalization` | `<model dir>/model.transform.json` → `normalization` | `element._model_metadata.normalization_matrix` |
| `anchor_offset` | `<model dir>/model.transform.json` → `anchor_offset` | `element._model_metadata.anchor_offset` |
| `secondary_normalization` | Element `__init__` code (e.g. `WindowDoorDouble`, `LeafyTree`, `GlassPanel`) | `element.secondary_normalization` (dict or `None`) |
| `secondary_anchor_offset` | Element `__init__` code | `element.secondary_anchor_offset` (list or `None`) |
| `orientation_angle` | YAML `orientation_angle:` | `element.orientation_angle` |
| `anchor_point` | YAML `anchor_point: [x, z]` | `element.anchor_point` |
| `v_anchor` | YAML `v_anchor:` (or computed vertical level) | `element.v_anchor` |

---

## Pipeline — order of application

The pipeline is a single 4 × 4 matrix product, computed by
`ExternalModelElement.get_final_transform()` in
`floor_planner/elements/external_models.py` (via `compose_transforms()`):

```
final = Placement × SecondaryAnchor × AnchorOffset × SecondaryNorm × Normalization
```

Matrix multiplication is **right-to-left**, so the transforms are **applied to
the model in this order**:

```
1. Normalization
2. SecondaryNormalization
3. AnchorOffset
4. SecondaryAnchorOffset
5. Placement
```

### Step 1 — Normalization

**Source:** `model.transform.json` → `normalization` section.  
**Built by:** `_build_transform_matrix()` in `ModelMetadata.from_dict()`
(`floor_planner/model_metadata.py`), stored as `ModelMetadata.normalization_matrix`.  
**Purpose:** Bring the raw model into standard space — correct scale, axis alignment, unit.

Two formats are accepted:

- **Components** (used when any of `scale` / `rotation` / `translation` is
  present; missing ones default to identity values):

  ```text
  Normalization = Translation @ (Rz @ Ry @ Rx) @ Scale
  ```

  i.e. scale first, then rotate X→Y→Z (Euler, degrees), then translate.
- **Legacy `matrix`**: a 4 × 4 nested row-major list (translation in the last
  column), loaded by `load_matrix_from_json()`.

No `normalization` section → identity.

Example (`models/window_90x120/model.transform.json`):
```json
"normalization": {
  "scale":       [1.0, 1.0, 1.0],
  "rotation":    [0, 0, 0],
  "translation": [0, 0, 0]
}
```

### Step 2 — SecondaryNormalization

**Source:** Python element class `__init__`.  
**Built by:** `build_normalization_matrix(element.secondary_normalization)` in
`floor_planner/transform.py` — same `{scale, rotation, translation}` dict and
the same `Translation @ (Rz @ Ry @ Rx) @ Scale` math as Step 1; all keys optional.  
**Purpose:** Per-instance adjustment.  `None` (class default) → identity.

Typical uses: scaling a fixed-size model to user-given dimensions (fixed
windows, `GlassPanel`, `GlassSlope`, `LeafyTree` / `LeafyShrub1` — which also
add a random Y rotation), or mirroring a model variant (`WindowDoorDouble`):

```python
self.secondary_normalization = {
    'scale': [length / self._default_length(), height / self._default_height(), 1],
}
```

(`ExternalModelElement.__init__` rejects `width` / `length` / `height` kwargs;
elements that support resizing take their own parameters and scale here.)

### Step 3 — AnchorOffset

**Source:** `model.transform.json` → `anchor_offset` (default `[0, 0, 0]`).  
**Built by:** inline matrix construction in `get_final_transform()`.  
**Purpose:** Move the model's logical anchor point (e.g. bottom-left corner of a
door frame) to the local origin before the placement rotation.

The offset is **negated**:

```python
anchor_offset_matrix[0, 3] = -off[0]
anchor_offset_matrix[1, 3] = -off[1]
anchor_offset_matrix[2, 3] = -off[2]
```

### Step 4 — SecondaryAnchorOffset

**Source:** Python element class `__init__`.  
**Built by:** inline matrix construction in `get_final_transform()`.  
**Purpose:** Same mechanic as AnchorOffset, set per instance in code; also
**negated** (the value is the point that should be moved to the origin).
`None` → identity.

### Step 5 — Placement

**Source:** YAML `anchor_point`, `orientation_angle`, `v_anchor`.  
**Built by:** `create_placement_matrix()` in `floor_planner/transform.py`.  
**Purpose:** Rotate the model around the world Y-axis and translate it to its
scene position.

Exact matrix (`a = radians(orientation_angle)`):

```
┌  cos(a)   0   -sin(a)   anchor_point[0] ┐
│  0        1    0        v_anchor        │
│  sin(a)   0    cos(a)   anchor_point[1] │
└  0        0    0        1               ┘
```

Local +X maps to `(cos a, sin a)` in floor-plan (x, y), i.e. the angle is
counter-clockwise in the floor plan.  `anchor_point[1]` maps to the **Z axis**.

---

## Where the computation happens

| Step | Python tool | 3D player |
|------|-------------|-----------|
| Steps 1–5 composed into matrices | **Yes** | No |
| Emitting to glTF (`matrix_to_json()` → flat column-major list of 16, or `matrix_to_trs()` → TRS) | **Yes** | No |
| Applying node transforms to mesh vertices | No | **Yes** — standard glTF scene graph |
| Playing door animations from `extras.animation` | No | **Yes** — custom player logic |

### Non-animated elements

`_add_external_model_element()` in `floor_planner/gltf_exporter.py` writes the
fully composed matrix into a single node:

```python
node = {
    "name": f"{registry_key}_{node_index:03d}",
    "matrix": matrix_to_json(element.get_final_transform()),
    "extras": {
        "element_type": element.get_registry_key(),
        "external_model": True,
        "model_path": str(model_path),
        "model_format": model_format,
    },
    "mesh": ...,   # loaded from the model file
}
```

```
glTF node.matrix = [m00, m10, m20, m30,  m01, m11, m21, m31,  ...]   (column-major)
```

`extras` is informational only; it does not affect the transform.

### Floor level and composite elements

- `export()` gets the floor plan's `v_anchor`; when non-zero, all element root
  nodes are wrapped in a `floor_level` node with `translation [0, v_anchor, 0]`
  (stacking storeys in one scene).
- Composite elements (e.g. `Composite_WindowDoorDouble`, `Composite_GlassDoor`)
  hold sub-elements in a list; `add_element()` recurses into `getList()` and
  each sub-element is exported with its own nodes/transforms.

---

## Animation (doors)

Animated elements are those with `element.animation is not None`.  Currently
these are doors: external-model `BalconyDoor` and subclasses (`WindowDoor`,
`WindowDoorDouble`, `SolidDoor1/2`, `GlassDoor`) and procedural `Door`
(and `SolidGlassDoor`).  `door_type='fixture'` produces no animation.

### Node hierarchy

```
Parent node  →  matrix = Placement only  (static)
  └── Child node  →  TRS + mesh + extras.animation
```

The glTF spec forbids `matrix` together with TRS on one node, and animation can
only target TRS, so the child uses `translation` / `rotation` / `scale`
decomposed with `matrix_to_trs()`.  Rest pose = `parent.matrix × child.TRS`,
identical to the non-animated result.

| Element kind | Child TRS decomposed from | Node names |
| --- | --- | --- |
| External model (`_add_external_model_element`) | `SecAnchor × AnchorOffset × SecNorm × Normalization` (Steps 1–4) | `<registry_key>_<idx>_placement` / `_anim` |
| Procedural (`_add_procedural_element`) | `SecAnchor × SecNorm` | `<ClassName>_<id>_placement` / `_anim` |

For procedural animated elements the mesh is generated in local space
(`_generate_local_geometry()` temporarily sets `anchor_point=(0,0)`,
`orientation_angle=0`, `v_anchor=0`), so the parent Placement positions it.

### `extras.animation` descriptor

Built by `Door3D.getAnimation()` (`floor_planner/elements/foundation/door.py`)
using `AnimationMetadata` (`floor_planner/motion_3d.py`).  `Door3D` delegates to
`Door3DHinged` (`door_type='hinged'`) or `SlidingDoor3D` (`'sliding'`), whose
`calcNormalisationAndOffset()` computes the values.  Only the `proximity`
trigger is emitted.

```jsonc
"animation": {
  "type": "proximity",
  "pre_translation":  [x, y, z],   // applied before the animated delta
  "pre_rotation":     [rx, ry, rz],//   (e.g. stretch to doorway width,
  "pre_scale":        [sx, sy, sz],//    180° flip for right-hand doors)
  "translation":      [x, y, z],   // open-state delta
  "rotation":         [rx, ry, rz],//   (degrees, Euler)
  "scale":            [sx, sy, sz],
  "post_translation": [x, y, z],   // applied after the delta (move back to
  "post_rotation":    [rx, ry, rz],//   the hinge/slide position in the wall)
  "post_scale":       [sx, sy, sz],
  "data": [px, py, pz, d1, d2]     // activation point + activation distances
}
```

| | Hinged (`Door3DHinged`) | Sliding (`SlidingDoor3D`) |
| --- | --- | --- |
| `rotation` | `[0, ±90, 0]` (sign from `opening_outside` / `to_the_right`) | `[0, 0, 0]` |
| `translation` | `[0, 0, 0]` | `[±door_width × stretch × 0.999, 0, 0]` (+X if `to_the_right`) |
| `pre_scale` | `[stretch, 1, 1]`, `stretch = doorway_width / model_door_width` | same |

Activation: `point = (doorway_width / 2, 1.2, -0.5 if opening_outside else 0.5)`,
`distance = (2.0, 1)`.  Procedural `Door` passes `model_door_width = doorway_width`
(stretch = 1) and `wing_width_on_model = model_depth = thickness`; external
doors use the defaults `0.9` / `0.12`.

How `pre_* → delta → post_*` is combined with the child rest TRS and
interpolated is defined by the 3D player (not part of this repo); the Python
tool only emits the descriptor.

### Adding animation to a new element

Set `self.animation` to a descriptor dict in `__init__` (for doors: build a
`Door3D` and call `getAnimation()`).  No exporter changes are needed — both
`_add_external_model_element()` and `_add_procedural_element()` detect
`element.animation is not None` and emit the two-node hierarchy.

---

## Summary diagram

```
Model file (.glb / .gltf / .obj / .dae / .3ds)
        │
        ▼
[1] Normalization          ← model.transform.json normalization
        │                     (scale, rotation[XYZ deg], translation  |  legacy matrix)
        ▼
[2] SecondaryNormalization ← element __init__ code (same dict format; None = skip)
        ▼
[3] AnchorOffset           ← model.transform.json anchor_offset (negated)
        ▼
[4] SecondaryAnchorOffset  ← element __init__ code (negated; None = skip)
        ▼
[5] Placement              ← YAML: anchor_point, orientation_angle, v_anchor
        │
        ├─ not animated → final 4×4 → matrix_to_json() → single node.matrix
        └─ animated     → parent.matrix = [5];  child TRS = [1–4] + extras.animation
        │
        ▼  (optional floor_level node: translation [0, floor v_anchor, 0])
  Rendered 3D position
```

---

## `model.transform.json` schema (transform-relevant fields)

```jsonc
{
  "model_file": "model.obj",
  "model_format": "obj",                 // "gltf" (default) or "obj" — informational
  "format_version": "1.0",
  "element_type": "window_90x120",
  "registry_key": "window_90x120",       // defaults to element_type
  "normalization": {
    "description": "...",
    "scale":       [sx, sy, sz],
    "rotation":    [rx_deg, ry_deg, rz_deg],  // Euler, X→Y→Z, degrees
    "translation": [tx, ty, tz]               // metres
    // or legacy: "matrix": [[...],[...],[...],[...]]  (4×4 row-major)
  },
  "anchor_point": "bottom_left",         // semantic name only
  "anchor_offset": [ox, oy, oz],         // negated when applied (Step 3)
  "bounding_box": { "min": [x, y, z], "max": [x, y, z] },
  "dimensions": { "width": w, "length": l, "height": h }  // optional; else from bounding_box
}
```

`model_file`, `format_version` and `element_type` are required.  Element
dimensions come from `dimensions` (if all three are given) or the bounding box
(`width` = X extent, `length` = Z extent, `height` = Y extent).  The actual
model file is chosen by file existence (see *Model lookup*), not by `model_file`.
