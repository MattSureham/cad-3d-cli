# CAD-3D-CLI 🎨🔧

> A simple command-line tool for 3D modeling, perfect for 3D printing and CAD workflows.

Transform text descriptions, images, or existing 3D files into printable models. No GUI needed—just type commands and get results.

[![GitHub](https://img.shields.io/badge/GitHub-MattSureham%2Fcad--3d--cli-blue)](https://github.com/MattSureham/cad-3d-cli)

---

## ✨ What Can It Do?

| Feature | Description | Example |
|---------|-------------|---------|
| **📝 Text to 3D** | Describe what you want, get a 3D model | `"a box 50x30x20mm"` → STL file |
| **🖼️ Image to 3D** | Convert images to heightmaps | `photo.jpg` → 3D relief |
| **🔄 Convert formats** | Switch between STL, STEP, DXF, FreeCAD | `model.stl` → `model.step` |
| **🛠️ Modify models** | Scale, rotate, move existing models | Scale by 2x, rotate 45° |

---

## 🚀 Quick Start (5 minutes)

### Step 1: Install FreeCAD

FreeCAD powers the 3D operations. Install it first:

**macOS:**
```bash
brew install freecad
```

**Ubuntu/Debian:**
```bash
sudo apt-get install freecad
```

**Windows:**
Download from [freecadweb.org](https://www.freecadweb.org/downloads.php)

### Step 2: Download CAD-3D-CLI

```bash
# Clone the repository
git clone https://github.com/MattSureham/cad-3d-cli.git
cd cad-3d-cli

# Make it executable
chmod +x cad-3d-cli
```

### Step 3: Test It

```bash
# Generate a simple box
./cad-3d-cli --prompt "a box" --width 50 --height 30 --depth 20 --output mybox.stl

# Check if file was created
ls -lh mybox.stl
```

✅ **Success!** You now have `mybox.stl` ready for 3D printing.

---

## 📖 Usage Guide

### 1. Generate from Text (Easiest)

Describe what you want using simple shapes:

```bash
# Basic shapes - just describe it!
./cad-3d-cli --prompt "a box" --output box.stl
./cad-3d-cli --prompt "a cylinder" --diameter 25 --height 40 --output cylinder.stl
./cad-3d-cli --prompt "a sphere" --diameter 30 --output sphere.stl

# Custom dimensions
./cad-3d-cli --prompt "a box" --width 100 --height 50 --depth 20 --output custom_box.stl

# Hollow objects (tubes, containers)
./cad-3d-cli --prompt "a hollow tube" --diameter 30 --height 50 --wall-thickness 3 --output tube.stl
```

**Supported shapes in prompts:**
- `box`, `cube` → Rectangular box
- `cylinder` → Cylinder
- `sphere` → Sphere
- `cone` → Cone
- `torus` → Donut shape
- `tube`, `pipe` → Hollow cylinder

### 2. Convert File Formats

Have a file in one format? Convert it to another:

```bash
# STL (printing) → STEP (CAD software)
./cad-3d-cli --input model.stl --output model.step

# STEP → STL for printing
./cad-3d-cli --input model.step --output model.stl

# FreeCAD → STL
./cad-3d-cli --input design.fcstd --output design.stl

# To 2D DXF
./cad-3d-cli --input model.stl --output drawing.dxf
```

### 3. Modify Existing Models

```bash
# Make it bigger (2x size)
./cad-3d-cli --input model.stl --scale 2 --output bigger.stl

# Make it smaller (half size)
./cad-3d-cli --input model.stl --scale 0.5 --output smaller.stl

# Rotate 90 degrees
./cad-3d-cli --input model.stl --rotate 90 --output rotated.stl

# Move it (translate X,Y,Z)
./cad-3d-cli --input model.stl --translate "10,0,5" --output moved.stl

# Combine operations
./cad-3d-cli --input model.stl --scale 1.5 --rotate 45 --output final.stl
```

### 4. Convert Images to 3D

Turn a photo or logo into a 3D printable relief:

```bash
# Simple conversion
./cad-3d-cli --image photo.jpg --output relief.stl

# Control the height (taller = more 3D effect)
./cad-3d-cli --image logo.png --height-scale 10 --output logo_3d.stl

# Limit detail for faster printing
./cad-3d-cli --image photo.jpg --max-size 50 --output simple.stl
```

### 5. Get Model Information

```bash
# See details about any 3D file
./cad-3d-cli --input model.stl --info
```

Output shows:
- Object names and types
- Volume (mm³)
- Surface area (mm²)
- Bounding box dimensions

---

## 📋 Command Reference

### Input Options (choose one)

| Option | Description | Example |
|--------|-------------|---------|
| `--prompt "text"` | Create from description | `--prompt "a box"` |
| `--input file.stl` | Load existing file | `--input model.stl` |
| `--image photo.jpg` | Convert image to 3D | `--image logo.png` |

### Output Options

| Option | Description | Example |
|--------|-------------|---------|
| `--output file.stl` | Where to save | `--output result.stl` |
| `--format stl` | Force format | `--format step` |

### Size Parameters

| Option | Default | Description |
|--------|---------|-------------|
| `--width` | 50 | Width in mm |
| `--height` | 30 | Height in mm |
| `--depth` | 20 | Depth in mm |
| `--diameter` | 25 | Diameter in mm |
| `--wall-thickness` | 3 | For hollow objects |

### Modifications

| Option | Example | Description |
|--------|---------|-------------|
| `--scale` | `--scale 2` | Size multiplier (2 = 2x bigger) |
| `--rotate` | `--rotate 90` | Degrees to rotate |
| `--translate` | `--translate "10,0,5"` | Move X,Y,Z mm |

### Other Options

| Option | Description |
|--------|-------------|
| `--info` | Show model details |
| `--output-dir ~/models` | Set default save location |
| `--help` | Show all options |
| `--version` | Show version |

---

## 💡 Real-World Examples

### Example 1: Phone Stand

```bash
./cad-3d-cli --prompt "an L-shaped bracket" \
  --width 70 --height 100 --depth 15 \
  --output phone_stand.stl
```

### Example 2: Resize for Different Printers

```bash
# Original model
./cad-3d-cli --input part.stl --info

# Too big? Scale down for mini printer
./cad-3d-cli --input part.stl --scale 0.5 --output part_mini.stl

# Need bigger? Scale up
./cad-3d-cli --input part.stl --scale 2 --output part_large.stl
```

### Example 3: Batch Processing

```bash
# Convert all STEP files to STL
for file in *.step; do
  ./cad-3d-cli --input "$file" --output "${file%.step}.stl"
done
```

### Example 4: Create a Custom Container

```bash
./cad-3d-cli --prompt "a hollow tube" \
  --diameter 60 --height 80 --wall-thickness 2 \
  --output container.stl
```

---

## 🔧 Troubleshooting

### "FreeCAD not available"

**Problem:** FreeCAD isn't installed or found.

**Solution:**
```bash
# macOS
brew install freecad

# Verify installation
ls /Applications/FreeCAD.app
```

### "File not found"

**Problem:** Input file path is wrong.

**Solution:** Use full path or check current directory:
```bash
# Use full path
./cad-3d-cli --input /Users/you/Downloads/model.stl --output result.stl

# Or navigate there first
cd /Users/you/Downloads
~/clawd/cad-3d-cli/cad-3d-cli --input model.stl --output result.stl
```

### Permission Denied

**Problem:** Script isn't executable.

**Solution:**
```bash
chmod +x cad-3d-cli
```

### "No API key found for provider"

**Problem:** Trying to use models that need API keys.

**Solution:** This tool uses local FreeCAD—no API keys needed! Just make sure FreeCAD is installed.

---

## 🏗️ Project Structure

```
cad-3d-cli/
├── cad-3d-cli              # Main script (run this)
├── src/
│   └── cad_3d_cli.py      # Core Python code
├── tests/                  # Test files
├── requirements.txt        # Python dependencies
├── setup.py               # Installation config
├── README.md              # This file
└── LICENSE                # MIT License
```

---

## 🐍 Python API

Use in your own Python scripts:

```python
from cad_3d_cli import CAD3DCLI

# Create instance
cli = CAD3DCLI(output_dir='~/my_models')

# Generate a box
cli.generate_from_prompt("a box", width=50, height=30, depth=20)
cli.export('box.stl')

# Load and modify
cli.load_file('existing.stl')
cli.apply_modifications({'scale': 1.5, 'rotate': 45})
cli.export('modified.stl')
```

---

## 🤝 Contributing

1. Fork it: `https://github.com/MattSureham/cad-3d-cli/fork`
2. Create your feature branch: `git checkout -b my-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin my-feature`
5. Submit a pull request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) file

---

## 🙏 Acknowledgments

- Built with [FreeCAD](https://www.freecadweb.org/) Python API
- Created for makers and engineers who prefer the command line

---

**Happy modeling!** 🎨🔧

Questions? Open an issue on GitHub: https://github.com/MattSureham/cad-3d-cli/issues
