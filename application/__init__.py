from application.common.console_io import clear_scr
from application.main import App

app: App = App()

__version__: str = "0.1.0"
__all__: list[str] = ["app", "clear_scr"]
