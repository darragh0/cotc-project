from __future__ import annotations

from datetime import datetime as dt
from typing import TYPE_CHECKING, Any

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship

from application.common.util import utc_now

if TYPE_CHECKING:
    from application.common._types import JSON

Base: Any = declarative_base()


class MetricSnapshot(Base):
    __tablename__ = "metric_snapshot"

    id = Column(Integer, primary_key=True)
    origin = Column(String, nullable=False)
    timestamp = Column(DateTime, default=utc_now)
    metrics = relationship(
        "Metric",
        backref="snapshot",
        lazy=True,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"MetricSnapshot[Origin={self.origin!r}, Time={self.timestamp!r}]"

    @staticmethod
    def from_json(data: JSON) -> MetricSnapshot:
        MetricSnapshot.validate_json(data)

        return MetricSnapshot(
            origin=data["origin"],
            timestamp=dt.fromisoformat(data["timestamp"]),
        )

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

        for metric_data in data["metrics"]:
            Metric.validate_json(metric_data)

    @staticmethod
    def get_types() -> dict[str, type]:
        return {
            "origin": str,
            "timestamp": str,  # str as data received is str
            "metrics": list,
        }


class Metric(Base):
    __tablename__ = "metric"

    id = Column(Integer, primary_key=True)
    name = Column(String, nullable=False)
    value = Column(Float, nullable=False)
    unit = Column(String, nullable=False)
    snapshot_id = Column(
        Integer,
        ForeignKey("metric_snapshot.id"),
        nullable=False,
    )

    def __repr__(self) -> str:
        return f"Metric[Name={self.name!r}, Data='{self.value}{self.unit}']"

    @staticmethod
    def from_json(data: JSON, snapshot_id: Column[int]) -> Metric:
        return Metric(
            name=data["name"],
            value=data["value"],
            unit=data["unit"],
            snapshot_id=snapshot_id,
        )

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

    @staticmethod
    def get_types() -> dict[str, type]:
        return {
            "name": str,
            "value": float,
            "unit": str,
        }
