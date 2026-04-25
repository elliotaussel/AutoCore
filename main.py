import sys
import time
import threading
import CoreFoundation
import Foundation
import AppKit
import Quartz
import ApplicationServices
import HIServices
import webbrowser
from PyQt6.QtWidgets import (QApplication, QWidget, QPushButton, QHBoxLayout, 
                             QVBoxLayout, QLabel, QSpinBox, QMenu, QMainWindow)
from PyQt6.QtCore import Qt, pyqtSignal, QObject, QTimer
from PyQt6.QtGui import QAction
from pynput import mouse, keyboard

class SignalEmitter(QObject):
    status_updated = pyqtSignal(str)
    btn_record_updated = pyqtSignal(str, str) # text, stylesheet
    btn_play_updated = pyqtSignal(str, str)
    toggle_record_signal = pyqtSignal()
    toggle_play_signal = pyqtSignal()
    timer_updated = pyqtSignal(str)
    hotkey_assigned = pyqtSignal(str, str) # target, key_name

class AutoCore(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("AutoCore")
        self.setFixedSize(400, 145)
        self.setWindowFlags(self.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        
        self.setStyleSheet("""
            QWidget {
                font-family: ".AppleSystemUIFont", Helvetica, Arial;
                font-size: 13px;
                background-color: #f5f5f7;
                color: #1d1d1f;
            }
            QPushButton {
                border-radius: 8px;
                border: 1px solid #d2d2d7;
                background-color: #ffffff;
                padding: 6px 14px;
            }
            QPushButton:hover {
                background-color: #e5e5ea;
            }
            QPushButton:pressed {
                background-color: #d1d1d6;
            }
            QPushButton:disabled {
                color: #8e8e93;
                background-color: #f2f2f7;
                border: 1px solid #e5e5ea;
            }
        """)

        self.events = []
        self.is_recording = False
        self.is_playing = False
        self.start_time = 0
        self.total_record_time = 0
        
        # Hotkeys
        self.record_hotkey = keyboard.Key.f8
        self.play_hotkey = keyboard.Key.f9
        self.assigning_record_key = False
        self.assigning_play_key = False
        self.record_hotkey_name = "F8"
        self.play_hotkey_name = "F9"

        self.mouse_controller = mouse.Controller()
        self.keyboard_controller = keyboard.Controller()

        self.emitter = SignalEmitter()
        self.emitter.status_updated.connect(self.update_status)
        self.emitter.btn_record_updated.connect(self.update_record_btn)
        self.emitter.btn_play_updated.connect(self.update_play_btn)
        self.emitter.toggle_record_signal.connect(self.toggle_record)
        self.emitter.toggle_play_signal.connect(self.toggle_play)
        self.emitter.timer_updated.connect(self.update_timer_label)
        self.emitter.hotkey_assigned.connect(self.on_hotkey_assigned)

        self.init_ui()
        
        # Timers
        self.action_timer = QTimer(self)
        self.action_timer.timeout.connect(self.update_timer)
        self.time_elapsed = 0
        self.current_loop = 0
        self.total_loops = 1

        # Start background listeners
        self.setup_listeners()

    def init_ui(self):
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(12)

        # Row 1: Actions
        row1 = QHBoxLayout()
        row1.setSpacing(10)

        self.btn_record = QPushButton(f"⏺ Rec ({self.record_hotkey_name})")
        self.btn_record.clicked.connect(self.toggle_record)
        self.btn_record.setMinimumHeight(30)
        row1.addWidget(self.btn_record)

        self.btn_play = QPushButton(f"▶ Play ({self.play_hotkey_name})")
        self.btn_play.clicked.connect(self.toggle_play)
        self.btn_play.setMinimumHeight(30)
        row1.addWidget(self.btn_play)

        self.btn_options = QPushButton("⚙ Options")
        self.btn_options.clicked.connect(self.show_options_menu)
        self.btn_options.setMinimumHeight(30)
        row1.addWidget(self.btn_options)

        main_layout.addLayout(row1)

        # Row 2: Settings
        row2 = QHBoxLayout()
        row2.setSpacing(10)

        self.lbl_loops = QLabel("Loops:")
        row2.addWidget(self.lbl_loops)

        self.spin_loops = QSpinBox()
        self.spin_loops.setRange(1, 9999)
        self.spin_loops.setValue(1)
        self.spin_loops.setFixedWidth(70)
        self.spin_loops.setMinimumHeight(28)
        self.spin_loops.setButtonSymbols(QSpinBox.ButtonSymbols.NoButtons)
        row2.addWidget(self.spin_loops)

        self.check_infinite = QPushButton("Continuous: OFF")
        self.check_infinite.setCheckable(True)
        self.check_infinite.clicked.connect(self.toggle_continuous)
        self.check_infinite.setMinimumHeight(30)
        row2.addWidget(self.check_infinite)
        
        row2.addStretch()  # pushes elements to the left

        main_layout.addLayout(row2)

        # Row 3: Status & Timer
        status_layout = QHBoxLayout()
        self.lbl_status = QLabel("Ready")
        self.lbl_status.setStyleSheet("color: #86868b;")
        
        self.lbl_timer = QLabel("00:00")
        self.lbl_timer.setStyleSheet("color: #86868b;")
        self.lbl_timer.setAlignment(Qt.AlignmentFlag.AlignRight)

        status_layout.addWidget(self.lbl_status)
        status_layout.addWidget(self.lbl_timer)

        main_layout.addLayout(status_layout)
        self.setLayout(main_layout)

    def toggle_continuous(self):
        if self.check_infinite.isChecked():
            self.check_infinite.setText("Continuous: ON")
            self.spin_loops.setEnabled(False)
        else:
            self.check_infinite.setText("Continuous: OFF")
            self.spin_loops.setEnabled(True)

    def show_options_menu(self):
        menu = QMenu(self)
        menu.setStyleSheet("""
            QMenu {
                background-color: #ffffff;
                border: 1px solid #d1d1d6;
                border-radius: 5px;
            }
            QMenu::item {
                padding: 6px 20px;
                background-color: transparent;
                color: #1d1d1f;
            }
            QMenu::item:selected {
                background-color: #007aff;
                color: white;
            }
        """)
        
        action_rec_key = QAction(f"Assign Record Key (Current: {self.record_hotkey_name})", self)
        action_rec_key.triggered.connect(self.start_assign_record_key)
        menu.addAction(action_rec_key)

        action_play_key = QAction(f"Assign Play Key (Current: {self.play_hotkey_name})", self)
        action_play_key.triggered.connect(self.start_assign_play_key)
        menu.addAction(action_play_key)

        menu.addSeparator()

        action_about = QAction("About AutoCore", self)
        action_about.triggered.connect(lambda: webbrowser.open("https://github.com/ELLIOT-USERNAME/AutoCore"))
        menu.addAction(action_about)

        menu.exec(self.btn_options.mapToGlobal(self.btn_options.rect().bottomLeft()))

    def start_assign_record_key(self):
        self.assigning_record_key = True
        self.emitter.status_updated.emit("Press ANY KEY for Record...")

    def start_assign_play_key(self):
        self.assigning_play_key = True
        self.emitter.status_updated.emit("Press ANY KEY for Play...")

    def on_hotkey_assigned(self, target, key_name):
        if target == "record":
            self.record_hotkey_name = key_name
            self.btn_record.setText(f"⏺ Rec ({key_name})")
        else:
            self.play_hotkey_name = key_name
            self.btn_play.setText(f"▶ Play ({key_name})")
        self.emitter.status_updated.emit("Ready")

    def update_status(self, text):
        self.lbl_status.setText(text)

    def update_record_btn(self, text, style):
        self.btn_record.setText(text)
        self.btn_record.setStyleSheet(style)

    def update_play_btn(self, text, style):
        self.btn_play.setText(text)
        self.btn_play.setStyleSheet(style)

    def update_timer_label(self, text):
        self.lbl_timer.setText(text)

    def update_timer(self):
        self.time_elapsed += 1
        mins, secs = divmod(self.time_elapsed, 60)
        time_str = f"{mins:02d}:{secs:02d}"
        
        if self.is_playing:
            total_text = "∞" if self.check_infinite.isChecked() else str(self.total_loops)
            self.lbl_timer.setText(f"Loop {self.current_loop}/{total_text} - {time_str}")
        else:
            self.lbl_timer.setText(time_str)

    def setup_listeners(self):
        self.mouse_listener = mouse.Listener(
            on_move=self.on_mouse_move,
            on_click=self.on_mouse_click,
            on_scroll=self.on_mouse_scroll
        )
        self.keyboard_listener = keyboard.Listener(
            on_press=self.on_key_press,
            on_release=self.on_key_release
        )
        self.mouse_listener.start()
        self.keyboard_listener.start()

    def clean_key_name(self, key):
        try:
            if hasattr(key, 'char') and key.char:
                return str(key.char).upper()
            return str(key.name).upper()
        except Exception:
            return str(key)

    def toggle_record(self):
        if self.is_playing:
            return

        if not self.is_recording:
            self.start_recording()
        else:
            self.stop_recording()

    def toggle_play(self):
        if self.is_recording:
            return

        if not self.is_playing:
            self.start_playing()
        else:
            self.stop_playing()

    def start_recording(self):
        self.events.clear()
        self.is_recording = True
        self.start_time = time.time()
        self.time_elapsed = 0
        self.action_timer.start(1000)
        
        self.emitter.btn_record_updated.emit("⏹ Stop Rec", "color: white; background-color: #ff3b30; border-color: #ff3b30;")
        self.emitter.status_updated.emit("Recording... (Press ESC to stop)")
        self.emitter.btn_play_updated.emit(f"▶ Play ({self.play_hotkey_name})", "color: #8e8e93;")
        self.btn_play.setEnabled(False)

    def stop_recording(self):
        self.is_recording = False
        self.total_record_time = time.time() - self.start_time
        self.action_timer.stop()
        
        self.emitter.btn_record_updated.emit(f"⏺ Rec ({self.record_hotkey_name})", "")
        self.emitter.btn_play_updated.emit(f"▶ Play ({self.play_hotkey_name})", "")
        self.btn_play.setEnabled(True)
        self.emitter.status_updated.emit(f"Recorded: {len(self.events)} actions")
        
        mins, secs = divmod(self.time_elapsed, 60)
        self.emitter.timer_updated.emit(f"Length: {mins:02d}:{secs:02d}")

    def start_playing(self):
        if not self.events:
            self.emitter.status_updated.emit("Nothing to play!")
            return

        self.is_playing = True
        self.btn_record.setEnabled(False)
        self.emitter.btn_play_updated.emit("⏹ Stop Play", "color: white; background-color: #ffcc00; border-color: #ffcc00;")
        self.emitter.btn_record_updated.emit(f"⏺ Rec ({self.record_hotkey_name})", "color: #8e8e93;")

        play_thread = threading.Thread(target=self.play_events, daemon=True)
        play_thread.start()

    def stop_playing(self):
        self.is_playing = False
        self.action_timer.stop()
        self.btn_record.setEnabled(True)
        self.emitter.btn_play_updated.emit(f"▶ Play ({self.play_hotkey_name})", "")
        self.emitter.btn_record_updated.emit(f"⏺ Rec ({self.record_hotkey_name})", "")
        self.emitter.status_updated.emit("Playback stopped")

    def play_events(self):
        self.total_loops = self.spin_loops.value()
        is_infinite = self.check_infinite.isChecked()
        self.current_loop = 1

        while self.is_playing and (is_infinite or self.current_loop <= self.total_loops):
            # Reset timer for each loop
            self.time_elapsed = 0
            self.action_timer.start(1000)
            
            elapsed_play_time = 0
            last_event_time = 0
            
            for event in self.events:
                if not self.is_playing:
                    break

                event_type, event_time, data = event
                
                # Wait until it's time to execute this event
                time_to_wait = event_time - last_event_time
                if time_to_wait > 0:
                    wait_accumulated = 0
                    while wait_accumulated < time_to_wait and self.is_playing:
                        time.sleep(0.01)
                        wait_accumulated += 0.01
                
                if not self.is_playing:
                    break

                try:
                    if event_type == 'mouse_move':
                        self.mouse_controller.position = data
                    elif event_type == 'mouse_click':
                        x, y, button, pressed = data
                        self.mouse_controller.position = (x, y)
                        if pressed:
                            self.mouse_controller.press(button)
                        else:
                            self.mouse_controller.release(button)
                    elif event_type == 'mouse_scroll':
                        x, y, dx, dy = data
                        self.mouse_controller.position = (x, y)
                        self.mouse_controller.scroll(dx, dy)
                    elif event_type == 'key_press':
                        self.keyboard_controller.press(data)
                    elif event_type == 'key_release':
                        self.keyboard_controller.release(data)
                except Exception as e:
                    print(f"Error during playback: {e}")

                last_event_time = event_time
                elapsed_play_time = event_time
            
            # Trailing idle time: wait for the remaining time of the record session
            if self.is_playing:
                time_to_wait_end = self.total_record_time - elapsed_play_time
                if time_to_wait_end > 0:
                    wait_accumulated = 0
                    while wait_accumulated < time_to_wait_end and self.is_playing:
                        time.sleep(0.01)
                        wait_accumulated += 0.01
            
            self.action_timer.stop()
            if not is_infinite:
                self.current_loop += 1

        if self.is_playing:
            self.emitter.toggle_play_signal.emit()

    def record_event(self, event_type, data):
        if self.is_recording:
            event_time = time.time() - self.start_time
            self.events.append((event_type, event_time, data))

    def on_mouse_move(self, x, y):
        self.record_event('mouse_move', (x, y))

    def on_mouse_click(self, x, y, button, pressed):
        self.record_event('mouse_click', (x, y, button, pressed))

    def on_mouse_scroll(self, x, y, dx, dy):
        self.record_event('mouse_scroll', (x, y, dx, dy))

    def on_key_press(self, key):
        # Emergency stop
        if key == keyboard.Key.esc:
            if self.is_recording:
                self.emitter.toggle_record_signal.emit()
            if self.is_playing:
                self.emitter.toggle_play_signal.emit()
            return

        if self.assigning_record_key:
            self.record_hotkey = key
            key_name = self.clean_key_name(key)
            self.emitter.hotkey_assigned.emit("record", key_name)
            self.assigning_record_key = False
            return
            
        if self.assigning_play_key:
            self.play_hotkey = key
            key_name = self.clean_key_name(key)
            self.emitter.hotkey_assigned.emit("play", key_name)
            self.assigning_play_key = False
            return

        # Check hotkeys
        if key == self.record_hotkey:
            self.emitter.toggle_record_signal.emit()
            return
        if key == self.play_hotkey:
            self.emitter.toggle_play_signal.emit()
            return
            
        self.record_event('key_press', key)

    def on_key_release(self, key):
        if not self.assigning_record_key and not self.assigning_play_key and key != self.record_hotkey and key != self.play_hotkey and key != keyboard.Key.esc:
            self.record_event('key_release', key)

def main():
    app = QApplication(sys.argv)
    window = AutoCore()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
