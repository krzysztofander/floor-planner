# Floor Planner Utility Scripts

Utility scripts for model validation and 3D visualization.

## Available Scripts

### `validate_models.py` — Model Validator

Validates all external 3D models and their metadata in the `models/` directory and its search subdirectories (`local/`, `models_3rd_party/`, `stubs/`). Exits with code 1 if any error is found, so it can be used as a check after changing models.

**Usage:**
```bash
python scripts/validate_models.py
python scripts/validate_models.py --models-dir=path/to/models
python scripts/validate_models.py --verbose
python scripts/validate_models.py --skip-registry   # only check the model folders
```

Checks:
- Required files exist (model file in loader priority order `model.glb`, `model.gltf`, `model.obj`, `model.dae`, `model.3ds`, plus `model.transform.json`)
- Metadata structure and field validity; `model_format` / `model_file` match the file actually used
- Bounding box correctness
- Registry key matches directory name
- Registry coverage:
  - error if an external-model element's required model is in no search location
  - warning if a model exists only in `local/` or `models_3rd_party/` without a stub in `stubs/`
  - warning for model folders no registered element uses

