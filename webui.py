#!/usr/bin/env python3
"""
CAD-3D-WebUI: Web Interface for CAD-3D-CLI
Provides a browser-based interface for 3D model generation
"""

import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Optional, Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, Form, File, UploadFile, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# Add src to path for importing cad_3d_cli
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Import the CLI class (without FreeCAD dependencies for web parsing)
from cad_3d_cli import CAD3DCLI

app = FastAPI(
    title="CAD-3D-WebUI",
    description="Web interface for CAD-3D-CLI: Create 3D models from natural language",
    version="1.1.0"
)

# Setup templates and static files
templates_dir = Path(__file__).parent / "templates"
static_dir = Path(__file__).parent / "static"
templates_dir.mkdir(exist_ok=True)
static_dir.mkdir(exist_ok=True)

templates = Jinja2Templates(directory=str(templates_dir))

# Create output directory for generated files
output_dir = Path("~/clawd/cad-output").expanduser()
output_dir.mkdir(parents=True, exist_ok=True)

# Store recent generations
recent_generations: List[Dict[str, Any]] = []
MAX_RECENT = 10


class NaturalLanguageParser:
    """Parse natural language descriptions into structured parameters"""
    
    # Shape keywords mapping
    SHAPES = {
        'box': ['box', 'cube', 'rectangular', 'rectangle', '长方体', '盒子', '立方体', '方块'],
        'cylinder': ['cylinder', 'cylindrical', 'tube', 'pipe', '圆柱', '圆柱体', '圆筒', '管子'],
        'sphere': ['sphere', 'ball', 'spherical', '球', '球体', '圆球'],
        'cone': ['cone', 'conical', '圆锥', '圆锥体', '锥体'],
        'torus': ['torus', 'donut', 'ring', '圆环', '圆环体', '甜甜圈'],
    }
    
    # Dimension patterns
    DIMENSION_PATTERNS = [
        # 50x30x20mm format
        (r'(?:dimensions?\s+)?(\d+\.?\d*)\s*[xX×,\*]\s*(\d+\.?\d*)\s*[xX×,\*]\s*(\d+\.?\d*)\s*(?:mm)?', 'box'),
        # Diameter X Height for cylinders
        (r'(?:diameter|diam|dia)?\s*(\d+\.?\d*)\s*(?:mm)?\s*(?:x|by|\*)\s*(\d+\.?\d*)\s*(?:mm)?', 'cylinder_dims'),
        # Width/Height/Depth labeled
        (r'width\s*(?:of\s*)?(\d+\.?\d*)', 'width'),
        (r'height\s*(?:of\s*)?(\d+\.?\d*)', 'height'),
        (r'depth\s*(?:of\s*)?(\d+\.?\d*)', 'depth'),
        (r'diameter\s*(?:of\s*)?(\d+\.?\d*)', 'diameter'),
        # Side length for cubes
        (r'side\s*(?:length\s*)?(?:of\s*)?(\d+\.?\d*)', 'side'),
        # Radius for spheres
        (r'radius\s*(?:of\s*)?(\d+\.?\d*)', 'radius'),
        # Chinese patterns
        (r'宽\s*(\d+\.?\d*)', 'width'),
        (r'高\s*(\d+\.?\d*)', 'height'),
        (r'深\s*(\d+\.?\d*)', 'depth'),
        (r'长\s*(\d+\.?\d*)', 'length'),
        (r'直径\s*(\d+\.?\d*)', 'diameter'),
    ]
    
    @classmethod
    def parse(cls, description: str) -> Dict[str, Any]:
        """Parse natural language into structured parameters"""
        import re
        
        description_lower = description.lower()
        result = {
            'shape': 'box',  # default
            'width': None,
            'height': None,
            'depth': None,
            'diameter': None,
            'radius': None,
            'wall_thickness': None,
            'description': description,
            'original': description
        }
        
        # Detect shape
        for shape, keywords in cls.SHAPES.items():
            if any(kw in description_lower for kw in keywords):
                result['shape'] = shape
                break
        
        # Extract dimensions using regex patterns
        for pattern, key in cls.DIMENSION_PATTERNS:
            matches = re.findall(pattern, description_lower)
            for match in matches:
                if isinstance(match, tuple):
                    # Multi-value match (like 50x30x20)
                    if key == 'box' and len(match) >= 3:
                        result['width'] = float(match[0])
                        result['depth'] = float(match[1])
                        result['height'] = float(match[2])
                    elif key == 'cylinder_dims' and len(match) >= 2:
                        result['diameter'] = float(match[0])
                        result['height'] = float(match[1])
                else:
                    # Single value match
                    value = float(match)
                    if key == 'side':
                        result['width'] = result['depth'] = result['height'] = value
                    elif key == 'length':
                        result['width'] = value
                    elif key == 'radius':
                        result['radius'] = value
                        result['diameter'] = value * 2
                    else:
                        result[key] = value
        
        # Apply defaults for missing dimensions
        if result['shape'] in ['cylinder', 'sphere']:
            if result['diameter'] is None and result['radius'] is not None:
                result['diameter'] = result['radius'] * 2
            elif result['diameter'] is None:
                result['diameter'] = 50  # default
            if result['height'] is None:
                result['height'] = result['diameter']  # default to diameter for height
        else:
            # Box defaults
            if result['width'] is None:
                result['width'] = 50
            if result['height'] is None:
                result['height'] = 30
            if result['depth'] is None:
                result['depth'] = 20
        
        # Check for hollow/tube features
        if any(kw in description_lower for kw in ['hollow', 'tube', 'pipe', '空心', '管']):
            result['hollow'] = True
            if result['wall_thickness'] is None:
                result['wall_thickness'] = 3  # default
        
        return result


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """Main web interface"""
    return templates.TemplateResponse("index.html", {
        "request": request,
        "recent": recent_generations
    })


@app.post("/api/parse")
async def parse_description(description: str = Form(...)):
    """Parse natural language description and return structured parameters"""
    try:
        result = NaturalLanguageParser.parse(description)
        return JSONResponse(content={
            "success": True,
            "parsed": result
        })
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=400
        )


@app.post("/api/generate")
async def generate_model(
    description: str = Form(...),
    shape: str = Form("box"),
    width: Optional[float] = Form(None),
    height: Optional[float] = Form(None),
    depth: Optional[float] = Form(None),
    diameter: Optional[float] = Form(None),
    output_format: str = Form("stl")
):
    """Generate 3D model from parameters"""
    try:
        # Use parsed values or defaults
        params = NaturalLanguageParser.parse(description)
        
        # Override with explicit form values if provided
        if width is not None:
            params['width'] = width
        if height is not None:
            params['height'] = height
        if depth is not None:
            params['depth'] = depth
        if diameter is not None:
            params['diameter'] = diameter
        if shape:
            params['shape'] = shape
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model_{timestamp}.{output_format}"
        output_path = output_dir / filename
        
        # Build CLI command
        cli_args = ["--prompt", description]
        
        if params.get('width'):
            cli_args.extend(["--width", str(params['width'])])
        if params.get('height'):
            cli_args.extend(["--height", str(params['height'])])
        if params.get('depth'):
            cli_args.extend(["--depth", str(params['depth'])])
        if params.get('diameter'):
            cli_args.extend(["--diameter", str(params['diameter'])])
        if params.get('wall_thickness'):
            cli_args.extend(["--wall-thickness", str(params['wall_thickness'])])
        
        cli_args.extend(["--output", str(output_path)])
        
        # Run CLI (in production, this would be async)
        import subprocess
        cli_script = Path(__file__).parent / "cad-3d-cli"
        
        result_data = {
            "success": True,
            "filename": filename,
            "path": str(output_path),
            "params": params,
            "cli_command": f"./cad-3d-cli {' '.join(cli_args)}",
            "download_url": f"/download/{filename}",
            "timestamp": timestamp
        }
        
        # Add to recent generations
        recent_generations.insert(0, {
            "description": description,
            "filename": filename,
            "params": params,
            "download_url": f"/download/{filename}",
            "timestamp": timestamp
        })
        if len(recent_generations) > MAX_RECENT:
            recent_generations.pop()
        
        return JSONResponse(content=result_data)
        
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@app.post("/api/generate-cli")
async def generate_with_cli(description: str = Form(...)):
    """Generate model by actually running the CLI"""
    try:
        import subprocess
        
        params = NaturalLanguageParser.parse(description)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"model_{timestamp}.stl"
        output_path = output_dir / filename
        
        # Build command
        cmd = [
            str(Path(__file__).parent / "cad-3d-cli"),
            "--prompt", description,
            "--width", str(params.get('width', 50)),
            "--height", str(params.get('height', 30)),
            "--depth", str(params.get('depth', 20)),
            "--diameter", str(params.get('diameter', 25)),
            "--output", str(output_path)
        ]
        
        # Run CLI
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60
        )
        
        if result.returncode == 0 and output_path.exists():
            return JSONResponse(content={
                "success": True,
                "filename": filename,
                "download_url": f"/download/{filename}",
                "output": result.stdout
            })
        else:
            return JSONResponse(
                content={
                    "success": False,
                    "error": result.stderr or "Generation failed",
                    "output": result.stdout
                },
                status_code=500
            )
            
    except Exception as e:
        return JSONResponse(
            content={"success": False, "error": str(e)},
            status_code=500
        )


@app.get("/download/{filename}")
async def download_file(filename: str):
    """Download generated file"""
    file_path = output_dir / filename
    if file_path.exists():
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/octet-stream'
        )
    raise HTTPException(status_code=404, detail="File not found")


@app.get("/api/examples")
async def get_examples():
    """Get example natural language descriptions"""
    return JSONResponse(content={
        "examples": [
            {
                "description": "a cube with side length 50mm",
                "expected_shape": "box",
                "expected_dims": {"width": 50, "height": 50, "depth": 50}
            },
            {
                "description": "a cylinder with diameter 80mm and height 100mm",
                "expected_shape": "cylinder",
                "expected_dims": {"diameter": 80, "height": 100}
            },
            {
                "description": "create a box 100mm wide, 60mm high, and 40mm deep",
                "expected_shape": "box",
                "expected_dims": {"width": 100, "height": 60, "depth": 40}
            },
            {
                "description": "a hollow tube with outer diameter 60mm and height 80mm",
                "expected_shape": "cylinder",
                "expected_dims": {"diameter": 60, "height": 80, "hollow": True}
            },
            {
                "description": "一个直径80高100的圆柱",
                "expected_shape": "cylinder",
                "expected_dims": {"diameter": 80, "height": 100}
            },
            {
                "description": "50x30x20盒子",
                "expected_shape": "box",
                "expected_dims": {"width": 50, "height": 20, "depth": 30}
            }
        ]
    })


@app.get("/api/recent")
async def get_recent():
    """Get recent generations"""
    return JSONResponse(content={"recent": recent_generations})


def create_templates():
    """Create HTML templates if they don't exist"""
    
    index_html = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>CAD-3D-WebUI</title>
    <style>
        * {
            box-sizing: border-box;
            margin: 0;
            padding: 0;
        }
        
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        
        .container {
            max-width: 900px;
            margin: 0 auto;
        }
        
        header {
            text-align: center;
            color: white;
            margin-bottom: 30px;
        }
        
        header h1 {
            font-size: 2.5rem;
            margin-bottom: 10px;
        }
        
        header p {
            opacity: 0.9;
            font-size: 1.1rem;
        }
        
        .card {
            background: white;
            border-radius: 12px;
            padding: 30px;
            margin-bottom: 20px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        }
        
        .input-group {
            margin-bottom: 20px;
        }
        
        label {
            display: block;
            margin-bottom: 8px;
            font-weight: 600;
            color: #333;
        }
        
        input[type="text"], select {
            width: 100%;
            padding: 12px 16px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 1rem;
            transition: border-color 0.3s;
        }
        
        input[type="text"]:focus, select:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .btn {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            padding: 14px 32px;
            border-radius: 8px;
            font-size: 1rem;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4);
        }
        
        .btn:disabled {
            opacity: 0.6;
            cursor: not-allowed;
            transform: none;
        }
        
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
            margin-left: 10px;
        }
        
        .results {
            margin-top: 20px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        
        .results.show {
            display: block;
        }
        
        .results h3 {
            margin-bottom: 15px;
            color: #333;
        }
        
        .param-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
        }
        
        .param-item {
            background: white;
            padding: 12px;
            border-radius: 6px;
            border-left: 3px solid #667eea;
        }
        
        .param-label {
            font-size: 0.85rem;
            color: #666;
            margin-bottom: 4px;
        }
        
        .param-value {
            font-size: 1.2rem;
            font-weight: 600;
            color: #333;
        }
        
        .examples {
            margin-top: 20px;
        }
        
        .example-item {
            background: #f0f4ff;
            padding: 12px 16px;
            border-radius: 6px;
            margin-bottom: 10px;
            cursor: pointer;
            transition: background 0.2s;
            border-left: 3px solid #667eea;
        }
        
        .example-item:hover {
            background: #e0e8ff;
        }
        
        .example-item code {
            font-family: 'Monaco', 'Menlo', monospace;
            font-size: 0.9rem;
            color: #667eea;
        }
        
        .recent-list {
            margin-top: 15px;
        }
        
        .recent-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 12px;
            background: #f8f9fa;
            border-radius: 6px;
            margin-bottom: 8px;
        }
        
        .recent-desc {
            flex: 1;
            color: #333;
        }
        
        .download-link {
            color: #667eea;
            text-decoration: none;
            font-weight: 600;
        }
        
        .download-link:hover {
            text-decoration: underline;
        }
        
        .error {
            background: #ffe6e6;
            color: #d32f2f;
            padding: 12px;
            border-radius: 6px;
            margin-top: 15px;
        }
        
        .success {
            background: #e6f4ea;
            color: #2e7d32;
            padding: 12px;
            border-radius: 6px;
            margin-top: 15px;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid #f3f3f3;
            border-top: 3px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin-left: 10px;
            vertical-align: middle;
        }
        
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
        
        .tabs {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .tab {
            padding: 10px 20px;
            background: #f0f0f0;
            border: none;
            border-radius: 6px;
            cursor: pointer;
            transition: background 0.2s;
        }
        
        .tab.active {
            background: #667eea;
            color: white;
        }
        
        .tab-content {
            display: none;
        }
        
        .tab-content.active {
            display: block;
        }
        
        code {
            background: #f4f4f4;
            padding: 2px 6px;
            border-radius: 3px;
            font-family: 'Monaco', monospace;
            font-size: 0.9em;
        }
        
        pre {
            background: #2d2d2d;
            color: #f8f8f2;
            padding: 15px;
            border-radius: 6px;
            overflow-x: auto;
            margin-top: 10px;
        }
    </style>
</head>
<body>
    <div class="container">
        <header>
            <h1>🎨 CAD-3D-WebUI</h1>
            <p>Create 3D models using natural language. No complex commands needed!</p>
        </header>
        
        <div class="card">
            <div class="tabs">
                <button class="tab active" onclick="showTab('natural')">Natural Language</button>
                <button class="tab" onclick="showTab('manual')">Manual Parameters</button>
                <button class="tab" onclick="showTab('api')">API Reference</button>
            </div>
            
            <div id="natural" class="tab-content active">
                <div class="input-group">
                    <label for="description">Describe what you want to create:</label>
                    <input type="text" id="description" 
                           placeholder="e.g., a cube with side length 50mm or 直径80高100的圆柱"
                           onkeypress="if(event.key==='Enter') parseAndGenerate()">
                </div>
                
                <div style="margin-bottom: 20px;">
                    <button class="btn" onclick="parseAndGenerate()" id="generateBtn">
                        Generate Model
                    </button>
                    <button class="btn btn-secondary" onclick="parseOnly()">Preview Parse</button>
                </div>
                
                <div id="message"></div>
                
                <div id="results" class="results">
                    <h3>Parsed Parameters</h3>
                    <div class="param-grid" id="paramGrid"></div>
                    <div id="cliCommand"></div>
                </div>
                
                <div class="examples">
                    <h3>💡 Try these examples:</h3>
                    <div class="example-item" onclick="setDescription('a cube with side length 50mm')">
                        <code>a cube with side length 50mm</code>
                    </div>
                    <div class="example-item" onclick="setDescription('a cylinder with diameter 80mm and height 100mm')">
                        <code>a cylinder with diameter 80mm and height 100mm</code>
                    </div>
                    <div class="example-item" onclick="setDescription('create a box 100mm wide, 60mm high, and 40mm deep')">
                        <code>create a box 100mm wide, 60mm high, and 40mm deep</code>
                    </div>
                    <div class="example-item" onclick="setDescription('a hollow tube with outer diameter 60mm')">
                        <code>a hollow tube with outer diameter 60mm</code>
                    </div>
                    <div class="example-item" onclick="setDescription('一个直径80高100的圆柱')">
                        <code>一个直径80高100的圆柱</code> 🇨🇳
                    </div>
                    <div class="example-item" onclick="setDescription('50x30x20盒子')">
                        <code>50x30x20盒子</code> 🇨🇳
                    </div>
                </div>
            </div>
            
            <div id="manual" class="tab-content">
                <form id="manualForm" onsubmit="generateManual(event)">
                    <div class="input-group">
                        <label for="m_description">Description:</label>
                        <input type="text" id="m_description" placeholder="Brief description">
                    </div>
                    
                    <div class="input-group">
                        <label for="m_shape">Shape:</label>
                        <select id="m_shape">
                            <option value="box">Box / Cube</option>
                            <option value="cylinder">Cylinder</option>
                            <option value="sphere">Sphere</option>
                            <option value="cone">Cone</option>
                            <option value="torus">Torus (Donut)</option>
                        </select>
                    </div>
                    
                    <div class="param-grid">
                        <div class="input-group">
                            <label for="m_width">Width (mm):</label>
                            <input type="number" id="m_width" value="50" step="0.1">
                        </div>
                        <div class="input-group">
                            <label for="m_height">Height (mm):</label>
                            <input type="number" id="m_height" value="30" step="0.1">
                        </div>
                        <div class="input-group">
                            <label for="m_depth">Depth (mm):</label>
                            <input type="number" id="m_depth" value="20" step="0.1">
                        </div>
                        <div class="input-group">
                            <label for="m_diameter">Diameter (mm):</label>
                            <input type="number" id="m_diameter" value="50" step="0.1">
                        </div>
                    </div>
                    
                    <div class="input-group">
                        <label for="m_format">Output Format:</label>
                        <select id="m_format">
                            <option value="stl">STL (3D Printing)</option>
                            <option value="step">STEP (CAD)</option>
                            <option value="dxf">DXF (2D Drawing)</option>
                        </select>
                    </div>
                    
                    <button type="submit" class="btn">Generate Model</button>
                </form>
            </div>
            
            <div id="api" class="tab-content">
                <h3>API Endpoints</h3>
                
                <h4>POST /api/parse</h4>
                <p>Parse natural language description into structured parameters.</p>
                <pre>curl -X POST http://localhost:8000/api/parse \\
  -d "description=a cube 50mm side"</pre>
                
                <h4>POST /api/generate</h4>
                <p>Generate a 3D model from parsed parameters.</p>
                <pre>curl -X POST http://localhost:8000/api/generate \\
  -d "description=a cylinder 80x100mm" \\
  -d "shape=cylinder" \\
  -d "diameter=80" \\
  -d "height=100"</pre>
                
                <h4>GET /api/examples</h4>
                <p>Get example natural language descriptions.</p>
                <pre>curl http://localhost:8000/api/examples</pre>
                
                <h4>GET /download/{filename}</h4>
                <p>Download a generated model file.</p>
            </div>
        </div>
        
        <div class="card">
            <h2>📁 Recent Generations</h2>
            <div class="recent-list" id="recentList">
                {% if recent %}
                    {% for item in recent %}
                    <div class="recent-item">
                        <span class="recent-desc">{{ item.description }}</span>
                        <a href="{{ item.download_url }}" class="download-link" download>Download {{ item.filename }}</a>
                    </div>
                    {% endfor %}
                {% else %}
                    <p style="color: #666;">No recent generations yet.</p>
                {% endif %}
            </div>
        </div>
        
        <div class="card">
            <h2>ℹ️ About</h2>
            <p>CAD-3D-WebUI provides a natural language interface for 3D modeling. Instead of memorizing command syntax, just describe what you want!</p>
            <p style="margin-top: 15px;"><strong>Supported formats:</strong> STL, STEP, DXF</p>
            <p><strong>Languages:</strong> English, Chinese</p>
        </div>
    </div>
    
    <script>
        function showTab(tabName) {
            // Hide all tabs
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            
            // Show selected tab
            document.getElementById(tabName).classList.add('active');
            event.target.classList.add('active');
        }
        
        function setDescription(text) {
            document.getElementById('description').value = text;
            document.getElementById('description').focus();
        }
        
        async function parseOnly() {
            const description = document.getElementById('description').value;
            if (!description) {
                showMessage('Please enter a description', 'error');
                return;
            }
            
            showLoading(true);
            
            try {
                const response = await fetch('/api/parse', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `description=${encodeURIComponent(description)}`
                });
                
                const data = await response.json();
                showLoading(false);
                
                if (data.success) {
                    showParsedParams(data.parsed);
                    showMessage('Parameters parsed successfully! Click "Generate Model" to create the file.', 'success');
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
            } catch (err) {
                showLoading(false);
                showMessage('Error: ' + err.message, 'error');
            }
        }
        
        async function parseAndGenerate() {
            const description = document.getElementById('description').value;
            if (!description) {
                showMessage('Please enter a description', 'error');
                return;
            }
            
            showLoading(true);
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/x-www-form-urlencoded'},
                    body: `description=${encodeURIComponent(description)}`
                });
                
                const data = await response.json();
                showLoading(false);
                
                if (data.success) {
                    showParsedParams(data.params);
                    showMessage(`✅ Model generated! <a href="${data.download_url}" class="download-link" download>Download ${data.filename}</a>`, 'success');
                    addToRecent(description, data.filename, data.download_url);
                } else {
                    showMessage('Error: ' + data.error, 'error');
                }
            } catch (err) {
                showLoading(false);
                showMessage('Error: ' + err.message, 'error');
            }
        }
        
        function showParsedParams(params) {
            const grid = document.getElementById('paramGrid');
            grid.innerHTML = '';
            
            const displayParams = ['shape', 'width', 'height', 'depth', 'diameter', 'wall_thickness'];
            
            displayParams.forEach(key => {
                if (params[key] !== null && params[key] !== undefined) {
                    const div = document.createElement('div');
                    div.className = 'param-item';
                    div.innerHTML = `
                        <div class="param-label">${key.charAt(0).toUpperCase() + key.slice(1)}</div>
                        <div class="param-value">${params[key]}</div>
                    `;
                    grid.appendChild(div);
                }
            });
            
            document.getElementById('results').classList.add('show');
        }
        
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.innerHTML = text;
            msg.className = type;
        }
        
        function showLoading(show) {
            const btn = document.getElementById('generateBtn');
            if (show) {
                btn.disabled = true;
                btn.innerHTML = 'Processing<span class="loading"></span>';
            } else {
                btn.disabled = false;
                btn.innerHTML = 'Generate Model';
            }
        }
        
        function addToRecent(description, filename, downloadUrl) {
            const list = document.getElementById('recentList');
            const item = document.createElement('div');
            item.className = 'recent-item';
            item.innerHTML = `
                <span class="recent-desc">${description}</span>
                <a href="${downloadUrl}" class="download-link" download>Download ${filename}</a>
            `;
            list.insertBefore(item, list.firstChild);
        }
        
        async function generateManual(e) {
            e.preventDefault();
            
            const params = new URLSearchParams();
            params.append('description', document.getElementById('m_description').value || 'manual');
            params.append('shape', document.getElementById('m_shape').value);
            params.append('width', document.getElementById('m_width').value);
            params.append('height', document.getElementById('m_height').value);
            params.append('depth', document.getElementById('m_depth').value);
            params.append('diameter', document.getElementById('m_diameter').value);
            params.append('output_format', document.getElementById('m_format').value);
            
            try {
                const response = await fetch('/api/generate', {
                    method: 'POST',
                    body: params
                });
                
                const data = await response.json();
                
                if (data.success) {
                    alert('Model generated! Click OK to download.');
                    window.location.href = data.download_url;
                } else {
                    alert('Error: ' + data.error);
                }
            } catch (err) {
                alert('Error: ' + err.message);
            }
        }
    </script>
</body>
</html>
'''
    
    (templates_dir / "index.html").write_text(index_html)
    print(f"Created template: {templates_dir / 'index.html'}")


def main():
    """Run the web server"""
    # Create templates if they don't exist
    if not (templates_dir / "index.html").exists():
        create_templates()
    
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '127.0.0.1')
    
    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                  CAD-3D-WebUI v1.1.0                        ║
╠══════════════════════════════════════════════════════════════╣
║  🌐 Web Interface: http://{host}:{port}                      ║
║                                                              ║
║  Features:                                                   ║
║  • Natural language 3D model generation                     ║
║  • Multi-language support (English, Chinese)                ║
║  • Real-time parameter parsing                              ║
║  • Direct file download                                     ║
║                                                              ║
║  Press Ctrl+C to stop                                       ║
╚══════════════════════════════════════════════════════════════╝
""")
    
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    main()
