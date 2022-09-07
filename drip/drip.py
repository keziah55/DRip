from qtpy.QtWidgets import QTabWidget
from .dvdbackupwidget import DvdBackupWidget
from .ffmpegwidget import FfmpegWidget

class DRip(QTabWidget):
    def __init__(self):
        super().__init__()
        
        self.dvdbackup = DvdBackupWidget()
        self.ffmpeg = FfmpegWidget()
        
        self.addTab(self.dvdbackup, "dvdbackup")
        self.addTab(self.ffmpeg, "ffmpeg")
    
            
        