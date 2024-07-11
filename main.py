#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Cycle Tracks.
"""
import sys
from pathlib import Path
from qtpy.QtWidgets import QApplication
from drip.drip import DRip

if __name__ == '__main__':

    QApplication.setApplicationName("DRip")
    QApplication.setOrganizationName("Tracks")
    
    app = QApplication(sys.argv)
    # set desktop file, if it exists
    # this allows the correct icon to be shown on wayland
    p = Path.home().joinpath(".local", "share", "applications", "drip.desktop")
    if p.exists():
        app.setDesktopFileName(str(p))
    
    window = DRip()
    window.show()
    
    sys.exit(app.exec_())
