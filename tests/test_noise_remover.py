"""
Unit tests for NoiseRemover class
"""
import pytest
import pandas as pd
import numpy as np
from src.noise_remover import NoiseRemover


class TestNoiseRemover:
    """Test cases for NoiseRemover"""
    
    def test_init(self):
        """Test NoiseRemover initialization"""
        remover = NoiseRemover()
        assert remover is not None
    
    def test_remove_noise_basic(self):
        """Test basic noise removal"""
        remover = NoiseRemover()
        
        # Create sample data with noise
        data = pd.DataFrame({
            'TD': np.arange(0, 10, 0.5),
            'Energy': np.sin(np.arange(0, 10, 0.5)) + np.random.normal(0, 0.1, 20)
        })
        
        result = remover.apply_lowess(data, 'Energy', frac=0.1)
        
        assert isinstance(result, pd.DataFrame)
        assert 'Energy_Lowess' in result.columns or 'Lowess_Trend' in result.columns
