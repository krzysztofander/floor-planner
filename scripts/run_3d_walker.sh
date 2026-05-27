#!/bin/bash

# Color codes for better readability
RED='\033[0;31m'
YELLOW='\033[1;33m'
GREEN='\033[0;32m'
NC='\033[0m' # No Color

# Function to print usage help
print_help() {
    echo ""
    echo -e "${GREEN}3D Walker Runner Script${NC}"
    echo -e "${GREEN}========================${NC}"
    echo ""
    echo "This script runs a 3D visualization tool on OBJ files with textures."
    echo ""
    echo -e "${YELLOW}Prerequisites:${NC}"
    echo "  1. Set the WALKER_3D environment variable to point to your 3D viewer executable"
    echo "  2. Place this script in a directory containing:"
    echo "     - At least one .obj file"
    echo "     - A 'textures/' subdirectory with texture files"
    echo ""
    echo -e "${YELLOW}Setup:${NC}"
    echo "  export WALKER_3D=\"/path/to/your/3d/viewer/executable\""
    echo ""
    echo -e "${YELLOW}Usage:${NC}"
    echo "  $0"
    echo ""
    echo -e "${YELLOW}Example:${NC}"
    echo "  export WALKER_3D=\"/usr/local/bin/meshlab\""
    echo "  cd examples/3d_visualization/visualisation_3d"
    echo "  bash ../../../scripts/run_3d_walker.sh"
    echo ""
    echo -e "${YELLOW}What it does:${NC}"
    echo "  - Validates WALKER_3D environment variable"
    echo "  - Finds the first .obj file in the script's directory"
    echo "  - Locates the textures/ folder"
    echo "  - Executes: \$WALKER_3D <obj_file> <textures_folder>"
    echo ""
}

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Check if WALKER_3D environment variable is set
if [ -z "$WALKER_3D" ]; then
    echo -e "${RED}ERROR: WALKER_3D environment variable is not set.${NC}" >&2
    echo -e "${YELLOW}Please set it to point to your 3D viewer executable:${NC}" >&2
    echo -e "  export WALKER_3D=\"/path/to/your/3d/viewer\"" >&2
    print_help
    exit 1
fi

# Check if WALKER_3D points to an executable file
if [ ! -f "$WALKER_3D" ]; then
    echo -e "${RED}ERROR: WALKER_3D does not point to a valid file: $WALKER_3D${NC}" >&2
    echo -e "${YELLOW}Please verify the path and ensure the file exists.${NC}" >&2
    print_help
    exit 1
fi

if [ ! -x "$WALKER_3D" ]; then
    echo -e "${RED}WARNING: WALKER_3D is not executable: $WALKER_3D${NC}" >&2
    echo -e "${YELLOW}Try making it executable with:${NC}" >&2
    echo -e "  chmod +x \"$WALKER_3D\"" >&2
    print_help
    exit 1
fi

# Find .obj file in the script's directory
OBJ_FILE=$(find "$SCRIPT_DIR" -maxdepth 1 -type f -name "*.obj" | head -n 1)

if [ -z "$OBJ_FILE" ]; then
    echo -e "${RED}ERROR: No .obj file found in: $SCRIPT_DIR${NC}" >&2
    echo -e "${YELLOW}Please ensure at least one .obj file exists in the script's directory.${NC}" >&2
    echo -e "${YELLOW}Expected location: $SCRIPT_DIR/*.obj${NC}" >&2
    print_help
    exit 1
fi

# Get the full path to the .obj file
OBJ_PATH="$(cd "$(dirname "$OBJ_FILE")" && pwd)/$(basename "$OBJ_FILE")"

# Check for textures folder
TEXTURES_DIR="$SCRIPT_DIR/textures"

if [ ! -d "$TEXTURES_DIR" ]; then
    echo -e "${RED}ERROR: Textures folder not found: $TEXTURES_DIR${NC}" >&2
    echo -e "${YELLOW}Please ensure a 'textures/' subdirectory exists in the script's directory.${NC}" >&2
    echo -e "${YELLOW}Expected location: $SCRIPT_DIR/textures/${NC}" >&2
    print_help
    exit 1
fi

# Get the full path to the textures directory
# (it must be path to script's directory, not the textures folder itself, 
# since walker expects the second argument to be the base path for textures)
TEXTURES_PATH="$(cd "$SCRIPT_DIR" && pwd)"

# Success - print what we're doing
echo -e "${GREEN}✓ Found WALKER_3D executable: $WALKER_3D${NC}"
echo -e "${GREEN}✓ Found OBJ file: $OBJ_PATH${NC}"
echo -e "${GREEN}✓ Found textures folder: $TEXTURES_PATH${NC}"
echo ""
echo -e "${YELLOW}Executing:${NC} $WALKER_3D \"$OBJ_PATH\" \"$TEXTURES_PATH\""
echo ""

# Execute the 3D walker with the two arguments
exec "$WALKER_3D" "$OBJ_PATH" "$TEXTURES_PATH"
