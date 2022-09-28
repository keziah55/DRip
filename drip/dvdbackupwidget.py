from qtpy.QtWidgets import (QFileDialog, QPushButton, QTabWidget, QSpinBox, QWidget,
                            QMessageBox, QCheckBox, QGridLayout, QLabel, QScrollArea,
                            QPlainTextEdit)
from qtpy.QtCore import Slot, QThread, Signal
from qtpy.QtGui import QIcon
from customQObjects.widgets import HSplitter, VSplitter
from .cmdwidget import CmdWidget
from .subprocessthread import SubprocessWorker
from .elidebutton import ElideButton
import os.path
import re

class ParamView(QWidget):
    
    valueChanged = Signal(str, object)
    
    def __init__(self,):
        super().__init__()
        
        self.deviceButton = ElideButton()
        self.deviceButton.setFlat(True)
        self.deviceButton.clicked.connect(self.selectDevice)
        self.deviceButton.setToolTip("Select dvd device")
        self.device = "/dev/sr0"
        
        self.outdirButton = ElideButton()
        self.outdirButton.setFlat(True)
        self.outdirButton.clicked.connect(self.selectOutdir)
        self.outdirButton.setToolTip("Select output directory")
        self.outdir = os.path.join(os.path.expanduser('~'), "Videos", "temp")
        
        self.titleBox = QSpinBox()
        self.titleBox.setMinimum(1)
        # self.titleBox.setPrefix("Title: ")
        self.titleBox.valueChanged.connect(lambda value: self.valueChanged.emit("title", str(value)))# self.setRunCmd)
        self.titleBox.setToolTip("Set title to be ripped")
        self.titleNum = 1
        titleLabel = QLabel("Title: ")
        
        for widget in [self.deviceButton, self.outdirButton, titleLabel]:
            widget.setStyleSheet("text-align: left;")
        
        argsLayout = QGridLayout()
        argsLayout.addWidget(self.deviceButton, 0, 0, 1, 3)
        argsLayout.addWidget(self.outdirButton, 1, 0, 1, 3)
        argsLayout.addWidget(titleLabel, 2, 0)
        argsLayout.addWidget(self.titleBox, 2, 1, 1, 2)
        argsLayout.setRowStretch(argsLayout.rowCount(), 1)
        
        self.setLayout(argsLayout)
        
    @property
    def device(self):
        return self._device
    
    @device.setter
    def device(self, dev):
        self._device = dev
        self.deviceButton.setText(f"DVD device: {dev}")
        self.valueChanged.emit("device", dev)
        
    def selectDevice(self):
        filename = QFileDialog.getOpenFileName(self, "Select dvd device", "/dev")
        if isinstance(filename, tuple):
            filename = filename[0]
        if filename:
            self.device = filename
      
    ## DVDBACKUP OUTPUT DIR
    @property
    def outdir(self):
        return self._outdir
    
    @outdir.setter
    def outdir(self, outdir):
        self._outdir = outdir
        self.outdirButton.setText(f"Out: {outdir}")
        # self.setRunCmd()
        self.valueChanged.emit("outdir", outdir)
        
    def selectOutdir(self):
        filename = QFileDialog.getExistingDirectory(self, "Select output directory", 
                                                    os.path.expanduser('~'))
        if isinstance(filename, tuple):
            filename = filename[0]
        if filename:
            self.outdir = filename
            
class InfoView(VSplitter):
    def __init__(self, *args, **kwargs):
        super().__init__()
        self.infoWidget = CmdWidget(*args, **kwargs)
        self.summaryWidget = QPlainTextEdit()
        self.summaryWidget.setReadOnly(True)
        
        # splitter = VSplitter()
        self.addWidget(self.infoWidget)
        self.addWidget(self.summaryWidget)
        
    def setSummaryInfo(self, text):
        self.summaryWidget.setPlainText(text)
        
    def __getattr__(self, name):
        return getattr(self.infoWidget, name)
        

class DvdBackupWidget(HSplitter):
    """ Widget to run 'dvdbackup' commands and show the output """
    
    vobPathChanged = Signal(str)
    
    def __init__(self):
        super().__init__()
        
        self.extraArgs = ["-v", "-p"]
        
        self.paramWidget = ParamView()
        paramScroll = QScrollArea()
        paramScroll.setWidget(self.paramWidget)
        paramScroll.setWidgetResizable(True)
        
        self.paramWidget.valueChanged.connect(self._paramChanged)
        
        self.infoView = InfoView()
        self.infoWidget = self.infoView.infoWidget #CmdWidget()
        self.runWidget = CmdWidget()
        self.catWidget = CmdWidget()
        self.infoWidget.requestRun.connect(self._getInfo)
        self.runWidget.requestRun.connect(self._run)
        self.catWidget.requestRun.connect(self._cat)
        
        self.autoCatCheckBox = QCheckBox("Auto cat")
        self.autoCatCheckBox.setToolTip("Automatically run 'cat' command on completion")
        self.autoCatCheckBox.setChecked(True)
        self.runWidget.topLayout.insertWidget(2, self.autoCatCheckBox)
        
        icon = QIcon.fromTheme("folder-open")
        vobPathButton = QPushButton(icon, "")
        vobPathButton.clicked.connect(self._selectVobPath)
        vobPathButton.setToolTip("Select directory containing *.VOB files")
        self.catWidget.topLayout.insertWidget(0, vobPathButton)
        
        self.setInfoCmd()
        self.setRunCmd()
        self.resetCatCmd()
        
        self.cmdView = QTabWidget()
        self.cmdView.addTab(self.infoView, "Info")
        self.cmdView.addTab(self.runWidget, "Run")
        self.cmdView.addTab(self.catWidget, "Cat")
        
        # self.addLayout(argsLayout)
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
        self.infoThread.finished.connect(self._infoComplete)
        
        self.runThread = QThread()
        self.runWorker = SubprocessWorker()
        self.runWorker.moveToThread(self.runThread)
        self.runWorker.stdout.connect(self.runWidget.appendText)
        self.runThread.started.connect(self.runWorker.start)
        self.runThread.started.connect(self.runWidget.setRunning)
        self.runWorker.processComplete.connect(self.runThread.quit)
        self.runThread.finished.connect(self.runWidget.setRunComplete)
        self.runThread.finished.connect(self._checkCat)
        
        self.catThread = QThread()
        self.catWorker = SubprocessWorker(shell=True)
        self.catWorker.moveToThread(self.catThread)
        self.catWorker.stdout.connect(self.catWidget.appendText)
        self.catThread.started.connect(self.catWorker.start)
        self.catThread.started.connect(self.catWidget.setRunning)
        self.catWorker.processComplete.connect(self.catThread.quit)
        self.catThread.finished.connect(self.catWidget.setRunComplete)
        self.catThread.finished.connect(self.resetCatCmd)
        
    ## DVD DEVICE
    @property
    def device(self):
        return self.paramWidget.device
    
    @device.setter
    def device(self, dev):
        self.setInfoCmd()
        self.setRunCmd()
        
    ## DVDBACKUP OUTPUT DIR
    @property
    def outdir(self):
        return self.paramWidget.outdir
    
    @outdir.setter
    def outdir(self, outdir):
        self.setRunCmd()
        
    def _paramChanged(self, name, value):
        # if (a:=getattr(self, name, None)) is not None and isinstance(a, property) and a.fset is not None:
        #     setattr(self, name, value)
        if name == "device":
            self.device = value
        elif name == "outdir":
            self.outdir = value
        self.setRunCmd()
    
    ## TITLE NUM TO BACK UP
    @property
    def titleNum(self):
        return str(self.titleBox.value())
    
    @titleNum.setter
    def titleNum(self, num):
        self.titleBox.setValue(num)
        self.setInfoCmd()
        
    ## DVDBACKUP GET INFO COMMAND
    def setInfoCmd(self):
        try:
            self.infoWidget.setCmd(self.infoCmd)
        except:
            # on initialisation, stuff won't exist yet
            pass
    
    @property
    def infoCmd(self):
        return ["dvdbackup", "-i", self.device, "-I"]
    
    def _getInfo(self):
        if not os.path.exists(self.device):
            raise ValueError
            
        self.infoWorker.cmd = self.infoCmd
        self.infoThread.start()
        
    def _infoComplete(self):
        self.dvdname, info, titleset = self._parseInfo()
        self.infoView.setSummaryInfo(f"{info}\n{titleset}")
        self.catCmd = self._getCatCmd(prompt=False)
        if self.catCmd is not None:
            self.catWidget.setCmd(self.catCmd)
            self.vobPathChanged.emit(self.vobPath)
        
    def _parseInfo(self):
        """ Get dvd name and guessed main title set """
        dvdname = ""
        mainFeatureInfo = ""
        titleSet = ""
        
        if (m := re.search(r'DVD-Video information of the DVD with title "(?P<name>.*)"', self.infoWidget.text)) is not None:
            dvdname = m.group('name')
        if (m := re.search(r'(?P<mainfeature>Main feature:.*?)\n\n', self.infoWidget.text, re.DOTALL)) is not None:
            mainFeatureInfo = m.group('mainfeature')
        if mainFeatureInfo:
            if (m := re.search(r'Title set containing the main feature is (?P<num>\d+)', mainFeatureInfo)) is not None:
                num = m.group('num')
                if (m := re.search(f'(?P<titleset>Title set {num}.*?)\n\n', self.infoWidget.text, re.DOTALL)) is not None:
                    titleSet = m.group('titleset')
                    # remove multiple indentation
                    titleSet = re.sub(r'\t+', '\t', titleSet)

        return dvdname, mainFeatureInfo, titleSet
        
    ## DVDBACKUP COMMAND
    def setRunCmd(self):
        try:
            self.runWidget.setCmd(self.runCmd)
        except:
            # on initialisation, stuff won't exist yet
            pass
        
    @property
    def runCmd(self):
        titleNum = str(self.paramWidget.titleBox.value())
        return ["dvdbackup", "-i", self.device, "-o", self.outdir, "-t", titleNum] + self.extraArgs
        
    def _run(self):
        if not os.path.exists(self.device):
            raise ValueError
            
        if not os.path.exists(self.outdir):
            raise ValueError
            
        self.runWorker.cmd = self.runCmd
        self.runThread.start()
        
    ## CAT COMMAND
    @Slot()
    def _checkCat(self):
        self.catCmd = self._getCatCmd(prompt=False)
        if self.catCmd is not None:
            self.catWidget.setCmd(self.catCmd)
        if not self.autoCatCheckBox.isChecked():
            return None
        else:
            self.cmdView.setCurrentWidget(self.catWidget)
            self._cat()
            
    @property    
    def vobPath(self):
        return os.path.join(self.outdir, self.dvdName, "VIDEO_TS")
    
    @property
    def dvdName(self):
        """ Parse `infoWidget` text for DVD name """
        if (m := re.search(r'DVD-Video information of the DVD with title "(?P<dvdname>.+)"', self.infoWidget.text)) is not None:
            return m.group('dvdname')
        else:
            return None
        
    def resetCatCmd(self):
        self.catCmd = None
     
    def _getCatCmd(self, prompt=True):
        if self.dvdName is None or not os.path.exists(self.vobPath):
            if not prompt:
                return None
            else:
                path = self._selectVobPath()
                if not path:
                    ret = QMessageBox.warning(self, "No *.VOB path", "No path to *.VOB files. Aborting.",
                                              buttons=QMessageBox.Ok|QMessageBox.Cancel)
                    if ret == QMessageBox.Cancel:
                        return self._getCatCmd()
                    else:
                        return None
        else:
            path = self.vobPath
        return self._makeCatCmd(path)
            
    def _selectVobPath(self):
        path = QFileDialog.getExistingDirectory(self, "Select *.VOB path", self.outdir)
        if path:
            self.catCmd = self._makeCatCmd(path)
            self.catWidget.setCmd(self.catCmd)
            self.catWorker.cmd = self.catCmd
        return path
    
    def _makeCatCmd(self, path):
        path = re.sub(r" ", "\\ ", path)
        outpath = os.path.join(path, "output.vob")
        return [f"cat {path}{os.path.sep}*.VOB > {outpath}"]
            
    def _cat(self):
        if self.catCmd is None:
            self.catCmd = self._getCatCmd()
        if self.catCmd is not None:
            self.catWidget.setCmd(self.catCmd)
            self.catWorker.cmd = self.catCmd
            self.catThread.start()
        