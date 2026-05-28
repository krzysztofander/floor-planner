#!/usr/bin/env python3
"""
Model Validator Tool

Validates external 3D models and their metadata files in the models/ directory.
Checks for:
- Required files existence (model.obj/model.glb + model.transform.json)
- Metadata structure and validity
- Bounding box correctness
- Transform normalization
- File naming conventions

Usage:
    python scripts/validate_models.py
    python scripts/validate_models.py --models-dir=path/to/models
    python scripts/validate_models.py --verbose
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Tuple

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from floor_planner.model_metadata import (
    find_model_metadata,
    load_model_metadata,
    validate_model_metadata,
    ModelMetadata
)


class ValidationResult:
    """Container for validation results."""
    
    def __init__(self, model_dir: Path):
        self.model_dir = model_dir
        self.registry_key = model_dir.name
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


def validate_model_directory(model_dir: Path, verbose: bool = False) -> ValidationResult:
    """
    Validate a single model directory.
    
    Args:
        model_dir: Path to model directory (e.g., models/chair/)
        verbose: Print detailed validation info
    
    Returns:
        ValidationResult with errors and warnings
    """
    result = ValidationResult(model_dir)
    
    if verbose:
        print(f"\nValidating: {model_dir.name}")
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
    
    # Check for model files (OBJ or glTF)
    has_gltf = (model_dir / "model.glb").exists()
    has_obj = (model_dir / "model.obj").exists()
    has_mtl = (model_dir / "model.mtl").exists()
    
    if not has_gltf and not has_obj:
        result.add_error("Missing model file (expected model.glb or model.obj)")
        return result
    
    if has_obj and not has_mtl:
        result.add_warning("model.obj exists but model.mtl is missing (materials may not render)")
    
    if has_gltf and has_obj:
        result.add_warning("Both model.glb and model.obj exist (glTF will be used)")
    
    if verbose:
        print(f"✓ Model files found: ", end="")
        if has_gltf:
            print("model.glb", end="")
        if has_obj:
            print(f"{' + ' if has_gltf else ''}model.obj", end="")
            if has_mtl:
                print(" + model.mtl", end="")
        print()
    
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
        
        # Check model_format matches files
        if metadata.model_format == 'gltf' and not has_gltf:
            result.add_error("Metadata specifies 'gltf' format but model.glb not found")
        elif metadata.model_format == 'obj' and not has_obj:
            result.add_error("Metadata specifies 'obj' format but model.obj not found")
        
        # Check model_file field matches
        expected_file = "model.glb" if has_gltf and not has_obj else "model.obj"
        if metadata.model_file != expected_file:
            result.add_warning(
                f"model_file field is '{metadata.model_file}' but actual file is '{expected_file}'"
            )
        
    except json.JSONDecodeError as e:
        result.add_error(f"Invalid JSON in metadata file: {e}")
    except Exception as e:
        result.add_error(f"Failed to load metadata: {e}")
    
    if verbose and not result.has_issues:
        print("✓ All checks passed!")
    
    return result


def validate_models_directory(models_dir: Path, verbose: bool = False) -> Dict[str, ValidationResult]:
    """
    Validate all model directories in the models folder.
    
    Args:
        models_dir: Path to models/ directory
        verbose: Print detailed validation info
    
    Returns:
        Dict mapping registry_key to ValidationResult
    """
    results = {}
    
    if not models_dir.exists():
        print(f"ERROR: Models directory not found: {models_dir}")
        return results
    
    # Find all subdirectories
    model_dirs = [d for d in models_dir.iterdir() if d.is_dir()]
    
    if not model_dirs:
        print(f"WARNING: No model directories found in {models_dir}")
        return results
    
    print(f"Found {len(model_dirs)} model directories")
    
    for model_dir in sorted(model_dirs):
        result = validate_model_directory(model_dir, verbose)
        results[result.registry_key] = result
    
    return results


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
    
    print(f"\nTotal models: {total}")
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
        for result in sorted(models_with_warnings, key=lambda r: r.registry_key):
            print(f"\n⚠ {result.registry_key}")
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
    
    args = parser.parse_args()
    
    print("External Model Validator")
    print("=" * 70)
    print(f"Models directory: {args.models_dir.absolute()}\n")
    
    # Validate all models
    results = validate_models_directory(args.models_dir, args.verbose)
    
    if not results:
        print("No models found to validate")
        return 1
    
    # Print summary
    print_summary(results)
    
    # Return exit code: 0 if all passed, 1 if any failed
    failed_count = sum(1 for r in results.values() if not r.passed)
    return 0 if failed_count == 0 else 1


if __name__ == '__main__':
    sys.exit(main())
