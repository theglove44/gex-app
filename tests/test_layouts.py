"""
Tests for layout management functionality.
"""

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from gex_app.layouts import Layout, upsert_layout, delete_layout, get_layout_names, get_layout_by_name, load_layouts, _LAYOUTS_PATH


@pytest.fixture
def sample_layout():
    """Create a sample layout for testing."""
    return Layout(
        name="Test Layout",
        symbol="SPY",
        max_dte=30,
        strike_range_pct=100.0,
        major_threshold=1000.0,
        data_wait=10,
        auto_update=False,
    )


@pytest.fixture
def clean_layouts():
    """Clean up layouts file before and after each test."""
    # Remove existing layouts file if it exists
    if _LAYOUTS_PATH.exists():
        _LAYOUTS_PATH.unlink()
    
    yield
    
    # Clean up after test
    if _LAYOUTS_PATH.exists():
        _LAYOUTS_PATH.unlink()


class TestLayout:
    """Test Layout dataclass and its methods."""
    
    def test_layout_creation(self, sample_layout):
        """Test creating a Layout instance."""
        assert sample_layout.name == "Test Layout"
        assert sample_layout.symbol == "SPY"
        assert sample_layout.max_dte == 30
        assert sample_layout.strike_range_pct == 100.0
        assert sample_layout.major_threshold == 1000.0
        assert sample_layout.data_wait == 10
        assert sample_layout.auto_update is False
    
    def test_layout_to_dict(self, sample_layout):
        """Test converting layout to dictionary."""
        layout_dict = sample_layout.to_dict()
        assert layout_dict["name"] == "Test Layout"
        assert layout_dict["symbol"] == "SPY"
        assert layout_dict["max_dte"] == 30
        assert layout_dict["strike_range_pct"] == 100.0
        assert layout_dict["major_threshold"] == 1000.0
        assert layout_dict["data_wait"] == 10
        assert layout_dict["auto_update"] is False
    
    def test_layout_from_dict(self):
        """Test creating layout from dictionary."""
        layout_dict = {
            "name": "Dict Layout",
            "symbol": "QQQ",
            "max_dte": 45,
            "strike_range_pct": 80.0,
            "major_threshold": 500.0,
            "data_wait": 15,
            "auto_update": True,
        }
        layout = Layout.from_dict(layout_dict)
        assert layout.name == "Dict Layout"
        assert layout.symbol == "QQQ"
        assert layout.max_dte == 45
        assert layout.strike_range_pct == 80.0
        assert layout.major_threshold == 500.0
        assert layout.data_wait == 15
        assert layout.auto_update is True


class TestLayoutStorage:
    """Test layout storage operations."""
    
    def test_load_empty_layouts(self, clean_layouts):
        """Test loading layouts when file doesn't exist."""
        layouts = load_layouts()
        assert layouts == []
    
    @patch('gex_app.layouts._LAYOUTS_PATH')
    def test_load_corrupted_file(self, mock_path):
        """Test loading layouts from corrupted JSON file."""
        mock_path.exists.return_value = True
        mock_path.open.return_value.__enter__.return_value.read.return_value = "invalid json"
        
        layouts = load_layouts()
        assert layouts == []
    
    def test_upsert_new_layout(self, clean_layouts, sample_layout):
        """Test saving a new layout."""
        upsert_layout(sample_layout)
        
        layouts = load_layouts()
        assert len(layouts) == 1
        assert layouts[0].name == "Test Layout"
        assert layouts[0].symbol == "SPY"
    
    def test_upsert_update_existing_layout(self, clean_layouts, sample_layout):
        """Test updating an existing layout."""
        # Save original layout
        upsert_layout(sample_layout)
        
        # Create updated version
        updated_layout = Layout(
            name="Test Layout",
            symbol="QQQ",
            max_dte=60,
            strike_range_pct=120.0,
            major_threshold=1500.0,
            data_wait=20,
            auto_update=True,
        )
        
        # Update layout
        upsert_layout(updated_layout)
        
        # Verify update
        layouts = load_layouts()
        assert len(layouts) == 1
        assert layouts[0].symbol == "QQQ"
        assert layouts[0].max_dte == 60
        assert layouts[0].auto_update is True
    
    def test_upsert_multiple_layouts(self, clean_layouts):
        """Test saving multiple layouts."""
        layout1 = Layout(
            name="Layout 1",
            symbol="SPY",
            max_dte=30,
            strike_range_pct=100.0,
            major_threshold=1000.0,
            data_wait=10,
            auto_update=False,
        )
        
        layout2 = Layout(
            name="Layout 2",
            symbol="QQQ",
            max_dte=45,
            strike_range_pct=80.0,
            major_threshold=500.0,
            data_wait=15,
            auto_update=True,
        )
        
        upsert_layout(layout1)
        upsert_layout(layout2)
        
        layouts = load_layouts()
        assert len(layouts) == 2
        
        layout_names = {layout.name for layout in layouts}
        assert layout_names == {"Layout 1", "Layout 2"}
    
    def test_delete_layout(self, clean_layouts):
        """Test deleting a layout."""
        layout1 = Layout(
            name="Layout 1",
            symbol="SPY",
            max_dte=30,
            strike_range_pct=100.0,
            major_threshold=1000.0,
            data_wait=10,
            auto_update=False,
        )
        
        layout2 = Layout(
            name="Layout 2",
            symbol="QQQ",
            max_dte=45,
            strike_range_pct=80.0,
            major_threshold=500.0,
            data_wait=15,
            auto_update=True,
        )
        
        upsert_layout(layout1)
        upsert_layout(layout2)
        
        # Delete one layout
        delete_layout("Layout 1")
        
        layouts = load_layouts()
        assert len(layouts) == 1
        assert layouts[0].name == "Layout 2"
    
    def test_get_layout_names(self, clean_layouts):
        """Test getting list of layout names."""
        layout1 = Layout(
            name="Z Layout",
            symbol="SPY",
            max_dte=30,
            strike_range_pct=100.0,
            major_threshold=1000.0,
            data_wait=10,
            auto_update=False,
        )
        
        layout2 = Layout(
            name="A Layout",
            symbol="QQQ",
            max_dte=45,
            strike_range_pct=80.0,
            major_threshold=500.0,
            data_wait=15,
            auto_update=True,
        )
        
        upsert_layout(layout1)
        upsert_layout(layout2)
        
        names = get_layout_names()
        assert names == ["A Layout", "Z Layout"]  # Should be sorted
    
    def test_get_layout_by_name(self, clean_layouts, sample_layout):
        """Test getting a layout by name."""
        # Test with no layouts
        result = get_layout_by_name("Nonexistent")
        assert result is None
        
        # Save a layout
        upsert_layout(sample_layout)
        
        # Test getting existing layout
        result = get_layout_by_name("Test Layout")
        assert result is not None
        assert result.name == "Test Layout"
        assert result.symbol == "SPY"
        
        # Test getting non-existing layout
        result = get_layout_by_name("Nonexistent")
        assert result is None
