"""
pytest configuration and shared fixtures
"""
import pytest
import sys
from pathlib import Path

# Add src directory to path for imports
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))


@pytest.fixture
def sample_data_dir():
    """Path to sample data directory"""
    return Path(__file__).parent.parent / "data"


@pytest.fixture
def sample_csv_L(sample_data_dir):
    """Path to sample L CSV file"""
    return sample_data_dir / "2025_11_17_12_33_57_L.csv"


@pytest.fixture
def sample_csv_M(sample_data_dir):
    """Path to sample M CSV file"""
    return sample_data_dir / "2025_11_17_12_33_57_M.csv"


@pytest.fixture
def sample_csv_R(sample_data_dir):
    """Path to sample R CSV file"""
    return sample_data_dir / "2025_11_17_12_33_57_R.csv"


@pytest.fixture
def sample_csv_path(sample_csv_L):
    """Path to default sample data CSV file (L)"""
    return sample_csv_L


@pytest.fixture
def config_path():
    """Path to config directory"""
    return Path(__file__).parent.parent / "config"
