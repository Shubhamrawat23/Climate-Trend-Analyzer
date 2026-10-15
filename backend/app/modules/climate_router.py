from fastapi import APIRouter

from app.modules.climate_schema import (
    ClimateAnalysisRequest,
    ClimateAnalysisResponse,
)
from app.modules.climate_service import fetch_daily_temp


router = APIRouter()


@router.post("/analysis", response_model=ClimateAnalysisResponse,)
def analyze_climate(request: ClimateAnalysisRequest):

    result = fetch_daily_temp(request.model_dump(mode="json"))

    return result
