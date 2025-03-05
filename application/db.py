from __future__ import annotations

from typing import TYPE_CHECKING, Any

from flask_sqlalchemy import SQLAlchemy

from application.models import Base, Metric, MetricSnapshot

if TYPE_CHECKING:
    from types import TracebackType

    from flask.ctx import AppContext

    from application.base import AppBase


class DB(SQLAlchemy):
    app: AppBase

    def __init__(self, app: AppBase) -> None:
        super().__init__(app)
        self.app = app
        self.context: AppContext | None = None

        with self:
            Base.metadata.bind = self.engine
            Base.query = self.session.query_property()
            self.init()

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
        if self.app.debug:
            Base.metadata.create_all(self.engine)
        self.app.logger.info("Database initialized")

    def add_snapshot(self, json: dict[str, Any]) -> tuple[dict[str, str], int]:
        try:
            snapshot: MetricSnapshot = MetricSnapshot.from_json(json)
        except (ValueError, TypeError) as e:
            self.app.logger.exception("Error parsing JSON data")
            return {"status": "error", "message": str(e)}, 400
        else:
            with self:
                self._addncom(snapshot)
                for metric_data in json["metrics"]:
                    metric: Metric = Metric.from_json(metric_data, snapshot.id)
                    self._addncom(metric)

        self.app.logger.info("JSON data saved to database")
        return {"status": "success"}, 200

    def get(self, n: int | None = None, *, desc: bool = False) -> list[MetricSnapshot]:
        return (
            self.session.query(MetricSnapshot)
            .order_by(MetricSnapshot.id.desc() if desc else MetricSnapshot.id.asc())
            .limit(n)
            .all()
        )

    def _addncom(self, data: Metric | MetricSnapshot) -> None:
        self.session.add(data)
        self.session.commit()
