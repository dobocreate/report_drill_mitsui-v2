"""
Unit tests for DataLoader class
"""
import pytest
import pandas as pd
from pathlib import Path
from src.data_loader import DataLoader


class TestDataLoader:
    """Test cases for DataLoader"""
    
    def test_init(self):
        """Test DataLoader initialization"""
        loader = DataLoader()
        assert loader is not None
        assert hasattr(loader, 'supported_encodings')
    
    def test_load_sample_file(self, sample_csv_path):
        """Test loading sample CSV file"""
        loader = DataLoader()
        df = loader.load_single_file(sample_csv_path, header_row=1)
        
        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        # Check for common column names after cleaning
        # Note: Actual columns depend on the header_row setting
    
    def test_clean_column_names(self):
        """Test column name cleaning"""
        loader = DataLoader()
        
        # Test various column name formats
        assert loader._clean_column_name('  TD  ') == 'TD'
        assert loader._clean_column_name('x:TD(m)') == 'TD'
    
    def test_convert_numeric_columns(self):
        """Test numeric column conversion"""
        loader = DataLoader()
        df = pd.DataFrame({
            'TD': ['1.0', '2.0', '3.0'],
            'X': ['10.5', '20.5', '30.5']
        })
        
        result = loader._convert_numeric_columns(df)
        assert result['TD'].dtype in ['float64', 'int64']
        assert result['X'].dtype in ['float64', 'int64']
