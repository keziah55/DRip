from qtpy.QtWidgets import (QLabel, QFileDialog, QPushButton, QWidget, QFrame, 
                            QInputDialog, QGridLayout, QPlainTextEdit, QTabWidget,
                            QHBoxLayout, QVBoxLayout, QCheckBox, QLineEdit,
                            QSpinBox)
from qtpy.QtCore import Qt, QTimer, Slot, QThread
from qtpy.QtGui import QIcon
from .cmdwidget import CmdWidget
from .subprocessthread import SubprocessWorker
import os
import re

class FfmpegWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.inpathButton = QPushButton()
        self.inpathButton.setFlat(True)
        self.inpathButton.clicked.connect(self.selectInpath)
        self.inpathButton.setToolTip("Select input vob")
        self.inpath = ""
        
        self.outdirButton = QPushButton()
        self.outdirButton.setFlat(True)
        self.outdirButton.clicked.connect(self.selectOutdir)
        self.outdirButton.setToolTip("Select output directory")
        self.outdir = os.path.join(os.path.expanduser('~'), "Videos", "temp")
        
        self.infoWidget = CmdWidget()
        self.runWidget = CmdWidget()
        self.infoWidget.requestRun.connect(self._getInfo)
        
        self.setInfoCmd()
        self.setRunCmd()
        
        self.cmdView = QTabWidget()
        self.cmdView.addTab(self.infoWidget, "Info")
        self.cmdView.addTab(self.runWidget, "Run")
        
        argsLayout = QHBoxLayout()
        argsLayout.addWidget(self.inpathButton)
        argsLayout.addWidget(self.outdirButton)
        
        layout = QVBoxLayout()
        layout.addLayout(argsLayout)
        layout.addWidget(self.cmdView)
        
        self.setLayout(layout)
        
        self.infoThread = QThread()
        self.infoWorker = SubprocessWorker()
        self.infoWorker.moveToThread(self.infoThread)
        self.infoWorker.stdout.connect(self.infoWidget.appendText)
        self.infoThread.started.connect(self.infoWorker.start)
        self.infoThread.started.connect(self.infoWidget.setRunning)
        self.infoWorker.processComplete.connect(self.infoThread.quit)
        self.infoThread.finished.connect(self.infoWidget.setRunComplete)
        self.infoThread.finished.connect(self._getStreamInfo)
        
    @property
    def inpath(self):
        return self._inpath
    
    @inpath.setter
    def inpath(self, inpath):
        self._inpath = inpath
        self.inpathButton.setText(f"Input: {inpath}")
        self.setInfoCmd()
        self.setRunCmd()
        
    def selectInpath(self):
        filename = QFileDialog.getOpenFileName(self, "Select input vob", self.outdir)
        if isinstance(filename, tuple):
            filename = filename[0]
        if filename:
            self.inpath = filename
            
            
    @property
    def outdir(self):
        return self._outdir
    
    @outdir.setter
    def outdir(self, outdir):
        self._outdir = outdir
        self.outdirButton.setText(f"Out: {outdir}")
        self.setRunCmd()
        
    def selectOutdir(self):
        filename = QFileDialog.getExistingDirectory(self, "Select output directory", 
                                                    self.outdir)
        if isinstance(filename, tuple):
            filename = filename[0]
        if filename:
            self.outdir = filename
            
    def setInfoCmd(self):
        try:
            self.infoWidget.setCmd(self.infoCmd)
        except:
            # on initialisation, stuff won't exist yet
            pass
            
    @property
    def infoCmd(self):
        return ["ffmpeg", "-analyzeduration", "100M", "-probesize", "100M", "-i", self.inpath]
        
        
    def _getInfo(self):
        
        if not os.path.exists(self.inpath):
            raise ValueError
            
        self.infoWorker.cmd = self.infoCmd
        self.infoThread.start()
        
        
    def setRunCmd(self):
        try:
            self.runWidget.setCmd(self.runCmd)
        except:
            # on initialisation, stuff won't exist yet
            pass
        
    def _getStreamInfo(self):
        self.widget = FfmpegArgWidget()
        if (text := self.infoWidget.text):
            i = re.finditer(r"Stream #(?P<stream>\d+:\d+)\[0x\w+\]: (?P<type>\w+): (?P<info>.*)", text)
            for m in i:
                self.widget.addStream(m.group('stream'), m.group('type'), m.group('info'))
        self.layout().insertWidget(1, self.widget)


class StreamWidget(QWidget):
    def __init__(self, num, streamType, info):
        super().__init__()
        box = QCheckBox()
        label = QLabel(f"Stream #{num}: {streamType}: {info}")
        self.num = num
        self.streamType = streamType
        layout = QGridLayout()
        layout.addWidget(box, 0, 0)
        layout.addWidget(label, 0, 1)
        if streamType.lower() in ['audio', 'subtitle']:
            langLabel = QLabel("Language: ")
            langEdit = QLineEdit("eng")
            titleLabel = QLabel("Title: ")
            titleEdit = QLineEdit("English")
            layout.addWidget(langLabel, 1, 1)
            layout.addWidget(langEdit, 1, 2)
            layout.addWidget(titleLabel, 2, 1)
            layout.addWidget(titleEdit, 2, 2)
        self.setLayout(layout)
            
            
class FfmpegArgWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QVBoxLayout()
        
        threadsLabel = QLabel("Threads:")
        threadsBox = QSpinBox()
        numCores = os.cpu_count()
        threadsBox.setMinimum(1)
        threadsBox.setMaximum(numCores)
        threadsBox.setValue(numCores)
        threadsLayout = QHBoxLayout()
        threadsLayout.addWidget(threadsLabel)
        threadsLayout.addWidget(threadsBox)
        
        crfLabel = QLabel("CRF:")
        crfBox = QSpinBox()
        crfBox.setValue(21)
        crfBox.setMinimum(0)
        crfBox.setMaximum(51)
        crfLayout = QHBoxLayout()
        crfLayout.addWidget(crfLabel)
        crfLayout.addWidget(crfBox)
        
        self.layout.addLayout(threadsLayout)
        self.layout.addLayout(crfLayout)
        
        self.setLayout(self.layout)
        
    def addStream(self, num, streamType, info):
        stream = StreamWidget(num, streamType, info)
        self.layout.addWidget(stream)
        
        