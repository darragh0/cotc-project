from json import loads
from typing import TYPE_CHECKING, Any

import requests
from flask import render_template, request

from application.base import AppBase
from application.common.console_io import clear_scr, print_snapshots
from application.common.util import app_route
from application.db import DB

if TYPE_CHECKING:
    from application.models import MetricSnapshot


class App(AppBase):
    db: DB

    def __init__(self) -> None:
        super().__init__(__name__)
        self.db = DB(self)

    @app_route("/", "/latest")
    def route_latest(self) -> str:
        with self.db:
            snapshots: list[MetricSnapshot] = self.db.get(2, desc=True)
            print_snapshots(snapshots)
            return render_template("latest.html", snapshots=snapshots)

    @app_route("/all", "/history")
    def route_history(self) -> str:
        with self.db:
            return render_template("history.html", snapshots=self.db.get(desc=True))

    @app_route("/metrics", methods=["POST"])
    def route_json(self) -> tuple[dict[str, str], int]:
        data_list: Any = request.json
        json: dict[str, Any] = loads(data_list)

        clear_scr()
        self.logger.info("JSON data received")

        if not isinstance(json, list):
            return {"error": "Invalid JSON data"}, 400

        for snapshot in json:
            ret: tuple[dict[str, str], int] = self.db.add_snapshot(snapshot)
            if ret[1] != requests.status_codes.codes.ok:
                return ret

        self.db.print_last(2)
        return ret
