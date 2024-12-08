import json
import os
import socket
import time
from datetime import UTC, datetime, timedelta
from threading import Event, Thread

import adafruit_dht
import board
from bson import json_util
from dotenv import load_dotenv
from flask import Flask, jsonify, render_template
from flask_socketio import SocketIO
from pymongo import MongoClient, errors

load_dotenv()

try:
	client = MongoClient(os.getenv("MONGO_URI"), serverSelectionTimeoutMS=5000)
	client.server_info()
	db = client[os.getenv("MONGO_DB_NAME", "humidity_db")]
	readings = db[os.getenv("MONGO_COLLECTION_NAME", "sensor_readings")]
	readings.create_index([("timestamp", 1)])
except errors.ServerSelectionTimeoutError as e:
	raise SystemExit(f"MongoDB connection failed: {e}") from e
except Exception as e:
	raise SystemExit(f"Database setup failed: {e}") from e

STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
if not os.path.exists(STATIC_DIR):
    os.makedirs(os.path.join(STATIC_DIR, "js"))

app = Flask(__name__, 
    static_folder=STATIC_DIR,
    static_url_path="/static")
socketio = SocketIO(app, cors_allowed_origins="*", ping_timeout=10, ping_interval=5, async_mode="gevent")

try:
	dht = adafruit_dht.DHT22(board.D4)
except Exception:
	try:
		dht = adafruit_dht.DHT22(4)
	except Exception as e:
		raise SystemExit(f"DHT22 initialization failed: {e}") from e

thread = None
thread_stop_event = Event()
last_reading = None
last_db_write = None


def get_formatted_time() -> str:
	return datetime.now().strftime("%I:%M:%S %p")


def calculate_stats(timeframe: str) -> list | None:
	now = datetime.now(UTC)
	timeframe_map = {
		"1h": (timedelta(hours=1), timedelta(minutes=1)),
		"24h": (timedelta(days=1), timedelta(minutes=15)),
		"7d": (timedelta(days=7), timedelta(hours=1)),
		"30d": (timedelta(days=30), timedelta(hours=3)),
	}

	if timeframe not in timeframe_map:
		return None

	delta, interval = timeframe_map[timeframe]
	start_time = now - delta

	try:
		pipeline = [
			{"$match": {"timestamp": {"$gte": start_time}}},
			{
				"$group": {
					"_id": {"$dateTrunc": {"date": "$timestamp", "unit": "minute", "binSize": int(interval.total_seconds() / 60)}},
					"timestamp": {"$first": "$timestamp"},
					"avg_temp": {"$avg": "$temperature"},
					"avg_humidity": {"$avg": "$humidity"},
					"min_temp": {"$min": "$temperature"},
					"max_temp": {"$max": "$temperature"},
					"min_humidity": {"$min": "$humidity"},
					"max_humidity": {"$max": "$humidity"},
					"count": {"$sum": 1},
				}
			},
			{"$sort": {"timestamp": 1}},
		]
		return list(readings.aggregate(pipeline))
	except Exception as e:
		print(f"Error calculating stats: {e}")
		return []


def read_sensor() -> None:
	global last_reading, last_db_write
	consecutive_errors = 0
	data_collection_interval = int(os.getenv("DATA_COLLECTION_INTERVAL", 60))
	last_emit_time = None
	emit_interval = 2

	while not thread_stop_event.is_set():
		try:
			temperature = dht.temperature
			humidity = dht.humidity

			if temperature is not None and humidity is not None:
				current_time = datetime.now(UTC)

				if last_emit_time is None or (current_time - last_emit_time).total_seconds() >= emit_interval:
					data = {
						"temperature": round(temperature, 2),
						"humidity": round(humidity, 2),
						"timestamp": get_formatted_time(),
					}
					socketio.emit("sensor_data", json.dumps(data))
					last_emit_time = current_time
					last_reading = data

				if last_db_write is None or (current_time - last_db_write).total_seconds() >= data_collection_interval:
					readings.insert_one(
						{
							"temperature": temperature,
							"humidity": humidity,
							"timestamp": current_time,
						}
					)
					last_db_write = current_time

					stats = {timeframe: calculate_stats(timeframe) for timeframe in ["1h", "24h", "7d", "30d"]}
					socketio.emit("stats_update", json.dumps(stats, default=json_util.default))

				consecutive_errors = 0

		except (RuntimeError, Exception):
			consecutive_errors += 1
			time.sleep(5 if consecutive_errors > 5 else 0.5)
			continue

		time.sleep(0.5)


@app.route("/")
def index():
	return render_template("index.html")


@app.route("/api/stats/<timeframe>")
def get_stats(timeframe: str):
	try:
		stats = calculate_stats(timeframe)
		return jsonify(json.loads(json_util.dumps(stats)))
	except Exception:
		return jsonify([])


@socketio.on("connect")
def handle_connect():
	global thread
	if last_reading:
		socketio.emit("sensor_data", json.dumps(last_reading))

	if thread is None:
		thread = Thread(target=read_sensor)
		thread_stop_event.clear()
		thread.daemon = True
		thread.start()


if __name__ == "__main__":
	try:
		def get_local_ip():
			try:
				s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				s.connect(('8.8.8.8', 80))
				ip = s.getsockname()[0]
				s.close()
				return ip
			except Exception:
				return "0.0.0.0"

		print("\n🌡️  DHT22 Sensor Monitor Starting...")
		port = 5000
		local_ip = get_local_ip()
		print("\n📡 Access the dashboard at:")
		print(f"   • Local:   http://localhost:{port}")
		print(f"   • Network: http://{local_ip}:{port}")
		print("\nPress Ctrl+C to stop the server\n")
		socketio.run(app, host="0.0.0.0", port=port, debug=False)
	except KeyboardInterrupt:
		print("\n\n🛑 Shutting down...")
		thread_stop_event.set()
		if thread:
			thread.join()
	finally:
		try:
			dht.exit()
			client.close()
		except Exception:
			pass
