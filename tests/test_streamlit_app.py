import importlib
import sys
import types

import pandas as pd
import plotly.graph_objects as go
import pytest

# Import components directly from the UI module
from gex_app.ui.components import (
    create_breakdown_chart,
    add_common_vertical_markers,
)


@pytest.fixture()
def app_module(monkeypatch):
    dummy_streamlit = types.SimpleNamespace(
        set_page_config=lambda *args, **kwargs: None,
        markdown=lambda *args, **kwargs: None,
    )
    monkeypatch.setitem(sys.modules, "streamlit", dummy_streamlit)

    import streamlit_app

    # Reload to ensure patched streamlit is used even if imported elsewhere
    importlib.reload(streamlit_app)
    return streamlit_app


@pytest.fixture
def sample_result():
    return types.SimpleNamespace(
        spot_price=100,
        zero_gamma_level=95,
        call_wall=110,
        put_wall=90,
    )


def test_create_breakdown_chart_aggregates_calls_and_puts():
    data = pd.DataFrame(
        [
            {"Strike": 100, "Type": "Call", "Net GEX ($M)": 2.0},
            {"Strike": 100, "Type": "Call", "Net GEX ($M)": 1.0},
            {"Strike": 105, "Type": "Put", "Net GEX ($M)": -3.0},
            {"Strike": 105, "Type": "Put", "Net GEX ($M)": -2.0},
        ]
    )
    result = types.SimpleNamespace(df=data, spot_price=100, zero_gamma_level=None, call_wall=None, put_wall=None, symbol="TEST", max_dte=10)

    fig = create_breakdown_chart(result)

    assert len(fig.data) == 2
    call_bar, put_bar = fig.data

    assert list(call_bar.x) == [100, 105]
    assert list(call_bar.y) == [3.0, 0]

    assert list(put_bar.x) == [100, 105]
    assert list(put_bar.y) == [0, -5.0]


def test_create_breakdown_chart_only_calls_or_puts():
    call_only = pd.DataFrame([
        {"Strike": 100, "Type": "Call", "Net GEX ($M)": 2.0}
    ])
    call_result = types.SimpleNamespace(df=call_only, spot_price=100, zero_gamma_level=None, call_wall=None, put_wall=None, symbol="CALL", max_dte=5)

    put_only = pd.DataFrame([
        {"Strike": 95, "Type": "Put", "Net GEX ($M)": -1.5}
    ])
    put_result = types.SimpleNamespace(df=put_only, spot_price=95, zero_gamma_level=None, call_wall=None, put_wall=None, symbol="PUT", max_dte=5)

    call_fig = create_breakdown_chart(call_result)
    put_fig = create_breakdown_chart(put_result)

    call_call_bar, call_put_bar = call_fig.data
    assert list(call_call_bar.x) == [100]
    assert list(call_call_bar.y) == [2.0]
    assert list(call_put_bar.y) == [0]

    put_call_bar, put_put_bar = put_fig.data
    assert list(put_call_bar.y) == [0]
    assert list(put_put_bar.x) == [95]
    assert list(put_put_bar.y) == [-1.5]


def test_create_breakdown_chart_empty_dataframe():
    empty_df = pd.DataFrame(columns=["Strike", "Type", "Net GEX ($M)"])
    result = types.SimpleNamespace(df=empty_df, spot_price=0, zero_gamma_level=None, call_wall=None, put_wall=None, symbol="EMPTY", max_dte=0)

    fig = create_breakdown_chart(result)

    assert len(fig.data) == 2
    for trace in fig.data:
        assert list(trace.x) == []
        assert list(trace.y) == []


def test_add_common_vertical_markers_with_all_levels(sample_result):
    fig = go.Figure()

    updated = add_common_vertical_markers(fig, sample_result)

    assert len(updated.layout.shapes) == 4
    x_values = [shape["x0"] for shape in updated.layout.shapes]
    assert {sample_result.spot_price, sample_result.zero_gamma_level, sample_result.call_wall, sample_result.put_wall} == set(x_values)
    assert any(ann.text.startswith("SPOT") for ann in updated.layout.annotations)


def test_add_common_vertical_markers_optional_levels_missing():
    partial_result = types.SimpleNamespace(
        spot_price=150,
        zero_gamma_level=None,
        call_wall=None,
        put_wall=None,
    )

    fig = go.Figure()
    updated = add_common_vertical_markers(fig, partial_result)

    assert len(updated.layout.shapes) == 1
    assert updated.layout.shapes[0]["x0"] == partial_result.spot_price
    assert any(ann.text.startswith("SPOT") for ann in updated.layout.annotations)
