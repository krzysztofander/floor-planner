# 3D Transform Pipeline for External Model Elements

This document describes exactly how each transform is computed, in which order they
are applied, and whether the work is done by the Python floor-planner tool or by the
3D player at runtime.

---

## Coordinate system

| Axis | Direction | Unit |
|------|-----------|------|
| **X** | East — floor-plan horizontal | metre |
| **Y** | Up — vertical height | metre |
| **Z** | South — floor-plan "depth" | metre |

A floor-plan `anchor_point: [2.5, 3.0]` therefore maps to world position
`X = 2.5 m`, `Z = 3.0 m`.  The YAML `v_anchor` / `v_offset` value sets the `Y`
position (height above floor).

---

## Data sources

| Name | Where defined | Python attribute |
|------|---------------|-----------------|
| `normalization` | `models/<key>/model.transform.json` | `element._model_metadata.normalization_matrix` |
| `anchor_offset` | `models/<key>/model.transform.json` → `anchor_offset` | `element._model_metadata.anchor_offset` |
| `secondary_normalization` | Element `__init__` code (e.g. `BalconyDoor`) | `element.secondary_normalization` (dict or `None`) |
| `secondary_anchor_offset` | Element `__init__` code | `element.secondary_anchor_offset` (list or `None`) |
| `orientation_angle` | YAML `orientation_angle:` | `element.orientation_angle` |
| `anchor_point` | YAML `anchor_point: [x, z]` | `element.anchor_point` |
| `v_anchor` / `v_offset` | YAML `v_anchor:` (or computed vertical level) | `element.v_anchor` |

---

## Pipeline — order of application

The pipeline is expressed as a single 4 × 4 matrix product, computed once
by `ExternalModelElement.get_final_transform()` in
`floor_planner/elements/external_models.py`:

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

**Source:** `models/<registry_key>/model.transform.json` → `normalization` section.  
**Built by:** `ModelMetadata.normalization_matrix` (parsed in `floor_planner/model_metadata.py`).  
**Purpose:** Bring the raw model into standard space — correct scale, axis alignment, unit.

The JSON section accepts `scale`, `rotation` (Euler XYZ in degrees), and `translation`.
The matrix is built as:

```
Normalization = Translation @ (Rz @ Ry @ Rx) @ Scale
```

i.e. scale first, then rotate X→Y→Z, then translate.

Example (`window_90x120/model.transform.json`):
```json
"normalization": {
  "scale":       [1.0, 1.0, 1.0],
  "rotation":    [0, 0, 0],
  "translation": [0, 0, 0]
}
```

### Step 2 — SecondaryNormalization

**Source:** Python element class `__init__` (e.g. `BalconyDoor.__init__`).  
**Built by:** `build_normalization_matrix(element.secondary_normalization)` in `floor_planner/transform.py`.  
**Purpose:** Per-instance override — used to partially open a door wing, mirror a
model variant, etc. Not present in most elements (`None` → identity matrix).

Accepts the same `{scale, rotation, translation}` dict as the JSON normalization:

```python
self.secondary_normalization = {
    'rotation': [0, 15, 0],   # open door 15° around Y
}
```

Matrix is built identically to Step 1:
```
SecondaryNorm = Translation @ (Rz @ Ry @ Rx) @ Scale
```

### Step 3 — AnchorOffset

**Source:** `models/<registry_key>/model.transform.json` → `anchor_offset` field.  
**Built by:** inline matrix construction in `get_final_transform()`.  
**Purpose:** Translate the model so that its logical anchor point (e.g. bottom-left
corner of a door frame) lies at the local origin before the placement rotation is
applied.

The offset is **negated**:

```python
anchor_offset_matrix[0, 3] = -off[0]   # move anchor to origin
anchor_offset_matrix[1, 3] = -off[1]
anchor_offset_matrix[2, 3] = -off[2]
```

Most current models have `anchor_offset: [0, 0, 0]` (identity).

### Step 4 — SecondaryAnchorOffset

**Source:** Python element class `__init__`.  
**Built by:** inline matrix construction in `get_final_transform()`.  
**Purpose:** Same mechanic as AnchorOffset but set per-instance in code.  Used by
`BalconyDoor` for `to_the_right=True` variants to move the hinge to the origin
before the secondary rotation is applied.

Also **negated** (same sign convention as `anchor_offset`):

```python
self.secondary_anchor_offset = [W, 0, 0]   # hinge is at X=W; move it to origin
```

`None` → identity matrix.

### Step 5 — Placement

**Source:** YAML `anchor_point`, `orientation_angle`, `v_anchor`.  
**Built by:** `create_placement_matrix()` in `floor_planner/transform.py`.  
**Purpose:** Rotate the model around the world Y-axis and translate it to its final
scene position.

```
Placement = Translation(anchor_point.x, v_anchor, anchor_point.z)
            × RotationY(orientation_angle)
```

Exact matrix (row-major notation, `a = radians(orientation_angle)`):

```
┌  cos(a)   0   -sin(a)   anchor_point.x ┐
│  0        1    0        v_anchor       │
│  sin(a)   0    cos(a)   anchor_point.z │
└  0        0    0        1              ┘
```

Note: `anchor_point[1]` (the second element of the YAML list) maps to the **Z axis**,
not Y.

---

## Where the computation happens

| Step | Done in Python tool? | Done by 3D player? |
|------|---------------------|--------------------|
| 1–5 combined into `final` matrix | **Yes** — in `get_final_transform()` | No |
| Emitting transform to glTF | **Yes** — `matrix_to_json(final_transform)` converts to column-major flat list of 16 | No |
| Applying the matrix to mesh vertices | No | **Yes** — the glTF node `matrix` field is applied by the renderer |

> **Note:** All five steps are fully computed and baked by the Python tool.
> The 3D player applies the resulting `node.matrix` passively; it performs no
> transform computation of its own.

### How the matrix is passed to the 3D player (non-animated elements)

`_add_external_model_element()` in `floor_planner/gltf_exporter.py` writes the
fully-composed matrix into the glTF node:

```python
final_transform = element.get_final_transform()   # 4×4 numpy array

node = {
    "name": f"{registry_key}_{index:03d}",
    "matrix": matrix_to_json(final_transform),    # 16-element column-major list
    "extras": {
        "element_type": element.get_registry_key(),
        "external_model": True,
        "model_path": str(model_path),
        "model_format": model_format,
    }
}
```

`matrix_to_json()` produces a **flat column-major array of 16 floats** as required
by the glTF 2.0 spec (`node.matrix`).  A conformant glTF renderer applies it to
every vertex of the node's mesh automatically — the 3D player needs no special
logic beyond loading a standard glTF file.

```
glTF node.matrix = [m00, m10, m20, m30,  m01, m11, m21, m31,  ...]   (column-major)
```

The `extras` object is purely informational metadata for tooling or debugging; it
is not used by the renderer for any transform.

---

## Animation support (Option B — extras metadata + node hierarchy)

Animated elements (currently: `BalconyDoor`; future: sliding garage doors, etc.)
use a **two-node glTF hierarchy** instead of a single baked node.  The split
allows the 3D player to animate the inner node independently while the outer
Placement stays fixed.

### Node hierarchy

```
Parent node  →  matrix = Placement only  (Steps 1–5 = Placement; static)
  └── Child node  →  TRS = Steps 1–4  +  mesh  +  extras.animation
```

glTF's scene graph multiplies `parent.matrix × child.TRS` at render time, so the
rendered rest-pose is identical to the single-node non-animated version.  The
player animates only the **child** node's `rotation` (hinge) or `translation`
(slide).

> **Why split?**  The glTF spec forbids a node from having both a `matrix` field
> **and** TRS (`translation`/`rotation`/`scale`) fields.  Animation channels can
> only target TRS properties, not `matrix`.  So the child must use TRS.

### What the Python tool emits

```python
# Parent — Placement only, static matrix
parent_node = {
    "name": "balcony_door_004_placement",
    "matrix": [...],          # 16-float column-major Placement matrix
    "children": [child_idx],
    "extras": { "element_type": "balcony_door", ... }
}

# Child — normalization chain as TRS + animation descriptor in extras
child_node = {
    "name": "balcony_door_005_anim",
    "translation": [tx, ty, tz],
    "rotation":    [qx, qy, qz, qw],   # unit quaternion decomposed from Steps 1-4
    "scale":       [sx, sy, sz],
    "mesh": ...,
    "extras": {
        "animation": {
            "type":         "hinge_rotation",
            "axis":         [0, 1, 0],         # Y-axis (vertical hinge)
            "pivot_local":  [0.0, 0.0, 0.0],   # hinge point in child-node space
            "closed_angle": 0.0,               # degrees, door shut
            "open_angle":   90.0,              # degrees, door fully open
            "duration":     0.5,               # seconds
            "trigger":      "click"
        }
    }
}
```

The TRS values are computed by decomposing the Steps 1–4 matrix via
`matrix_to_trs()` in `floor_planner/transform.py`.

The child's rest-pose (TRS) already includes the 15° ajar angle from
`secondary_normalization`.  The `closed_angle` and `open_angle` in the animation
descriptor are relative to that rest-pose and are applied **on top of** it by the
player.

### What the 3D player must do

Only the child node (`_anim` suffix, has `extras.animation`) requires player logic.

```js
// Pseudo-code for a hinge_rotation door
function onSceneLoad(gltf) {
    for (const node of gltf.nodes) {
        if (node.extras?.animation?.type === 'hinge_rotation') {
            node.userData.anim = node.extras.animation;
            node.addEventListener('click', () => toggleDoor(node));
        }
    }
}

function toggleDoor(node) {
    const a = node.userData.anim;
    // Rotate node around a.pivot_local along a.axis
    // from current angle toward a.open_angle (or back to a.closed_angle)
    // over a.duration seconds.
    // DO NOT touch the parent node's matrix.
}
```

For `slide_translation` (e.g. garage door):
```js
// Translate node along a.axis by a.distance over a.duration seconds.
```

### How to add animation to a new element

1. Set `self.animation` dict in the element's `__init__` (see
   `ExternalModelElement.animation` class-level docstring for full schema).
2. No exporter changes needed — `_add_external_model_element()` detects
   `element.animation is not None` and automatically emits the two-node hierarchy.

```python
# Example: sliding garage door
self.animation = {
    'type':     'slide_translation',
    'axis':     [1, 0, 0],    # slide along X
    'distance': self.door_width,
    'duration': 1.2,
    'trigger':  'click',
}
```

---

## Summary diagram

```
Model file (.obj / .glb)
        │
        ▼
[1] Normalization          ← models/<key>/model.transform.json  →  scale/rotate/translate
        │                     (scale, rotation[XYZ deg], translation)
        ▼
[2] SecondaryNormalization ← element __init__ code             →  per-variant adjust
        │                     (same dict format; None = skip)
        ▼
[3] AnchorOffset           ← model.transform.json anchor_offset →  negate & translate
        │                     (moves logical anchor to origin)
        ▼
[4] SecondaryAnchorOffset  ← element __init__ code             →  additional pivot shift
        │                     (None = skip)
        ▼
[5] Placement              ← YAML: anchor_point, orientation_angle, v_anchor
        │                     RotationY(orientation_angle) then translate to scene pos
        ▼
  final 4×4 matrix
        │
        ▼  matrix_to_json()  →  16-float column-major list
  glTF node.matrix
        │
        ▼  (renderer applies to mesh at load time)
  Rendered 3D position
```

---

## `build_normalization_matrix` helper

Used for both Steps 1 and 2.  Located in `floor_planner/transform.py`.

```python
build_normalization_matrix({'scale': [sx,sy,sz], 'rotation': [rx,ry,rz], 'translation': [tx,ty,tz]})
# Returns: Translation @ (Rz @ Ry @ Rx) @ Scale
```

All keys optional; defaults: `scale=[1,1,1]`, `rotation=[0,0,0]`, `translation=[0,0,0]`.

---

## `model.transform.json` schema (relevant fields)

```jsonc
{
  "normalization": {
    "scale":       [sx, sy, sz],         // uniform or per-axis scale
    "rotation":    [rx_deg, ry_deg, rz_deg],  // Euler angles, X→Y→Z, degrees
    "translation": [tx, ty, tz]          // metres
  },
  "anchor_offset": [ox, oy, oz],         // point in model-space that is the logical anchor
  "bounding_box": {
    "min": [x, y, z],
    "max": [x, y, z]
  }
}
```

The `anchor_offset` vector is **negated** when applied (Step 3) so the named
anchor point is moved to the local origin before the placement rotation.
