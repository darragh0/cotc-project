from __future__ import annotations

from datetime import datetime, timezone
from socket import gethostname
from typing import TypedDict

from psutil import cpu_percent, virtual_memory


class Metric(TypedDict):
    name: str
    value: float
    unit: str


class MetricSnapshot(TypedDict):
    device_name: str
    timestamp: str
    metrics: list[Metric]


def iso_tz_to_readable(timestamp: str) -> str:
    """Convert an ISO 8601 timestamp to a human-readable format."""
    return datetime.fromisoformat(timestamp).strftime("%d-%m-%Y %H:%M:%S")


def local_snapshot() -> MetricSnapshot:
    """Retrieve a snapshot of the local machine's CPU and RAM usage."""

    # CPU % usage (1 sec. interval)
    cpu_usage: Metric = Metric(
        name="CPU Usage",
        value=cpu_percent(interval=1),
        unit="%",
    )

    # RAM usage (in MB)
    ram_usage: Metric = Metric(
        name="RAM Usage",
        value=virtual_memory().used / 1e6,
        unit="MB",
    )

    return MetricSnapshot(
        device_name=gethostname(),
        timestamp=datetime.now(tz=timezone.utc).isoformat(),
        metrics=[cpu_usage, ram_usage],
    )
