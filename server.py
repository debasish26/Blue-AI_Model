from flask import Flask, request, jsonify
from flask_cors import CORS
import joblib
import subprocess
from datetime import datetime
import traceback
from concurrent.futures import ThreadPoolExecutor

import re
app = Flask(__name__)
CORS(app)

# Load trained model
try:
    model = joblib.load("weather_risk_model.joblib")
except Exception as e:
    print(f"Error loading model: {str(e)}")
    model = None

# Cache for recommendations
recommendations_cache = {}



executor = ThreadPoolExecutor(max_workers=4)  # Allow more parallel processing

def get_disaster_prediction(temperature, wind_speed, pressure, humidity):
    try:
        print(f"🔍 AI Processing: Temp={temperature}, Wind={wind_speed}, Pressure={pressure}, Humidity={humidity}")

        prompt = f"""Based on the weather conditions:
        Temperature: {temperature}°C
        Wind Speed: {wind_speed} km/h
        Pressure: {pressure} hPa
        Humidity: {humidity}%

        Provide exactly 10 specific safety recommendations in a numbered list format.
        """

        result = subprocess.run(
            ["ollama", "run", "llama2"],
            input=prompt.encode("utf-8"),  # ✅ Fix encoding issue
            capture_output=True,
            text=True,
            check=True
        )

        response = result.stdout.strip()
        print(f"🤖 AI Response: {response}")

        recommendations = re.findall(r"\d+\.\s(.+)", response)
        return recommendations[:4] if recommendations else ["No recommendations available."]

    except subprocess.CalledProcessError as e:
        print(f"❌ AI Processing Error: {e}")
        return ["Stay indoors", "Monitor updates", "Follow local alerts"]

@app.route("/extreme_weather", methods=["POST"])
def extreme_weather():
    try:
        print("📡 Received request at /extreme_weather")  # Confirm request is received

        data = request.get_json()
        print(f"📥 Incoming data: {data}")  # Log the received data

        if not data:
            print("❌ No data received in request")
            return jsonify({"error": "No data received"}), 400

        forecast = data.get("forecast")
        location = data.get("location", "Unknown")

        if not forecast or not isinstance(forecast, list):
            print("❌ Invalid forecast data format")
            return jsonify({"error": "Invalid forecast data format"}), 400

        print(f"🌍 Processing forecast for location: {location}")

        # Ensure forecast structure is correct
        if len(forecast) == 0:
            print("❌ Forecast list is empty")
            return jsonify({"error": "Empty forecast data"}), 400

        first_item = forecast[0]
        if not all(key in first_item for key in ["main", "wind", "weather"]):
            print("❌ Forecast data structure is invalid")
            return jsonify({"error": "Invalid forecast data structure"}), 400

        # Processing weather data
        max_temp = max(forecast, key=lambda x: x["main"]["temp"])
        max_wind = max(forecast, key=lambda x: x["wind"]["speed"])
        extreme_humidity = max(forecast, key=lambda x: x["main"]["humidity"])

        # Calculate risk score
        risk_score = 0.5  # Default risk
        if model:
            try:
                risk_features = [[
                    max_temp["main"]["temp"],
                    max_wind["wind"]["speed"],
                    extreme_humidity["main"]["humidity"]
                ]]
                risk_score = float(model.predict_proba(risk_features)[0][1])
            except Exception as e:
                print(f"⚠️ Error calculating risk score: {str(e)}")

        # AI Recommendation
        try:
            print("🤖 Generating AI recommendations...")
            recommendations = get_disaster_prediction(
                max_temp["main"]["temp"],
                max_wind["wind"]["speed"],
                max_temp["main"]["pressure"],
                extreme_humidity["main"]["humidity"]
            )
        except Exception as e:
            print(f"⚠️ Error getting AI recommendations: {str(e)}")
            recommendations = [
                "Stay informed about weather updates",
                "Keep emergency supplies ready",
                "Follow local authority guidelines",
                "Stay indoors during severe weather"
            ]

        response_data = {
            "today": {
                "location": location,
                "maxTemp": max_temp["main"]["temp"],
                "maxWind": max_wind["wind"]["speed"],
                "humidity": extreme_humidity["main"]["humidity"],
                "pressure": max_temp["main"]["pressure"],
                "condition": max_temp["weather"][0]["main"],
                "riskScore": risk_score,
                "recommendations": recommendations,
                "image": "https://images.unsplash.com/photo-1527482797697-8795b05a13fe?w=800&auto=format&fit=crop"  # ✅ Dynamic image
            }
        }


        print(f"✅ Sending Response: {response_data}")
        return jsonify(response_data)

    except Exception as e:
        print(f"❌ Error in extreme_weather endpoint: {str(e)}")
        print(traceback.format_exc())
        return jsonify({"error": "Internal server error", "message": str(e)}), 500


@app.route("/chat", methods=["POST"])
def chat():
    try:
        data = request.get_json()
        message = data.get("message")

        if not message:
            return jsonify({"error": "No message provided"}), 400

        prompt = f"""User Question about weather safety: {message}

        Provide a helpful response about weather safety, considering:
        - Current weather conditions
        - Safety precautions
        - Emergency preparedness
        - Weather-related advice

        Keep the response concise and practical."""

        result = subprocess.run(
            ["ollama", "run", "llama2"],
            input=prompt,
            capture_output=True,
            text=True,
            check=True
        )

        response = result.stdout.strip()
        return jsonify({"response": response})

    except Exception as e:
        print(f"Error in chat endpoint: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5000, use_reloader=False)  # ✅ Fixes auto-restart issue
