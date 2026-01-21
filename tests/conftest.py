"""Pytest configuration and fixtures for GEX Tool tests."""

import sys
from pathlib import Path

import pytest

# Add project root to path for imports
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


@pytest.fixture
def sample_gex_data():
    """Sample GEX calculation data for testing."""
    return {
        "gex": 125000000,
        "gamma": 0.45,
        "vanna": 0.12,
        "charm": 0.08,
        "underlying_price": 4500.0,
        "implied_volatility": 0.18,
        "days_to_expiration": 5,
        "call_gex": 75000000,
        "put_gex": -50000000,
        "net_gex": 25000000,
    }


@pytest.fixture
def mock_market_data():
    """Mock market data for testing GEX calculations."""
    return {
        "spot_price": 4500.0,
        "risk_free_rate": 0.05,
        "dividend_yield": 0.02,
        "volatility": 0.18,
        "time_to_expiry": 5 / 365,
    }


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for file operations."""
    return tmp_path


@pytest.fixture
def mock_streamlit_modules(monkeypatch):
    """Mock streamlit modules for non-streamlit test environments."""
    try:
        import streamlit
    except ImportError:
        monkeypatch.setattr(sys, "streamlit", None)
