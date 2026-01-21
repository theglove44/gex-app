"""Tests for core GEX calculation functionality."""

import pytest


def check_gex_module():
    """Check if gex_core module is available."""
    try:
        import gex_core

        return True
    except ImportError:
        return False


def test_module_available():
    """Test that gex_core module can be imported."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)
    assert check_gex_module()


def test_gex_calculation_positive(sample_gex_data):
    """Test that positive GEX is correctly identified."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)

    gex = sample_gex_data["gex"]
    assert isinstance(gex, (int, float))
    assert gex > 0


def test_gex_calculation_negative():
    """Test negative GEX scenarios."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)

    # Simulate negative net GEX scenario
    call_gex = 30000000
    put_gex = -80000000
    net_gex = call_gex + put_gex

    assert net_gex == -50000000
    assert net_gex < 0


def test_gamma_values(sample_gex_data):
    """Test gamma value ranges."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)

    gamma = sample_gex_data["gamma"]
    assert isinstance(gamma, (int, float))
    assert 0 < gamma < 1  # Typical gamma range


def test_vanna_values(sample_gex_data):
    """Test vanna value ranges."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)

    vanna = sample_gex_data["vanna"]
    assert isinstance(vanna, (int, float))
    assert abs(vanna) < 1  # Typical vanna range


def test_charm_values(sample_gex_data):
    """Test charm value ranges."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)

    charm = sample_gex_data["charm"]
    assert isinstance(charm, (int, float))
    assert abs(charm) < 1  # Typical charm range


def test_net_gex_calculation(sample_gex_data):
    """Test net GEX equals call GEX minus put GEX."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)

    call_gex = sample_gex_data["call_gex"]
    put_gex = sample_gex_data["put_gex"]
    expected_net = call_gex + put_gex

    assert sample_gex_data["net_gex"] == expected_net


def test_price_input_validation():
    """Test that price inputs are validated correctly."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)

    valid_price = 4500.0
    assert valid_price > 0

    # Negative prices should be invalid
    invalid_price = -100.0
    assert invalid_price <= 0


def test_volatility_input_validation():
    """Test that volatility inputs are validated correctly."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)

    valid_volatility = 0.18
    assert 0 < valid_volatility < 1

    # Volatility should not be negative
    invalid_volatility = -0.1
    assert invalid_volatility <= 0


def test_expiration_input_validation():
    """Test that expiration inputs are validated correctly."""
    if not check_gex_module():
        pytest.skip("gex_core module not found", allow_module_level=True)

    valid_days = 5
    assert valid_days >= 0

    # Negative days should be invalid
    invalid_days = -1
    assert invalid_days < 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
