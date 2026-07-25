import os
from PySide6.QtCore import Signal, QObject
from PySide6.QtGui import QIcon, QAction
from PySide6.QtWidgets import QSystemTrayIcon, QMenu


class TrayIconManager(QObject):
    trigger_break_now = Signal()
    trigger_water_now = Signal()
    toggle_pause = Signal(int)
    set_work_interval = Signal(int)
    set_break_duration = Signal(int)
    set_water_interval = Signal(int)
    set_water_duration = Signal(int)
    open_settings = Signal()
    open_stats = Signal()
    open_about = Signal()
    exit_app = Signal()

    def __init__(self, icon_path: str, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.is_paused = False

        self.tray = QSystemTrayIcon(self)
        if os.path.exists(self.icon_path):
            self.tray.setIcon(QIcon(self.icon_path))

        self.tray.setToolTip("EyeReminder - Active")
        self._build_context_menu()
        self.tray.activated.connect(self._on_tray_activated)

    def _build_context_menu(self) -> None:
        menu = QMenu()
        menu.setStyleSheet("""
            QMenu {
                background-color: #1E293B; color: #F8FAFC; border: 1px solid #334155;
                border-radius: 8px; padding: 4px; font-family: 'Segoe UI', sans-serif;
            }
            QMenu::item { padding: 6px 16px; border-radius: 4px; }
            QMenu::item:selected { background-color: #0284C7; color: white; }
            QMenu::separator { height: 1px; background-color: #334155; margin: 4px 8px; }
        """)

        self.act_rest = QAction("👁️ Eye Rest Now", self)
        self.act_rest.triggered.connect(lambda: self.trigger_break_now.emit())
        menu.addAction(self.act_rest)

        self.act_water = QAction("💧 Drink Water Now", self)
        self.act_water.triggered.connect(lambda: self.trigger_water_now.emit())
        menu.addAction(self.act_water)

        menu.addSeparator()

        pause_menu = menu.addMenu("⏸️ Pause Reminders")
        self.act_pause_toggle = QAction("Pause / Resume Toggle", self)
        self.act_pause_toggle.triggered.connect(lambda: self.toggle_pause.emit(0))
        act_pause_15 = QAction("Pause for 15 Minutes", self)
        act_pause_15.triggered.connect(lambda: self.toggle_pause.emit(15))
        act_pause_60 = QAction("Pause for 1 Hour", self)
        act_pause_60.triggered.connect(lambda: self.toggle_pause.emit(60))

        pause_menu.addAction(self.act_pause_toggle)
        pause_menu.addAction(act_pause_15)
        pause_menu.addAction(act_pause_60)

        interval_menu = menu.addMenu("⏱️ Eye Break Frequency")
        for mins in [10, 15, 20, 30, 45, 60]:
            act = QAction(f"Every {mins} Minutes{' (Default)' if mins == 20 else ''}", self)
            act.triggered.connect(lambda checked=False, m=mins: self.set_work_interval.emit(m))
            interval_menu.addAction(act)

        duration_menu = menu.addMenu("⏳ Eye Popup Duration")
        for secs in [10, 15, 20, 30, 45, 60]:
            act = QAction(f"Hold for {secs} Seconds{' (Default)' if secs == 20 else ''}", self)
            act.triggered.connect(lambda checked=False, s=secs: self.set_break_duration.emit(s))
            duration_menu.addAction(act)

        water_interval_menu = menu.addMenu("💧 Water Frequency")
        for mins in [15, 30, 45, 60, 90, 120]:
            act = QAction(f"Every {mins} Minutes{' (Default)' if mins == 60 else ''}", self)
            act.triggered.connect(lambda checked=False, m=mins: self.set_water_interval.emit(m))
            water_interval_menu.addAction(act)

        water_duration_menu = menu.addMenu("⏳ Water Popup Duration")
        for secs in [10, 15, 20, 30, 45, 60]:
            act = QAction(f"Hold for {secs} Seconds{' (Default)' if secs == 20 else ''}", self)
            act.triggered.connect(lambda checked=False, s=secs: self.set_water_duration.emit(s))
            water_duration_menu.addAction(act)

        menu.addSeparator()

        self.act_stats = QAction("📊 Statistics", self)
        self.act_stats.triggered.connect(lambda: self.open_stats.emit())
        menu.addAction(self.act_stats)

        self.act_settings = QAction("⚙️ Full Settings", self)
        self.act_settings.triggered.connect(lambda: self.open_settings.emit())
        menu.addAction(self.act_settings)

        self.act_about = QAction("ℹ️ About EyeReminder", self)
        self.act_about.triggered.connect(lambda: self.open_about.emit())
        menu.addAction(self.act_about)

        menu.addSeparator()

        act_exit = QAction("❌ Exit", self)
        act_exit.triggered.connect(lambda: self.exit_app.emit())
        menu.addAction(act_exit)

        self.tray.setContextMenu(menu)

    def show(self) -> None:
        self.tray.show()

    def update_status(self, text: str, is_paused: bool = False) -> None:
        self.is_paused = is_paused
        status_prefix = "⏸️ [PAUSED] " if is_paused else "👁️ "
        self.tray.setToolTip(f"EyeReminder - {status_prefix}{text}")

    def show_notification(self, title: str, message: str) -> None:
        self.tray.showMessage(title, message, QSystemTrayIcon.MessageIcon.Information, 4000)

    def _on_tray_activated(self, reason) -> None:
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.trigger_break_now.emit()
        elif reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.open_settings.emit()
