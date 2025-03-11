from flask import Flask, jsonify, request
import requests
from flask_cors import CORS
from datetime import datetime

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

# Fake disaster data
fake_weather_data = {
    "lat": None,
    "lon": None,
    "temperature": 28,
    "humidity": 90,
    "precipitation": 50,
    "wind_speed": 70,
    "weather_code": 95,  # Thunderstorm with heavy rain
}

fake_flood_zones = [
    {"id": 1, "severity": "severe", "center": [], "radius": 2000, "waterLevel": 5.0},
    {"id": 2, "severity": "moderate", "center": [], "radius": 1500, "waterLevel": 3.0},
]

fake_live_updates = [
    {"message": "Cyclone warning! Winds up to 70 km/h and heavy rain detected nearby.", "type": "cyclone", "timestamp": datetime.utcnow().isoformat()},
    {"message": "Severe flooding reported nearby. Seek higher ground!", "type": "flood", "timestamp": datetime.utcnow().isoformat()},
]

@app.route("/api/floods", methods=["GET"])
def get_flood_data():
    lat = request.args.get("lat", type=float, default=20.1717029)
    lon = request.args.get("lon", type=float, default=85.7134411)

    try:
        api_url = f"https://flood-api.open-meteo.com/v1/flood?latitude={lat}&longitude={lon}&daily=river_discharge"
        response = requests.get(api_url)

        if response.status_code != 200:
            return jsonify({"error": "Failed to fetch flood data", "status_code": response.status_code}), 500

        flood_data = response.json()
        result = {
            "latitude": lat,
            "longitude": lon,
            "flood_risk": flood_data.get("flood_risk", "No data"),
            "water_level": flood_data.get("water_level", "Unknown"),
            "risk_description": flood_data.get("risk_description", "No risk detected")
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to fetch flood data", "message": str(e)}), 500

@app.route("/api/rainfall", methods=["GET"])
def get_rainfall():
    lat = request.args.get("lat", type=float, default=28.7041)
    lon = request.args.get("lon", type=float, default=77.1025)

    try:
        api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=precipitation"
        response = requests.get(api_url)
        weather_data = response.json()
        rainfall = weather_data.get("hourly", {}).get("precipitation", [])[:5]
        return jsonify({"lat": lat, "lon": lon, "rainfall": rainfall})
    except Exception as e:
        return jsonify({"error": "Failed to fetch rainfall data", "message": str(e)}), 500

@app.route("/api/shelters", methods=["GET"])
def get_shelters():
    try:
        # Placeholder shelter data (replace with real API if available)
        shelter_list = [
            {"name": "Shelter 1", "lat": 18.9691, "lon": 72.8193},
            {"name": "Shelter 2", "lat": 18.9750, "lon": 72.8300}
        ]
        return jsonify({"shelters": shelter_list})
    except Exception as e:
        return jsonify({"error": "Failed to fetch shelter data", "message": str(e)}), 500

@app.route("/api/weather", methods=["GET"])
def get_weather():
    lat = request.args.get("lat", type=float, default=28.7041)
    lon = request.args.get("lon", type=float, default=77.1025)
    use_fake = request.args.get("fake", default="false").lower() == "true"

    if use_fake:
        fake_weather_data["lat"] = lat
        fake_weather_data["lon"] = lon
        return jsonify(fake_weather_data)

    try:
        api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,relative_humidity_2m,precipitation,wind_speed_10m,weather_code"
        response = requests.get(api_url)
        weather_data = response.json()

        current = weather_data.get("current", {})
        result = {
            "lat": lat,
            "lon": lon,
            "temperature": current.get("temperature_2m", "N/A"),
            "humidity": current.get("relative_humidity_2m", "N/A"),
            "precipitation": current.get("precipitation", "N/A"),
            "wind_speed": current.get("wind_speed_10m", "N/A"),
            "weather_code": current.get("weather_code", "N/A"),
        }
        return jsonify(result)
    except Exception as e:
        return jsonify({"error": "Failed to fetch weather data", "message": str(e)}), 500

@app.route("/api/flood-zones", methods=["GET"])
def get_flood_zones():
    lat = request.args.get("lat", type=float, default=28.7041)
    lon = request.args.get("lon", type=float, default=77.1025)
    use_fake = request.args.get("fake", default="false").lower() == "true"

    if use_fake:
        fake_flood_zones[0]["center"] = [lat + 0.01, lon + 0.01]
        fake_flood_zones[1]["center"] = [lat - 0.015, lon - 0.015]
        return jsonify(fake_flood_zones)

    try:
        return jsonify([
            {"id": 1, "severity": "moderate", "center": [18.9691, 72.8193], "radius": 0, "waterLevel": 2.5},
            {"id": 2, "severity": "severe", "center": [18.9750, 72.8300], "radius": 0, "waterLevel": 4.0}
        ])
    except Exception as e:
        return jsonify({"error": "Failed to fetch flood zones", "message": str(e)}), 500

@app.route("/api/live-updates", methods=["GET"])
def get_live_updates():
    lat = request.args.get("lat", type=float, default=28.7041)
    lon = request.args.get("lon", type=float, default=77.1025)
    use_fake = request.args.get("fake", default="false").lower() == "true"

    if use_fake:
        fake_live_updates[0]["timestamp"] = datetime.utcnow().isoformat()
        fake_live_updates[1]["timestamp"] = datetime.utcnow().isoformat()
        return jsonify(fake_live_updates)

    try:
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current=temperature_2m,precipitation,wind_speed_10m,weather_code"
        weather_response = requests.get(weather_url)
        weather_data = weather_response.json().get("current", {})

        flood_url = f"https://flood-api.open-meteo.com/v1/flood?latitude={lat}&longitude={lon}&daily=river_discharge"
        flood_response = requests.get(flood_url)
        flood_data = flood_response.json()

        updates = []
        wind_speed = weather_data.get("wind_speed_10m", 0)
        precipitation = weather_data.get("precipitation", 0)
        weather_code = weather_data.get("weather_code", 0)

        if wind_speed > 50 or weather_code in [61, 63, 65, 95, 96, 99]:
            updates.append({
                "message": "Potential cyclone or severe storm detected! High winds and heavy rain expected.",
                "type": "cyclone",
                "timestamp": datetime.utcnow().isoformat()
            })
        elif precipitation > 10:
            updates.append({
                "message": f"Heavy rainfall ({precipitation} mm) detected. Risk of localized flooding.",
                "type": "rainfall",
                "timestamp": datetime.utcnow().isoformat()
            })

        river_discharge = flood_data.get("daily", {}).get("river_discharge", [0])[0]
        if river_discharge > 100:
            updates.append({
                "message": "High river discharge detected. Flood risk elevated in your area.",
                "type": "flood",
                "timestamp": datetime.utcnow().isoformat()
            })

        if not updates:
            updates.append({
                "message": "No threat nearby. Conditions are currently safe.",
                "type": "safe",
                "timestamp": datetime.utcnow().isoformat()
            })

        return jsonify(updates)
    except Exception as e:
        return jsonify({"error": "Failed to fetch live updates", "message": str(e)}), 500
@app.route("/api/hourly-weather", methods=["GET"])
def get_hourly_weather():
    lat = request.args.get("lat", type=float, default=28.7041)
    lon = request.args.get("lon", type=float, default=77.1025)

    try:
        api_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m"
        response = requests.get(api_url)
        weather_data = response.json()

        hourly_temps = weather_data.get("hourly", {}).get("temperature_2m", [])
        timestamps = weather_data.get("hourly", {}).get("time", [])

        # Convert timestamps to readable format
        hourly_forecast = []
        for i in range(len(hourly_temps)):
            time_obj = datetime.fromisoformat(timestamps[i])
            formatted_time = time_obj.strftime("%I %p")  # Example: "7 PM"
            hourly_forecast.append({"time": formatted_time, "temp": hourly_temps[i]})

        return jsonify({"lat": lat, "lon": lon, "forecast": hourly_forecast[:8]})  # Limit to 8 hours
    except Exception as e:
        return jsonify({"error": "Failed to fetch hourly weather data", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)
