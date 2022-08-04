from qtpy.QtCore import QObject, Signal, Slot
import subprocess

class SubprocessWorker(QObject):
    processComplete = Signal()
    
    stdout = Signal(str)
    
    def __init__(self, cmd=None, **kwargs):
        super().__init__()
        self.cmd = cmd
        self.process = None
        self.pkwargs = kwargs
        
    def start(self):
        if self.cmd is None:
            return self._finished()
        
        # echo command
        self.stdout.emit(" ".join(self.cmd))
        
        self.process = subprocess.Popen(self.cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                        **self.pkwargs)
        while True:
            line = self.process.stdout.readline()
            if not line:
                break
            self.stdout.emit(line.decode().rstrip())
        rc = self.process.wait()
        self.stdout.emit(f"Completed with returncode {rc}")
        self._finished()
        
    @Slot()
    def _finished(self):
        self.process = None
        self.cmd = None
        self.processComplete.emit()