from qtpy.QtWidgets import (QLabel, QFileDialog, QPushButton, QWidget, QFrame, 
                            QInputDialog, QGridLayout, QPlainTextEdit, QTabWidget,
                            QHBoxLayout, QVBoxLayout, QCheckBox, QLineEdit,
                            QSpinBox, QScrollArea)
from qtpy.QtCore import Qt, QTimer, Slot, QThread
from qtpy.QtGui import QIcon
from customQObjects.widgets import ElideMixin
from .cmdwidget import CmdWidget
from .subprocessthread import SubprocessWorker
import os
import re

class ElideButton(ElideMixin, QPushButton): 
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setStyleSheet("text-align: left;")
        

class FfmpegWidget(QWidget):
    def __init__(self):
        super().__init__()
        
        self.inpathButton = ElideButton()
        self.inpathButton.setFlat(True)
        self.inpathButton.clicked.connect(self.selectInpath)
        self.inpathButton.setToolTip("Select input vob")
        self.inpath = ""
        
        self.outdirButton = ElideButton()
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
        
        threadsLabel = QLabel("Threads:")
        self.threadsBox = QSpinBox()
        numCores = os.cpu_count()
        self.threadsBox.setMinimum(1)
        self.threadsBox.setMaximum(numCores)
        self.threadsBox.setValue(numCores)
        threadsLayout = QHBoxLayout()
        threadsLayout.addWidget(threadsLabel)
        threadsLayout.addWidget(self.threadsBox)
        
        crfLabel = QLabel("CRF:")
        self.crfBox = QSpinBox()
        self.crfBox.setValue(21)
        self.crfBox.setMinimum(0)
        self.crfBox.setMaximum(51)
        crfLayout = QHBoxLayout()
        crfLayout.addWidget(crfLabel)
        crfLayout.addWidget(self.crfBox)
        
        self.argsLayout = QGridLayout()
        self.argsLayout.addWidget(self.inpathButton, 0, 0, 1, 3)
        self.argsLayout.addWidget(self.outdirButton, 1, 0, 1, 3)
        self.argsLayout.addWidget(threadsLabel, 2, 0)
        self.argsLayout.addWidget(self.threadsBox, 2, 1, 1, 2)
        self.argsLayout.addWidget(crfLabel, 3, 0)
        self.argsLayout.addWidget(self.crfBox, 3, 1, 1, 2)
        
        layout = QHBoxLayout()
        layout.addLayout(self.argsLayout)
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
        # TODO remove existing stream widgets and remake
        nextRow = self.argsLayout.rowCount() + 1
        if (text := self.infoWidget.text):
            i = re.finditer(r"Stream #(?P<stream>\d+:\d+)\[0x\w+\]: (?P<type>\w+): (?P<info>.*)", text)
            for m in i:
                nextRow = self.addStream(self.argsLayout, nextRow, m.group('stream'), m.group('type'), m.group('info'))

    def addStream(self, layout, nextRow, num, streamType, info):
        # TODO get values 
        box = QCheckBox()
        label = QLabel(f"Stream #{num}: {streamType}: {info}")
        label.setStyleSheet("text-align: left;")
        self.num = num
        self.streamType = streamType
        layout.addWidget(box, nextRow, 0)
        layout.addWidget(label, nextRow, 1, 1, 2)
        if streamType.lower() in ['audio', 'subtitle']:
            nextRow += 1
            langLabel = QLabel("Language: ")
            langEdit = QLineEdit("eng")
            titleLabel = QLabel("Title: ")
            titleEdit = QLineEdit("English")
            layout.addWidget(langLabel, nextRow, 1)
            layout.addWidget(langEdit, nextRow, 2)
            nextRow += 1
            layout.addWidget(titleLabel, nextRow, 1)
            layout.addWidget(titleEdit, nextRow, 2)
        nextRow += 1
        return nextRow