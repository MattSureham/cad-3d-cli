# Installation Guide

## Quick Install (Recommended)

### macOS

```bash
# 1. Install FreeCAD
brew install freecad

# 2. Download CAD-3D-CLI
git clone https://github.com/MattSureham/cad-3d-cli.git
cd cad-3d-cli

# 3. Make executable
chmod +x cad-3d-cli

# 4. Test
./cad-3d-cli --prompt "a box" --output test.stl
```

### Linux (Ubuntu/Debian)

```bash
# 1. Install FreeCAD
sudo apt-get update
sudo apt-get install freecad python3-pip

# 2. Download CAD-3D-CLI
git clone https://github.com/MattSureham/cad-3d-cli.git
cd cad-3d-cli

# 3. Install Python dependencies
pip3 install -r requirements.txt

# 4. Make executable
chmod +x cad-3d-cli

# 5. Test
./cad-3d-cli --prompt "a box" --output test.stl
```

### Windows

1. **Install FreeCAD**
   - Download from https://www.freecad.org/downloads.php
   - Run installer
   - Note the installation path (e.g., `C:\Program Files\FreeCAD 1.0`)

2. **Download CAD-3D-CLI**
   ```powershell
   git clone https://github.com/MattSureham/cad-3d-cli.git
   cd cad-3d-cli
   ```

3. **Install Python dependencies**
   ```powershell
   pip install -r requirements.txt
   ```

4. **Edit the wrapper script**
   - Open `cad-3d-cli` in a text editor
   - Find the FreeCAD Python path section
   - Update it to match your FreeCAD installation
   - Save

5. **Test**
   ```powershell
   python src\cad_3d_cli.py --prompt "a box" --output test.stl
   ```

---

## Add to PATH (Optional)

### macOS / Linux

```bash
# Add to PATH temporarily (current session only)
export PATH="$PATH:$(pwd)"

# Or add permanently
echo 'export PATH="$PATH:$HOME/clawd/cad-3d-cli"' >> ~/.zshrc  # macOS
echo 'export PATH="$PATH:$HOME/clawd/cad-3d-cli"' >> ~/.bashrc  # Linux

# Then use from anywhere
cad-3d-cli --prompt "a box" --output box.stl
```

### Windows

```powershell
# Add to PATH permanently (PowerShell as Admin)
[Environment]::SetEnvironmentVariable(
    "Path",
    [Environment]::GetEnvironmentVariable("Path", "User") + ";C:\path\to\cad-3d-cli",
    "User"
)
```

---

## Verify Installation

Run these commands to verify everything works:

```bash
# Check FreeCAD
cad-3d-cli --version

# Test basic generation
cad-3d-cli --prompt "a box" --width 50 --height 30 --depth 20 --output test.stl

# Verify output
ls -lh test.stl
```

If `test.stl` exists and is > 0 bytes, you're good to go! 🎉

---

## Uninstall

```bash
# Just remove the directory
rm -rf ~/clawd/cad-3d-cli

# Remove from PATH (if added)
# Edit ~/.zshrc or ~/.bashrc and remove the export line
```

---

## Troubleshooting

See [README.md#troubleshooting](README.md#troubleshooting) for common issues.
