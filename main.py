#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Run Cycle Tracks.
"""
import sys
from qtpy.QtWidgets import QApplication
from drip.drip import DRip

if __name__ == '__main__':

    QApplication.setApplicationName("DRip")
    QApplication.setOrganizationName("Tracks")
    
    app = QApplication(sys.argv)
    
    window = DRip()
    window.show()
    
    sys.exit(app.exec_())
