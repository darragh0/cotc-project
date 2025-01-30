from pathlib import Path
from threading import Thread

from dotenv import load_dotenv
from flask import Flask, render_template
from flask_socketio import SocketIO

from application.logger import init_logger
from application.metrics import MetricSnapshot, iso_tz_to_readable, local_snapshot

__all__ = ["app", "socketio"]

app: Flask = Flask(__name__)
socketio: SocketIO = SocketIO(app)

init_logger()

config_path: Path = Path(__file__).parent / "config"
load_dotenv(dotenv_path=config_path / ".flaskenv")
load_dotenv(dotenv_path=config_path / ".env")
app.config.from_prefixed_env()


@app.route("/")
@app.route("/index")
@app.route("/home")
def home() -> str:
    app.logger.info("Home webpage accessed")
    return render_template("index.html")


def send_data() -> None:
    while True:
        ms: MetricSnapshot = local_snapshot()
        ms["timestamp"] = iso_tz_to_readable(ms["timestamp"])
        app.logger.info(
            "Updating webpage w/ new metric snapshot from %s",
            ms["device_name"],
        )
        socketio.emit("update", {"metric_snapshots": [ms]})


@socketio.on("connect")
def handle_connect() -> None:
    app.logger.info("Client connected")
    Thread(target=send_data, daemon=True).start()
