import os

from application.models import MetricSnapshot


def clear_scr() -> None:
    os.system("cls" if os.name == "nt" else "clear")  # noqa: S605


def print_snapshots(snapshots: list[MetricSnapshot]) -> None:
    print("\n\033[1;92m===========================\033[0;0m\n")

    for snapshot in snapshots:
        print("Snapshot:")
        print(f"    ID:      {snapshot.id}")
        print(f"    ORIGIN:  {snapshot.origin}")
        print(f"    TIME:    {snapshot.timestamp}")
        print("    METRICS:")

        for metric in snapshot.metrics:
            print(f"        {metric}")

    print("\n\033[1;92m============================\033[0;0m\n")
