from pydantic import BaseModel, Field, ConfigDict, model_validator
from datetime import date

class ClimateAnalysisRequest(BaseModel):
    region: str | None = Field(default=None, min_length=1, max_length=100)
    lat: float | None = Field(default=None, ge=-90, le=90)
    lon: float | None = Field(default=None, ge=-180, le=180)
    start_date: date
    end_date: date

    @model_validator(mode="after")
    def _check(self):
        if not self.region and (self.lat is None or self.lon is None):
            raise ValueError("Provide either a region or both lat and lon.")
        if self.start_date > self.end_date:
            raise ValueError("start_date must be before or equal to end_date.")
        return self


# class HeatwaveEvent(BaseModel):
#     model_config = ConfigDict(extra="ignore")
#     start_date: date
#     end_date: date
#     duration: int


class AnnualMetric(BaseModel):
    model_config = ConfigDict(extra="ignore")
    year: int
    event_count: int
    total_heatwave_days: int
    avg_event_duration_days: float


class TrendMetric(BaseModel):
    model_config = ConfigDict(extra="ignore")
    slope: float | None = None
    intercept: float | None = None
    direction: str | None = None
    percentage_change: float | None = None


class ClimateAnalysisResponse(BaseModel):
    model_config = ConfigDict(extra="ignore")
    name: str
    latitude: float
    longitude: float

    start_date: date
    end_date: date

    reference_period: str
    threshold_percentile: int
    threshold_val: float
    hazard_type:str = "heatwave"

    # events: list[HeatwaveEvent]
    annual_metrics: list[AnnualMetric]

    trend: dict[str, TrendMetric]
    insights: dict[str, str]