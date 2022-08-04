from qtpy.QtWidgets import (QFileDialog, QPushButton, QWidget, QTabWidget,
                            QHBoxLayout, QVBoxLayout, QSpinBox, QMessageBox,
                            QCheckBox)
from qtpy.QtCore import Qt, QTimer, Slot, Signal, QThread
from qtpy.QtGui import QIcon
from .cmdwidget import CmdWidget
from .subprocessthread import SubprocessWorker
import os.path
import re

class DvdBackupWidget(QWidget):
    """ Widget to run 'dvdbackup' commands and show the output """
    def __init__(self):
        super().__init__()
        
        self.extraArgs = ["-v", "-p"]
        
        self.deviceButton = QPushButton()
        self.deviceButton.setFlat(True)
        self.deviceButton.clicked.connect(self.selectDevice)
        self.deviceButton.setToolTip("Select dvd device")
        self.device = "/dev/sr0"
        
        self.outdirButton = QPushButton()
        self.outdirButton.setFlat(True)
        self.outdirButton.clicked.connect(self.selectOutdir)
        self.outdirButton.setToolTip("Select output directory")
        self.outdir = os.path.join(os.path.expanduser('~'), "Videos", "temp")
        
        self.titleBox = QSpinBox()
        self.titleBox.setMinimum(1)
        self.titleBox.setPrefix("Title: ")
        self.titleBox.valueChanged.connect(self.setRunCmd)
        self.titleBox.setToolTip("Set title to be ripped")
        self.titleNum = 1
        
        self.infoWidget = CmdWidget()
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
        self.cmdView.addTab(self.infoWidget, "Info")
        self.cmdView.addTab(self.runWidget, "Run")
        self.cmdView.addTab(self.catWidget, "Cat")
        
        argsLayout = QHBoxLayout()
        argsLayout.addWidget(self.deviceButton)
        argsLayout.addWidget(self.outdirButton)
        argsLayout.addWidget(self.titleBox)
        
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
        return self._device
    
    @device.setter
    def device(self, dev):
        self._device = dev
        self.deviceButton.setText(f"DVD device: {dev}")
        self.setInfoCmd()
        self.setRunCmd()
        
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
        self.setRunCmd()
        
    def selectOutdir(self):
        filename = QFileDialog.getExistingDirectory(self, "Select output directory", 
                                                    os.path.expanduser('~'))
        if isinstance(filename, tuple):
            filename = filename[0]
        if filename:
            self.outdir = filename
        
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
        
    ## DVDBACKUP COMMAND
    def setRunCmd(self):
        try:
            self.runWidget.setCmd(self.runCmd)
        except:
            # on initialisation, stuff won't exist yet
            pass
        
    @property
    def runCmd(self):
        # return ['echo', '"hello"']
        return ["dvdbackup", "-i", self.device, "-o", self.outdir, "-t", self.titleNum] + self.extraArgs
        
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
        if self.catCmd is None or self.dvdName is None or not os.path.exists(self.vobPath):
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
        