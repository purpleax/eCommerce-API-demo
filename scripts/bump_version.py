#!/usr/bin/env python3
import re
import sys
from pathlib import Path

def bump_version(file_path):
    content = file_path.read_text()
    
    # Regex to find version="X.Y.Z"
    pattern = r'version="(\d+)\.(\d+)\.(\d+)"'
    match = re.search(pattern, content)
    
    if not match:
        print(f"Error: Could not find version string in {file_path}")
        sys.exit(1)
        
    major, minor, patch = map(int, match.groups())
    new_version = f"{major}.{minor}.{patch + 1}"
    
    print(f"Bumping version: {major}.{minor}.{patch} -> {new_version}")
    
    new_content = re.sub(pattern, f'version="{new_version}"', content)
    file_path.write_text(new_content)
    return new_version

if __name__ == "__main__":
    backend_main = Path(__file__).parents[1] / "backend" / "app" / "main.py"
    if not backend_main.exists():
        print("Error: backend/app/main.py not found")
        sys.exit(1)
        
    bump_version(backend_main)
