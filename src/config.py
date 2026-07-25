import os
import json
import shutil
import datetime
from typing import Dict, Any

CONFIG_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'EyeReminder')
CONFIG_FILE = os.path.join(CONFIG_DIR, 'settings.json')
BACKUP_FILE = os.path.join(CONFIG_DIR, 'settings.json.bak')

DEFAULT_CONFIG: Dict[str, Any] = {
    "work_interval_mins": 20,
    "break_duration_secs": 20,
    "idle_pause_secs": 120,          # 2 minutes of no input -> pause timer
    "sound_enabled": True,
    "autostart_enabled": True,
    "lunch_break_enabled": True,
    "lunch_start_time": "13:00",
    "lunch_end_time": "14:00",
    "reset_on_lock": True,
    "water_reminder_enabled": True,
    "water_interval_mins": 60,
    "water_duration_secs": 20,
    "stats": {},                     # {"YYYY-MM-DD": count}
    "water_stats": {}                # {"YYYY-MM-DD": count}
}


class ConfigManager:
    """Manages application settings, automatic backups, stats, and import/export."""

    def __init__(self):
        os.makedirs(CONFIG_DIR, exist_ok=True)
        self.data: Dict[str, Any] = DEFAULT_CONFIG.copy()
        self.load()

    def load(self) -> None:
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    self.data.update(json.load(f))
            except Exception:
                self.restore_backup()
        else:
            self.save()

    def save(self) -> None:
        try:
            if os.path.exists(CONFIG_FILE):
                try:
                    shutil.copy(CONFIG_FILE, BACKUP_FILE)
                except Exception:
                    pass

            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
        except Exception:
            pass

    def restore_backup(self) -> bool:
        if os.path.exists(BACKUP_FILE):
            try:
                with open(BACKUP_FILE, 'r', encoding='utf-8') as f:
                    self.data.update(json.load(f))
                self.save()
                return True
            except Exception:
                pass
        return False

    def get(self, key: str, default: Any = None) -> Any:
        return self.data.get(key, default if default is not None else DEFAULT_CONFIG.get(key))

    def set(self, key: str, value: Any) -> None:
        self.data[key] = value
        self.save()

    def increment_today_break(self) -> int:
        today_str = datetime.date.today().isoformat()
        stats = self.data.setdefault("stats", {})
        stats[today_str] = stats.get(today_str, 0) + 1
        self.save()
        return stats[today_str]

    def get_today_breaks_count(self) -> int:
        today_str = datetime.date.today().isoformat()
        return self.data.get("stats", {}).get(today_str, 0)

    def increment_today_water_break(self) -> int:
        today_str = datetime.date.today().isoformat()
        stats = self.data.setdefault("water_stats", {})
        stats[today_str] = stats.get(today_str, 0) + 1
        self.save()
        return stats[today_str]

    def get_today_water_breaks_count(self) -> int:
        today_str = datetime.date.today().isoformat()
        return self.data.get("water_stats", {}).get(today_str, 0)

    def export_settings(self, target_filepath: str) -> bool:
        try:
            with open(target_filepath, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=4)
            return True
        except Exception:
            return False

    def import_settings(self, source_filepath: str) -> bool:
        try:
            with open(source_filepath, 'r', encoding='utf-8') as f:
                self.data.update(json.load(f))
            self.save()
            return True
        except Exception:
            return False
