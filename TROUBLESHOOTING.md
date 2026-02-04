# Troubleshooting Guide

## Common Issues and Solutions

### 1. "FreeCAD not available" Warning

**What you see:**
```
Warning: FreeCAD not available. Some features will be limited.
```

**What it means:** The script can't find FreeCAD's Python libraries.

**Solutions:**

**macOS:**
```bash
# Check if FreeCAD is installed
ls /Applications/FreeCAD.app

# If not, install it
brew install freecad

# If installed but not found, check the wrapper script
cat cad-3d-cli | grep -A5 "FREECAD_PYTHON"
```

**Linux:**
```bash
# Check installation
which freecad
freecad --version

# If not found, reinstall
sudo apt-get install freecad
```

**Windows:**
- Verify FreeCAD is installed
- Check the path in `cad-3d-cli` matches your installation
- Default is usually `C:\Program Files\FreeCAD 1.0\bin`

---

### 2. "Permission Denied" Error

**What you see:**
```
bash: ./cad-3d-cli: Permission denied
```

**Solution:**
```bash
chmod +x cad-3d-cli
```

---

### 3. "File not found" Error

**What you see:**
```
Error: File not found: model.stl
```

**Solutions:**

**Option A - Use full path:**
```bash
./cad-3d-cli --input /Users/yourname/Downloads/model.stl --output result.stl
```

**Option B - Navigate to the folder first:**
```bash
cd /Users/yourname/Downloads
~/clawd/cad-3d-cli/cad-3d-cli --input model.stl --output result.stl
```

**Option C - Use relative path:**
```bash
./cad-3d-cli --input ./model.stl --output ./result.stl
```

---

### 4. Command Not Found

**What you see:**
```
bash: cad-3d-cli: command not found
```

**Solution:**
```bash
# You're not in the right directory or it's not in PATH

# Option 1: Use full path
~/clawd/cad-3d-cli/cad-3d-cli --help

# Option 2: Navigate to directory
cd ~/clawd/cad-3d-cli
./cad-3d-cli --help

# Option 3: Add to PATH (see INSTALL.md)
```

---

### 5. Python Module Errors

**What you see:**
```
ImportError: No module named 'PIL'
```

**Solution:**
```bash
# Install dependencies
pip install -r requirements.txt

# Or individually
pip install Pillow numpy
```

---

### 6. Generated File is Empty or Corrupted

**What you see:**
- Output file is 0 bytes
- File can't be opened in slicer software

**Solutions:**

1. **Check FreeCAD is working:**
```bash
/Applications/FreeCAD.app/Contents/Resources/bin/python -c "import FreeCAD; print('OK')"
```

2. **Try a simpler command:**
```bash
./cad-3d-cli --prompt "a box" --output test.stl
```

3. **Check output directory exists:**
```bash
mkdir -p ~/clawd/cad-output
./cad-3d-cli --output-dir ~/clawd/cad-output --prompt "a box" --output box.stl
```

---

### 7. Image Processing Not Working

**What you see:**
```
RuntimeError: PIL and numpy are required for image processing
```

**Solution:**
```bash
pip install Pillow numpy
```

---

### 8. Output Format Not Recognized

**What you see:**
- File has wrong extension
- CAD software can't open it

**Solution:**
```bash
# Always specify format if extension is ambiguous
./cad-3d-cli --input model.fcstd --output model --format step

# Or use correct extension
./cad-3d-cli --input model.fcstd --output model.step
```

---

### 9. macOS "App is from unidentified developer"

**What you see:**
Security warning when running for the first time.

**Solution:**
```bash
# Right-click on Terminal and select "Open"
# Or go to System Preferences > Security & Privacy > Allow Anyway

# For the script itself (if needed):
xattr -dr com.apple.quarantine cad-3d-cli
```

---

### 10. Windows PowerShell Execution Policy

**What you see:**
```
ExecutionPolicy prevents running scripts
```

**Solution:**
```powershell
# Run in PowerShell as Administrator
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Or use cmd.exe instead of PowerShell
```

---

## Still Having Issues?

1. **Check your setup:**
```bash
# Verify FreeCAD
ls /Applications/FreeCAD.app  # macOS
which freecad                 # Linux

# Verify Python
python3 --version

# Verify script location
pwd
ls -la cad-3d-cli
```

2. **Run with verbose output:**
```bash
./cad-3d-cli --prompt "a box" --output test.stl --info
```

3. **Open an issue:**
https://github.com/MattSureham/cad-3d-cli/issues

Include:
- Your operating system
- FreeCAD version
- Python version (`python3 --version`)
- Exact command you ran
- Full error message
