# AutoCore for macOS

![AutoCore](https://img.shields.io/badge/macOS-Compatible-success)
![Version](https://img.shields.io/badge/version-1.0.0-blue)

## 🚀 Quick Download & Installation

You can download the pre-compiled `.app` entirely ready to use on macOS:
1. Go to the [Releases](https://github.com/elliotaussel/AutoCore/releases) page.
2. Download `AutoCore.dmg` or the ZIP file containing `AutoCore.app`.
3. Drag and drop it into your `Applications` folder.

## ⚠️ Important: How to make it work (macOS Permissions)

Because AutoCore simulates mouse clicks and reads keyboard inputs globally, macOS **will block it** unless you grant Accessibility permissions.

1. Open **System Settings** > **Privacy & Security** > **Accessibility**.
2. Click the `+` button (or simply toggle the switch if AutoCore is already in the list).
3. Select `AutoCore.app` and make sure the toggle is **ON**.

*(Note: If the app stops working after a macOS update, remove it from the list with the `-` button and re-add it).*

---

## About AutoCore

AutoCore is a lightweight, minimalistic macro recorder for macOS, heavily inspired by the simplicity of TinyTask on Windows. It allows you to record mouse and keyboard actions and play them back in loops, complete with custom hotkeys and idle time recording.

### Features
- 🖱️ **Record & Playback**: Accurately records mouse movements, clicks, and keystrokes.
- 🕒 **Idle Time Tracking**: Captures the exact timing between actions, including trailing idle time before you stop recording.
- ⌨️ **Custom Hotkeys**: Click to assign any key to start/stop recording and playback from the Options menu.
- 🔄 **Looping**: Set a specific number of loops or let it run continuously.
- 🛑 **Emergency Stop**: Press `ESC` at any time to instantly stop playback or recording.

### Usage
- **Record**: Click the Record button or press your custom Record hotkey. Do your actions.
- **Stop**: Click Stop or press the hotkey again.
- **Play**: Click Play or press your custom Play hotkey. The loops will execute automatically with a real-time progress timer.

## Code Quality & Contribution
AutoCore is designed to be as clean, readable, and native-feeling as possible using `PyQt6` and `pynput`.

---
*Created by [elliotaussel](https://github.com/elliotaussel)*
