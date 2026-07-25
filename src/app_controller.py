import datetime
from typing import Optional
from PySide6.QtCore import QObject, QTimer
from PySide6.QtWidgets import QApplication

from src.config import ConfigManager
from src.system_utils import get_idle_duration_seconds, is_workstation_locked, is_in_lunch_break, set_autostart, logger
from src.tray_icon import TrayIconManager
from src.break_popup import BreakPopupWindow, WaterPopupWindow
from src.settings_dialog import SettingsDialog, AboutDialog


class AppController(QObject):
    def __init__(self, icon_path: str, parent=None):
        super().__init__(parent)
        self.icon_path = icon_path
        self.config = ConfigManager()

        if self.config.get("autostart_enabled", True):
            set_autostart(True)

        self.elapsed_active_secs: int = 0
        self.elapsed_water_secs: int = 0
        self.is_manual_paused: bool = False
        self.pause_until: Optional[datetime.datetime] = None
        self.is_in_break: bool = False

        self.tray_mgr = TrayIconManager(self.icon_path)
        self.popup = BreakPopupWindow(
            break_duration=self.config.get("break_duration_secs", 20),
            work_interval=self.config.get("work_interval_mins", 20),
            sound_enabled=self.config.get("sound_enabled", True)
        )
        self.water_popup = WaterPopupWindow(
            water_duration=self.config.get("water_duration_secs", 20),
            water_interval=self.config.get("water_interval_mins", 60),
            sound_enabled=self.config.get("sound_enabled", True)
        )
        self.settings_dialog: Optional[SettingsDialog] = None
        self.about_dialog: Optional[AboutDialog] = None

        # Signal connections
        self.tray_mgr.trigger_break_now.connect(self.trigger_break_immediately)
        self.tray_mgr.trigger_water_now.connect(self.trigger_water_reminder_immediately)
        self.tray_mgr.toggle_pause.connect(self.handle_pause_request)
        self.tray_mgr.set_work_interval.connect(self.set_work_interval)
        self.tray_mgr.set_break_duration.connect(self.set_break_duration)
        self.tray_mgr.set_water_interval.connect(self.set_water_interval)
        self.tray_mgr.set_water_duration.connect(self.set_water_duration)
        self.tray_mgr.open_settings.connect(self.show_settings)
        self.tray_mgr.open_stats.connect(self.show_stats)
        self.tray_mgr.open_about.connect(self.show_about)
        self.tray_mgr.exit_app.connect(self.quit_app)

        self.popup.break_finished.connect(self._on_break_finished)
        self.popup.postpone_requested.connect(self._on_postpone_requested)
        self.popup.config_changed.connect(self._on_popup_config_changed)

        self.water_popup.break_finished.connect(self._on_water_break_finished)
        self.water_popup.postpone_requested.connect(self._on_water_postpone_requested)
        self.water_popup.config_changed.connect(self._on_water_popup_config_changed)

        self.loop_timer = QTimer(self)
        self.loop_timer.setInterval(1000)
        self.loop_timer.timeout.connect(self._tick)

    def start(self) -> None:
        self.tray_mgr.show()
        self.loop_timer.start()
        logger.info("AppController: Service started successfully.")
        self.tray_mgr.show_notification(
            "EyeReminder Active",
            f"Protecting your eyes! Reminder set every {self.config.get('work_interval_mins', 20)} mins."
        )

    def set_work_interval(self, mins: int) -> None:
        self.config.set("work_interval_mins", mins)
        self.tray_mgr.show_notification("Timer Updated", f"Eye break interval set to every {mins} minutes.")

    def set_break_duration(self, secs: int) -> None:
        self.config.set("break_duration_secs", secs)
        self.tray_mgr.show_notification("Break Duration Updated", f"Eye popup timer set to {secs} seconds.")

    def set_water_interval(self, mins: int) -> None:
        self.config.set("water_interval_mins", mins)
        self.tray_mgr.show_notification("Water Timer Updated", f"Water reminder interval set to every {mins} minutes.")

    def set_water_duration(self, secs: int) -> None:
        self.config.set("water_duration_secs", secs)
        self.tray_mgr.show_notification("Water Duration Updated", f"Water popup timer set to {secs} seconds.")

    def _on_popup_config_changed(self, work_mins: int, break_secs: int) -> None:
        self.config.set("work_interval_mins", work_mins)
        self.config.set("break_duration_secs", break_secs)
        self.tray_mgr.show_notification("Eye Settings Saved", f"Work: {work_mins}m | Break: {break_secs}s")

    def _on_water_popup_config_changed(self, water_mins: int, water_secs: int) -> None:
        self.config.set("water_interval_mins", water_mins)
        self.config.set("water_duration_secs", water_secs)
        self.tray_mgr.show_notification("Water Settings Saved", f"Every: {water_mins}m | Duration: {water_secs}s")

    def _tick(self) -> None:
        if self.is_in_break:
            return

        if self.pause_until is not None:
            if datetime.datetime.now() >= self.pause_until:
                self.pause_until = None
                self.is_manual_paused = False
            else:
                remaining_pause = int((self.pause_until - datetime.datetime.now()).total_seconds())
                self.tray_mgr.update_status(f"Paused ({remaining_pause // 60 + 1}m remaining)", is_paused=True)
                return

        if self.is_manual_paused:
            self.tray_mgr.update_status("Paused manually", is_paused=True)
            return

        if is_workstation_locked():
            if self.config.get("reset_on_lock", True):
                self.elapsed_active_secs = 0
            self.tray_mgr.update_status("Laptop Locked", is_paused=True)
            return

        if self.config.get("lunch_break_enabled", True):
            st = self.config.get("lunch_start_time", "13:00")
            et = self.config.get("lunch_end_time", "14:00")
            if is_in_lunch_break(st, et):
                self.tray_mgr.update_status("Lunch Break (Quiet Hours)", is_paused=True)
                return

        idle_secs = get_idle_duration_seconds()
        idle_threshold = self.config.get("idle_pause_secs", 120)

        if idle_secs >= idle_threshold:
            self.tray_mgr.update_status(f"Idle ({int(idle_secs)}s away)", is_paused=True)
            return

        self.elapsed_active_secs += 1
        work_target_secs = self.config.get("work_interval_mins", 20) * 60
        remaining_secs = max(0, work_target_secs - self.elapsed_active_secs)

        mins = remaining_secs // 60
        secs = remaining_secs % 60
        today_count = self.config.get_today_breaks_count()

        water_target_secs = self.config.get("water_interval_mins", 60) * 60
        remaining_water_secs = max(0, water_target_secs - self.elapsed_water_secs)
        w_mins = remaining_water_secs // 60
        w_secs = remaining_water_secs % 60
        today_water = self.config.get_today_water_breaks_count()

        status_msg = f"Next Eye: {mins:02d}:{secs:02d} | Water: {w_mins:02d}:{w_secs:02d} | Today: {today_count}👁️ {today_water}💧"
        self.tray_mgr.update_status(status_msg, is_paused=False)

        if self.elapsed_active_secs >= work_target_secs:
            self.trigger_break_immediately()

        if self.config.get("water_reminder_enabled", True):
            self.elapsed_water_secs += 1
            water_target_secs = self.config.get("water_interval_mins", 60) * 60
            if self.elapsed_water_secs >= water_target_secs:
                self.trigger_water_reminder_immediately()

    def trigger_break_immediately(self) -> None:
        if self.is_in_break and self.popup.isVisible():
            return
        self.is_in_break = True
        break_duration = self.config.get("break_duration_secs", 20)
        work_interval = self.config.get("work_interval_mins", 20)
        sound_enabled = self.config.get("sound_enabled", True)

        self.popup.sound_enabled = sound_enabled

        if self.water_popup.isVisible():
            offset_y_water = self.popup.height() + 10
            self.water_popup.position_bottom_right(offset_y=offset_y_water)

        self.popup.start_break(break_duration, work_interval, offset_y=0)

    def trigger_water_reminder_immediately(self) -> None:
        self.elapsed_water_secs = 0
        if not self.config.get("water_reminder_enabled", True):
            return
        sound_enabled = self.config.get("sound_enabled", True)
        duration_secs = self.config.get("water_duration_secs", 20)
        water_interval = self.config.get("water_interval_mins", 60)

        self.water_popup.sound_enabled = sound_enabled

        offset_y = 0
        if self.is_in_break and self.popup.isVisible():
            offset_y = self.popup.height() + 10

        self.water_popup.show_water_reminder(duration_secs=duration_secs, water_interval_mins=water_interval, offset_y=offset_y)

    def _on_break_finished(self, completed: bool) -> None:
        self.is_in_break = False
        self.elapsed_active_secs = 0
        if completed:
            count = self.config.increment_today_break()
            self.tray_mgr.show_notification("Great Job! 🎯", f"Break completed! Total breaks today: {count}")
        if self.water_popup.isVisible():
            self.water_popup.position_bottom_right(offset_y=0)

    def _on_postpone_requested(self, mins: int) -> None:
        self.is_in_break = False
        work_target_secs = self.config.get("work_interval_mins", 20) * 60
        postpone_secs = mins * 60
        self.elapsed_active_secs = max(0, work_target_secs - postpone_secs)
        if self.water_popup.isVisible():
            self.water_popup.position_bottom_right(offset_y=0)

    def _on_water_break_finished(self, completed: bool) -> None:
        self.elapsed_water_secs = 0
        if completed:
            count = self.config.increment_today_water_break()
            self.tray_mgr.show_notification("Stay Hydrated! 💧", f"Water break completed! Total water breaks today: {count}")
        if self.popup.isVisible():
            self.popup.position_bottom_right(offset_y=0)

    def _on_water_postpone_requested(self, mins: int) -> None:
        water_target_secs = self.config.get("water_interval_mins", 60) * 60
        postpone_secs = mins * 60
        self.elapsed_water_secs = max(0, water_target_secs - postpone_secs)
        if self.popup.isVisible():
            self.popup.position_bottom_right(offset_y=0)

    def handle_pause_request(self, duration_mins: int) -> None:
        if duration_mins == 0:
            self.is_manual_paused = not self.is_manual_paused
            self.pause_until = None
        else:
            self.is_manual_paused = True
            self.pause_until = datetime.datetime.now() + datetime.timedelta(minutes=duration_mins)

    def show_settings(self) -> None:
        if not self.settings_dialog or not self.settings_dialog.isVisible():
            self.settings_dialog = SettingsDialog(self.config)
            self.settings_dialog.show()
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()

    def show_stats(self) -> None:
        if not self.settings_dialog or not self.settings_dialog.isVisible():
            self.settings_dialog = SettingsDialog(self.config)
            self.settings_dialog.tab_widget.setCurrentIndex(2)
            self.settings_dialog.show()
            self.settings_dialog.raise_()
            self.settings_dialog.activateWindow()

    def show_about(self) -> None:
        if not self.about_dialog or not self.about_dialog.isVisible():
            self.about_dialog = AboutDialog()
            self.about_dialog.show()
            self.about_dialog.raise_()
            self.about_dialog.activateWindow()

    def quit_app(self) -> None:
        QApplication.quit()
