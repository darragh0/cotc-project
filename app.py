from datetime import datetime as dt
from pathlib import Path

from dotenv import load_dotenv
from flask import Flask, render_template

from logger import init_logger
from metrics import MetricSnapshot, get_local_snapshot

app: Flask = Flask(__name__)

init_logger()

config_path: Path = Path(__file__).parent / "config"
load_dotenv(dotenv_path=config_path / ".flaskenv")
load_dotenv(dotenv_path=config_path / ".env")
app.config.from_prefixed_env()


@app.route("/")
@app.route("/index")
@app.route("/home")
def home() -> str:
    app.logger.info("Home route accessed")
    local_snapshot: MetricSnapshot = get_local_snapshot()

    local_snapshot.timestamp = dt.fromisoformat(local_snapshot.timestamp).strftime(
        "%d-%m-%Y %H:%M:%S",
    )

    metric_snapshots: list[MetricSnapshot] = [local_snapshot]
    return render_template("index.html", metric_snapshots=metric_snapshots)


if __name__ == "__main__":
    app.run()
