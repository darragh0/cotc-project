from json import load
from logging.config import dictConfig
from pathlib import Path
from typing import Final

from flask import Flask


class AppBase(Flask):
    CONFIG_PATH: Final[str] = "config/config.json"
    root_dir: Path

    def __init__(self, import_name: str) -> None:
        super().__init__(import_name)
        self.root_dir = Path(self.root_path)
        self._init_routes()
        self._init_config()

    def _init_routes(self) -> None:
        for attr in dir(self):
            if attr.startswith("route_"):
                func = getattr(self, attr)

                for route in func.routes:
                    self.route(route, **func.kwargs)(func)

    def _init_config(self) -> None:
        path: Path = self.root_dir / AppBase.CONFIG_PATH

        if not path.exists():
            msg: str = f"Config file not found at {path!r}"
            raise FileNotFoundError(msg)

        with Path.open(path) as file:
            cfg: dict = load(file)

        self._init_logging_config(cfg["logging"])
        self._init_flask_config(cfg["flask"])

    def _init_logging_config(self, cfg: dict) -> None:
        log_file_output: Path = self.root_dir / cfg["handlers"]["file"]["filename"]

        if not log_file_output.parent.exists():
            log_file_output.parent.mkdir(parents=True)

        cfg["handlers"]["file"]["filename"] = str(log_file_output)
        dictConfig(cfg)

    def _init_flask_config(self, cfg: dict) -> None:
        self.config.update(cfg)
