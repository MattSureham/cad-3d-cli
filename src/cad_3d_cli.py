#!/usr/bin/env python3
"""
CAD-3D-CLI: 3D Modeling Tool for 3D Printing and CAD
Supports prompts, images, and 3D file inputs
Outputs: STL, STEP, DXF, FreeCAD

Author: Matthew
Repository: https://github.com/matthew/cad-3d-cli
"""

import argparse
import os
import sys
import json
import tempfile
from pathlib import Path
from typing import Optional, List, Dict, Any

# FreeCAD imports (will be available when running with FreeCAD Python)
try:
    import FreeCAD
    import Part
    import Mesh
    import Import
    FREECAD_AVAILABLE = True
except ImportError:
    FREECAD_AVAILABLE = False
    print("Warning: FreeCAD not available. Some features will be limited.")

# Optional imports for image processing
try:
    from PIL import Image
    import numpy as np
    IMAGE_PROCESSING_AVAILABLE = True
except ImportError:
    IMAGE_PROCESSING_AVAILABLE = False

# Optional imports for AI parsing
try:
    import urllib.request
    import urllib.error
    AI_AVAILABLE = True
except ImportError:
    AI_AVAILABLE = False

# Import for dimension extraction
import re


class CAD3DCLI:
    """Main CLI class for 3D modeling operations"""
    
    VERSION = "1.0.0"
    SUPPORTED_INPUTS = ['.stl', '.step', '.stp', '.dxf', '.fcstd', '.fcstd1', '.obj', '.ply']
    SUPPORTED_OUTPUTS = ['.stl', '.step', '.stp', '.dxf', '.fcstd', '.png']
    
    def __init__(self, output_dir: Optional[str] = None, api_key: Optional[str] = None):
        self.output_dir = Path(output_dir or os.environ.get('CAD_OUTPUT_DIR', '~/clawd/cad-output'))
        self.output_dir = self.output_dir.expanduser().resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.doc = None
        self.api_key = api_key or os.environ.get('KIMI_API_KEY')
    
    def extract_dimensions(self, prompt: str) -> Dict[str, Optional[float]]:
        """Extract dimensions from text description using regex patterns.
        
        Supports formats like:
        - "50x30x20" or "50*30*20" or "50,30,20"
        - "50mm x 30mm x 20mm"
        - "直径80高100" or "diameter 80 height 100"
        - "宽50深30高20" or "width 50 depth 30 height 20"
        - "50 by 30 by 20"
        
        Returns dict with keys: width, height, depth, diameter
        """
        dimensions = {
            'width': None,
            'height': None,
            'depth': None,
            'diameter': None
        }
        
        # Pattern 1: 50x30x20 or 50*30*20 or 50,30,20 (most common)
        # Matches: number (separator) number (separator) number
        pattern_3d = r'(\d+\.?\d*)\s*[xX*×,]\s*(\d+\.?\d*)\s*[xX*×,]\s*(\d+\.?\d*)\s*(?:mm)?'
        match = re.search(pattern_3d, prompt)
        if match:
            dims = [float(match.group(i)) for i in range(1, 4)]
            # Try to determine which is which based on context
            if any(kw in prompt.lower() for kw in ['diameter', 'diam', '直径', ' Φ', ' phi', 'φ']):
                # For cylinders: diameter x height (x wall_thickness optionally)
                dimensions['diameter'] = dims[0]
                dimensions['height'] = dims[1]
                # dims[2] could be wall thickness if hollow
            else:
                # For boxes: width x depth x height
                dimensions['width'] = dims[0]
                dimensions['depth'] = dims[1]
                dimensions['height'] = dims[2]
            return dimensions
        
        # Pattern 2: Explicit labels - width/height/depth
        # English: width 50, height 30, depth 20
        patterns_en = {
            'width': r'width\s*(\d+\.?\d*)',
            'height': r'height\s*(\d+\.?\d*)',
            'depth': r'depth\s*(\d+\.?\d*)',
            'diameter': r'diameter\s*(\d+\.?\d*)',
        }
        
        for dim_name, pattern in patterns_en.items():
            match = re.search(pattern, prompt, re.IGNORECASE)
            if match:
                dimensions[dim_name] = float(match.group(1))
        
        # Chinese patterns - separate to handle Chinese characters correctly
        patterns_cn = {
            'width': r'(?:宽|长度|长)\s*(\d+\.?\d*)',
            'height': r'(?:高|高度)\s*(\d+\.?\d*)',
            'depth': r'(?:深|厚度|厚)\s*(\d+\.?\d*)',
            'diameter': r'(?:直径|Φ|phi|φ)\s*(\d+\.?\d*)',
        }
        
        for dim_name, pattern in patterns_cn.items():
            if dimensions[dim_name] is None:  # Only if not already found
                match = re.search(pattern, prompt)
                if match:
                    dimensions[dim_name] = float(match.group(1))
        
        # Pattern 3: "50 by 30 by 20" or "50乘30乘20"
        pattern_by = r'(\d+\.?\d*)\s*(?:by|乘|\*)\s*(\d+\.?\d*)\s*(?:by|乘|\*)\s*(\d+\.?\d*)'
        match = re.search(pattern_by, prompt, re.IGNORECASE)
        if match and not any(dimensions.values()):  # Only if no explicit labels found
            dims = [float(match.group(i)) for i in range(1, 4)]
            dimensions['width'] = dims[0]
            dimensions['depth'] = dims[1]
            dimensions['height'] = dims[2]
        
        # Pattern 4: Single dimension for simple shapes
        # "直径50" or "diameter 50" or "50mm diameter"
        if not dimensions['diameter']:
            pattern_single_diam = r'(?:^|\s)(\d+\.?\d*)\s*(?:mm)?\s*(?:diameter|diam|直径)'
            match = re.search(pattern_single_diam, prompt, re.IGNORECASE)
            if match:
                dimensions['diameter'] = float(match.group(1))
            else:
                pattern_single_diam2 = r'(?:diameter|diam|直径)\s*(\d+\.?\d*)'
                match = re.search(pattern_single_diam2, prompt, re.IGNORECASE)
                if match:
                    dimensions['diameter'] = float(match.group(1))
        
        # Pattern 5: Two dimensions (diameter x height for cylinders)
        pattern_2d = r'(\d+\.?\d*)\s*[xX*×,]\s*(\d+\.?\d*)\s*(?:mm)?'
        match = re.search(pattern_2d, prompt)
        if match and not any(dimensions.values()):
            dims = [float(match.group(1)), float(match.group(2))]
            if any(kw in prompt.lower() for kw in ['cylinder', 'cyl', '圆柱', '圆筒', '管', 'tube']):
                dimensions['diameter'] = dims[0]
                dimensions['height'] = dims[1]
            else:
                dimensions['width'] = dims[0]
                dimensions['height'] = dims[1]
        
        return dimensions
    
    def parse_with_ai(self, prompt: str) -> Dict[str, Any]:
        """Use AI to parse complex descriptions into structured parameters"""
        if not AI_AVAILABLE:
            raise RuntimeError("urllib is required for AI parsing")
        if not self.api_key:
            raise RuntimeError("KIMI_API_KEY not set. Use --api-key or set environment variable.")
        
        system_prompt = """You are a CAD model parser. Extract structured information from user descriptions.

Return ONLY a JSON object with this structure:
{
    "shape": "box|cylinder|sphere|cone|torus|tube|custom",
    "description": "brief description of what to create",
    "dimensions": {
        "width": number or null,
        "height": number or null,
        "depth": number or null,
        "diameter": number or null,
        "radius": number or null
    },
    "features": ["list", "of", "features", "like", "hollow", "fillet", "chamfer"],
    "wall_thickness": number or null,
    "notes": "any additional notes for the designer"
}

Rules:
- Extract all numeric dimensions mentioned (in mm)
- If shape is unclear, use "custom"
- For Chinese input, understand context and map to appropriate shapes
- Common mappings:
  - 杯子/水杯/容器 → cylinder with hollow
  - 支架/支撑 → bracket (custom)
  - 盒子/箱子 → box
  - 管/管道 → tube
  - 球/圆球 → sphere
"""

        try:
            import ssl
            
            # Create SSL context that works on macOS
            ssl_context = ssl.create_default_context()
            ssl_context.check_hostname = False
            ssl_context.verify_mode = ssl.CERT_NONE
            
            # API endpoint - can be overridden via environment variable
            api_endpoint = os.environ.get('KIMI_API_URL', 'https://api.moonshot.cn/v1/chat/completions')
            model_name = os.environ.get('KIMI_MODEL', 'kimi-k2-0905-preview')
            
            req = urllib.request.Request(
                api_endpoint,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                data=json.dumps({
                    "model": model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                }).encode('utf-8'),
                method="POST"
            )
            
            with urllib.request.urlopen(req, timeout=30, context=ssl_context) as response:
                data = json.loads(response.read().decode('utf-8'))
                content = data['choices'][0]['message']['content']
                return json.loads(content)
                
        except Exception as e:
            print(f"AI parsing failed: {e}", file=sys.stderr)
            return {
                "shape": "box",
                "description": prompt,
                "dimensions": {},
                "features": [],
                "notes": "AI parsing failed, using defaults"
            }
    
    def create_document(self, name: str = "Model") -> Any:
        """Create a new FreeCAD document"""
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for this operation")
        self.doc = FreeCAD.newDocument(name)
        return self.doc
    
    def load_file(self, filepath: str) -> Any:
        """Load a 3D file (STL, STEP, DXF, FreeCAD)"""
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for loading files")
        
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        ext = path.suffix.lower()
        
        if ext in ['.fcstd', '.fcstd1']:
            self.doc = FreeCAD.open(str(path))
        elif ext in ['.step', '.stp']:
            self.doc = FreeCAD.newDocument("Imported")
            Import.insert(str(path), self.doc.Name)
        elif ext == '.stl':
            self.doc = FreeCAD.newDocument("Imported")
            Mesh.insert(str(path), self.doc.Name)
        elif ext == '.dxf':
            self.doc = FreeCAD.newDocument("Imported")
            Import.insert(str(path), self.doc.Name)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
        
        return self.doc
    
    def generate_from_prompt(self, prompt: str, use_ai: bool = False, **params) -> Any:
        """Generate 3D model from text description"""
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for model generation")
        
        self.doc = FreeCAD.newDocument("Generated")
        
        # Extract dimensions from prompt text first (works in both modes)
        print("📏 Extracting dimensions from text...")
        extracted_dims = self.extract_dimensions(prompt)
        print(f"Extracted: {extracted_dims}")
        
        # Merge extracted dimensions with provided params (provided params take precedence)
        width = params.get('width') or extracted_dims.get('width') or 50
        height = params.get('height') or extracted_dims.get('height') or 30
        depth = params.get('depth') or extracted_dims.get('depth') or 20
        diameter = params.get('diameter') or extracted_dims.get('diameter') or 25
        
        # If AI mode enabled, use AI to enhance parsing
        if use_ai and self.api_key:
            print("🧠 Using AI to parse your description...")
            ai_params = self.parse_with_ai(prompt)
            print(f"AI parsed: {ai_params}")
            
            # Override with AI dimensions if they exist
            ai_dims = ai_params.get('dimensions', {})
            if ai_dims.get('width'):
                width = ai_dims['width']
            if ai_dims.get('height'):
                height = ai_dims['height']
            if ai_dims.get('depth'):
                depth = ai_dims['depth']
            if ai_dims.get('diameter'):
                diameter = ai_dims['diameter']
            
            # Create params dict for shape creation
            shape_params = {
                'width': width,
                'height': height,
                'depth': depth,
                'diameter': diameter,
                'radius1': params.get('radius1', diameter/2),
                'radius2': params.get('radius2', diameter/4),
                'major_radius': params.get('major_radius', 30),
                'minor_radius': params.get('minor_radius', 10),
                'wall_thickness': params.get('wall_thickness', 3)
            }
            
            # Check for hollow feature
            features = ai_params.get('features', [])
            if 'hollow' in features and ai_params.get('wall_thickness'):
                shape_params['wall_thickness'] = ai_params['wall_thickness']
            
            # Use AI-determined shape
            shape_type = ai_params.get('shape', 'box')
            shape = self._create_shape(shape_type, shape_params)
            
            if shape:
                obj = self.doc.addObject("Part::Feature", "Shape")
                obj.Shape = shape
                self.doc.recompute()
                
                # Add AI notes as comment
                if 'notes' in ai_params and ai_params['notes']:
                    print(f"💡 AI Note: {ai_params['notes']}")
                
                return self.doc
        
        # Use extracted dimensions for keyword-based parsing
        prompt_lower = prompt.lower()
        
        # Remove dimension params from params dict to avoid duplication
        shape_params = {
            'width': width,
            'height': height,
            'depth': depth,
            'diameter': diameter,
            'radius1': params.get('radius1', diameter/2),
            'radius2': params.get('radius2', diameter/4),
            'major_radius': params.get('major_radius', 30),
            'minor_radius': params.get('minor_radius', 10),
            'wall_thickness': params.get('wall_thickness', 3)
        }
        
        shape = self._create_shape_from_keywords(prompt_lower, shape_params)
        
        if shape:
            obj = self.doc.addObject("Part::Feature", "Shape")
            obj.Shape = shape
            self.doc.recompute()
        
        return self.doc
    
    def _create_shape(self, shape_type: str, params: dict):
        """Create a shape based on type"""
        width = params.get('width', 50)
        height = params.get('height', 30)
        depth = params.get('depth', 20)
        diameter = params.get('diameter', 25)
        
        if shape_type == 'box':
            return Part.makeBox(width, depth, height)
        elif shape_type == 'cylinder':
            return Part.makeCylinder(diameter/2, height)
        elif shape_type == 'sphere':
            return Part.makeSphere(diameter/2)
        elif shape_type == 'cone':
            radius1 = params.get('radius1', diameter/2)
            radius2 = params.get('radius2', diameter/4)
            return Part.makeCone(radius1, radius2, height)
        elif shape_type == 'torus':
            radius1 = params.get('major_radius', 30)
            radius2 = params.get('minor_radius', 10)
            return Part.makeTorus(radius1, radius2)
        elif shape_type in ['tube', 'pipe']:
            outer_radius = diameter / 2
            inner_radius = outer_radius - params.get('wall_thickness', 3)
            outer_cyl = Part.makeCylinder(outer_radius, height)
            inner_cyl = Part.makeCylinder(inner_radius, height)
            return outer_cyl.cut(inner_cyl)
        else:
            return Part.makeBox(width, depth, height)
    
    def _create_shape_from_keywords(self, prompt_lower: str, params: dict):
        """Create shape based on keyword matching (supports English and Chinese)"""
        width = params.get('width', 50)
        height = params.get('height', 30)
        depth = params.get('depth', 20)
        diameter = params.get('diameter', 25)
        
        # Box / Cube - English: box, cube | Chinese: 盒子, 立方体, 方块, 长方体
        if any(kw in prompt_lower for kw in ['box', 'cube', '盒子', '立方体', '方块', '长方体']):
            return Part.makeBox(width, depth, height)
        
        # Cylinder - English: cylinder | Chinese: 圆柱, 圆柱体, 圆筒
        elif any(kw in prompt_lower for kw in ['cylinder', '圆柱', '圆柱体', '圆筒']):
            return Part.makeCylinder(diameter/2, height)
        
        # Sphere - English: sphere, ball | Chinese: 球, 球体, 圆球
        elif any(kw in prompt_lower for kw in ['sphere', 'ball', '球', '球体', '圆球']):
            return Part.makeSphere(diameter/2)
        
        # Cone - English: cone | Chinese: 圆锥, 圆锥体, 锥体
        elif any(kw in prompt_lower for kw in ['cone', '圆锥', '圆锥体', '锥体']):
            radius1 = params.get('radius1', diameter/2)
            radius2 = params.get('radius2', diameter/4)
            return Part.makeCone(radius1, radius2, height)
        
        # Torus - English: torus, donut | Chinese: 圆环, 圆环体, 甜甜圈
        elif any(kw in prompt_lower for kw in ['torus', 'donut', '圆环', '圆环体', '甜甜圈']):
            radius1 = params.get('major_radius', 30)
            radius2 = params.get('minor_radius', 10)
            return Part.makeTorus(radius1, radius2)
        
        # Tube / Pipe - English: tube, pipe | Chinese: 管, 管子, 管道, 圆管, 空心管, 空心
        elif any(kw in prompt_lower for kw in ['tube', 'pipe', '管', '管子', '管道', '圆管', '空心管', '空心圆柱']):
            outer_radius = diameter / 2
            inner_radius = outer_radius - params.get('wall_thickness', 3)
            outer_cyl = Part.makeCylinder(outer_radius, height)
            inner_cyl = Part.makeCylinder(inner_radius, height)
            return outer_cyl.cut(inner_cyl)
        
        else:
            # Default to box
            return Part.makeBox(width, depth, height)
        
        if shape:
            obj = self.doc.addObject("Part::Feature", "Shape")
            obj.Shape = shape
            self.doc.recompute()
        
        return self.doc
    
    def process_image(self, image_path: str, **params) -> Any:
        """Process image to generate 3D model (heightmap approach)"""
        if not IMAGE_PROCESSING_AVAILABLE:
            raise RuntimeError("PIL and numpy are required for image processing")
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for 3D generation")
        
        # Load and convert image to grayscale
        img = Image.open(image_path).convert('L')
        
        # Resize if too large
        max_size = params.get('max_size', 100)
        img.thumbnail((max_size, max_size))
        
        # Convert to numpy array
        array = np.array(img)
        
        # Normalize to height values
        height_scale = params.get('height_scale', 10)
        heights = (array / 255.0) * height_scale
        
        self.doc = FreeCAD.newDocument("Heightmap")
        
        # Create mesh from heightmap
        # This is a simplified version - creates a point cloud then mesh
        mesh = Mesh.Mesh()
        
        rows, cols = heights.shape
        scale = params.get('scale', 1.0)
        
        points = []
        for i in range(rows):
            for j in range(cols):
                x = j * scale
                y = i * scale
                z = heights[i, j]
                points.append(FreeCAD.Vector(x, y, z))
        
        # Create simple mesh from points (simplified)
        # For production, use more sophisticated mesh generation
        mesh.addFacet(points[0], points[1], points[2])
        
        mesh_obj = self.doc.addObject("Mesh::Feature", "HeightmapMesh")
        mesh_obj.Mesh = mesh
        self.doc.recompute()
        
        return self.doc
    
    def apply_modifications(self, modifications: Dict[str, Any]):
        """Apply modifications to current model"""
        if not self.doc:
            raise RuntimeError("No document loaded")
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for modifications")
        
        for obj in self.doc.Objects:
            if hasattr(obj, 'Shape'):
                shape = obj.Shape
                
                # Apply scaling
                if 'scale' in modifications:
                    s = modifications['scale']
                    if isinstance(s, (int, float)):
                        s = (s, s, s)
                    shape = shape.scale(*s)
                
                # Apply rotation
                if 'rotate' in modifications:
                    angle = modifications['rotate']
                    axis = modifications.get('rotate_axis', (0, 0, 1))
                    shape = shape.rotate(FreeCAD.Vector(0, 0, 0), 
                                        FreeCAD.Vector(*axis), angle)
                
                # Apply translation
                if 'translate' in modifications:
                    t = modifications['translate']
                    shape = shape.translate(FreeCAD.Vector(*t))
                
                obj.Shape = shape
        
        self.doc.recompute()
    
    def export(self, output_path: str, format: Optional[str] = None) -> str:
        """Export model to specified format"""
        if not self.doc:
            raise RuntimeError("No document to export")
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for export")
        
        path = Path(output_path)
        
        if format:
            path = path.with_suffix(format)
        
        ext = path.suffix.lower()
        
        if ext == '.stl':
            # Export as STL (mesh)
            mesh_objs = [obj for obj in self.doc.Objects if obj.TypeId.startswith('Mesh::')]
            part_objs = [obj for obj in self.doc.Objects if obj.TypeId.startswith('Part::')]
            
            if mesh_objs:
                mesh = mesh_objs[0].Mesh
            elif part_objs:
                shape = part_objs[0].Shape
                mesh = Mesh.Mesh(shape.tessellate(0.1))
            else:
                raise RuntimeError("No exportable objects found")
            
            mesh.write(str(path))
            
        elif ext in ['.step', '.stp']:
            # Export as STEP
            Import.export(self.doc.Objects, str(path))
            
        elif ext == '.dxf':
            # Export as DXF
            Import.export(self.doc.Objects, str(path))
            
        elif ext in ['.fcstd', '.fcstd1']:
            # Save as FreeCAD document
            self.doc.saveAs(str(path))
            
        elif ext == '.png':
            # Render to image
            self.render(str(path))
            
        else:
            raise ValueError(f"Unsupported export format: {ext}")
        
        return str(path)
    
    def render(self, output_path: str, width: int = 800, height: int = 600):
        """Render model to image"""
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for rendering")
        
        # Note: This is a placeholder for actual rendering
        # FreeCAD's rendering requires Gui which may not be available in CLI mode
        print(f"Rendering to {output_path}...")
        print("Note: Full rendering requires FreeCAD GUI mode")
        
    def get_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        if not self.doc:
            return {}
        
        info = {
            'name': self.doc.Name,
            'objects': [],
            'file_path': str(self.doc.FileName) if self.doc.FileName else None
        }
        
        for obj in self.doc.Objects:
            obj_info = {
                'name': obj.Name,
                'label': obj.Label,
                'type': obj.TypeId
            }
            
            if hasattr(obj, 'Shape'):
                shape = obj.Shape
                obj_info['volume'] = shape.Volume
                obj_info['surface_area'] = shape.Area
                obj_info['bounds'] = {
                    'x': [shape.BoundBox.XMin, shape.BoundBox.XMax],
                    'y': [shape.BoundBox.YMin, shape.BoundBox.YMax],
                    'z': [shape.BoundBox.ZMin, shape.BoundBox.ZMax]
                }
            
            info['objects'].append(obj_info)
        
        return info


def main():
    parser = argparse.ArgumentParser(
        description='CAD-3D-CLI: 3D Modeling Tool for 3D Printing and CAD',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate from prompt
  cad-3d-cli --prompt "a box 50x30x20mm"
  
  # Load and modify existing file
  cad-3d-cli --input model.stl --scale 1.5 --output model_scaled.stl
  
  # Process image to 3D heightmap
  cad-3d-cli --image photo.jpg --output heightmap.stl
  
  # Export to different formats
  cad-3d-cli --input model.fcstd --output model.step
  cad-3d-cli --input model.fcstd --output model.dxf
        """
    )
    
    parser.add_argument('--version', action='version', version=f'%(prog)s {CAD3DCLI.VERSION}')
    
    # Input options
    input_group = parser.add_mutually_exclusive_group()
    input_group.add_argument('--prompt', '-p', type=str, help='Text description of the model')
    input_group.add_argument('--input', '-i', type=str, help='Input 3D file path')
    input_group.add_argument('--image', type=str, help='Input image for heightmap generation')
    
    # Output options
    parser.add_argument('--output', '-o', type=str, help='Output file path')
    parser.add_argument('--format', '-f', type=str, choices=['stl', 'step', 'stp', 'dxf', 'fcstd', 'png'],
                       help='Output format (if not specified from output path)')
    
    # Generation parameters
    parser.add_argument('--width', type=float, default=50, help='Width in mm')
    parser.add_argument('--height', type=float, default=30, help='Height in mm')
    parser.add_argument('--depth', type=float, default=20, help='Depth in mm')
    parser.add_argument('--diameter', type=float, default=25, help='Diameter in mm')
    parser.add_argument('--wall-thickness', type=float, default=3, help='Wall thickness for hollow shapes')
    
    # Modification options
    parser.add_argument('--scale', type=float, help='Scale factor')
    parser.add_argument('--rotate', type=float, help='Rotation angle in degrees')
    parser.add_argument('--translate', type=str, help='Translation as x,y,z')
    
    # AI options
    parser.add_argument('--ai', action='store_true', help='Use AI to parse complex prompts (requires API key)')
    parser.add_argument('--api-key', type=str, help='API key for AI parsing (or set KIMI_API_KEY env var)')
    
    # Other options
    parser.add_argument('--output-dir', type=str, help='Output directory')
    parser.add_argument('--info', action='store_true', help='Show model info')
    parser.add_argument('--render', action='store_true', help='Render to image')
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = CAD3DCLI(output_dir=args.output_dir, api_key=args.api_key)
    
    try:
        # Handle input
        if args.prompt:
            print(f"Generating model from prompt: '{args.prompt}'")
            cli.generate_from_prompt(
                args.prompt,
                use_ai=args.ai,
                width=args.width,
                height=args.height,
                depth=args.depth,
                diameter=args.diameter,
                wall_thickness=args.wall_thickness
            )
            
        elif args.input:
            print(f"Loading file: {args.input}")
            cli.load_file(args.input)
            
        elif args.image:
            print(f"Processing image: {args.image}")
            cli.process_image(args.image)
            
        else:
            parser.print_help()
            return 1
        
        # Apply modifications
        modifications = {}
        if args.scale:
            modifications['scale'] = args.scale
        if args.rotate:
            modifications['rotate'] = args.rotate
        if args.translate:
            modifications['translate'] = [float(x) for x in args.translate.split(',')]
        
        if modifications:
            print("Applying modifications...")
            cli.apply_modifications(modifications)
        
        # Show info
        if args.info:
            info = cli.get_info()
            print(json.dumps(info, indent=2))
        
        # Export
        if args.output:
            output_path = cli.export(args.output, format=f".{args.format}" if args.format else None)
            print(f"Exported to: {output_path}")
        elif not args.info:
            # Default output
            timestamp = os.path.basename(tempfile.mktemp())
            default_path = cli.output_dir / f"model_{timestamp}.stl"
            output_path = cli.export(str(default_path))
            print(f"Exported to: {output_path}")
        
        print("Done!")
        return 0
        
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
