import random
from PySide6.QtCore import Qt, QTimer, Signal, QRectF
from PySide6.QtGui import QColor, QPainter, QPen, QFont, QGuiApplication
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QGraphicsDropShadowEffect, QFrame, QSpinBox
)
from src.system_utils import GentleAudioPlayer


class CircularProgressBar(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.total_seconds = 20
        self.remaining_seconds = 20
        self.setMinimumSize(110, 110)

    def set_progress(self, remaining: int, total: int) -> None:
        self.remaining_seconds = remaining
        self.total_seconds = max(1, total)
        self.update()

    def paintEvent(self, event) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        side = min(self.width(), self.height())
        margin = 8
        rect = QRectF(margin, margin, side - margin * 2, side - margin * 2)

        pen_bg = QPen(QColor(40, 52, 75, 180), 6)
        pen_bg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_bg)
        painter.drawEllipse(rect)

        progress_ratio = max(0.0, min(1.0, self.remaining_seconds / max(1, self.total_seconds)))
        angle = int(360 * progress_ratio * 16)

        pen_fg = QPen(QColor(0, 210, 255), 6)
        pen_fg.setCapStyle(Qt.PenCapStyle.RoundCap)
        painter.setPen(pen_fg)
        painter.drawArc(rect, 90 * 16, angle)

        painter.setPen(QColor(255, 255, 255))
        font = QFont("Segoe UI", 22, QFont.Weight.Bold)
        painter.setFont(font)
        painter.drawText(rect, Qt.AlignmentFlag.AlignCenter, f"{int(self.remaining_seconds)}s")


class BreakPopupWindow(QWidget):
    break_finished = Signal(bool)
    postpone_requested = Signal(int)
    config_changed = Signal(int, int)

    def __init__(self, break_duration: int = 20, work_interval: int = 20, sound_enabled: bool = True, parent=None):
        super().__init__(parent)
        self.total_duration = break_duration
        self.remaining_duration = break_duration
        self.work_interval = work_interval
        self.sound_enabled = sound_enabled

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_tick)

        self._init_ui()

    def _init_ui(self) -> None:
        self.main_card = QFrame(self)
        self.main_card.setObjectName("MainCard")
        self.main_card.setStyleSheet("""
            QFrame#MainCard { background-color: #121826; border: 1px solid #1E293B; border-radius: 16px; }
            QLabel#TitleLabel { color: #00E5FF; font-family: 'Segoe UI'; font-size: 16px; font-weight: bold; }
            QLabel#TipLabel { color: #94A3B8; font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton { font-family: 'Segoe UI'; font-size: 12px; font-weight: 600; border-radius: 8px; padding: 6px 12px; }
            QPushButton#DoneBtn { background-color: #00C853; color: white; border: none; }
            QPushButton#DoneBtn:hover { background-color: #00E676; }
            QPushButton#PostponeBtn { background-color: #334155; color: #E2E8F0; border: none; }
            QPushButton#PostponeBtn:hover { background-color: #475569; }
            QPushButton#SkipBtn { background-color: transparent; color: #64748B; border: 1px solid #334155; }
            QPushButton#SkipBtn:hover { color: #94A3B8; border-color: #475569; }
            QPushButton#GearBtn { background-color: transparent; color: #64748B; font-size: 15px; border: none; padding: 2px 6px; }
            QPushButton#GearBtn:hover { color: #00E5FF; }
            QSpinBox { background-color: #0F172A; color: #00E5FF; border: 1px solid #334155; border-radius: 6px; padding: 2px 6px; font-weight: bold; }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        self.main_card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.main_card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        header_icon = QLabel("👀")
        header_icon.setStyleSheet("font-size: 24px;")

        title_label = QLabel("20-20-20 Eye Break")
        title_label.setObjectName("TitleLabel")

        self.btn_gear = QPushButton("⚙️")
        self.btn_gear.setObjectName("GearBtn")
        self.btn_gear.setToolTip("Quick Time Settings")
        self.btn_gear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_gear.clicked.connect(self._toggle_quick_settings)

        header_layout.addWidget(header_icon)
        header_layout.addWidget(title_label, 1)
        header_layout.addWidget(self.btn_gear)
        card_layout.addLayout(header_layout)

        # Quick Config Frame
        self.quick_config_frame = QFrame()
        self.quick_config_frame.setStyleSheet("""
            QFrame { background-color: #0F172A; border: 1px solid #334155; border-radius: 10px; padding: 6px 10px; }
            QLabel { color: #CBD5E1; font-size: 11px; font-weight: 600; }
        """)
        qc_layout = QHBoxLayout(self.quick_config_frame)
        qc_layout.setContentsMargins(8, 6, 8, 6)
        qc_layout.setSpacing(8)

        qc_layout.addWidget(QLabel("Break Time:"))
        self.spin_break_time = QSpinBox()
        self.spin_break_time.setRange(5, 300)
        self.spin_break_time.setSuffix("s")
        self.spin_break_time.setValue(self.total_duration)
        qc_layout.addWidget(self.spin_break_time)

        qc_layout.addWidget(QLabel("Every:"))
        self.spin_work_time = QSpinBox()
        self.spin_work_time.setRange(1, 120)
        self.spin_work_time.setSuffix("m")
        self.spin_work_time.setValue(self.work_interval)
        qc_layout.addWidget(self.spin_work_time)

        btn_apply = QPushButton("Apply")
        btn_apply.setStyleSheet("background-color: #0284C7; color: white; border-radius: 4px; padding: 4px 8px;")
        btn_apply.clicked.connect(self._apply_quick_settings)
        qc_layout.addWidget(btn_apply)

        self.quick_config_frame.setVisible(False)
        card_layout.addWidget(self.quick_config_frame)

        # Body
        body_layout = QHBoxLayout()
        body_layout.setSpacing(14)

        self.progress_bar = CircularProgressBar()
        body_layout.addWidget(self.progress_bar)

        tip_box = QVBoxLayout()
        self.tip_title = QLabel(f"Look at something <b>20 feet away</b> for <b>{self.total_duration} seconds</b>.")
        self.tip_title.setObjectName("TipLabel")
        self.tip_title.setWordWrap(True)

        tips_list = [
            "💡 Blink slowly to moisten your eyes.",
            "🌿 Look out the window at trees or distant objects.",
            "🧘 Relax your shoulders & take a deep breath."
        ]
        tip_detail = QLabel(random.choice(tips_list))
        tip_detail.setStyleSheet("color: #64748B; font-size: 11px; font-style: italic;")
        tip_detail.setWordWrap(True)

        tip_box.addWidget(self.tip_title)
        tip_box.addWidget(tip_detail)
        tip_box.addStretch()
        body_layout.addLayout(tip_box, 1)

        card_layout.addLayout(body_layout)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_skip = QPushButton("Skip")
        self.btn_skip.setObjectName("SkipBtn")
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.clicked.connect(self._on_skip)

        self.btn_postpone = QPushButton("+5 Min")
        self.btn_postpone.setObjectName("PostponeBtn")
        self.btn_postpone.setToolTip("Postpone break for 5 minutes")
        self.btn_postpone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_postpone.clicked.connect(self._on_postpone)

        self.btn_done = QPushButton("Complete")
        self.btn_done.setObjectName("DoneBtn")
        self.btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_done.clicked.connect(self._on_complete)

        btn_layout.addWidget(self.btn_skip)
        btn_layout.addWidget(self.btn_postpone)
        btn_layout.addWidget(self.btn_done)

        card_layout.addLayout(btn_layout)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.addWidget(self.main_card)

        self.resize(360, 240)

    def _toggle_quick_settings(self) -> None:
        visible = not self.quick_config_frame.isVisible()
        self.quick_config_frame.setVisible(visible)
        if visible:
            self.spin_break_time.setValue(self.total_duration)
            self.spin_work_time.setValue(self.work_interval)
            self.resize(360, 290)
        else:
            self.resize(360, 240)
        self.position_bottom_right()

    def _apply_quick_settings(self) -> None:
        new_break_secs = self.spin_break_time.value()
        new_work_mins = self.spin_work_time.value()

        self.total_duration = new_break_secs
        self.work_interval = new_work_mins

        if self.remaining_duration > self.total_duration:
            self.remaining_duration = self.total_duration

        self.tip_title.setText(f"Look at something <b>20 feet away</b> for <b>{self.total_duration} seconds</b>.")
        self.progress_bar.set_progress(self.remaining_duration, self.total_duration)

        self.quick_config_frame.setVisible(False)
        self.resize(360, 240)
        self.position_bottom_right()
        self.config_changed.emit(new_work_mins, new_break_secs)

    def position_bottom_right(self, offset_y: int = 0) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            self.move(g.right() - self.width() - 16, g.bottom() - self.height() - 16 - offset_y)

    def start_break(self, duration_secs: int = 20, work_interval_mins: int = 20, offset_y: int = 0) -> None:
        self.total_duration = duration_secs
        self.work_interval = work_interval_mins
        self.remaining_duration = duration_secs

        self.tip_title.setText(f"Look at something <b>20 feet away</b> for <b>{self.total_duration} seconds</b>.")
        self.progress_bar.set_progress(self.remaining_duration, self.total_duration)

        self.quick_config_frame.setVisible(False)
        self.resize(360, 240)
        self.position_bottom_right(offset_y)
        self.show()
        self.raise_()
        self.activateWindow()

        GentleAudioPlayer.play_chime(self.sound_enabled)
        self.timer.start()

    def _on_tick(self) -> None:
        self.remaining_duration -= 1
        if self.remaining_duration <= 0:
            self.progress_bar.set_progress(0, self.total_duration)
            self.timer.stop()
            GentleAudioPlayer.play_chime(self.sound_enabled)
            self._on_complete()
        else:
            self.progress_bar.set_progress(self.remaining_duration, self.total_duration)

    def _on_complete(self) -> None:
        self.timer.stop()
        self.hide()
        self.break_finished.emit(True)

    def _on_skip(self) -> None:
        self.timer.stop()
        self.hide()
        self.break_finished.emit(False)

    def _on_postpone(self) -> None:
        self.timer.stop()
        self.hide()
        self.postpone_requested.emit(5)


class WaterPopupWindow(QWidget):
    break_finished = Signal(bool)
    postpone_requested = Signal(int)
    config_changed = Signal(int, int)
    dismissed = Signal()

    def __init__(self, water_duration: int = 20, water_interval: int = 60, sound_enabled: bool = True, parent=None):
        super().__init__(parent)
        self.total_duration = water_duration
        self.remaining_seconds = water_duration
        self.water_interval = water_interval
        self.sound_enabled = sound_enabled

        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        self.timer = QTimer(self)
        self.timer.setInterval(1000)
        self.timer.timeout.connect(self._on_tick)

        self._init_ui()

    def _init_ui(self) -> None:
        self.main_card = QFrame(self)
        self.main_card.setObjectName("MainCard")
        self.main_card.setStyleSheet("""
            QFrame#MainCard { background-color: #121826; border: 1px solid #1E293B; border-radius: 16px; }
            QLabel#TitleLabel { color: #00E5FF; font-family: 'Segoe UI'; font-size: 16px; font-weight: bold; }
            QLabel#TipLabel { color: #94A3B8; font-family: 'Segoe UI'; font-size: 13px; }
            QPushButton { font-family: 'Segoe UI'; font-size: 12px; font-weight: 600; border-radius: 8px; padding: 6px 12px; }
            QPushButton#DoneBtn { background-color: #0284C7; color: white; border: none; }
            QPushButton#DoneBtn:hover { background-color: #0369A1; }
            QPushButton#PostponeBtn { background-color: #334155; color: #E2E8F0; border: none; }
            QPushButton#PostponeBtn:hover { background-color: #475569; }
            QPushButton#SkipBtn { background-color: transparent; color: #64748B; border: 1px solid #334155; }
            QPushButton#SkipBtn:hover { color: #94A3B8; border-color: #475569; }
            QPushButton#GearBtn { background-color: transparent; color: #64748B; font-size: 15px; border: none; padding: 2px 6px; }
            QPushButton#GearBtn:hover { color: #00E5FF; }
            QSpinBox { background-color: #0F172A; color: #00E5FF; border: 1px solid #334155; border-radius: 6px; padding: 2px 6px; font-weight: bold; }
        """)

        shadow = QGraphicsDropShadowEffect(self)
        shadow.setBlurRadius(24)
        shadow.setColor(QColor(0, 0, 0, 160))
        shadow.setOffset(0, 8)
        self.main_card.setGraphicsEffect(shadow)

        card_layout = QVBoxLayout(self.main_card)
        card_layout.setContentsMargins(18, 16, 18, 16)
        card_layout.setSpacing(10)

        # Header
        header_layout = QHBoxLayout()
        header_icon = QLabel("💧")
        header_icon.setStyleSheet("font-size: 24px;")

        title_label = QLabel("Drink Water")
        title_label.setObjectName("TitleLabel")

        self.btn_gear = QPushButton("⚙️")
        self.btn_gear.setObjectName("GearBtn")
        self.btn_gear.setToolTip("Quick Water Settings")
        self.btn_gear.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_gear.clicked.connect(self._toggle_quick_settings)

        header_layout.addWidget(header_icon)
        header_layout.addWidget(title_label, 1)
        header_layout.addWidget(self.btn_gear)
        card_layout.addLayout(header_layout)

        # Quick Config Frame
        self.quick_config_frame = QFrame()
        self.quick_config_frame.setStyleSheet("""
            QFrame { background-color: #0F172A; border: 1px solid #334155; border-radius: 10px; padding: 6px 10px; }
            QLabel { color: #CBD5E1; font-size: 11px; font-weight: 600; }
        """)
        qc_layout = QHBoxLayout(self.quick_config_frame)
        qc_layout.setContentsMargins(8, 6, 8, 6)
        qc_layout.setSpacing(8)

        qc_layout.addWidget(QLabel("Hold Time:"))
        self.spin_break_time = QSpinBox()
        self.spin_break_time.setRange(5, 300)
        self.spin_break_time.setSuffix("s")
        self.spin_break_time.setValue(self.total_duration)
        qc_layout.addWidget(self.spin_break_time)

        qc_layout.addWidget(QLabel("Every:"))
        self.spin_work_time = QSpinBox()
        self.spin_work_time.setRange(1, 240)
        self.spin_work_time.setSuffix("m")
        self.spin_work_time.setValue(self.water_interval)
        qc_layout.addWidget(self.spin_work_time)

        btn_apply = QPushButton("Apply")
        btn_apply.setStyleSheet("background-color: #0284C7; color: white; border-radius: 4px; padding: 4px 8px;")
        btn_apply.clicked.connect(self._apply_quick_settings)
        qc_layout.addWidget(btn_apply)

        self.quick_config_frame.setVisible(False)
        card_layout.addWidget(self.quick_config_frame)

        # Body Message & Tips
        body_layout = QVBoxLayout()
        body_layout.setSpacing(4)

        self.tip_title = QLabel("Stay hydrated! Please drink a glass of water.")
        self.tip_title.setObjectName("TipLabel")
        self.tip_title.setWordWrap(True)

        tips_list = [
            "💡 Drinking water boosts energy and focus.",
            "🌿 Keep a water bottle at your desk.",
            "💧 Proper hydration reduces eye dryness and fatigue."
        ]
        self.tip_detail = QLabel(random.choice(tips_list))
        self.tip_detail.setStyleSheet("color: #64748B; font-size: 11px; font-style: italic;")
        self.tip_detail.setWordWrap(True)

        body_layout.addWidget(self.tip_title)
        body_layout.addWidget(self.tip_detail)
        card_layout.addLayout(body_layout)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)

        self.btn_skip = QPushButton("Skip")
        self.btn_skip.setObjectName("SkipBtn")
        self.btn_skip.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_skip.clicked.connect(self._on_skip)

        self.btn_postpone = QPushButton("+5 Min")
        self.btn_postpone.setObjectName("PostponeBtn")
        self.btn_postpone.setToolTip("Postpone water reminder for 5 minutes")
        self.btn_postpone.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_postpone.clicked.connect(self._on_postpone)

        self.btn_done = QPushButton(f"Dismiss ({self.remaining_seconds}s)")
        self.btn_done.setObjectName("DoneBtn")
        self.btn_done.setCursor(Qt.CursorShape.PointingHandCursor)
        self.btn_done.clicked.connect(self._on_complete)

        btn_layout.addWidget(self.btn_skip)
        btn_layout.addWidget(self.btn_postpone)
        btn_layout.addWidget(self.btn_done)

        card_layout.addLayout(btn_layout)

        outer_layout = QVBoxLayout(self)
        outer_layout.setContentsMargins(10, 10, 10, 10)
        outer_layout.addWidget(self.main_card)

        self.resize(360, 200)

    def _toggle_quick_settings(self) -> None:
        visible = not self.quick_config_frame.isVisible()
        self.quick_config_frame.setVisible(visible)
        if visible:
            self.spin_break_time.setValue(self.total_duration)
            self.spin_work_time.setValue(self.water_interval)
            self.resize(360, 250)
        else:
            self.resize(360, 200)

    def _apply_quick_settings(self) -> None:
        new_break_secs = self.spin_break_time.value()
        new_work_mins = self.spin_work_time.value()

        self.total_duration = new_break_secs
        self.water_interval = new_work_mins

        if self.remaining_seconds > self.total_duration:
            self.remaining_seconds = self.total_duration

        self.btn_done.setText(f"Dismiss ({self.remaining_seconds}s)")

        self.quick_config_frame.setVisible(False)
        self.resize(360, 200)
        self.config_changed.emit(new_work_mins, new_break_secs)

    def position_bottom_right(self, offset_y: int = 0) -> None:
        screen = QGuiApplication.primaryScreen()
        if screen:
            g = screen.availableGeometry()
            self.move(g.right() - self.width() - 16, g.bottom() - self.height() - 16 - offset_y)

    def show_water_reminder(self, duration_secs: int = 20, water_interval_mins: int = 60, offset_y: int = 0) -> None:
        self.total_duration = duration_secs
        self.water_interval = water_interval_mins
        self.remaining_seconds = duration_secs

        self.btn_done.setText(f"Dismiss ({self.remaining_seconds}s)")
        self.quick_config_frame.setVisible(False)
        self.resize(360, 200)
        self.position_bottom_right(offset_y)
        self.show()
        self.raise_()
        self.activateWindow()

        GentleAudioPlayer.play_chime(self.sound_enabled)
        self.timer.start()

    def _on_tick(self) -> None:
        self.remaining_seconds -= 1
        if self.remaining_seconds <= 0:
            self.timer.stop()
            self._on_complete()
        else:
            self.btn_done.setText(f"Dismiss ({self.remaining_seconds}s)")

    def _on_complete(self) -> None:
        self.timer.stop()
        self.hide()
        self.break_finished.emit(True)
        self.dismissed.emit()

    def _on_skip(self) -> None:
        self.timer.stop()
        self.hide()
        self.break_finished.emit(False)
        self.dismissed.emit()

    def _on_postpone(self) -> None:
        self.timer.stop()
        self.hide()
        self.postpone_requested.emit(5)
        self.dismissed.emit()
