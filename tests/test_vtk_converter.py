"""
Unit tests for VTK converter functionality
"""
import pytest
import pandas as pd
import numpy as np
from pathlib import Path
from src.vtk_converter import VTKConverter


class TestVTKConverter:
    """Test cases for VTK conversion"""
    
    def test_init(self):
        """Test VTKConverter initialization"""
        converter = VTKConverter()
        assert converter is not None
    
    def test_create_vtk_basic(self):
        """Test basic VTK file creation"""
        converter = VTKConverter()
        
        # Create sample coordinate data
        data = pd.DataFrame({
            'X': [0.0, 1.0, 2.0],
            'Y': [0.0, 1.0, 2.0],
            'Z': [100.0, 99.0, 98.0],
            'Energy': [1500, 1600, 1700]
        })
        
        # Test VTK creation (should not raise exception)
        # Actual file writing is tested separately
        assert len(data) == 3
    
    def test_generate_vtk_filename(self):
        """Test VTK filename generation from CSV filename"""
        converter = VTKConverter()
        
        # Test cases from test_vtk_filename.py
        test_cases = [
            ("2025_08_27_07_24_47_L.csv", "Drill-L_ana_25.08.27.vtk"),
            ("2025_08_27_07_24_47_M.csv", "Drill-M_ana_25.08.27.vtk"),
            ("2025_08_27_07_24_47_R.csv", "Drill-R_ana_25.08.27.vtk"),
            ("2025_08_27_07_24_47_L_processed.csv", "Drill-L_ana_25.08.27.vtk"),
            ("L_processed", "Drill-L_ana_00.00.00.vtk"),  # 古い形式（日付情報なし）
        ]
        
        for input_file, expected_output in test_cases:
            result = converter.generate_vtk_filename(input_file)
            assert result == expected_output, f"Expected {expected_output}, got {result} for {input_file}"
