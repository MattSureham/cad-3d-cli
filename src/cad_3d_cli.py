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


class CAD3DCLI:
    """Main CLI class for 3D modeling operations"""
    
    VERSION = "1.0.0"
    SUPPORTED_INPUTS = ['.stl', '.step', '.stp', '.dxf', '.fcstd', '.fcstd1', '.obj', '.ply']
    SUPPORTED_OUTPUTS = ['.stl', '.step', '.stp', '.dxf', '.fcstd', '.png']
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or os.environ.get('CAD_OUTPUT_DIR', '~/clawd/cad-output'))
        self.output_dir = self.output_dir.expanduser().resolve()
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.doc = None
        
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
    
    def generate_from_prompt(self, prompt: str, **params) -> Any:
        """Generate 3D model from text description"""
        if not FREECAD_AVAILABLE:
            raise RuntimeError("FreeCAD is required for model generation")
        
        self.doc = FreeCAD.newDocument("Generated")
        
        # Parse prompt for basic shapes
        prompt_lower = prompt.lower()
        
        # Extract dimensions if provided
        width = params.get('width', 50)
        height = params.get('height', 30)
        depth = params.get('depth', 20)
        diameter = params.get('diameter', 25)
        
        shape = None
        
        if 'box' in prompt_lower or 'cube' in prompt_lower:
            shape = Part.makeBox(width, depth, height)
        elif 'cylinder' in prompt_lower:
            shape = Part.makeCylinder(diameter/2, height)
        elif 'sphere' in prompt_lower:
            shape = Part.makeSphere(diameter/2)
        elif 'cone' in prompt_lower:
            radius1 = params.get('radius1', diameter/2)
            radius2 = params.get('radius2', diameter/4)
            shape = Part.makeCone(radius1, radius2, height)
        elif 'torus' in prompt_lower:
            radius1 = params.get('major_radius', 30)
            radius2 = params.get('minor_radius', 10)
            shape = Part.makeTorus(radius1, radius2)
        elif 'tube' in prompt_lower or 'pipe' in prompt_lower:
            outer_radius = diameter / 2
            inner_radius = outer_radius - params.get('wall_thickness', 3)
            outer_cyl = Part.makeCylinder(outer_radius, height)
            inner_cyl = Part.makeCylinder(inner_radius, height)
            shape = outer_cyl.cut(inner_cyl)
        else:
            # Default to box
            shape = Part.makeBox(width, depth, height)
        
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
    
    # Other options
    parser.add_argument('--output-dir', type=str, help='Output directory')
    parser.add_argument('--info', action='store_true', help='Show model info')
    parser.add_argument('--render', action='store_true', help='Render to image')
    
    args = parser.parse_args()
    
    # Initialize CLI
    cli = CAD3DCLI(output_dir=args.output_dir)
    
    try:
        # Handle input
        if args.prompt:
            print(f"Generating model from prompt: '{args.prompt}'")
            cli.generate_from_prompt(
                args.prompt,
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
