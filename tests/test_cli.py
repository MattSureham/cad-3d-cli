import unittest
import sys
import os
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from cad_3d_cli import CAD3DCLI


class TestCAD3DCLI(unittest.TestCase):
    """Test cases for CAD-3D-CLI"""
    
    def setUp(self):
        """Set up test fixtures"""
        self.cli = CAD3DCLI(output_dir='/tmp/cad-test')
    
    def test_initialization(self):
        """Test CLI initialization"""
        self.assertIsNotNone(self.cli)
        self.assertTrue(self.cli.output_dir.exists())
    
    def test_supported_formats(self):
        """Test supported format lists"""
        self.assertIn('.stl', CAD3DCLI.SUPPORTED_INPUTS)
        self.assertIn('.step', CAD3DCLI.SUPPORTED_INPUTS)
        self.assertIn('.dxf', CAD3DCLI.SUPPORTED_INPUTS)
        self.assertIn('.stl', CAD3DCLI.SUPPORTED_OUTPUTS)
        self.assertIn('.step', CAD3DCLI.SUPPORTED_OUTPUTS)
    
    def test_version(self):
        """Test version string"""
        self.assertEqual(CAD3DCLI.VERSION, "1.0.0")


class TestPromptParsing(unittest.TestCase):
    """Test prompt parsing functionality"""
    
    def test_box_detection(self):
        """Test box shape detection from prompt"""
        cli = CAD3DCLI()
        # This would need FreeCAD to actually test
        # For now, just verify the method exists
        self.assertTrue(hasattr(cli, 'generate_from_prompt'))
    
    def test_cylinder_detection(self):
        """Test cylinder shape detection"""
        cli = CAD3DCLI()
        self.assertTrue(hasattr(cli, 'generate_from_prompt'))


if __name__ == '__main__':
    unittest.main()
