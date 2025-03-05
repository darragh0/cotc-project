from __future__ import annotations

import json
from json import loads
from logging.config import dictConfig
from pathlib import Path
from typing import TYPE_CHECKING, Any, Final

from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy

from application.common.util import app_route, utc_now

if TYPE_CHECKING:
    from types import TracebackType

    from flask.ctx import AppContext

    from application.common import JSON


class AppBase(Flask):
    def __init__(self, *, import_name: str, config_path: str) -> None:
        super().__init__(import_name)
        self._init_routes()
        self._init_config(config_path)

    def _init_routes(self) -> None:
        for attr in dir(self):
            if attr.startswith("route_"):
                func = getattr(self, attr)

                for route in func.routes:
                    self.route(route, **func.kwargs)(func)

    def _init_config(self, config_path: str) -> None:
        path: Path = Path(self.root_path) / config_path

        if not path.exists():
            msg: str = f"Config file not found at {path!r}"
            raise FileNotFoundError(msg)

        with Path.open(path) as file:
            cfg: dict = json.load(file)

        self._init_logging_config(cfg["logging"])
        self._init_app_config(cfg["app"])

    def _init_logging_config(self, cfg: dict) -> None:
        log_file_output: str = cfg["handlers"]["file"]["filename"]
        cfg["handlers"]["file"]["filename"] = Path(self.root_path) / log_file_output
        dictConfig(cfg)

    def _init_app_config(self, cfg: dict) -> None:
        self.config.update(cfg)


class DB(SQLAlchemy):
    app: AppBase

    def __init__(self, app: AppBase) -> None:
        super().__init__(app)
        self.app = app
        self.context: AppContext | None = None

    def __enter__(self) -> AppContext:
        self.context = self.app.app_context()
        return self.context.__enter__()

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        if self.context is not None:
            self.context.__exit__(exc_type, exc_val, exc_tb)
        self.context = None

    def init(self) -> None:
        with self:
            if self.app.debug:
                self.drop_all()
            self.create_all()

    def add_snapshot(self, json: JSON) -> tuple[dict[str, str], int]:
        try:
            snapshot: MetricSnapshot = MetricSnapshot.from_json(json)
        except (ValueError, TypeError) as e:
            self.app.logger.exception("Error parsing JSON data")
            return {"status": "error", "message": str(e)}, 400
        else:
            with self:
                self._addncom(snapshot)
                metric_data: JSON
                for metric_data in json["metrics"]:  # type: ignore  # noqa: PGH003
                    metric: Metric = Metric.from_json(metric_data, snapshot.id)
                    self._addncom(metric)

        self.app.logger.info("JSON data saved to database")
        return {"status": "success"}, 200

    def print_all(self) -> None:
        with self:
            snapshots: list[MetricSnapshot] = MetricSnapshot.query.all()
            for snapshot in snapshots:
                print("Snapshot:")
                print(f"    ID:      {snapshot.id}")
                print(f"    ORIGIN:  {snapshot.origin}")
                print(f"    TIME:    {snapshot.timestamp}\n")
                print("    METRICS:")

                for metric in snapshot.metrics:  # type: ignore  # noqa: PGH003
                    print(f"        {metric}")

    def _addncom(self, data: Metric | MetricSnapshot) -> None:
        self.session.add(data)
        self.session.commit()


class App(AppBase):
    CONFIG_PATH: Final[str] = "config/config.json"

    db: DB

    def __init__(self) -> None:
        super().__init__(import_name=__name__, config_path=App.CONFIG_PATH)
        self.db = DB(self)

    @app_route("/", "/index", "/home")
    def route_home(self) -> str:
        self.logger.info("Home webpage accessed")
        return render_template("index.html", metric_snapshots=[])

    @app_route("/metrics", methods=["POST"])
    def route_json(self) -> tuple[dict[str, str], int]:
        data: Any = request.json
        self.logger.info("JSON data received: %s", data)

        ret: tuple[dict[str, str], int] = self.db.add_snapshot(loads(data))
        self.db.print_all()
        return ret


app: App = App()


class MetricSnapshot(app.db.Model):  # type: ignore  # noqa: PGH003
    __tablename__ = "metric_snapshot"

    id = app.db.Column(app.db.Integer, primary_key=True)
    origin = app.db.Column(app.db.String, nullable=False)
    timestamp = app.db.Column(app.db.String, default=utc_now)  # change to dt
    metrics = app.db.relationship(
        "Metric",
        backref="snapshot",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"MetricSnapshot[Origin={self.origin!r}, Time={self.timestamp!r}]"

    # @override
    @staticmethod
    def from_json(data: JSON) -> MetricSnapshot:
        MetricSnapshot.validate_json(data)

        return MetricSnapshot(
            origin=data["origin"],
            timestamp=data["timestamp"],
        )

    # @override
    @staticmethod
    def validate_json(data: JSON) -> None:
        types: dict[str, type] = MetricSnapshot.get_types()
        err_msg: str

        for key, key_type in types.items():
            if key not in data:
                err_msg = f"Missing required key: {key!r}"
                raise ValueError(err_msg)
            if not isinstance(data[key], key_type):
                err_msg = f"Invalid type for key {key!r}: {data[key]!r}"
                raise TypeError(err_msg)

        metric_data: JSON
        for metric_data in data["metrics"]:  # type: ignore  # noqa: PGH003
            Metric.validate_json(metric_data)

    # @override
    @staticmethod
    def get_types() -> dict[str, type]:
        return {
            "origin": str,
            "timestamp": str,
            "metrics": list,
        }


class Metric(app.db.Model):  # type: ignore  # noqa: PGH003
    __tablename__ = "metric"

    id = app.db.Column(app.db.Integer, primary_key=True)
    name = app.db.Column(app.db.String, nullable=False)
    value = app.db.Column(app.db.Float, nullable=False)
    unit = app.db.Column(app.db.String, nullable=False)
    snapshot_id = app.db.Column(
        app.db.Integer,
        app.db.ForeignKey("metric_snapshot.id"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"Metric[Name={self.name!r}, Data='{self.value}{self.unit}']"

    # @override
    @staticmethod
    def from_json(data: JSON, snapshot_id: int) -> Metric:
        return Metric(
            name=data["name"],
            value=data["value"],
            unit=data["unit"],
            snapshot_id=snapshot_id,
        )

    # @override
    @staticmethod
    def validate_json(data: JSON) -> None:
        types: dict[str, type] = Metric.get_types()
        err_msg: str

        for key in Metric.get_types():
            if key not in data:
                err_msg = f"Missing required key: {key!r}"
                raise ValueError(err_msg)
            if not isinstance(data[key], types[key]):
                err_msg = (
                    f"Invalid type for {key!r}: {data[key]!r}; expected {types[key]!r}"
                )
                raise TypeError(err_msg)

    # @override
    @staticmethod
    def get_types() -> dict[str, type]:
        return {
            "name": str,
            "value": float,
            "unit": str,
        }


app.db.init()
