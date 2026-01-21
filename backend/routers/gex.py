from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from tastytrade import Session

from backend.dependencies import get_tt_session
from gex_app.core.gex_core import calculate_gex_profile

router = APIRouter()


class GEXRequest(BaseModel):
    symbol: str = "SPX"
    max_dte: int = 30
    strike_range_pct: float = 0.20
    major_threshold: float = 50.0
    data_wait: float = 5.0


class MajorLevel(BaseModel):
    strike: float
    type: str  # "Call" or "Put"
    net_gex: float


class StrategySignal(BaseModel):
    signal: str
    bias: str
    message: str
    validity: str
    color: str


class GEXResponse(BaseModel):
    symbol: str
    spot_price: float
    total_gex: float
    zero_gamma_level: Optional[float]
    call_wall: Optional[float]
    put_wall: Optional[float]
    major_levels: list[dict[str, Any]]
    strike_gex: list[dict[str, Any]]
    # strike_gex includes 'VolWeightedGEX' = Net GEX * (Strike Volume / Total Volume)
    # This is a relative metric of intraday participation.
    strategy: Optional[StrategySignal] = None
    error: Optional[str] = None


class UniverseRequest(BaseModel):
    symbols: list[str]
    max_dte: int = 30
    strike_range_pct: float = 0.20
    major_threshold: float = 50.0
    data_wait: float = 5.0


@router.post("/calculate", response_model=GEXResponse)
async def calculate_gex(
    request: GEXRequest, session: Session = Depends(get_tt_session)
):
    try:
        # Use the async function directly to avoid event loop conflicts
        result = await calculate_gex_profile(
            symbol=request.symbol,
            max_dte=request.max_dte,
            strike_range_pct=request.strike_range_pct,
            major_level_threshold=request.major_threshold,
            data_wait_seconds=request.data_wait,
            session=session,
        )

        if result.error:
            # We return the object with error, or we could raise HTTPException
            # Returning object allows UI to display specific error states
            pass

        # Convert DataFrames to dicts for JSON response
        major_levels_data = []
        if not result.major_levels.empty:
            # Ensure columns exist before converting
            df = result.major_levels.copy()
            # Rename for consistency if needed, but existing names are: 'Strike', 'Net GEX ($M)'
            # We probably want to keep them or normalize keys to lowercase snake_case
            # Let's simple to_dict('records')
            major_levels_data = df.to_dict(orient="records")

        strike_gex_data = []
        if not result.strike_gex.empty:
            strike_gex_data = result.strike_gex.to_dict(orient="records")

        return GEXResponse(
            symbol=result.symbol,
            spot_price=float(result.spot_price) if result.spot_price else 0.0,
            total_gex=float(result.total_gex) if result.total_gex else 0.0,
            zero_gamma_level=result.zero_gamma_level,
            call_wall=result.call_wall,
            put_wall=result.put_wall,
            major_levels=major_levels_data,
            strike_gex=strike_gex_data,
            strategy=result.strategy,
            error=result.error,
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/scan", response_model=list[GEXResponse])
async def scan_universe(
    request: UniverseRequest, session: Session = Depends(get_tt_session)
):
    results = []
    # Process sequentially for now to avoid rate limits or session conflicts
    # In production, we'd use a task queue or parallel execution with rate limiting
    for sym in request.symbols:
        try:
            result = await calculate_gex_profile(
                symbol=sym,
                max_dte=request.max_dte,
                strike_range_pct=request.strike_range_pct,
                major_level_threshold=request.major_threshold,
                data_wait_seconds=request.data_wait,
                session=session,
            )

            # Format result
            major_levels_data = []
            if not result.major_levels.empty:
                major_levels_data = result.major_levels.to_dict(orient="records")

            strike_gex_data = []
            if not result.strike_gex.empty:
                strike_gex_data = result.strike_gex.to_dict(orient="records")

            results.append(
                GEXResponse(
                    symbol=result.symbol,
                    spot_price=float(result.spot_price) if result.spot_price else 0.0,
                    total_gex=float(result.total_gex) if result.total_gex else 0.0,
                    zero_gamma_level=result.zero_gamma_level,
                    call_wall=result.call_wall,
                    put_wall=result.put_wall,
                    major_levels=major_levels_data,
                    strike_gex=strike_gex_data,
                    error=result.error,
                )
            )
        except Exception as e:
            # Add error result for this symbol
            results.append(
                GEXResponse(
                    symbol=sym,
                    spot_price=0.0,
                    total_gex=0.0,
                    zero_gamma_level=None,
                    call_wall=None,
                    put_wall=None,
                    major_levels=[],
                    strike_gex=[],
                    strategy=None,
                    error=str(e),
                )
            )

    return results
