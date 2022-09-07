from qtpy.QtWidgets import (QLabel, QFileDialog, QWidget, QGridLayout, QTabWidget, 
                            QHBoxLayout, QCheckBox, QLineEdit, QSpinBox, QScrollArea)
from qtpy.QtCore import Signal, QThread
from customQObjects.widgets import HSplitter
from .cmdwidget import CmdWidget
from .subprocessthread import SubprocessWorker
from .elidebutton import ElideButton
import os
import re
from dataclasses import dataclass, field
        
@dataclass
class StreamInfo:
    num: str
    streamType: str
    info: str
    selected: bool = False
    hasMetadata: bool = False
    metadata: dict[str] = field(default_factory=dict)
    
    @property
    def label(self):
        return f"Stream #{self.num}: {self.streamType}: {self.info}"
    
    @property
    def stype(self):
        return self.streamType.lower()
    
    def setSelected(self, state):
        selected = False if state == 0 else True # `state` is Qt.CheckState enum
        self.selected = selected
        
    def setMetadata(self, language=None, title=None):
        self.hasMetadata = True
        if language is not None:
            self.metadata['language'] = language
        if title is not None:
            self.metadata['title'] = title
            
    def setMetadataLanguage(self, language):
        self.setMetadata(language=language)
        
    def setMetadataTitle(self, title):
        self.setMetadata(title=title)
            
    def getStreamInfo(self) -> list[str]:
        if not self.selected:
            return None
        cmd = ["-map", self.num]
        if self.hasMetadata:
            if self.stype == "audio":
                metadataId = "s:a:0"
            elif self.stype == "subtitle":
                metadataId = "s:s:0"
            if (language := self.metadata.get("language", None)) is not None:
                cmd += [f"-metadata:{metadataId}", f"language={language}"]
            if (title := self.metadata.get("title", None)) is not None:
                cmd += [f"-metadata:{metadataId}", f"title={title}"]
        return cmd

class ParamView(QWidget):
    
    valueChanged = Signal(str, object)
    
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
        
        self.streamInfo = []
        
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
        
        self.threadsBox.valueChanged.connect(lambda value: self.valueChanged.emit("threads", value))
        self.crfBox.valueChanged.connect(lambda value: self.valueChanged.emit("crf", value))
        
        self.layout = QGridLayout()
        self.layout.addWidget(self.inpathButton, 0, 0, 1, 3)
        self.layout.addWidget(self.outdirButton, 1, 0, 1, 3)
        self.layout.addWidget(threadsLabel, 2, 0)
        self.layout.addWidget(self.threadsBox, 2, 1, 1, 2)
        self.layout.addWidget(crfLabel, 3, 0)
        self.layout.addWidget(self.crfBox, 3, 1, 1, 2)
        
        self._streamLayoutRowNum = 4
        
        self._stretchItemRow = self.layout.rowCount()
        self.layout.setRowStretch(self._stretchItemRow, 1)
        
        self.setLayout(self.layout)

    def addStream(self, num, streamType, info):
        
        # remove stretch from (current) last row
        self.layout.setRowStretch(self._stretchItemRow, 0)
        
        streamInfo = StreamInfo(num, streamType, info)
        
        box = QCheckBox()
        box.stateChanged.connect(streamInfo.setSelected)
        box.stateChanged.connect(lambda state: self.valueChanged.emit(num, state))
        
        label = QLabel(streamInfo.label)
        label.setStyleSheet("text-align: left;")
        
        nextRow = self.layout.rowCount() + 1
        self.layout.addWidget(box, nextRow, 0)
        self.layout.addWidget(label, nextRow, 1, 1, 2)
        inc = 0
        if streamType.lower() in ['audio', 'subtitle']:
            inc += 1
            
            language = "eng"
            title = "English"
            langLabel = QLabel("Language: ")
            langEdit = QLineEdit(language)
            titleLabel = QLabel("Title: ")
            titleEdit = QLineEdit(title)
            
            self.layout.addWidget(langLabel, nextRow+inc, 1)
            self.layout.addWidget(langEdit, nextRow+inc, 2)
            inc += 1
            self.layout.addWidget(titleLabel, nextRow+inc, 1)
            self.layout.addWidget(titleEdit, nextRow+inc, 2)
        # inc += 1
        
            langEdit.textChanged.connect(streamInfo.setMetadataLanguage)
            titleEdit.textChanged.connect(streamInfo.setMetadataTitle)
            
            langEdit.textChanged.connect(lambda text: self.valueChanged.emit(f"{num}-language", text))
            titleEdit.textChanged.connect(lambda text: self.valueChanged.emit(f"{num}-title", text))
            
            streamInfo.setMetadata(language=language, title=title)
            
        self.streamInfo.append(streamInfo)
        
        # add stretch to last row
        self._stretchItemRow += inc + 1
        self.layout.setRowStretch(self._stretchItemRow, 1)
        
    def _removeStreams(self):
        for row in range(self._streamLayoutRowNum, self.layout.rowCount()):
            for col in range(self.layout.columnCount()):
                item = self.layout.itemAtPosition(row, col)
                if item is not None:
                    w = item.widget()
                    self.layout.removeWidget(w)
                    w.deleteLater()
        
    @property
    def inpath(self):
        return self._inpath
    
    @inpath.setter
    def inpath(self, inpath):
        self._inpath = inpath
        self.inpathButton.setText(f"Input: {inpath}")
        self.valueChanged.emit("inpath", inpath)
        
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
        self.valueChanged.emit("outdir", outdir)
        # self.setRunCmd()
        
    def selectOutdir(self):
        filename = QFileDialog.getExistingDirectory(self, "Select output directory", 
                                                    self.outdir)
        if isinstance(filename, tuple):
            filename = filename[0]
        if filename:
            self.outdir = filename
        
    def getParams(self):
        cmd = ["ffmpeg", "-analyzeduration", "100M", "-probesize", "100M", "-i", self.inpath]
        for streamInfo in self.streamInfo:
            info = streamInfo.getStreamInfo()
            if info is not None:
                cmd += info
        cmd += ["-threads", str(self.threadsBox.value()),
               "-codec:v", "libx264",
               "-crf", str(self.crfBox.value()),
               "-codec:a", "copy",
               "-codec:s", "copy",
               os.path.join(self.outdir, "output.mkv")]
        return cmd
        

class FfmpegWidget(HSplitter):
    def __init__(self):
        super().__init__()
        
        self.paramWidget = ParamView()
        paramScroll = QScrollArea()
        paramScroll.setWidget(self.paramWidget)
        paramScroll.setWidgetResizable(True)
        
        self.paramWidget.valueChanged.connect(self._paramChanged)
        
        self.inpath = ""
        self.outdir = os.path.join(os.path.expanduser('~'), "Videos", "temp")
        
        self.infoWidget = CmdWidget()
        self.runWidget = CmdWidget()
        self.infoWidget.requestRun.connect(self._getInfo)
        
        self.runWidget.requestRun.connect(self._run)
        
        self.setInfoCmd()
        self.setRunCmd()
        
        self.cmdView = QTabWidget()
        self.cmdView.addTab(self.infoWidget, "Info")
        self.cmdView.addTab(self.runWidget, "Run")
        
        self.addWidget(paramScroll)
        self.addWidget(self.cmdView)
        
        self.infoThread = QThread()
        self.infoWorker = SubprocessWorker()
        self.infoWorker.moveToThread(self.infoThread)
        self.infoWorker.stdout.connect(self.infoWidget.appendText)
        self.infoThread.started.connect(self.infoWorker.start)
        self.infoThread.started.connect(self.infoWidget.setRunning)
        self.infoWorker.processComplete.connect(self.infoThread.quit)
        self.infoThread.finished.connect(self.infoWidget.setRunComplete)
        self.infoThread.finished.connect(self._setStreamInfo)
        
        self.runThread = QThread()
        self.runWorker = SubprocessWorker()
        self.runWorker.moveToThread(self.runThread)
        self.runWorker.stdout.connect(self.runWidget.appendText)
        self.runThread.started.connect(self.runWorker.start)
        self.runThread.started.connect(self.runWidget.setRunning)
        self.runWorker.processComplete.connect(self._runFinished)
        self.runThread.finished.connect(self.runWidget.setRunComplete)
        
    @property
    def runCmd(self):
         return self.paramWidget.getParams()
        
    @property
    def inpath(self):
        return self._inpath
    
    @inpath.setter
    def inpath(self, inpath):
        self._inpath = inpath
        self.setInfoCmd()
        self.setRunCmd()
            
    @property
    def outdir(self):
        return self._outdir
    
    @outdir.setter
    def outdir(self, outdir):
        self._outdir = outdir
        self.setRunCmd()
    
    def _paramChanged(self, name, value):
        if name == "inpath":
            self._inpath = value
        if name == "outdir":
              self._outdir = value
        self.setRunCmd()
            
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
            
        self.paramWidget._removeStreams()
        self.infoWorker.cmd = self.infoCmd
        self.infoThread.start()
        
    def setRunCmd(self):
        try:
            self.runWidget.setCmd(self.runCmd)
        except:
            # on initialisation, stuff won't exist yet
            pass
        
    def _run(self):
        if not os.path.exists(self.inpath):
            raise ValueError
            
        if not os.path.exists(self.outdir):
            raise ValueError
            
        self.runWorker.cmd = self.runCmd
        self.runThread.start()
        
    def _runFinished(self):
        self.runThread.quit()
        self.activateWindow()
        
    def _setStreamInfo(self):
        if (text := self.infoWidget.text):
            i = re.finditer(r"Stream #(?P<stream>\d+:\d+)\[0x\w+\]: (?P<type>\w+): (?P<info>.*)", text)
            for m in i:
                 self.paramWidget.addStream(m.group('stream'), m.group('type'), m.group('info'))
        
