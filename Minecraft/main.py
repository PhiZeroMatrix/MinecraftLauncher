import sys
import os
import minecraft_launcher_lib
import subprocess
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QLineEdit, QPushButton, QListWidget, 
                             QLabel, QProgressBar, QMessageBox)
from PySide6.QtCore import Qt, QThread, Signal
from PySide6.QtGui import QIcon, QPixmap

# --- LOGIKA BACKEND ---
class LaunchWorker(QThread):
    progress_update = Signal(int, int) 
    status_update = Signal(str)
    finished = Signal()

    def __init__(self, nickname, version, directory):
        super().__init__()
        self.nickname = nickname
        self.version = version
        self.directory = directory

    def run(self):
        def set_status(text): self.status_update.emit(text)
        def set_max(value): self.max_val = value
        def set_progress(value): self.progress_update.emit(value, self.max_val)

        callback = {
            "setStatus": set_status,
            "setProgress": set_progress,
            "setMax": set_max
        }

        try:
            self.status_update.emit(f"Checking/Downloading {self.version}...")
            minecraft_launcher_lib.install.install_minecraft_version(
                self.version, self.directory, callback=callback
            )

            options = {
                "username": self.nickname,
                "uuid": "",
                "token": ""
            }

            command = minecraft_launcher_lib.command.get_minecraft_command(
                self.version, self.directory, options
            )

            self.status_update.emit("Game Running!")
            subprocess.run(command)
        except Exception as e:
            self.status_update.emit(f"Error: {str(e)}")
        
        self.finished.emit()

# --- TAMPILAN UI MINIMALIS (CRISPYBOX) ---
class CrispyBox(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CrispyBox")
        self.setFixedSize(500, 650)
        
        # FIX PATH: Mencari file di dalam folder 'asset'
        icon_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "asset", "crispy.png")

        # Pasang Ikon di Taskbar
        if os.path.exists(icon_path):
            self.setWindowIcon(QIcon(icon_path))

        self.minecraft_dir = minecraft_launcher_lib.utils.get_minecraft_directory().replace("minecraft", "crispybox")

        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.layout = QVBoxLayout(self.central_widget)
        self.layout.setContentsMargins(30, 30, 30, 30)

        # Logo Kentang Goreng di dalam UI
        self.logo = QLabel()
        if os.path.exists(icon_path):
            pixmap = QPixmap(icon_path).scaled(120, 120, Qt.KeepAspectRatio, Qt.SmoothTransformation)
            self.logo.setPixmap(pixmap)
            self.logo.setAlignment(Qt.AlignCenter)
            self.layout.addWidget(self.logo)

        self.title_label = QLabel("CrispyBox Launcher")
        self.title_label.setStyleSheet("font-size: 24px; font-weight: bold; margin-bottom: 10px; color: #333;")
        self.title_label.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.title_label)

        self.nickname_input = QLineEdit()
        self.nickname_input.setPlaceholderText("Enter Nickname...")
        self.layout.addWidget(self.nickname_input)

        self.version_list = QListWidget()
        self.load_versions()
        self.layout.addWidget(self.version_list)

        self.status_label = QLabel("Ready to play.")
        self.layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.layout.addWidget(self.progress_bar)

        self.play_button = QPushButton("PLAY")
        self.play_button.setStyleSheet("background-color: #4CAF50; color: white; font-weight: bold; padding: 10px; border-radius: 5px;")
        self.play_button.clicked.connect(self.start_launch)
        self.layout.addWidget(self.play_button)

    def load_versions(self):
        try:
            all_versions = minecraft_launcher_lib.utils.get_version_list()
            for v in all_versions:
                if v['type'] == 'release':
                    self.version_list.addItem(v['id'])
        except:
            self.version_list.addItem("1.20.1")

    def start_launch(self):
        nickname = self.nickname_input.text().strip()
        version = self.version_list.currentItem()

        if not nickname or not version:
            QMessageBox.warning(self, "Error", "Fill in all fields!")
            return

        self.play_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        
        self.worker = LaunchWorker(nickname, version.text(), self.minecraft_dir)
        self.worker.progress_update.connect(self.update_progress)
        self.worker.status_update.connect(self.status_label.setText)
        self.worker.finished.connect(self.on_finished)
        self.worker.start()

    def update_progress(self, val, max_val):
        self.progress_bar.setMaximum(max_val)
        self.progress_bar.setValue(val)

    def on_finished(self):
        self.play_button.setEnabled(True)
        self.progress_bar.setVisible(False)
        self.status_label.setText("Ready.")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = CrispyBox()
    window.show()
    sys.exit(app.exec())