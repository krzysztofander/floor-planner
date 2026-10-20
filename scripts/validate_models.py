#!/usr/bin/env python3
"""
Model Validator Tool

Validates external 3D models and their metadata files in the models/ directory
and its search subdirectories (local/, models_3rd_party/, stubs/).
Checks for:
- Required files existence (model file + model.transform.json)
- Metadata structure and validity
- Bounding box correctness
- Transform normalization
- File naming conventions
- Every external-model element in the registry has a model (and a stub when the
  real model is kept outside the repository)

Usage:
    python scripts/validate_models.py
    python scripts/validate_models.py --models-dir=path/to/models
    python scripts/validate_models.py --verbose
    python scripts/validate_models.py --skip-registry
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from floor_planner.elements.external_models import ExternalModelElement
from floor_planner.elements.registry import create_elements_registry
from floor_planner.model_metadata import (
    find_model_metadata,
    load_model_metadata,
    validate_model_metadata,
    ModelMetadata
)


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self, model_dir: Path, location: str = ""):
        self.model_dir = model_dir
        self.registry_key = model_dir.name
        # Name used in the report, e.g. "stubs/leafy_tree"
        self.name = f"{location}/{model_dir.name}" if location else model_dir.name
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.passed = True
    
    def add_error(self, message: str):
        """Add critical error."""
        self.errors.append(message)
        self.passed = False
    
    def add_warning(self, message: str):
        """Add non-critical warning."""
        self.warnings.append(message)
    
    @property
    def has_issues(self) -> bool:
        """Check if any errors or warnings exist."""
        return len(self.errors) > 0 or len(self.warnings) > 0


def validate_model_directory(model_dir: Path, verbose: bool = False, location: str = "") -> ValidationResult:
    """
    Validate a single model directory.
    
    Args:
        model_dir: Path to model directory (e.g., models/chair/)
        verbose: Print detailed validation info
        location: Search subdirectory the model is in ("" for the models root)
    
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult(model_dir, location)
    
    if verbose:
        print(f"\nValidating: {result.name}")
        print("=" * 60)
    
    # Check if directory exists
    if not model_dir.exists():
        result.add_error(f"Directory does not exist: {model_dir}")
        return result
    
    # Check for metadata file
    metadata_path = model_dir / "model.transform.json"
    if not metadata_path.exists():
        result.add_error("Missing model.transform.json metadata file")
        return result
    
    # Check for model files, in the same priority order the loader uses
    model_files = [name for name in ExternalModelElement._MODEL_FILE_NAMES if (model_dir / name).exists()]
    has_obj = "model.obj" in model_files
    has_mtl = (model_dir / "model.mtl").exists()
    
    if not model_files:
        result.add_error(
            f"Missing model file (expected one of: {', '.join(ExternalModelElement._MODEL_FILE_NAMES)})"
        )
        return result
    
    used_file = model_files[0]
    
    if has_obj and not has_mtl:
        result.add_warning("model.obj exists but model.mtl is missing (materials may not render)")
    
    if len(model_files) > 1:
        result.add_warning(f"Several model files exist ({', '.join(model_files)}); {used_file} will be used")
    
    if verbose:
        print(f"✓ Model files found: {', '.join(model_files)}" + (" + model.mtl" if has_mtl else ""))
    
    # Load and validate metadata
    try:
        metadata = load_model_metadata(metadata_path)
        
        if verbose:
            print(f"✓ Metadata loaded successfully")
            print(f"  Format: {metadata.model_format}")
            print(f"  Element type: {metadata.element_type}")
            print(f"  Registry key: {metadata.registry_key}")
            print(f"  Dimensions: {metadata.width}m × {metadata.length}m × {metadata.height}m")
        
        # Validate metadata consistency
        warnings = validate_model_metadata(metadata)
        for warning in warnings:
            result.add_warning(f"Metadata: {warning}")
        
        # Check registry key matches directory name
        if metadata.registry_key != model_dir.name:
            result.add_error(
                f"Registry key mismatch: metadata says '{metadata.registry_key}' "
                f"but directory is '{model_dir.name}'"
            )
        
        # Check model_format matches the file that will be used
        format_files = {
            'gltf': ('model.glb', 'model.gltf'),
            'obj': ('model.obj',),
            'dae': ('model.dae',),
            '3ds': ('model.3ds',),
        }
        expected_files = format_files.get(metadata.model_format)
        if expected_files is None:
            result.add_warning(f"Unknown model_format '{metadata.model_format}'")
        elif used_file not in expected_files:
            result.add_error(
                f"Metadata specifies '{metadata.model_format}' format but the model file used is {used_file}"
            )
        
        # Check model_file field matches
        if metadata.model_file != used_file:
            result.add_warning(
                f"model_file field is '{metadata.model_file}' but actual file is '{used_file}'"
            )
        
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON in metadata file: {e}")
    except Exception as e:
        result.add_error(f"Failed to load metadata: {e}")
    
    if verbose and not result.has_issues:
        print("✓ All checks passed!")
    
    return result


def find_model_directories(models_dir: Path) -> list[tuple[str, Path]]:
    """
    Find model directories in the models root and its search subdirectories.
    
    Args:
        models_dir: Path to models/ directory
    
    Returns:
        List of (location, model_dir) pairs; location is "" for the models root
        or the name of the search subdirectory (e.g. "stubs")
    """
    search_subdirs = ExternalModelElement._MODELS_SUBDIRS
    found = []
    for location in ("",) + search_subdirs:
        base_dir = models_dir / location if location else models_dir
        if not base_dir.is_dir():
            continue
        for model_dir in sorted(d for d in base_dir.iterdir() if d.is_dir() and not d.name.startswith('.')):
            # Search subdirectories are containers, not models
            if not location and model_dir.name in search_subdirs:
                continue
            found.append((location, model_dir))
    return found


def validate_models_directory(models_dir: Path, verbose: bool = False) -> Dict[str, ValidationResult]:
    """
    Validate all model directories in the models folder and its search subdirectories.
    
    Args:
        models_dir: Path to models/ directory
        verbose: Print detailed validation info
    
    Returns:
        Dict mapping model name (e.g. "chair", "stubs/chair") to ValidationResult
    """
    results = {}
    
    if not models_dir.exists():
        print(f"ERROR: Models directory not found: {models_dir}")
        return results
    
    model_dirs = find_model_directories(models_dir)
    
    if not model_dirs:
        print(f"WARNING: No model directories found in {models_dir}")
        return results
    
    print(f"Found {len(model_dirs)} model directories")
    
    for location, model_dir in model_dirs:
        result = validate_model_directory(model_dir, verbose, location)
        results[result.name] = result
    
    return results


def validate_registry_coverage(models_dir: Path) -> ValidationResult:
    """
    Check that every external-model element in the registry has a model.
    
    - Error: a required model is found in none of the search locations.
    - Warning: a model exists only outside the repository (local/ or
      models_3rd_party/) and has no placeholder in stubs/.
    - Warning: a model directory does not belong to any registered element.
    
    Args:
        models_dir: Path to models/ directory
    
    Returns:
        ValidationResult named "registry"
    """
    result = ValidationResult(models_dir, "")
    result.name = "registry"
    
    locations = [""] + list(ExternalModelElement._MODELS_SUBDIRS)
    present = {loc: set() for loc in locations}
    for location, model_dir in find_model_directories(models_dir):
        present[location].add(model_dir.name)
    
    known_keys = set()
    for yaml_type, element_class in sorted(create_elements_registry().items()):
        if not (isinstance(element_class, type) and issubclass(element_class, ExternalModelElement)):
            continue
        key = element_class._registry_key
        if key is None:
            result.add_error(f"{yaml_type}: {element_class.__name__} has no _registry_key")
            continue
        known_keys.add(key)
        found_in = [loc or "models" for loc in locations if key in present[loc]]
        if not found_in:
            if element_class._requires_external_model:
                result.add_error(f"{yaml_type}: required model '{key}' not found in any search location")
            continue
        outside_repo = key not in present[""] and key not in present["stubs"]
        if outside_repo:
            result.add_warning(
                f"{yaml_type}: model '{key}' is only in {', '.join(found_in)} and has no stub in stubs/"
            )
    
    for location in locations:
        for key in sorted(present[location] - known_keys):
            result.add_warning(f"Model directory '{location or 'models'}/{key}' is not used by any registered element")
    
    return result


def print_summary(results: Dict[str, ValidationResult]):
    """Print validation summary report."""
    total = len(results)
    passed = sum(1 for r in results.values() if r.passed)
    failed = total - passed
    total_errors = sum(len(r.errors) for r in results.values())
    total_warnings = sum(len(r.warnings) for r in results.values())
    
    print("\n" + "=" * 70)
    print("VALIDATION SUMMARY")
    print("=" * 70)
    
    print(f"\nTotal checked: {total} (model directories + registry coverage)")
    print(f"✓ Passed: {passed}")
    if failed > 0:
        print(f"✗ Failed: {failed}")
    print(f"⚠ Total warnings: {total_warnings}")
    print(f"✗ Total errors: {total_errors}")
    
    # List failed models
    if failed > 0:
        print("\n" + "-" * 70)
        print("FAILED MODELS:")
        print("-" * 70)
        for key, result in sorted(results.items()):
            if not result.passed:
                print(f"\n✗ {key}")
                for error in result.errors:
                    print(f"  ERROR: {error}")
                for warning in result.warnings:
                    print(f"  WARN:  {warning}")
    
    # List warnings even for passed models
    models_with_warnings = [r for r in results.values() if r.passed and r.warnings]
    if models_with_warnings:
        print("\n" + "-" * 70)
        print("WARNINGS:")
        print("-" * 70)
        for result in sorted(models_with_warnings, key=lambda r: r.name):
            print(f"\n⚠ {result.name}")
            for warning in result.warnings:
                print(f"  WARN: {warning}")
    
    print("\n" + "=" * 70)
    if failed == 0 and total_warnings == 0:
        print("✓ ALL MODELS VALID - NO ISSUES FOUND")
    elif failed == 0:
        print(f"✓ ALL MODELS PASSED - {total_warnings} warnings")
    else:
        print(f"✗ VALIDATION FAILED - {failed} models have errors")
    print("=" * 70 + "\n")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Validate external 3D models and metadata",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument(
        '--models-dir',
        type=Path,
        default=Path('models'),
        help='Path to models directory (default: models/)'
    )
    parser.add_argument(
        '-v', '--verbose',
        action='store_true',
        help='Print detailed validation info for each model'
    )
    parser.add_argument(
        '--skip-registry',
        action='store_true',
        help='Do not check the models against the external-model elements in the registry'
    )
    
    args = parser.parse_args()
    
    print("External Model Validator")
    print("=" * 70)
    print(f"Models directory: {args.models_dir.absolute()}\n")
    
    # Validate all models
    results = validate_models_directory(args.models_dir, args.verbose)
    
    if not results:
        print("No models found to validate")
        return 1
    
    if not args.skip_registry:
        results["registry"] = validate_registry_coverage(args.models_dir)
    
    # Print summary
    print_summary(results)
    
    # Return exit code: 0 if all passed, 1 if any failed
    failed_count = sum(1 for r in results.values() if not r.passed)
    return 0 if failed_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
