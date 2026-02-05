# CAD-3D-CLI 🎨🔧

> A simple command-line tool for 3D modeling, perfect for 3D printing and CAD workflows.

Transform text descriptions, images, or existing 3D files into printable models. No GUI needed—just type commands and get results.

[![GitHub](https://img.shields.io/badge/GitHub-MattSureham%2Fcad--3d--cli-blue)](https://github.com/MattSureham/cad-3d-cli)

---

## 📚 Table of Contents

- [Quick Start](#-quick-start-5-minutes)
- [WebUI](#-webui-browser-interface)
- [Features](#-what-can-it-do)
- [Usage Guide](#-usage-guide)
  - [Text to 3D](#1-generate-from-text-easiest)
  - [Dimension Extraction](#-smart-dimension-extraction-auto-detect)
  - [File Conversion](#2-convert-file-formats)
  - [Modify Models](#3-modify-existing-models)
- [Natural Language Examples](#-natural-language-examples)
- [Command Reference](#-command-reference)
- [API Reference](#-api-reference)
- [Examples](#-real-world-examples)
- [Troubleshooting](#-troubleshooting)

---

## ✨ What Can It Do?

| Feature | Description | Example |
|---------|-------------|---------|
| **📝 Text to 3D** | Describe what you want, get a 3D model | `"a box 50x30x20mm"` → STL file |
| **🇨🇳 Chinese Support** | Use Chinese prompts | `"一个盒子"`, `"圆柱体"` |
| **🖼️ Image to 3D** | Convert images to heightmaps | `photo.jpg` → 3D relief |
| **🔄 Convert formats** | Switch between STL, STEP, DXF, FreeCAD | `model.stl` → `model.step` |
| **🛠️ Modify models** | Scale, rotate, move existing models | Scale by 2x, rotate 45° |

---

## 🎯 Quick Reference Card

```bash
# Generate from text (auto-extracts dimensions!)
./cad-3d-cli --prompt "50x30x20 box" --output box.stl
./cad-3d-cli --prompt "直径80高100的圆柱" --output cyl.stl

# Convert formats
./cad-3d-cli --input model.step --output model.stl

# Modify existing
./cad-3d-cli --input model.stl --scale 2 --output bigger.stl
```

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
Download from [freecad.org](https://www.freecad.org/downloads.php)

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

## 🌐 WebUI (Browser Interface)

NEW! CAD-3D-CLI now includes a web-based interface for even easier 3D model creation. No need to remember command syntax—just describe what you want in plain English!

### Starting the WebUI

```bash
# Install dependencies
pip install -r requirements.txt

# Start the web server
python webui.py

# Open your browser to http://localhost:8000
```

### Features

- 📝 **Natural Language Input** - Just type what you want (e.g., "a cube with side length 50mm")
- 🌍 **Multi-language Support** - Works in English and Chinese
- ⚡ **Real-time Parsing** - See how your description is interpreted before generating
- 📥 **Direct Download** - Get your STL/STEP/DXF files immediately
- 📋 **Example Library** - Quick-start templates for common shapes

### Natural Language Examples

| Description | Result |
|-------------|--------|
| `a cube with side length 50mm` | 50×50×50mm cube |
| `a cylinder with diameter 80mm and height 100mm` | 80mm diameter, 100mm tall cylinder |
| `create a box 100mm wide, 60mm high, and 40mm deep` | Custom rectangular box |
| `a hollow tube with outer diameter 60mm` | Hollow cylinder (pipe) |
| `一个直径80高100的圆柱` | Chinese: 80mm diameter, 100mm tall cylinder |
| `50x30x20盒子` | Chinese: 50×30×20mm box |

### Supported Dimension Formats

The WebUI automatically extracts dimensions from various formats:

- **Standard**: `50x30x20` or `50*30*20` or `50,30,20`
- **Labeled**: `width 50 height 30 depth 20`
- **English phrases**: `50mm wide`, `diameter 80mm`
- **Chinese**: `宽50高30深20`, `直径80`
- **Mixed**: `a box 100mm wide by 50mm tall`

### API Endpoints

The WebUI also provides a REST API for integration:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/parse` | POST | Parse natural language into parameters |
| `/api/generate` | POST | Generate model from parameters |
| `/api/examples` | GET | Get example descriptions |
| `/download/{filename}` | GET | Download generated file |

Example API usage:
```bash
curl -X POST http://localhost:8000/api/parse \
  -d "description=a cube 50mm side"

curl -X POST http://localhost:8000/api/generate \
  -d "description=a cylinder 80x100mm" \
  -d "shape=cylinder"
```

---

## 📖 Usage Guide

### 1. Generate from Text (Easiest)

#### 📏 Smart Dimension Extraction (Auto-detect)

**No API key needed!** The tool automatically extracts dimensions from your description:

```bash
# These all work without AI:
./cad-3d-cli --prompt "一个50x30x20的盒子" --output box.stl
./cad-3d-cli --prompt "直径80高100的圆柱" --output cylinder.stl
./cad-3d-cli --prompt "box width 100 height 60 depth 40" --output box.stl
./cad-3d-cli --prompt "a cylinder with diameter 50 and height 80" --output cyl.stl
```

**Supported formats:**
| Format | Example | Description |
|--------|---------|-------------|
| `50x30x20` | `50x30x20` or `50*30*20` or `50,30,20` | Width x Depth x Height |
| Labeled | `width 50 height 30` | Explicit dimension labels |
| 中文格式 | `宽50高30深20` | Chinese labels |
| 2D | `80x100` | Diameter x Height (for cylinders) |
| Mixed | `直径80高100` | Chinese + numbers |

#### 🧠 AI-Powered Generation (Optional)

For even smarter understanding, use `--ai` flag with an API key:

```bash
# Set your API key (one time)
export KIMI_API_KEY="your-api-key"

# Complex descriptions work!
./cad-3d-cli --ai --prompt "a coffee cup with handle, 80mm diameter" --output cup.stl
./cad-3d-cli --ai --prompt "一个带盖子的水杯" --output cup.stl
```

> **Note:** AI mode is optional. Without `--ai`, the tool still extracts dimensions automatically!

#### Basic Keyword Mode (No AI)

For simple shapes without AI:

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

#### 🇨🇳 Chinese Language Support

You can also use Chinese prompts (works in both AI and keyword modes):

```bash
# With AI
./cad-3d-cli --ai --prompt "一个带盖子的水杯，直径60mm，高80mm" --output cup.stl

# Without AI (keywords only)
./cad-3d-cli --prompt "一个盒子" --output box.stl
./cad-3d-cli --prompt "圆柱体" --diameter 30 --height 40 --output cylinder.stl
./cad-3d-cli --prompt "球体" --diameter 50 --output sphere.stl
```

**支持的中文关键词：**
| English | 中文 | Shape |
|---------|------|-------|
| box, cube | 盒子, 立方体, 方块, 长方体 | 长方体 |
| cylinder | 圆柱, 圆柱体, 圆筒 | 圆柱体 |
| sphere, ball | 球, 球体, 圆球 | 球体 |
| cone | 圆锥, 圆锥体, 锥体 | 圆锥体 |
| torus, donut | 圆环, 圆环体, 甜甜圈 | 圆环体 |
| tube, pipe | 管, 管子, 管道, 圆管, 空心管 | 空心圆柱 |

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

## 🗣️ Natural Language Examples

The CLI and WebUI support natural language descriptions. Here are comprehensive examples:

### English Examples

| Natural Language | Parsed Result |
|------------------|---------------|
| `a cube with side length 50mm` | Shape: box, Width: 50, Height: 50, Depth: 50 |
| `a cylinder with diameter 80mm and height 100mm` | Shape: cylinder, Diameter: 80, Height: 100 |
| `create a box 100mm wide, 60mm high, and 40mm deep` | Shape: box, Width: 100, Height: 60, Depth: 40 |
| `a hollow tube with outer diameter 60mm and height 80mm` | Shape: cylinder (hollow), Diameter: 60, Height: 80 |
| `sphere with radius 25mm` | Shape: sphere, Diameter: 50 |
| `a torus with major radius 30 and minor radius 10` | Shape: torus |
| `box 50 by 30 by 20 millimeters` | Shape: box, Width: 50, Depth: 30, Height: 20 |
| `can you make a cylinder 100x200mm` | Shape: cylinder, Diameter: 100, Height: 200 |

### Chinese Examples (中文示例)

| Natural Language | Parsed Result |
|------------------|---------------|
| `一个直径80高100的圆柱` | Shape: cylinder, Diameter: 80, Height: 100 |
| `50x30x20盒子` | Shape: box, Width: 50, Depth: 30, Height: 20 |
| `创建一个宽100高60深40的盒子` | Shape: box, Width: 100, Height: 60, Depth: 40 |
| `空心管外径60高80` | Shape: cylinder (hollow), Diameter: 60, Height: 80 |
| `球体直径50mm` | Shape: sphere, Diameter: 50 |
| `圆锥底面直径30高50` | Shape: cone, Diameter: 30, Height: 50 |

### Supported Dimension Formats

The parser automatically recognizes these formats:

| Format | Example | Description |
|--------|---------|-------------|
| Standard | `50x30x20` | Width × Depth × Height |
| Star | `50*30*20` | Alternative separator |
| Comma | `50,30,20` | CSV-style format |
| Labeled EN | `width 50 height 30` | English labels |
| Labeled CN | `宽50高30深20` | Chinese labels |
| Diameter | `diameter 80 height 100` | For cylinders |
| Diameter CN | `直径80高100` | Chinese cylinder format |
| By-format | `50 by 30 by 20` | Natural language separator |
| Mixed | `100mm wide, 50mm tall` | Mixed units and labels |

---

## 📋 Command Reference

### Input Options (choose one)

| Option | Description | Example |
|--------|-------------|---------|
| `--prompt "text"` | Create from description | `--prompt "a box"` |
| `--ai` | Use AI to parse complex prompts | `--ai --prompt "a cup"` |
| `--input file.stl` | Load existing file | `--input model.stl` |
| `--image photo.jpg` | Convert image to 3D | `--image logo.png` |

### AI Options

| Option | Description | Example |
|--------|-------------|---------|
| `--ai` | Enable AI parsing for complex descriptions | `--ai --prompt "a cup with handle"` |
| `--api-key KEY` | Set API key (or use KIMI_API_KEY env var) | `--api-key sk-xxx` |

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

## 🔌 API Reference

### WebUI REST API

When running the WebUI (`python webui.py`), the following REST API endpoints are available:

#### POST /api/parse

Parse a natural language description into structured parameters.

**Request:**
```bash
curl -X POST http://localhost:8000/api/parse \
  -d "description=a cube with side length 50mm"
```

**Response:**
```json
{
  "success": true,
  "parsed": {
    "shape": "box",
    "width": 50,
    "height": 50,
    "depth": 50,
    "diameter": null,
    "wall_thickness": null
  }
}
```

#### POST /api/generate

Generate a 3D model from parameters.

**Request:**
```bash
curl -X POST http://localhost:8000/api/generate \
  -d "description=a cylinder 80x100mm" \
  -d "shape=cylinder" \
  -d "diameter=80" \
  -d "height=100" \
  -d "output_format=stl"
```

**Response:**
```json
{
  "success": true,
  "filename": "model_20240205_143022.stl",
  "path": "/Users/matthew/clawd/cad-output/model_20240205_143022.stl",
  "params": { ... },
  "download_url": "/download/model_20240205_143022.stl"
}
```

#### GET /api/examples

Get example natural language descriptions.

**Request:**
```bash
curl http://localhost:8000/api/examples
```

**Response:**
```json
{
  "examples": [
    {
      "description": "a cube with side length 50mm",
      "expected_shape": "box",
      "expected_dims": {"width": 50, "height": 50, "depth": 50}
    }
  ]
}
```

#### GET /download/{filename}

Download a generated model file.

**Request:**
```bash
curl http://localhost:8000/download/model_20240205_143022.stl \
  --output model.stl
```

### Python API

Use the CAD3DCLI class directly in your Python code:

```python
from src.cad_3d_cli import CAD3DCLI

# Create instance
cli = CAD3DCLI(output_dir='~/my_models')

# Generate from prompt with natural language
cli.generate_from_prompt("a box 50x30x20mm")
cli.export('box.stl')

# Or use explicit parameters
cli.generate_from_prompt(
    "custom shape",
    shape='cylinder',
    diameter=80,
    height=100
)
cli.export('cylinder.stl')

# Load and modify existing
cli.load_file('existing.stl')
cli.apply_modifications({'scale': 1.5, 'rotate': 45})
cli.export('modified.stl')
```

---

## 💡 Real-World Examples

### Example 1: Quick Box with Dimensions

```bash
# Just type the dimensions in any format!
./cad-3d-cli --prompt "50x30x20 box" --output box.stl
./cad-3d-cli --prompt "盒子 宽50深30高20" --output box.stl
./cad-3d-cli --prompt "box width 50 depth 30 height 20" --output box.stl
```

### Example 2: Cylinder with Auto-extracted Dimensions

```bash
# All these work!
./cad-3d-cli --prompt "直径80高100的圆柱" --output cylinder.stl
./cad-3d-cli --prompt "cylinder 80x100" --output cylinder.stl
./cad-3d-cli --prompt "a cylinder with diameter 80 and height 100" --output cylinder.stl
```

### Example 3: Phone Stand

```bash
./cad-3d-cli --prompt "an L-shaped bracket 70x100x15" \
  --output phone_stand.stl
```

### Example 4: Custom Container

```bash
./cad-3d-cli --prompt "空心管 直径60高80壁厚2" --output container.stl
```

### Example 5: Resize for Different Printers

```bash
# Original model
./cad-3d-cli --input part.stl --info

# Too big? Scale down for mini printer
./cad-3d-cli --input part.stl --scale 0.5 --output part_mini.stl

# Need bigger? Scale up
./cad-3d-cli --input part.stl --scale 2 --output part_large.stl
```

### Example 6: Batch Processing

```bash
# Convert all STEP files to STL
for file in *.step; do
  ./cad-3d-cli --input "$file" --output "${file%.step}.stl"
done
```

---

## 🔧 Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed solutions to common problems.

### Quick Fixes

**"FreeCAD not available"**

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
├── cad-3d-cli              # Main CLI script (run this)
├── webui.py               # WebUI server (NEW!)
├── src/
│   └── cad_3d_cli.py      # Core Python code
├── templates/             # WebUI HTML templates
│   └── index.html         # Main web interface
├── static/                # WebUI static assets
├── tests/                 # Test files
├── requirements.txt       # Python dependencies
├── setup.py              # Installation config
├── README.md             # This file
└── LICENSE               # MIT License
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
