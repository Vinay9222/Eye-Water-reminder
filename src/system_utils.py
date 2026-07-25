import os
import sys
import io
import math
import wave
import struct
import ctypes
import winreg
import logging
import winsound
import datetime
import traceback
from logging.handlers import RotatingFileHandler
from typing import Optional

# Setup Application Directories
CONFIG_DIR = os.path.join(os.getenv('APPDATA', os.path.expanduser('~')), 'EyeReminder')
LOG_DIR = os.path.join(CONFIG_DIR, 'logs')
CRASH_DIR = os.path.join(CONFIG_DIR, 'crashes')
os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(CRASH_DIR, exist_ok=True)

LOG_FILE = os.path.join(LOG_DIR, 'eyereminder.log')


def get_resource_path(relative_path: str) -> str:
    """Get absolute path to resource, works for dev and for PyInstaller bundle."""
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, relative_path)


# --- Logging & Exception Handling ---
def setup_logger(name: str = "EyeReminder") -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    if not logger.handlers:
        file_handler = RotatingFileHandler(LOG_FILE, maxBytes=2 * 1024 * 1024, backupCount=3, encoding='utf-8')
        formatter = logging.Formatter('[%(asctime)s] [%(levelname)s] [%(filename)s:%(lineno)d]: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
    return logger


logger = setup_logger()


def handle_uncaught_exception(exc_type, exc_value, exc_traceback):
    if issubclass(exc_type, KeyboardInterrupt):
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    crash_filename = os.path.join(CRASH_DIR, f"crash_report_{timestamp}.log")
    tb_str = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))
    logger.critical(f"UNHANDLED CRASH OCCURRED:\n{tb_str}")

    try:
        with open(crash_filename, 'w', encoding='utf-8') as f:
            f.write(f"EyeReminder Crash Report - {timestamp}\n{'='*60}\n")
            f.write(f"Python: {sys.version}\nExe: {sys.executable}\n{'='*60}\n\n{tb_str}")
    except Exception:
        pass


sys.excepthook = handle_uncaught_exception


# --- Win32 Ctypes Structures ---
class LASTINPUTINFO(ctypes.Structure):
    _fields_ = [('cbSize', ctypes.c_uint), ('dwTime', ctypes.c_ulong)]


try:
    user32 = ctypes.windll.user32
    kernel32 = ctypes.windll.kernel32
except Exception:
    user32 = None
    kernel32 = None


def get_idle_duration_seconds() -> float:
    if not user32 or not kernel32:
        return 0.0
    last_input_info = LASTINPUTINFO()
    last_input_info.cbSize = ctypes.sizeof(LASTINPUTINFO)
    if user32.GetLastInputInfo(ctypes.byref(last_input_info)):
        try:
            millis = kernel32.GetTickCount64() - last_input_info.dwTime
        except AttributeError:
            millis = kernel32.GetTickCount() - last_input_info.dwTime
        return max(0.0, millis / 1000.0)
    return 0.0


def is_workstation_locked() -> bool:
    if not user32:
        return False
    try:
        hwnd = user32.GetForegroundWindow()
        if hwnd == 0:
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        buff = ctypes.create_unicode_buffer(length + 1)
        user32.GetWindowTextW(hwnd, buff, length + 1)
        return buff.value in ["Windows Default Lock Screen", "LockApp", "Sign in"]
    except Exception:
        return False


def set_autostart(enable: bool, app_name: str = "EyeReminder") -> bool:
    key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    if getattr(sys, 'frozen', False):
        exe_path = f'"{sys.executable}"'
    else:
        pythonw = os.path.join(os.path.dirname(sys.executable), "pythonw.exe")
        if not os.path.exists(pythonw):
            pythonw = sys.executable
        main_script = os.path.abspath(sys.argv[0])
        exe_path = f'"{pythonw}" "{main_script}"'

    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_ALL_ACCESS)
        if enable:
            winreg.SetValueEx(key, app_name, 0, winreg.REG_SZ, exe_path)
        else:
            try:
                winreg.DeleteValue(key, app_name)
            except FileNotFoundError:
                pass
        winreg.CloseKey(key)
        return True
    except Exception:
        return False


def is_in_lunch_break(start_str: str, end_str: str) -> bool:
    try:
        now = datetime.datetime.now().time()
        st = datetime.datetime.strptime(start_str, "%H:%M").time()
        et = datetime.datetime.strptime(end_str, "%H:%M").time()
        return st <= now <= et if st <= et else (now >= st or now <= et)
    except Exception:
        return False


# --- Audio Synthesizer ---
class GentleAudioPlayer:
    _cached_wav_data: Optional[bytes] = None

    @classmethod
    def generate_chime_wav(cls, sample_rate: int = 44100) -> bytes:
        if cls._cached_wav_data is not None:
            return cls._cached_wav_data

        notes = [(659.25, 0.25), (880.0, 0.4)]
        audio_data = bytearray()
        for freq, duration in notes:
            num_samples = int(sample_rate * duration)
            for i in range(num_samples):
                t = i / sample_rate
                envelope = math.exp(-t * 5.0)
                sample = int(32767 * 0.25 * envelope * math.sin(2 * math.pi * freq * t))
                audio_data.extend(struct.pack('<h', sample))

        wav_io = io.BytesIO()
        with wave.open(wav_io, 'wb') as wf:
            wf.setnchannels(1)
            wf.setsampwidth(2)
            wf.setframerate(sample_rate)
            wf.writeframes(audio_data)

        cls._cached_wav_data = wav_io.getvalue()
        return cls._cached_wav_data

    @classmethod
    def play_chime(cls, enabled: bool = True) -> None:
        if not enabled:
            return
        try:
            wav_bytes = cls.generate_chime_wav()
            winsound.PlaySound(wav_bytes, winsound.SND_MEMORY | winsound.SND_ASYNC)
        except Exception:
            try:
                winsound.MessageBeep(winsound.MB_ICONASTERISK)
            except Exception:
                pass
