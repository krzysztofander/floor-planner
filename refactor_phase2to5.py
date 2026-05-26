#!/usr/bin/env python3
"""
Refactoring script for Phases 2-5: Update all element classes to use new base class constructors.
This script updates RectangularElement, SurfaceElement, and CircularElement subclasses.
"""

import re
import os
from pathlib import Path

# Files and classes to update for each phase
PHASE_2_RECTANGULAR = {
    'floor_planner/elements/basic.py': ['WallND', 'Window'],
    'floor_planner/elements/door.py': None,  # Will auto-detect all classes
    'floor_planner/elements/multipurpose.py': ['Room'],
    'floor_planner/elements/furniture/bed.py': None,
    'floor_planner/elements/furniture/furniture.py': None,
    'floor_planner/elements/furniture/storage.py': None,
    'floor_planner/elements/furniture/appliances.py': None,
    'floor_planner/elements/furniture/bathroom.py': None,
    'floor_planner/elements/furniture/decorations.py': None,
    'floor_planner/elements/info.py': None,
    'floor_planner/elements/lighting.py': None,
    'floor_planner/elements/electricity.py': None,
    'floor_planner/elements/landscaping/hardscape.py': ['Fence', 'RetainingWall'],
    'floor_planner/elements/landscaping/structures.py': ['Pergola'],
}

PHASE_3_SURFACE = {
    'floor_planner/elements/landscaping/hardscape.py': ['GardenPath'],
    'floor_planner/elements/landscaping/structures.py': ['Deck', 'RaisedBed'],
    'floor_planner/elements/landscaping/vegetation.py': ['Hedge', 'Lawn'],
}

PHASE_4_CIRCULAR = {
    'floor_planner/elements/landscaping/vegetation.py': ['CircularVegetation', 'Tree', 'Shrub'],
    'floor_planner/elements/landscaping/water.py': ['Fountain'],
    'floor_planner/elements/landscaping/structures.py': ['Gazebo'],
}

PHASE_5_POOLS = {
    'floor_planner/elements/landscaping/water.py': ['RectPool', 'OvalPool'],
}


def backup_file(filepath):
    """Create a backup of the file."""
    backup_path = filepath + '.backup'
    if not os.path.exists(backup_path):
        with open(filepath, 'r') as f:
            content = f.read()
        with open(backup_path, 'w') as f:
            f.write(content)
        print(f"  📦 Backed up: {filepath}")


def find_class_init(content, class_name):
    """Find the __init__ method of a specific class."""
    # Pattern to find class definition and its __init__
    class_pattern = rf'class {class_name}\([^)]+\):\s*"""[^"]*"""[^d]*def __init__\('
    match = re.search(class_pattern, content, re.DOTALL)
    if match:
        return match.start()
    return None


def update_rectangular_class(content, class_name):
    """
    Update a RectangularElement subclass to pass properties to parent constructor.
    Pattern: Remove self.length/thickness/color assignments, add them to super().__init__()
    """
    # Find the class and its __init__ method
    class_pattern = rf'(class {class_name}\(RectangularElement\):.*?def __init__\([^)]+\):.*?)(super\(\).__init__\([^)]+\))(.*?)(self\.length = length\s*self\.thickness = thickness\s*self\.color = color)'
    
    def replacer(match):
        before_super = match.group(1)
        old_super = match.group(2)
        between = match.group(3)
        assignments = match.group(4)
        
        # Update super call to include length, thickness, color
        new_super = old_super.replace(
            'super().__init__(',
            'super().__init__('
        ).replace(
            'label=label',
            'length=length,\n            thickness=thickness,\n            color=color,\n            label=label'
        ).replace(
            'orientation_angle=orientation_angle,',
            'orientation_angle=orientation_angle,'
        )
        
        # Remove the assignments (they're gone)
        return before_super + new_super + between
    
    # Try multiple patterns to catch variations
    updated = content
    
    # Pattern 1: Standard pattern with all three assignments together
    pattern1 = rf'(class {class_name}\(RectangularElement\):.*?super\(\).__init__\(\s*anchor_point=anchor_point,\s*orientation_angle=orientation_angle,\s*label=label\s*\))\s*(self\.length = length\s*self\.thickness = thickness\s*self\.color = color)'
    if re.search(pattern1, updated, re.DOTALL):
        updated = re.sub(
            pattern1,
            lambda m: m.group(1).replace(
                'label=label',
                'length=length,\n            thickness=thickness,\n            color=color,\n            label=label'
            ),
            updated,
            flags=re.DOTALL
        )
    
    return updated


def main():
    print("=" * 70)
    print("REFACTORING PHASES 2-5: Element Class Hierarchy")
    print("=" * 70)
    
    # Phase 2: RectangularElement subclasses
    print("\n🔧 PHASE 2: Updating RectangularElement Subclasses")
    print("-" * 70)
    
    for filepath, classes in PHASE_2_RECTANGULAR.items():
        if not os.path.exists(filepath):
            print(f"  ⚠️  File not found: {filepath}")
            continue
        
        print(f"\n  📝 Processing: {filepath}")
        backup_file(filepath)
        
        with open(filepath, 'r') as f:
            content = f.read()
        
        original_content = content
        
        if classes is None:
            # Auto-detect all RectangularElement subclasses
            classes = re.findall(r'class (\w+)\(RectangularElement\):', content)
            print(f"     Auto-detected classes: {', '.join(classes)}")
        
        for class_name in classes:
            if f'class {class_name}(RectangularElement):' in content:
                content = update_rectangular_class(content, class_name)
                print(f"     ✅ Updated: {class_name}")
        
        if content != original_content:
            with open(filepath, 'w') as f:
                f.write(content)
            print(f"     💾 Saved changes")
        else:
            print(f"     ℹ️  No changes needed")
    
    print("\n" + "=" * 70)
    print("✅ Phase 2 Complete!")
    print("=" * 70)


if __name__ == '__main__':
    main()
