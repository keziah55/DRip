from qtpy.QtWidgets import (QApplication, QPushButton, QWidget, QPlainTextEdit,
                            QHBoxLayout, QVBoxLayout, QSizePolicy)
from qtpy.QtCore import Signal, Qt
from qtpy.QtGui import QFontDatabase, QIcon, QClipboard
from customQObjects.widgets import ElideLabel

class CmdWidget(QWidget):
    """ Widget to display a command and its output 
    
        Note that running the command should be handled by another object.
        The :attr:`requestRun` will be emitted when the 'Run' button is clicked.
    """
    
    requestRun = Signal()
    """ **signal** requestRun() 
    
        Emitted when 'Run' button clicked
    """
    
    def __init__(self):
        super().__init__()
        
        fixedfont = QFontDatabase.systemFont(QFontDatabase.FixedFont)
        
        icon = QIcon.fromTheme("system-run")
        infoButton = QPushButton(icon, "")
        infoButton.clicked.connect(self.requestRun)
        infoButton.setToolTip("Run command")
        
        icon = QIcon.fromTheme("edit-copy")
        copyButton = QPushButton(icon, "")
        copyButton.clicked.connect(self.copyCommand)
        copyButton.setToolTip("Copy command to mouse selection")
        
        icon = QIcon.fromTheme("edit-clear")
        clearButton = QPushButton(icon, "")
        clearButton.clicked.connect(self.reset)
        clearButton.setToolTip("Clear output")
        
        self.cmdLabel = ElideLabel()
        self.cmdLabel.setFont(fixedfont)
        self.cmdLabel.setTextInteractionFlags(Qt.TextSelectableByMouse)
        
        infoButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        clearButton.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Preferred)
        self.cmdLabel.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Preferred)
        
        self.topLayout = QHBoxLayout()
        self.topLayout.addWidget(infoButton)
        self.topLayout.addWidget(self.cmdLabel)
        self.topLayout.addWidget(copyButton)
        self.topLayout.addWidget(clearButton)
        
        self.view = QPlainTextEdit()
        self.view.setReadOnly(True)
        self.view.setFont(fixedfont)
        
        layout = QVBoxLayout()
        layout.addLayout(self.topLayout)
        layout.addWidget(self.view)
        self.setLayout(layout)
        
        self.reset()
        
    def reset(self):
        """ Remove all output text """
        self.view.setPlainText("")
        self.cmd = None
        
    def setText(self, text):
        """ Set `text` in viewer """
        self.view.setPlainText(text)
        
    def appendText(self, text):
        """ Append `text` to viewer """
        self.view.appendPlainText(text)
        
    def setCmd(self, cmd):
        """ Set the command. `cmd` should be list of command components """
        if not cmd:
            self.cmdLabel.setText("")
        else:
            self.cmdLabel.setText(" ".join(cmd))
        
    @property 
    def text(self):
        return self.view.toPlainText()
    
    def setRunning(self):
        self._enable(enable=False)
                
    def setRunComplete(self):
        self._enable(enable=True)
                
    def _enable(self, enable=True):
        for n in range(self.topLayout.count()):
            item = self.topLayout.itemAt(n)
            if item is not None:
                item.widget().setEnabled(enable)
                
    def copyCommand(self):
        """ Copy command to mouse selection """
        if (text := self.cmdLabel.fullText):
            QApplication.clipboard().setText(text, mode=QClipboard.Selection)