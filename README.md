# CAD-3D-CLI

A command-line 3D modeling tool for 3D printing and CAD workflows. Generate, modify, and convert 3D models using text prompts, images, or existing 3D files.

## Features

- 📝 **Text-to-3D**: Generate models from natural language descriptions
- 🖼️ **Image-to-3D**: Create heightmaps and 3D models from images
- 🔄 **Format Conversion**: Convert between STL, STEP, DXF, and FreeCAD formats
- 🛠️ **Model Modification**: Scale, rotate, and translate existing models
- 📐 **Parametric Design**: Adjust dimensions and parameters
- 🖨️ **3D Print Ready**: Export optimized STL files for 3D printing

## Supported Formats

### Input
- STL (.stl)
- STEP (.step, .stp)
- DXF (.dxf)
- FreeCAD (.fcstd, .fcstd1)
- OBJ (.obj)
- PLY (.ply)
- Images (.jpg, .png) - for heightmap generation

### Output
- STL (.stl) - for 3D printing
- STEP (.step, .stp) - for CAD software
- DXF (.dxf) - for 2D drawings
- FreeCAD (.fcstd) - for parametric editing
- PNG (.png) - rendered images

## Installation

### Prerequisites

- Python 3.8+
- FreeCAD 0.20+ (for full functionality)
- pip

### Install FreeCAD

```bash
# macOS
brew install freecad

# Ubuntu/Debian
sudo apt-get install freecad

# Windows
# Download from https://www.freecadweb.org/downloads.php
```

### Install CAD-3D-CLI

```bash
# Clone repository
git clone https://github.com/matthew/cad-3d-cli.git
cd cad-3d-cli

# Install dependencies
pip install -r requirements.txt

# Make executable
chmod +x cad-3d-cli

# Optional: Add to PATH
sudo ln -s $(pwd)/cad-3d-cli /usr/local/bin/
```

## Usage

### Generate from Text Prompt

```bash
# Simple box
cad-3d-cli --prompt "a box 50x30x20mm"

# Cylinder
cad-3d-cli --prompt "a cylinder" --diameter 25 --height 40

# Sphere
cad-3d-cli --prompt "a sphere" --diameter 30

# Hollow tube
cad-3d-cli --prompt "a hollow tube" --diameter 30 --height 50 --wall-thickness 3
```

### Process Image to 3D

```bash
# Convert image to heightmap
cad-3d-cli --image photo.jpg --output heightmap.stl

# Adjust height scale
cad-3d-cli --image photo.jpg --height-scale 20 --output heightmap.stl
```

### Convert Between Formats

```bash
# STL to STEP
cad-3d-cli --input model.stl --output model.step

# FreeCAD to STL
cad-3d-cli --input model.fcstd --output model.stl

# Multiple formats
cad-3d-cli --input model.fcstd --output model.step
cad-3d-cli --input model.fcstd --output model.dxf
```

### Modify Existing Models

```bash
# Scale model
cad-3d-cli --input model.stl --scale 1.5 --output model_scaled.stl

# Rotate model
cad-3d-cli --input model.stl --rotate 90 --output model_rotated.stl

# Translate model
cad-3d-cli --input model.stl --translate "10,20,0" --output model_moved.stl

# Combined operations
cad-3d-cli --input model.stl --scale 2 --rotate 45 --output model_modified.stl
```

### Get Model Info

```bash
cad-3d-cli --input model.stl --info
```

## CLI Reference

```
cad-3d-cli [OPTIONS]

Input Options:
  --prompt, -p TEXT      Generate from text description
  --input, -i PATH       Load existing 3D file
  --image PATH           Process image to 3D heightmap

Output Options:
  --output, -o PATH      Output file path
  --format, -f FORMAT    Output format (stl, step, dxf, fcstd, png)

Generation Parameters:
  --width FLOAT          Width in mm (default: 50)
  --height FLOAT         Height in mm (default: 30)
  --depth FLOAT          Depth in mm (default: 20)
  --diameter FLOAT       Diameter in mm (default: 25)
  --wall-thickness FLOAT Wall thickness for hollow shapes (default: 3)

Modification Options:
  --scale FLOAT          Scale factor
  --rotate FLOAT         Rotation angle in degrees
  --translate "X,Y,Z"    Translation as x,y,z

Other Options:
  --output-dir PATH      Output directory
  --info                 Show model information
  --render               Render to image
  --version              Show version
  --help                 Show help
```

## Examples

### Example 1: Generate a Custom Bracket

```bash
cad-3d-cli --prompt "an L-shaped bracket" \
           --width 60 --height 40 --depth 20 \
           --output bracket.stl
```

### Example 2: Convert and Scale

```bash
cad-3d-cli --input part.step \
           --scale 0.5 \
           --output part_scaled.stl
```

### Example 3: Image to 3D Print

```bash
# Convert logo to 3D printable badge
cad-3d-cli --image logo.png \
           --height-scale 5 \
           --output badge.stl
```

## API Usage

You can also use CAD-3D-CLI as a Python library:

```python
from cad_3d_cli import CAD3DCLI

# Initialize
cli = CAD3DCLI(output_dir='~/my_models')

# Generate from prompt
cli.generate_from_prompt(
    "a cylindrical container",
    diameter=50,
    height=80,
    wall_thickness=2
)

# Export
cli.export('container.stl')

# Load and modify
cli.load_file('existing_model.stl')
cli.apply_modifications({'scale': 1.5})
cli.export('model_scaled.step')
```

## Development

### Running Tests

```bash
cd cad-3d-cli
python -m pytest tests/
```

### Project Structure

```
cad-3d-cli/
├── src/
│   └── cad_3d_cli.py      # Main CLI module
├── tests/
│   └── test_cli.py        # Unit tests
├── examples/               # Example models
├── docs/                   # Documentation
├── cad-3d-cli             # Shell wrapper
├── requirements.txt       # Python dependencies
├── setup.py              # Package setup
└── README.md             # This file
```

## Requirements

- Python 3.8+
- FreeCAD 0.20+ (optional, for full functionality)
- NumPy
- Pillow

## License

MIT License - See LICENSE file

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Acknowledgments

- Built with [FreeCAD](https://www.freecadweb.org/) Python API
- Inspired by the need for simple CLI-based 3D modeling
