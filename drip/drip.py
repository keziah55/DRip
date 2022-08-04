from qtpy.QtWidgets import (QMainWindow, QDockWidget, QAction, QSizePolicy, 
                             QMessageBox, QLabel, QFileDialog, QPushButton,
                             QHBoxLayout, QVBoxLayout, QWidget, QFrame, QInputDialog,
                             QGridLayout, QPlainTextEdit, QTabWidget)
from qtpy.QtCore import Qt, QTimer, Slot
from qtpy.QtGui import QIcon
import os.path

from .dvdbackupwidget import DvdBackupWidget
from .ffmpegwidget import FfmpegWidget

class DRip(QTabWidget):
    def __init__(self):
        super().__init__()
        
        self.dvdbackup = DvdBackupWidget()
        self.ffmpeg = FfmpegWidget()
        
        self.addTab(self.dvdbackup, "dvdbackup")
        self.addTab(self.ffmpeg, "ffmpeg")
    
            
        