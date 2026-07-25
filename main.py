import os
import sys
import ctypes
from PySide6.QtCore import QSharedMemory
from PySide6.QtWidgets import QApplication, QMessageBox

from generate_assets import create_app_icon
from src.system_utils import logger, get_resource_path
from src.app_controller import AppController

os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"


def main() -> None:
    try:
        app_id = 'antigravity.eyereminder.app.1.2'
        ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(app_id)
    except Exception:
        pass

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    app.setApplicationName("EyeReminder")

    logger.info("=== Starting EyeReminder v1.2.0 ===")

    shared_mem = QSharedMemory("EyeReminder_SingleInstance_Mutex")
    if not shared_mem.create(1):
        QMessageBox.information(
            None,
            "EyeReminder Already Running",
            "EyeReminder is already running silently in your system tray (near the clock)."
        )
        sys.exit(0)

    icon_png = get_resource_path(os.path.join("assets", "icon.png"))
    if not os.path.exists(icon_png):
        create_app_icon(os.path.dirname(icon_png))

    controller = AppController(icon_png)
    controller.start()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
