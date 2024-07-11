from pathlib import Path
from qtpy.QtWidgets import QTabWidget
from qtpy.QtGui import QIcon
from .dvdbackupwidget import DvdBackupWidget
from .ffmpegwidget import FfmpegWidget

def get_path():
    p = Path(__file__)
    p = p.resolve()
    return p.parent.parent

class DRip(QTabWidget):
    def __init__(self):
        super().__init__()
        
        self.dvdbackup = DvdBackupWidget()
        self.ffmpeg = FfmpegWidget()
        
        self.addTab(self.dvdbackup, "dvdbackup")
        self.addTab(self.ffmpeg, "ffmpeg")
        
        self.dvdbackup.vobPathChanged.connect(self.ffmpeg.vobPathChanged)
    
        p = get_path().joinpath('images').joinpath('icon.png')
        icon = QIcon(str(p))
        self.setWindowIcon(icon)
        