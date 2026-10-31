# Feature: pytest-regression-suite

**Status:** Phase 2 complete (3D golden for selected scenes)  
**Priority:** Medium  
**Estimated Effort:** 2–3 days (phase 1)

## Overview

Add a `pytest` suite that runs every YAML scene project end to end and fails on errors, broken output or visual regressions, plus contract tests over the element registry. It replaces the manual checks used so far: scratch copies, grepping `make` logs, and ad-hoc glTF comparison scripts.

Layers:

| Layer | What it checks | Speed |
|-------|----------------|-------|
| Contract tests | rules every registered element type must follow | seconds |
| Scene tests | each YAML project: runs without error, glTF invariants, 2D image vs golden | minutes (marked `slow`) |
| 3D golden (phase 2) | per-node summary of the glTF vs golden, for the scenes in `GOLDEN_3D_SCENES` | part of the scene tests |

## Motivation

- `make` exits 0 even when the glTF export fails: `Project.export_to_gltf` catches the exception and only prints "Error exporting".
- `make` writes its outputs into the repository, so tracked PNGs change whenever it is run.
- Rendering regressions are found only by opening the outputs.
- The checks done during the last refactorings (no `**kwargs`, `id` on every element, `textures` on every box) were one-off scripts; nothing stops a new element from breaking them.

## Decisions

| # | Topic | Decision |
|---|-------|----------|
| 1 | Scene tests | **Yes.** Run each YAML project end to end and check the result. |
| 2 | Global state | Reset it in a pytest fixture; add code to the package where needed. |
| 3 | Randomness | Remove it from `LeafyTree` / `LeafyShrub1` (deterministic rotation, e.g. a fixed seed). |
| 4 | Entry point | Add a callable entry point for tests (no subprocess). |
| 5 | Exceptions | Re-raise where they are swallowed today. |
| 6 | 2D regression | Image comparison of every rendered PNG against a stored golden image. |
| 7 | 3D regression | Per mesh name: primitive count, material (texture name, colour factors, alpha mode, roughness, specular), positions/UVs rounded to ~1e-5. **Disabled in phase 1**: planned changes would force regenerating the golden data repeatedly. |
| 8 | 3D invariants | (a) the run finishes and a `.gltf` exists for every floor plan; (b) every primitive has a material and every texture it uses exists in the output `textures/` folder; (c) POSITION / NORMAL / TEXCOORD_0 counts match, no NaNs, indices in range. |
| 9 | Contract tests | **Yes**, across the registry. |
| 10 | CLI strictness | **Strict everywhere.** A failed glTF export re-raises in the CLI too, so `python -m floor_planner` and `make` exit non-zero. |
| 11 | 2D golden resolution | Scene tests render at **100 dpi** (`run_project` dpi override); the scenes' own `dpi` stays for normal runs. |
| 12 | Tree rotation | Seeded **per anchor point**: varied between trees, stable between runs. |
| 13 | Unit tests | **Not part of this feature.** They are added mostly with new code, and retrofitted case by case when needed. |
| 14 | CI | **None for now** (no GitHub Actions); the suite runs locally. |
| 15 | Scene list | **Explicit list** in `tests/conftest.py`, for flexibility at the start; automatic discovery may come later. |
| 16 | 3D golden scope (phase 2) | **Selected scenes only:** an explicit `GOLDEN_3D_SCENES` list (subset of `SCENES`), extended scene by scene once a scene is stable. Starts with `tests/play_with_textures/face_textures_test.yml` and `face_textures_walls_test.yml`. Replaces the `--golden-3d` switch. |

## Current State

| Topic | Today | Where |
|-------|-------|-------|
| Running a project | only via CLI: `main()` parses arguments, loads YAML, builds elements, renders, exports, writes the report | `floor_planner/__main__.py` |
| Output location | relative to the YAML file (`png_dir`, `visualisation_dir`, `<config>.md`) | `main()` |
| Fatal problems | `WarnMsg()` calls `exit("WARNING: ...")` → `SystemExit`, 21 call sites | `floor_planner/utils.py` |
| glTF export errors | caught per floor plan, printed, not re-raised | `Project.export_to_gltf()` |
| Global state | `Element._element_counter` (never reset; adds `0.0001 × n` to `v_anchor`), `options._id_counters` (reset by `main()`), `options._element_options`, `Group._group_templates`; matplotlib figures are never closed | `elements/element.py`, `options.py`, `elements/foundation/group.py`, `floor_plan.py` |
| Randomness | `LeafyTree` / `LeafyShrub1`: `random.uniform(0, 360)` model rotation; `GardenPath` reseeds the **global** `random` (`random.seed(42/43)`) while drawing | `elements/external/trees.py`, `elements/landscaping/hardscape.py` |
| Scene projects | `tests/<scene>/project_main.yml` (8), `examples/**` (about 20 incl. templates), built by the Makefile | `Makefile` |
| Dependencies | `requirements/base.txt`, `requirements/constraints.txt`; no test dependencies | `requirements/` |
| Git | `tests/**/*.png`, `*.gltf`, `*.bin`, `tests/**/*.md` are ignored | `.gitignore` |

## Design

### Layout

The `tests/` folder already holds the YAML scene projects. The pytest code goes next to them; pytest only collects `test_*.py`, so the scene folders are not affected.

```
tests/
├── conftest.py                 # fixtures, explicit SCENES / GOLDEN_3D_SCENES lists (CLI options: root conftest.py)
├── contract/test_registry.py   # contract tests
├── scenes/test_scenes.py       # scene tests (invariants, 2D golden, 3D golden)
├── scenes/gltf_checks.py       # glTF loading, invariants, summary
├── golden/
│   ├── 2d/<scene_id>/<file>.png
│   └── 3d/<scene_id>/<gltf name>.json   # scenes in GOLDEN_3D_SCENES only
└── <existing scene folders>/project_main.yml
```

`.gitignore` needs `!tests/golden/**` so the golden files are versioned.

### Entry point

Move the body of `main()` into a function that tests can call:

```python
# floor_planner/runner.py (or in __main__.py)
@dataclass
class RunResult:
    project: Project
    png_files: list[Path]
    gltf_files: list[Path]        # one per floor plan, in floor-plan order
    report_file: Path

def run_project(config_path: Path, *, dpi: int | None = None) -> RunResult:
    """dpi: override of the project's dpi for rendered PNGs (scene tests use 100)."""
    ...
```

- `main()` becomes `run_project(Path(cli_args.config_path))`.
- `run_project` starts with `reset_global_state()`, so CLI and tests behave the same.
- To return the produced files, `Project.render_to_png` and `Project.export_to_gltf` return the paths they write. Today they only print them.

### Errors

- **`WarnMsg`** raises a new `FloorPlannerError` that subclasses `SystemExit`. The CLI behaviour is unchanged (message on stderr, exit code 1, not caught by `except Exception`), and tests can use `pytest.raises(FloorPlannerError)`.
- **`Project.export_to_gltf`** re-raises after printing the error, always (no flag). The CLI and `make` then fail with a non-zero exit code when an export fails, instead of reporting success.

### Global state

New `floor_planner/state.py` (or a function in `elements/__init__.py`):

```python
def reset_global_state() -> None:
    Element._element_counter = 0
    options.reset_id_counters()
    options.set_element_options({})
    Group.register_templates({})
    plt.close('all')
```

- An autouse fixture calls it before and after every scene test.
- Pure caches (`rotate_point` `lru_cache`, the per-class `textures` default cache) need no reset.

### Randomness

- **`LeafyTree` / `LeafyShrub1`:** the rotation is seeded per anchor point, through a local generator, e.g. `random.Random(zlib.crc32(repr(anchor_point).encode())).uniform(0, 360)`. Trees still look varied, but the result is reproducible and doesn't depend on which other elements exist or on creation order.
- **`GardenPath`:** use local `random.Random(42)` / `random.Random(43)` instead of reseeding the global generator.

Changing the tree rotation changes the 3D output once; the 3D golden is not active yet.

### Scene list

The scenes are listed explicitly in `tests/conftest.py`. That gives flexibility at the start (add, skip or reorder scenes on purpose). Automatic discovery can come later.

```python
SCENES = [
    "tests/all_elements/project_main.yml",
    "tests/doors_and_windows/doors_and_windows.yml",
    "tests/play_with_doors/project_main.yml",
    # ... the configs the Makefile builds (all, tests, extras)
    "examples/3d_visualization/face_textures_demo.yml",
]
```

- The scene id is the path without the suffix, e.g. `tests/vege/project_main`.
- A contract-style check fails if a listed file does not exist or has no `floor_plans` key, so the list cannot silently go stale.

### Scene test flow

```python
@pytest.mark.slow
@pytest.mark.parametrize("scene", SCENES, ids=scene_id)
def test_scene(scene, tmp_path, golden_options):
    work = copy_scene(scene, tmp_path)               # copy the scene's folder (incl. included files)
    result = run_project(work / scene.name, dpi=100) # any error raises and fails the test
    check_run_invariants(result)                     # (a)
    for gltf in result.gltf_files:
        check_gltf_invariants(gltf)                  # (b), (c)
    problems = [image_vs_golden(png, GOLDEN_2D / scene_id / png.name, update) for png in result.png_files]
    if scene in GOLDEN_3D_SCENES:                    # selected scenes only
        problems += [summary_vs_golden(gltf, GOLDEN_3D / scene_id / f"{gltf.stem}.json", update)
                     for gltf in result.gltf_files]
    # 2D and 3D differences are reported together
```

`copy_scene` copies the scene's whole folder, so relative includes, `png_dir` and `visualisation_dir` all resolve inside `tmp_path`. The repository is never written to.

### 3D invariants

| # | Check |
|---|-------|
| a | `run_project` returns without exception; if `visualisation_dir` is set, `len(gltf_files)` equals the number of floor plans and every file exists, together with its `.bin` |
| b | every primitive has `material` < `len(materials)`; every `baseColorTexture` → image `uri` exists relative to the `.gltf` |
| c | for each primitive, the present attributes among POSITION / NORMAL / TEXCOORD_0 have equal counts; no NaN or inf in them; `max(indices) < POSITION count` |

Accessors are decoded from the `.bin` with numpy (component type, type, byteOffset), as in the comparison script used during the texture work.

### 2D golden comparison

- Scene tests render at 100 dpi (golden images are generated at the same dpi).
- The comparison uses `matplotlib.testing.compare.compare_images(expected, actual, tol)` (RMS difference, default `tol` e.g. 2.0). matplotlib is already a dependency.
- On failure the diff image is kept in the pytest `tmp_path`, and the test message gives its path.
- A missing golden image fails, with a hint to run with `--update-golden`.
- **Platform:** golden images depend on fonts and the matplotlib version. They are generated and checked locally in the same environment (the project's `.venv`, pinned via `requirements/constraints.txt`); there is no CI.

### 3D golden comparison (phase 2)

- **Scope:** only the scenes in `GOLDEN_3D_SCENES` (`tests/conftest.py`), a subset of `SCENES`. A scene is added once it is stable. A contract test checks that every entry is in `SCENES` and has a `visualisation_dir`.
- **Summary per glTF, keyed by node name** (not index, so adding an element doesn't shift the others; node names are unique also for external models, whose meshes are all called `model`). Per node:
  - `world_matrix`: the node's world transform (parent chain composed), only when it is not the identity. It covers the placement of external models and animated doors;
  - per primitive: material (texture file name, `baseColorFactor`, `alphaMode`, `roughnessFactor`, `KHR_materials_specular`, `doubleSided`), number of triangles, and POSITION / TEXCOORD_0 **at every triangle corner** (via the indices, so the summary records which faces each material covers), rounded to 1e-5;
  - primitives with more than 600 corners (detailed external models) are summarized by corner count, bounding box and mean instead.
- **Comparison:** by key, numbers with a tolerance of 2e-5. A failure lists up to 15 differences by path, e.g. `/GenericStorage_x_1/primitives[1]/material/texture: 'a.jpg' != 'b.jpg'` or `.../POSITION: 6 of 18 values differ, max deviation 0.01`. 2D and 3D problems of a scene are reported together.
- **Excluded:** absolute paths (`extras.model_path`), buffer layout, normals, `extras`.
- **Storage:** JSON with nodes in scene order and one vertex per line, so a reviewed diff shows what changed.
- **Third-party models:** scenes that use `models/models_3rd_party` should not be in `GOLDEN_3D_SCENES`; where those models are missing, the stubs are used and the summary differs.

### Options and markers

| Option / marker | Effect |
|-----------------|--------|
| `--update-golden` | write golden files instead of comparing (2D; and 3D for the scenes in `GOLDEN_3D_SCENES`) |
| `--scene <substring>` | run only matching scenes |
| `@pytest.mark.slow` | scene tests; `pytest -m "not slow"` runs contract + unit tests only |

`pytest-xdist` (`pytest -n auto`) runs scenes in parallel. Each worker is its own process, so global state stays per worker, and the reset fixture handles state within one worker.

### Contract tests

Parametrized over `create_elements_registry()`:

| Contract | Rule |
|----------|------|
| No `**kwargs` | no `__init__` of any `ElementBase` subclass has a `VAR_KEYWORD` parameter |
| Common parameters | every registered type takes `id` and `label`; `anchor_point` too, except `line`, `polygon`, `ground_cable` |
| Box textures | every type with the plain `RectangularGeometry3D` box takes `textures` and not `texture_scale` |
| Class defaults | every `_default_textures` passes `FaceTextures.from_yaml` |
| Materials | every 3D-eligible procedural type has `models/procedural/<key>/<key>.mtl` (or is listed as colour-only) |
| Texture references | every `map_Kd` in `models/procedural/**` and `models/<model>/model.mtl` (not `models_3rd_party`) resolves via `find_texture` |
| External models | every `ExternalModelElement` type finds a model folder (including `models/stubs/`) |

### Unit tests

Not part of this feature. They are added mostly together with new code, and retrofitted case by case when there is a need (candidates: `face_textures` resolution, `resolve_element_params`, `wall_openings` face groups, `find_texture`). The layout above leaves room for a `tests/unit/` folder.

## Implementation Plan

### Phase 1: Testability (code changes)
- [x] `FloorPlannerError(SystemExit)`; `WarnMsg` raises it
- [x] `Project.export_to_gltf` re-raises (CLI and `make` fail on export errors); `render_to_png` / `export_to_gltf` return written paths
- [x] `run_project(config_path, dpi=None) -> RunResult`; `main()` uses it
- [x] `reset_global_state()` (element counter, id counters, element options, group templates, `plt.close('all')`); `run_project` calls it
- [x] Rotation seeded per anchor point in `LeafyTree` / `LeafyShrub1`; local RNG in `GardenPath`
- [x] Check that `make all tests extras` still passes and that the 2D outputs are unchanged. Only tree rotations may change in 3D.

### Phase 1: Test suite
- [x] `requirements/dev.txt` (`pytest`, `pytest-xdist`, pinned in `constraints.txt`) and installed in `.venv`
- [x] `pytest.ini` / `[tool.pytest.ini_options]` with markers and `testpaths = ["tests"]`
- [x] `tests/conftest.py`: options, explicit `SCENES` list (+ existence check), `copy_scene`, autouse reset fixture
- [x] `tests/scenes/gltf_checks.py`: accessor decoding, invariants (a)–(c), `gltf_summary()`
- [x] `tests/scenes/test_scenes.py`: scene test at 100 dpi with invariants and 2D golden; 3D golden behind `--golden-3d`
- [x] `tests/contract/test_registry.py`
- [x] `.gitignore`: `!tests/golden/**`; generate the 2D golden images with `--update-golden` and commit them
- [x] Makefile target `check` (`pytest`) and `check-fast` (`pytest -m "not slow"`)
- [x] Run all scenes; fix or document invariant failures found in existing scenes

### Phase 2: 3D golden
- [x] `GOLDEN_3D_SCENES` (explicit subset of `SCENES`) replaces `--golden-3d`; contract check that each entry is in `SCENES` and exports 3D
- [x] Summary keyed by node, with world transform, per-corner geometry, `doubleSided`; compact summary for large primitives; readable JSON writer
- [x] Generate the 3D golden summaries for `tests/play_with_textures/face_textures_test.yml` and `face_textures_walls_test.yml`
- [ ] Add further scenes to `GOLDEN_3D_SCENES` when they are stable

## Implementation Notes (phase 1)

- **Entry point** lives in `floor_planner/runner.py` (`run_project`, `RunResult`, plus the loading helpers moved from `__main__.py`); `__main__.py` only parses arguments.
- **Room list order fixed.** `FloorPlan.draw_report` grouped rooms in a `set`, so the "room areas" list order followed memory addresses and changed between runs (seen in `tests/play_with_doors`). It now keeps the declaration order; without this the 2D golden comparison would fail at random.
- **`copy_scene`** skips generated outputs (`*.png`, `*.pdf`, `*.gltf`, `*.bin`, `*.md`, `camera.json`) and dangling symlinks (e.g. a local `run_3d_walker_simling.sh` in `tests/test_invisible_openings/visualisation_3d/`).
- **`GardenPath`** uses local `random.Random(42/43)`, which produces the same sequence as before, so its 2D pattern is unchanged.
- **Golden images:** 37 PNGs at 100 dpi, 4.7 MB in `tests/golden/2d/`; file names follow the floor-plan titles (they may contain spaces).
- **Speed:** contract tests about 1 s; the full suite with `-n auto` about 8 s.
- **Commands:** `make check` (full suite, `-n auto`), `make check-fast` (`-m "not slow"`); refresh golden images with `python -m pytest -m slow -n auto --update-golden`.
- **New scenes** must be added to `SCENES` in `tests/conftest.py`; a contract test fails for listed files that are missing or have no `floor_plans`.

## Implementation Notes (phase 2)

- **Golden files:** `tests/golden/3d/tests/play_with_textures/face_textures_test/textures_test.json` (27 nodes, about 90 KB) and `.../face_textures_walls_test/textures_walls_test.json` (15 nodes, about 57 KB).
- **Change detection checked** on a copy of `face_textures_test.yml`: a face's texture, opacity, `double_sided`, diffuse, texture scale (UVs only), moving an element by 1 cm, rotating it, and removing it each fail with a message naming the node, primitive and property; an unchanged run passes.
- **All scenes checked:** the summary works for every scene's glTF (world transforms for doors and models, compact summary for large models); the JSON round-trips without differences. All scenes together would be about 1.9 MB of golden data.
- **Adding a scene:** add it to `GOLDEN_3D_SCENES`, run `python -m pytest -m slow --scene <part of path> --update-golden`, review and commit the JSON.

## Testing Strategy (of the suite itself)

- **Each invariant must catch a real failure.** Break a copy of an output on purpose (delete a texture file, drop a material index, put a NaN in POSITION) and check that the matching check fails with a clear message.
- **The 2D golden must catch a real change.** Change one element's colour in a scene copy and check that the comparison fails and writes a diff image.
- **Reset works:** running the same scene twice in one process gives identical outputs.
- **Determinism:** two separate runs give identical 2D PNGs and identical 3D summaries, including trees.
- **The repo stays clean:** `git status` is unchanged after `pytest`.
- **Strict CLI:** a scene with a broken export (e.g. a missing texture) makes `python -m floor_planner -c ...` exit non-zero.

## Open Questions

None. All decisions are recorded in the Decisions table.

## References

- `floor_planner/__main__.py` – `main()`, to be split into `run_project()`
- `floor_planner/project.py` – `render_to_png`, `export_to_gltf`
- `floor_planner/utils.py` – `WarnMsg`
- `floor_planner/options.py`, `elements/element.py`, `elements/foundation/group.py` – global state
- `floor_planner/elements/external/trees.py`, `elements/landscaping/hardscape.py` – randomness
- [fine-grained-textures-for-boxes.md](fine-grained-textures-for-boxes.md) – testing strategy and glTF comparison used there
- `matplotlib.testing.compare.compare_images` – image comparison with tolerance
