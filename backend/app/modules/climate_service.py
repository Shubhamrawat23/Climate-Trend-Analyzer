from fastapi import HTTPException
from datetime import date, datetime, timezone, timedelta
import requests
import numpy as np
from app.db.db_connection import region_threshold_collection, region_climate_collection, climate_trend_collection



# def fetch_daily_temp(data):
#     if not data["region"]:
#         if not data["lat"] or not data["lon"]:
#                 raise HTTPException(status_code=422, detail="Please fill atleast one from Region and Lat/Lon")
     
#     if not data["start_date"] or not data["end_date"]:
#             raise HTTPException(status_code=422, detail="Date range is not completed")

#     if data["region"]:
#         region_convert_data = get_lat_lon_of_region(data["region"])
#         data["lat"] = region_convert_data['lat']
#         data["lon"] = region_convert_data['lon']

#     cache_region_threshold_val = region_threshold_collection.find_one({"latitude":data['lat'],"longitude":data['lon'], "reference_period": "1991-2020",})
#     if cache_region_threshold_val:
#         threeshold_val = cache_region_threshold_val["threshold_val"]

#     if not cache_region_threshold_val:
#         region_threshold_val = fetch_climate_data_with_threshold(float(data["lat"]), float(data["lon"]), for_threshold=True)

#         region_threshold_val["name"] = data["region"] or ""
#         region_threshold_val["created_at"] = datetime.now(timezone.utc)

#         region_threshold_collection.insert_one(region_threshold_val)

#         threeshold_val = region_threshold_val["threshold_val"]

#     region_climate_data = region_climate_collection.find_one({
#         "latitude":data['lat'], 
#         "longitude":data['lon'], 
#         "$and":[
#             {f"daily_temperatures.{data["start_date"]}": {"$exists":True}},
#             {f"daily_temperatures.{data["end_date"]}": {"$exists":True}}
#         ]
#     })


#     if not region_climate_data:
#         region_climate_data = fetch_climate_data_with_threshold(float(data["lat"]), float(data["lon"]), False, str(data["start_date"]), str(data["end_date"]))
#         region_climate_data["name"] = data["name"] or ""
#         region_climate_data["created_at"] = datetime.now(timezone.utc)
        
#         # insert data of climate
#         region_climate_collection.insert_one(region_climate_data)

#         #fetch list of heatwaves duration
#         events = detect_heatwave_events(region_climate_data["daily_temperatures"], threeshold_val)
#         anuual_matrics = calculate_annual_metrics(events, str(data["start_date"]), str(data["end_date"]))

#         anuual_matrics_resp = {
#             "name": data['name'] or "",
#             "latitude": data["lat"],
#             "longitude": data["lon"],
#             "matrics_res": anuual_matrics,
#             "hazard_type": "heatwave",
#             "created_at": datetime.now(timezone.utc)
#         }

#         climate_trend_collection.insert_one(anuual_matrics_resp)




def fetch_daily_temp(data):
    if not data.get("region"):
        if data.get("lat") is None or data.get("lon") is None:
            raise HTTPException(
                status_code=422,
                detail="Please fill at least one: Region or Lat/Lon"
            )

    if not data.get("start_date") or not data.get("end_date"):
        raise HTTPException(
            status_code=422,
            detail="Date range is not completed"
        )

    start, end = validate_dates(
        str(data["start_date"]),
        str(data["end_date"])
    )

    start_date = start.isoformat()
    end_date = end.isoformat()

    if data.get("region"):
        region_convert_data = get_lat_lon_of_region(data["region"])
        data["lat"] = region_convert_data["lat"]
        data["lon"] = region_convert_data["lon"]
        data["name"] = region_convert_data["name"]

    lat = float(data["lat"])
    lon = float(data["lon"])
    name = data.get("name") or data.get("region") or ""

    if not (-90 <= lat <= 90) or not (-180 <= lon <= 180):
        raise HTTPException(
            status_code=422,
            detail="latitude must be between -90 and 90 and longitude between -180 and 180."
        )


    # check if the given data already present in climate_trend_collection
    analysis_query = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start_date,
        "end_date": end_date,
        "hazard_type": "heatwave",
        "reference_period": "1991-2020",
        "threshold_percentile": 95,
    }

    cached_analysis = climate_trend_collection.find_one(analysis_query)

    if cached_analysis:
        cached_analysis.pop("_id")
        cached_analysis["name"] = name
        if "trend" not in cached_analysis or "insights" not in cached_analysis:
            cached_metrics = cached_analysis.get("annual_metrics") or []
            cached_analysis["trend"] = calculate_trend(cached_metrics)
            cached_analysis["insights"] = generate_insights(
                cached_analysis["trend"], cached_metrics
            )

        return cached_analysis


    # Get 95th threshold Value
    threshold_query = {
        "latitude": lat,
        "longitude": lon,
        "reference_period": "1991-2020",
        "percentile": 95,
    }

    cached_threshold = region_threshold_collection.find_one(threshold_query)

    if cached_threshold:
        threshold_val = cached_threshold["threshold_val"]
        if threshold_val is None:
            raise HTTPException(
                status_code=502,
                detail="Cached threshold record is missing threshold_val."
            )

    else:
        threshold_data = fetch_climate_data_with_threshold(lat, lon, for_threshold=True)

        threshold_data["name"] = name
        threshold_data["created_at"] = datetime.now(timezone.utc)
        threshold_val = threshold_data.get("threshold_val")
        if threshold_val is None:
            raise HTTPException(
                status_code=502,
                detail="Cached threshold record is missing threshold_val."
            )
            
        region_threshold_collection.insert_one(threshold_data)


    # get daily temp    
    climate_query = {
        "latitude": lat,
        "longitude": lon,
        "start_date": {"$lte": start_date},
        "end_date": {"$gte": end_date},
    }

    region_climate_data = region_climate_collection.find_one(climate_query)

    if not region_climate_data:
        region_climate_data = fetch_climate_data_with_threshold(lat, lon, for_threshold=False, start_date=start_date, end_date=end_date)

        region_climate_data["name"] = name
        region_climate_data["created_at"] = datetime.now(timezone.utc)

        region_climate_collection.insert_one(region_climate_data)

    raw_daily_temp_data = region_climate_data.get("daily_temperatures")
    if not raw_daily_temp_data:
        raise HTTPException(
            status_code=502,
            detail="Stored climate record has no daily temperature data."
        )

    daily_temperatures = {
        day: temp
        for day, temp in raw_daily_temp_data.items()
        if start_date <= day <= end_date
    }



    expected_days = (end - start).days + 1

    if len(daily_temperatures) != expected_days:
        raise HTTPException(
            status_code=502,
            detail=(
                "Climate data is incomplete for the requested date range. "
                "Please retry the request."
            )
        )


    # get heatwave events
    try:
        events = detect_heatwave_events(daily_temperatures, threshold_val)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Heatwave detection failed: {exc}"
        ) from exc


    # get annually metrics
    print("Entering in Annually metrics.......")
    try:
        annual_metrics = calculate_annual_metrics(events, start_date, end_date)
        print(annual_metrics)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Annual metrics computation failed: {exc}"
        ) from exc

    if not annual_metrics:
        raise HTTPException(
            status_code=500,
            detail="Annual metrics could not be computed for the requested period."
        )


    try:
        trends = calculate_trend(annual_metrics)
        insights = generate_insights(trends, annual_metrics)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail=f"Trend/insight generation failed: {exc}"
        ) from exc


    analysis_result = {
        **analysis_query,
        "name": name,
        "threshold_val": threshold_val,
        "events": events,
        "annual_metrics": annual_metrics,
        "trend": trends,
        "insights": insights,
        "created_at": datetime.now(timezone.utc),
    }

    climate_trend_collection.insert_one(analysis_result)

    return analysis_result








def get_lat_lon_of_region(region: str):

    if not region.strip():
        raise HTTPException(
            status_code=422,
            detail="Region Field can't be empty"
        )
    geocoding_url = f"https://geocoding-api.open-meteo.com/v1/search?name={region}&count=1"

    response = requests.get(geocoding_url,timeout=10)
    data = response.json()

    if "results" in data and len(data["results"])>0:
        lat = data['results'][0]['latitude']
        lon = data['results'][0]['longitude']
        name = data['results'][0]['name']

        return {
            "name":name,
            "lat":lat,
            "lon":lon
        }
    else:
        error_message = f"Region '{region}' not found via Geocoding API."
        raise HTTPException(
            status_code=404,
            detail=error_message
        )



def fetch_climate_data_with_threshold(lat:float, lon: float, for_threshold: bool, start_date: str =None, end_date: str=None):
    REFERENCE_START = "1991-01-01"
    REFERENCE_END = "2020-12-31"
    WEATHER_URL = "https://archive-api.open-meteo.com/v1/archive"

    if lat is None or lon is None:
        raise HTTPException(status_code=422, detail="latitude or longitude is missing")

    if for_threshold:
        param={
            "latitude": lat,
            "longitude": lon,
            "start_date": REFERENCE_START,
            "end_date": REFERENCE_END,
            "daily": "temperature_2m_max"
        }
        try:
            response = requests.get(WEATHER_URL, params=param, timeout=15)
            if response.status_code != 200:
                err_data = response.json()
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=err_data.get("reason", "Error fetching data from weather API.")
                )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(502, "Unable to fetch historical weather data.") from exc

        try:
            data = response.json()
        except ValueError:
            raise HTTPException(502, "Weather API returned an invalid response.")
        
        daily = data.get("daily") or {}
        temperatures = daily.get("temperature_2m_max")
        if not temperatures:
            raise HTTPException(status_code=502, detail="Weather API returned no temperature data.")

        valid_temperatures = [
            float(temp)
            for temp in temperatures
            if temp is not None
            and np.isfinite(float(temp))
        ]
        if not valid_temperatures:
            raise HTTPException(
                status_code=502,
                detail="No valid temperatures available for threshold calculation."
            )

        threshold = round(float(np.percentile(valid_temperatures, 95)), 2)
        return {
            "latitude": lat,
            "longitude": lon,
            "reference_period": "1991-2020",
            "percentile": 95,
            "threshold_val": threshold,
            "dataset": "open-meteo-archive"
            }
    else:
        if not start_date or not end_date:
            raise HTTPException(status_code=422, detail="Date range is not completed")
        param={
            "latitude": lat,
            "longitude": lon,
            "start_date": start_date,
            "end_date": end_date,
            "daily": "temperature_2m_max",
        }
        try:
            response = requests.get(WEATHER_URL, params=param, timeout=15)
            if response.status_code != 200:
                err_data = response.json()
                raise HTTPException(
                    status_code=response.status_code, 
                    detail=err_data.get("reason", "Error fetching data from weather API.")
                )
            response.raise_for_status()
        except requests.RequestException as exc:
            raise HTTPException(502, "Unable to fetch historical weather data.") from exc

        try:
            data = response.json()
        except ValueError:
            raise HTTPException(502, "Weather API returned an invalid response.")

        daily = data.get("daily") or {}
        temperatures = daily.get("temperature_2m_max")
        if not temperatures:
            raise HTTPException(status_code=502, detail="Weather API returned no temperature data.")
        
        daily_temperatures = dict(
            zip(daily.get("time"), temperatures)
       )
    if daily_temperatures:
        data["latitude"] = lat
        data["longitude"] = lon
        data["start_date"] = start_date
        data["end_date"] = end_date
        data["daily_temperatures"] = daily_temperatures
        del data["daily"]
        data["dataset"] = "open-meteo-archive"

    else:
        raise HTTPException(
            status_code=502,
            detail="No daily temperature data returned for the requested region/period." 
        )
    return data

def validate_dates(start_date, end_date):
    try:
        start = date.fromisoformat(str(start_date))
        end = date.fromisoformat(str(end_date))
    except (TypeError, ValueError):
        raise HTTPException(
            status_code=422,
            detail="Dates must use YYYY-MM-DD format",
        )

    if start > end:
        raise HTTPException(
            status_code=422,
            detail="start_date must be before or equal to end_date",
        )

    return start, end

def detect_heatwave_events(temp_data, threeshold_val):
    if threeshold_val is None:
        raise HTTPException(status_code=500, detail="Heatwave threshold is not available.")

    event_list = []
    if temp_data:
        current_streak = []
        for key, val in sorted(temp_data.items()):
            if val > threeshold_val:
                current_streak.append(key)
            else:
                if len(current_streak)> 0 and len(current_streak)<3: 
                    current_streak = []
                if len(current_streak)>=3:
                    streak_len = len(current_streak)
                    data = {
                        "start_date": current_streak[0],
                        "end_date": current_streak[-1], 
                        "duration": streak_len
                    }
                    event_list.append(data)
                    current_streak = []

        if len(current_streak)>=3:
            streak_len = len(current_streak)
            data = {
                "start_date": current_streak[0],
                "end_date": current_streak[-1], 
                "duration": streak_len
            }
            event_list.append(data)
            current_streak = []
    return event_list

def calculate_annual_metrics(events, start_date, end_date):
    print(start_date)
    print("Type = ", type(start_date))
    start, end = validate_dates(str(start_date), str(end_date))

    print(start)
    print("Type = ", type(start))

    result = {
        year: {
            "year": year,
            "event_count": 0,
            "total_heatwave_days": 0,
            "avg_event_duration_days": 0.0,
            "_duration_sum": 0,
        }
        for year in range(start.year, end.year + 1)
    }

    for event in events:
        event_start = date.fromisoformat(event["start_date"])
        event_end = date.fromisoformat(event["end_date"])
        event_year = event_start.year

        if event_year in result:
            result[event_year]["event_count"] += 1
            result[event_year]["_duration_sum"] += event["duration"]

        if event_start.year == event_end.year:
            if event_start.year in result:
                result[event_start.year]["total_heatwave_days"] += (
                    event["duration"]
                )
        else:
            current_day = event_start

            while current_day <= event_end:
                year = current_day.year

                if year in result:
                    result[year]["total_heatwave_days"] += 1

                current_day += timedelta(days=1)


    for metrics in result.values():
        if metrics["event_count"] > 0:
            metrics["avg_event_duration_days"] = round(metrics["_duration_sum"] / metrics["event_count"],2)
        del metrics["_duration_sum"]

    return list(result.values())




def calculate_trend(annual_metrics):
    if not annual_metrics:
        return {
            "frequency_trend": {
                "slope": None,
                "intercept":None,
                "direction": "insufficient_data",
                "percentage_change": None,
            },
            "heatwave_days_trend": {
                "slope": None,
                "intercept":None,
                "direction": "insufficient_data",
                "percentage_change": None,
            },
        }

    annual_metrics = sorted(
        annual_metrics,
        key=lambda item: item["year"]
    )

    years = [m["year"] for m in annual_metrics]
    event_counts = [m["event_count"] for m in annual_metrics]
    total_heatwave_days = [m["total_heatwave_days"] for m in annual_metrics]

    def compute_regression(years, values):
        if len(years) < 2:
            return {
                "slope": None,
                "intercept":None,
                "direction": "insufficient_data",
                "percentage_change": None,
            }

        x = np.array(years)
        x = x - x[0]
        y = np.array(values, dtype=float)

        if not np.all(np.isfinite(y)):
            return {
                "slope": None,
                "intercept":None,
                "direction": "invalid_data",
                "percentage_change": None,
            }

        slope, intercept = np.polyfit(x, y, 1)

        print(intercept)

        start_val = slope * x[0] + intercept
        end_val = slope * x[-1] + intercept

        if np.isclose(slope, 0.0, atol=1e-9):
            direction = "stable"
        elif slope > 0:
            direction = "increasing"
        else:
            direction = "decreasing"

        
        if start_val <= 1e-9:
            percentage_change = None
        if start_val < 1.0:
            percentage_change = None
        else:
            percentage_change = round(
                ((end_val - start_val) / start_val) * 100,
                2,
            )

        return {
            "slope": round(float(slope), 4),
            "intercept":round(float(intercept), 4),
            "direction": direction,
            "percentage_change": percentage_change,
        }

    return {
        "frequency_trend": compute_regression(
            years, event_counts
        ),
        "heatwave_days_trend": compute_regression(
            years, total_heatwave_days
        ),
    }


def generate_insights(trend, annual_metrics):
    insights = {}
    if not annual_metrics:
        return {
        "frequency_trend": "No annual climate data is available for this period.",
        "heatwave_days_trend": "No annual climate data is available for this period.",
        "peak_year_insight": "No valid records available to determine peak heatwave year.",
    }

    trend_labels = {
        "frequency_trend": "Heatwave frequency",
        "heatwave_days_trend": "Annual heatwave days",
    }

    for key, value in trend_labels.items():
        result = trend.get(key, {})
        direction = result.get("direction")
        slope = result.get("slope")
        
        if direction == "increasing":
            message = f"{value} shows an increasing linear trend over the selected period."
        elif direction == "decreasing":
            message = f"{value} shows a decreasing linear trend over the selected period."
        elif direction == "stable":
            message = f"{value} shows little or no linear change under the current trend rule."
        elif direction == "insufficient_data":
            message = f"There are not enough annual observations to estimate the trend for {value.lower()}."
        else:
            message = f"The trend for {value.lower()} could not be determined from the available data."

        if direction in ("increasing", "decreasing", "stable") and slope is not None:
            unit_label = "events" if "frequency" in key else "days"
            message += f" The estimated rate of change is {slope:+.2f} {unit_label} per year."

        insights[key] = message
        
    valid_metrics = [
        item for item in annual_metrics
        if isinstance(item.get("total_heatwave_days"), (int, float))
        and isinstance(item.get("year"), int)
    ]

    if valid_metrics:
        peak_year = max(
            valid_metrics,
            key=lambda item: item["total_heatwave_days"]
        )

        insights["peak_year_insight"] = (
            f"The highest annual number of heatwave days "
            f"occurred in {peak_year['year']}, with "
            f"{peak_year['total_heatwave_days']} days."
        )
    else:
        insights["peak_year_insight"] = (
            "No valid records available to determine peak heatwave year."
        )

    return insights
