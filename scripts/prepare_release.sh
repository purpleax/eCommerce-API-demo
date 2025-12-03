#!/bin/bash
set -e

# Run the python bump script
python3 scripts/bump_version.py

# Stage the version change
git add backend/app/main.py

echo "Version bumped and staged."
