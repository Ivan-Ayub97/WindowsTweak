import ctypes
import datetime
import locale
import os
import platform
import re
import shutil
import subprocess
import sys
import threading
import time
import webbrowser
import zipfile

# Try importing external libraries, if they fail, they will be installed below
try:
    import psutil
    import requests
    import wmi
    from PyQt5.QtCore import (QObject, QPoint, QSize, Qt, QThread, QTimer,
                              pyqtSignal, pyqtSlot)
    from PyQt5.QtGui import (QBrush, QColor, QCursor, QFont, QFontDatabase,
                             QIcon, QPainter, QPen)
    from PyQt5.QtWidgets import (QAbstractItemView, QApplication, QCheckBox,
                                 QComboBox, QFrame, QGridLayout, QGroupBox,
                                 QHBoxLayout, QHeaderView, QLabel, QLineEdit,
                                 QMainWindow, QMenu, QMessageBox, QProgressBar,
                                 QPushButton, QScrollArea, QSplitter,
                                 QStyleFactory, QTableWidget, QTableWidgetItem,
                                 QTabWidget, QTextEdit, QToolTip, QVBoxLayout,
                                 QWidget)
except ImportError:
    pass

# ============================================================================
# AUTOMATIC DEPENDENCY INSTALLATION
# ============================================================================


def install_and_restart():
    """Installs dependencies and restarts the script if libraries are missing."""
    required = ["PyQt5", "psutil", "requests", "wmi", "pywin32"]
    missing = []

    for lib in required:
        try:
            if lib == "pywin32":
                import win32api
            else:
                __import__(lib)
        except ImportError:
            missing.append(lib)

    if missing:
        print(f"Installing missing libraries: {', '.join(missing)}...")
        try:
            subprocess.check_call(
                [sys.executable, "-m", "pip", "install"] + missing)
            print("Restarting application...")
            os.execl(sys.executable, sys.executable, *sys.argv)
        except Exception as e:
            print(f"Error installing dependencies: {e}")
            input("Press Enter to exit...")
            sys.exit(1)


install_and_restart()

try:
    HAS_WMI = True
except ImportError:
    HAS_WMI = False

# ============================================================================
# CONFIGURATION & STYLES
# ============================================================================

THEME = {
    "bg_main": "#050300",
    "bg_panel": "#303030",
    "fg_text": "#34b00e",
    "accent": "#ebb331",       # Neon Green
    "accent_low": "#157417",   # Dark Green
    "alert": "#ff3e3e",        # Alert Red
    "warning": "#e22dd0",      # Warning Yellow
    "info": "#2e65fe",         # Info Blue
    "border": "#474749",
    "font": "Consolas" if platform.system() == "Windows" else "Monospace"
}

STYLESHEET = f"""
    QMainWindow, QWidget {{
        background-color: {THEME['bg_main']};
        color: {THEME['fg_text']};
        font-family: "{THEME['font']}";
    }}
    QGroupBox {{
        background-color: {THEME['bg_panel']};
        border: 1px solid {THEME['border']};
        border-radius: 8px;
        margin-top: 15px;
        font-weight: bold;
        color: {THEME['accent']};
        padding: 15px;
    }}
    QGroupBox::title {{
        subcontrol-origin: margin;
        subcontrol-position: top left;
        padding: 0 5px;
        left: 10px;
    }}
    QPushButton {{
        background-color: "#1a1a21";
        border: 1px solid {THEME['border']};
        color: {THEME['fg_text']};
        padding: 8px;
        border-radius: 4px;
    }}
    QPushButton:hover {{
        border: 1px solid {THEME['accent']};
        background-color: "#22222b";
    }}
    QPushButton:disabled {{
        color: #555;
        border-color: #333;
    }}
    QPushButton#danger_btn {{
        background-color: #330000;
        border: 1px solid {THEME['alert']};
        color: {THEME['alert']};
    }}
    QPushButton#danger_btn:hover {{ background-color: {THEME['alert']}; color: white; }}

    QPushButton#action_btn {{
        background-color: {THEME['accent_low']};
        border: 1px solid {THEME['accent']};
        color: white;
        font-weight: bold;
    }}
    QPushButton#action_btn:hover {{ background-color: {THEME['accent']}; color: black; }}

    QTabWidget::pane {{ border: 1px solid {THEME['border']}; }}
    QTabBar::tab {{
        background: {THEME['bg_panel']};
        padding: 10px 20px;
        border: 1px solid {THEME['border']};
        margin-right: 2px;
        border-top-left-radius: 4px;
        border-top-right-radius: 4px;
    }}
    QTabBar::tab:selected {{
        background: {THEME['bg_main']};
        border-bottom: 3px solid {THEME['accent']};
        color: {THEME['accent']};
        font-weight: bold;
    }}
    QTableWidget {{ background-color: {THEME['bg_panel']}; gridline-color: #333; border: none; }}
    QTableWidget::item {{ padding: 5px; }}
    QHeaderView::section {{ background-color: #222; color: {THEME['accent']}; border: 1px solid #333; padding: 4px; }}
    QLineEdit, QComboBox {{ background: "#1a1a21"; border: 1px solid {THEME['border']}; color: {THEME['accent']}; padding: 5px; }}
    QProgressBar {{ border: 1px solid #333; background: #000; text-align: center; border-radius: 2px; }}
    QProgressBar::chunk {{ background-color: {THEME['accent']}; }}
    QScrollBar:vertical {{ background: {THEME['bg_main']}; width: 12px; }}
    QScrollBar::handle:vertical {{ background: #333; min-height: 20px; border-radius: 6px; }}
    QScrollBar::handle:vertical:hover {{ background: {THEME['accent']}; }}
    QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0px; }}
"""

TOOLS_DB = {
    # ==================================================
    # Cleaning & Optimization (Portable)
    # ==================================================
    "Cleaning and Optimization": [
        {
            "id": "bleachbit",
            "name": "BleachBit Portable",
            "url": "https://download.bleachbit.org/BleachBit-4.6.0-portable.zip",
            "exe_64": "BleachBit.exe",
            "exe_32": "BleachBit.exe",
            "type": "zip",
            "desc": "Deep cleaning of temporary data and privacy traces (Open Source)."
        },
        {
            "id": "cleanmgrplus",
            "name": "Cleanmgr+",
            "url": "https://github.com/builtbybel/CleanmgrPlus/releases/download/1.50.1300/Cleanmgr+.zip",
            "exe_64": "Cleanmgr+.exe",
            "exe_32": "Cleanmgr+.exe",
            "type": "zip",
            "desc": "Modern version with rich features of the Windows Disk Cleanup utility."
        },
        {
            "id": "czkawka",
            "name": "Czkawka GUI",
            "url": "https://github.com/qarmin/czkawka/releases/latest/download/windows_czkawka_gui.zip",
            "exe_64": "czkawka_gui.exe",
            "exe_32": "czkawka_gui.exe",
            "type": "zip",
            "desc": "Deep cleaning of duplicate and broken files (Rust)."
        }
    ],

    # ==================================================
    # System Essentials (Portable)
    # ==================================================
    "System Essentials": [
        {
            "id": "peazip",
            "name": "PeaZip Portable",
            "url": "https://github.com/peazip/PeaZip/releases/download/9.7.1/peazip_portable-9.7.1.WIN64.zip",
            "exe_64": "peazip.exe",
            "exe_32": "peazip.exe",
            "type": "zip",
            "desc": "Powerful compressed file manager (7z, zip, rar) without installation."
        },
        {
            "id": "notepadplus",
            "name": "Notepad++ Portable",
            "url": "https://github.com/notepad-plus-plus/notepad-plus-plus/releases/download/v8.6.2/npp.8.6.2.portable.x64.zip",
            "exe_64": "notepad++.exe",
            "exe_32": "notepad++.exe",
            "type": "zip",
            "desc": "Lightweight and powerful code and text editor."
        },
    ],

    # ==================================================
    # Hardware Diagnosis (Portable)
    # ==================================================
    "Hardware Diagnosis": [
        {
            "id": "cpu_z",
            "name": "CPU-Z",
            "url": "https://download.cpuid.com/cpu-z/cpu-z_2.08-en.zip",
            "exe_64": "cpuz_x64.exe",
            "exe_32": "cpuz_x32.exe",
            "type": "zip",
            "desc": "Detailed information about the Processor, Motherboard and RAM."
        },
        {
            "id": "hwmonitor",
            "name": "HWMonitor",
            "url": "https://download.cpuid.com/hwmonitor/hwmonitor_1.52.zip",
            "exe_64": "HWMonitor_x64.exe",
            "exe_32": "HWMonitor_x32.exe",
            "type": "zip",
            "desc": "Real-time monitoring of voltages, temperatures, and fans."
        },
    ],

    # ==================================================
    # Security & Privacy (Portable)
    # ==================================================
    "Security and Privacy": [
        {
            "id": "adwcleaner",
            "name": "Malwarebytes AdwCleaner",
            "url": "https://downloads.malwarebytes.com/file/adwcleaner",
            "exe_64": "adwcleaner.exe",
            "exe_32": "adwcleaner.exe",
            "type": "exe",
            "desc": "Aggressively removes adware, spyware, and unwanted programs."
        },
        {
            "id": "shutup10",
            "name": "O&O ShutUp10++",
            "url": "https://dl5.oo-software.com/files/ooshutup10/OOSU10.exe",
            "exe_64": "OOSU10.exe",
            "exe_32": "OOSU10.exe",
            "type": "exe",
            "desc": "Disable telemetry and spying in Windows 10/11."
        },
    ],

    # ==================================================
    # Disk & Storage Analysis (Portable)
    # ==================================================
    "Disk and Storage Analysis": [
        {
            "id": "wiztree",
            "name": "WizTree Portable",
            "url": "https://diskanalyzer.com/files/wiztree_4_15_portable.zip",
            "exe_64": "WizTree64.exe",
            "exe_32": "WizTree.exe",
            "type": "zip",
            "desc": "The world's fastest disk analyzer (reads the MFT directly)."
        },
    ],

    # ==================================================
    # System Management (Portable)
    # ==================================================
    "System Management": [
        {
            "id": "geek",
            "name": "Geek Uninstaller",
            "url": "https://geekuninstaller.com/geek.zip",
            "exe_64": "geek.exe",
            "exe_32": "geek.exe",
            "type": "zip",
            "desc": "Simple, lightweight and very fast uninstaller for daily use."
        },
        {
            "id": "autoruns",
            "name": "Sysinternals Autoruns",
            "url": "https://download.sysinternals.com/files/Autoruns.zip",
            "exe_64": "Autoruns64.exe",
            "exe_32": "Autoruns.exe",
            "type": "zip",
            "desc": "The ultimate tool to see what starts up with Windows."
        },
        {
            "id": "process_explorer",
            "name": "Process Explorer",
            "url": "https://download.sysinternals.com/files/ProcessExplorer.zip",
            "exe_64": "procexp64.exe",
            "exe_32": "procexp.exe",
            "type": "zip",
            "desc": "Advanced task manager from Microsoft."
        },
        {
            "id": "tcpview",
            "name": "TCPView",
            "url": "https://download.sysinternals.com/files/TCPView.zip",
            "exe_64": "Tcpview64.exe",
            "exe_32": "Tcpview.exe",
            "type": "zip",
            "desc": "View all active internet connections by process."
        }
    ],
}


# ============================================================================
# AUXILIARY CLASSES AND WORKERS
# ============================================================================


class HoverButton(QPushButton):
    """Interactive button with mouse tracking."""
    on_hover = pyqtSignal(str)
    on_leave = pyqtSignal()

    def __init__(self, tool_data, is_installed, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.tool_data = tool_data
        self.setMouseTracking(True)
        self.setText(tool_data['name'])
        self.setCursor(Qt.PointingHandCursor)
        self.setFixedHeight(45)
        self.update_style(is_installed)

    def update_style(self, installed):
        base_style = f"""
            QPushButton {{
                background-color: #1a1a21;
                color: {THEME['fg_text']};
                border-radius: 4px;
                padding-left: 10px;
                text-align: left;
                font-size: 10pt;
            }}
            QPushButton:hover {{ background-color: #252530; border: 1px solid {THEME['accent']}; }}
        """
        border_color = THEME['accent'] if installed else THEME['border']
        border_width = "4px" if installed else "1px"
        # Left border indicates installation status
        extra = f"border: 1px solid {THEME['border']}; border-left: {border_width} solid {border_color};"
        self.setStyleSheet(base_style + extra)

    def enterEvent(self, event):
        self.on_hover.emit(
            f"<h3 style='color:{THEME['accent']}'>{self.tool_data['name']}</h3>"
            f"<p style='font-size:13px'>{self.tool_data['desc']}</p>"
            f"<p style='color:#888; font-size:11px'><i>ID: {self.tool_data['id']} | Type: {self.tool_data.get('type', 'N/A')}</i></p>"
        )
        super().enterEvent(event)

    def leaveEvent(self, event):
        self.on_leave.emit()
        super().leaveEvent(event)


class ModernGraph(QFrame):
    """Real-time modern graph."""

    def __init__(self, label, suffix="%", color="#00ff9d"):
        super().__init__()
        self.label = label
        self.suffix = suffix
        self.color = QColor(color)
        self.data = [0] * 60
        self.current = 0
        self.setMinimumHeight(120)
        self.setStyleSheet(
            f"border: 1px solid {THEME['border']}; background: #080808; border-radius: 6px;")

    def update_value(self, val):
        self.current = val
        self.data.append(val)
        self.data.pop(0)
        self.update()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        w, h = self.width(), self.height()

        # Grid
        painter.setPen(QPen(QColor("#151515"), 1))
        for i in range(0, w, 20):
            painter.drawLine(i, 0, i, h)
        for i in range(0, h, 20):
            painter.drawLine(0, i, w, i)

        # Big Text
        painter.setPen(QColor("white"))
        painter.setFont(QFont("Consolas", 14, QFont.Bold))
        painter.drawText(15, 30, f"{self.label}")

        painter.setFont(QFont("Consolas", 20, QFont.Bold))
        painter.setPen(self.color)
        painter.drawText(15, 60, f"{self.current}{self.suffix}")

        # Line Graph with Fill
        path_color = QColor(self.color)
        path_color.setAlpha(50)

        painter.setPen(QPen(self.color, 2))
        step = w / (len(self.data) - 1) if len(self.data) > 1 else w
        max_val = 100
        if self.label == "NET":
            max_val = max(max(self.data), 10)

        prev_x, prev_y = 0, h

        # Draw lines
        for i in range(len(self.data)):
            val = self.data[i]
            x = int(i * step)
            y = int(h - (val / max_val * (h - 10)))  # Bottom margin
            y = max(0, min(h, y))

            if i > 0:
                painter.drawLine(prev_x, prev_y, x, y)
            prev_x, prev_y = x, y


class DownloadWorker(QThread):
    """Background download and extraction."""
    progress = pyqtSignal(int)
    log = pyqtSignal(str, str)
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self, tool, dest_folder):
        super().__init__()
        self.tool = tool
        self.dest_folder = dest_folder

    def find_executable(self, search_path, exe_name):
        if os.path.isfile(os.path.join(search_path, exe_name)):
            return os.path.join(search_path, exe_name)
        # Deep search for the exe inside folders
        for root, dirs, files in os.walk(search_path):
            if exe_name in files:
                return os.path.join(root, exe_name)
            # Case insensitive check
            for f in files:
                if f.lower() == exe_name.lower():
                    return os.path.join(root, f)
        return None

    def run(self):
        tool = self.tool
        is_64 = sys.maxsize > 2**32
        target_exe = tool['exe_64'] if is_64 else tool['exe_32']
        tool_dir = os.path.join(self.dest_folder, tool['id'])
        os.makedirs(tool_dir, exist_ok=True)

        # 1. Check existence
        existing = self.find_executable(tool_dir, target_exe)
        if existing:
            self.log.emit(f"Launching {tool['name']} (Cache)...", "INFO")
            self.finished.emit(existing)
            return

        # 2. CMD Mode
        if tool['type'] == 'cmd':
            self.finished.emit("CMD_MODE")
            return

        if not tool.get('url'):
            self.error.emit(f"URL not defined for {tool['name']}")
            return

        # 3. Download
        self.log.emit(f"Downloading {tool['name']}...", "INFO")
        temp_file = os.path.join(tool_dir, f"temp_{tool['id']}.dat")

        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'}
            with requests.get(tool['url'], stream=True, headers=headers, timeout=60) as r:
                r.raise_for_status()
                total = int(r.headers.get('content-length', 0))
                dl = 0
                with open(temp_file, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)
                            dl += len(chunk)
                            if total > 0:
                                self.progress.emit(int(50 * dl / total))

            # 4. Process/Extract
            self.log.emit("Extracting/Installing...", "INFO")
            if tool['type'] == 'zip':
                try:
                    with zipfile.ZipFile(temp_file, 'r') as z:
                        z.extractall(tool_dir)
                except zipfile.BadZipFile:
                    self.error.emit("Corrupt ZIP file.")
                    return
                finally:
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
            elif tool['type'] == 'exe':
                final_path = os.path.join(tool_dir, target_exe)
                if os.path.exists(final_path):
                    os.remove(final_path)
                os.rename(temp_file, final_path)

            # 5. Finalize
            final = self.find_executable(tool_dir, target_exe)
            if final:
                self.progress.emit(100)
                self.finished.emit(final)
            else:
                self.error.emit(
                    f"Could not find {target_exe} after installation.")

        except Exception as e:
            self.error.emit(f"Error: {str(e)}")
            if os.path.exists(temp_file):
                os.remove(temp_file)


class SystemWorker(QThread):
    """Consolidated Worker for System Tasks (CMD and Python)."""
    log = pyqtSignal(str, str)  # Msg, Type
    progress = pyqtSignal(int)

    def __init__(self, tasks):
        super().__init__()
        self.tasks = tasks

    def run(self):
        sys_encoding = locale.getpreferredencoding()
        total = len(self.tasks)

        for i, task in enumerate(self.tasks):
            self.log.emit(f"Task {i+1}/{total}: {task['name']}", "INFO")

            try:
                if task['type'] == 'cmd':
                    self.progress.emit(-1)  # Indeterminate
                    self.log.emit(f"> {task['cmd']}", "CMD")

                    startupinfo = subprocess.STARTUPINFO()
                    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW

                    process = subprocess.Popen(
                        task['cmd'], shell=True,
                        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                        stdin=subprocess.DEVNULL, text=True,
                        encoding=sys_encoding, errors='replace',
                        startupinfo=startupinfo
                    )

                    while True:
                        line = process.stdout.readline()
                        if not line and process.poll() is not None:
                            break
                        if line:
                            clean = line.strip()
                            if clean:
                                # Simple percentage detection
                                match = re.search(r'(\d+)[.,]?\d*%', clean)
                                if match:
                                    self.progress.emit(int(match.group(1)))
                                self.log.emit(clean, "PROCESS")

                    if process.returncode == 0:
                        self.log.emit("Task finished successfully.", "SUCCESS")
                    else:
                        err = process.stderr.read()
                        self.log.emit(f"Warning/Error: {err}", "WARNING")

                elif task['type'] == 'py':
                    self.progress.emit(-1)
                    # Pass lambda compatible with (msg, type)
                    task['func'](lambda m, t="PROCESS": self.log.emit(m, t))
                    self.log.emit("Script finished.", "SUCCESS")

            except Exception as e:
                self.log.emit(f"CRITICAL ERROR: {e}", "ERROR")

            self.log.emit("-" * 30, "INFO")

        self.progress.emit(100)
        self.log.emit("Maintenance completed.", "SUCCESS")


class HardwareWorker(QThread):
    """Hardware and Battery Scan."""
    info_ready = pyqtSignal(str)

    def run(self):
        lines = []
        try:
            lines.append("=== OPERATING SYSTEM ===")
            lines.append(
                f"OS: {platform.system()} {platform.release()} ({platform.version()})")
            lines.append(f"Hostname: {platform.node()}")
            lines.append(f"Arch: {platform.machine()}")

            lines.append("\n=== PROCESSOR ===")
            lines.append(f"CPU: {platform.processor()}")
            lines.append(
                f"Cores: {psutil.cpu_count(logical=False)} Physical / {psutil.cpu_count(logical=True)} Logical")
            lines.append(f"Frequency: {psutil.cpu_freq().current:.2f} Mhz")

            lines.append("\n=== MEMORY (RAM) ===")
            mem = psutil.virtual_memory()
            lines.append(f"Total: {mem.total / (1024**3):.2f} GB")
            lines.append(f"Used: {mem.percent}%")
            lines.append(f"Available: {mem.available / (1024**3):.2f} GB")

            # Battery
            if hasattr(psutil, "sensors_battery"):
                batt = psutil.sensors_battery()
                if batt:
                    lines.append("\n=== BATTERY ===")
                    lines.append(f"Charge: {batt.percent}%")
                    lines.append(
                        f"Status: {'Charging' if batt.power_plugged else 'Discharging'}")
                    if batt.secsleft != psutil.POWER_TIME_UNLIMITED:
                        m, s = divmod(batt.secsleft, 60)
                        h, m = divmod(m, 60)
                        lines.append(f"Time remaining: {h}h {m}m")

            if HAS_WMI:
                try:
                    c = wmi.WMI()
                    lines.append("\n=== GPU & VIDEO ===")
                    for gpu in c.Win32_VideoController():
                        lines.append(f"- {gpu.Name}")
                        lines.append(f"  Driver: {gpu.DriverVersion}")
                        lines.append(
                            f"  Resolution: {gpu.CurrentHorizontalResolution}x{gpu.CurrentVerticalResolution}")

                    lines.append("\n=== BIOS & BOARD ===")
                    for board in c.Win32_BaseBoard():
                        lines.append(
                            f"Board: {board.Manufacturer} {board.Product}")
                    for bios in c.Win32_BIOS():
                        lines.append(
                            f"BIOS: {bios.Manufacturer} v{bios.Version}")
                except:
                    lines.append("\n[!] WMI Query Error.")
        except Exception as e:
            lines.append(f"\nScan Error: {e}")

        self.info_ready.emit("\n".join(lines))

# ============================================================================
# MAIN WINDOW
# ============================================================================


class UltimateMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("WindowsTweak - MAINTENANCE SUITE")
        self.setWindowIcon(QIcon("icon.ico"))
        self.resize(1300, 850)
        self.base_path = os.path.join(os.getcwd(), "DeckTools")

        self.init_ui()

        # Global Timer
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_monitor)
        self.timer.start(1500)

    def init_ui(self):
        main = QWidget()
        self.setCentralWidget(main)
        layout = QVBoxLayout(main)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # HEADER
        header = QHBoxLayout()
        header.addWidget(QLabel(f"<b>HOST:</b> {platform.node()}"))
        header.addStretch()

        is_admin = ctypes.windll.shell32.IsUserAnAdmin()
        lbl = QLabel(" ADMINISTRATOR " if is_admin else " LIMITED USER ")
        lbl.setStyleSheet(
            f"background: {'#004d2f' if is_admin else '#330000'}; color: white; border-radius: 4px; padding: 4px; font-weight: bold;")
        header.addWidget(lbl)
        layout.addLayout(header)

        # TABS
        self.tabs = QTabWidget()
        layout.addWidget(self.tabs)

        self.tab_monitor = QWidget()
        self.tab_tools = QWidget()
        self.tab_repair = QWidget()
        self.tab_process = QWidget()
        self.tab_info = QWidget()

        self.tabs.addTab(self.tab_monitor, "📊 MONITOR")
        self.tabs.addTab(self.tab_tools, "🛠 TOOLS")
        self.tabs.addTab(self.tab_repair, "🔧 REPAIR")
        self.tabs.addTab(self.tab_process, "⚙ PROCESSES")
        self.tabs.addTab(self.tab_info, "ℹ HARDWARE")

        self.setup_monitor()
        self.setup_tools()
        self.setup_repair()
        self.setup_process()
        self.setup_info()

        # CONSOLE
        grp_console = QGroupBox("ACTIVITY LOG")
        grp_console.setFixedHeight(180)
        clayout = QVBoxLayout(grp_console)

        self.console = QTextEdit()
        self.console.setReadOnly(True)
        self.console.setStyleSheet(
            "background: #000; border: none; font-family: Consolas; font-size: 10pt;")

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedHeight(8)
        self.progress_bar.setTextVisible(False)

        clayout.addWidget(self.console)
        clayout.addWidget(self.progress_bar)
        layout.addWidget(grp_console)

        self.log_msg(
            "System initialized. Welcome to WindowsTweak", "INFO")

    # --- LOGGER ---
    def log_msg(self, msg, mtype="INFO"):
        colors = {
            "INFO": "#e0e0e0", "CMD": "#00d4ff", "SUCCESS": "#00ff9d",
            "WARNING": "#ffcc00", "ERROR": "#ff3e3e", "PROCESS": "#888888"
        }
        icons = {"INFO": "ℹ️", "CMD": "⚡", "SUCCESS": "✅",
                 "WARNING": "⚠️", "ERROR": "❌", "PROCESS": " ›"}

        ts = datetime.datetime.now().strftime("%H:%M:%S")
        c = colors.get(mtype, "#fff")
        icon = icons.get(mtype, "")

        html = f"""<div style='margin:1px;'><span style='color:#555'>[{ts}]</span>
                   <span style='color:{c}'><b>{icon}</b> {msg}</span></div>"""

        self.console.append(html)
        sb = self.console.verticalScrollBar()
        sb.setValue(sb.maximum())

    # --- TAB 1: MONITOR ---
    def setup_monitor(self):
        layout = QGridLayout(self.tab_monitor)
        self.g_cpu = ModernGraph("CPU", "%", "#ff3e3e")
        self.g_ram = ModernGraph("RAM", "%", "#ffcc00")
        self.g_disk = ModernGraph("DISK", "%", "#00ff9d")
        self.g_net = ModernGraph("NET", " KB/s", "#00d4ff")

        layout.addWidget(self.g_cpu, 0, 0)
        layout.addWidget(self.g_ram, 0, 1)
        layout.addWidget(self.g_disk, 1, 0)
        layout.addWidget(self.g_net, 1, 1)

    def update_monitor(self):
        if self.tabs.currentIndex() != 0:
            return
        self.g_cpu.update_value(psutil.cpu_percent())
        self.g_ram.update_value(psutil.virtual_memory().percent)
        self.g_disk.update_value(psutil.disk_usage('/').percent)
        net = psutil.net_io_counters().bytes_recv / 1024
        # Modulo for visual effect on spikes
        self.g_net.update_value(round(net % 5000, 1))

    # --- TAB 2: TOOLS ---
    def setup_tools(self):
        layout = QHBoxLayout(self.tab_tools)

        # Scroll Area Left
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        container = QWidget()
        clayout = QVBoxLayout(container)
        clayout.setSpacing(15)

        self.tool_btns = {}

        for cat, tools in TOOLS_DB.items():
            gb = QGroupBox(cat)
            gl = QGridLayout(gb)
            for i, tool in enumerate(tools):
                installed = self.check_installed(tool)
                btn = HoverButton(tool, installed)
                btn.on_hover.connect(self.update_tool_info)
                btn.clicked.connect(lambda ch, t=tool,
                                    b=btn: self.launch_tool(t, b))
                gl.addWidget(btn, i//2, i % 2)
                self.tool_btns[tool['id']] = btn
            clayout.addWidget(gb)

        clayout.addStretch()
        scroll.setWidget(container)

        # Panel Right Info
        info_panel = QFrame()
        info_panel.setFixedWidth(320)
        info_panel.setStyleSheet(
            f"background: {THEME['bg_panel']}; border-left: 1px solid #333;")
        ilayout = QVBoxLayout(info_panel)

        self.txt_tool_info = QTextEdit()
        self.txt_tool_info.setReadOnly(True)
        self.txt_tool_info.setStyleSheet(
            "border:none; font-size:11pt; color: #ccc;")
        self.txt_tool_info.setHtml(
            "<br><center>Select a tool...</center>")

        ilayout.addWidget(QLabel("DETAILS"))
        ilayout.addWidget(self.txt_tool_info)

        layout.addWidget(scroll)
        layout.addWidget(info_panel)
        self.downloads = []  # Keep refs

    def check_installed(self, tool):
        if tool['type'] == 'cmd':
            return True
        exe = tool['exe_64'] if sys.maxsize > 2**32 else tool['exe_32']
        # Preliminary check path
        path = os.path.join(self.base_path, tool['id'])
        # Use simple exist check or deep check
        return os.path.exists(path) and any(exe.lower() in f.lower() for r, d, f in os.walk(path) for f in f)

    def update_tool_info(self, html):
        self.txt_tool_info.setHtml(html)

    def launch_tool(self, tool, btn):
        self.log_msg(f"Preparing {tool['name']}...", "INFO")
        btn.setEnabled(False)
        btn.setText("⏳ Processing...")

        worker = DownloadWorker(tool, self.base_path)
        worker.log.connect(self.log_msg)
        worker.progress.connect(self.progress_bar.setValue)
        worker.finished.connect(lambda p: self.on_tool_ready(p, btn, tool))
        worker.error.connect(lambda e: self.on_tool_error(e, btn, tool))

        self.downloads.append(worker)
        worker.start()

    def on_tool_ready(self, path, btn, tool):
        btn.setEnabled(True)
        btn.setText(tool['name'])
        btn.update_style(True)
        self.progress_bar.setValue(100)

        if path == "CMD_MODE":
            subprocess.Popen(tool['cmd'], shell=True)
        else:
            self.log_msg(f"Running: {path}", "SUCCESS")
            cwd = os.path.dirname(path)
            try:
                subprocess.Popen([path], cwd=cwd, shell=True)
            except Exception as e:
                self.log_msg(f"Error opening: {e}", "ERROR")

    def on_tool_error(self, err, btn, tool):
        btn.setEnabled(True)
        btn.setText(tool['name'])
        self.log_msg(err, "ERROR")
        QMessageBox.warning(self, "Error", err)

    # --- TAB 3: REPAIR AND NETWORK ---
    def setup_repair(self):
        layout = QHBoxLayout(self.tab_repair)

        # --- LEFT COLUMN: SYSTEM TASKS ---
        left_widget = QWidget()
        l_layout = QVBoxLayout(left_widget)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        cont = QWidget()
        cl = QVBoxLayout(cont)

        self.repair_checks = []

        tasks_db = {
            "🔧 System & Disk Integrity": [
                {"name": "SFC /Scannow (System File Checker)",
                 "type": "cmd", "cmd": "sfc /scannow"},
                {"name": "DISM RestoreHealth (Repair Image)", "type": "cmd",
                    "cmd": "DISM /Online /Cleanup-Image /RestoreHealth"},
                {"name": "CHKDSK (Scan Only)", "type": "py",
                 "func": self.task_chkdsk},
                {"name": "Clean Temporary Files", "type": "py",
                    "func": self.task_clean_temp}
            ],
            "🌐 Network & Internet": [
                {"name": "Flush DNS & Reset IP", "type": "py",
                    "func": self.task_net_reset},
                {"name": "Reset Winsock (Requires Restart)", "type": "cmd",
                    "cmd": "netsh winsock reset"}
            ],
            "🎨 UI & Applications": [
                {"name": "Reset Icon Cache", "type": "py",
                    "func": self.task_icon_cache},
                {"name": "Reset Windows Store", "type": "cmd", "cmd": "wsreset.exe"}
            ],
            "⚙️ Advanced System": [
                {"name": "Reset Windows Update Components", "type": "py",
                    "func": self.task_reset_update},
                {"name": "Restart Print Spooler", "type": "cmd",
                    "cmd": "net stop spooler && net start spooler"},
                {"name": "Generate Battery Report", "type": "py",
                    "func": self.task_battery_report}
            ]
        }

        for cat, tasks in tasks_db.items():
            gb = QGroupBox(cat)
            gl = QVBoxLayout(gb)
            for t in tasks:
                chk = QCheckBox(t['name'])
                self.repair_checks.append((chk, t))
                gl.addWidget(chk)
            cl.addWidget(gb)

        cont.layout().addStretch()
        scroll.setWidget(cont)
        l_layout.addWidget(scroll)

        btn_run = QPushButton("🚀 EXECUTE SELECTED TASKS")
        btn_run.setObjectName("action_btn")
        btn_run.setFixedHeight(50)
        btn_run.clicked.connect(self.run_maintenance)
        l_layout.addWidget(btn_run)

        # --- RIGHT COLUMN: NETWORK UTILITIES ---
        right_widget = QWidget()
        right_widget.setFixedWidth(320)
        r_layout = QVBoxLayout(right_widget)

        # 1. DNS Switcher
        gb_dns = QGroupBox("Quick DNS Switcher")
        gl_dns = QVBoxLayout(gb_dns)
        self.combo_dns = QComboBox()
        self.combo_dns.addItems(
            ["-- Select --", "Google (8.8.8.8)", "Cloudflare (1.1.1.1)", "Automatic (DHCP)"])
        btn_set_dns = QPushButton("Apply DNS")
        btn_set_dns.clicked.connect(self.set_dns)
        gl_dns.addWidget(self.combo_dns)
        gl_dns.addWidget(btn_set_dns)
        r_layout.addWidget(gb_dns)

        # 2. Wi-Fi Passwords
        gb_wifi = QGroupBox("Saved Wi-Fi Passwords")
        gl_wifi = QVBoxLayout(gb_wifi)
        self.txt_wifi = QTextEdit()
        self.txt_wifi.setReadOnly(True)
        btn_get_wifi = QPushButton("🔍 Reveal Keys")
        btn_get_wifi.clicked.connect(self.get_wifi_keys)
        gl_wifi.addWidget(btn_get_wifi)
        gl_wifi.addWidget(self.txt_wifi)
        r_layout.addWidget(gb_wifi)

        layout.addWidget(left_widget)
        layout.addWidget(right_widget)

    def run_maintenance(self):
        selected = [t for chk, t in self.repair_checks if chk.isChecked()]
        if not selected:
            QMessageBox.information(
                self, "Info", "Select at least one task.")
            return

        self.sys_worker = SystemWorker(selected)
        self.sys_worker.log.connect(self.log_msg)
        self.sys_worker.progress.connect(self.progress_bar.setValue)
        self.sys_worker.start()

    # Python Tasks
    def task_chkdsk(self, log_func):
        drives = [p.device.replace("\\", "")
                  for p in psutil.disk_partitions() if 'fixed' in p.opts]
        for d in drives:
            log_func(f"Scanning {d}...", "CMD")
            subprocess.run(f"chkdsk {d} /scan", shell=True)

    def task_clean_temp(self, log_func):
        folders = [os.environ.get(
            "TEMP"), r"C:\Windows\Temp", r"C:\Windows\Prefetch"]
        for folder in folders:
            if not folder:
                continue
            log_func(f"Cleaning: {folder}", "INFO")
            try:
                shutil.rmtree(folder, ignore_errors=True)
                os.makedirs(folder, exist_ok=True)
            except:
                pass

    def task_net_reset(self, log_func):
        cmds = ["ipconfig /release", "ipconfig /renew",
                "ipconfig /flushdns", "netsh int ip reset"]
        for c in cmds:
            log_func(f"Exec: {c}", "CMD")
            subprocess.run(c, shell=True)

    def task_icon_cache(self, log_func):
        log_func("Restarting Explorer and clearing cache...", "WARNING")
        subprocess.run("taskkill /IM explorer.exe /F", shell=True)
        db = os.path.join(os.environ["LOCALAPPDATA"], "IconCache.db")
        if os.path.exists(db):
            os.remove(db)
        subprocess.run("start explorer.exe", shell=True)

    def task_reset_update(self, log_func):
        log_func("Stopping Update Services...", "INFO")
        subprocess.run("net stop wuauserv", shell=True)
        subprocess.run("net stop cryptSvc", shell=True)
        subprocess.run("net stop bits", shell=True)
        subprocess.run("net stop msiserver", shell=True)

        log_func("Renaming SoftwareDistribution...", "INFO")
        sw_dist = r"C:\Windows\SoftwareDistribution"
        if os.path.exists(sw_dist):
            try:
                os.rename(sw_dist, sw_dist + ".old")
            except:
                pass

        cat_root = r"C:\Windows\System32\catroot2"
        if os.path.exists(cat_root):
            try:
                os.rename(cat_root, cat_root + ".old")
            except:
                pass

        log_func("Restarting Services...", "INFO")
        subprocess.run("net start wuauserv", shell=True)
        subprocess.run("net start cryptSvc", shell=True)
        subprocess.run("net start bits", shell=True)
        subprocess.run("net start msiserver", shell=True)

    def task_battery_report(self, log_func):
        path = os.path.join(os.getcwd(), "battery_report.html")
        log_func(f"Generating report at {path}", "INFO")
        subprocess.run(
            f"powercfg /batteryreport /output \"{path}\"", shell=True)
        if os.path.exists(path):
            webbrowser.open(path)

    # Right Panel Functions
    def set_dns(self):
        sel = self.combo_dns.currentIndex()
        if sel == 0:
            return

        cmd = ""
        desc = ""
        if sel == 1:  # Google
            cmd = 'netsh interface ip set dns "Wi-Fi" static 8.8.8.8 && netsh interface ip add dns "Wi-Fi" 8.8.4.4 index=2'
            desc = "Google DNS"
        elif sel == 2:  # Cloudflare
            cmd = 'netsh interface ip set dns "Wi-Fi" static 1.1.1.1 && netsh interface ip add dns "Wi-Fi" 1.0.0.1 index=2'
            desc = "Cloudflare DNS"
        elif sel == 3:  # DHCP
            cmd = 'netsh interface ip set dns "Wi-Fi" dhcp'
            desc = "DHCP"

        # Try for Ethernet too
        cmd_eth = cmd.replace('"Wi-Fi"', '"Ethernet"')

        self.log_msg(f"Changing DNS to {desc}...", "CMD")
        subprocess.run(cmd, shell=True)
        subprocess.run(cmd_eth, shell=True)
        self.log_msg("DNS configuration applied (Wi-Fi/Ethernet).", "SUCCESS")

    def get_wifi_keys(self):
        self.txt_wifi.setText("Scanning...")
        self.log_msg("Getting WLAN profiles...", "INFO")
        try:
            out = subprocess.check_output(
                "netsh wlan show profiles", shell=True).decode('cp850', errors='ignore')
            profiles = [line.split(":")[1].strip() for line in out.splitlines(
            ) if "All User Profile" in line]

            result = ""
            for p in profiles:
                try:
                    p_info = subprocess.check_output(
                        f'netsh wlan show profile name="{p}" key=clear', shell=True).decode('cp850', errors='ignore')
                    match = re.search(
                        r"Key Content\s*:\s*(.*)", p_info)
                    key = match.group(1) if match else "N/A"
                    result += f"SSID: {p}\nPASS: {key}\n{'-'*20}\n"
                except:
                    pass
            self.txt_wifi.setText(
                result if result else "No profiles found.")
        except Exception as e:
            self.txt_wifi.setText(f"Error: {e}")

    # --- TAB 4: PROCESSES ---
    def setup_process(self):
        layout = QVBoxLayout(self.tab_process)

        h = QHBoxLayout()
        self.txt_proc_filter = QLineEdit()
        self.txt_proc_filter.setPlaceholderText("Filter name...")
        self.txt_proc_filter.textChanged.connect(self.refresh_processes)

        btn_ref = QPushButton("Refresh")
        btn_ref.clicked.connect(self.refresh_processes)

        h.addWidget(self.txt_proc_filter)
        h.addWidget(btn_ref)
        layout.addLayout(h)

        self.tbl_proc = QTableWidget()
        self.tbl_proc.setColumnCount(4)
        self.tbl_proc.setHorizontalHeaderLabels(
            ["PID", "Name", "Memory (MB)", "Status"])
        self.tbl_proc.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.tbl_proc.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.tbl_proc.setContextMenuPolicy(Qt.CustomContextMenu)
        self.tbl_proc.customContextMenuRequested.connect(self.proc_menu)

        layout.addWidget(self.tbl_proc)
        QTimer.singleShot(1000, self.refresh_processes)

    def refresh_processes(self):
        if self.tabs.currentIndex() != 3:
            return

        filter_txt = self.txt_proc_filter.text().lower()
        self.tbl_proc.setSortingEnabled(False)
        self.tbl_proc.setRowCount(0)

        for p in psutil.process_iter(['pid', 'name', 'memory_info', 'status']):
            try:
                if filter_txt and filter_txt not in p.info['name'].lower():
                    continue

                r = self.tbl_proc.rowCount()
                self.tbl_proc.insertRow(r)

                # PID
                it_pid = QTableWidgetItem()
                it_pid.setData(Qt.DisplayRole, p.info['pid'])
                self.tbl_proc.setItem(r, 0, it_pid)

                # Name
                self.tbl_proc.setItem(r, 1, QTableWidgetItem(p.info['name']))

                # Mem
                mem = round(p.info['memory_info'].rss / 1024 / 1024, 1)
                it_mem = QTableWidgetItem()
                it_mem.setData(Qt.DisplayRole, mem)
                self.tbl_proc.setItem(r, 2, it_mem)

                # Status
                self.tbl_proc.setItem(r, 3, QTableWidgetItem(p.info['status']))

            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass
        self.tbl_proc.setSortingEnabled(True)

    def proc_menu(self, pos):
        row = self.tbl_proc.rowAt(pos.y())
        if row < 0:
            return

        pid = int(self.tbl_proc.item(row, 0).text())
        name = self.tbl_proc.item(row, 1).text()

        menu = QMenu()
        act_kill = menu.addAction("❌ Kill Process")
        act_susp = menu.addAction("⏸ Suspend")
        act_res = menu.addAction("▶ Resume")

        action = menu.exec_(self.tbl_proc.viewport().mapToGlobal(pos))

        try:
            p = psutil.Process(pid)
            if action == act_kill:
                p.kill()
                self.log_msg(f"Process {name} killed.", "WARNING")
            elif action == act_susp:
                p.suspend()
                self.log_msg(f"Process {name} suspended.", "INFO")
            elif action == act_res:
                p.resume()
                self.log_msg(f"Process {name} resumed.", "SUCCESS")

            QTimer.singleShot(500, self.refresh_processes)
        except Exception as e:
            QMessageBox.critical(
                self, "Error", f"Action failed: {e}")

    # --- TAB 5: HARDWARE ---
    def setup_info(self):
        layout = QVBoxLayout(self.tab_info)
        self.txt_hw = QTextEdit()
        self.txt_hw.setReadOnly(True)
        self.txt_hw.setStyleSheet(
            "font-size:12pt; color: #fff; line-height: 1.5;")

        btn = QPushButton("🔄 SCAN HARDWARE")
        btn.clicked.connect(self.scan_hardware)

        layout.addWidget(self.txt_hw)
        layout.addWidget(btn)
        QTimer.singleShot(2000, self.scan_hardware)

    def scan_hardware(self):
        self.txt_hw.setText("Scanning components... Please wait.")
        self.hw_worker = HardwareWorker()
        self.hw_worker.info_ready.connect(self.txt_hw.setText)
        self.hw_worker.start()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(STYLESHEET)

    win = UltimateMainWindow()
    win.show()
    sys.exit(app.exec_())
