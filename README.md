# dht22-webui

A lightweight Flask-based web interface for monitoring DHT22 temperature and humidity sensor data with real-time updates and historical data visualization.

<p align="center">
  <picture>
    <source srcset="preview_info.webp">
    <img alt="preview">
  </picture>
</p>

<p align="center">
  <picture>
    <source srcset="preview_history.webp">
    <img alt="preview">
  </picture>
</p>

<p align="center">
    <a href="https://github.com/astral-sh/ruff">
        <img src="https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json" alt="Ruff" /></a>
    <a href="https://github.com/Z1xus/dht22-webui/issues?q=is%3Aissue+is%3Aopen+" alt="GitHub issues">
        <img src="https://img.shields.io/github/issues/z1xus/dht22-webui"></a>
    <a href="https://github.com/Z1xus/dht22-webui/pulls?q=is%3Apr+is%3Aopen+" alt="GitHub pull requests">
        <img src="https://img.shields.io/github/issues-pr/z1xus/dht22-webui"></a>
</p>

### Features
- Real-time temperature and humidity monitoring
- Historical data visualization with interactive charts
- Multiple timeframe views (1h, 24h, 7d, 30d)
- Temperature unit conversion (°C/°F)
- Time format selection (12h/24h)
- MongoDB integration for data storage

### Requirements
- Raspberry Pi
- DHT22 temperature and humidity sensor
- Python 3.12+
- MongoDB database

### Installation
1. Clone the repository
```bash
git clone https://github.com/z1xus/dht22-webui
cd dht22-webui
```
2. Install dependencies
```bash
pip install -r requirements.txt
```
3. Configure your .env file
```bash
MONGO_URI=mongodb+srv://<username>:<password>@<cluster>.mongodb.net/<database>?retryWrites=true&w=majority

MONGO_DB_NAME=humidity_db
MONGO_COLLECTION_NAME=sensor_readings

DATA_COLLECTION_INTERVAL=60
```
4. Run the server
```bash
python main.py
```

### Usage
1. Connect your DHT22 sensor to your Raspberry Pi (default: GPIO4)
2. Start the application
3. Access the web interface at:
   - Local: http://localhost:5000
   - Network: http://<your_pi_ip>:5000

### License
This project is licensed under the GPL-3.0 License - see the [LICENSE](LICENSE) file for details.
