from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from socket import gethostname

from psutil import cpu_percent, virtual_memory


@dataclass
class Metric:
    name: str
    value: float
    unit: str

    def to_dict(self) -> dict[str, str | float]:
        """Convert the metric to a dictionary."""

        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
        }


@dataclass
class MetricSnapshot:
    device_name: str
    timestamp: str
    metrics: list[Metric]

    def to_dict(self) -> dict[str, str | list[dict[str, str | float]]]:
        """Convert the metric snapshot to a dictionary."""

        return {
            "device_name": self.device_name,
            "timestamp": self.timestamp,
            "metrics": [m.to_dict() for m in self.metrics],
        }


def get_local_snapshot() -> MetricSnapshot:
    """Get a snapshot of the local machine's CPU and RAM usage."""

    device_name: str = gethostname()
    timestamp: str = dt.datetime.now(tz=dt.timezone.utc).isoformat()
    # CPU % usage (1 sec. interval)
    cpu_usage: Metric = Metric("CPU Usage", cpu_percent(interval=1), "%")
    # RAM usage (in MB)
    ram_usage: Metric = Metric("RAM Usage", virtual_memory().used / 1e6, "MB")

    return MetricSnapshot(
        device_name=device_name,
        timestamp=timestamp,
        metrics=[cpu_usage, ram_usage],
    )
